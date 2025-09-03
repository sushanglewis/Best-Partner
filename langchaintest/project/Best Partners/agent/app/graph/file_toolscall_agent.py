from __future__ import annotations

import json
import os
from typing import Any, Dict

from langchain_core.runnables import RunnableConfig
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.graph.state import RequirementsValidationState
from app.services.llm import get_chat_model
from app.prompt.file_toolscall_agent_prompt import (
    FILE_TOOLSCALL_SYSTEM,
    FILE_TOOLSCALL_HUMAN,
)

# Prompt: system + human
prompt = ChatPromptTemplate.from_messages([
    ("system", FILE_TOOLSCALL_SYSTEM),
    ("human", FILE_TOOLSCALL_HUMAN),
])


def _build_llm_input(state: RequirementsValidationState) -> dict:
    messages = state.get("messages", [])
    latest = messages[-1] if messages else {"message_content": ""}
    files = state.get("multi_files", [])
    return {
        "human_message": latest.get("message_content", ""),
        "available_files": [
            {
                "file_id": f.get("file_id"),
                "file_name": f.get("file_name"),
                "file_type": f.get("file_type"),
                "file_size": f.get("file_size"),
                "file_path": f.get("file_path"),
                "has_content": bool(f.get("file_content")),
            }
            for f in files
        ],
    }


def file_toolscall_agent(state: RequirementsValidationState, config: RunnableConfig) -> RequirementsValidationState:
    files_by_id = {f.get("file_id"): f for f in state.get("multi_files", [])}

    # 最近一条 human_message 的 message_id
    latest = (state.get("messages") or [{}])[-1]
    current_message_id = latest.get("message_id")

    # 检查是否可用外部 LLM
    mp = state.get("model_params", {}) or {}
    api_key = mp.get("api_key") or os.getenv("OPENAI_API_KEY")

    if api_key:
        # 单轮 LLM 规划：根据当前状态规划一次需要提取的文件
        llm = get_chat_model(mp)
        chain = prompt | llm | StrOutputParser()

        llm_input = _build_llm_input({**state, "multi_files": list(files_by_id.values())})
        raw_output = chain.invoke(llm_input)

        commands = []
        try:
            data = json.loads(raw_output)
            commands = data.get("commands", [])
        except Exception:
            commands = []

        for cmd in commands:
            if cmd.get("tool") != "file_extract":
                continue
            fid = cmd.get("file_id")
            f = files_by_id.get(fid)
            if not f:
                continue
            # 幂等：已有内容则跳过
            if f.get("file_content"):
                continue
            # 仅处理当前 human_message 关联的文件或未提取过的文件
            if f.get("message_id") not in (None, current_message_id):
                continue

            # 执行“文件提取”工具（占位实现由 tools.py 负责）
            from app.services.tools import FileTools

            try:
                extracted = FileTools.extract_file(
                    file_path=cmd.get("file_path") or f.get("file_path"),
                    file_type=cmd.get("file_type") or f.get("file_type"),
                )
                f["file_content"] = extracted
                f["error"] = None
            except Exception as e:
                f["error"] = str(e)

        # 将更新写回 state
        state["multi_files"] = list(files_by_id.values())
        return state

    # 无外部 LLM：启用兜底策略（最多处理 3 个尚未提取的文本/代码类文件）
    from app.services.tools import FileTools

    picked = 0
    for f in files_by_id.values():
        if picked >= 3:
            break
        if f.get("file_content"):
            continue
        ft = (f.get("file_type") or "").lower()
        if any(t in ft for t in ["text", "markdown", "md", "json", "yaml", "yml", "xml", "csv", "python", "typescript", "javascript", "java", "go", "rust", "c", "cpp"]):
            try:
                extracted = FileTools.extract_file(file_path=f.get("file_path"), file_type=f.get("file_type"))
                f["file_content"] = extracted
                f["error"] = None
                picked += 1
            except Exception as e:
                f["error"] = str(e)

    state["multi_files"] = list(files_by_id.values())
    return state