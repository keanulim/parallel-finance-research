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
