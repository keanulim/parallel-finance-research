# Learning Log

Kept per the plan's habit: what broke, what I learned, doubles as interview
material later.

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
