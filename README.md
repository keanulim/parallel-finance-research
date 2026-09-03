# Parallel Finance-Research Agents

Phase 0 of the Self-Service Developer Platform + Parallel Finance-Research
Agents project: four specialist research agents (technical, fundamentals,
sentiment, risk) plus an aggregator, orchestrated with LangGraph so the four
specialists run concurrently and fan back in to the aggregator once all four
finish. No infra yet — that's Phase 1+ (Terraform/K8s/CI/CD), which will host
this app once the agent logic itself is proven out.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in GOOGLE_API_KEY
```

## Run

```bash
python main.py AAPL
```

## Run in Docker

```bash
docker build -t finance-research-agents .
docker run --rm --env-file .env finance-research-agents AAPL
```

## Structure

- `agents/technical.py` — price action, moving averages, momentum, volatility
- `agents/fundamentals.py` — valuation, profitability, balance sheet
- `agents/sentiment.py` — recent news headlines
- `agents/risk.py` — drawdown, leverage, volatility (downside-only lens)
- `agents/aggregator.py` — synthesizes the four reports into one note
- `data/market_data.py` — yfinance wrappers (no API key required)
- `graph.py` — LangGraph `StateGraph`: fan-out to the 4 specialists, fan-in to
  the aggregator, per-node timeout/failure containment, systemic-failure
  detection
- `main.py` — CLI entrypoint, invokes the compiled graph
- `Dockerfile` / `.dockerignore` — containerizes the app (Python 3.12-slim,
  no secrets baked in — `GOOGLE_API_KEY` is injected at `docker run` time)

## Next steps (per the plan)

- Move to Phase 1 (Terraform foundation) — S3 + DynamoDB remote state, then a
  VPC module.
- Eventually deploy this image to a local `kind`/`minikube` cluster (Phase 2).
