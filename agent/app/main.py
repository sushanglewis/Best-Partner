"""
最佳拍档 Agent 服务（LangGraph + FastAPI）

一、概述
- 独立的 Agent 服务，严格按照《Agent 实现方案（LangGraph + LangSmith）v1.0》实现：start → input_processor → file_toolscall_agent → requirements_analysis_agent → 条件路由 → end
- 以 FastAPI 暴露 HTTP API，仅与 Backend 通过 HTTP 协作；状态检查点优先使用 Redis（可选），本地默认使用内存 Checkpointer
- 运行期可接入 LangSmith（通过环境变量启用）

二、目录与模块职责
- app.graph.state：定义 Agent 工作流的状态模型（TypedDict），与方案一致（question_list、requirements_document、multi_files 等）
- app.graph.nodes：实现各节点：
  - start：初始化 thread_id/state_version/current_status 与消息
  - input_processor：追加并裁剪 messages；将 files 与本轮 message_id 绑定；去重
  - file_toolscall_agent：基于文件元信息按需提取内容（幂等：已有 file_content 跳过）
  - requirements_analysis_agent：更新 requirements_document、question_list、current_status，并将 state_version += 1，然后路由（completed→end；否则→input_processor）
  - end：收敛节点，无副作用
- app.graph.graph：装配并编译 StateGraph，配置 Checkpointer（Redis 或内存）
- app.services.tools：文件提取工具（占位实现，支持重试，可替换为 MCP/解析器）
- app.services.state_repo：内存态快照仓库，支撑 /v1/poll 与 /v1/state
- app.schemas：HTTP 接口的 Pydantic 入/出参 Schema
- app.utils.env：环境变量读取工具

三、HTTP 输入/输出 Schema（与方案口径一致）
1) POST /v1/submit 入参 SubmitRequest：
   - user_id: str
   - human_message: str
   - timestamp: ISO8601 字符串
   - files: FileInfoIn[]（可选）
     - file_id, file_name, file_type, file_size?, file_path
   - thread_id?: str（优先使用 Backend 传入）
   - state_version?: int（缺省从 0 起步）
   - message_id?: str（建议 Backend 传 uuid6；缺失则在 start 节点生成 uuid6-like）
   - current_status?: "clarifying" | "completed"（默认 clarifying）
   - model_params?: {provider?, base_url?, model?, temperature?, max_tokens?}

   出参 SubmitResponse：
   - thread_id: str
   - state_version: int
   - current_status: "clarifying" | "completed"
   - requirements_document: {version: str, content: str, last_updated: date}
   - question_list: QuestionOut[]（3题，每题2–3个建议选项）
   - messages: MessageOut[]（仅保留最近1条 human 和最近1条 assistant（若有）；当前示例仅有人类消息）
   - multi_files: FileInfoOut[]（含提取的 file_content 或 extract_error）

2) GET /v1/poll 入参：thread_id, client_state_version → 出参 PollResponse：
   - thread_id, client_state_version, current_state_version, has_update（通过 state_version 对比判断）

3) GET /v1/state 入参：thread_id → 出参：与 SubmitResponse 一致（完整快照）

四、核心函数/方法/类说明
- app.services.state_repo.StateRepository：
  - upsert(state: dict)：按 thread_id 存储当前快照（线程安全）
  - get(thread_id: str) -> Optional[dict]：读取快照
- app.graph.graph.get_compiled_graph()：构建并编译 LangGraph（含节点、边、条件路由）；内部自动选择 Checkpointer（Redis/内存）
- app.graph.nodes：
  - start(state, config) → RequirementsValidationState：初始化 thread_id/state_version/current_status，规范化消息ID与时间
  - input_processor(state, config) → RequirementsValidationState：裁剪消息窗口为“最近一条”；为本轮文件绑定 message_id 并去重
  - file_toolscall_agent(state, config) → RequirementsValidationState：对“本轮文件”按需提取内容，失败记录 extract_error；已提取跳过
  - requirements_analysis_agent(state, config) → RequirementsValidationState：
    • 汇总最近一轮上下文与文件摘要，生成“自动生成草稿”的 requirements_document
    • 产出三条澄清问题（带建议选项）
    • 根据用户意图（如包含“直接输出/完成/提交”）决定 current_status
    • 完成写入后 state_version += 1（与方案保持一致）
  - end(state, config)：收敛节点，无副作用
- app.services.tools.FileTools.extract_file(file_path: str) -> str：
  - 简化实现：直接以 UTF-8 读取文本；超长截断；失败抛出异常（由重试器兜底）

五、幂等性与一致性
- 文件提取：若目标 file_id 已有 file_content 则默认跳过，避免重复成本
- 仅 requirements_analysis_agent 完成写入后才推进 state_version，供前端轮询
- messages 仅保留最近一条 human（与方案一致；assistant 可扩展加入）

六、观测与配置
- 可通过环境变量启用 LangSmith：
  LANGCHAIN_TRACING_V2=true
  LANGSMITH_API_KEY=...（请勿写入代码）
  LANGSMITH_PROJECT=Best Partners Agent
- Checkpointer：
  - REDIS_URL=redis://:password@host:6379/0（存在则优先使用 RedisSaver；否则使用 MemorySaver）

七、运行方式
1) Python 3.10+
2) pip install -r requirements.txt
3) 可选：设置 REDIS_URL
4) uvicorn app.main:app --host 0.0.0.0 --port 8081

注意
- uuid6 规范：当前以 uuid4 hex 占位（uuid6-like），可在生产替换为 uuid6 实现
- 文件工具：当前为文本直读占位实现，生产建议接入 MCP/解析库并带指数退避重试
"""
from __future__ import annotations

import os
from datetime import datetime
import uuid
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import ORJSONResponse
import orjson 

from app.schemas import SubmitRequest, SubmitResponse, PollResponse, StateResponse
from app.graph.graph import get_compiled_graph
from app.services.state_repo import StateRepository
from app.utils.env import get_redis_url
# 移除：from langgraph.types import Command  # 兼容性：不再依赖不同版本的 Command/interrupt


class ORJSONResponseCustom(ORJSONResponse):
    def render(self, content: object) -> bytes:
        return orjson.dumps(content, option=orjson.OPT_NON_STR_KEYS)


app = FastAPI(title="Best Partners Agent", default_response_class=ORJSONResponseCustom)


# Compile graph with selected checkpointer
compiled_graph = get_compiled_graph()
# Repository for polling/state snapshot (works with or without Redis)
state_repo = StateRepository()


@app.post("/v1/submit", response_model=SubmitResponse)
def submit(req: SubmitRequest) -> SubmitResponse:
    """Run one step of the Agent graph.
    - Accepts a new user message and optional files.
    - Invokes the compiled graph which runs: start → input_processor → file_toolscall_agent → requirements_analysis_agent → (route)
    - Returns the updated snapshot of the Agent state for this thread.
    """
    # Compose initial input state for the graph from the HTTP request
    try:
        init_state = req.to_graph_state()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Ensure the LangGraph configurable.thread_id matches the thread id inside state.
    # If client didn't supply one, we must generate it here BEFORE running the graph,
    # so the checkpointer stores under the correct session id and subsequent rounds can load it.
    thread_id = init_state.get("thread_id") or req.thread_id
    if not thread_id:
        thread_id = uuid.uuid4().hex  # server-side new session id
        init_state["thread_id"] = thread_id

    # ==== NEW: Preload previous state and merge to preserve requirements_document/question_list across turns ====
    prev_state = None
    try:
        current_prev = compiled_graph.get_state({"configurable": {"thread_id": thread_id}})
        prev_state = current_prev.values if hasattr(current_prev, "values") else None
    except Exception:
        prev_state = None

    if prev_state:
        # Start from previous snapshot
        merged_state = {**prev_state}
        # Always use this thread_id
        merged_state["thread_id"] = thread_id
        # Use the incoming user message and the current-round files only
        merged_state["messages"] = init_state.get("messages", [])
        merged_state["multi_files"] = init_state.get("multi_files", [])
        # Prefer previous current_status unless client explicitly provides one
        if req.current_status is not None:
            merged_state["current_status"] = req.current_status
        # Never trust client-sent state_version; keep server-side version
        merged_state["state_version"] = int(prev_state.get("state_version", 0))
        # Model params: prefer incoming if provided; otherwise keep previous
        if init_state.get("model_params"):
            merged_state["model_params"] = init_state["model_params"]
        # Reset routing markers so a new turn won't be misdetected as returning from analysis
        merged_state.pop("from_node", None)
        merged_state.pop("prev_node", None)
        init_state = merged_state
    else:
        # 无历史状态：若后端提供 preload_state，则以其为基线合并本轮输入
        if getattr(req, "preload_state", None):
            pl = getattr(req, "preload_state") or {}
            merged_state = {**pl}
            merged_state["thread_id"] = thread_id
            # 覆盖为本轮用户输入与文件
            merged_state["messages"] = init_state.get("messages", [])
            if init_state.get("multi_files"):
                merged_state["multi_files"] = init_state["multi_files"]
            # 状态与模型参数：优先使用请求显式传入，其次使用预载值，最后使用默认
            merged_state["current_status"] = (
                req.current_status if req.current_status is not None else merged_state.get("current_status", "clarifying")
            )
            if init_state.get("model_params"):
                merged_state["model_params"] = init_state["model_params"]
            merged_state["state_version"] = int(pl.get("state_version", 0) or 0)
            # Reset routing markers for a clean new-turn start
            merged_state.pop("from_node", None)
            merged_state.pop("prev_node", None)
            init_state = merged_state
        else:
            # New thread: ensure version starts at 0
            init_state["state_version"] = int(init_state.get("state_version", 0) or 0)

    config = {
        "configurable": {
            # LangGraph uses "thread_id" to identify sessions/checkpoints
            "thread_id": thread_id,
        },
        # 显式限制单次调用的递归/步数，避免在 clarifying 状态下循环
        "recursion_limit": 8,
    }

    # 统一执行路径：直接 stream 执行一轮，然后从 checkpointer 读取最新状态
    try:
        for _ in compiled_graph.stream(init_state, config=config, stream_mode="values"):
            pass
        current = compiled_graph.get_state({"configurable": {"thread_id": thread_id}})
        result_state = current.values if hasattr(current, "values") else init_state
    except Exception as ex:
        import traceback
        print(f"[submit] Graph execution error: {ex}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"graph execution failed: {ex}")

    # Update snapshot repository for /v1/poll and /v1/state
    try:
        state_repo.upsert(result_state)
    except Exception:
        pass

    # Shape HTTP response
    try:
        return SubmitResponse.from_graph_state(result_state)
    except Exception as ex:
        import traceback, orjson as _orjson
        print("[submit] Response build error:", ex)
        try:
            print("[submit] result_state keys:", list(result_state.keys()))
            print("[submit] result_state sample:", _orjson.dumps({k: result_state.get(k) for k in ["thread_id","state_version","current_status","requirements_document"]}).decode())
        except Exception:
            pass
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"response build failed: {ex}")


@app.get("/v1/poll", response_model=PollResponse)
def poll(
    thread_id: str = Query(..., description="Session/thread id"),
    client_state_version: int = Query(..., ge=0, description="Client-side last known state version"),
) -> PollResponse:
    """Polling endpoint to check if server-side state_version has advanced."""
    snapshot = state_repo.get(thread_id)
    if not snapshot:
        return PollResponse(
            thread_id=thread_id,
            client_state_version=client_state_version,
            current_state_version=client_state_version,
            has_update=False,
        )
    cur = int(snapshot.get("state_version", 0))
    return PollResponse(
        thread_id=thread_id,
        client_state_version=client_state_version,
        current_state_version=cur,
        has_update=(cur > client_state_version),
    )


@app.get("/v1/state", response_model=StateResponse)
def get_state(thread_id: str = Query(..., description="Session/thread id")) -> StateResponse:
    """Return the full current snapshot for a given thread_id."""
    snapshot = state_repo.get(thread_id)
    if not snapshot:
        # Try reading from graph/checkpointer as a secondary source
        try:
            current = compiled_graph.get_state({"configurable": {"thread_id": thread_id}})
            snapshot = current.values if hasattr(current, "values") else None
        except Exception:
            snapshot = None

    if not snapshot:
        raise HTTPException(status_code=404, detail="Thread not found")

    return StateResponse.from_graph_state(snapshot)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "redis": bool(get_redis_url()),
        "pid": os.getpid(),
    }