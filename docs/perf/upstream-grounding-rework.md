<!-- doccode: pyreason-rewrite-docs-perf-upstream-grounding-rework -->
# Upstream grounding rework — which commit traded the O(E) neighborhood grounder for the global FOL grounder

**Status: source-level attribution, 2026-07-12.** This report extends the
[Pokec scaling report](pokec-scaling-report.md), which measured a ~202× runtime
step between pyreason 1.2.4 (2023-03-06) and the pinned 2026 engine on the
paper's own workload (10k rung: 13.4 s vs ~2,600 s; scaling x^0.98 vs x^1.87
in edges) and identified the mechanism at *version* granularity:
neighborhood-scoped clause matching vs global candidate-set grounding. The
operator asked which upstream commit made the trade. This report answers at
*commit* granularity, by reading the history inside the read-only oracle clone
(`oracle/pyreason`, pinned at `e1a94af33e1f`). Everything here is source-reading
evidence plus upstream's own PR text; the empirical two-release confirmation on
the paper workload is **queued** (see [Queued confirmation](#queued-confirmation)).

## Verdict

**The pivot is `b01a80394334feb62a1ca63ec9b06934d1390056`** — *"new grounding
methods, fixed annotations and speedups to be tested"*, Dyuman Aditya,
**2024-06-15**, authored on upstream's `v3.0.0` development branch. It switches
the reasoning loop's call site from the target-anchored grounders to the new
general first-order grounder `_ground_rule`, whose fresh-variable candidate
sets are the whole graph's node and edge lists. The change reaches `main` in
the merge `5a1aab7` (**PR #43**, "New release v3.0.0", 2024-12-01) and first
ships in tag **v3.0.0 (2024-12-01)**. The **last release without it is v2.3.0
(2024-05-16)**; there are no tags between v2.3.0 and v3.0.0. The pivot heads a
series (bounded below), but the asymptotic trade happens in this one commit —
the follow-ups propagate it and tune constants.

## The grounding lineage, three eras

| Era | Grounding shape | Where |
|---|---|---|
| 1.2.4 (paper era, 2023-03-06) | Per candidate node `n`, clause matching receives only `neighbors[n]` — per rule-timestep work O(Σ degree) = O(E) | `interpretation.py:373-376` at tag `1.2.4`: `for n in nodes:` → `a = neighbors[n]` → `_is_rule_applicable(...)` (def at `:432`) |
| daeefde3 (2023-05-26) → v2.3.0 | Refactored into `_ground_node_rule` / `_ground_edge_rule`: multi-clause variable chaining gained, but grounding stays **target-anchored** — fresh node clauses ground over `neighbors[target_node]`, edge clauses over `neighbors`/`reverse_neighbors` of the target | `interpretation.py:691` at `daeefde`: `subset = neighbors[target_node] if clause_var_1 not in subsets else subsets[clause_var_1]`; same shape at `v2.3.0` (`:1205`, call site `:576`) |
| b01a803 (2024-06-15) → v3.0.0 → the pin | General FOL grounder `_ground_rule`: no target parameter at all; one global grounding pass per rule; fresh node variables ← **all nodes**, fresh edge variable pairs ← **all edges**; head variables are read out of the body groundings afterwards | evidence hunks below |

The intermediate rework (`daeefde35a00494ca693f14febef4321428f0cee`, *"changed
grounding process"*, 2023-05-26, first tag v1.7.0, merged to `main` via PR #14
"grounding-improvement" on 2023-09-28) is where the Pokec report's literal
`a = neighbors[n]` / `_is_rule_applicable` text disappears — but it **preserves
the asymptotics** for target-anchored rules (the paper's diffusion shape): only
the case where *both* edge-clause variables are fresh falls back to all nodes,
which the paper's two rules never hit. It is not the regression.

## The pivot commit, evidence

`git -C oracle/pyreason show b01a803` — +515 lines to
`pyreason/scripts/interpretation/interpretation.py`. The load-bearing hunks:

**1. The call-site switch** (reason loop; old calls left commented, new one in):

```
-  applicable_node_rules = _ground_node_rule(rule, ..., neighbors, reverse_neighbors, ..., nodes_to_skip[i])
-  applicable_edge_rules = _ground_edge_rule(rule, ..., neighbors, reverse_neighbors, ..., edges_to_skip[i])
+  applicable_node_rules, applicable_edge_rules = _ground_rule(rule, interpretations_node,
+      interpretations_edge, nodes, edges, neighbors, reverse_neighbors, atom_trace)
```

(at `b01a803`: `interpretation.py:584`, commented predecessors `:582-583`;
new `_ground_rule` def `:757`.)

**2. Fresh node variables ground over the whole node list**
(`interpretation.py:1857-1859` at `b01a803`):

```python
def get_rule_node_clause_grounding(clause_var_1, groundings, nodes):
    # The groundings for a node clause can be either a previous grounding or all possible nodes
    grounding = numba.typed.List(nodes) if clause_var_1 not in groundings else groundings[clause_var_1]
```

**3. Fresh edge-variable pairs ground over every edge in the graph**
(`interpretation.py:1864` at `b01a803`, Case 1):

```python
if clause_var_1 not in groundings and clause_var_2 not in groundings:
    for n in nodes:
        es = numba.typed.List([(n, nn) for nn in neighbors[n]])
        edge_groundings.extend(es)
```

Contrast the removed anchor: in every prior era the first clause of a
target-anchored rule sees `deg(target)` candidates; from `b01a803` it sees
`|V|` (node clause) or `|E|` (edge clause) candidates, and every downstream
intersection, threshold check, and `refine_groundings` pass operates on those
graph-sized lists once per rule per fixpoint operation. The old
`_ground_node_rule` / `_ground_edge_rule` remain in the file as dead code
(marked `NOTE: DEPRECATED`) until `1f65f6b` deletes them.

**What was gained** — generality: rules whose clauses need not touch the head
variable at all, arbitrary variable patterns, `infer_edges`, ground atoms in
rule bodies. The head stops being the grounding anchor, which is exactly what
makes the engine a general FOL grounder and exactly what removes the per-target
O(degree) bound.

## The series, bounded

All on upstream's `v3.0.0` branch, between the pivot and the merge to `main`:

| Commit | Date | What it does |
|---|---|---|
| `b01a803` | 2024-06-15 | **The pivot** — `_ground_rule` introduced, call site switched in `interpretation.py` |
| `d218a33` | 2024-06-25 | `interpretation_parallel.py` switched to `_ground_rule` ("fixed parallel implementation, now works") |
| `e041a3d` | 2024-08-24 | Clause reordering |
| `0f7d315` | 2024-09-03 | Sets to speed up `in` searches over the (now global) grounding lists |
| `1f65f6b` | 2024-12-01 | Deletes the deprecated neighborhood grounders (−996 lines across both engine files) |
| `5a1aab7` | 2024-12-01 | **Merge PR #43** (`v3.0.0` → `main`) |

Tag **v3.0.0** is cut the same day. On the engine triplication: the modern
tree's three engine files did not exist together when the trade was made —
`interpretation_parallel.py` was created 2023-08-29 (`ed62cd4`) with the
neighborhood grounder and converted by `d218a33`; `interpretation_fp.py` was
created 2025-08-25 (`b35231b`), after the rework, and carries the global
grounder from birth. One attribution therefore covers all three files at the
pin.

At the pin (`e1a94af`, v3.6.0) the same structure stands: call site
`interpretation.py:577`, `_ground_rule` def `:810`, fresh-variable helpers
`:1396` / `:1406` — now with a `predicate_map` narrowing fresh groundings to
predicate-carrying components (present by the v3.0.0 tag; bugfix PR #61 merged
2024-12-15). That narrowing is by predicate, not by target — candidates remain
graph-global, and the banked Phase-4 profile clocks this clause-satisfaction
subtree at ~94% of large-rung runtime
([profile-phase4.md](profile-phase4.md)). The `prange` over rules at
`interpretation.py:571` (parallel width = rule count) is the same pin-era code
the Pokec report already characterized.

## Corroboration (upstream, public)

PR #43 ("New release v3.0.0", merged 2024-12-01,
`github.com/lab-v2/pyreason/pull/43`) describes the change in upstream's own
words: *"Make unseen clause variables in node clauses take all possible nodes
instead of just the neighbors."* The v3.0.0 release page's changelog is
one-line-per-PR and carries no performance notes; the release notes make no
mention of a complexity trade.

## What is measured vs what is attributed

- **Measured (banked, version granularity)** — the
  [Pokec scaling report](pokec-scaling-report.md): 202× at the 10k rung
  (13.4 s vs ~2,600 s), x^0.98 vs x^1.87 scaling in edges, the ~94%
  clause-satisfaction profile share. Those numbers compare release 1.2.4
  against the pin; they do not by themselves isolate a commit.
- **Attributed (this report, commit granularity)** — source-reading evidence
  that the target anchor survives every release through v2.3.0 and is removed
  in `b01a803`, first shipping in v3.0.0. The reading is corroborated by
  upstream's PR #43 text, but it is not yet an on-workload measurement of the
  step between adjacent releases.

## Queued confirmation

The empirical two-release confirmation is **queued for the lab box under the
operator's existing waiver** (not attempted here): the paper workload's 10k
rung, **v2.3.0** (last release without the rework) vs **v3.0.0** (first release
with it), same protocol as the banked runs (fresh-process bench, logged scratch
envs, median + band). Expected shape if the attribution is right: the ~2
orders-of-magnitude step lands between exactly those two releases; if it does
not, this report's attribution is wrong and gets revised, not defended.

## Reproduce (read-only, against the oracle clone)

```sh
# the pivot and its stats
git -C oracle/pyreason --no-pager show --stat b01a803
# fresh-variable candidate construction at the pivot
git -C oracle/pyreason show b01a803:pyreason/scripts/interpretation/interpretation.py | sed -n '1857,1900p'
# the paper-era anchor
git -C oracle/pyreason show 1.2.4:pyreason/scripts/interpretation/interpretation.py | sed -n '373,376p'
# the intermediate (still target-anchored) era
git -C oracle/pyreason show daeefde:pyreason/scripts/interpretation/interpretation.py | sed -n '688,692p'
# release bracketing
git -C oracle/pyreason show v2.3.0:pyreason/scripts/interpretation/interpretation.py | grep -c '_ground_rule(rule'   # 0
git -C oracle/pyreason show v3.0.0:pyreason/scripts/interpretation/interpretation.py | grep -n '_ground_rule(rule'   # :536
git -C oracle/pyreason --no-pager tag --contains b01a803 | head -1                                                   # v3.0.0
```
