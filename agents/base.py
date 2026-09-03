"""Shared plumbing for the finance-research agents."""

from dataclasses import dataclass, field
import os

from google import genai
from google.genai import types
from google.genai.errors import ClientError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_random_exponential

_client = None


def client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GOOGLE_API_KEY not set. Copy .env.example to .env and fill it in."
            )
        _client = genai.Client(api_key=api_key)
    return _client


@dataclass
class AgentResult:
    agent: str
    ticker: str
    rating: str  # bullish / neutral / bearish
    confidence: float  # 0-1
    summary: str
    key_points: list[str] = field(default_factory=list)


@retry(
    wait=wait_random_exponential(min=1, max=60),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(ClientError),
)
def ask_gemini(system: str, user: str, model: str = "gemini-3.7-flash") -> str:
    resp = client().models.generate_content(
        model=model,
        contents=user,
        config=types.GenerateContentConfig(system_instruction=system),
    )
    return resp.text
