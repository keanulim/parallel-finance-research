# Parallel Finance-Research Agents

Phase 0 of the [Self-Service Developer Platform + Parallel Finance-Research
Agents](../) project: four specialist research agents (technical,
fundamentals, sentiment, risk) plus an aggregator, run sequentially against
one ticker. No infra yet — that's Phase 1+ (Terraform/K8s/CI/CD), which will
host this app once the agent logic itself is proven out.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in ANTHROPIC_API_KEY
```

## Run

```bash
python main.py AAPL
```

## Structure

- `agents/technical.py` — price action, moving averages, momentum, volatility
- `agents/fundamentals.py` — valuation, profitability, balance sheet
- `agents/sentiment.py` — recent news headlines
- `agents/risk.py` — drawdown, leverage, volatility (downside-only lens)
- `agents/aggregator.py` — synthesizes the four reports into one note
- `data/market_data.py` — yfinance wrappers (no API key required)
- `main.py` — CLI entrypoint, runs agents sequentially

## Next steps (per the plan)

- Parallelize the four agents with `asyncio.gather` (toy example first),
  then LangGraph for real fan-out/fan-in + failure handling.
- Once the logic is solid, containerize and move to the infra phases.
