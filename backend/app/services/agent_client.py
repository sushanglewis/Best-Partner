import os
import httpx
from typing import Any, Dict, List
from ..schemas.requirements import SubmitRequest

class AgentClient:
    def __init__(self):
        # 固定端口一致性：默认指向 2024，允许通过环境变量覆盖
        self.base = os.getenv("AGENT_BASE_URL", "http://127.0.0.1:2024")
        self.client = httpx.AsyncClient(timeout=30.0)

    async def submit(self, payload: dict):
        # Map backend payload to Agent's SubmitRequest shape
        files_in: List[Dict[str, Any]] = []
        for f in (payload.get("file_info") or []):
            fp = f.get("file_path")
            ft = f.get("file_type")
            # Agent requires file_path and file_type for each file; skip invalid ones
            if not fp:
                continue
            files_in.append({
                "file_id": f.get("file_id"),
                "file_name": f.get("file_name"),
                "file_type": ft or "unknown",
                "file_size": f.get("file_size"),
                "file_path": fp,
            })
        data = {
            "user_id": payload.get("user_id"),
            "human_message": payload.get("human_message"),
            "timestamp": payload.get("timestamp"),
            "thread_id": payload.get("thread_id"),
            "state_version": payload.get("state_version"),
            "message_id": payload.get("message_id"),
            "current_status": payload.get("current_status"),
            "model_params": payload.get("model_params") or None,
            "files": files_in if files_in else None,
            # 新增：预载状态（来自 PostgreSQL），仅当 Agent 无旧状态时用于恢复上下文
            "preload_state": payload.get("preload_state") or None,
        }
        r = await self.client.post(f"{self.base}/v1/submit", json=data)
        r.raise_for_status()
        return r.json()

    async def poll(self, thread_id: str, state_version: int):
        # 注意：Agent 的参数名为 client_state_version
        r = await self.client.get(
            f"{self.base}/v1/poll", params={"thread_id": thread_id, "client_state_version": state_version}
        )
        r.raise_for_status()
        return r.json()

    async def state(self, thread_id: str):
        r = await self.client.get(f"{self.base}/v1/state", params={"thread_id": thread_id})
        r.raise_for_status()
        return r.json()

agent_client = AgentClient()