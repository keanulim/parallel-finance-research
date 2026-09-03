"""Run the finance-research agent graph for one ticker.

Orchestration is LangGraph: the four specialists fan out from START and run
concurrently, then fan back in to the aggregator once all four finish.
"""

import os
import sys
import time

from dotenv import load_dotenv

from graph import build_graph

load_dotenv()

app = build_graph()

AGENT_ORDER = ["technical", "fundamentals", "sentiment", "risk"]


def run_research(ticker: str) -> None:
    ticker = ticker.upper()

    print("[graph] running 4 agents in parallel...", file=sys.stderr)
    start = time.time()
    state = app.invoke({"ticker": ticker})
    elapsed = time.time() - start
    print(f"[graph] all agents + aggregator done in {elapsed:.1f}s", file=sys.stderr)

    print("\n" + "=" * 70)
    print(f"RESEARCH REPORT: {ticker}")
    print("=" * 70)
    for name in AGENT_ORDER:
        r = state[name]
        if r is None:
            print(f"\n## {name.upper()} (unavailable)")
            continue
        print(f"\n## {r.agent.upper()} ({r.rating}, confidence {r.confidence})")
        print(r.summary)
    print("\n" + "=" * 70)
    print("FINAL SYNTHESIS")
    print("=" * 70)
    print(state["final_report"])


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py TICKER", file=sys.stderr)
        sys.exit(1)

    # A timed-out node's worker thread is abandoned, not stopped (Python
    # can't force-kill a thread) — a normal interpreter shutdown would hang
    # here waiting for it via concurrent.futures' atexit thread-join, on
    # *either* exit path, success or the systemic-failure error below. So
    # both branches flush and skip that wait via os._exit instead of letting
    # the interpreter shut down normally.
    exit_code = 0
    try:
        run_research(sys.argv[1])
    except Exception as exc:
        print(f"\n[fatal] {exc}", file=sys.stderr)
        exit_code = 1

    sys.stdout.flush()
    sys.stderr.flush()
    os._exit(exit_code)
