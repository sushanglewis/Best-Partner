from __future__ import annotations

from typing import List, Literal, Optional, TypedDict

# ===============
# LangGraph State
# ===============


class Message(TypedDict):
    message_id: str
    message_role: Literal["user", "assistant", "system"]
    message_content: str
    timestamp: str  # ISO string


class SuggestionOption(TypedDict):
    option_id: str
    content: str
    selected: bool


class Question(TypedDict):
    question_id: str
    content: str
    suggestion_options: List[SuggestionOption]


class FileInfo(TypedDict, total=False):
    file_id: str
    message_id: str
    file_name: str
    file_type: str
    file_size: int
    file_path: str
    file_content: str
    extract_error: str


class RequirementsDocument(TypedDict):
    version: str
    content: str
    last_updated: str  # YYYY-MM-DD


# 显式定义模型参数结构，遵循项目命名规范（provider/base_url/api_key/temperature/model/max_tokens）
class ModelParams(TypedDict, total=False):
    # 供应商标识（统一使用英文小写）：
    # openai｜deepseek｜moonshot（“月之暗面”）｜qwen（“通义千问”）｜doubao（“豆包”）｜hunyuan（“腾讯混元”）
    provider: str
    base_url: Optional[str]
    api_key: Optional[str]
    model: Optional[str]
    temperature: Optional[float]
    max_tokens: Optional[int]


class RequirementsValidationState(TypedDict, total=False):
    thread_id: str
    user_id: str
    state_version: int
    current_status: Literal["clarifying", "completed"]
    messages: List[Message]
    question_list: List[Question]
    requirements_document: RequirementsDocument
    multi_files: List[FileInfo]
    model_params: ModelParams
    # When True, graph should stop after input_processor and wait for next user input
    interrupt: bool