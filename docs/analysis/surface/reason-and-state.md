# Input equivalence classes: reason, state accessors, resetters, and core value types

Pin: `e1a94af3`, pyreason v3.6.0. Source-read only; anchors are `file:line` at the pin.
All line references are to files under `oracle/pyreason/pyreason/`.

Module-global state lives at the top of `pyreason.py`: `__rules`, `__program`, `__node_facts`,
`__edge_facts`, `__ipl`, `__clause_maps`, `__timestamp`, `__closed_world_predicates`,
`__specific_graph_node_labels`/`__specific_graph_edge_labels`, and the `settings` singleton.
Most items below read or mutate that shared state, so a differential harness must control call
ordering, not just arguments.

---

## fn:reason

**anchor:** `pyreason.py:1497` (hint correct).

**contract:** Runs the main fixed-point reasoning loop over the already-loaded graph and rules,
dispatching to a fresh run (`_reason`) or a resumed run (`_reason_again`), and returns the final
`Interpretation`.

**input classes:**
- happy-fresh: `again=False` with rules loaded runs `_reason`; builds a new `Program` and returns its interpretation (`pyreason.py:1516`, `1522`, `1534`).
- again-resume: `again=True` and `__program is not None` runs `_reason_again` on the existing program (`pyreason.py:1523`, `1529`, `1629`).
- again-but-no-program: `again=True` while `__program is None` still falls into the fresh `_reason` branch (the `or __program is None` short-circuit at `pyreason.py:1516`), so "again" silently degrades to a first run rather than asserting.
- again-assert-path: calling `_reason_again` with `__program` cleared (e.g. after `reset()`) trips `assert __program is not None` (`pyreason.py:1631`).
- conv-perfect: `timesteps=-1, convergence_threshold=-1, convergence_bound_threshold=-1` selects `perfect_convergence`; loop ends only when `t>=max_facts_time and t>=max_rules_time` (`interpretation.py:179-181`, `675`).
- conv-delta-interp: `convergence_bound_threshold=-1` and `convergence_threshold>=0` selects `delta_interpretation`; converges when `changes_cnt <= convergence_threshold` (`interpretation.py:182-184`, `657-663`).
- conv-delta-bound: any `convergence_bound_threshold != -1` selects `delta_bound` and IGNORES `convergence_threshold` entirely; converges when `bound_delta <= convergence_bound_threshold` (`interpretation.py:185-187`, `664-670`). `convergence_bound_threshold` strictly dominates when both are set — a load-bearing precedence class.
- timesteps-cap: `timesteps=N>=0` sets `tmax=N`; the loop stops when `t==tmax` even if not converged (`interpretation.py:254-255`). `timesteps=0` runs exactly the `t=0` pass then halts (`t==tmax` true on entry).
- timesteps-neg1-run-to-convergence: `timesteps=-1` makes `t==tmax` never true, so termination depends solely on the convergence branch — pair this class with each conv-* mode.
- queries-filter: `queries` non-None calls `ruleset_filter.filter_ruleset(queries, __rules)` and REASSIGNS the `__rules` global to the filtered set (`pyreason.py:1594-1595`); the empty vs. non-empty vs. no-match query list are distinct sub-cases. `queries=None` skips filtering.
- restart-true (resume): `again=True, restart=True` sets `tmax=timesteps` and resets `self.time=0` / `prev_reasoning_data[0]=0` before the extra run (`program.py:54-56`, `interpretation.py:221-223`).
- restart-false (resume): `again=True, restart=False` sets `tmax = interp.time + timesteps`, continuing the timeline (`program.py:57`); the loop starts at the stored `prev_reasoning_data[0]`.
- memory-profile-on: `settings.memory_profile=True` wraps the run in `memory_profiler.memory_usage(...)` and prints MB used; the return value is the `retval` of the profiled call, not the profiler tuple (`pyreason.py:1517-1520`, `1524-1527`). This is a distinct path for both fresh and again branches.
- no-graph: `__graph is None` auto-loads an empty `nx.DiGraph()` (and warns only if `settings.verbose`) rather than erroring (`pyreason.py:1545-1548`).
- no-rules: `__rules is None` raises `Exception('There are no rules...')` (`pyreason.py:1549-1550`).
- trace-suppression-interaction: `store_interpretation_changes=False` force-sets `settings.atom_trace=False` before building the program (`pyreason.py:1584-1585`) — mutates the settings singleton as a side effect.
- clause-reorder: `len(__graph.edges) > len(__graph.nodes)` reorders clauses (node clauses ahead of edge clauses) and rebuilds `__rules` + `__clause_maps` (`pyreason.py:1598-1606`); equal or fewer edges takes the identity-map path.
- output-to-file: `settings.output_to_file=True` reopens `sys.stdout` to `./<name>_<timestamp>.txt` in append mode (`pyreason.py:1513-1514`, again at `1541-1542`) — a process-global stdout redirect that never restores.

**notes:** `_reason` clears `__node_facts`/`__edge_facts` to `None` on exit (`pyreason.py:1623-1624`), so a second fresh `reason()` reasons only over facts added since. `queries` filtering permanently narrows the `__rules` global — a subsequent `reason()` without queries sees the already-filtered set unless rules are re-added. The `analysis corpus (REASON_ANALYSIS.md)` describes a fourth `'naive'` convergence mode; hypothesis(corpus-naive-mode) — not present at this pin, `_init_convergence` emits only the three modes above. Returned time convention: on convergence the loop does `t += 1` before breaking so the returned `interp.time` equals `t-1` (`interpretation.py:662`,`669`,`679`,`233`), i.e. consistent with the non-converged `tmax+1` case.

---

## fn:save_rule_trace

**anchor:** `pyreason.py:1645` (hint correct).

**contract:** Writes the node and edge rule-trace DataFrames (every interpretation change) to CSV
files in `folder`, using the `Output` helper.

**input classes:**
- happy: `store_interpretation_changes` on and a valid interpretation writes both traces (`pyreason.py:1654-1655`).
- store-off-assert: `settings.store_interpretation_changes=False` fails `assert` before any I/O (`pyreason.py:1652`).
- atom-trace-columns: `interpretation.atom_trace=True` adds per-clause `Clause-i` columns and fills "Occurred Due To" from the atom trace; off, those columns are absent and "Occurred Due To" comes from the rule name `r[7]` (`output.py:24-47`).
- folder-variants: default `folder='./'` vs. a caller path; the path is passed straight through to `Output.save_rule_trace` (`pyreason.py:1650`, `1655`).
- clause-map-reorder: a non-empty `__clause_maps` (populated by `reason`) drives `_reorder_row`, so trace column order reflects clause reordering; an empty/`None` map leaves order untouched (`output.py:6-8`, `93-97`).

**notes:** `Output` is constructed with the module-global `__timestamp` and `__clause_maps`
(`pyreason.py:1654`); both are set by the most recent `reason()`. Calling this before any
`reason()` uses a stale/empty timestamp and clause map. `reset()` does NOT clear `__timestamp`
or `__clause_maps`.

---

## fn:get_rule_trace

**anchor:** `pyreason.py:1658` (hint correct).

**contract:** Returns the node and edge rule-trace as two pandas DataFrames rather than writing
them to disk.

**input classes:**
- happy: same construction as `save_rule_trace`, returns `(node_df, edge_df)` (`pyreason.py:1668-1669`).
- store-off-assert: `store_interpretation_changes=False` fails `assert` first (`pyreason.py:1666`).
- atom-trace-columns: same `atom_trace` on/off column-shape split as `save_rule_trace` (`output.py:24-47`, `62-84`).
- empty-trace: an interpretation whose `rule_trace_node`/`rule_trace_edge` is empty yields DataFrames with the fixed 10-column header and no rows (`output.py:13`, `50`).

**notes:** Shares the `Output`/`__timestamp`/`__clause_maps` global dependency with
`save_rule_trace`. Column headers are fixed at
`['Time','Fixed-Point-Operation','Node|Edge','Label','Old Bound','New Bound','Occurred Due To','Consistent','Triggered By','Inconsistency Message']`
plus optional `Clause-i` (`output.py:13`, `52`).

---

## fn:filter_and_sort_nodes

**anchor:** `pyreason.py:1672` (hint correct).

**contract:** Returns a per-timestep list of pandas DataFrames of node bounds, keeping only the
latest change per (component,label), filtered to `labels`/`bound` and sorted by `sort_by`.

**input classes:**
- happy: labels present in the trace, default `bound=interval.closed(0,1)` (no-op filter), `sort_by='lower'`, `descending=True` (`pyreason.py:1683-1684`, `filter.py:8`).
- store-off-assert: `store_interpretation_changes=False` fails `assert` before filtering — a named interaction: a run made with tracing off produces an interpretation this function cannot consume (`pyreason.py:1682`).
- bound-filter: a narrower `bound` drops rows where `bnd in bound` is false; `in` uses `Interval.__contains__` (lower>=, upper<=) (`filter.py:46`, `interval.py:86-90`).
- sort-lower / sort-upper: `sort_by='lower'` keys on `x[0].lower`, `'upper'` on `x[0].upper`; any other string leaves the list unsorted (no else branch) (`filter.py:34-37`).
- descending-toggle: `descending=False` flips `reverse` to ascending (`filter.py:33`).
- label-not-present: a label in `labels` that never appears still becomes a column, defaulted to `[0,1]` for rows that exist for other labels (`filter.py:48`).
- empty-timestep: timesteps with no matching component yield an empty DataFrame carrying only `['component', *labels]` columns (`filter.py:57-58`).
- multi-label: multiple labels widen every component row to one column per label, defaulting missing entries to `[0,1]` (`filter.py:48-49`).

**notes:** The frame count is `interpretation.time + 1` — one DataFrame per timestep `0..tmax`
(`filter.py:5`, `15`, `52`). It reads `interpretation.rule_trace_node`; if
`store_interpretation_changes` was off during `reason`, that list is empty even though the assert
guards the call. "Latest change wins" is order-sensitive: it relies on `rule_trace_node` being
appended in chronological order so later entries overwrite earlier ones per `(comp,label)`
(`filter.py:22-24`). hypothesis(corpus-filter) — treat any corpus bug on filter column defaulting
as unverified.

---

## fn:filter_and_sort_edges

**anchor:** `pyreason.py:1688` (hint correct).

**contract:** Edge counterpart of `filter_and_sort_nodes`; returns a per-timestep list of
DataFrames of edge bounds with a `component` column built from the (source,target) pair.

**input classes:**
- happy / store-off-assert / bound-filter / sort-lower / sort-upper / descending-toggle / label-not-present / empty-timestep / multi-label: identical structure to `filter_and_sort_nodes` but reading `interpretation.rule_trace_edge` (`pyreason.py:1698-1700`, `filter.py:62-117`).
- edge-component-shape: non-empty frames get columns `['source','target',*labels]`, then `source`/`target` are collapsed into a single tuple `component` column and dropped (`filter.py:110-113`); empty frames get only `['component', *labels]` (`filter.py:115`) — a distinct column-shape divergence from the node version worth a differential assertion.

**notes:** Same `interpretation.time + 1` frame count and chronological-append dependence as the
node version. The component-tuple reconstruction (`apply(tuple, axis=1)`) is an extra transform
absent from the node path.

---

## fn:reset

**anchor:** `pyreason.py:487` (hint correct).

**contract:** Clears facts, closed-world predicates, the loaded graph, and rules from module state
(and from `__program` if one exists) so `reason()` can be run again without memory growth.

**input classes:**
- no-program: `__program is None` clears only the module globals (facts, name set, closed-world set, graph) and cascades into `reset_rules` (`pyreason.py:494-507`).
- with-program: `__program is not None` additionally calls `__program.reset_facts()` and `__program.reset_graph()`, the latter nulling `self.interp` (`pyreason.py:498-504`, `program.py:62-64`, `69-71`).

**notes:** `reset()` does NOT clear `settings`, `__timestamp`, `__clause_maps`, `__ipl`,
`__closed_world_predicates` is reassigned to a fresh `set()` (`pyreason.py:497`), and
`__facts_name_set` is `.clear()`-ed in place (`pyreason.py:496`). Because it cascades into
`reset_rules`, a `reason(again=True)` immediately after `reset()` hits the `_reason_again` assert
path only if `__program` was already `None`; otherwise `__program` still exists but its graph and
rules are gone (`program.reset_graph` sets `interp=None`), so a resumed run is left in a
half-cleared state — a load-bearing ordering interaction.

---

## fn:reset_rules

**anchor:** `pyreason.py:517` (hint correct).

**contract:** Nulls the rules, annotation functions, head functions, and rule-name set (and the
program's rules) so a new ruleset can be added.

**input classes:**
- no-program: sets `__rules=None`, clears `__rules_name_set`, empties `__annotation_functions`/`__head_functions` (`pyreason.py:522-525`).
- with-program: also calls `__program.reset_rules()` setting `self._rules=None` (`pyreason.py:526-527`, `program.py:66-67`).

**notes:** After this, `reason()` raises `'There are no rules'` unless rules are re-added
(`pyreason.py:1549-1550`). It does not touch facts, graph, or settings.

---

## fn:reset_settings

**anchor:** `pyreason.py:561` (hint correct).

**contract:** Restores every field of the `settings` singleton to its constructor default.

**input classes:**
- always: delegates to `settings.reset()`, resetting all 18 knobs to defaults — notably `verbose=True`, `store_interpretation_changes=True`, `atom_trace=False`, `persistent=False`, `inconsistency_check=True`, `update_mode='intersection'`, `parallel_computing=False`, `fp_version=False` (`pyreason.py:565`, `pyreason.py:65-83`).

**notes:** Independent of graph/rules/program state; touches only the settings object. Resetting
here does not re-enable a trace already suppressed inside a completed `reason()` run.

---

## fn:get_rules

**anchor:** `pyreason.py:510` (hint correct).

**contract:** Returns the current `__rules` global (a numba typed list, or `None`).

**input classes:**
- loaded: rules added via `add_rule`/`add_rules_from_file` returns the typed list (`pyreason.py:514`).
- none: after `reset`/`reset_rules` or before any add returns `None`.
- post-reason-filtered: after a `reason(queries=...)` run, returns the query-filtered / clause-reordered `__rules`, not the originally added set (`pyreason.py:1595`, `1603-1606`).

**notes:** Returns the live global reference, not a copy — callers can observe in-place mutation by
`reason`.

---

## fn:get_logic_program

**anchor:** `pyreason.py:529` (hint correct).

**contract:** Returns the `__program` global (`Program` or `None`).

**input classes:**
- before-reason: `None` until the first `reason()` builds a `Program` (`pyreason.py:535`, `1609`).
- after-reason: the constructed program object.
- after-reset: still returns whatever `__program` holds — `reset()` does NOT null `__program` (only clears its facts/graph/rules), so this can return a program whose interpretation is `None`.

**notes:** `reset()`/`reset_rules`/`reset_settings` never reassign `__program` to `None`; only a
fresh `_reason` rebuilds it. Distinguish "no program" from "program with cleared interpretation".

---

## fn:get_interpretation

**anchor:** `pyreason.py:538` (hint correct).

**contract:** Returns the current interpretation (`__program.interp`), raising if no program exists.

**input classes:**
- happy: `__program` set returns `__program.interp` (`pyreason.py:546`).
- no-program: `__program is None` raises `Exception('No interpretation found. Please run pr.reason() first')` (`pyreason.py:544-545`).
- program-with-null-interp: after `reset()` cascaded `__program.reset_graph()` set `interp=None`, this returns `None` without raising (the guard only checks `__program`, not `interp`) — a distinct class from the raise path (`program.py:64`).

**notes:** The raise vs. return-`None` distinction hinges on whether `reset()` ran with a live
program. Returns the live interpretation reference.

---

## fn:get_time

**anchor:** `pyreason.py:549` (hint correct).

**contract:** Returns the current reasoning time as `interpretation.time + 1`, or `0` when no
interpretation is available.

**input classes:**
- happy: interpretation present returns `i.time + 1` (`pyreason.py:557-558`).
- no-interpretation: `get_interpretation()` raising is caught and `0` is returned (`pyreason.py:554-557`).
- null-interp-attribute: if `__program` exists but `interp is None` (post-`reset`), `i.time` raises `AttributeError` which is NOT caught (only `Exception` from the missing-program guard is), so this path errors rather than returning `0` — hypothesis(reset-null-interp-gettime): worth a differential case. (`pyreason.py:554-558`; note the `try` wraps only `get_interpretation`, but attribute access on `None` happens after the `try` at line 558.)

**notes:** The `+1` mirrors the loop's post-increment convention (see fn:reason notes); `get_time`
after a converged run returns `tmax_reached + 1`-style values consistent with the returned frame
count in the filter functions.

---

## type:Query

**anchor:** `query.py:4` (class `Query`); `__init__` at `query.py:5`.

**contract:** Parses a query string of form `pred(node)`, `pred(edge)`, or `pred(x) : [l,u]` into
predicate, component, component-type, and bound, for post-hoc analysis or ruleset filtering.

**input classes:**
- node-default-bound: `pred(x)` with no `:` sets bound `[1,1]` (`query_parser.py:18-19`).
- negated: leading `~` (no bounds) sets bound `[0,0]` (`query_parser.py:14-16`).
- explicit-bounds: `pred(x):[l,u]` parses floats `l,u` via `split(':')` then `split(',')` (`query_parser.py:8-12`).
- edge-vs-node: a comma inside the parentheses makes `comp_type='edge'` and a tuple component; no comma makes `'node'` (`query_parser.py:28-32`).
- whitespace: all spaces are stripped first, so `pred( x ) : [0, 1]` parses identically (`query_parser.py:6`).
- malformed-no-paren: absence of `(` makes `find('(')` return `-1`, so `pred = Label(pred_comp[:-1])` and `component = pred_comp[0:]` — silent misparse, not an error (`query_parser.py:24-26`).
- malformed-negated-with-bounds: `~pred(x):[l,u]` takes the `:` branch and the `~` is never stripped, leaving it in the predicate name (`query_parser.py:8-12`, `14` only reached when no `:`) — a corner the two branches do not reconcile.
- malformed-bad-float: non-numeric bounds raise `ValueError` from `float()` (`query_parser.py:12`).

**notes:** Bounds are built via `interval.closed(lower, upper)` so they inherit the closed-interval
semantics below. Accessors `get_predicate/get_component/get_component_type/get_bounds` expose the
four parsed fields; `__str__`/`__repr__` echo the raw `query_text` (`query.py:20-36`). The `~`
handling and the `:` handling are mutually exclusive branches — combining them is unspecified.

---

## type:Interval

**anchor:** proxy class `interval.py:6` (`Interval`); numba type + `closed()` at
`interval_type.py:13`, constructor `closed` at `interval_type.py:143-145`.

**contract:** A closed numeric bound `[l,u]` with a static flag and remembered previous bounds
`(prev_l, prev_u)`; `closed(l,u,static=False)` is the canonical constructor used throughout the
engine.

**input classes:**
- closed-happy: `closed(l,u)` casts to `float64` and seeds `prev_l=l, prev_u=u`, `static=False` (`interval_type.py:143-145`).
- closed-static: `closed(l,u,static=True)` marks the bound non-resettable, which survives non-persistent timestep resets (`interval_type.py:144`; reset skips `is_static()` bounds at `interpretation.py:265`).
- inverted-bounds: `l>u` is NOT validated at construction — accepted as-is; downstream `intersection` is where `lower>upper` gets clamped to `[0,1]` (`interval_type.py:60-62`, `interval.py:66-68`).
- intersection-empty: two disjoint intervals intersect to `[0,1]` (empty-clamp), not to an empty interval (`interval_type.py:57-63`).
- reset-semantics: `reset()` copies current `(l,u)` into `(prev_l,prev_u)` then sets `(l,u)=(0,1)` — the "no information" bound; drives non-persistent timestep clearing (`interval_type.py:74-83`, `interval.py:40-45`).
- has-changed: `has_changed()` compares current vs. prev bounds (`interval_type.py:97-104`) — used by convergence/change counting.
- contains: `x in interval` is `interval.lower<=x.lower and interval.upper>=x.upper` (`interval_type.py:133-140`, `interval.py:86-90`) — the operative filter test in `filter_and_sort_*`.
- equality: `==`/`!=` compare only `(lower,upper)`, ignoring `static` and prev bounds (`interval_type.py:113-131`, `interval.py:74-78`).
- prev-seed-mismatch: the Python proxy `__new__` seeds `prev = (lower,upper)` (`interval.py:7-8`) while njit `intersection` seeds the returned interval's prev from `self.lower/self.upper` (interval_type.py:63 uses `self.prev_lower/self.prev_upper` — divergent from the pure-Python `interval.py:69` which uses `self.lower/self.upper`). hypothesis(interval-prev-divergence): the two `intersection` implementations disagree on what `prev` the result carries — a differential-worthy corner.

**notes:** There are TWO parallel implementations: the numba-jitted `interval_type.py`
(`overload_*`) and the pure-Python `structref` proxy `interval.py`. The engine runs the jitted one;
Python-side calls (e.g. defaults in `filter_and_sort_*` signatures, `query_parser`) use the proxy.
Any rewrite must match BOTH, and note the `intersection` prev-bound divergence above. `closed` casts
inputs to `np.float64`, so integer `0/1` and float `0.0/1.0` bounds are equivalent post-construction.

---

## type:Label

**anchor:** `label_type.py:16` (numba `LabelType`); the user-facing `Label` value class lives at
`scripts/components/label.py` and is imported at `label_type.py:1`.

**contract:** A hashable string-valued predicate name; `LabelType` is its numba native
representation with boxing/unboxing and equality/hash overloads.

**input classes:**
- construct: `Label(str)` typing accepts only `UnicodeType`; a non-string is rejected by the numba typer (returns `None` typer → type error) (`label_type.py:30-35`).
- equality: two labels are `==` iff their `.value` strings match (`label_type.py:67-75`).
- hash: `hash(label)` is `hash(label.value)`, so labels key numba dicts by string identity (`label_type.py:77-81`) — the mechanism behind `predicate_map`/`world` lookups.
- get-value: `get_value()` / attribute `value` expose the underlying string (`label_type.py:49`, `61-65`); the Python side reads `_value` during unbox (`label_type.py:88`).
- boxing-roundtrip: `box`/`unbox` reconstruct `Label(value)` across the Python↔numba boundary; a mismatch between the boxed attr name (`_value` at `label_type.py:88`) and the Python class field is a load-bearing invariant (`label_type.py:86-105`).

**notes:** Equality and hashing ignore everything but the string, so distinct `Label` objects with
the same text are interchangeable as dict keys — the filter functions rely on this when calling
`label.get_value() in labels` (`filter.py:46`). The value class in `components/label.py` (not this
numba wrapper) is what user code instantiates; the wrapper only teaches numba how to carry it.
