# Learning Log

Kept per the plan's habit: what broke, what I learned, doubles as interview
material later.

## Phase 1 (Terraform foundation)

- `terraform` isn't in Homebrew core anymore — HashiCorp pulled it over a
  licensing dispute a while back. It's only in `hashicorp/tap/terraform` now.
- `brew install awscli` hit the *exact same* `pyexpat`/`libexpat` symbol
  mismatch from Phase 0's venv problem — Homebrew's `python@3.14` bottle on
  this machine, again. AWS CLI v2 doesn't help here since it's not
  pip-installable, so the earlier "just use `~/.local/bin/python3.12`" fix
  didn't directly apply. Fix: isolated venv (`~/.local/bin/python3.12 -m
  venv ~/.local/aws-cli-venv`), pip-installed AWS CLI *v1* into it (still
  fine for `configure`/`sts get-caller-identity`), symlinked its `aws` binary
  into `~/.local/bin` — which already sits before `/opt/homebrew/bin` in
  PATH, so it shadows the broken one without touching Homebrew's install.
  Tried a plain global `pip install --user awscli` first; that Python is
  `uv`-managed and correctly refused (PEP 668 externally-managed-environment)
  rather than risk breaking other tooling with `--break-system-packages`.
- Remote state has a real chicken-and-egg shape: you can't store Terraform's
  state in S3 before the S3 bucket exists, and you can't create the bucket
  with Terraform without state going somewhere. Resolved by bootstrapping
  with plain local state once (`terraform/bootstrap/`), then pointing the
  *next* config's backend at what that created — not an actual loop, just a
  one-time ordering constraint.
- `aws` CLI's configured default region (`us-west-1`) didn't match the
  bootstrap config's default (`us-east-1`) — first `aws dynamodb
  describe-table` call came back `ResourceNotFoundException` purely because
  it silently checked the wrong region. Not a real bug, but exactly the kind
  of false alarm this mismatch causes; worth remembering before assuming
  something's actually broken.
- Decided *not* to migrate the already-applied bootstrap bucket/table from
  us-east-1 to us-west-1 to match — a state bucket's region is functionally
  irrelevant (nothing but Terraform itself ever touches it), so the simpler
  fix was pointing the VPC module's provider at us-west-1 instead and
  leaving bootstrap where it is. Backend `region` and provider `region` are
  independent settings and don't need to match.
- Hand-wrote the VPC module instead of using the community
  `terraform-aws-modules/vpc` registry module, on purpose — the point right
  now is understanding subnets/route-tables/IGW/NAT as primitives, which a
  module would hide. `terraform plan` resolved real AZs via the
  `aws_availability_zones` data source instead of hardcoded names, and it's
  a good thing it did: this account's `us-west-1` only has `1a`/`1c`, no
  `1b`. Hardcoding `us-west-1b` would have failed outright.
- Terraform's `backend {}` block can't reference variables — bucket/region/
  table name have to be literal (or passed via `-backend-config` flags).
  Real limitation, not a style choice: the backend has to be resolved before
  Terraform can evaluate anything else, including variables.
- Validated the VPC module fully (`fmt`/`init`/`validate`/`plan` all clean,
  14 resources, backend connects) but did not `apply` — stopped deliberately
  before creating the NAT Gateway (real hourly cost) rather than spin up and
  immediately tear down infrastructure just to prove it works. Applying is
  the natural next session's first step.

## Phase 2 (containerize)

- No Docker on this machine at all. Installed Colima (`brew install colima
  docker`) instead of Docker Desktop — lightweight, CLI-only, no GUI app, no
  admin-password installer step. `colima start` boots a small Linux VM (macOS
  can't run Linux containers natively — there's no way around a VM boundary
  somewhere) and wires up the Docker socket to it.
- Fresh install still failed on the very first `docker run`: `error getting
  credentials - err: exec: "docker-credential-desktop": executable file not
  found`. `~/.docker/config.json` had `"credsStore": "desktop"` pointing at a
  Docker-Desktop-only credential helper binary that doesn't exist when you're
  not running Desktop. Fix: removed that key from the config — not needed
  for pulling public images anyway.
- Layer-caching order matters more than it looks: `COPY requirements.txt .`
  + `pip install` has to come *before* `COPY . .`, not after. Docker caches
  each instruction as a layer and invalidates everything from the first
  changed instruction onward. Copy-everything-then-install would mean any
  code edit (even a comment in README.md) reinstalls every dependency from
  scratch on every build.
- Verified the built image for real, not just "it built": ran it against a
  live ticker (NVDA) with `--env-file .env` (so the key never gets typed or
  echoed anywhere, including by me) and got a complete 4-agent report with
  real disagreement between the fundamentals and risk agents, same as the
  bare-metal run. Image is 138MB unique content / 636MB total disk usage
  including shared base layers.
- Proved the layer-caching claim empirically rather than trusting the docs:
  rebuilding unchanged took 2.53s (`RUN pip install` showed `Using cache`);
  touching `requirements.txt` and rebuilding took 43.6s (full reinstall,
  every layer from `COPY requirements.txt .` onward invalidated). A cache
  miss invalidates that layer *and every layer after it in the file*, not
  just the changed instruction — which is the actual reason ordering matters,
  not just "put small things first."
- The app was a one-shot CLI (`main.py`, prints a report, exits), but the
  plan's Phase 2 deliverable is specifically a Deployment + Service —
  Kubernetes Deployments expect a long-running process; a container that
  exits looks like a crash and gets restarted (`CrashLoopBackOff`). Added
  `api.py` (FastAPI: `/research/{ticker}`, `/healthz`) as what actually gets
  containerized/deployed; `main.py` stays as a separate local-dev-only path,
  not something the Docker image runs anymore.
- `kind create cluster` runs the entire "Kubernetes node" as one Docker
  container (`kindest/node`) with its own kubelet/containerd inside it —
  confirmed by `docker ps` showing it directly. That node's containerd is
  isolated from the host's Docker/Colima image store, so a locally-built
  image is invisible inside the cluster until `kind load docker-image`
  copies it in — the local-dev substitute for a registry push.
- `imagePullPolicy` defaults to `Always` for a `:latest` tag, which would
  make the pod try to *pull* the image from a registry instead of using the
  one just loaded via `kind load` — and fail, since it was never pushed
  anywhere. Needed `imagePullPolicy: IfNotPresent` explicitly.
- `kubectl get ... -l app=finance-agents` only returned the Pod, not the
  Deployment or Service — because that label lives on the pod template
  (what gets stamped onto pods the Deployment creates) and in the
  selectors, not on the Deployment/Service objects' own metadata. Small
  mixup, but a real one, not just a hypothetical gotcha to watch for.
- Verified past "it built" and "kubectl says Running" to an actual request:
  `kubectl port-forward svc/finance-agents 8000:8000` then `curl
  localhost:8000/research/TSLA` returned a live 4-agent report through the
  real Service, not a mock.

## Phase 0

- Homebrew's python3.11 and python3.14 both have a broken `ensurepip` on this
  machine (`pyexpat`/`libexpat` symbol mismatch — Homebrew's libexpat and the
  system one disagree). `python3 -m venv` fails partway through pip bootstrap.
  Fix: use `~/.local/bin/python3.12` to create the venv instead.
- Swapped the manual `for agent in AGENTS: ...` loop for a LangGraph
  `StateGraph`. Proved empirically (not just assumed) that `.invoke()` runs
  independent nodes concurrently via a thread pool: 4 nodes each sleeping 1s
  finished in 1.01s wall-clock, not 4s. With real yfinance calls in the mix
  the specialists take longer individually (network I/O per node), but they
  still overlap — a 4-node run came back in ~2s once the aggregator's
  dependency wait (fan-in) was accounted for, not ~5s+ of serial execution.
- Switched providers from Claude to Gemini (`google-genai`, `gemini-3.7-flash`)
  to reuse a key already on hand — matched the pattern already proven in the
  THP-RAG project rather than inventing a new one.
- `yfinance`'s `.history()` includes a row for the *current* trading day even
  before the market closes, with `Close`/`High`/`Low` all `NaN`. That NaN
  silently propagated through every derived stat (SMA, 6-month return,
  drawdown) — the technical agent's LLM output reported "price data
  unavailable" even though the code was, on the surface, computing real
  numbers. Only surfaced by actually running the pipeline live against real
  Gemini output and reading what it said, not by unit-testing the math in
  isolation. Fix: `dropna(subset=["Close"])` right after the fetch.
- Added per-node failure handling (retry / containment / timeout / systemic-
  failure detection) to the graph, then found two more real bugs *while
  testing that work*, both concurrency-specific — the kind that only show up
  once things genuinely run in parallel, not in a single-threaded script:
  - `concurrent.futures.ThreadPoolExecutor` registers a global `atexit` hook
    that joins **every** worker thread it has ever created, from every
    executor, before the interpreter exits — not just threads still inside a
    `with` block. A timed-out node's worker thread can't be force-killed
    (Python threads never can be), only abandoned, so a normal script exit
    hung waiting for it anyway, even after the script's own logic had
    already finished and printed its output. Fix: `os._exit()` after
    flushing stdout/stderr, skipping the graceful-shutdown thread-join
    entirely. Caught by literally running the timeout test and watching the
    process not exit — the "it timed out correctly" log line printed, and
    the process still didn't return.
  - A single shared `genai.Client` instance, called from 4 concurrent
    threads, intermittently raised `RuntimeError("Cannot send a request, as
    the client has been closed")` — httpx's guard against reusing a client
    after `.close()`, which `genai.Client.__del__` calls on garbage
    collection. Rather than dig into why concurrent use was triggering that,
    switched to one `genai.Client` per thread (`threading.local()`) — it
    sidesteps the question of whether the SDK is safe to share across
    threads instead of relying on undocumented internals. Confirmed fixed
    with repeated live runs, since the original failure wasn't consistently
    reproducible.
