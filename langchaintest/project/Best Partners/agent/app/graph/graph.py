from __future__ import annotations

from typing import Optional
import sys
import atexit

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from app.graph.state import RequirementsValidationState
from app.graph.nodes import start as start_node, input_processor as input_processor_node
from app.graph.file_toolscall_agent import file_toolscall_agent as file_toolscall_agent_node
from app.graph.requirements_analysis_agent import requirements_analysis_agent as requirements_analysis_agent_node
from app.utils.env import get_redis_url, get_postgres_url


# Optional: Redis checkpointer if available
try:
    from langgraph.checkpoint.redis import RedisSaver  # type: ignore
except Exception:  # pragma: no cover
    RedisSaver = None  # type: ignore

# Optional: Postgres checkpointer if available (via langgraph-checkpoint-postgres)
try:
    from langgraph.checkpoint.postgres import PostgresSaver  # type: ignore
except Exception:  # pragma: no cover
    PostgresSaver = None  # type: ignore

# Keep opened context managers to close gracefully at process exit
_cm_stack = []  # type: ignore[var-annotated]

def _enter_if_context(obj):
    """If obj is a context manager, enter it and remember to close at exit.
    Return the inner object; otherwise return obj itself.
    """
    try:
        is_cm = hasattr(obj, "__enter__") and hasattr(obj, "__exit__") and not hasattr(obj, "get_next_version")
        if is_cm:
            inner = obj.__enter__()
            _cm_stack.append(obj)
            return inner
    except Exception:
        pass
    return obj

# Ensure all opened contexts are closed on process exit
@atexit.register
def _cleanup_cm_stack():
    while _cm_stack:
        cm = _cm_stack.pop()
        try:
            cm.__exit__(None, None, None)
        except Exception:
            pass


def get_checkpointer():
    # Prefer PostgreSQL when available
    pg_url = get_postgres_url()
    if pg_url and PostgresSaver is not None:
        try:
            cp = PostgresSaver.from_conn_string(pg_url)
            cp = _enter_if_context(cp)
            # Ensure tables exist on first use
            try:
                cp.setup()
            except Exception:
                # setup best-effort; if it fails due to existing tables or perms, continue
                pass
            try:
                sys.stdout.write(f"[graph] Using PostgresSaver checkpointer at {pg_url}\n")
                sys.stdout.flush()
            except Exception:
                pass
            return cp
        except Exception as e:
            try:
                sys.stdout.write(f"[graph] Failed to init PostgresSaver ({e}), will try Redis next.\n")
                sys.stdout.flush()
            except Exception:
                pass

    # Fallback: Redis
    redis_url = get_redis_url()
    if redis_url and RedisSaver is not None:
        try:
            cp = RedisSaver.from_conn_string(redis_url) if hasattr(RedisSaver, 'from_conn_string') else RedisSaver(redis_url)  # type: ignore
            cp = _enter_if_context(cp)
            try:
                sys.stdout.write(f"[graph] Using RedisSaver checkpointer at {redis_url}\n")
                sys.stdout.flush()
            except Exception:
                pass
            return cp
        except Exception as e:
            try:
                sys.stdout.write(f"[graph] Failed to init RedisSaver ({e}), fallback to MemorySaver.\n")
                sys.stdout.flush()
            except Exception:
                pass

    # Default: in-memory
    try:
        sys.stdout.write("[graph] Using MemorySaver checkpointer (no Postgres/Redis available).\n")
        sys.stdout.flush()
    except Exception:
        pass
    return MemorySaver()


# 轻量包装：在节点执行后标记来源节点，供下一节点判断中断

def _wrap_with_from(tag, fn):
    def _inner(state: RequirementsValidationState, config):
        out = fn(state, config)
        prev = state.get("from_node")
        # 合并旧状态与节点输出，避免节点只返回部分字段时丢失其余状态
        new_state = {**state, **out, "prev_node": prev, "from_node": tag}
        try:
            sys.stdout.write(f"[graph] after {tag}: prev={prev}, from={tag}, interrupt={new_state.get('interrupt')}, status={new_state.get('current_status')}\n")
            sys.stdout.flush()
        except Exception:
            pass
        return new_state
    return _inner


def build_graph():
    workflow = StateGraph(RequirementsValidationState)

    # 注册节点（带 from_node 包装）
    workflow.add_node("start", _wrap_with_from("start", start_node))
    workflow.add_node("input_processor", _wrap_with_from("input_processor", input_processor_node))
    workflow.add_node("file_toolscall_agent", _wrap_with_from("file_toolscall_agent", file_toolscall_agent_node))
    workflow.add_node("requirements_analysis_agent", _wrap_with_from("requirements_analysis_agent", requirements_analysis_agent_node))

    workflow.add_edge(START, "start")
    workflow.add_edge("start", "input_processor")

    # 条件路由：input_processor → (interrupt? END : file_toolscall_agent)
    def route_after_input(state: RequirementsValidationState):
        try:
            sys.stdout.write(f"[graph] route_after_input: interrupt={state.get('interrupt')} (from={state.get('from_node')}, prev={state.get('prev_node')})\n")
            sys.stdout.flush()
        except Exception:
            pass
        return END if state.get("interrupt") else "file_toolscall_agent"

    workflow.add_conditional_edges(
        "input_processor",
        route_after_input,
        {"file_toolscall_agent": "file_toolscall_agent", END: END},
    )

    # 条件路由：requirements_analysis_agent → (completed? END : input_processor)
    def route_after_analysis(state: RequirementsValidationState):
        try:
            sys.stdout.write(f"[graph] route_after_analysis: status={state.get('current_status')}\n")
            sys.stdout.flush()
        except Exception:
            pass
        status = state.get("current_status") or "clarifying"
        # 单轮执行策略：分析节点后直接结束本轮，等待下一次用户输入，避免在同一轮内回流造成递归
        return END

    workflow.add_conditional_edges(
        "requirements_analysis_agent",
        route_after_analysis,
        {"input_processor": "input_processor", END: END},
    )

    workflow.add_edge("file_toolscall_agent", "requirements_analysis_agent")

    return workflow


def get_compiled_graph():
    checkpointer = get_checkpointer()
    return build_graph().compile(checkpointer=checkpointer)

# For LangGraph CLI: export a graph without checkpointer (platform manages persistence)
graph = build_graph().compile()