<!-- doccode: pyreason-rewrite-README -->
# pyreason-rewrite

Campaign repo for the **ground-up pyreason reimagining**: understand what pyreason is good
at, where the code breaks, and the common pain points; then rewrite it as an
API-compatible sibling with an e2e differential harness proving equivalence against the
pinned upstream **oracle** (`oracle/pyreason` at the commit in `oracle/PIN`) — every
divergence an operator-adjudicated correctness bug with a failing test. The campaign runs
charter-shaped in the Fable window; agent rules live in [CLAUDE.md][pyreason-rewrite-CLAUDE].

This repo is also the first **federated consumer** of the ai-hivemind substrate (the
hivemind-portability MVP): it is registered in the umbrella `repos.toml`, its docs join the
cross-repo link graph, and the operator's clean-room analysis corpus federates in as the
lrag collection `pyreason-analysis`.

## Status

**The authoritative state is always the newest `docs/ledger/session-<N>.md`** — read that,
not this snapshot, to resume work. Snapshot as of 2026-07-12 (session 33): the rewrite is
live and API-equivalent — all 52 `docs/surface.md` rows at `equivalent`, the Phase-4
boundary sweep banked **116/116 PASS** oracle-vs-rewrite in one clean invocation
(session 32), and the execution layer operator-signed as the pure-Python core
([ADR 0004](docs/adr/0004-execution-layer-pure-python-core.md)); the AC-5 maintainability
bars are closed 5/5. Performance record: `docs/perf/` (ladder baselines, profiles, the
Pokec scaling replication).

## Quick start

```
git config core.hooksPath scripts/hooks   # once per clone
uv run python tools/hive_preflight.py     # Step 0 — must pass before campaign work
uv run pytest -m "not e2e"                # fast tier (what the pre-commit gate runs)
uv run pytest -m e2e                      # acceptance: needs the live substrate; the
                                          # oracle-vs-oracle corpus test alone takes 20+ min
                                          # (it reruns the full case corpus through the
                                          # oracle twice) — a long quiet stretch is normal
```

## Layout

- `oracle/` — `PIN` (the pinned upstream SHA) + `pyreason/` (read-only oracle clone,
  untracked here — its own git history).
- `tools/` — campaign tooling; `hive_preflight.py` is the federation preflight doctor.
- `tests/` — fast-tier seam tests + the `e2e`-marked acceptance test.
- `docs/ledger/` — session banking seam; newest `session-<N>.md` is the resume point.
- `scripts/hooks/` — the committed pre-commit gate (fast tests + corpus link check).

<!-- links:begin -->
[pyreason-rewrite-CLAUDE]: CLAUDE.md
<!-- links:end -->
