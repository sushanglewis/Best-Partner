from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import os
import httpx
from typing import Optional, Dict, Any
from datetime import datetime

# 替换为 PostgreSQL + SQLAlchemy(异步)
import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, Float, Integer, DateTime, select
from cryptography.fernet import Fernet

router = APIRouter(tags=["models"]) 

# 进程内“就绪”标记仅用于 /config 向后兼容
# （移除内存兜底与就绪标记的影响，转为仅依赖 DB 是否存在记录）
_MODEL_CONFIG: Dict[str, Any] = {}
_MODEL_TEST_OK: bool = False
# 内存兜底（开发环境 / 未配置数据库时使用，不做持久化）
_MODEL_STORE: Dict[str, list[Dict[str, Any]]] = {}
_MODEL_ACTIVE_MEM: Dict[str, int] = {}
_MODEL_AUTO_INC: int = 0

# ---------- DB & ORM ----------
class Base(DeclarativeBase):
    pass

class ModelSetting(Base):
    __tablename__ = "model_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(128), index=True)
    provider: Mapped[str] = mapped_column(String(64))
    base_url: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    model: Mapped[Optional[str]] = mapped_column(String(256), nullable=True)
    api_key_encrypted: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    temperature: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    max_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=False))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=False))

class ModelActive(Base):
    __tablename__ = "model_active"

    user_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    active_model_id: Mapped[int] = mapped_column(Integer)

_engine: Optional[Any] = None
_Session: Optional[async_sessionmaker[AsyncSession]] = None
_db_inited = False
_db_init_lock = asyncio.Lock()

# 检查并强制仅允许 postgresql+asyncpg
_DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
# 兼容用户误配为 postgresql:// —— 自动升级为 postgresql+asyncpg://
if _DATABASE_URL.startswith("postgresql://"):
    _DATABASE_URL = "postgresql+asyncpg://" + _DATABASE_URL[len("postgresql://"):]
if not _DATABASE_URL.startswith("postgresql+asyncpg://"):
    _engine = None
    _Session = None
else:
    _engine = create_async_engine(_DATABASE_URL, echo=False, future=True)
    _Session = async_sessionmaker(_engine, expire_on_commit=False, class_=AsyncSession)

async def _ensure_db_initialized():
    global _db_inited
    if _db_inited:
        return
    if _engine is None or _Session is None:
        raise HTTPException(status_code=500, detail="DATABASE_URL 未配置或无效，请设置环境变量 DATABASE_URL（postgresql+asyncpg）")
    async with _db_init_lock:
        if _db_inited:
            return
        async with _engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        _db_inited = True

# ---------- 加密工具（避免明文持久化 api_key） ----------
_FERNET_KEY = os.getenv("FERNET_KEY")  # 请在部署时提供，使用 Fernet.generate_key() 生成的 urlsafe base64 字符串
_fernet: Optional[Fernet] = None
try:
    if _FERNET_KEY:
        _fernet = Fernet(_FERNET_KEY)
except Exception:
    _fernet = None

def _encrypt(text: Optional[str]) -> Optional[str]:
    if not text:
        return None
    if not _fernet:
        # 未配置密钥时，不允许持久化明文
        raise HTTPException(status_code=500, detail="未配置 FERNET_KEY，禁止持久化明文 api_key")
    return _fernet.encrypt(text.encode("utf-8")).decode("utf-8")

# 新增：解密工具（仅用于服务内部临时转发，不回显给前端）
def _decrypt(token: Optional[str]) -> Optional[str]:
    if not token:
        return None
    if not _fernet:
        raise HTTPException(status_code=500, detail="未配置 FERNET_KEY，无法解密 api_key")
    try:
        return _fernet.decrypt(token.encode("utf-8")).decode("utf-8")
    except Exception:
        raise HTTPException(status_code=500, detail="FERNET_KEY 无法解密已存储的 api_key，请确认密钥一致")

# ---------- Schemas ----------
class ModelConfig(BaseModel):
    provider: str = Field(..., description="llm provider")
    base_url: Optional[str] = None
    model: Optional[str] = None
    api_key: Optional[str] = None
    temperature: Optional[float] = 0.3
    max_tokens: Optional[int] = 2048

class SaveModelRequest(BaseModel):
    user_id: str
    config: ModelConfig

class ActivateRequest(BaseModel):
    user_id: str
    model_id: int

# ---------- APIs ----------
@router.get("/config")
async def get_model_config():
    # 仅依赖 PostgreSQL：存在任意记录即 ready，并回显最近一条（脱敏）
    await _ensure_db_initialized()
    cfg = {
        "provider": "",
        "base_url": None,
        "model": None,
        "api_key": None,
        "temperature": 0.3,
        "max_tokens": 2048,
    }
    ready_flag = False

    async with _Session() as session:  # type: ignore[arg-type]
        exists_row = (await session.execute(select(ModelSetting.id).limit(1))).first()
        if exists_row:
            ready_flag = True
            row_obj = (await session.execute(
                select(ModelSetting).order_by(ModelSetting.id.desc()).limit(1)
            )).scalar_one()
            cfg.update({
                "provider": row_obj.provider,
                "base_url": row_obj.base_url,
                "model": row_obj.model,
                "temperature": row_obj.temperature,
                "max_tokens": row_obj.max_tokens,
                "api_key": "***",
            })
    return {"config": cfg, "ready": ready_flag}

@router.post("/test")
async def test_model(cfg: ModelConfig):
    # 使用表单参数真实连通性检测（OpenAI 兼容 /v1/models）
    # 根据 provider 设置合理默认 base_url；避免误把非 openai 的请求指向 openai.com
    provider = (cfg.provider or "openai").strip().lower()
    base_input = (cfg.base_url or "").strip()
    if not base_input:
        if provider == "openai":
            base_input = "https://api.openai.com/v1"
        elif provider in {"qwen", "tongyi", "aliyun", "dashscope"}:
            # 通义千问（DashScope）OpenAI 兼容模式
            base_input = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        else:
            # 其他供应商（如 deepseek/moonshot/doubao/hunyuan）需显式传入其 OpenAI 兼容网关 base_url
            raise HTTPException(status_code=400, detail="缺少 base_url：非 openai/tongyi 供应商必须显式提供 base_url")

    base_input = base_input.rstrip("/")
    # 兼容用户传入已包含 /v1 的网关地址，避免拼出 /v1/v1/models 导致 404
    if base_input.endswith("/v1"):
        url = f"{base_input}/models"
    else:
        url = f"{base_input}/v1/models"

    headers = {}
    if cfg.api_key:
        headers["Authorization"] = f"Bearer {cfg.api_key}"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            r = await client.get(url, headers=headers)
            if r.status_code >= 400:
                detail = r.text
                raise HTTPException(status_code=502, detail=f"Provider error {r.status_code}: {detail[:200]}")
    except HTTPException:
        raise
    except Exception as ex:
        raise HTTPException(status_code=502, detail=f"Connectivity failed: {ex}")

    global _MODEL_TEST_OK
    _MODEL_TEST_OK = True
    return {"ok": True}

@router.post("/save")
async def save_model(req: SaveModelRequest):
    # 强制使用 PostgreSQL 持久化
    await _ensure_db_initialized()
    cfg = req.config
    now = datetime.utcnow()

    # 加密 api_key（若未配置 FERNET_KEY 将返回 500，避免明文落库）
    api_key_encrypted = _encrypt(cfg.api_key)

    async with _Session() as session:  # type: ignore[arg-type]
        ms = ModelSetting(
            user_id=req.user_id,
            provider=cfg.provider,
            base_url=cfg.base_url,
            model=cfg.model,
            api_key_encrypted=api_key_encrypted,
            temperature=float(cfg.temperature or 0.3),
            max_tokens=int(cfg.max_tokens or 2048),
            created_at=now,
            updated_at=now,
        )
        session.add(ms)
        await session.commit()

        # 若该用户尚未设置 active，则将最新保存的设为 active
        existing_active = (await session.execute(select(ModelActive).where(ModelActive.user_id == req.user_id))).scalar_one_or_none()
        if existing_active is None:
            session.add(ModelActive(user_id=req.user_id, active_model_id=ms.id))
            await session.commit()

    return {"saved": True, "ready": True}

@router.get("/list")
async def list_models(user_id: str):
    # 强制使用 PostgreSQL 查询
    await _ensure_db_initialized()
    async with _Session() as session:  # type: ignore[arg-type]
        rows = (await session.execute(select(ModelSetting).where(ModelSetting.user_id == user_id).order_by(ModelSetting.id.desc()))).scalars().all()
        data = [
            {
                "id": r.id,
                "user_id": r.user_id,
                "provider": r.provider,
                "base_url": r.base_url,
                "model": r.model,
                "temperature": r.temperature,
                "max_tokens": r.max_tokens,
                "created_at": r.created_at.isoformat(),
                "updated_at": r.updated_at.isoformat(),
            }
            for r in rows
        ]
        return {"items": data}

@router.post("/activate")
async def activate_model(req: ActivateRequest):
    # 强制使用 PostgreSQL 更新活跃模型
    await _ensure_db_initialized()
    async with _Session() as session:  # type: ignore[arg-type]
        # 校验模型是否属于该用户
        ms = (await session.execute(select(ModelSetting).where(ModelSetting.id == req.model_id, ModelSetting.user_id == req.user_id))).scalar_one_or_none()
        if ms is None:
            raise HTTPException(status_code=404, detail="模型不存在或不属于该用户")

        row = (await session.execute(select(ModelActive).where(ModelActive.user_id == req.user_id))).scalar_one_or_none()
        if row is None:
            session.add(ModelActive(user_id=req.user_id, active_model_id=req.model_id))
        else:
            row.active_model_id = req.model_id
        await session.commit()
    return {"ok": True, "active_id": req.model_id}

@router.get("/active")
async def get_active(user_id: str):
    # 强制使用 PostgreSQL 查询活跃模型
    await _ensure_db_initialized()
    async with _Session() as session:  # type: ignore[arg-type]
        row = (await session.execute(select(ModelActive.active_model_id).where(ModelActive.user_id == user_id))).first()
        active_id = row[0] if row else None
    return {"active_id": active_id}