from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any, Dict, List
from uuid import uuid4, UUID

from langchain_core.runnables import RunnableConfig
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

from app.graph.state import RequirementsValidationState
from app.services.llm import get_chat_model
from app.prompt.requirements_analysis_agent_prompt import (
    REQUIREMENTS_SYSTEM,
    REQUIREMENTS_HUMAN,
)

# 载入 prompt
prompt = ChatPromptTemplate.from_messages([
    ("system", REQUIREMENTS_SYSTEM),
    ("human", REQUIREMENTS_HUMAN),
])


def _is_uuid(value: Any) -> bool:
    try:
        UUID(str(value))
        return True
    except Exception:
        return False


def _uuid() -> str:
    return str(uuid4())


## 获取最新的需求文档
def _ensure_requirements_document(d: Dict[str, Any]) -> Dict[str, Any]:
    # 基础兜底，确保必要字段存在且类型正确
    version = str(d.get("version") or "0.1")
    last_updated = d.get("last_updated")
    if not last_updated:
        last_updated = datetime.utcnow().strftime("%Y-%m-%d")
    content = d.get("content")
    if isinstance(content, (dict, list)):
        try:
            content = json.dumps(content, ensure_ascii=False)
        except Exception:
            content = str(content)
    if content is None:
        content = ""
    return {"version": version, "last_updated": last_updated, "content": content}


def _build_llm_input(state: RequirementsValidationState) -> Dict[str, Any]:
    """构造 LLM 输入上下文
    要求：
    1) 文件列表（含内容与错误信息）：来自 state.multi_files；
    2) 当前文档：仅 requirements_document.content；
    3) 当前状态：state.current_status；
    4) 版本：state.state_version。
    """
    messages = state.get("messages", [])
    latest = messages[-1] if messages else {"message_content": ""}

    # 1) 文件列表（原始结构，避免丢失字段；如含文本内容过长，可由上游裁剪）
    files = state.get("multi_files", []) or []
    files_json = json.dumps(files, ensure_ascii=False, indent=2)

    # 2) 当前文档：仅 content
    current_doc = state.get("requirements_document") or {}
    current_doc_content = current_doc.get("content") if isinstance(current_doc, dict) else None
    if current_doc_content is None:
        current_doc_content = "无现有文档"

    return {
        "human_message": latest.get("message_content", ""),
        "files": files_json,
        "current_document": current_doc_content,
        "current_status": state.get("current_status", "clarifying"),
        "state_version": state.get("state_version", 0),
    }


def _validate_and_fix_json_output(raw_output: str) -> Dict[str, Any]:
    """验证并修复 LLM 输出的 JSON 结构。关键点：
    - 统一将 question_id/option_id 修正为 UUIDv4 字符串（带连字符的 canonical 形式）。
    - 始终产出恰好 3 个问题，每题 3 个选项。
    """
    try:
        data = json.loads(raw_output.strip())
    except json.JSONDecodeError:
        # JSON 解析失败，返回占位结构（内部已使用 UUID）
        return _create_fallback_response()
    
    # 验证必需字段
    if not isinstance(data, dict):
        return _create_fallback_response()
    
    # 验证 requirements_document
    req_doc = data.get("requirements_document", {})
    if not isinstance(req_doc, dict) or not all(k in req_doc for k in ["version", "content", "last_updated"]):
        req_doc = {
            "version": "0.1", 
            "content": "文档生成失败，请重试", 
            "last_updated": datetime.utcnow().strftime("%Y-%m-%d")
        }
        data["requirements_document"] = req_doc
    else:
        # 规范化文档字段
        data["requirements_document"] = _ensure_requirements_document(req_doc)
    
    # 验证 question_list
    questions = data.get("question_list", [])
    if not isinstance(questions, list) or len(questions) != 3:
        questions = _create_fallback_questions()
    else:
        # 验证每个问题的结构
        fixed_questions = []
        for i, q in enumerate(questions[:3]):
            if not isinstance(q, dict):
                fixed_questions.append(_create_fallback_question())
                continue
            
            # question 基础字段
            qid = q.get("question_id")
            if not _is_uuid(qid):
                qid = _uuid()
            content = q.get("content") or f"问题 {i+1}"
            question = {
                "question_id": qid,
                "content": content,
                "suggestion_options": []
            }
            
            # 验证选项
            options = q.get("suggestion_options", [])
            if not isinstance(options, list) or len(options) != 3:
                question["suggestion_options"] = _create_fallback_options()
            else:
                fixed_options = []
                for j, opt in enumerate(options[:3]):
                    if isinstance(opt, dict) and all(k in opt for k in ["option_id", "content", "selected"]):
                        oid = opt.get("option_id")
                        if not _is_uuid(oid):
                            oid = _uuid()
                        fixed_options.append({
                            "option_id": oid,
                            "content": opt.get("content") or f"选项 {j+1}",
                            "selected": bool(opt.get("selected", False))
                        })
                    else:
                        fixed_options.append({
                            "option_id": _uuid(),
                            "content": f"选项 {j+1}",
                            "selected": False
                        })
                question["suggestion_options"] = fixed_options
            
            fixed_questions.append(question)
        
        questions = fixed_questions
    
    data["question_list"] = questions
    
    # 验证 current_status
    status = data.get("current_status", "clarifying")
    if status not in ["clarifying", "completed"]:
        status = "clarifying"
    data["current_status"] = status
    
    return data


def _create_fallback_response() -> Dict[str, Any]:
    """创建兜底响应（使用 UUIDv4 作为 ID）。"""
    return {
        "requirements_document": {
            "version": "0.1",
            "content": "文档生成失败，请重试或提供更详细信息",
            "last_updated": datetime.utcnow().strftime("%Y-%m-%d")
        },
        "question_list": _create_fallback_questions(),
        "current_status": "clarifying"
    }


def _create_fallback_questions() -> List[Dict[str, Any]]:
    """创建兜底问题列表（3题，每题3个选项，全部使用 UUID）。"""
    return [
        _create_fallback_question(),
        _create_fallback_question(), 
        _create_fallback_question()
    ]


def _create_fallback_question(question_id: str | None = None) -> Dict[str, Any]:
    """创建单个兜底问题（使用 UUIDv4）。"""
    return {
        "question_id": question_id if (question_id and _is_uuid(question_id)) else _uuid(),
        "content": "请提供更多详细信息以便我们更好地理解您的需求？",
        "suggestion_options": _create_fallback_options()
    }


def _create_fallback_options() -> List[Dict[str, Any]]:
    """创建兜底选项（3个，使用 UUIDv4）。"""
    return [
        {"option_id": _uuid(), "content": "选项 1", "selected": False},
        {"option_id": _uuid(), "content": "选项 2", "selected": False},
        {"option_id": _uuid(), "content": "选项 3", "selected": False}
    ]


def requirements_analysis_agent(state: RequirementsValidationState, config: RunnableConfig) -> RequirementsValidationState:
    """
    需求分析智能体节点
    
    功能：
    1. 分析用户输入和文件内容
    2. 更新需求文档
    3. 生成结构化澄清问题（每个问题3个选项）
    4. 判断是否需要继续澄清
    """
    # 检查是否有可用的 LLM 配置
    mp = state.get("model_params", {}) or {}
    api_key = mp.get("api_key") or os.getenv("DASHSCOPE_API_KEY") or os.getenv("OPENAI_API_KEY")
    
    if not api_key:
        # 无 LLM 配置，使用占位实现
        return _create_placeholder_response(state)
    
    try:
        # 使用真实 LLM 生成结构化输出
        llm = get_chat_model(mp)
        chain = prompt | llm | StrOutputParser()
        
        llm_input = _build_llm_input(state)
        raw_output = chain.invoke(llm_input)
        
        # 验证并修复 JSON 输出（含 UUID 统一）
        result_data = _validate_and_fix_json_output(raw_output)
        
    except Exception as e:
        # LLM 调用失败，使用占位实现
        print(f"[requirements_analysis_agent] LLM error: {e}")
        return _create_placeholder_response(state)
    
    # 构造新的助手消息
    messages = state.get("messages", [])
    last_user = None
    for m in reversed(messages):
        if m.get("message_role") == "user":
            last_user = m
            break
    
    new_assistant_msg = {
        "message_id": str(uuid4()).replace("-", ""),
        "message_role": "assistant",
        "message_content": "我已更新需求文档并准备了澄清问题，请查看并提供反馈。",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    
    new_messages = []
    if last_user:
        new_messages.append(last_user)
    new_messages.append(new_assistant_msg)
    
    return {
        "requirements_document": result_data["requirements_document"],
        "question_list": result_data["question_list"],
        "current_status": result_data["current_status"],
        "state_version": (state.get("state_version", 0) + 1),
        "messages": new_messages,
    }


def _create_placeholder_response(state: RequirementsValidationState) -> Dict[str, Any]:
    """创建占位响应（无 LLM 时使用，统一 UUID）。"""
    messages = state.get("messages", [])
    last_user = None
    for m in reversed(messages):
        if m.get("message_role") == "user":
            last_user = m
            break
    
    # 构造占位文档
    today = datetime.utcnow().strftime("%Y-%m-%d")
    prev_doc = state.get("requirements_document")
    prev_version = "0.0"
    if prev_doc:
        prev_version = prev_doc.get("version", "0.0")
    
    try:
        major, minor = prev_version.split(".")
        version = f"{major}.{int(minor) + 1}"
    except Exception:
        version = "0.1"
    
    user_input = last_user.get("message_content", "") if last_user else ""
    files_count = len(state.get("multi_files", []))

    # 如果用户明确要求直接完成/终止澄清，则占位分支也应置为 completed
    text_lc = (user_input or "").lower()
    force_keywords = [
        "直接输出", "无需继续澄清", "就这样", "强制输出", "直接完成", "终止澄清", "不需要澄清", "完成", "提交", "不用问了",
        "stop clarifying", "just output", "force output", "finalize", "complete now"
    ]
    status = "completed" if any(k.lower() in text_lc for k in force_keywords) else "clarifying"
    
    new_doc = {
        "version": version,
        "content": f"需求文档草稿（占位） - {today}\n- 输入摘要: {user_input}\n- 文件数: {files_count}",
        "last_updated": today,
    }
    
    # 构造占位问题（统一 UUID）
    questions = [
        {
            "question_id": _uuid(),
            "content": "请确认目标用户与使用场景？",
            "suggestion_options": [
                {"option_id": _uuid(), "content": "个人用户", "selected": False},
                {"option_id": _uuid(), "content": "企业用户", "selected": False},
                {"option_id": _uuid(), "content": "混合用户", "selected": False}
            ]
        },
        {
            "question_id": _uuid(),
            "content": "是否有性能/安全等非功能性要求？",
            "suggestion_options": [
                {"option_id": _uuid(), "content": "高性能要求", "selected": False},
                {"option_id": _uuid(), "content": "高安全要求", "selected": False},
                {"option_id": _uuid(), "content": "标准要求", "selected": False}
            ]
        },
        {
            "question_id": _uuid(),
            "content": "交付时间与优先级如何？",
            "suggestion_options": [
                {"option_id": _uuid(), "content": "紧急交付", "selected": False},
                {"option_id": _uuid(), "content": "标准周期", "selected": False},
                {"option_id": _uuid(), "content": "充足时间", "selected": False}
            ]
        }
    ]
    
    new_assistant_msg = {
        "message_id": str(uuid4()).replace("-", ""),
        "message_role": "assistant",
        "message_content": "我已更新需求文档草稿，并提出了3个澄清问题，请逐一确认。",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
    
    new_messages = []
    if last_user:
        new_messages.append(last_user)
    new_messages.append(new_assistant_msg)
    
    return {
        "requirements_document": new_doc,
        "question_list": questions,
        "current_status": status,
        "state_version": (state.get("state_version", 0) + 1),
        "messages": new_messages,
    }