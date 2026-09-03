from agents.base import AgentResult, ask_claude
from agents.parsing import RESPONSE_FORMAT_INSTRUCTIONS, parse_agent_response
from data.market_data import get_price_history

SYSTEM = """You are a technical analysis agent on a finance-research team.
Analyze price action only — trend, momentum, moving averages, support/resistance,
volatility. Do not comment on fundamentals or news. Be concise and specific."""


def run(ticker: str) -> AgentResult:
    hist = get_price_history(ticker)
    closes = hist["Close"]

    sma20 = closes.rolling(20).mean().iloc[-1]
    sma50 = closes.rolling(50).mean().iloc[-1] if len(closes) >= 50 else None
    sma50_str = f"{sma50:.2f}" if sma50 else "N/A"
    last = closes.iloc[-1]
    six_month_return = (last / closes.iloc[0] - 1) * 100
    volatility = closes.pct_change().std() * (252 ** 0.5) * 100  # annualized

    prompt = f"""Ticker: {ticker}
Last close: {last:.2f}
20-day SMA: {sma20:.2f}
50-day SMA: {sma50_str}
6-month return: {six_month_return:.1f}%
Annualized volatility: {volatility:.1f}%
52-week high: {hist['High'].max():.2f}
52-week low: {hist['Low'].min():.2f}

Give a short technical read (3-4 sentences), then the structured block.
{RESPONSE_FORMAT_INSTRUCTIONS}"""

    text = ask_claude(SYSTEM, prompt)
    return parse_agent_response("technical", ticker, text)
