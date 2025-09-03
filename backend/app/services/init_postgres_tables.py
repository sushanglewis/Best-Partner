import os
import sys
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

"""
基于《最佳拍档整体方案v1.0.md》中 PostgreSQL 设计，创建以下表：
- sessions
- messages
- questions
- suggestion_options
- requirements_documents
- multi_file

使用方法：
  1) 确保已设置环境变量 DATABASE_URL（postgresql+asyncpg）
  2) 在 backend 目录的虚拟环境下运行：
     python -m app.services.init_postgres_tables
"""

DDL_STATEMENTS = [
    # sessions
    """
    CREATE TABLE IF NOT EXISTS sessions (
        thread_id UUID PRIMARY KEY,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        current_status VARCHAR(20) NOT NULL DEFAULT 'clarifying'
    );
    """,
    # messages
    """
    CREATE TABLE IF NOT EXISTS messages (
        message_id UUID PRIMARY KEY,
        thread_id UUID REFERENCES sessions(thread_id) ON DELETE CASCADE,
        role VARCHAR(10) NOT NULL,
        content TEXT NOT NULL,
        timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        metadata JSONB NULL
    );
    """,
    # questions
    """
    CREATE TABLE IF NOT EXISTS questions (
        question_id UUID PRIMARY KEY,
        thread_id UUID REFERENCES sessions(thread_id) ON DELETE CASCADE,
        content TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """,
    # suggestion_options
    """
    CREATE TABLE IF NOT EXISTS suggestion_options (
        option_id UUID PRIMARY KEY,
        question_id UUID REFERENCES questions(question_id) ON DELETE CASCADE,
        content TEXT NOT NULL,
        selected BOOLEAN NOT NULL DEFAULT FALSE
    );
    """,
    # requirements_documents
    """
    CREATE TABLE IF NOT EXISTS requirements_documents (
        document_id UUID PRIMARY KEY,
        thread_id UUID REFERENCES sessions(thread_id) ON DELETE CASCADE,
        version VARCHAR(20) NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        current_status VARCHAR(20) NOT NULL DEFAULT 'clarifying'
    );
    """,
    # multi_file
    """
    CREATE TABLE IF NOT EXISTS multi_file (
        file_id UUID PRIMARY KEY,
        message_id UUID NOT NULL,
        thread_id UUID REFERENCES sessions(thread_id) ON DELETE CASCADE,
        file_name TEXT NOT NULL,
        file_type TEXT NOT NULL,
        file_content TEXT NULL,
        file_path TEXT NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    );
    """,
    # helpful indexes
    """
    CREATE INDEX IF NOT EXISTS idx_messages_thread_id ON messages(thread_id);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_questions_thread_id ON questions(thread_id);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_suggestion_options_question_id ON suggestion_options(question_id);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_requirements_documents_thread_id ON requirements_documents(thread_id);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_multi_file_thread_id ON multi_file(thread_id);
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_multi_file_message_id ON multi_file(message_id);
    """,
]

async def init_tables(database_url: str) -> None:
    engine = create_async_engine(database_url, echo=False, future=True)
    try:
        async with engine.begin() as conn:
            for stmt in DDL_STATEMENTS:
                await conn.execute(text(stmt))
    finally:
        await engine.dispose()

async def _amain() -> None:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("[ERROR] DATABASE_URL 未设置，请先在终端导出环境变量后再运行本脚本。", file=sys.stderr)
        sys.exit(1)
    await init_tables(database_url)
    print("[OK] PostgreSQL 基础表已初始化/存在即跳过。")

if __name__ == "__main__":
    asyncio.run(_amain())