from __future__ import annotations

import time
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


class FileExtractionError(Exception):
    pass


class FileTools:
    """Placeholder for MCP/External tools to extract text from a file path.

    For now, we simply read small text-like files; for non-text, we return a stub message.
    This class is designed to be replaced with real tools (MCP, parsers, etc.).
    """

    @retry(reraise=True, stop=stop_after_attempt(3), wait=wait_exponential(multiplier=0.5, min=0.5, max=4), retry=retry_if_exception_type(FileExtractionError))
    def extract_file(self, file_path: str) -> str:
        try:
            # Very naive extractor: only for small text files
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            if not content:
                raise FileExtractionError("empty file content")
            # limit content size to prevent context explosion
            if len(content) > 8000:
                return content[:8000] + "\n... [truncated]"
            return content
        except Exception as e:
            raise FileExtractionError(str(e))


file_tools = FileTools()