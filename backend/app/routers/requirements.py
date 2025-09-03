from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..schemas.requirements import SubmitRequest, SubmitResponse, PollResponse, StateResponse
from ..services.agent_client import agent_client
import time
import os
import uuid
import json
from datetime import datetime
from typing import Optional

# 新增：从模型配置表读取当前激活配置
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from ..routers.models import ModelSetting, ModelActive, _Session, _ensure_db_initialized, _decrypt
# 新增：业务表初始化（若尚未创建）
from ..services.init_postgres_tables import init_tables

router = APIRouter(tags=["requirements"]) 

# 业务表一次性初始化标记
_BIZ_TABLES_READY = False


def _norm_uuid(u: Optional[str]) -> Optional[str]:
    if not u:
        return None
    try:
        # 支持 32 位 hex（无连字符）与标准 UUID
        return str(uuid.UUID(u))
    except Exception:
        return None


def _parse_ts(s: Optional[str]) -> Optional[datetime]:
    if not s:
        return None
    try:
        v = s
        if isinstance(v, str) and v.endswith("Z"):
            v = v[:-1] + "+00:00"
        return datetime.fromisoformat(v)  # type: ignore[arg-type]
    except Exception:
        return None


async def _ensure_biz_tables() -> None:
    global _BIZ_TABLES_READY
    if _BIZ_TABLES_READY:
        return
    await _ensure_db_initialized()  # 确保模型相关表已初始化（与会话工厂可用）
    db_url = os.getenv("DATABASE_URL", "").strip()
    # 兼容误填 postgresql:// —— 自动升级为 postgresql+asyncpg://
    if db_url.startswith("postgresql://"):
        db_url = "postgresql+asyncpg://" + db_url[len("postgresql://"):]
    if db_url:
        try:
            await init_tables(db_url)
        except Exception:
            # 若创建失败（例如权限不足/已存在），不阻断；后续写入若失败再回报
            pass
    _BIZ_TABLES_READY = True


async def _persist_state(data: dict) -> None:
    """将 Agent 返回的状态快照持久化到 PostgreSQL。
    要求：DATABASE_URL 为 postgresql+asyncpg，且 _Session 可用。
    """
    if _Session is None:
        return
    thread_id_raw = data.get("thread_id")
    tid = _norm_uuid(thread_id_raw)
    if not tid:
        return

    current_status = data.get("current_status") or "clarifying"

    await _ensure_biz_tables()
    async with _Session() as session:  # type: ignore[arg-type]
        # 1) sessions：upsert 当前状态并更新更新时间
        await session.execute(
            text(
                """
                INSERT INTO sessions(thread_id, current_status)
                VALUES (:tid, :status)
                ON CONFLICT (thread_id)
                DO UPDATE SET updated_at = NOW(), current_status = EXCLUDED.current_status
                """
            ),
            {"tid": tid, "status": current_status},
        )

        # 2) messages：按 message_id 幂等 upsert
        for m in (data.get("messages") or []):
            mid = _norm_uuid(m.get("message_id"))
            if not mid:
                continue
            role = m.get("message_role") or "user"
            content = m.get("message_content") or ""
            ts = _parse_ts(m.get("timestamp")) or datetime.utcnow()
            await session.execute(
                text(
                    """
                    INSERT INTO messages(message_id, thread_id, role, content, timestamp, metadata)
                    VALUES (:mid, :tid, :role, :content, :ts, :meta)
                    ON CONFLICT (message_id)
                    DO UPDATE SET thread_id = EXCLUDED.thread_id,
                                  role = EXCLUDED.role,
                                  content = EXCLUDED.content,
                                  timestamp = EXCLUDED.timestamp
                    """
                ),
                {"mid": mid, "tid": tid, "role": role, "content": content, "ts": ts, "meta": None},
            )

        # 3) requirements_documents：追加版本历史（一条一条记录）
        rdoc = data.get("requirements_document") or {}
        if rdoc.get("version") and rdoc.get("content"):
            await session.execute(
                text(
                    """
                    INSERT INTO requirements_documents(document_id, thread_id, version, content, current_status)
                    VALUES (:doc_id, :tid, :version, :content, :status)
                    """
                ),
                {
                    "doc_id": str(uuid.uuid4()),
                    "tid": tid,
                    "version": rdoc.get("version"),
                    "content": rdoc.get("content"),
                    "status": current_status,
                },
            )

        # 4) questions & suggestion_options：按主键幂等 upsert
        for q in (data.get("question_list") or []):
            qid = _norm_uuid(q.get("question_id"))
            if not qid:
                continue
            qcontent = q.get("content") or ""
            await session.execute(
                text(
                    """
                    INSERT INTO questions(question_id, thread_id, content)
                    VALUES (:qid, :tid, :content)
                    ON CONFLICT (question_id) DO UPDATE SET content = EXCLUDED.content
                    """
                ),
                {"qid": qid, "tid": tid, "content": qcontent},
            )
            for o in (q.get("suggestion_options") or []):
                oid = _norm_uuid(o.get("option_id"))
                if not oid:
                    continue
                await session.execute(
                    text(
                        """
                        INSERT INTO suggestion_options(option_id, question_id, content, selected)
                        VALUES (:oid, :qid, :content, :selected)
                        ON CONFLICT (option_id) DO UPDATE SET content = EXCLUDED.content, selected = EXCLUDED.selected
                        """
                    ),
                    {
                        "oid": oid,
                        "qid": qid,
                        "content": o.get("content") or "",
                        "selected": bool(o.get("selected", False)),
                    },
                )

        # 5) multi_file：按 file_id 幂等 upsert（保留解析内容/路径）
        for f in (data.get("multi_files") or []):
            fid = _norm_uuid(f.get("file_id"))
            mid = _norm_uuid(f.get("message_id"))
            if not fid or not mid:
                # 表定义 message_id NOT NULL
                continue
            await session.execute(
                text(
                    """
                    INSERT INTO multi_file(file_id, message_id, thread_id, file_name, file_type, file_content, file_path)
                    VALUES (:fid, :mid, :tid, :name, :ftype, :content, :fpath)
                    ON CONFLICT (file_id)
                    DO UPDATE SET file_name = EXCLUDED.file_name,
                                  file_type = EXCLUDED.file_type,
                                  file_content = EXCLUDED.file_content,
                                  file_path = EXCLUDED.file_path
                    """
                ),
                {
                    "fid": fid,
                    "mid": mid,
                    "tid": tid,
                    "name": f.get("file_name") or "",
                    "ftype": f.get("file_type") or "",
                    "content": f.get("file_content"),
                    "fpath": f.get("file_path"),
                },
            )

        # 重要：提交事务，确保真正落库
        await session.commit()


async def _build_preload_state(thread_id: str) -> Optional[dict]:
    # 若无可用 DB，直接返回 None
    if _Session is None:
        return None
    # 统一为 UUID 带连字符格式，避免与数据库 uuid 类型不匹配
    try:
        if len(thread_id) == 32:
            tid_uuid = str(uuid.UUID(thread_id))
        else:
            tid_uuid = str(uuid.UUID(thread_id))
    except Exception:
        # 非法 thread_id 则不尝试预载
        return None

    preload: dict = {}

    await _ensure_db_initialized()
    async with _Session() as session:  # type: ignore[arg-type]
        # sessions.current_status
        try:
            row = (await session.execute(
                text("SELECT current_status FROM sessions WHERE thread_id = :tid ORDER BY updated_at DESC LIMIT 1"),
                {"tid": tid_uuid},
            )).first()
            if row and row[0]:
                preload["current_status"] = row[0]
        except Exception:
            pass

        # 最新需求文档
        try:
            rdoc = (await session.execute(
                text("""
                    SELECT version, content, created_at
                    FROM requirements_documents
                    WHERE thread_id = :tid
                    ORDER BY created_at DESC
                    LIMIT 1
                """),
                {"tid": tid_uuid},
            )).first()
            if rdoc:
                preload["requirements_document"] = {
                    "version": rdoc[0],
                    "content": rdoc[1],
                    # Agent 的 Schema 接受 date 或 ISO 字符串
                    "last_updated": rdoc[2].date().isoformat() if hasattr(rdoc[2], "date") else str(rdoc[2]),
                }
        except Exception:
            pass

        # 问题与建议选项
        try:
            qrows = (await session.execute(
                text("""
                    SELECT q.question_id, q.content
                    FROM questions q
                    WHERE q.thread_id = :tid
                    ORDER BY q.created_at ASC
                """),
                {"tid": tid_uuid},
            )).all()
            questions = []
            for q in qrows:
                qid, qcontent = q[0], q[1]
                opt_rows = (await session.execute(
                    text("""
                        SELECT option_id, content, selected
                        FROM suggestion_options
                        WHERE question_id = :qid
                        ORDER BY option_id
                    """),
                    {"qid": qid},
                )).all()
                questions.append({
                    "question_id": str(qid),
                    "content": qcontent,
                    "suggestion_options": [
                        {"option_id": str(o[0]), "content": o[1], "selected": bool(o[2])}
                        for o in opt_rows
                    ],
                })
            if questions:
                preload["question_list"] = questions
        except Exception:
            pass

        # 多文件信息（保留最近若干条）
        try:
            frows = (await session.execute(
                text("""
                    SELECT file_id, file_name, file_type, file_content, file_path, message_id
                    FROM multi_file
                    WHERE thread_id = :tid
                    ORDER BY created_at DESC
                    LIMIT 10
                """),
                {"tid": tid_uuid},
            )).all()
            files = []
            for r in frows:
                files.append({
                    "file_id": str(r[0]),
                    "file_name": r[1],
                    "file_type": r[2],
                    "file_size": None,
                    "file_path": r[4],
                    "file_content": r[3],
                    "message_id": str(r[5]) if r[5] else None,
                })
            if files:
                preload["multi_files"] = files
        except Exception:
            pass

    return preload or None

@router.post("/submit", response_model=SubmitResponse)
async def submit(req: SubmitRequest):
    # 若未显式传入 model_params，则尝试注入“当前激活模型”的参数（含服务间临时传递 api_key）
    payload = req.model_dump()
    mp = payload.get("model_params") or {}
    try:
        if not mp:
            await _ensure_db_initialized()
            if _Session is None:
                raise RuntimeError("DB session 未初始化")
            async with _Session() as session:  # type: ignore[arg-type]
                # 查找当前用户激活的模型
                active_row = (await session.execute(
                    select(ModelActive.active_model_id).where(ModelActive.user_id == req.user_id)
                )).first()
                active_id = active_row[0] if active_row else None
                if active_id:
                    ms = (await session.execute(
                        select(ModelSetting).where(ModelSetting.id == active_id)
                    )).scalar_one_or_none()
                    if ms:
                        api_key_plain = _decrypt(ms.api_key_encrypted)
                        mp = {
                            "provider": ms.provider,
                            "base_url": ms.base_url,
                            "model": ms.model,
                            "temperature": ms.temperature,
                            "max_tokens": ms.max_tokens,
                            # 仅服务间转发使用，不对外回显
                            "api_key": api_key_plain or os.getenv("OPENAI_API_KEY"),
                        }
                        payload["model_params"] = mp
    except Exception as ex:
        # 注入失败不阻断提交流程，仅在完全不存在可用配置时会导致 Agent 侧报错
        pass

    # 新增：按 thread_id 预载上下文（若数据库中存在）
    try:
        if payload.get("thread_id"):
            preload = await _build_preload_state(payload["thread_id"])  # type: ignore[arg-type]
            if preload:
                payload["preload_state"] = preload
    except Exception:
        # 预载失败不影响主流程
        pass

    # 直接转调 Agent，并原样返回 + 持久化
    try:
        data = await agent_client.submit(payload)
        # 新增：落库持久化（sessions/messages/questions/suggestion_options/requirements_documents/multi_file）
        try:
            await _persist_state(data)
        except Exception as _ex:
            # 落库失败不影响用户请求返回，但需在日志中可见
            # 这里不抛到前端，避免影响体验
            pass
        return data
    except Exception as ex:
        raise HTTPException(status_code=502, detail=f"submit failed: {ex}")

@router.get("/status", response_model=PollResponse)
async def status(thread_id: str, state_version: int):
    try:
        data = await agent_client.poll(thread_id, state_version)
        return data
    except Exception as ex:
        raise HTTPException(status_code=502, detail=f"status failed: {ex}")

@router.get("/state", response_model=StateResponse)
async def get_state(thread_id: str, state_version: Optional[int] = None, version: Optional[str] = None):
    """
    返回指定 thread_id 下的完整状态，完全由 PostgreSQL 聚合生成：
    - 保留向后兼容字段（requirements_document/question_list/messages/multi_files）
    - 新增聚合字段（versions/documents）
    - state_version 取所有 version 的“数字部分”最大值（无则为 0）
    注意：保留 state_version/version 参数仅兼容旧前端，但不作为过滤条件。
    """
    try:
        # 确保业务表与会话已初始化
        await _ensure_biz_tables()
        try:
            tid_uuid = uuid.UUID(thread_id)
        except Exception:
            raise HTTPException(status_code=400, detail="invalid thread_id")

        await _ensure_db_initialized()
        if _Session is None:
            raise HTTPException(status_code=500, detail="database not ready")

        # 单条 SQL 一次性聚合出完整 state
        sql = text(
            """
            SELECT jsonb_build_object(
              'thread_id', (:tid)::text,
              'state_version', COALESCE(
                (
                  SELECT MAX(NULLIF(regexp_replace(rd.version, '[^0-9]+', '', 'g'), '')::int)
                  FROM requirements_documents rd
                  WHERE rd.thread_id = :tid
                ),
                0
              ),
              'current_status', COALESCE(
                (
                  SELECT rd.current_status
                  FROM requirements_documents rd
                  WHERE rd.thread_id = :tid
                  ORDER BY rd.created_at DESC
                  LIMIT 1
                ),
                (
                  SELECT s.current_status
                  FROM sessions s
                  WHERE s.thread_id = :tid
                )
              ),
              'requirements_document', (
                SELECT to_jsonb(sub)
                FROM (
                  SELECT
                    rd.version,
                    rd.content,
                    to_char(rd.created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"') AS last_updated
                  FROM requirements_documents rd
                  WHERE rd.thread_id = :tid
                  ORDER BY rd.created_at DESC
                  LIMIT 1
                ) AS sub
              ),
              'versions', COALESCE(
                (
                  SELECT jsonb_agg(v.version ORDER BY v.created_at ASC)
                  FROM (
                    SELECT rd.version, rd.created_at
                    FROM requirements_documents rd
                    WHERE rd.thread_id = :tid
                    ORDER BY rd.created_at ASC
                  ) AS v
                ),
                '[]'::jsonb
              ),
              'documents', COALESCE(
                (
                  SELECT jsonb_agg(
                    jsonb_build_object(
                      'version', rd.version,
                      'content', rd.content,
                      'last_updated', to_char(rd.created_at AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
                      'current_status', rd.current_status
                    )
                    ORDER BY rd.created_at ASC
                  )
                  FROM requirements_documents rd
                  WHERE rd.thread_id = :tid
                ),
                '[]'::jsonb
              ),
              'question_list', COALESCE(
                (
                  SELECT jsonb_agg(
                    jsonb_build_object(
                      'question_id', q.question_id,
                      'content', q.content,
                      'suggestion_options', COALESCE(
                        (
                          SELECT jsonb_agg(
                            jsonb_build_object(
                              'option_id', so.option_id,
                              'content', so.content,
                              'selected', so.selected
                            )
                            ORDER BY so.option_id
                          )
                          FROM suggestion_options so
                          WHERE so.question_id = q.question_id
                        ),
                        '[]'::jsonb
                      )
                    )
                    ORDER BY q.created_at ASC
                  )
                  FROM questions q
                  WHERE q.thread_id = :tid
                ),
                '[]'::jsonb
              ),
              'messages', COALESCE(
                (
                  SELECT jsonb_agg(
                    jsonb_build_object(
                      'message_id', m.message_id,
                      'role', m.role,
                      'content', m.content,
                      'timestamp', to_char(m.timestamp AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS.MS"Z"'),
                      'metadata', m.metadata
                    )
                    ORDER BY m.timestamp ASC
                  )
                  FROM messages m
                  WHERE m.thread_id = :tid
                ),
                '[]'::jsonb
              ),
              'multi_files', COALESCE(
                (
                  SELECT jsonb_agg(
                    jsonb_build_object(
                      'file_id', f.file_id,
                      'file_name', f.file_name,
                      'file_type', f.file_type,
                      'file_size', NULL,
                      'file_path', f.file_path,
                      'file_content', f.file_content,
                      'message_id', f.message_id
                    )
                    ORDER BY f.created_at DESC
                  )
                  FROM multi_file f
                  WHERE f.thread_id = :tid
                ),
                '[]'::jsonb
              )
            ) AS state
            """
        )

        async with _Session() as session:  # type: ignore[arg-type]
            res = (await session.execute(sql, {"tid": tid_uuid})).first()

        if not res or res[0] is None:
            # 空数据兜底（保持响应模型字段完备）
            return {
                "thread_id": thread_id,
                "state_version": int(state_version or 0),
                "current_status": "clarifying",
                "requirements_document": None,
                "question_list": [],
                "messages": [],
                "multi_files": [],
                "versions": [],
                "documents": [],
            }

        state_obj = res[0]
        if isinstance(state_obj, (str, bytes)):
            try:
                state_obj = json.loads(state_obj)
            except Exception:
                state_obj = {}
        if not isinstance(state_obj, dict):
            state_obj = {}
        # 确保 thread_id 为字符串（而非 UUID 对象）
        state_obj.setdefault("thread_id", str(thread_id))
        # 兼容老前端：若无字段则补默认
        state_obj.setdefault("state_version", int(state_version or state_obj.get("state_version", 0) or 0))
        state_obj.setdefault("current_status", "clarifying")
        state_obj.setdefault("requirements_document", None)
        state_obj.setdefault("question_list", [])
        state_obj.setdefault("messages", [])
        state_obj.setdefault("multi_files", [])
        state_obj.setdefault("versions", [])
        state_obj.setdefault("documents", [])
        return state_obj
    except HTTPException:
        raise
    except Exception as ex:
        raise HTTPException(status_code=502, detail=f"state failed: {ex}")

# --- 新增：版本目录与文档内容查询接口 ---
@router.get("/versions")
async def list_versions(thread_id: str):
    """返回给定 thread_id 的文档版本列表（按时间顺序升序）。"""
    try:
        # 确保业务表已初始化
        global _BIZ_TABLES_READY
        if not _BIZ_TABLES_READY:
            await init_tables()
            _BIZ_TABLES_READY = True

        # 线程 ID 规范化为 UUID
        try:
            tid_uuid = uuid.UUID(thread_id)
        except Exception:
            raise HTTPException(status_code=400, detail="invalid thread_id")

        await _ensure_db_initialized()
        async with _Session() as session:
            rows = (
                await session.execute(
                    text(
                        """
                        SELECT version
                        FROM requirements_documents
                        WHERE thread_id = :tid
                        ORDER BY created_at ASC
                        """
                    ),
                    {"tid": tid_uuid},
                )
            ).all()
        versions = [r[0] for r in rows]
        return {"thread_id": thread_id, "versions": versions}
    except HTTPException:
        raise
    except Exception as ex:
        raise HTTPException(status_code=502, detail=f"list versions failed: {ex}")

@router.get("/document")
async def get_document(thread_id: str, version: str):
    """返回指定 thread_id + version 的文档内容。"""
    try:
        global _BIZ_TABLES_READY
        if not _BIZ_TABLES_READY:
            await init_tables()
            _BIZ_TABLES_READY = True

        try:
            tid_uuid = uuid.UUID(thread_id)
        except Exception:
            raise HTTPException(status_code=400, detail="invalid thread_id")

        await _ensure_db_initialized()
        async with _Session() as session:
            row = (
                await session.execute(
                    text(
                        """
                        SELECT version, content, created_at, current_status
                        FROM requirements_documents
                        WHERE thread_id = :tid AND version = :ver
                        ORDER BY created_at DESC
                        LIMIT 1
                        """
                    ),
                    {"tid": tid_uuid, "ver": version},
                )
            ).first()
        if not row:
            raise HTTPException(status_code=404, detail="document not found")
        return {
            "thread_id": thread_id,
            "version": row[0],
            "content": row[1],
            "created_at": row[2].isoformat() if hasattr(row[2], "isoformat") else str(row[2]),
            "current_status": row[3],
        }
    except HTTPException:
        raise
    except Exception as ex:
        raise HTTPException(status_code=502, detail=f"get document failed: {ex}")