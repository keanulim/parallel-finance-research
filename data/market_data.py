"""Free-tier market data pulls via yfinance. No API key required."""

import yfinance as yf


def get_price_history(ticker: str, period: str = "6mo"):
    hist = yf.Ticker(ticker).history(period=period)
    if hist.empty:
        raise ValueError(f"No price history for {ticker}")
    return hist


def get_fundamentals(ticker: str) -> dict:
    info = yf.Ticker(ticker).info
    keys = [
        "shortName", "sector", "industry", "marketCap", "trailingPE",
        "forwardPE", "priceToBook", "debtToEquity", "returnOnEquity",
        "revenueGrowth", "grossMargins", "operatingMargins", "profitMargins",
        "totalCash", "totalDebt", "freeCashflow", "currentRatio",
        "dividendYield", "beta", "fiftyTwoWeekHigh", "fiftyTwoWeekLow",
    ]
    return {k: info.get(k) for k in keys}


def get_recent_news(ticker: str, limit: int = 8) -> list[dict]:
    news = yf.Ticker(ticker).news or []
    out = []
    for item in news[:limit]:
        content = item.get("content", item)
        out.append({
            "title": content.get("title"),
            "publisher": (content.get("provider") or {}).get("displayName"),
            "summary": content.get("summary"),
        })
    return out
