"""LangGraph orchestration: the four specialists fan out in parallel from
START, then fan back in to the aggregator once all four have finished.

Each specialist is isolated: a failure or timeout in one produces None for
that agent instead of taking down the whole run. The aggregator treats a
missing agent as "unknown," not as agreement or disagreement — and if most
agents failed, that's treated as a systemic problem (bad key, network down)
rather than quietly shipped as a normal partial report.
"""

import concurrent.futures
import sys
from typing import Callable, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from agents import aggregator, fundamentals, risk, sentiment, technical
from agents.base import AgentResult

NODE_TIMEOUT_SECONDS = 30
SYSTEMIC_FAILURE_THRESHOLD = 1  # 0 or 1 of 4 succeeding is not "a bit flaky"


class ResearchState(TypedDict):
    ticker: str
    technical: Optional[AgentResult]
    fundamentals: Optional[AgentResult]
    sentiment: Optional[AgentResult]
    risk: Optional[AgentResult]
    final_report: str


def _safe_run(name: str, fn: Callable[[str], AgentResult], ticker: str) -> Optional[AgentResult]:
    """Run one specialist with a hard timeout, converting any failure into
    None rather than letting it propagate and kill the whole graph run.

    Note: Python threads can't be forcibly killed, so a timeout here means
    "stop waiting for it," not "stop it from running" — the worker thread
    may keep running in the background after we give up on it. Deliberately
    NOT using the executor as a context manager: `__exit__` calls
    `shutdown(wait=True)`, which would block on that same orphaned thread and
    silently defeat the timeout.
    """
    pool = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    future = pool.submit(fn, ticker)
    try:
        return future.result(timeout=NODE_TIMEOUT_SECONDS)
    except concurrent.futures.TimeoutError:
        print(f"[{name}] timed out after {NODE_TIMEOUT_SECONDS}s", file=sys.stderr)
        return None
    except Exception as exc:
        print(f"[{name}] failed: {exc}", file=sys.stderr)
        return None
    finally:
        pool.shutdown(wait=False)


def _technical_node(state: ResearchState) -> dict:
    return {"technical": _safe_run("technical", technical.run, state["ticker"])}


def _fundamentals_node(state: ResearchState) -> dict:
    return {"fundamentals": _safe_run("fundamentals", fundamentals.run, state["ticker"])}


def _sentiment_node(state: ResearchState) -> dict:
    return {"sentiment": _safe_run("sentiment", sentiment.run, state["ticker"])}


def _risk_node(state: ResearchState) -> dict:
    return {"risk": _safe_run("risk", risk.run, state["ticker"])}


def _aggregator_node(state: ResearchState) -> dict:
    by_name = {
        "technical": state.get("technical"),
        "fundamentals": state.get("fundamentals"),
        "sentiment": state.get("sentiment"),
        "risk": state.get("risk"),
    }
    available = [r for r in by_name.values() if r is not None]
    missing = [name for name, r in by_name.items() if r is None]

    if len(available) <= SYSTEMIC_FAILURE_THRESHOLD:
        raise RuntimeError(
            f"Only {len(available)}/4 agents produced results (missing: {missing}). "
            "This looks like a systemic problem (bad API key, network outage, code "
            "bug) rather than ordinary single-agent flakiness — investigate before "
            "trusting any report generated from this state."
        )

    report = aggregator.run(state["ticker"], available, missing)
    return {"final_report": report}


def build_graph():
    graph = StateGraph(ResearchState)

    graph.add_node("technical", _technical_node)
    graph.add_node("fundamentals", _fundamentals_node)
    graph.add_node("sentiment", _sentiment_node)
    graph.add_node("risk", _risk_node)
    graph.add_node("aggregator", _aggregator_node)

    graph.add_edge(START, "technical")
    graph.add_edge(START, "fundamentals")
    graph.add_edge(START, "sentiment")
    graph.add_edge(START, "risk")

    graph.add_edge("technical", "aggregator")
    graph.add_edge("fundamentals", "aggregator")
    graph.add_edge("sentiment", "aggregator")
    graph.add_edge("risk", "aggregator")

    graph.add_edge("aggregator", END)

    return graph.compile()
