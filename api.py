"""HTTP API for the research graph: what runs in the container in
Kubernetes. main.py (the CLI) is for local, non-containerized runs.
"""

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException

from agents.base import AgentResult
from graph import build_graph

load_dotenv()

app = FastAPI(title="Parallel Finance-Research Agents")
graph = build_graph()


def _serialize(result: AgentResult | None) -> dict | None:
    if result is None:
        return None
    return {
        "rating": result.rating,
        "confidence": result.confidence,
        "summary": result.summary,
        "key_points": result.key_points,
    }


@app.get("/healthz")
def healthz():
    """Liveness/readiness probe target — Kubernetes hits this to decide if
    the pod is up and should receive traffic."""
    return {"status": "ok"}


@app.get("/research/{ticker}")
def research(ticker: str):
    ticker = ticker.upper()
    try:
        state = graph.invoke({"ticker": ticker})
    except RuntimeError as exc:
        # Systemic failure (see graph.py) — most agents down, not just one.
        raise HTTPException(status_code=503, detail=str(exc))

    return {
        "ticker": ticker,
        "technical": _serialize(state.get("technical")),
        "fundamentals": _serialize(state.get("fundamentals")),
        "sentiment": _serialize(state.get("sentiment")),
        "risk": _serialize(state.get("risk")),
        "final_report": state["final_report"],
    }
