from pydantic import BaseModel, Field
from typing import List, Optional

class FileInfo(BaseModel):
    file_id: str
    file_name: str
    file_type: Optional[str] = None
    file_size: Optional[int] = None
    file_path: Optional[str] = None

class SubmitRequest(BaseModel):
    user_id: str
    human_message: str
    timestamp: str
    file_info: Optional[List[FileInfo]] = Field(default=None)
    thread_id: Optional[str] = None
    state_version: Optional[int] = None
    message_id: Optional[str] = None
    current_status: Optional[str] = None
    model_params: Optional[dict] = None

class SubmitResponse(BaseModel):
    thread_id: str
    state_version: int
    current_status: str
    requirements_document: Optional[dict] = None
    question_list: List[dict] = []
    messages: List[dict] = []
    multi_files: List[dict] = []

class PollResponse(BaseModel):
    thread_id: str
    client_state_version: int
    current_state_version: int
    has_update: bool

class StateResponse(SubmitResponse):
    # Aggregated thread data (optional) for returning all versions under a thread_id
    versions: List[str] = []
    # Each document item: {version: str, content: str, last_updated: str, current_status: Optional[str]}
    documents: List[dict] = []