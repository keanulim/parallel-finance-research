from agents.base import AgentResult, ask_claude
from agents.parsing import RESPONSE_FORMAT_INSTRUCTIONS, parse_agent_response
from data.market_data import get_recent_news

SYSTEM = """You are a news-sentiment analysis agent on a finance-research team.
Analyze recent headlines/summaries only — tone, narrative, catalysts.
Do not comment on price action or valuation. Be concise and specific."""


def run(ticker: str) -> AgentResult:
    news = get_recent_news(ticker)

    if not news:
        headlines = "No recent news found."
    else:
        headlines = "\n".join(
            f"- [{n['publisher']}] {n['title']}: {n['summary'] or ''}".strip()
            for n in news
        )

    prompt = f"""Ticker: {ticker}
Recent headlines:
{headlines}

Give a short sentiment read (3-4 sentences), then the structured block.
{RESPONSE_FORMAT_INSTRUCTIONS}"""

    text = ask_claude(SYSTEM, prompt)
    return parse_agent_response("sentiment", ticker, text)
