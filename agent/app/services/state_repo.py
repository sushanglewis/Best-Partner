from __future__ import annotations

from typing import Dict, Optional
from threading import RLock


class StateRepository:
    """A minimal in-memory state snapshot repository.

    - Stores the latest state per thread_id for quick /v1/poll and /v1/state access.
    - In a production setup, this can be replaced or supplemented by DB persistence.
    """

    def __init__(self) -> None:
        self._store: Dict[str, dict] = {}
        self._lock = RLock()

    def upsert(self, state: dict) -> None:
        thread_id = state.get("thread_id")
        if not thread_id:
            return
        with self._lock:
            self._store[thread_id] = state

    def get(self, thread_id: str) -> Optional[dict]:
        with self._lock:
            return self._store.get(thread_id)