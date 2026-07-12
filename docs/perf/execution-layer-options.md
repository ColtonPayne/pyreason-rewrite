<!-- doccode: pyreason-rewrite-docs-perf-execution-layer-options -->
# Execution-layer options — the operator's decision memo (2026-07-12, session 28)

The charter commits the execution-layer choice to the operator. This memo
presents the options with their measured numbers and one recommendation.
**It is a queued ask: nothing in Option C is authorized or started by this
session.** All numbers are n = 7 medians with (min…max) bands from the
committed baseline reports ([rewrite-baselines.md](rewrite-baselines.md),
[oracle-baselines.md](oracle-baselines.md)); ties follow the banked
tie rule (a delta inside the noise band is a tie).

## Where the engine stands after the session-28 spike

Four zero-dependency optimizations (all equivalence-verified: fast tier
288 passed; ladder-3 and a 16-case stratified grounding-heavy sample
oracle-vs-rewrite ALL PASS) moved the pure-Python core:

| rung, reason() | rewrite post-spike | rewrite pre-spike (session 27) | oracle |
|---|---|---|---|
| small | **0.0028 s** (0.0028…0.0028) | 0.0041 s | 2.992 s (2.922…3.053) |
| medium | **0.151 s** (0.151…0.153) | 0.655 s | 3.611 s (3.529…3.625) |
| large | **1.226 s** (1.224…1.240) | 18.792 s (18.124…18.940) | 17.977 s (17.178…18.524) |

The session-27 large-rung tie is now a **14.7× win over the oracle with
disjoint bands**; every rung, cold-start (0.067 s vs 4.376 s), and peak
RSS (67 MiB vs 329 MiB on large) favor the rewrite.

## Option A — ship the pure-Python core as of session 27

The pre-spike floor already satisfied AC-4 (faster on small/medium/
cold-start with disjoint bands, ~7× less memory, tie on large). Shipping
A means discarding this session's four commits. There is no reason to
prefer A over B: the spike changed no observable behavior (the
equivalence evidence above), added no dependency, and added ~40 lines.
Listed only for completeness.

## Option B — A plus the session-28 algorithmic win (recommended)

Ship the pure-Python core with commits `c56d238`, `c218f45`, `958523a`,
`ca600a3`. The win cleared every band: large-rung 15.3× vs the pre-spike
rewrite band and 14.7× vs the oracle band, medium 4.3×, small 1.46× —
all with disjoint bands (the memo's table above; full bands in
[rewrite-baselines.md](rewrite-baselines.md)). Zero new dependencies,
one reasoning core, no kernel seam, no compile step, no version
ceiling. Cost: none identified — the candidates are engine-internal
mechanism and one algebraic identity (the per-head clause re-check is
constant across a node rule's head loop), each carried by the harness
evidence in the author report.

## Option C — authorize a dependency-bearing acceleration spike

Each sub-option needs an explicit dependency ask (hard rule: no installs
without operator permission) and its own spike session with harness
evidence. **Amdahl honesty, from the post-spike large-rung profile**
(banked in `results-phase4-profile/rewrite-postspike-2026-07-12/`): the
profile is now flat. The top self-time holders are the temporal loop
body itself (23.6%), the pinned per-update bookkeeping
(`_update_component` 9.6% self / 23.8% cum, `_apply_fact` 8.0% self /
15.9% cum), and the whole grounding subtree is down to 25.4% cumulative
(was 95.2% pre-spike). No single kernel holds more than ~26%. A perfect
elimination of the grounding subtree would buy at most **1.34×**; only
compiling essentially the whole reasoning loop buys more.

- **C1 — numpy vectorization of the grounding scans.** Ask: add `numpy`.
  Ceiling: the 25.4% grounding subtree → ≤ 1.34× large-rung, and the
  scans operate over per-candidate dict/object lookups that must be
  restructured into arrays first — the restructuring, not the
  arithmetic, is the work. AC-5 cost: an array mirror of the world state
  risks exactly the two-representation drift the one-core rule exists to
  prevent.
- **C2 — numba re-added behind a kernel seam.** Ask: add `numba` (and
  accept its interpreter-version ceiling — charter AC-5.5: the oracle's
  own numba pin is why the campaign exists on Python 3.13 with a
  separate oracle env). Ceiling: could reach the whole loop (~99%), but
  re-inherits the compile floor the oracle pays (≈ 3.0 s per reason()
  call, ≈ 1.4 s import — the fixed costs the rewrite's small-rung and
  cold-start wins are made of) plus a second implementation surface
  behind the seam.
- **C3 — C-level compilation (C extension / Cython / mypyc) of the hot
  modules.** Ask: add a build toolchain + the chosen compiler dep.
  Ceiling: same flat-profile bound — meaningful gains require compiling
  the temporal loop and update paths wholesale; adds a build step and a
  platform matrix to a currently pure-Python, zero-build package.

All three spend their budget against a large rung that now runs in
1.226 s — 14.7× ahead of the oracle — so the marginal user-visible win
is bounded and the AC-5 costs are structural.

## Recommendation and the ask

**Recommendation: Option B.** The algorithmic spike already banked a
band-clearing win on every rung with zero dependencies and one core;
the post-spike profile is flat, so every Option-C candidate buys a
bounded improvement at the cost of a dependency, a version ceiling, or
a second implementation surface.

**The question the operator must answer:** *Ship Option B (the
pure-Python core with the session-28 optimizations) as the campaign's
execution layer — or authorize one Option-C spike, and if so, which
sub-option and its dependency ask?* Until answered, no dependency is
added and no C-track work starts.
