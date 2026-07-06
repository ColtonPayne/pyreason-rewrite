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

**MVP scaffolding — campaign not yet started.** The federation glue is in place and
verified: the preflight doctor (`tools/hive_preflight.py`) passes end-to-end on the
authoring machine, the fast test tier is green, and the corpus link gate is green with
this repo registered. Next: the operator fires the campaign charter; its Step 0 re-runs
the preflight on the campaign machine and banks ledger session 0.

## Quick start

```
git config core.hooksPath scripts/hooks   # once per clone
uv run python tools/hive_preflight.py     # Step 0 — must pass before campaign work
uv run pytest -m "not e2e"                # fast tier (what the pre-commit gate runs)
uv run pytest -m e2e                      # acceptance: preflight against the live substrate
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
