# Parallel Finance-Research Agents

Phase 0/2 of the Self-Service Developer Platform + Parallel Finance-Research
Agents project: four specialist research agents (technical, fundamentals,
sentiment, risk) plus an aggregator, orchestrated with LangGraph so the four
specialists run concurrently and fan back in to the aggregator once all four
finish. Containerized and deployed to a local Kubernetes cluster (`kind`).
Phase 1 (Terraform/AWS foundation) in progress — see `terraform/`.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in GOOGLE_API_KEY
```

## Run locally (CLI)

```bash
python main.py AAPL
```

## Run locally (API server)

```bash
uvicorn api:app --reload
curl http://localhost:8000/research/AAPL
```

## Run in Docker

The image runs the API server (`api.py`), not the CLI — this is what gets
deployed to Kubernetes.

```bash
docker build -t finance-research-agents .
docker run --rm -p 8000:8000 --env-file .env finance-research-agents
curl http://localhost:8000/research/AAPL
```

## Run in Kubernetes (local, via kind)

```bash
kind create cluster --name finance-agents
kind load docker-image finance-research-agents:latest --name finance-agents
kubectl create secret generic finance-agents-secrets --from-env-file=.env
kubectl apply -f k8s/deployment.yaml -f k8s/service.yaml
kubectl port-forward svc/finance-agents 8000:8000
curl http://localhost:8000/research/AAPL
```

`kind load docker-image` is the local-dev substitute for a registry — the
cluster's node runs its own isolated containerd, so a `docker build` on the
host isn't visible inside it without this step (or, later, a real registry
push in Phase 1+).

## AWS foundation (Terraform)

Requires an IAM user's credentials via `aws configure` — never the root
account. `terraform/bootstrap` creates the S3 bucket + DynamoDB table that
later Terraform configs use as their remote state backend; it necessarily
runs with local state itself (see LEARNING.md for why).

```bash
cd terraform/bootstrap
cp terraform.tfvars.example terraform.tfvars  # edit: pick a globally-unique bucket name
terraform init
terraform plan
terraform apply
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
- `main.py` — CLI entrypoint (local dev only, not what's containerized)
- `api.py` — FastAPI server (`/research/{ticker}`, `/healthz`) — this is what
  the Docker image and Kubernetes Deployment actually run
- `Dockerfile` / `.dockerignore` — containerizes the app (Python 3.12-slim,
  no secrets baked in — `GOOGLE_API_KEY` is injected via env at runtime,
  never at build time)
- `k8s/deployment.yaml` / `k8s/service.yaml` — Deployment (1 replica,
  liveness/readiness probes on `/healthz`) + ClusterIP Service
- `terraform/bootstrap/` — S3 bucket (versioned, encrypted, public access
  blocked, `prevent_destroy`) + DynamoDB lock table for remote state

## Next steps (per the plan)

- Finish Phase 1: point a real config's backend at the bootstrap output,
  then build the VPC module (2 AZs, public+private subnets, IGW, NAT gateway).
- Phase 3: CI/CD — lint/test, build + push the image, `terraform plan` on PRs.
- Phase 4: ephemeral PR preview environments (the centerpiece) — this
  Deployment/Service pair is the template that gets templated per-branch.
