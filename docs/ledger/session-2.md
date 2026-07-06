# Session 2 — the AC-2 harness spine, self-proved and adversarially reviewed

Date: 2026-07-06 (same sitting as sessions 0–1)

## Verdict

The oracle-differential harness exists, self-proves (oracle-vs-oracle PASS on the seed
corpus, repeats green, digests stable), and survived the charter's review gate — two
independent Opus reviews, 23 distinct findings, 20 fixed and 3 down-rated/declined with
recorded rationale; AC-2 is mechanism-complete and consumed by the board (13/52 surface
rows now `cased`).

## Evidence

- **The spine** (`harness/`): `capture` runs one case per engine in a bare subprocess
  (env inherited, `PYTHONHASHSEED=0` pinned) and emits a self-describing artifact;
  `compare` is stdlib-only (canonical form with documented decisions — numeric type is
  not contract, non-finite sentinels, unreducible types raise; exact-by-default,
  per-probe tolerance with rationale; list order is contract); `run` pairs every
  verdict-bearing run with a same-engine repeat and judges pass / divergent /
  irreproducible / error — self-proof mode (one engine both sides) cannot emit a
  divergence by construction.
- **Self-proof:** `uv run pytest -m e2e` → oracle-vs-oracle PASS on `hello-world`
  (26.9s, four fresh-process captures); verdict-of-record banked as
  [session-2-oracle-vs-oracle.json](session-2-oracle-vs-oracle.json). Warm per-capture
  timing: import ~1.3s, reason ~2.8s.
- **Review gate:** [docs/reviews/2026-07-06-harness.md](../reviews/2026-07-06-harness.md)
  (raw reviewer files committed beside it; report fidelity-checked by an independent
  agent, three attribution nits fixed). The two Highs — a stale-artifact/ignored-rc
  false-PASS path, and a probe calling a method absent at the pin — are both fixed and
  regression-tested.
- **Gates:** fast tier 35 passed (compare layer, judge taxonomy, capture-seam, case
  validation, inventory, preflight); links gate green on every commit.
- **Board:** `docs/surface.md` — 13 rows `cased` by hello-world, 39 `uncovered`;
  input-class coverage 0/~420 proven (no rewrite exists yet — `cased` marks harness
  coverage, `equivalent` awaits oracle-vs-rewrite runs).

## Committed

- `253f6be` — harness: the AC-2 differential spine; first oracle-vs-oracle PASS.
- `4b8f63c` — harness: the review's 20 confirmed findings fixed; report + raw reviews.
- (this commit) — ledger: session 2 banked; surface rows flipped to `cased`.

## NEXT

Grow the seed corpus against the board, spine-first: author cases from `docs/surface.md`
rows for `fn:reason`'s convergence modes (`conv-perfect` / `conv-delta-interp` /
`conv-delta-bound`), `setting:persistent`, an inconsistency path, and a first tranche of
`dsl:rule-text` / `dsl:fact-text` malformed classes (error-message probes will need a
small `expect-raise` probe kind in capture) — run oracle-vs-oracle on the grown corpus,
flip covered rows to `cased`, and bank the run.

## Deviations

- None from the charter's Phase-2 shape. The review gate ran in-session rather than
  waiting for a session boundary — the harness is the campaign's proof spine, so its
  trustworthiness was gated before anything downstream leans on it.

## Asks queued

None.

## Idea seeds

- The pin's own `docs/hello-world.py` is stale against the pinned API (old `Fact`
  signature, `get_interpretation_dict` vs `get_dict`) — a post-window upstream-docs
  contribution candidate (upstream work is out of in-window scope, operator-gated).
