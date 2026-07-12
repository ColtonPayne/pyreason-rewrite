# Session 30 — the case-seed batch banks: 10 cases, two parser models fixed to the pin, the corpus reaches 115

Date: 2026-07-12

## Verdict

**The carried case-seed backlog is cleared.** 18 arms pin-screened → 10
new cases, **10/10 PASS oracle-vs-rewrite** (author and review runs,
separate results dirs), 0 un-bankable arms, 0 divergences: the
`raise_errors=False` warn-skip family (4 cases), the loader widenings
(ragged CSV, weights-dtype trio, delta variants incl. 0), the
never-grounded closed-world predicate, and the O1/O2 graphml coercion
arms (batch §B23/§B24 — the inverted-pair static freeze and its
node/edge resolve asymmetry, now observed by a committed case instead
of a review probe). Two rewrite parser gaps were screen-forced to
pinned behavior (delta dtype semantics; weights conversion), and the
review's independent re-derivation caught **three further coercion
classes** outside the author's sampled points (pinned OverflowError
past C-long max; tuple weights accepted; scalar weights' unsized-len
message) — fixed with seam tests. Fast tier **310**. The session also
absorbed a mid-run interruption cleanly: the author was cut off by a
transient API failure with work uncommitted, resumed against ground
truth, and the review audited the recovery (all commits coherent).

## Evidence

- **Author report:**
  [docs/reviews/2026-07-12-case-seed-batch-author.md](../reviews/2026-07-12-case-seed-batch-author.md)
  — the 18-arm triage table, the banked pin facts (invalid loader
  cells split skip-vs-load-with-default; nested weights accepted;
  delta uint16 wrap at sampled points; all-nodes fallback for
  never-grounded closed-world predicates), the interruption-recovery
  note.
- **Independent review (approved-with-fixes):**
  [docs/reviews/2026-07-12-case-seed-batch-review.md](../reviews/2026-07-12-case-seed-batch-review.md)
  — both engine models re-derived at the pin with off-sample screens
  (F1 delta OverflowError + raise ordering; F2 tuple weights; F3
  scalar message); triage completeness verified (interval-nonnumeric
  present); the graphml-static-pin case's probes genuinely observe
  the frozen bounds; warn-skip compared surface honestly scoped
  (warnings ride the diagnostic log, not the compared value); 10/10
  rerun PASS; recovery audit clean.
- **Tests:** `uv run pytest -m "not e2e"` → 310 passed, 5 deselected;
  inventory gate green; oracle pin byte-clean.
- **Corpus:** committed cases now 96 + 3 (ladder) + 6 (session 29) +
  10 = **115**; the deferred full-corpus sweep is named below.

## Committed

- `92eed57` — rewrite: delta + weights conversion semantics fixed to
  the pin (8 seam tests).
- `4b87f2e` — cases: 10 new cases + 13 fixtures.
- `7cc5678` — board: touched rows widened; interacts-unknown-predicate
  banked.
- `99b1351` — docs: session-30 author report.
- `1dd1bf9` — review fixes: three coercion-class corrections + 5 seam
  tests.
- `d60dc16` — docs: session-30 review report.
- (this commit) — ledger: session 30 banked; campaign log continued.

## NEXT

**The harness-quality seed batch — the last unblocked thread:** (1)
**sweep durability** — make the full-corpus runner resumable/idempotent
per case so a host interruption mid-sweep (the session-24 incident,
repeated in miniature this session) loses one case, not the invocation;
(2) the **pyyaml-version parity tripwire** (fast-tier test pinning the
campaign env's pyyaml against the recorded expectation); (3)
**artifact-schema `inputs` echo** (capture artifacts echo their full
input record for self-description); (4) **`probe_s` timing** in
capture artifacts; (5) **multi-rule prange characterization** — a
screened characterization of the pinned parallel kernel's multi-rule
behavior, banked as a board note (measurement, not a case, unless the
screen shows a bankable deterministic arm). All local, no deps, no
gates. **This is the last unblocked NEXT**: after it banks, every
remaining thread waits on the operator (the execution-layer
commitment → then the Phase-4 boundary sweep over the now-115-case
corpus; the cache re-baseline). The loop stops there with the asks
queued.

**Blocked asks standing:** (1) execution-layer commitment
([docs/perf/execution-layer-options.md](../perf/execution-layer-options.md),
recommendation B); (2) oracle-env numba-cache re-baseline (session-29
review F2, non-blocking).

## Deviations

- The author was terminated mid-packet by a transient API connection
  failure (environment, not work); resumed against ground truth with
  nothing lost. The exit taxonomy's environment-failure handling
  applied at the orchestration layer.

## Asks queued

- Carried: the execution-layer commitment (blocking Phase-4 closure);
  the oracle-env cache re-baseline (non-blocking).

## Divergences

- None opened; the batch surfaced no cross-engine mismatch.

## Idea seeds

- The pin's skip-vs-load-with-default split on invalid loader cells
  (bad `end_time` silently loads `end=start`) is quirk-class material
  for any future upstream-contribution triage (post-window scope).
- Carried: sweep durability; `probe_s` timing; multi-rule prange
  characterization; pyyaml parity tripwire; artifact `inputs` echo —
  all now scheduled in NEXT.
