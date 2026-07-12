# Session 28 — the zero-dependency spike: the large-rung tie becomes a 14.7× win; the execution-layer decision is queued

Date: 2026-07-12

## Verdict

**Four pure-Python optimizations inside the single reasoning core turn
session 27's large-rung tie into a band-disjoint win on every rung** —
large-rung `reason()` 1.226 s (1.224–1.240) vs the oracle's 17.977 s
(17.178–18.524): **14.7× faster, with equivalence intact** (fast tier
289; ladder 3/3 and a 20-case grounding-adversarial stratified sample
ALL PASS oracle-vs-rewrite). The adversarial review re-derived each
optimization's safety against the pinned source (no K reverted; one new
seam test pinning the lazy-hash TypeError shape; one rounding fix). The
**execution-layer options memo is written and queued as the operator
ask** — the charter's operator-signed commitment; recommendation:
Option B, ship the pure-Python core with this session's win.

## Evidence

- **The four optimizations (kept 4 / reverted 0; screens 18.13 →
  1.62 → 1.49 → 1.27 → 1.22 s):** K3 memoized node-arm per-head clause
  re-check (memo local to `_ground_rule`, invalidation by
  construction); K1 lazy-cached `Label.__hash__` (pinned
  TypeError-at-every-hash byte-identical to the pin, seam-tested); K2
  hoisted constant work out of qualified-grounding scans + conditional
  `nodes_set`/`edges_set` (all five consumers enumerated; infer-edges
  snapshot timing identical to the pin); K4 canonical Label per
  attribute string in the graph loader (Label immutable; the pin
  itself shares one object per string at the same seam).
- **Confirmed numbers (n=7, bands):** large 1.226 s (15.3× vs
  pre-spike rewrite, 14.7× vs oracle, bands disjoint) · medium 0.151 s
  (4.3×) · small 0.0028 s (1.47×) · cold-start/RSS unchanged. New
  large-rung profile is flat (grounding subtree 95.2% → 25.4% cum;
  top self-time now the temporal loop body at 23.6%) — remaining
  no-dep headroom ≈1.34× by Amdahl, banked in the memo.
- **Equivalence:** ladder 3/3; 20-case stratified sample ALL PASS —
  the author's 16 plus four reviewer-chosen adversarial swaps
  (`rule-from-csv-basic` = the corpus's only infer-edges mid-run edge
  addition; `persistent-off` fires-then-expires; `fp-version-on`
  re-grounding through the memoized loop;
  `save-rule-trace-clause-reorder` trace order). Trace/list order is
  part of the compared value (harness/compare.py).
- **Author report:**
  [docs/reviews/2026-07-12-phase4-spike-author.md](../reviews/2026-07-12-phase4-spike-author.md).
- **Independent review (approved-with-fixes):**
  [docs/reviews/2026-07-12-phase4-spike-review.md](../reviews/2026-07-12-phase4-spike-review.md)
  — per-K semantic re-derivation against the pinned source
  (interpretation.py:955–1063 for K3), perf spot-checks on the band
  edges, every memo number re-derived from the raw reports.
- **Post-spike baselines:** new dated section in
  [docs/perf/rewrite-baselines.md](../perf/rewrite-baselines.md)
  (session-27 numbers preserved as the pre-spike record).
- **Tests:** `uv run pytest -m "not e2e"` → 289 passed, 4 deselected.

## Committed

- `c56d238` — perf K3: memoize the node-arm per-head clause re-check.
- `c218f45` — perf K1: lazy-cache Label's hash, pinned relations kept.
- `958523a` — perf K2: hoist constant work out of grounding scans.
- `ca600a3` — perf K4: canonical loader labels.
- `b89d318` — docs: post-spike baselines, options memo, author report.
- `4081851` — review: seam test for K1's TypeError shape; ratio fix.
- `44816c5` — docs: session-28 review report.
- (this commit) — ledger: session 28 banked; campaign log continued.

## NEXT

**Blocked on the operator: the execution-layer commitment.** The memo
is [docs/perf/execution-layer-options.md](../perf/execution-layer-options.md)
— Option A (ship the session-27 pure core), **Option B (recommended:
ship the pure core with this session's four optimizations — every rung
faster than the oracle with disjoint bands, no new dependencies, no
version ceiling)**, Option C (authorize dependency-bearing spikes:
numpy / numba-behind-a-seam / C-level, each with its dependency ask;
remaining no-dep headroom is only ≈1.34× so C is for headroom beyond
14.7×). The commitment is operator-signed per charter; nothing
proceeds on it until the word comes.

**Unblocked meanwhile (queue-and-continue):** the carried breadth
seeds that widen input classes independent of the execution layer —
the registrand-behavior packet (L3/L4 arms) and the edge-rule
head-function forms (note: an fp+infer_edges case will surface the
B17 divergence, whose direction the operator already adjudicated in
session 25 — DIV-0002 shape: same seam, same type, honest stable
message — so filing that DIV record and implementing the direction is
pre-authorized work). A cron-launched session picks this up while the
ask waits.

## Deviations

- The reviewer agent stalled once mid-review (backgrounded its own
  gating run, then idled); resumed by the orchestrator and completed
  synchronously. Process note, not a finding about the work.

## Asks queued

- **The execution-layer commitment (blocking for Phase-4 closure):**
  [docs/perf/execution-layer-options.md](../perf/execution-layer-options.md)
  — options + measured numbers + recommendation (B). The operator's
  question is stated at the memo's end.

## Divergences

- None opened or updated this session (the 20-case adversarial sample
  surfaced none).

## Idea seeds

- Post-decision: a follow-on profile if Option C is taken (the flat
  profile means the next win needs a different lever, not a hotter
  kernel).
- Carried: registrand-behavior packet (L3/L4 arms); edge-rule
  head-function forms (→ B17 case + pre-authorized DIV); sweep
  durability; `probe_s` timing; multi-rule prange characterization;
  pyyaml-version parity tripwire; artifact-schema `inputs` echo;
  `raise_errors=False` warn-skip arms.
