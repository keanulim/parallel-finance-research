"""Shared plumbing for the finance-research agents."""

from dataclasses import dataclass, field
import os
import threading

from google import genai
from google.genai import types
from google.genai.errors import ClientError, ServerError
from tenacity import retry, retry_if_exception, stop_after_attempt, wait_random_exponential

# One genai.Client per thread, not a shared global singleton. The specialist
# agents run concurrently (LangGraph's thread pool, plus another thread layer
# from graph.py's per-node timeout wrapper), and a single shared Client was
# observed failing with "Cannot send a request, as the client has been
# closed" under that concurrency — genai.Client.__del__ calls close() on GC,
# and something about concurrent use was triggering that. Thread-local
# storage sidesteps the question of whether the SDK is safe to share across
# threads entirely, rather than relying on undocumented internals.
_thread_local = threading.local()


def client() -> genai.Client:
    if not hasattr(_thread_local, "client"):
        api_key = os.environ.get("GOOGLE_API_KEY")
        if not api_key:
            raise RuntimeError(
                "GOOGLE_API_KEY not set. Copy .env.example to .env and fill it in."
            )
        _thread_local.client = genai.Client(api_key=api_key)
    return _thread_local.client


@dataclass
class AgentResult:
    agent: str
    ticker: str
    rating: str  # bullish / neutral / bearish
    confidence: float  # 0-1
    summary: str
    key_points: list[str] = field(default_factory=list)


def _is_retryable(exc: BaseException) -> bool:
    """Server errors and rate limits are worth retrying. Other 4xx (bad
    request, bad auth) will fail identically every time — retrying just
    delays the inevitable and burns quota."""
    if isinstance(exc, ServerError):
        return True
    if isinstance(exc, ClientError):
        return exc.code == 429
    return False


@retry(
    wait=wait_random_exponential(min=1, max=60),
    stop=stop_after_attempt(5),
    retry=retry_if_exception(_is_retryable),
)
def ask_gemini(system: str, user: str, model: str = "gemini-3.7-flash") -> str:
    resp = client().models.generate_content(
        model=model,
        contents=user,
        config=types.GenerateContentConfig(system_instruction=system),
    )
    return resp.text
