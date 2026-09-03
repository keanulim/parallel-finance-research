# Learning Log

Kept per the plan's habit: what broke, what I learned, doubles as interview
material later.

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
