"""Shared plumbing for the finance-research agents.

Phase 0 scope: agents run sequentially in one process. No orchestration
framework yet — that's introduced later (LangGraph) once this logic works.
"""

from dataclasses import dataclass, field
import os

from anthropic import Anthropic

_client = None


def client() -> Anthropic:
    global _client
    if _client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY not set. Copy .env.example to .env and fill it in."
            )
        _client = Anthropic(api_key=api_key)
    return _client


@dataclass
class AgentResult:
    agent: str
    ticker: str
    rating: str  # bullish / neutral / bearish
    confidence: float  # 0-1
    summary: str
    key_points: list[str] = field(default_factory=list)


def ask_claude(system: str, user: str, model: str = "claude-sonnet-5") -> str:
    resp = client().messages.create(
        model=model,
        max_tokens=1024,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return resp.content[0].text
