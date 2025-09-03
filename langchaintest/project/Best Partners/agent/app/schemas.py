from __future__ import annotations

from datetime import datetime, date
from typing import List, Literal, Optional
from pydantic import BaseModel, Field, root_validator

# ====================
# Pydantic HTTP Schemas
# ====================


class ModelParams(BaseModel):
    provider: Optional[str] = Field(None, description="LLM Provider (e.g., openai, azure, etc.)")
    base_url: Optional[str] = None
    model: Optional[str] = None
    temperature: Optional[float] = 0.2
    max_tokens: Optional[int] = 1024
    # 新增：服务间临时转发使用的密钥字段（仅在后端->Agent之间传递，不回显给前端）
    api_key: Optional[str] = None


class FileInfoIn(BaseModel):
    file_id: str
    file_name: str
    file_type: str
    file_size: Optional[int] = None
    file_path: str


class SuggestionOption(BaseModel):
    option_id: str
    content: str
    selected: bool = False


class QuestionOut(BaseModel):
    question_id: str
    content: str
    suggestion_options: List[SuggestionOption]


class RequirementsDocumentOut(BaseModel):
    version: str
    content: str
    last_updated: date


class MessageOut(BaseModel):
    message_id: str
    message_role: Literal["user", "assistant", "system"]
    message_content: str
    timestamp: datetime


class FileInfoOut(FileInfoIn):
    message_id: Optional[str] = None
    file_content: Optional[str] = None
    extract_error: Optional[str] = None


class SubmitRequest(BaseModel):
    user_id: str
    human_message: str
    timestamp: datetime
    files: Optional[List[FileInfoIn]] = None
    thread_id: Optional[str] = None
    state_version: Optional[int] = None
    message_id: Optional[str] = None
    current_status: Optional[Literal["clarifying", "completed"]] = None
    model_params: Optional[ModelParams] = None
    # 新增：可选预载状态（仅用于服务端内部合并，不直接进入初始状态）
    preload_state: Optional[dict] = None

    def to_graph_state(self) -> dict:
        if not self.human_message:
            raise ValueError("human_message is required")
        return {
            "thread_id": self.thread_id,
            "state_version": self.state_version if self.state_version is not None else 0,
            "current_status": self.current_status or "clarifying",
            "messages": [
                {
                    "message_id": self.message_id or "auto",  # real id finalized in start node
                    "message_role": "user",
                    "message_content": self.human_message,
                    "timestamp": self.timestamp.isoformat(),
                }
            ],
            # 不再在此处重置问题与需求文档，避免覆盖已有状态
            # "question_list": [],
            # "requirements_document": {
            #     "version": "0.0",
            #     "content": "",
            #     "last_updated": date.today().isoformat(),
            # },
            "multi_files": [f.dict() for f in (self.files or [])],
            "model_params": self.model_params.dict() if self.model_params else {},
        }


class SubmitResponse(BaseModel):
    thread_id: str
    state_version: int
    current_status: Literal["clarifying", "completed"]
    requirements_document: RequirementsDocumentOut
    question_list: List[QuestionOut]
    messages: List[MessageOut]
    multi_files: List[FileInfoOut]

    @classmethod
    def from_graph_state(cls, state: dict) -> "SubmitResponse":
        # Normalize messages timestamps
        def parse_ts(m):
            ts = m.get("timestamp")
            if isinstance(ts, str):
                s = ts
                # Support RFC3339/ISO8601 with trailing 'Z' (UTC)
                if s.endswith("Z"):
                    s = s[:-1] + "+00:00"
                try:
                    return datetime.fromisoformat(s)
                except Exception:
                    # Best-effort: return original string if parsing fails; Pydantic will attempt coercion
                    return s  # type: ignore
            return ts

        return cls(
            thread_id=state.get("thread_id"),
            state_version=int(state.get("state_version", 0)),
            current_status=state.get("current_status", "clarifying"),
            requirements_document=RequirementsDocumentOut(
                version=state["requirements_document"]["version"],
                content=state["requirements_document"]["content"],
                last_updated=datetime.fromisoformat(state["requirements_document"]["last_updated"]).date()
                if isinstance(state["requirements_document"]["last_updated"], str)
                else state["requirements_document"]["last_updated"],
            ),
            question_list=[QuestionOut(**q) for q in state.get("question_list", [])],
            messages=[
                MessageOut(
                    message_id=m.get("message_id"),
                    message_role=m.get("message_role"),
                    message_content=m.get("message_content"),
                    timestamp=parse_ts(m),
                )
                for m in state.get("messages", [])
            ],
            multi_files=[FileInfoOut(**f) for f in state.get("multi_files", [])],
        )


class PollResponse(BaseModel):
    thread_id: str
    client_state_version: int
    current_state_version: int
    has_update: bool


class StateResponse(SubmitResponse):
    @classmethod
    def from_graph_state(cls, state: dict) -> "StateResponse":
        return cls(**SubmitResponse.from_graph_state(state).dict())