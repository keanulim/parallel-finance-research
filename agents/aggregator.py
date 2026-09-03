from agents.base import AgentResult, ask_claude

SYSTEM = """You are the lead analyst on a finance-research team. You receive
independent reports from four specialist agents (technical, fundamentals,
sentiment, risk) and must synthesize them into one final research note.
Where agents disagree, say so explicitly rather than papering over it."""


def run(ticker: str, results: list[AgentResult]) -> str:
    reports = "\n\n".join(
        f"--- {r.agent.upper()} AGENT (rating: {r.rating}, confidence: {r.confidence}) ---\n{r.summary}"
        for r in results
    )

    prompt = f"""Ticker: {ticker}

{reports}

Write a final research note with:
1. An overall call (bullish/neutral/bearish) with a one-line reason.
2. A short synthesis paragraph.
3. Any notable disagreement between agents.
4. Key risks to the thesis."""

    return ask_claude(SYSTEM, prompt)
