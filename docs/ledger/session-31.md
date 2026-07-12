# Session 31 — the harness-quality batch lands; the unblocked queue is empty and the campaign waits on the operator

Date: 2026-07-12

## Verdict

**All five harness-quality seeds are landed and reviewed** — (1) the
full-corpus runner is now **interruption-durable**: per-case atomic
completion markers with invocation identity and per-artifact hashes,
hash-re-verified on every resume decision; a resumed sweep re-judges
completed cases from artifacts through the same pure judge (report
verdicts provably equal a single invocation's) and says `resumed: true`
structurally, so a verdict-of-record can still prove single-invocation
coherence; (2) capture artifacts are **self-describing** (full case
echo, error paths included) with per-probe wall-clock excluded from
digests; (3) a **pyyaml 6.0.3 parity tripwire** guards the campaign
env at the right seam; (4) the **multi-rule prange characterization**
banked at the pin: the width-3 parallel kernel is deterministic across
fresh processes and digest-equal to the serial engine on both rule
orders (rule-list order is behavior — identically in both engines;
mechanism deliberately unclaimed), with one new case
(`parallel-computing-multirule`, PASS both engines — **corpus 116**);
(5) .gitignore consolidated to a `results*/` glob. Fast tier **321**.
**The unblocked queue is now empty: every remaining thread is an
operator gate. The session loop stops here.**

## Evidence

- **Author report:**
  [docs/reviews/2026-07-12-harness-quality-author.md](../reviews/2026-07-12-harness-quality-author.md)
  — durability design (completion/resume semantics, the honesty
  block), the prange screens (4 fresh processes per arm, 4 arms), the
  mini-sweep resume demonstration.
- **Independent review (approved-with-fixes):**
  [docs/reviews/2026-07-12-harness-quality-review.md](../reviews/2026-07-12-harness-quality-review.md)
  — the durability model attacked on five fronts (completion lies /
  identity confusion / report equality / honesty / backward compat),
  all sound in the harness code; three fast-tier coverage gaps closed
  (all-complete resumes say resumed, deleted-artifact-under-intact-
  marker re-runs, error artifacts echo); prange re-screened
  independently ALL PASS; digest isolation of the volatile additions
  verified at capture.py:1255.
- **Tests:** `uv run pytest -m "not e2e"` → 321 passed, 6 deselected;
  resume e2e 1 passed (~30 s); `parallel-computing-multirule` ALL
  PASS oracle-vs-rewrite. Oracle pin byte-clean; no installs.

## Committed

- `bc1fab7` — harness: artifacts echo their case; per-probe timing.
- `00c2e61` — harness: per-case durability + resume + report honesty.
- `95b65eb` — tests: pyyaml parity tripwire.
- `0f6e637` — tests: e2e mini-sweep resume exercise.
- `f21b296` — cases: parallel-computing-multirule (corpus 116).
- `d857784` — docs: board note + session-31 author report.
- `9ae5f64` — review: three coverage gaps closed.
- `dda37d4` — hygiene: `results*/` glob replaces 22 per-sweep lines.
- `bc0bb66` — docs: session-31 review report + key-name fix.
- (this commit) — ledger: session 31 banked; campaign log continued.

## NEXT

**Blocked on the operator — nothing unblocked remains.** The gates, in
order of consequence:
1. **The execution-layer commitment** (charter phase 4, operator-
   signed): [docs/perf/execution-layer-options.md](../perf/execution-layer-options.md)
   — recommendation **Option B** (ship the pure-Python core with the
   session-28 optimizations: every ladder rung faster than the oracle
   with disjoint bands — large 14.7× — at ~1/7 the memory, ~65×
   cold-start, zero dependencies, no version ceiling). Options A and C
   stated with numbers in the memo.
2. After the word: **the Phase-4 boundary sweep** — the full 116-case
   corpus in one invocation (now interruption-durable) as the
   verdict-of-record session, then the AC-5 closure audit and the
   execution-layer ADR (AC-5.5 version-headroom statement per the
   chosen option).
3. **Non-blocking:** the oracle-env numba-cache re-baseline
   (session-29 review F2).
A fresh session picks up here with `/campaign` once any gate opens;
the resume point is this file.

## Deviations

- None from the session shape.

## Asks queued

- **Execution-layer commitment** (blocking): the memo, recommendation
  B; the operator's question is stated at the memo's end.
- **Oracle-env cache re-baseline** (non-blocking): session-29 review
  F2 evidence; recommendation to regenerate from a bare capture sweep
  and re-bank count + digests.

## Divergences

- None opened or updated (three records total, all adjudicated).

## Idea seeds

- Post-decision: the boundary sweep should exercise the new resume
  machinery only if an interruption actually occurs — a clean single
  invocation remains the preferred verdict-of-record form.
- The prange mechanism question (numba serializing vs ordered commit)
  stays deliberately unclaimed; only worth pursuing if an Option-C
  numba spike is ever authorized.
