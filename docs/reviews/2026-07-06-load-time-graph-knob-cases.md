<!-- doccode: pyreason-rewrite-docs-reviews-2026-07-06-load-time-graph-knob-cases -->
# Review report — the load-time graph-knob cases (attr parsing, static stamp, trace inclusion)

Scope: the six-case authoring commit (`9473457`) — three settings-only pairs
over one shared attribute-bearing inline graph. One focused reviewer-fixer with
no shared session context, verifying against the pinned oracle source
(`e1a94af33e1f`) and the run artifacts, then applying fixes in-session.

Every mechanism claim was re-derived at the pin: the load-time gate and its
else branch (`pyreason.py:602`/`:604-608`, mirrored at `:580` for
`load_graphml`), the `static_graph_facts` consumption at `:603` flowing into
the parser's static stamp (`graphml_parser.py:60`/`:90`, bound `[1,1]` for the
value-1 attributes), the non-persistent per-timestep reset that spares static
worlds (`interpretation.py:260-273`, `interval.reset()` restoring `[0,1]`),
the perfect-convergence exit (`:674-680`, with `max_rules_time = t + delta`
keeping the regrounding twins at `get_time` 3), and the trace gates
(`:1538`/`:1657` in `_update_node`/`_update_edge`, `:297`/`:373` static
branches, `:340`/`:415` static re-appends). The `get_time`/frame arithmetic
checks out (`get_time` returns `t`; `get_dict` yields `t` frames). Non-vacuity
was re-derived from the artifacts: every pair differs on multiple reasoning
probes (parsing 3-vs-1 and static 3-vs-2 on `time`, `nodes-derived`,
`nodes-special`, `edges-rel`, `trace-node`; the trace pair on both traces and
the trace-derived `special`/`rel` frames), and the predicted-identical probes
are digest-equal (`trace-edge` for the first two pairs; `nodes-derived` and
`time` for the trace pair — its "trace contents only, never derived bounds"
note). Twins differ only in the target knob; all eight in-scope board classes
are covered; every cross-twin observation carries the authoring-time hedge
(the session-6 finding did not recur); the commit touches only the six case
files, the oracle tree is untouched, and the board/ledger are correctly left
for the phase boundary.

## Fixed

- **L1 (Low)** — the save-graph-attrs-to-trace purposes cited only the
  node-side source lines for behavior their own probes also pin on the edge
  side (`trace-edge` rows flow through `_update_edge` at `:1657` and the edge
  re-append at `:415`, not `:1538`/`:340`), and the off twin quoted the
  `:297`/`:373` predicate form (`or not graph_attribute`) while attributing it
  to `:1538` (whose form is `or not mode=='graph-attribute-fact'`). Both
  purposes now cite the node/edge line pairs and attach each predicate form to
  its own site. Case inputs, probes, and behavior unchanged.

## Deferred with rationale

None — the single finding was fixed in-session.

## Rerun evidence (post-fix)

- `uv run pytest -m "not e2e"` — 61 passed, 2 deselected.
- `uv run python -m harness.run --cases harness/cases/<case>.json
  --engine-a oracle-env/bin/python` for each of the six cases (the run
  harness takes one case per invocation) — ALL PASS on all six, fresh
  same-engine repeat captures; cross-twin digests re-derived from the fresh
  artifacts match the table above.
