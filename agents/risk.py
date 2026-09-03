from agents.base import AgentResult, ask_claude
from agents.parsing import RESPONSE_FORMAT_INSTRUCTIONS, parse_agent_response
from data.market_data import get_fundamentals, get_price_history

SYSTEM = """You are a risk analysis agent on a finance-research team.
Analyze downside risk only — volatility, leverage, drawdown history,
concentration/sector risk. Do not give a bullish/bearish price call on
fundamentals or news; focus purely on what could go wrong and how badly.
Be concise and specific."""


def run(ticker: str) -> AgentResult:
    hist = get_price_history(ticker)
    fundamentals = get_fundamentals(ticker)
    closes = hist["Close"]

    drawdown = (closes / closes.cummax() - 1).min() * 100
    volatility = closes.pct_change().std() * (252 ** 0.5) * 100

    prompt = f"""Ticker: {ticker}
Max drawdown (6mo): {drawdown:.1f}%
Annualized volatility: {volatility:.1f}%
Beta: {fundamentals.get('beta')}
Debt/Equity: {fundamentals.get('debtToEquity')}
Current ratio: {fundamentals.get('currentRatio')}
Sector: {fundamentals.get('sector')}

Give a short risk read (3-4 sentences), then the structured block.
For this agent, RATING means: bullish = low risk, bearish = high risk.
{RESPONSE_FORMAT_INSTRUCTIONS}"""

    text = ask_claude(SYSTEM, prompt)
    return parse_agent_response("risk", ticker, text)
