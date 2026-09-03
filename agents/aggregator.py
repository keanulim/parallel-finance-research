from agents.base import AgentResult, ask_gemini

SYSTEM = """You are the lead analyst on a finance-research team. You receive
independent reports from up to four specialist agents (technical, fundamentals,
sentiment, risk) and must synthesize them into one final research note.
Where agents disagree, say so explicitly rather than papering over it. If an
agent's report is missing, treat it as genuinely unknown — do not guess what
it would have said or silently treat the missing view as neutral."""


def run(ticker: str, results: list[AgentResult], missing: list[str] | None = None) -> str:
    reports = "\n\n".join(
        f"--- {r.agent.upper()} AGENT (rating: {r.rating}, confidence: {r.confidence}) ---\n{r.summary}"
        for r in results
    )

    missing_note = ""
    if missing:
        missing_note = (
            f"\nNote: the following agents were unavailable and produced no "
            f"report this run: {', '.join(missing)}. Explicitly flag these as "
            f"unknown in your note rather than assuming a neutral view.\n"
        )

    prompt = f"""Ticker: {ticker}
{missing_note}
{reports}

Write a final research note with:
1. An overall call (bullish/neutral/bearish) with a one-line reason.
2. A short synthesis paragraph.
3. Any notable disagreement between agents.
4. Key risks to the thesis.
5. If any agents were unavailable, note that explicitly and how it limits confidence in this note."""

    return ask_gemini(SYSTEM, prompt)
