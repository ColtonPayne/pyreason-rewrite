# Session 32 — the Phase-4 boundary sweep banks its verdict-of-record: 116/116 PASS in one clean invocation

Date: 2026-07-12

## Verdict

**The Phase-4 boundary sweep is banked and independently approved with
zero fixes: the full 116-case corpus, oracle-vs-rewrite, PASSED 116/116
in one clean single invocation** (`resumed: false`, proven structurally
and against all 1097 result files' mtimes and birthtimes; wall-clock
2308 s), zero cross-engine divergences, zero same-engine
irreproducibility, zero spot-fixes needed. This is the
verdict-of-record for the current tree — the Option-B state (pure-Python
core with the session-28 optimizations) — banked ahead of the
operator's execution-layer word under the operator's overnight
directive (2026-07-12): the evidence stands for the tree as it is; a
decision for Option A or C would force a fresh sweep over the changed
tree. Fast tier **321**. The campaign remains blocked on the
execution-layer commitment.

## Evidence

- **Author report:**
  [docs/reviews/2026-07-12-phase4-boundary-sweep-author.md](../reviews/2026-07-12-phase4-boundary-sweep-author.md)
  — the invocation of record (`PYTHONHASHSEED=0 uv run python -m
  harness.run --cases harness/cases --engine-a oracle-env/bin/python
  --engine-b scripts/rewrite-python --results
  results-phase4-boundary`), taxonomy counts, and the honesty note: a
  first launch was killed ~34 s in by a session-host interruption, its
  3-case partial directory deleted wholesale; the banked artifact is
  entirely the second, uninterrupted invocation.
- **Independent review (approved, zero fixes):**
  [docs/reviews/2026-07-12-phase4-boundary-sweep-review.md](../reviews/2026-07-12-phase4-boundary-sweep-review.md)
  — the reviewer's own verdict derivation through the pure judge over
  the on-disk artifacts (uniform invocation identity across all
  completion markers, 464/464 artifact hashes verified, case digests
  vs committed case files, capture-order physicality in all 116 case
  dirs), plus a stratified 7-case live rerun — ALL PASS, 28/28
  digest/probe/engine maps identical to the banked artifact.
- **Tests:** `uv run pytest -m "not e2e"` → 321 passed, 6 deselected
  (author and reviewer independently). Oracle pin byte-clean at
  `e1a94af3` (both agents). No installs; results dir git-ignored by
  the committed `results*/` glob.

## Committed

- `a2a20e7` — docs: the boundary sweep's author report; 116/116 PASS,
  clean single invocation, contingent verdict-of-record framing.
- `ec6537b` — docs: the independent review — approved, zero fixes; own
  derivation + 7-case live sample.
- (this commit) — ledger: session 32 banked; campaign log continued.

## NEXT

**Blocked on the operator — the execution-layer commitment** (charter
phase 4, operator-signed):
[docs/perf/execution-layer-options.md](../perf/execution-layer-options.md),
recommendation **Option B**. With the word given:
- **Option B** → the boundary sweep banked this session already stands
  as the verdict-of-record; next is the AC-5 closure audit and the
  execution-layer ADR (AC-5.5 version-headroom statement per the
  choice), then the AC-7 window-close pickup drill.
- **Option A or C** → the tree changes, so a fresh boundary sweep
  follows whatever session lands that change.
Ungated at any time: the AC-7 pickup drill (a cold Opus subagent run
mid-campaign is still unbanked as a window-close drill). Non-blocking
ask outstanding: the oracle-env numba-cache re-baseline (session-29
review F2). A fresh session picks up with `/campaign`; the resume
point is this file.

## Deviations

- The boundary sweep ran **ahead of** session-31's gate ordering
  (which slotted it after the execution-layer word), under the
  operator's overnight keep-going directive (2026-07-12). The
  contingent framing above carries the consequence: the evidence binds
  to the current tree, and Options A/C would require a re-sweep.

## Asks queued

- **Execution-layer commitment** (blocking): the memo, recommendation
  B; the operator's question is stated at the memo's end.
- **Oracle-env cache re-baseline** (non-blocking): session-29 review
  F2; recommendation to regenerate from a bare capture sweep and
  re-bank count + digests.

## Divergences

- None opened or updated (next free stays DIV-0004).

## Friction

- **Session-host background tasks** — expected: a long sweep runs
  undisturbed; actual: the first launch was killed ~34 s in by a
  session-host background-task interruption (same class as the
  phase-3 sweep incident). Workaround: relaunch `nohup`-detached;
  partial results dir deleted wholesale to preserve the
  single-invocation form. Cost: ~1 min plus the partial dir's cleanup.
  Recommendation: detach any invocation expected to run tens of
  minutes as a matter of course.

## Idea seeds

- None new; session-31's stand (the prange mechanism question stays
  unclaimed unless an Option-C numba spike is authorized).
