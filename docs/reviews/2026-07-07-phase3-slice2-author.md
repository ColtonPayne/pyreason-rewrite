<!-- doccode: pyreason-rewrite-docs-reviews-phase3-slice2-author -->
# Phase 3, slice 2 — author report: the default-path reasoning spine

- session: 17 · date: 2026-07-07 · author packet
- verdict: **13/13 oracle-vs-rewrite PASS** (`results-phase3-slice2/report.json`),
  fast tier **195 passed** (175 preexisting + 20 new), zero DIV records needed
- code commits: `56b0559` (engine + ADR 0002), `0ad3fa4` (seam tests);
  design record: [ADR 0002](../adr/0002-reference-core-state-step-trace.md)

## What was built, and why shaped that way

The reference reasoning core — the heart of Phase 3 — as pure Python over
the explicit state landed in slice 1, transcribed meaning-for-meaning from
the pinned default-settings engine (the non-parallel, non-fp
`interpretation.py` at e1a94af3):

| piece | file(s) | shape rationale |
|---|---|---|
| graph load | `_graph.py` | `load_graph` copies into a fresh DiGraph and reduces attributes to graph-attribute facts + specific labels (the pinned coercion ladder, incl. the unconditional "Added N ..." print) |
| world | `_world.py` | Label→Interval map per component; `update` runs the JITTED intersection arm (`interval.intersect_jitted`, prev bounds preserved through updates — what makes re-derivation count zero toward convergence) |
| grounding | `_grounding.py` | clause candidate derivation (4 edge-clause cases), qualification, CLAUSE-LEVEL threshold gating (number/percent × total/available), dependency-graph refinement to fixed point, head-function resolution (silent no-match arm) |
| step loop | `_interpretation.py` | the temporal fixed-point loop: non-persistent reset, due facts (nodes→edges), inner delta-0 loop, reground-on-update, three convergence modes; `_ground_rule`; the shared update body with IPL propagation and inconsistency resolution; `annotate` with the pinned NameError arm |
| program | `_program.py` | `Program` (the `get_logic_program().interp` contract), `reorder_clauses`, `filter_ruleset` |
| views | `_output.py` | `Frame` (the DataFrame surface the capture consumes: `columns`/`itertuples`/`empty`) — trace frames with ragged-row None padding and clause-map re-rendering; the filter/sort per-timestep frames |
| facade + state | `__init__.py`, `_state.py` | `load_graph`, `reason` (+again/queries structure), `add_inconsistent_predicate`, `add_annotation_function` (pinned arity TypeError), `add_head_function`, `add_closed_world_predicate`, `get_rule_trace`, `filter_and_sort_nodes/edges` — one-line delegations to pure functions over `EngineState` |

Numba *idioms* were not transcribed; ADR 0002 §Decision 2 names each
collapse and why it is order-equivalent (threadsafe per-rule buffers →
sequential appends; one shared `_update_component` body with the pinned
node/edge static-fact trace asymmetry kept per-kind; the never-fed
`edges_to_be_added_node_rule` container omitted).

## Banked contracts leaned on, and how each was re-verified

1. **The 13 banked oracle artifacts** (`results/<case>/a1.json`, session-15
   sweep) — used as design-time diff targets: every probe of all 13 cases
   was diffed against them via fresh-process rewrite captures BEFORE the
   live run (screen script, scratchpad). Final cross-check: all 39 rewrite
   `b1` probe digests equal the banked sweep's `a1` digests byte-for-byte
   (command below).
2. **Clause-level threshold gating** (sessions 12–14 characterization,
   surface.md type:Threshold notes) — re-verified against the pinned source
   (`check_node_grounding_threshold_satisfaction`,
   interpretation.py:1364-1377: the gate consumes the clause's whole-graph
   candidate/qualified counts before head enumeration) and re-proven live by
   threshold-number-gate-clause-level plus the seam test's thresh=3 twin.
3. **The unregistered-name asymmetry** (session 13/14 screens; case
   purposes) — re-verified at interpretation.py:1918-1931 (objmode output
   variable assigned only inside the match loop → NameError) vs :2330-2338
   (pre-seeded empty head grounding → silence); both arms pass live and are
   seam-tested with exact message text.
4. **Interval prev-seed divergence** (interval-ops row; board item) — the
   engine-internal arm re-verified at interval_type.py:56-63 (jitted
   intersection seeds prev from self's PREVIOUS bounds) vs the proxy arm at
   interval.py:69; implemented as two explicit arms
   (`Interval.intersection` public / `intersect_jitted` engine) with the
   convergence consequence seam-tested
   (test_rederived_bound_counts_zero_toward_convergence).
5. **The capture contract** (`harness/capture.py`) — inputs applied
   settings→graph→rules→facts→reason; probes consume `columns`/`itertuples`
   only; exceptions compare module-qualified with exact messages — which is
   what makes `Frame` sufficient and the NameError text load-bearing.

## Acceptance criteria, answered

1. **Pure functions over explicit state, one core, ADR.** All run state
   lives on the `Interpretation` object; the loop/grounding/update functions
   are module-level over it; the facade holds exactly one `EngineState` and
   only grew one-line delegations. No second core, no module state beyond
   the facade's single state instance (seam-tested:
   test_engine_states_are_independent still green, and every new test swaps
   a fresh state through the facade). Design recorded in
   `docs/adr/0002-reference-core-state-step-trace.md`.
2. **Fast tier.** `uv run pytest -m "not e2e"` → **195 passed, 2
   deselected** (pre-commit hook enforces per commit). 20 new seam tests in
   `tests/test_rewrite_reasoning_core.py`, all driven through the facade
   (`load_graph/add_rule/add_fact/reason` in, trace/filter/get_time out),
   each with a `proves:` docstring: grounding + trace rows, threshold gating
   (clause-level, percent, available-vs-total, dict form), the three
   convergence modes' hand-derived stop times, re-derivation counting zero,
   annotation fns (2-arg, 6-arg metadata, arity gate, unregistered raise),
   head fns (registered + silent unregistered), closed-world both arms, IPL
   rows, queries filtering, clause reordering, store-off gating.
3. **13-case run: 13/13 PASS** into `results-phase3-slice2/` (gitignored
   like the other results dirs — verdict of record is `report.json` + the
   table below). Per case: 4 fresh-process captures, same-engine repeats
   digest-stable (a1=a2 and b1=b2 for all 13), A-vs-B equal. **Zero
   divergences → no DIV records.** Additionally all 39 rewrite probe digests
   equal the banked session-15 sweep's oracle digests.
4. **surface.md.** Row flipped to `equivalent`: **`type:Threshold`** — the
   only row whose full `cases` list (threshold-construct + the five
   consumption cases) now sits inside the 25 cases passed across sessions
   16–17. Every other row these 13 cases touch (fn:load_graph, fn:add_rule,
   fn:add_fact, fn:reason, fn:filter_and_sort_nodes/edges,
   fn:get_rule_trace, fn:get_time, fn:add_annotation_function,
   fn:add_head_function, fn:add_closed_world_predicate, type:Rule/Fact, the
   dsl rows, setting rows) keeps `cased`: their case lists include cases
   outside the sessions' proof sets (verified mechanically by subset check).
   Coverage: **3/52 rows equivalent-or-adjudicated (5.8%)**, from 2/52.
   Inventory gate green (in the 195).
5. **Hygiene.** All work committed; `git status` clean at close;
   `git -C oracle/pyreason status --porcelain` empty, pin untouched; no
   installs or dependency changes (pandas deliberately NOT requested — see
   asks); banked `results/`, `results-phase3-slice1/`,
   `results-phase3-slice1-review/` unmodified (results/ read only); scratch
   files confined to the session scratchpad.

## Per-case verdicts (oracle-vs-rewrite, 4 fresh captures each)

Wall-clock is the artifact-recorded per-capture engine time (import +
reason/steps) for the first capture of each engine; verdicts of record are
`results-phase3-slice2/report.json`.

| case | verdict | oracle a1 | rewrite b1 |
|---|---|---|---|
| hello-world | pass | 4.29s | 0.06s |
| conv-perfect | pass | 4.23s | 0.06s |
| conv-delta-interp | pass | 4.17s | 0.06s |
| conv-delta-bound | pass | 4.20s | 0.09s |
| edge-rule-frames | pass | 4.23s | 0.06s |
| closed-world-off | pass | 3.77s | 0.09s |
| annotation-fn-unregistered-name | pass | 4.22s | 0.06s |
| head-fn-unregistered-name | pass | 3.82s | 0.06s |
| threshold-dict-gate | pass | 3.87s | 0.06s |
| threshold-number-gate-clause-level | pass | 3.92s | 0.06s |
| threshold-number-gate-default | pass | 3.87s | 0.09s |
| threshold-number-gate-two | pass | 3.87s | 0.06s |
| threshold-percent-total | pass | 3.88s | 0.06s |

(The rewrite's smaller numbers are import weight, not a speed claim — the
oracle pays numba/pandas import per fresh process; no performance claim is
made or licensed by this table.)

## Deliberately-reproduced oracle behaviors (AC-6 candidates, not blessed)

Each reproduced because matching the pin is the default meaning of correct;
each is a legitimate oracle-bug-candidate follow-up if the operator wants an
improvement proposal, and none was silently absorbed:

- **Unregistered annotation-function NameError** with the pinned message
  `name 'annotation' is not defined` — an accidental unbound-variable raise
  at the pin, reproduced as an explicit raise at the same decision point
  (interpretation.py:1918-1931; `_interpretation.annotate`).
- **Unregistered head-function silence** — the asymmetric twin: empty head
  grounding, rule fires for no one, run completes
  (interpretation.py:2330-2338).
- **No-break annotation match loop** — every same-named registrand runs,
  last result wins (interpretation.py:1919-1930).
- **Two intersection arms** (proxy vs jitted prev-seeding) — both kept, the
  board item stands (ADR 0002 §Decision 4).
- **`filter_ruleset`'s unordered de-dup** (`list(set(...))`) — surviving
  rule order is an unpinned behavior; transcribed as-is, flagged for the
  query-consuming cases' session (single-rule arm seam-tested only).
- **Graph-attribute parse print** — unconditional stdout output at load
  time, kept (observable under the stdout-redirect knob's future cases).

## Deviations from the pin / spec, with reasons

- **`Frame` instead of pandas DataFrames** for `get_rule_trace` and
  `filter_and_sort_*` returns: the campaign takes no new dependencies
  without an operator ask, and every consumer (capture, seam tests)
  compares cell-for-cell through `columns`/`itertuples`/`empty`, which
  Frame reproduces including ragged-row None padding and clause-map
  re-rendering. An embedder using pandas-only DataFrame methods would see
  the difference; that is a documented consequence in ADR 0002, revisitable
  as an ask if a case ever compares a pandas-only surface.
- **Narrowed excepts**: the pin's blanket `except Exception` guards around
  component/label lookup become `except KeyError` (+ `AttributeError` in
  satisfaction checks) — same reachable arms ("missing never
  satisfies/updates"), but a rewrite implementation fault cannot silently
  bank as engine behavior (ADR 0002 §Decision 5).
- **Non-default arms wired but unproven** (structure transcribed from the
  pin, no covering case run this session — no equivalence claim):
  `reason(again=..., restart=...)` / `Program.reason_again`, queries
  filtering beyond the single-rule seam test, `update_mode='override'`,
  inconsistency resolution, infer-edges edge addition, IPL propagation
  beyond the seam-tested basic arm, `allow_ground_rules=True`,
  persistent=True. Their cases are later packets.
- **Not implemented this slice** (packet scope; their cases are later
  packets): `load_graphml`, `save_rule_trace`, `load_inconsistent_predicate_list`
  (pyyaml ask), the reset family, `Interpretation.get_dict`/`query`,
  `output_to_file`/`memory_profile` reason-time arms, the
  parallel/fp_version interpretation variants (`Program` builds the one
  reference core regardless — the knobs' distinguishing cases will
  adjudicate what those arms mean for the rewrite).

## Reproduction commands (from the repo root)

```
# fast tier (AC-2 evidence)
uv run pytest -m "not e2e"

# the 13-case oracle-vs-rewrite run (AC-3 evidence)
mkdir -p /tmp/phase3-slice2-cases && for c in hello-world conv-perfect \
  conv-delta-interp conv-delta-bound edge-rule-frames closed-world-off \
  annotation-fn-unregistered-name head-fn-unregistered-name \
  threshold-dict-gate threshold-number-gate-clause-level \
  threshold-number-gate-default threshold-number-gate-two \
  threshold-percent-total; do cp harness/cases/$c.json /tmp/phase3-slice2-cases/; done
PYTHONHASHSEED=0 uv run python -m harness.run --cases /tmp/phase3-slice2-cases \
  --engine-a oracle-env/bin/python --engine-b scripts/rewrite-python \
  --results results-phase3-slice2

# rewrite-vs-banked-sweep digest cross-check (39/39 probes)
uv run python -c "
import json, pathlib
cases = [p.stem for p in pathlib.Path('/tmp/phase3-slice2-cases').glob('*.json')]
assert all(json.load(open(f'results/{c}/a1.json'))['digests']
           == json.load(open(f'results-phase3-slice2/{c}/b1.json'))['digests']
           for c in cases), 'digest mismatch'
print('ALL MATCH', len(cases), 'cases')"
```

## Queued-ask recommendations

- **pyyaml** (already queued): unchanged; nothing in this slice pre-shapes it.
- **pandas**: **not recommended.** Frame covers every current consumer
  cell-for-cell; a dependency for display parity alone buys no equivalence
  evidence. Revisit only if a future case compares a pandas-only surface
  (e.g. save_rule_trace's CSV rendering can be done with stdlib csv when
  that packet lands — its exact bytes will adjudicate).
