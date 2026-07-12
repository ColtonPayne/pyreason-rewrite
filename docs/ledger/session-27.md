# Session 27 — the pickup drill passes cold; the rewrite's baselines confirm the floor already holds; the hot kernel is named

Date: 2026-07-12

## Verdict

**Three results.** (1) The owed **AC-7 mid-campaign pickup drill PASSED**:
a cold Opus subagent, given only the committed repo, reconstructed the
campaign's state accurately (phases, proof mechanisms, rules, NEXT), ran
the preflight and a rewrite-side bench smoke unaided, and declared the
NEXT executable — no reading-vs-intended gap; its flagged "gaps" were the
session's own planned work plus two minor doc items, both closed this
session. (2) The **rewrite's confirmed baselines** (n=7, same
machine/method as the oracle's): the pure-Python reference core is
**faster than the oracle with disjoint bands on the small (~730×) and
medium (~5.5×) rungs and on cold-start (~65×)**, at **~7× less peak
memory on every rung**, and a **tie on the large rung** (Δ median
+0.815 s, inside the oracle's own 1.346 s spread, bands overlap) — **the
AC-4 execution-layer floor holds for the reference core as it stands.**
(3) The **profile deliverable** names where large-rung time goes:
grounding's clause-satisfaction subtree is 93.8% cumulative (edge arm
65.8%), with `World.is_satisfied` (19.5% self, 40.7M calls),
`Label.__eq__` (14.6%, 41.4M), `Label.__hash__` (13.9%, 43.4M) the top
self-time functions — the named target for any acceleration spike. Fast
tier **288**; review approved-with-fixes (four doc-precision fixes, no
number or verdict affected).

## Evidence

- **Drill:** run by the orchestrator as a cold `model: 'opus'`
  general-purpose subagent, only the committed repo as input; its
  state-statement, commands (preflight 10/10; one small-rung bench
  smoke, 0.004 s reason, matching the committed screen), and gap list
  are quoted in the author report §Drill. Verdict: committed state
  sufficient; no re-drill required.
- **Rewrite baselines of record:**
  [docs/perf/rewrite-baselines.md](../perf/rewrite-baselines.md) —
  small reason 0.0041 s · medium 0.655 s (0.654–0.656) · large
  18.792 s (18.124–18.940) · cold-start 0.068 s (no compile cache —
  stated beside the oracle's separated cache-build context) · RSS
  39.7/45.9/68.8 MiB; side-by-side vs the oracle's banked bands with
  per-rung faster/slower/tie calls under the sub-band-is-a-tie rule.
- **Profile report:**
  [docs/perf/profile-phase4.md](../perf/profile-phase4.md) — cProfile
  (stdlib) via the committed `harness/profile.py` driver on medium +
  large; cProfile overhead (4.0×/4.2×) disclosed, percentages quoted as
  distribution only; oracle side decomposed per-stage from the banked
  bench reports (≈1.38 s import + ≈1.9 s setup + ≈3.0 s in-reason
  per-call floor — the session-26 "~2.7 s" screen refined).
- **Author report:**
  [docs/reviews/2026-07-12-phase4-profiles-author.md](../reviews/2026-07-12-phase4-profiles-author.md).
- **Independent review (approved-with-fixes):**
  [docs/reviews/2026-07-12-phase4-profiles-review.md](../reviews/2026-07-12-phase4-profiles-review.md)
  — every median/band in both baselines docs recomputed from the raw
  n=7 reports (exact match); profile tables re-derived from the pstats
  dumps (exact); medium-rung control repeat 0.623 s (the documented
  lone-run-vs-series offset) and profile re-run with identical call
  counts and ranking; machine identity confirmed live; four
  doc-precision fixes.
- **Tests:** `uv run pytest -m "not e2e"` → 288 passed, 4 deselected
  (author and review runs). No e2e touched this packet (ladder
  equivalence stands verified twice from session 26).

## Committed

- `c774312` — perf: rewrite baselines banked; bench-ladder staging
  helper; oracle-doc reproduce block (drill gaps closed).
- `d211c40` — perf: harness/profile.py cProfile driver + 6 fast-tier
  tests.
- `51f33e7` — docs: profile-phase4.md — where time goes, measured.
- `fc038cd` — docs: session-27 author report.
- `a45374d` — review fixes: four measured-precision doc corrections.
- `be09774` — docs: session-27 review report.
- (this commit) — ledger: session 27 banked; campaign log continued.

## NEXT

**Spike the no-dependency acceleration candidate on the named kernel**
(charter phase 4: spike candidates on the hottest kernel only, screened
cheap before any long confirmation): pure-Python algorithmic work on the
clause-satisfaction subtree — label identity/interning so `Label.__eq__`
/`__hash__` stop dominating (43M hash calls on the large rung), the
`World.is_satisfied` lookup path, and the edge-arm grounding loop —
keeping AC-5's one-core discipline (this is optimization of the single
core, not a second engine; no kernel seam until a second consumer
exists). Evidence per the wall-clock rule: fast tier green + the 3
ladder cases through the harness + a stratified e2e sample of
grounding-heavy case families (the session-24 review's 15-case
stratification is the precedent); the full-corpus sweep remains the
phase-boundary session. Measure on the ladder (screen-then-confirm,
n=7 vs the banked rewrite baselines; the win must clear the noise
band). Then assemble the **execution-layer options memo** for the
operator (the charter's operator-signed commitment): the measured
options — (A) ship the pure-Python core as-is (the floor already
holds; the small/medium/cold-start/memory story is banked), (B) A plus
the algorithmic spike if it wins beyond the band, (C) dependency-bearing
spike candidates (vectorized numpy / numba behind a seam / C-level)
with their dependency asks, only if the operator wants headroom beyond
A/B — with a recommendation. The memo is an ask gate: queue it and stop
the loop there if the operator is still absent.

## Deviations

- None. The drill ran inside the session rather than as its own
  session (session-25 NEXT phrasing) — same substance, one session
  earlier than the letter; recorded, not material.

## Asks queued

- None yet — the execution-layer options memo (next session) is the
  next operator ask by design.

## Divergences

- None opened or updated.

## Idea seeds

- The oracle's per-call floor decomposition (import/setup/in-reason)
  as consumer-facing latency material once the execution layer is
  signed.
- If the algorithmic spike lands, a follow-on profile to re-rank the
  next kernel (grounding edge arm vs interval updates).
- Carried: registrand-behavior packet (L3/L4 arms); edge-rule
  head-function forms; sweep durability; `probe_s` timing; multi-rule
  prange characterization; pyyaml-version parity tripwire;
  artifact-schema `inputs` echo; `raise_errors=False` warn-skip arms.
