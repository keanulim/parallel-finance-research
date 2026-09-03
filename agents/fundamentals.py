from agents.base import AgentResult, ask_gemini
from agents.parsing import RESPONSE_FORMAT_INSTRUCTIONS, parse_agent_response
from data.market_data import get_fundamentals

SYSTEM = """You are a fundamentals analysis agent on a finance-research team.
Analyze valuation, profitability, growth, and balance-sheet health only.
Do not comment on price action or news sentiment. Be concise and specific."""


def run(ticker: str) -> AgentResult:
    fundamentals = get_fundamentals(ticker)

    lines = "\n".join(f"{k}: {v}" for k, v in fundamentals.items() if v is not None)
    prompt = f"""Ticker: {ticker}
{lines}

Give a short fundamentals read (3-4 sentences), then the structured block.
{RESPONSE_FORMAT_INSTRUCTIONS}"""

    text = ask_gemini(SYSTEM, prompt)
    return parse_agent_response("fundamentals", ticker, text)
