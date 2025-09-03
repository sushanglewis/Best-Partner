"""
LLM 客户端工厂

职责：
- 基于 state.model_params 或环境变量，实例化可用的 Chat 模型；
- 根据不同供应商使用对应的基础 ChatModel；
- 支持 OpenAI 兼容网关（base_url + api_key）。

使用：
    from app.services.llm import get_chat_model
    llm = get_chat_model(state.get("model_params", {}))
    chain = prompt | llm | StrOutputParser()
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional


def _get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    v = os.getenv(name)
    return v if v is not None and v != "" else default


def _build_openai_compatible(mp: Dict[str, Any]):
    """使用 OpenAI 兼容的 ChatOpenAI 实例化（包含 deepseek/moonshot/doubao/hunyuan 等）。"""
    try:
        from langchain_openai import ChatOpenAI
    except Exception as e:  # pragma: no cover
        raise RuntimeError(
            "缺少依赖 langchain-openai，请先在 Agent 虚拟环境中安装：pip install langchain-openai"
        ) from e

    api_key = mp.get("api_key") or _get_env("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("未检测到 OPENAI_API_KEY 或 model_params.api_key，无法创建 OpenAI 兼容模型实例")

    base_url = mp.get("base_url") or _get_env("OPENAI_BASE_URL")
    model = mp.get("model") or _get_env("OPENAI_MODEL", "gpt-4o-mini")
    temperature = float(mp.get("temperature") or 0.2)
    max_tokens = mp.get("max_tokens")

    kwargs: Dict[str, Any] = {
        "model": model,
        "temperature": temperature,
        "api_key": api_key,
    }
    if base_url:
        kwargs["base_url"] = base_url
    if max_tokens is not None:
        kwargs["max_tokens"] = int(max_tokens)

    return ChatOpenAI(**kwargs)


def _build_tongyi(mp: Dict[str, Any]):
    """阿里通义（Qwen/Tongyi）。优先使用官方 SDK，经由 langchain-community ChatTongyi。
    兼容用户传入的 api_key（DASHSCOPE_API_KEY）。
    """
    # 兼容两种导入路径
    ChatTongyi = None
    exc: Exception | None = None
    try:
        from langchain_community.chat_models.tongyi import ChatTongyi as _CT
        ChatTongyi = _CT
    except Exception as e1:  # pragma: no cover
        exc = e1
        try:
            from langchain_community.chat_models import ChatTongyi as _CT2
            ChatTongyi = _CT2
        except Exception as e2:  # pragma: no cover
            exc = e2
    if ChatTongyi is None:
        raise RuntimeError(
            "缺少依赖：langchain-community 或未包含 ChatTongyi，请安装：pip install langchain-community dashscope"
        ) from exc

    api_key = mp.get("api_key") or _get_env("DASHSCOPE_API_KEY")
    if api_key:
        # ChatTongyi 默认从环境变量读取
        os.environ["DASHSCOPE_API_KEY"] = api_key
    model = mp.get("model") or _get_env("TONGYI_MODEL", "qwen-plus-latest")
    temperature = float(mp.get("temperature") or 0.2)

    # ChatTongyi 目前不显式接收 max_tokens 参数；如需可通过 model_kwargs 传递
    model_kwargs: Dict[str, Any] = {}
    if mp.get("max_tokens") is not None:
        model_kwargs["max_tokens"] = int(mp.get("max_tokens"))

    # 修复 DashScope 非流式调用需要关闭思考模式（enable_thinking）
    # 参考错误：parameter.enable_thinking must be set to false for non-streaming calls
    model_kwargs["enable_thinking"] = False

    return ChatTongyi(model=model, temperature=temperature, model_kwargs=model_kwargs or None)


def get_chat_model(model_params: Optional[Dict[str, Any]] = None):
    """返回一个 Chat 模型实例。

    分支规则：
    - openai/deepseek/moonshot/doubao/hunyuan → OpenAI 兼容（ChatOpenAI）
    - qwen/tongyi/aliyun/dashscope → ChatTongyi（需要 dashscope）
    - 其他/未知 → 回退为 OpenAI 兼容（需提供 api_key 与可用 base_url）
    """
    mp = (model_params or {}).copy()

    # 供应商归一化别名
    provider_raw = (mp.get("provider") or _get_env("LLM_PROVIDER", "openai")).strip().lower()
    aliases = {
        "openai": "openai",
        "deepseek": "openai",
        "moonshot": "openai",  # 月之暗面（Moonshot AI）
        "月之暗面": "openai",
        "doubao": "openai",     # 火山引擎豆包（OpenAI 兼容模式）
        "豆包": "openai",
        "hunyuan": "openai",    # 腾讯混元（OpenAI 兼容模式）
        "腾讯混元": "openai",
        "qwen": "tongyi",
        "tongyi": "tongyi",
        "aliyun": "tongyi",
        "dashscope": "tongyi",
        "通义千问": "tongyi",
    }
    provider = aliases.get(provider_raw, "openai")

    if provider == "tongyi":
        return _build_tongyi(mp)
    else:
        return _build_openai_compatible(mp)