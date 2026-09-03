"""Phase 0: run the finance-research agents sequentially for one ticker.

No orchestration framework, no infra — just the agent logic, to be validated
before Phase 1 (Terraform) and later parallelized with LangGraph.
"""

import sys
import time

from dotenv import load_dotenv

from agents import aggregator, fundamentals, risk, sentiment, technical

load_dotenv()

AGENTS = [technical, fundamentals, sentiment, risk]


def run_research(ticker: str) -> None:
    ticker = ticker.upper()
    results = []

    for agent in AGENTS:
        name = agent.__name__.rsplit(".", 1)[-1]
        print(f"[{name}] running...", file=sys.stderr)
        start = time.time()
        result = agent.run(ticker)
        elapsed = time.time() - start
        print(f"[{name}] done in {elapsed:.1f}s -> {result.rating} ({result.confidence})", file=sys.stderr)
        results.append(result)

    print(f"\n[aggregator] synthesizing...", file=sys.stderr)
    final_report = aggregator.run(ticker, results)

    print("\n" + "=" * 70)
    print(f"RESEARCH REPORT: {ticker}")
    print("=" * 70)
    for r in results:
        print(f"\n## {r.agent.upper()} ({r.rating}, confidence {r.confidence})")
        print(r.summary)
    print("\n" + "=" * 70)
    print("FINAL SYNTHESIS")
    print("=" * 70)
    print(final_report)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py TICKER", file=sys.stderr)
        sys.exit(1)
    run_research(sys.argv[1])
