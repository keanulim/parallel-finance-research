"""Parse the small structured header every specialist agent is asked to emit."""

import re

from agents.base import AgentResult

_RATING_RE = re.compile(r"RATING:\s*(bullish|neutral|bearish)", re.IGNORECASE)
_CONFIDENCE_RE = re.compile(r"CONFIDENCE:\s*([0-9.]+)")
_POINTS_RE = re.compile(r"^-\s*(.+)$", re.MULTILINE)


def parse_agent_response(agent: str, ticker: str, text: str) -> AgentResult:
    rating_match = _RATING_RE.search(text)
    confidence_match = _CONFIDENCE_RE.search(text)
    points = _POINTS_RE.findall(text)

    return AgentResult(
        agent=agent,
        ticker=ticker,
        rating=rating_match.group(1).lower() if rating_match else "neutral",
        confidence=float(confidence_match.group(1)) if confidence_match else 0.5,
        summary=text.strip(),
        key_points=points[:5],
    )


RESPONSE_FORMAT_INSTRUCTIONS = """
End your response with this exact structured block:

RATING: <bullish|neutral|bearish>
CONFIDENCE: <0.0-1.0>
KEY POINTS:
- <point 1>
- <point 2>
- <point 3>
"""
