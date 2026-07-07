# Settings surface — input equivalence classes for the 18 `settings` knobs

Scope: the module-global `settings = _Settings()` object in the pinned oracle
(`oracle/pyreason/pyreason/pyreason.py`, pin e1a94af3, v3.6.0). Source-read only.
`reset_settings()` (pyreason.py:561-565) calls `settings.reset()` (pyreason.py:65-83),
which restores **all 18** knobs to the defaults below; this holds for every knob and is
not repeated per-section. All 18 setters raise `TypeError` on a wrong-typed assignment and
otherwise write the private field; 17 check `isinstance(value, bool)`, `update_mode` checks
`isinstance(value, str)`. Reasoning-time reads are captured into the `Program` constructor
(pyreason.py:1609) and dispatched inside `Program.reason` (scripts/program/program.py).

Read timing splits the knobs into two groups:
- **load-time** (must be set before `load_graph`/`load_graphml`): `graph_attribute_parsing`,
  `reverse_digraph` (graph-reversal half), `static_graph_facts`.
- **reason-time** (captured when `reason()` runs; may be set any time before it): all others.

---

## setting:verbose

- `anchor`: pyreason.py:86
- `contract`: Controls whether the engine prints progress/filtering/optimization messages and the empty-graph warning; also forwarded to `Program.reason`. Default `True`. Setter (pyreason.py:236) raises `TypeError` if not `bool` (pyreason.py:243).
- `input classes`:
  - default-true-prints: `verbose=True` emits progress/filtering/optimization prints; consumed live at pyreason.py:686, 862, 1074, 1409, 1547, 1592, 1600.
  - nondefault-false-silent: `verbose=False` suppresses those prints, including the empty-graph warning at pyreason.py:1548.
  - forwarded-to-engine: value passed to `Program.reason(..., verbose)` at pyreason.py:1620 / 1640 → program.py `reason(verbose)`.
  - type-reject: non-bool assignment → `TypeError` at pyreason.py:243.
- `notes`: Read live at each `add_*`/`load_*`/`reason` call site, so flipping it between `add_*` and `reason()` only affects prints emitted after the flip. Reasoning results are identical for `True` vs `False`.

## setting:output_to_file

- `anchor`: pyreason.py:94
- `contract`: Redirects `sys.stdout` to a per-run text file during `reason`. Default `False`. Setter (pyreason.py:248) raises `TypeError` if not `bool` (pyreason.py:256).
- `input classes`:
  - default-false-stdout: `output_to_file=False` leaves `sys.stdout` untouched.
  - nondefault-true-redirect: `output_to_file=True` opens `./{output_file_name}_{timestamp}.txt` in append mode and rebinds `sys.stdout` at pyreason.py:1513-1514 and 1541-1542.
  - interaction-filename: file basename comes from `output_file_name`; the memory-profile MB line (pyreason.py:1520/1527) also lands in the file.
  - type-reject: non-bool → `TypeError` at pyreason.py:256.
- `notes`: Read at the top of `reason` and `_reason`. `sys.stdout` is reassigned but never restored, so a redirect persists across subsequent calls in the process until `reset_settings()`/manual restore.

## setting:output_file_name

- `anchor`: pyreason.py:102
- `contract`: Basename for the redirect file; only meaningful when `output_to_file` is `True`. Default `'pyreason_output'`. Setter (pyreason.py:261) raises `TypeError` if not `str` (pyreason.py:268).
- `input classes`:
  - default-name: `'pyreason_output'` → file `./pyreason_output_{timestamp}.txt`.
  - nondefault-name: any other string changes the basename in the f-string at pyreason.py:1514 / 1542.
  - inert-when-output-false: value never read unless `output_to_file` is `True`.
  - type-reject: non-str → `TypeError` at pyreason.py:268.
- `notes`: Consumed only inside the two f-strings during `reason`/`_reason`. No path/extension validation; the string is interpolated verbatim.

## setting:graph_attribute_parsing

- `anchor`: pyreason.py:110
- `contract`: Gates whether a loaded graphml is parsed for node/edge attribute facts. Default `True`. Setter (pyreason.py:273) raises `TypeError` if not `bool` (pyreason.py:282).
- `input classes`:
  - default-true-parse: `True` → `parse_graph_attributes` runs, producing non-fluent graph facts and specific graph labels (pyreason.py:580-581, 602-603).
  - nondefault-false-skip: `False` → attribute parse skipped; the non-fluent fact/label lists retain their prior/empty state.
  - read-at-load-time: consumed only in `load_graphml`/`load_graph`; changing it after the graph is loaded has no effect (must be set before `load_graph`).
  - interaction-static: when true, forwards `settings.static_graph_facts` into `parse_graph_attributes(static_facts)`.
  - type-reject: non-bool → `TypeError` at pyreason.py:282.
- `notes`: Load-time knob. Feeds grounding indirectly by seeding the graph-attribute facts the interpretation later applies.

## setting:abort_on_inconsistency

- `anchor`: pyreason.py:118
- `contract`: Documented as "abort the program when an inconsistency is found." Default `False`. Setter (pyreason.py:285) raises `TypeError` if not `bool` (pyreason.py:294).
- `input classes`:
  - dead-knob: no consumption site exists anywhere in `scripts/` or `pyreason.py` beyond the getter/setter; a full-tree grep finds the name only inside `_Settings`. `True` vs `False` yields byte-identical reasoning. hypothesis(dead-knob): inconsistency behavior is actually governed by `inconsistency_check`, not this knob.
  - type-reject: non-bool → `TypeError` at pyreason.py:294.
- `notes`: Orphan setting — read nowhere in the engine. Differential proof should confirm it is inert; the effective inconsistency control is `setting:inconsistency_check`.

## setting:memory_profile

- `anchor`: pyreason.py:126
- `contract`: Wraps the reasoning call in `memory_profiler.memory_usage` and prints peak MB. Default `False`. Setter (pyreason.py:297) raises `TypeError` if not `bool` (pyreason.py:306).
- `input classes`:
  - default-false-direct: `False` → `_reason`/`_reason_again` invoked directly (pyreason.py:1522 / 1529).
  - nondefault-true-profiled: `True` → call wrapped in `mp.memory_usage(..., max_usage=True, retval=True)` and MB printed (pyreason.py:1517-1520, 1524-1527).
  - interaction-output: the MB print is subject to the `output_to_file` redirect.
  - type-reject: non-bool → `TypeError` at pyreason.py:306.
- `notes`: Read at the top of the public `reason` dispatch. Purely observational — does not change the returned interpretation.

## setting:reverse_digraph

- `anchor`: pyreason.py:134
- `contract`: Reverses every graph edge (a→b becomes b→a) at parse time, and is also forwarded to the interpretation as `reverse_graph`. Default `False`. Setter (pyreason.py:309) raises `TypeError` if not `bool` (pyreason.py:319).
- `input classes`:
  - default-false-asis: `False` → edges kept as loaded.
  - nondefault-true-reversed: `True` → graph reversed in graphml_parser.py:18-19 (`self.graph.reverse()`) via `parse_graph(path, settings.reverse_digraph)` at pyreason.py:577.
  - forwarded-to-engine: same value passed to `Program` as `reverse_graph` (pyreason.py:1609) → stored at interpretation.py:69 and threaded into the kernel `reason` call (interpretation.py:232/:242, mirrored in the fp and parallel kernels), but never consumed in any kernel body — a dead snapshot with no behavioral observable (session 9, grep-verified at the pin).
  - read-at-load-time: the actual reversal happens during `load_graphml` (`load_graph` never reads the knob: pyreason.py:589-599); set before loading.
  - type-reject: non-bool → `TypeError` at pyreason.py:319.
- `notes`: Split read — graph structure is reversed once at load (graphml path only), and the flag is also snapshotted into the `Program` at reason time. Setting it after loading reverses nothing but still flips the engine-side flag, which is itself inert at the pin (see forwarded-to-engine). An earlier revision of this section said the engine copy "is re-read at reason time" — refuted session 9: it is passed, never read.

## setting:atom_trace

- `anchor`: pyreason.py:143
- `contract`: Records the ground atoms responsible for each rule firing (provenance). Default `False`. Setter (pyreason.py:322) raises `TypeError` if not `bool` (pyreason.py:332).
- `input classes`:
  - default-false-notrace: `False` → no atom provenance stored; trace slots written as `''` (interpretation.py:298, 374).
  - nondefault-true-trace: `True` → firing atoms recorded throughout interpretation.py (206, 300, 342, 353, 376, ...); passed via `Program` at pyreason.py:1609.
  - forced-off-by-store: if `store_interpretation_changes` is `False`, `atom_trace` is mutated to `False` at reason time (pyreason.py:1584-1585) — a live mutation of the settings object.
  - interaction-rule-trace: `save_rule_trace`/`get_rule_trace` explainability is only meaningful with `atom_trace=True`.
  - type-reject: non-bool → `TypeError` at pyreason.py:332.
- `notes`: Reason-time knob captured into `Program`. Note the engine writes back to `settings.atom_trace` at pyreason.py:1585; `reset_settings()` restores the default afterward.

## setting:save_graph_attributes_to_trace

- `anchor`: pyreason.py:152
- `contract`: Whether graph-attribute facts are written into the rule trace (large graphs → large traces). Default `False`. Setter (pyreason.py:335) raises `TypeError` if not `bool` (pyreason.py:345).
- `input classes`:
  - default-false-exclude: `False` → graph-attribute facts excluded; the guard `(save_graph_attributes_to_rule_trace or not graph_attribute) and store_interpretation_changes` at interpretation.py:297 / 373 skips them.
  - nondefault-true-include: `True` → graph-attribute facts recorded into the trace (larger trace/memory).
  - interaction-store: trace writes gated by `store_interpretation_changes` in the same conjunction (interpretation.py:297, 373).
  - type-reject: non-bool → `TypeError` at pyreason.py:345.
- `notes`: Passed to `Program` as `save_graph_attributes_to_rule_trace` (pyreason.py:1609 → interpretation.py:71). Reason-time; affects trace contents only, not derived bounds.

## setting:canonical

- `anchor`: pyreason.py:161
- `contract`: **Deprecated alias of `persistent`.** The getter returns `self.__persistent` (pyreason.py:167) and the setter writes `self.__persistent` (pyreason.py:357) — there is no independent `__canonical` field. Default `False`. Setter (pyreason.py:348) raises `TypeError` if not `bool` (pyreason.py:355).
- `input classes`:
  - alias-of-persistent: reading `canonical` returns the `persistent` value; assigning `canonical` sets `persistent`. Any differential effect is exactly `persistent`'s (see that section).
  - last-write-wins: `canonical` and `persistent` share one field, so whichever is set last governs.
  - naming-mismatch: the value flows to `Program` under the parameter name `canonical` (pyreason.py:1609, program.py `__init__`), but interpretation.py:72 stores it as `persistent` — the `canonical` name survives only in the `Program` layer.
  - type-reject: non-bool → `TypeError` at pyreason.py:355.
- `notes`: No standalone state; a differential harness cannot distinguish `canonical` from `persistent`. Treat as one knob for correctness.

## setting:persistent

- `anchor`: pyreason.py:170
- `contract`: When `True`, bounds are not reset each timestep (persistent interpretation); when `False`, non-static bounds reset every timestep. Default `False`. Setter (pyreason.py:360) raises `TypeError` if not `bool` (pyreason.py:366).
- `input classes`:
  - default-false-nonpersistent: `False` → `if t>0 and not persistent:` reset loop runs each timestep (interpretation.py:260), clearing non-static bounds.
  - nondefault-true-persistent: `True` → reset loop skipped; bounds carry across timesteps.
  - interaction-static: static bounds are never reset even in non-persistent mode. hypothesis(BUG-173): `persistent`×`static` semantics undocumented/ambiguous.
  - interaction-canonical: shares the `__persistent` field with `canonical`.
  - type-reject: non-bool → `TypeError` at pyreason.py:366.
- `notes`: Passed to `Program` as `canonical` (pyreason.py:1609) → interpretation.py:72; drives the per-timestep reset at interpretation.py:259-260. Reason-time knob.

## setting:inconsistency_check

- `anchor`: pyreason.py:178
- `contract`: Whether the engine resolves inconsistencies (via `resolve_inconsistency_*`) rather than force-overriding bounds. Default `True`. Setter (pyreason.py:372) raises `TypeError` if not `bool` (pyreason.py:381).
- `input classes`:
  - default-true-resolve: `True` → on conflict, `resolve_inconsistency_node`/`_edge` runs (interpretation.py:328-329, 403-404, 457-458, 504-505).
  - nondefault-false-override: `False` → conflicting updates forced through `_update_*(..., override=True)` (interpretation.py:331, 406, 460, 507). hypothesis(BUG-176): consistent and override paths are near-duplicate.
  - type-reject: non-bool → `TypeError` at pyreason.py:381.
- `notes`: Passed to `Program` (pyreason.py:1609) → interpretation.py:73. This is the true inconsistency governor (contrast the dead `abort_on_inconsistency`). Reason-time knob.

## setting:static_graph_facts

- `anchor`: pyreason.py:186
- `contract`: Whether graph-attribute facts are created as static (never reset). Default `True`. Setter (pyreason.py:384) raises `TypeError` if not `bool` (pyreason.py:393).
- `input classes`:
  - default-true-static: `True` → graph-attribute facts built with `static=True` (graphml_parser.py:60, 90) via `parse_graph_attributes(settings.static_graph_facts)` at pyreason.py:581 / 603.
  - nondefault-false-fluent: `False` → graph-attribute facts non-static, subject to per-timestep reset.
  - read-at-load-time: consumed only during attribute parsing; requires `graph_attribute_parsing=True` and must be set before `load_graph`.
  - interaction-persistent: static facts escape the non-persistent reset loop (interpretation.py:260 static guard) — hypothesis(BUG-173).
  - type-reject: non-bool → `TypeError` at pyreason.py:393.
- `notes`: Load-time knob; influences later reasoning only through the static flag stamped on the generated facts.

## setting:store_interpretation_changes

- `anchor`: pyreason.py:194
- `contract`: Whether the engine records interpretation changes / rule-trace rows (needed to view results after reasoning). Default `True`. Setter (pyreason.py:395) raises `TypeError` if not `bool` (pyreason.py:406).
- `input classes`:
  - default-true-store: `True` → change/trace recording enabled (interpretation.py:297, 373 conjunction; passed at pyreason.py:1609).
  - nondefault-false-nostore: `False` → no recording; the post-run assertions in `save_rule_trace` (pyreason.py:1652), `get_rule_trace` (1666), and the filter/sort helpers (1682, 1698) fail with an AssertionError.
  - interaction-atom-trace: `False` forces `settings.atom_trace = False` at pyreason.py:1584-1585.
  - type-reject: non-bool → `TypeError` at pyreason.py:406.
- `notes`: Passed to `Program` (pyreason.py:1609) → interpretation.py:74. Reason-time; also mutates `atom_trace` as a side effect at reason start.

## setting:parallel_computing

- `anchor`: pyreason.py:203
- `contract`: Selects the multi-core interpretation class (disables numba caching, forces recompile). Default `False`. Setter (pyreason.py:409) raises `TypeError` if not `bool` (pyreason.py:419).
- `input classes`:
  - default-false-standard: `False` → standard cached `Interpretation` selected (program.py `else` branch).
  - nondefault-true-parallel: `True` → `InterpretationParallel` selected in `Program.reason` (program.py `if self._parallel_computing`).
  - interaction-fp-precedence: with both `parallel_computing=True` and `fp_version=True`, parallel wins — the `elif self._fp_version` branch is unreachable (program.py branch order); `fp_version` is silently ignored.
  - type-reject: non-bool → `TypeError` at pyreason.py:419.
- `notes`: Passed to `Program` (pyreason.py:1609) and dispatched inside `Program.reason` (program.py). Reason-time engine-selection knob.

## setting:update_mode

- `anchor`: pyreason.py:212
- `contract`: How interpretation bounds are combined: `'intersection'` or `'override'`. Default `'intersection'`. Setter (pyreason.py:422) raises `TypeError` only if not `str` (pyreason.py:430) — **no value-domain check**.
- `input classes`:
  - default-intersection: `'intersection'` → `override = False`, bounds intersected (interpretation.py:316, 391, 446, 493, 520).
  - nondefault-override: `'override'` → `override = True`, bounds replaced.
  - unvalidated-string: any other string (`'Override'`, `'foo'`, `''`) passes the setter and behaves as intersection, since only `== 'override'` triggers override. hypothesis(silent-fallthrough): no domain validation on the accepted string.
  - type-reject: non-str → `TypeError` at pyreason.py:430.
- `notes`: Passed to `Program` (pyreason.py:1609) → interpretation.py:75; converted to the boolean `override` at each update site. Reason-time knob.

## setting:allow_ground_rules

- `anchor`: pyreason.py:220
- `contract`: Whether rules may contain ground atoms treated as singleton groundings. Default `False`. Setter (pyreason.py:435) raises `TypeError` if not `bool` (pyreason.py:444).
- `input classes`:
  - default-false-nonground: `False` → ground-atom clauses fall through to the `elif`/general grounding path (interpretation.py:892, 938-style branches).
  - nondefault-true-ground: `True` → ground atoms accepted as their own groundings (interpretation.py:861, 888, 968 first branches).
  - redundant-branch: for a head var already in nodes, both `True` and `False` can produce identical `groundings[head_var] = [head_var]`. hypothesis: the `allow_ground_rules`-gated branch is redundant in that scenario.
  - type-reject: non-bool → `TypeError` at pyreason.py:444.
- `notes`: Passed to `Program` (pyreason.py:1609) → interpretation.py:76 → `_ground_rule` (interpretation.py:810). Reason-time; affects grounding/graph-augmentation behavior.

## setting:fp_version

- `anchor`: pyreason.py:228
- `contract`: Selects the fixed-point interpretation class instead of the optimized one. Default `False`. Setter (pyreason.py:447) raises `TypeError` if not `bool` (pyreason.py:456).
- `input classes`:
  - default-false-optimized: `False` → standard optimized `Interpretation` (program.py `else`).
  - nondefault-true-fp: `True` (and `parallel_computing=False`) → `InterpretationFP` selected (program.py `elif self._fp_version`).
  - interaction-parallel-precedence: `parallel_computing=True` masks `fp_version` entirely (parallel branch checked first).
  - type-reject: non-bool → `TypeError` at pyreason.py:456.
- `notes`: Passed to `Program` (pyreason.py:1609) and dispatched inside `Program.reason` (program.py). Reason-time engine-selection knob; only reachable when `parallel_computing` is `False`.
