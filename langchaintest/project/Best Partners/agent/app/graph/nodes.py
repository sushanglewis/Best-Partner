from __future__ import annotations

import uuid
from datetime import datetime
from typing import List

from langchain_core.runnables import RunnableConfig
# REMOVED: from langgraph.types import interrupt as lg_interrupt

from app.graph.state import RequirementsValidationState, FileInfo


# ============
# Helper utils
# ============


def uuid6_like() -> str:
    # A simple UUID4 placeholder; production can swap with real uuid6 impl
    return uuid.uuid4().hex


# ======
# Nodes (shared/basic)
# ======


def start(state: RequirementsValidationState, config: RunnableConfig) -> RequirementsValidationState:
    now = datetime.utcnow().isoformat()
    thread_id = state.get("thread_id") or uuid6_like()
    # Only initialize; do not bump version here
    state_version = int(state.get("state_version", 0))
    current_status = state.get("current_status") or "clarifying"

    # Normalize messages: ensure the incoming latest user message has a proper id and timestamp
    messages = state.get("messages", [])
    if messages:
        m = messages[-1]
        m["message_id"] = m.get("message_id") if m.get("message_id") and m.get("message_id") != "auto" else uuid6_like()
        m["timestamp"] = m.get("timestamp") or now
        m["message_role"] = m.get("message_role") or "user"
        m["message_content"] = m.get("message_content") or ""
        messages = [m]
    else:
        # 若没有传入消息，则构造一条空的人类消息以保证流程
        messages = [{
            "message_id": uuid6_like(),
            "message_role": "user",
            "message_content": "",
            "timestamp": now,
        }]

    # user_id/model_params 透传
    user_id = state.get("user_id") or ""
    model_params = state.get("model_params") or {}

    new_state = {
        **state,
        "thread_id": thread_id,
        "user_id": user_id,
        "state_version": state_version,
        "current_status": current_status,
        "messages": messages,
        "model_params": model_params,
        # 从 start 路由进入 input_processor 不中断
        "interrupt": False,
    }
    try:
        print(f"[nodes.start] init thread={thread_id}, state_version={state_version}, status={current_status}")
    except Exception:
        pass
    return new_state


def input_processor(state: RequirementsValidationState, config: RunnableConfig) -> RequirementsValidationState:
    # 进入来源判定（当前实现不再触发 LangGraph 中断，直接透传）
    from_node = state.get("from_node")
    prev_node = state.get("prev_node")
    came_from_start = (prev_node == "start") or (from_node == "start")
    came_from_analysis = (prev_node == "requirements_analysis_agent") or (from_node == "requirements_analysis_agent")

    # 默认/首次进入：来自 start 或分析节点回流，均不中断，继续使用请求态中的最近一条消息与文件
    messages = state.get("messages", [])
    if not messages:
        return state
    latest = messages[-1]

    current_message_id = latest.get("message_id") or uuid6_like()

    # 将 multi_files 绑定到本轮 message_id，并去重
    files = state.get("multi_files", [])
    seen = set()
    new_files: List[FileInfo] = []
    for f in files:
        fid = f.get("file_id")
        if not fid or fid in seen:
            continue
        seen.add(fid)
        f = {**f, "message_id": current_message_id}
        new_files.append(f)

    trimmed_messages = [latest]

    # 根据来源与状态决定是否中断，匹配设计文档：
    # - 首轮（来自 start）：不中断，继续执行 file_toolscall_agent
    # - 从 requirements_analysis_agent 回流且 current_status=clarifying：中断，等待下一轮用户输入
    status = state.get("current_status") or "clarifying"
    should_interrupt = bool(came_from_analysis and status != "completed")

    new_state = {
        **state,
        "messages": trimmed_messages,
        "multi_files": new_files,
        "interrupt": should_interrupt,
    }
    try:
        print(
            f"[nodes.input_processor] from={from_node}, prev={prev_node}, "
            f"came_from_start={came_from_start}, came_from_analysis={came_from_analysis}, "
            f"status={status}, set interrupt={new_state.get('interrupt')}"
        )
    except Exception:
        pass
    return new_state


def end(state: RequirementsValidationState, config: RunnableConfig) -> RequirementsValidationState:
    return state