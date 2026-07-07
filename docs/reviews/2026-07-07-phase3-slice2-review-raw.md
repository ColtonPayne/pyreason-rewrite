<!-- doccode: pyreason-rewrite-docs-reviews-phase3-slice2-review-raw -->
# Phase 3, slice 2 review — raw probe materials

The ten reviewer probes from [the review](2026-07-07-phase3-slice2-review.md),
verbatim, so the evidence is reproducible after the session scratchpad is gone.
Harness probes: put any subset in a directory and run
`PYTHONHASHSEED=0 uv run python -m harness.run --cases <dir> --engine-a oracle-env/bin/python --engine-b scripts/rewrite-python --results <fresh-dir>`.
All ten passed (identical cross-engine) on 2026-07-07.

## probe-conv-bound-arith.json

```json
{
  "id": "probe-conv-bound-arith",
  "purpose": "Reviewer probe: delta-bound convergence arithmetic on partial bounds — a [0.4,0.6] fact and a [0.5,1] rule head produce per-timestep max deltas 0.6 (t0), 0.5 (t1, the new derivation), 0 (t2, everything re-lands its previous bounds) against threshold 0.35, pinning that re-derived unchanged bounds contribute zero.",
  "runtime_class": "smoke",
  "surface_items": ["fn:reason"],
  "inputs": {
    "settings": {"verbose": false, "atom_trace": true},
    "graph": {"nodes": ["A"]},
    "rules": [
      {"text": "n(x) : [0.5, 1] <-1 m(x) : [0.1, 1]", "name": "rn"}
    ],
    "facts": [
      {"text": "m(A) : [0.4, 0.6]", "name": "f_m", "start": 0, "end": 3}
    ],
    "reason": {"timesteps": -1, "convergence_threshold": 500, "convergence_bound_threshold": 0.35}
  },
  "probes": [
    {"id": "trace-node", "kind": "rule_trace_node"},
    {"id": "nodes", "kind": "filter_sort_nodes", "labels": ["m", "n"]},
    {"id": "time", "kind": "get_time"}
  ],
  "comparison": {"probes": {}}
}
```

## probe-conv-count-one.json

```json
{
  "id": "probe-conv-count-one",
  "purpose": "Reviewer probe: convergence_threshold=1 — whether graph-attribute fact updates count toward changes_cnt at t=0 (they do at the pin, deferring convergence to t=1 where the lone new derivation meets the threshold), pinning the change-counting arithmetic and the <= comparison.",
  "runtime_class": "smoke",
  "surface_items": ["fn:reason"],
  "inputs": {
    "settings": {"verbose": false, "atom_trace": true},
    "graph": {
      "nodes": ["A", "B"],
      "edges": [["A", "B", {"F": 1}]]
    },
    "rules": [
      {"text": "pop(x) <-1 pop(y), F(y,x)", "name": "spread"}
    ],
    "facts": [
      {"text": "pop(A)", "name": "f_pop", "start": 0, "end": 2}
    ],
    "reason": {"timesteps": -1, "convergence_threshold": 1}
  },
  "probes": [
    {"id": "trace-node", "kind": "rule_trace_node"},
    {"id": "trace-edge", "kind": "rule_trace_edge"},
    {"id": "time", "kind": "get_time"}
  ],
  "comparison": {"probes": {}}
}
```

## probe-edge-chain.json

```json
{
  "id": "probe-edge-chain",
  "purpose": "Reviewer probe: a two-clause edge-head rule over a triangle — head-pair enumeration is filtered to existing edges, per-head temp-grounding refinement narrows the clause groundings, and the trace's clause columns carry the per-head-filtered edge sets.",
  "runtime_class": "smoke",
  "surface_items": ["fn:reason", "fn:get_rule_trace"],
  "inputs": {
    "settings": {"verbose": false, "atom_trace": true},
    "graph": {
      "nodes": ["A", "B", "C"],
      "edges": [
        ["A", "B", {"rel": 1}],
        ["B", "C", {"rel": 1}],
        ["A", "C", {"rel": 1}]
      ]
    },
    "rules": [
      {"text": "reach(x,z) <-1 rel(x,y), rel(y,z)", "name": "chain"}
    ],
    "facts": [
      {"text": "seed(A)", "name": "f_seed", "start": 0, "end": 1}
    ],
    "reason": {"timesteps": 1}
  },
  "probes": [
    {"id": "trace-edge", "kind": "rule_trace_edge"},
    {"id": "edges", "kind": "filter_sort_edges", "labels": ["reach"]},
    {"id": "time", "kind": "get_time"}
  ],
  "comparison": {"probes": {}}
}
```

## probe-fact-window.json

```json
{
  "id": "probe-fact-window",
  "purpose": "Reviewer probe: a fact active only in [2,4] with a delta-2 rule under perfect convergence — non-persistent resets starve the rule after the window closes and the run converges when t reaches the last enqueued conclusion (max_rules_time), pinning the fact-window and convergence-horizon bookkeeping.",
  "runtime_class": "standard",
  "surface_items": ["fn:reason"],
  "inputs": {
    "settings": {"verbose": false, "atom_trace": true},
    "graph": {
      "nodes": ["A", "B"],
      "edges": [["A", "B", {"F": 1}]]
    },
    "rules": [
      {"text": "pop(x) <-2 pop(y), F(y,x)", "name": "spread2"}
    ],
    "facts": [
      {"text": "pop(A)", "name": "f_pop", "start": 2, "end": 4}
    ],
    "reason": {"timesteps": -1}
  },
  "probes": [
    {"id": "trace-node", "kind": "rule_trace_node"},
    {"id": "nodes", "kind": "filter_sort_nodes", "labels": ["pop"]},
    {"id": "time", "kind": "get_time"}
  ],
  "comparison": {"probes": {}}
}
```

## probe-fp-delta0.json

```json
{
  "id": "probe-fp-delta0",
  "purpose": "Reviewer probe: delta-0 rule chain drives the inner fixed-point loop — fp counter increments per pass, delta-0 conclusions re-enter the same timestep, and the reset at t=1 starves regrounding so the run perfectly converges at t=1.",
  "runtime_class": "smoke",
  "surface_items": ["fn:reason"],
  "inputs": {
    "settings": {"verbose": false, "atom_trace": true},
    "graph": {"nodes": ["A"]},
    "rules": [
      {"text": "b(x) <-0 a(x)", "name": "rb"},
      {"text": "c(x) <-0 b(x)", "name": "rc"},
      {"text": "d(x) <-1 c(x)", "name": "rd"}
    ],
    "facts": [
      {"text": "a(A)", "name": "fa", "start": 0, "end": 0}
    ],
    "reason": {"timesteps": 1}
  },
  "probes": [
    {"id": "trace-node", "kind": "rule_trace_node"},
    {"id": "nodes", "kind": "filter_sort_nodes", "labels": ["a", "b", "c", "d"]},
    {"id": "time", "kind": "get_time"}
  ],
  "comparison": {"probes": {}}
}
```

## probe-inconsistency.json

```json
{
  "id": "probe-inconsistency",
  "purpose": "Reviewer probe: inconsistency resolution under the default inconsistency_check — both message arms (the IPL grounding-conflict text and the float_to_str bounds text), the [0,1]+static resolution rows, and consistent-fact IPL complement rows along the way.",
  "runtime_class": "smoke",
  "surface_items": ["fn:reason", "fn:add_inconsistent_predicate"],
  "inputs": {
    "settings": {"verbose": false, "atom_trace": true},
    "graph": {"nodes": ["A", "B"]},
    "ipl": [["p2", "q2"], ["r", "s"]],
    "rules": [
      {"text": "p(x) <-0 q(x)", "name": "rp"},
      {"text": "p2(x) <-0 q2(x)", "name": "rp2"},
      {"text": "r(x) <-0 w(x)", "name": "rr"}
    ],
    "facts": [
      {"text": "p(A) : [0, 0.2]", "name": "f_p", "start": 0, "end": 0},
      {"text": "q(A)", "name": "f_q", "start": 0, "end": 0},
      {"text": "q2(A)", "name": "f_q2", "start": 0, "end": 0},
      {"text": "s(B)", "name": "f_s", "start": 0, "end": 0},
      {"text": "w(B)", "name": "f_w", "start": 0, "end": 0}
    ],
    "reason": {"timesteps": 0}
  },
  "probes": [
    {"id": "trace-node", "kind": "rule_trace_node"},
    {"id": "nodes", "kind": "filter_sort_nodes", "labels": ["p", "q", "p2", "q2", "r", "s", "w"]},
    {"id": "time", "kind": "get_time"}
  ],
  "comparison": {"probes": {}}
}
```

## probe-static-fact.json

```json
{
  "id": "probe-static-fact",
  "purpose": "Reviewer probe: static user facts ride forward re-enqueueing at t+1, and the static-bound trace arm's node/edge asymmetry — a second static fact on an already-static component banks the FACT's bound in the node arm but the live WORLD bound in the edge arm (interpretation.py:299 vs :375 at the pin).",
  "runtime_class": "smoke",
  "surface_items": ["fn:reason", "fn:get_rule_trace"],
  "inputs": {
    "settings": {"verbose": false, "atom_trace": true},
    "graph": {
      "nodes": ["A", "B"],
      "edges": [["A", "B", {"F": 1}]]
    },
    "rules": [
      {"text": "pop(x) <-1 pop(y), F(y,x)", "name": "spread"}
    ],
    "facts": [
      {"text": "pop(A)", "name": "f_pop", "start": 0, "end": 0, "static": true},
      {"text": "pn(A) : [0.5, 1]", "name": "f_pn1", "start": 0, "end": 0, "static": true},
      {"text": "pn(A) : [0.25, 1]", "name": "f_pn2", "start": 0, "end": 0, "static": true},
      {"text": "pe(A,B) : [0.5, 1]", "name": "f_pe1", "start": 0, "end": 0, "static": true},
      {"text": "pe(A,B) : [0.25, 1]", "name": "f_pe2", "start": 0, "end": 0, "static": true}
    ],
    "reason": {"timesteps": 3}
  },
  "probes": [
    {"id": "trace-node", "kind": "rule_trace_node"},
    {"id": "trace-edge", "kind": "rule_trace_edge"},
    {"id": "nodes", "kind": "filter_sort_nodes", "labels": ["pop", "pn"]},
    {"id": "time", "kind": "get_time"}
  ],
  "comparison": {"probes": {}}
}
```

## probe-threshold-edges.json

```json
{
  "id": "probe-threshold-edges",
  "purpose": "Reviewer probe: threshold boundary arithmetic — percent ratio 2/3 against 66.66 (passes) vs 66.67 (fails), equal-percent 50 on an exact half, less_equal-0 satisfied by an empty qualifying set (rule still fires for heads from other clauses), and percent/available re-basing the denominator on label carriers (1/2 passes 50 where total's 1/3 would fail).",
  "runtime_class": "smoke",
  "surface_items": ["type:Threshold"],
  "inputs": {
    "settings": {"verbose": false, "atom_trace": true},
    "graph": {
      "nodes": ["A", "B", "C", "D", "E", "F", "G"],
      "edges": [
        ["A", "B", {"Friends": 1}],
        ["A", "C", {"Friends": 1}],
        ["A", "D", {"Friends": 1}],
        ["E", "F", {"FriendsX": 1}],
        ["E", "G", {"FriendsX": 1}]
      ]
    },
    "rules": [
      {"text": "t1(x) <-1 Friends(x,y), popular(y)", "name": "r6666",
       "custom_thresholds": [
         {"quantifier": "greater_equal", "quantifier_type": ["number", "total"], "thresh": 1},
         {"quantifier": "greater_equal", "quantifier_type": ["percent", "total"], "thresh": 66.66}]},
      {"text": "t2(x) <-1 Friends(x,y), popular(y)", "name": "r6667",
       "custom_thresholds": [
         {"quantifier": "greater_equal", "quantifier_type": ["number", "total"], "thresh": 1},
         {"quantifier": "greater_equal", "quantifier_type": ["percent", "total"], "thresh": 66.67}]},
      {"text": "t3(x) <-1 FriendsX(x,y), busyX(y)", "name": "req50",
       "custom_thresholds": [
         {"quantifier": "greater_equal", "quantifier_type": ["number", "total"], "thresh": 1},
         {"quantifier": "equal", "quantifier_type": ["percent", "total"], "thresh": 50}]},
      {"text": "t4(x) <-1 Friends(x,y), spam(z)", "name": "rle0",
       "custom_thresholds": [
         {"quantifier": "greater_equal", "quantifier_type": ["number", "total"], "thresh": 1},
         {"quantifier": "less_equal", "quantifier_type": ["number", "total"], "thresh": 0}]},
      {"text": "t5(x) <-1 Friends(x,y), maybe(y)", "name": "ravail50",
       "custom_thresholds": [
         {"quantifier": "greater_equal", "quantifier_type": ["number", "total"], "thresh": 1},
         {"quantifier": "greater_equal", "quantifier_type": ["percent", "available"], "thresh": 50}]}
    ],
    "facts": [
      {"text": "popular(B)", "name": "f_b", "start": 0, "end": 1},
      {"text": "popular(C)", "name": "f_c", "start": 0, "end": 1},
      {"text": "busyX(F)", "name": "f_f", "start": 0, "end": 1},
      {"text": "maybe(B)", "name": "f_mb", "start": 0, "end": 1},
      {"text": "maybe(C) : [0.3, 1]", "name": "f_mc", "start": 0, "end": 1}
    ],
    "reason": {"timesteps": 1}
  },
  "probes": [
    {"id": "trace-node", "kind": "rule_trace_node"},
    {"id": "nodes", "kind": "filter_sort_nodes", "labels": ["t1", "t2", "t3", "t4", "t5"]},
    {"id": "time", "kind": "get_time"}
  ],
  "comparison": {"probes": {}}
}
```

## probe-clause-reorder.json

```json
{
  "id": "probe-clause-reorder",
  "purpose": "Reviewer probe: an edge-heavy graph (4 edges > 3 nodes) triggers the clause-reordering optimization — grounding runs node-clause-first while the trace's clause columns render back in the author's order through the clause map, cross-engine.",
  "runtime_class": "smoke",
  "surface_items": ["fn:reason", "fn:get_rule_trace"],
  "inputs": {
    "settings": {"verbose": false, "atom_trace": true},
    "graph": {
      "nodes": ["A", "B", "C"],
      "edges": [
        ["A", "B", {"F": 1}],
        ["A", "C", {"F": 1}],
        ["B", "C", {"F": 1}],
        ["C", "A", {"F": 1}]
      ]
    },
    "rules": [
      {"text": "t(x) <-1 F(x,y), pop(y)", "name": "t_rule"}
    ],
    "facts": [
      {"text": "pop(B)", "name": "f_b", "start": 0, "end": 1}
    ],
    "reason": {"timesteps": 1}
  },
  "probes": [
    {"id": "trace-node", "kind": "rule_trace_node"},
    {"id": "nodes", "kind": "filter_sort_nodes", "labels": ["t", "pop"]},
    {"id": "rules-live", "kind": "accessor_fingerprint", "accessor": "rules"},
    {"id": "time", "kind": "get_time"}
  ],
  "comparison": {"probes": {}}
}
```

## regfns_probe.py (direct two-engine probe)

Run from the repo root, once per engine (oracle kernel cache
snapshot/restored around the oracle run exactly as harness/capture.py
does for registrand cases):

```
PYTHONHASHSEED=0 oracle-env/bin/python  <script> oracle
PYTHONHASHSEED=0 scripts/rewrite-python <script> rewrite
```

```python
"""Reviewer probe: registered annotation/head functions, cross-engine.

Run once under each engine interpreter from the repo root:
  PYTHONHASHSEED=0 oracle-env/bin/python  scratchpad/regfns_probe.py oracle
  PYTHONHASHSEED=0 scripts/rewrite-python scratchpad/regfns_probe.py rewrite

The oracle requires njit-compilable registrands; the rewrite env has no
numba, so the same functions ride plain. The compared observation is the
printed canonical trace + time, which must be identical.
"""
import sys

mode = sys.argv[1]

import networkx as nx
import pyreason as pr

pr.settings.verbose = False
pr.settings.atom_trace = True


def clause_lower_mean(annotations, weights):
    total = 0.0
    count = 0
    upper = 0.0
    for i, clause in enumerate(annotations):
        for ann in clause:
            total += ann.lower * weights[i]
            count += 1
            if ann.upper > upper:
                upper = ann.upper
    return total / count, upper


def clause_zero_grounding_eighths(annotations, weights, qualified_nodes,
                                  qualified_edges, clause_labels,
                                  clause_variables):
    count = len(qualified_nodes[0]) + len(qualified_edges[0])
    lower = count / 8.0
    if lower > 1.0:
        lower = 1.0
    return lower, 1.0


if mode == "oracle":
    import numba

    def pick_first(fn_arg_values):
        return numba.typed.List([fn_arg_values[0][0]])

    ann1 = numba.njit(clause_lower_mean)
    ann2 = numba.njit(clause_zero_grounding_eighths)
    head1 = numba.njit(pick_first)
    # njit renames survive: __name__ rides through the dispatcher
else:
    def pick_first(fn_arg_values):
        return [fn_arg_values[0][0]]

    ann1 = clause_lower_mean
    ann2 = clause_zero_grounding_eighths
    head1 = pick_first

pr.add_annotation_function(ann1)
pr.add_annotation_function(ann2)
pr.add_head_function(head1)

g = nx.DiGraph()
g.add_nodes_from(["A", "B", "C"])
g.add_edge("A", "B", Friends=1)
g.add_edge("A", "C", Friends=1)
pr.load_graph(g)

pr.add_rule(pr.Rule("w(x) : clause_lower_mean <-1 Friends(x,y), m(y) : [0.1, 1]", "r_ann2"))
pr.add_rule(pr.Rule("z(x) : clause_zero_grounding_eighths <-1 Friends(x,y), m(y) : [0.1, 1]", "r_ann6"))
pr.add_rule(pr.Rule("~neg(x) : clause_lower_mean <-1 Friends(x,y), m(y) : [0.1, 1]", "r_annneg"))
pr.add_rule(pr.Rule("Processed(pick_first(V)) <- starter(V)", "r_head"))
pr.add_fact(pr.Fact("m(B) : [0.5, 0.75]", "f_mb", 0, 1))
pr.add_fact(pr.Fact("m(C) : [0.25, 1]", "f_mc", 0, 1))
pr.add_fact(pr.Fact("starter(B)", "f_s1", 0, 1))
pr.add_fact(pr.Fact("starter(C)", "f_s2", 0, 1))

interp = pr.reason(timesteps=1)

node_frame, edge_frame = pr.get_rule_trace(interp)


def canon(cell):
    if isinstance(cell, float) and cell != cell:  # NaN (pandas padding)
        return None
    if isinstance(cell, list):
        return [canon(c) for c in cell]
    if isinstance(cell, tuple):
        return tuple(canon(c) for c in cell)
    return cell


print("COLUMNS", list(node_frame.columns))
for row in node_frame.itertuples(index=False, name=None):
    print("NROW", [canon(c) for c in row])
for row in edge_frame.itertuples(index=False, name=None):
    print("EROW", [canon(c) for c in row])
print("TIME", pr.get_time())
```

## regfns probe output (identical from both engines, banked from the rewrite run)

```
COLUMNS ['Time', 'Fixed-Point-Operation', 'Node', 'Label', 'Old Bound', 'New Bound', 'Occurred Due To', 'Consistent', 'Triggered By', 'Inconsistency Message', 'Clause-1', 'Clause-2']
NROW [0, 0, 'B', 'm', '[0.0,1.0]', '[0.5,0.75]', 'f_mb', True, 'Fact', '', None, None]
NROW [0, 0, 'C', 'm', '[0.0,1.0]', '[0.25,1.0]', 'f_mc', True, 'Fact', '', None, None]
NROW [0, 0, 'B', 'starter', '[0.0,1.0]', '[1.0,1.0]', 'f_s1', True, 'Fact', '', None, None]
NROW [0, 0, 'C', 'starter', '[0.0,1.0]', '[1.0,1.0]', 'f_s2', True, 'Fact', '', None, None]
NROW [0, 1, 'B', 'Processed', '[0.0,1.0]', '[1.0,1.0]', 'r_head', True, 'Rule', '', ['B', 'C'], None]
NROW [1, 2, 'B', 'm', '[0.0,1.0]', '[0.5,0.75]', 'f_mb', True, 'Fact', '', None, None]
NROW [1, 2, 'C', 'm', '[0.0,1.0]', '[0.25,1.0]', 'f_mc', True, 'Fact', '', None, None]
NROW [1, 2, 'B', 'starter', '[0.0,1.0]', '[1.0,1.0]', 'f_s1', True, 'Fact', '', None, None]
NROW [1, 2, 'C', 'starter', '[0.0,1.0]', '[1.0,1.0]', 'f_s2', True, 'Fact', '', None, None]
NROW [1, 2, 'A', 'w', '[0.0,1.0]', '[0.6875,1.0]', 'r_ann2', True, 'Rule', '', [('A', 'B'), ('A', 'C')], ['B', 'C']]
NROW [1, 2, 'A', 'z', '[0.0,1.0]', '[0.25,1.0]', 'r_ann6', True, 'Rule', '', [('A', 'B'), ('A', 'C')], ['B', 'C']]
NROW [1, 2, 'A', 'neg', '[0.0,1.0]', '[0.0,0.3125]', 'r_annneg', True, 'Rule', '', [('A', 'B'), ('A', 'C')], ['B', 'C']]
NROW [1, 3, 'B', 'Processed', '[0.0,1.0]', '[1.0,1.0]', 'r_head', True, 'Rule', '', ['B', 'C'], None]
TIME 2
```
