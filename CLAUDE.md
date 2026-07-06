<!-- doccode: pyreason-rewrite-CLAUDE -->
# CLAUDE.md — pyreason-rewrite

Campaign repo for the **ground-up pyreason reimagining** (a Fable-window, charter-shaped
campaign). This repo is a **federated consumer** of the ai-hivemind substrate — it lives
*outside* the umbrella tree, so the umbrella's CLAUDE.md does **not** ancestor-load here and
this file must carry the vital rules itself. The full constitution is the
[agent playbook][ai-hivemind-docs-agent-playbook]; the recurring-mistake catalogue is
[ai-coding-pitfalls][ai-hivemind-docs-ai-coding-pitfalls]; the deployment threat model is the
[security model][ai-hivemind-docs-security-model] family. Read the playbook before non-trivial
work.

## Step 0 — preflight, always

Before any campaign work on any machine, run the preflight doctor:

```
uv run python tools/hive_preflight.py
```

It verifies every federated mechanism this repo consumes (umbrella manifest entry, hstate,
the corpus link gate, the lrag `pyreason-analysis` probe, the oracle pin, the ledger seam,
git wiring) with an actionable hint per failure. On a fresh environment, bank the passing
`--json` report as ledger session 0 (see [docs/ledger/README.md][pyreason-rewrite-docs-ledger-README]).
No campaign work starts while the preflight is red.

## Layout & the oracle

- `oracle/pyreason/` — a **read-only** clone of upstream lab-v2/pyreason, detached at the
  commit in `oracle/PIN`. It is the campaign's **equivalence oracle**: the rewrite's e2e
  harness runs the same programs through the oracle and the rewrite and compares. **Never
  modify, rebase, or build work inside it.** Moving the pin is an operator-adjudicated
  decision recorded in the ledger.
- `tools/` — campaign tooling (the preflight doctor lives here).
- `docs/ledger/` — session banking; newest session file is the resume point.
- `tests/` — fast tier always runs; `e2e`-marked tests need the live substrate and are
  deselected by the gate (`uv run pytest -m e2e` to run them explicitly).

## Federation — how this repo reaches the hivemind

The umbrella root resolves as `$HIVEMIND_ROOT`, defaulting to `~/Projects/ai-hivemind`
(both operator laptops mirror `~/Projects` via syncthing). From it:

- **Analysis corpus retrieval** — the operator's clean-room pyreason analysis (two BUG_LOGs
  with ~191 catalogued bugs, a theory glossary, layer/interpretation analyses) is federated
  as the lrag collection `pyreason-analysis`:
  `uv run --directory $HIVEMIND_ROOT/local-rag lrag retrieve "<query>" -c pyreason-analysis --no-sync`.
  Keyword (BM25) retrieval is the default and needs no model daemon. The registry is
  **machine-local and single-writer**: on a fresh machine, ledger session 0 registers +
  syncs the collection once (see [docs/ledger/README.md][pyreason-rewrite-docs-ledger-README]);
  every retrieval after that passes `--no-sync`. Bug reports there are *seeds* for
  understanding, not acceptance criteria.
- **Docs** — this repo's markdown participates in the hivemind cross-repo link graph
  (doc-code markers + reference-style links; convention in
  [cross-repo-links][ai-hivemind-docs-cross-repo-links]). The pre-commit hook runs the
  corpus-wide check whenever a `.md` is staged.

## Hard rules

- **Isolation.** All campaign work happens in this repo. Never write to
  `~/Projects/dyuman-pryeason` (read-only input corpus), the operator's `pyreason` clones,
  or any other tree of his. Never touch `oracle/pyreason` except to read it.
- **No lab compute, at all.** This campaign never reaches the GH200 fleet — no inference
  endpoints, no broker, nothing. Experiments are local and intentionally lightweight
  (screen-then-confirm: a short smoke screen before any long measurement).
- **Toolchain** — uv only (`uv run pytest`, `uv run python …`); `uv.lock` is committed;
  never commit `.venv/` or caches. **Never install anything unprompted** — even `uv add`
  for a new dependency gets explicit operator permission first.
- **Commits** — commit at every green checkpoint, small and focused, message says *why*,
  agent `Co-Authored-By` trailer. Never bypass hooks. Push only when the operator asks.
  One-time per clone: `git config core.hooksPath scripts/hooks`.
- **Testing** — tiered pytest; a failing fast tier means *not done*. Test the I/O seam,
  not just the pure helper. Every test carries a one-line `proves:` docstring matched to
  what it actually asserts.
- **Subagents** — pass an explicit `model:` on every subagent call, capped at Opus
  (`'opus'` for substantive work, `'sonnet'`/`'haiku'` for narrow lookups). Never let a
  subagent inherit the session model.
- **Root cause** — name a cause only after evidence forces it; a guess asserted as a
  finding is the expensive failure mode.
- **Consequential forks** — options + a recommendation, then wait for the operator.
  Correctness-bug divergences from the oracle are operator-adjudicated, each with a
  failing test.

<!-- links:begin -->
[ai-hivemind-docs-agent-playbook]: ../ai-hivemind/docs/agent-playbook.md
[ai-hivemind-docs-ai-coding-pitfalls]: ../ai-hivemind/docs/ai-coding-pitfalls.md
[ai-hivemind-docs-cross-repo-links]: ../ai-hivemind/docs/cross-repo-links.md
[ai-hivemind-docs-security-model]: ../ai-hivemind/docs/security-model.md
[pyreason-rewrite-docs-ledger-README]: docs/ledger/README.md
<!-- links:end -->
