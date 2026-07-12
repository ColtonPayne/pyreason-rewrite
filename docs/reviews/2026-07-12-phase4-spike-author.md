<!-- doccode: pyreason-rewrite-docs-reviews-phase4-spike-author -->
# Session-28 author report — the zero-dependency algorithmic spike on the grounding kernel

- Session: 28 (author pass, 2026-07-12)
- Packet: NO-DEPENDENCY algorithmic spike on the clause-satisfaction
  kernel the Phase-4 profile named
  ([profile-phase4.md](../perf/profile-phase4.md)), then the
  execution-layer options memo
  ([execution-layer-options.md](../perf/execution-layer-options.md))
- Commits: `c56d238` (K3), `c218f45` (K1), `958523a` (K2), `ca600a3`
  (K4), plus this report + the baselines section + the memo
- Constraint honored: pure Python, stdlib only, zero new dependencies,
  one reasoning core, no kernel seam; every pinned observable
  (label-ops relations, B27's `AttributeError` eq raise, the
  closed-world absent-label arm, trace ordering) unchanged — evidence
  below.

## Candidates — tried, screened, kept/reverted

Discipline: one candidate at a time; fast tier + a single large-rung
screen after each (`harness.bench`, fresh process, `PYTHONHASHSEED=0`);
ladder-3 differential run before each commit. Baseline screen on the
session-27 code: **18.129 s** (inside the banked band 18.124…18.940).

| id | candidate | screen (large reason()) | verdict |
|---|---|---|---|
| K3 | Memoize the node-arm per-head clause re-check: `check_all_clause_satisfaction` is recomputed per head grounding at the pin, but nothing in that loop mutates the groundings or worlds it reads (the lone `_add_node` arm forces a single-element head list), so one value serves the whole loop. Lazy — computed on the first iteration — so a zero-head loop still never calls it. The edge-rule arm is untouched (its per-pair temp groundings genuinely differ). | 18.129 → **1.617 s** (11.2×) | **kept** (`c56d238`) |
| K1 | Cache `Label.__hash__` after first computation (the pin round-trips `hash(str(self))` every call — 43.4M calls per pre-spike large run). Lazy on purpose: a non-string value still raises its `TypeError` at first `hash()`, never at construction; hash-by-string-value and the B27 eq raise untouched. | 1.617 → **1.490 s** (−7.9%) | **kept** (`c218f45`) |
| K2 | Hoist per-candidate constant work out of `get_qualified_node/edge_groundings` (None guards, closed-world membership, World/Interval method dispatch; the open-world scan reads the same bound-inclusion comparison `Interval.__contains__` performs, with the same KeyError/AttributeError never-satisfied arm; the closed-world arm keeps the original path). Plus: `_ground_rule` builds `nodes_set`/`edges_set` only when a consumer arm can reach them; `_apply_fact`'s static check does one `.get()` instead of membership-test-plus-lookup. | 1.490 → **1.273 s** (−14.6%) | **kept** (`958523a`) |
| K4 | One canonical `Label` per distinct attribute string in `parse_graph_attributes` (the pin builds two objects per occurrence — the specific-labels key and the graph fact's label), so downstream world/predicate-map lookups short-circuit on identity. Values, equality, and hash are unchanged. Borderline single-run screen (−4%), so it got a deeper screen: 3-run bands **1.214–1.225 s with vs 1.269–1.284 s without — disjoint**. | 1.273 → **1.221 s** (−4.3%) | **kept** (`ca600a3`) |

**Reverted candidates: none.** Zero candidates died on screen this
session; the spike loop stopped after K4 because the re-profile came
back flat (below) — the remaining self-time leaders are the pinned
temporal loop body and pinned per-update bookkeeping, with no kernel
holding more than ~26% cumulative. Directions considered and *not*
implemented, recorded for the memo: global label interning (residual
`Label.__hash__` is 4.7% self — bounded win, public-surface identity
questions) and string-keying the world dicts (touches ~80 call sites
across `_interpretation.py` for a bounded fraction — poor
risk-per-second at this profile).

## Confirmed numbers (n = 7 per rung, `scripts/bench-ladder`, tag `rewrite-postspike-2026-07-12`)

| rung | reason() median (band) [spread] | pre-spike (band) | oracle (band) | verdict |
|---|---|---|---|---|
| small | **0.0028** (0.0028…0.0028) [0.0000] | 0.0041 (0.0041…0.0041) | 2.992 (2.922…3.053) | 1.46× vs pre-spike, bands disjoint |
| medium | **0.151** (0.151…0.153) [0.002] | 0.655 (0.654…0.656) | 3.611 (3.529…3.625) | 4.3× vs pre-spike, bands disjoint |
| large | **1.226** (1.224…1.240) [0.017] | 18.792 (18.124…18.940) | 17.977 (17.178…18.524) | **15.3× vs pre-spike, 14.7× vs oracle — all bands disjoint; the session-27 large-rung tie is now a win** |

Cold-start (small, import + first reason): 0.067 (0.066…0.067) vs
pre-spike 0.068 (0.067…0.069) — tie (import dominates the metric).
Peak RSS: large 67.1 MiB (66.6…68.7) vs 68.8 (68.2…69.0) — bands
overlap, tie; small/medium unchanged. Full table banked as the dated
post-spike section in [rewrite-baselines.md](../perf/rewrite-baselines.md);
raw runs in gitignored
`results-phase4-baselines/rewrite-postspike-2026-07-12/`.

## Re-profile (large rung, `harness.profile`, banked in `results-phase4-profile/rewrite-postspike-2026-07-12/`)

Profiled reason(): **3.168 s** (was 79.31 s pre-spike, same 2.6–4.2×
cProfile overhead caveat — distributions only, never wall-clock). What
moved: the grounding subtree fell from **95.2% to 25.4% cumulative**
(`_ground_rule`); `World.is_satisfied` (19.5% self / 40.7M calls) and
`Interval.__contains__` (12.0% / 40.5M) left the table entirely
(bypassed by K2's hoisted scans on the hot path); `Label.__eq__` fell
from 14.6% self / 41.4M calls to 2.4% / 0.29M; `Label.__hash__` from
13.9% + a 1:1 `str()` round-trip / 43.4M calls to 4.7% cached / 2.76M.

New top-3 by self time: `_interpretation.reason` (the temporal loop
body) **23.6%**, `_update_component` **9.6%** (23.8% cum),
`_apply_fact` **8.0%** (15.9% cum). The profile is flat — the input the
options memo's Amdahl ceilings are computed from. Medium rung mirrors
it (loop body 27.7%, `_apply_fact` 28.3% cum): scale-stable, same as
the pre-spike report's observation.

## Equivalence evidence (all on the final kept set)

- **Fast tier:** `uv run pytest -m "not e2e"` — **288 passed** (run
  after every candidate and at the final state).
- **Ladder 3:** `harness.run` oracle-vs-rewrite on
  perf-ladder-{small,medium,large} — **ALL PASS (3)**, run after every
  kept candidate (K3, K1, K2, K4 states each verified before commit).
- **Stratified grounding-heavy sample — 16 cases, ALL PASS**, chosen to
  cover exactly the seams the candidates touched (the session-24
  15-case stratification is the precedent): `hello-world` (the join
  shape K3 memoizes), `threshold-number-gate-clause-level` /
  `threshold-number-gate-two` / `threshold-percent-total` /
  `threshold-dict-gate` (clause-level gating over the qualified counts
  K2's scans produce), `closed-world-on` / `closed-world-off` (the arm
  K2 deliberately left on the original per-candidate path),
  `allow-ground-rules-on` / `allow-ground-rules-off` (K2's lazy
  `nodes_set`/`edges_set`), `edge-rule-frames` (the edge-rule head loop
  K3 did NOT memoize — regression guard), `head-fn-grounding` /
  `head-fn-ungrounded-var` (head-function groundings and the
  `_add_node` single-iteration arm inside K3's loop),
  `static-graph-facts-on` / `save-graph-attrs-to-trace-on` (K2's
  `.get()` static check + K4's canonical loader labels riding into the
  trace), `inconsistency-ipl-resolve` (label equality on the
  `_apply_fact` IPL/inconsistency path), `annotation-fn-six-arg`
  (world reads inside the memoized head loop).
- Seam tests pinning the deliberately-kept behaviors (label-ops
  relations, B27's eq raise, interval containment/repr) are in the fast
  tier and unchanged — no test was modified this session.

## Memo summary (the queued ask — no action taken)

[execution-layer-options.md](../perf/execution-layer-options.md):
Option A (ship session-27 core) listed for completeness; **Option B
(A + this session's win) recommended** — the win cleared every band
with zero dependencies and one core; Option C (numpy / numba-behind-a-
seam / C compilation) laid out with per-sub-option dependency asks and
Amdahl ceilings from the flat post-spike profile (grounding subtree
25.4% cum → ≤ 1.34× large-rung for C1; C2 reaches the whole loop but
re-inherits the oracle's compile floor and a version ceiling per
charter AC-5.5). Ends with the exact operator question: ship Option B,
or authorize one Option-C spike and its dependency.

## Reproduction

```
# fast tier (288):
uv run pytest -m "not e2e"
# confirmation series (n=7, all rungs):
scripts/bench-ladder scripts/rewrite-python rewrite-postspike-2026-07-12 7
# re-profile:
PYTHONHASHSEED=0 scripts/rewrite-python -m harness.profile \
  --case harness/cases/perf-ladder-large.json \
  --out-dir results-phase4-profile/rewrite-postspike-2026-07-12 --top 25
# equivalence — ladder 3 and the 16-case sample (stage into a dir, then):
PYTHONHASHSEED=0 uv run python -m harness.run --cases <staged-dir> \
  --engine-a oracle-env/bin/python --engine-b scripts/rewrite-python \
  --results <results-dir>
```
