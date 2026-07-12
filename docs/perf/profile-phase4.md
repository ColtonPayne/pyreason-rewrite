<!-- doccode: pyreason-rewrite-docs-perf-profile-phase4 -->
# Phase-4 profile report — where the time actually goes (2026-07-12)

Measured decomposition of both engines over the committed ladder
([ladder.md](ladder.md)): per-function cProfile on the pure-Python
reference core (medium + large rungs), per-stage wall-clock on the pinned
oracle (its hot loop is numba-jitted — cProfile sees one opaque dispatcher
call, so per-function attribution there is meaningless by construction).
This report names the hottest kernels; it is the input to
acceleration-spike candidates, each of which is its own later session.

## Method

- **Reference core:** `harness/profile.py` (committed, stdlib
  cProfile/pstats), run under the engine interpreter
  (`scripts/rewrite-python`), one in-process run per rung, profiler
  active around the `reason()` call only. Artifacts (pstats dumps +
  top-N tables) in gitignored
  `results-phase4-profile/rewrite-2026-07-12/`.
- **cProfile overhead, measured:** profiled reason() wall-clock vs the
  unprofiled banked median ([rewrite-baselines.md](rewrite-baselines.md)):
  medium **2.588 s vs 0.655 s (4.0×)**, large **79.310 s vs 18.792 s
  (4.2×)**. cProfile taxes per-call-dense code, so this report cites the
  *distribution* (percentages of total profiled time, call counts) — all
  wall-clock claims come from the bench baselines, never from profiled
  runs.
- **Oracle:** per-stage wall-clock reused from the banked n=7 bench
  report (`results-phase4-baselines/oracle-baselines-2026-07-12/`, the
  [oracle-baselines.md](oracle-baselines.md) numbers of record) —
  reuse-or-extract, not re-measured.
- Percentages below use cProfile's own total (sum of per-function self
  time = 100% = the profiled reason() time); cumulative percentages
  overlap since callers subsume callees.

## Reference core — the large rung (profiled reason = 79.31 s, 100%)

Top of the call graph (cumulative): the whole run is the temporal loop
(`_interpretation.reason` 100%), and grounding dominates it —
`_ground_rule` **95.2%**, its clause-satisfaction walk
`check_all_clause_satisfaction` **93.8%**, with the edge-clause arm
(`get_qualified_edge_groundings` → `is_satisfied_edge`) at **65.8%**
and the node-clause arm (`get_qualified_node_groundings` →
`is_satisfied_node`) at **28.4%**.

Hottest functions by self time (top 10 ≈ 88% of everything):

| function | self % | self s | cum % | calls |
|---|---|---|---|---|
| `_world.py:26 World.is_satisfied` | **19.5** | 15.44 | 75.1 | 40,694,677 |
| `label.py:21 Label.__eq__` | **14.6** | 11.61 | 20.1 | 41,439,141 |
| `label.py:28 Label.__hash__` | **13.9** | 11.00 | 20.0 | 43,382,765 |
| `interval.py:104 Interval.__contains__` | **12.0** | 9.55 | 17.2 | 40,454,287 |
| `_grounding.py:55 is_satisfied_edge` | 8.7 | 6.91 | 61.0 | 28,368,878 |
| `_grounding.py:79 get_qualified_edge_groundings` | 4.9 | 3.85 | 65.8 | 73,183 |
| `_grounding.py:37 is_satisfied_node` | 3.3 | 2.62 | 26.2 | 12,325,799 |
| `<built-in> hash` | 3.2 | 2.57 | 3.2 | 43,382,765 |
| `label.py:25 Label.__str__` | 2.8 | 2.25 | 2.8 | 43,382,765 |
| `<built-in> isinstance` | 2.8 | 2.23 | 2.8 | 41,439,141 |

Next tier, same pattern: `Label.get_value` 2.6% (41.4M calls),
`Interval.lower` 2.6% (41.0M), `Interval.upper` 2.6% (40.9M). Summing the
grounding chain's frames and the value-type primitives they call accounts
for **≈ 96% of all self time**; everything else — fact application
(`_apply_fact` 1.7% cum), interval updates (`_update_component` 1.3%
cum), consistency checks, bookkeeping — is measurably cold.

The call counts tie exactly to the source, so the attribution is not a
sampling artifact: `Label.__hash__` is `hash(str(self))`, and its
43,382,765 calls match `Label.__str__`'s count 1:1; `Label.__eq__` calls
`get_value()` and `isinstance` once each, and all three counters read
41,439,141; `Interval.__contains__` reads the `lower`/`upper` properties
of its argument, matching their ~41M counts. One clause-satisfaction
check costs one dict lookup keyed by a `Label` (a `__hash__` + `__eq__`)
plus one `Interval.__contains__` — ~40M such checks per large-rung run.

## Reference core — the medium rung (profiled reason = 2.588 s, 100%)

Same shape, smaller exponents — the profile is scale-stable across the
ladder: `_ground_rule` 75.6% cum, `check_all_clause_satisfaction` 72.6%,
edge arm 51.0%; by self time `World.is_satisfied` **15.2%** (1.06M
calls), `Label.__hash__` **14.5%** (1.52M), `Label.__eq__` **13.3%**
(1.26M), `Interval.__contains__` **9.4%** (1.04M). The non-grounding
remainder is proportionally larger only because the join rule is absent
(fact application `_apply_fact` reaches 12.1% cum here vs 1.7% on
large); no new hot function appears at either scale.

## Oracle — per-stage wall-clock decomposition (n = 7 medians, banked)

Bench data times three stages per fresh process; that is as far as the
oracle's decomposition can honestly go (the in-reason interior is jitted,
per-function attribution impossible by construction).

| stage | small | medium | large | behavior across 40× edge-count |
|---|---|---|---|---|
| import | 1.380 | 1.383 | 1.389 | fixed (loads numba + cached kernel indexes) |
| setup | 1.864 | 1.957 | 2.000 | near-fixed (+0.14 s across the ladder) |
| reason() | 2.992 | 3.611 | 17.977 | floor ≈ 3 s + workload |

**The fixed per-call overhead, broken down as far as bench data allows:**

- **Pre-reason, per fresh process: ≈ 3.3 s** (import ≈ 1.38 s + setup
  ≈ 1.9 s, both nearly scale-invariant).
- **In-reason floor: ≈ 3.0 s per `reason()` call.** The oracle's reason()
  never measured below 2.922 s on any rung — including the small rung,
  whose entire reasoning workload the rewrite completes in 0.0041 s — so
  ≈ 3.0 s of every oracle reason() call is per-call floor, not rung
  workload. Bench data locates this floor *inside* reason() (import and
  setup are separately timed) but cannot attribute it per-function. This
  refines session 26's screened "~2.7 s fixed per-call overhead" to a
  confirmed ≈ 3.0 s (band 2.922–3.053, n=7).
- Fresh-process fixed cost ≈ 6.3 s total (both components) before any
  scale work — the whole of the rewrite's small/medium/cold-start wins
  in the [baselines side-by-side](rewrite-baselines.md) sits in this
  fixed cost.
- **Incremental scale cost, median-to-median:** small→medium the two
  engines pay nearly the same (+0.619 s oracle vs +0.651 s rewrite — the
  chain-rule workload costs both engines alike at this scale);
  medium→large the jitted loop scales better (+14.366 s oracle vs
  +18.137 s rewrite on the join workload). That differential is what the
  large-rung tie is made of.

## What this means for acceleration candidates (measured statements only)

1. **The target is the clause-satisfaction inner loop of grounding, and
   nothing else is close.** `check_all_clause_satisfaction` and its
   callees hold 93.8% of large-rung profiled reason time (72.6% medium);
   the edge-clause arm alone holds 65.8% (51.0% medium). Every other
   subsystem (fact application, interval updates, consistency, output)
   is ≤ 2% cum on large. An acceleration spike aimed anywhere but
   grounding cannot move the large rung materially.
2. **Within the loop, the cost is per-candidate value-type overhead at
   ~40M checks per large run:** one `Label`-keyed dict lookup
   (`__hash__` — which round-trips through `str()` every call — plus
   `__eq__`, which pays `get_value` + `isinstance` every call) and one
   `Interval.__contains__` (two property reads) per candidate check.
   These primitives plus `World.is_satisfied` itself carry ≈ 76% of
   large-rung self time. Candidate directions the measurements support:
   fewer candidate checks (the superlinear join-grounding term —
   `get_qualified_edge_groundings` is called 73k times but induces 28.4M
   `is_satisfied_edge` calls), or cheaper checks (the per-call `str()` /
   `isinstance` / property overhead is internal mechanism, invisible to
   the pinned observable surface — equality-and-hash-*by-string-value*
   is the pinned behavior (label-ops), not *how* the hash is computed).
3. **The profile is scale-stable** (same hot set, same ordering, medium
   and large), so a single spike target covers the ladder; medium is the
   cheap iteration rung (0.655 s unprofiled) for spike development, with
   large as the confirmation rung.
4. Each spike is a later session with its own equivalence evidence
   through the harness; this report names targets, it promises no
   speedup numbers.

## Reproduction

```
# reference-core profiles (this report's tables):
PYTHONHASHSEED=0 scripts/rewrite-python -m harness.profile \
  --case harness/cases/perf-ladder-medium.json \
  --out-dir results-phase4-profile/rewrite-2026-07-12 --top 25
PYTHONHASHSEED=0 scripts/rewrite-python -m harness.profile \
  --case harness/cases/perf-ladder-large.json \
  --out-dir results-phase4-profile/rewrite-2026-07-12 --top 25
# oracle stage decomposition (reused, not re-measured):
#   results-phase4-baselines/oracle-baselines-2026-07-12/bench-report.json
#   or regenerate: scripts/bench-ladder oracle-env/bin/python <tag> 7
```
