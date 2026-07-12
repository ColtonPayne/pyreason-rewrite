<!-- doccode: pyreason-rewrite-docs-surface -->
# The equivalence target set — AC-1 surface inventory

The countable definition of "all pyreason-API features" for the campaign: one row per
surface item at pin `e1a94af3` (v3.6.0). 52 rows across three kinds — 26 public
module-level functions, 6 public types plus their 2 text DSLs as their own rows, and 18
`settings` knobs. The fast-tier gate (`tests/test_surface_inventory.py`) AST-scans the
pinned API module per row kind and reds on any omitted or phantom row; nothing
off-inventory counts toward an equivalence claim.

**Scope note (operator-set, 2026-07-06):** the torch-gated model-integration surface
(`LogicIntegratedClassifier`, `ModelInterfaceOptions`) is out of campaign scope — torch is
never installed and no equivalence claim covers those two names. They are named here so
the exclusion is visible, not silent.

Row fields (the seam contract): `oracle anchor` (file:line at the pin) · `status` ∈
{uncovered, cased, equivalent, divergent-queued, adjudicated} · `cases` (covering harness
case ids) · `input classes` (the enumerated equivalence classes the item must be proven
over; ids only — each id's full description, source citation, and hypotheses live in the
row's `analysis` file under [docs/analysis/surface/](analysis/surface/)) · `notes`.
Coverage is a measured fraction: rows at equivalent-or-adjudicated over 52, and input
classes likewise.

---

## fn:load_graphml
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:569
- status: equivalent
- cases: reverse-digraph-default, reverse-digraph-on, load-graphml-basic, load-graphml-no-attr-parse, graphml-attr-coercions, graphml-empty, perf-ladder-small, perf-ladder-medium, perf-ladder-large
- input classes:
  - happy-basic
  - happy-no-attr-parse
  - interacts-reverse_digraph
  - interacts-static_graph_facts
  - bound-empty-graph
  - bound-attr-numeric-in-range
  - bound-attr-zero-one-edges
  - bound-attr-comma-pair
  - malformed-attr-comma-float
  - malformed-attr-out-of-range
  - malformed-attr-nonnumeric
  - malformed-missing-file
  - malformed-bad-graphml
- notes: mutates five module globals; grounding tables survive reset(); attribute-bound coercions are the hazard cluster — all silent at the pin (session 9: no malformed attribute value raises; values 0 and '0,1' coerce to the vacuous [0,1] and leave no observable row). Uncovered classes: interacts-static_graph_facts (stamping in effect in every happy case here; the interaction itself is proven over load_graph by the static-graph-facts pair), malformed-missing-file and malformed-bad-graphml (the capture's graphml_path input existence-checks fixtures, and a loader raise during input application would fail the capture — the apply_input raising-probe form exists as of session 13, but load_graphml is deliberately not yet an apply op: no committed case consumes it, and the op rides the case that does)
- analysis: docs/analysis/surface/facts-and-graph.md

## fn:load_graph
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:589
- status: equivalent
- cases: hello-world, conv-perfect, conv-delta-interp, conv-delta-bound, persistent-off, persistent-on, inconsistency-ipl-resolve, inconsistency-ipl-override, reason-again-restart-true, reason-again-restart-false, reason-again-no-program, reason-bare-again-no-facts, reset-with-program, reset-no-program, reset-rules-with-program, reset-rules-no-program, reset-settings-restore, edge-rule-frames, store-off-accessors, store-off-atom-trace-flip, fp-version-on, update-mode-default, update-mode-override, update-mode-junk-string, allow-ground-rules-on, allow-ground-rules-off, graph-attr-parsing-on, graph-attr-parsing-off, static-graph-facts-on, static-graph-facts-off, save-graph-attrs-to-trace-on, save-graph-attrs-to-trace-off, canonical-on, canonical-last-write, abort-on-inconsistency-default, abort-on-inconsistency-on, memory-profile-default, memory-profile-on, output-to-file-default, output-to-file-on, output-file-name-custom, output-file-name-inert, parallel-computing-default, parallel-computing-on, parallel-fp-precedence
- input classes:
  - happy-digraph
  - happy-no-attr-parse
  - interacts-static_graph_facts
  - bound-undirected-input
  - bound-empty-graph
  - bound-attr-numeric-in-range
  - bound-attr-comma-pair
  - malformed-attr-out-of-range
  - malformed-attr-nonnumeric
  - divergence-no-reverse
- notes: unlike load_graphml it never consults reverse_digraph — a load-path-dependent knob asymmetry
- analysis: docs/analysis/surface/facts-and-graph.md

## fn:load_inconsistent_predicate_list
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:611
- status: equivalent
- cases: ipl-load-basic, ipl-load-null-overwrite, ipl-load-malformed, ipl-atom-trace-off-trace
- input classes:
  - happy-basic
  - bound-ipl-null
  - bound-ipl-empty-list
  - malformed-missing-ipl-key
  - malformed-short-pair
  - malformed-missing-file
  - malformed-bad-yaml
- notes: overwrites __ipl wholesale — pinned semantically by ipl-load-null-overwrite (add_inconsistent_predicate first, then a null-'ipl:' yaml → zero complement rows in the trace); the happy pair's effect observed through reason() complement rows ('IPL: popular', Triggered By 'IPL'), not a stored value. The four malformed arms are four distinct exception types (parse_ipl validates nothing itself, yaml_parser.py:187-196): FileNotFoundError / KeyError "'ipl'" / IndexError / yaml.parser.ParserError — the yaml error's message embeds the repo-resolved fixture path, identical for both engines run from this repo, so it compares exactly. Uncovered: bound-ipl-empty-list (an explicit `ipl: []` — same empty-list outcome as null via a different branch: null fails the `is not None` guard while `[]` passes it and iterates zero times, yaml_parser.py:191-194; not cased, but review-probed cross-engine 2026-07-07: slice-8 review's rv-ipl-empty-list-overwrite PASS, zero complement rows) and the IPL-survives-reset() interaction (unpinned by any committed case). Slice-8 review probes additionally banked cross-engine (uncommitted, report-recorded): four plain-Python shape arms (empty file → TypeError NoneType-subscript; top-level list → TypeError list-indices; scalar 'ipl:' → TypeError not-iterable; string 'ipl:' → IndexError 'string index out of range'), duplicate pairs (both engines double the complement rows), and inconsistency_check=False (complement emission unaffected, trace identical to ipl-load-basic in both engines). **DIV-0002 (adjudicated 2026-07-11, session 25, batch item A2)**: NON-STRING pair entries (`ipl: [[1, 2]]`) — the pin raises builtins.ValueError from the typed-list unbox with an ADDRESS-DERIVED message (same-engine unstable: 4 fresh pin processes, 4 distinct texts, so the arm is un-bankable — the harness scores it irreproducible on the pin itself); the rewrite, per the operator's option (a), raises the same ValueError type at the same append seam with the stable, honest message 'IPL entries must be strings; got int: 1' (the ipl_pair guard, shared with add_inconsistent_predicate whose pinned twin fails the identical unbox). docs/divergences/DIV-0002.md; pin-side reproducer tests/test_div_0002_reproducer.py (e2e), rewrite-side seam tests in tests/test_rewrite_state_loaders.py
- analysis: docs/analysis/surface/facts-and-graph.md

## fn:add_inconsistent_predicate
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:620
- status: equivalent
- cases: inconsistency-ipl-resolve, inconsistency-ipl-override, abort-on-inconsistency-default, abort-on-inconsistency-on
- input classes:
  - happy-basic
  - interacts-additive-after-yaml
  - bound-same-predicate
  - bound-duplicate-pair
  - malformed-empty-string
  - malformed-non-str
- notes: additive, no dedup or name-content validation at this boundary. **DIV-0002 guard parity (adjudicated 2026-07-11, session 25, batch item A2)**: non-string predicates raise the stable ValueError at the append — the shared ipl_pair guard, src/pyreason/_state.py; the pinned twin's typed-list append (pyreason.py:629) fails the identical unbox — and a first failed add leaves the IPL created-but-empty, matching the pin binding the empty typed list before the failing append; seam test tests/test_rewrite_state_loaders.py::test_add_inconsistent_predicate_nonstring_raises_the_same_guard
- analysis: docs/analysis/surface/facts-and-graph.md

## fn:add_closed_world_predicate
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:1122
- status: equivalent
- cases: closed-world-on, closed-world-off
- input classes:
  - happy-basic
  - bound-duplicate
  - bound-empty-string
  - malformed-non-str
  - interacts-unknown-predicate
  - interacts-reset
- notes: effect deferred to reason() — pinned differentially by the on/off twins: with 'busy' closed-world, a busy(x):[0,0] clause over Friends-grounded x fires for the never-stated nodes (is_satisfied_node's CWA branch treats a missing/unknown [0,1] label as [0,0], interpretation.py:1763-1770) while the known-[1,1] node still fails it; off, no available row ever derives. Grounding scope (review-corrected 2026-07-07): the prior-clause grounding shape is needed only because a fact states the predicate — get_rule_node_clause_grounding (interpretation.py:1396-1402) draws a map-known predicate's candidates from the predicate map, hiding never-stated nodes from a single-clause rule; with the predicate wholly unstated the fallback grounding is ALL nodes and a single-clause [0,0] rule fires for every node (screened live 2026-07-07, not cased). Duplicate add is a set no-op (pinned: the on twin applies it twice). Uncovered: bound-empty-string (screened 2026-07-07: adds and reasons without effect on a program whose rules never name an empty predicate — not cased), malformed-non-str (screened: the add itself is silent — a bare set.add — and the raise surfaces only at reason() from the numba Label conversion with a run-varying character-code message, unbankable under exact compare; a canonicalization would need its own recorded policy), interacts-reset (cleared by reset() unlike IPL — unpinned), interacts-unknown-predicate (the all-nodes grounding screen above is its ready-made case shape)
- analysis: docs/analysis/surface/facts-and-graph.md

## fn:add_fact
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:1133
- status: equivalent
- cases: hello-world, conv-perfect, conv-delta-interp, conv-delta-bound, persistent-off, persistent-on, inconsistency-ipl-resolve, inconsistency-ipl-override, reason-again-restart-true, reason-again-restart-false, reason-again-no-program, reason-bare-again-no-facts, reset-with-program, reset-no-program, reset-rules-with-program, reset-rules-no-program, reset-settings-restore, edge-rule-frames, store-off-accessors, store-off-atom-trace-flip, fp-version-on, update-mode-default, update-mode-override, update-mode-junk-string, allow-ground-rules-on, allow-ground-rules-off, canonical-on, canonical-last-write, abort-on-inconsistency-default, abort-on-inconsistency-on, memory-profile-default, memory-profile-on, output-to-file-default, output-to-file-on, output-file-name-custom, output-file-name-inert, parallel-computing-default, parallel-computing-on, parallel-fp-precedence, perf-ladder-small, perf-ladder-medium, perf-ladder-large
- input classes:
  - happy-node
  - happy-edge
  - bound-unnamed
  - interacts-duplicate-name
  - bound-lazy-init
  - interacts-name-counter-mixing
  - malformed-static-window
- notes: duplicate names warn but still append; auto-name counter spans node+edge lists (order-sensitive)
- analysis: docs/analysis/surface/facts-and-graph.md

## fn:add_fact_from_json
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:1168
- status: equivalent
- cases: fact-from-json-basic, fact-from-json-malformed
- input classes:
  - happy-basic
  - bound-empty-array
  - bound-defaults
  - malformed-not-array
  - malformed-item-not-object
  - malformed-missing-fact_text
  - malformed-bad-fact_text
  - malformed-nonint-time
  - interacts-static_field
  - interacts-duplicate-name-intrafile
  - malformed-missing-file
  - malformed-bad-json
- notes: loaded state observed through the reason trace (no fact accessor at the pin): given + auto-counter names, windows, bounds, static all pinned there. Malformed arms pin the doubled item prefix on loader-level failures ("Item 0: Failed to parse fact - Item 0: ...") vs the single prefix when the fact parser itself raises ("Item 0: Failed to parse fact - Missing closing parenthesis in fact"); duplicate-name raises at item 1 AFTER item 0 loaded (that partial state has no accessor — named unobserved). The summary print is unconditional at the pin (pyreason.py:1290-1292, differs from the CSV loader's verbose gate) but lands on pre-reason process stdout, which the harness never compares — named unobserved. Uncovered: bound-empty-array, malformed-item-not-object (pinned on the rule loader only; the shared helper makes the fact-side message shape a same-code-path inference, not a banked observation), malformed-nonint-time's end_time half (the "invalid end_time silently defaults to start_time" behavior lives on the raise_errors=False path — no warn-and-skip arm of this loader is cased)
- analysis: docs/analysis/surface/facts-and-graph.md

## fn:add_fact_from_csv
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:1294
- status: equivalent
- cases: fact-from-csv-basic, fact-from-csv-malformed
- input classes:
  - happy-basic
  - happy-header
  - bound-header-mismatch
  - bound-short-rows
  - bound-empty-file
  - malformed-missing-fact_text
  - malformed-bad-fact_text
  - malformed-nonint-time
  - interacts-static_field
  - interacts-quoted-commas
  - interacts-duplicate-name-intrafile
  - malformed-missing-file
- notes: header detection is an exact-match (pinned: the fixture's exact header row loads no fact); every cell read as string with keep_default_na off — short rows are padded by the reader (the two-field row loads with start/end 0, static False), truthy 'yes' coerces static, a quoted comma-bearing edge fact with an interval bound rides one cell, empty name cells auto-name through the shared node+edge counter, and a zero-byte file warns and returns without raising (the no-raise outcome record is the compared observation — nothing else is observable, no fact accessor exists). Malformed arms: missing file (the loader's own 'CSV file not found' FileNotFoundError), plus invalid static cell and missing fact_text — those two doubled-row-prefix ValueErrors. Uncovered: bound-header-mismatch, malformed-bad-fact_text and malformed-nonint-time on this loader (pinned on the JSON fact loader; the shared _parse_and_validate_fact_params makes the CSV-side shape a same-code-path inference, not a banked observation), interacts-duplicate-name-intrafile on this loader, every raise_errors=False warn-and-skip arm
- analysis: docs/analysis/surface/facts-and-graph.md

## fn:add_rule
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:632
- status: equivalent
- cases: hello-world, conv-perfect, conv-delta-interp, conv-delta-bound, persistent-off, persistent-on, inconsistency-ipl-resolve, inconsistency-ipl-override, reason-again-restart-true, reason-again-restart-false, reason-again-no-program, reason-bare-again-no-facts, reset-with-program, reset-no-program, reset-rules-with-program, reset-rules-no-program, reset-settings-restore, edge-rule-frames, store-off-accessors, store-off-atom-trace-flip, fp-version-on, update-mode-default, update-mode-override, update-mode-junk-string, allow-ground-rules-on, allow-ground-rules-off, graph-attr-parsing-on, graph-attr-parsing-off, static-graph-facts-on, static-graph-facts-off, save-graph-attrs-to-trace-on, save-graph-attrs-to-trace-off, canonical-on, canonical-last-write, abort-on-inconsistency-default, abort-on-inconsistency-on, memory-profile-default, memory-profile-on, reverse-digraph-default, reverse-digraph-on, load-graphml-basic, load-graphml-no-attr-parse, graphml-attr-coercions, graphml-empty, output-to-file-default, output-to-file-on, output-file-name-custom, output-file-name-inert, parallel-computing-default, parallel-computing-on, parallel-fp-precedence, perf-ladder-small, perf-ladder-medium, perf-ladder-large
- input classes:
  - happy-basic
  - happy-named
  - bound-unnamed-autoname
  - malformed-duplicate-name
  - interacts-append-order
  - interacts-reset
- notes: no parsing here — all validation lives in the Rule constructor; duplicate names warn-only
- analysis: docs/analysis/surface/rules.md

## fn:add_rules_from_file
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:652
- status: equivalent
- cases: rules-from-file-basic, rules-from-file-malformed
- input classes:
  - happy-multi-rule
  - happy-comments-and-blanks
  - bound-empty-file
  - bound-name-offset
  - malformed-line-raise
  - malformed-line-skip
  - malformed-missing-file
  - interacts-infer_edges
  - interacts-verbose
  - bound-inline-comma
- notes: raise_errors defaults False here (CSV/JSON default True) — both arms pinned on the same bad-middle-line fixture: True raises "Line 2: ..." after loading line 1 (partial load pinned by fingerprint), default warns, skips, and leaves the rule_1/rule_3 name gap (the loader names rule_{i+offset} over the filtered line list even for failed lines, with offset = live rule count — bound-name-offset pinned with one inline rule preloaded); '#' comments only when first char (pinned: the fixture's comment + blank lines load nothing). Missing file raises open()'s bare errno FileNotFoundError (contrast the CSV/JSON loaders' own messages). Uncovered: bound-empty-file, interacts-infer_edges, interacts-verbose, bound-inline-comma
- analysis: docs/analysis/surface/rules.md

## fn:add_rule_from_csv
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:753
- status: equivalent
- cases: rule-from-csv-basic, rule-from-csv-malformed
- input classes:
  - happy-full-row
  - happy-minimal-row
  - happy-header-present
  - malformed-header-mismatch
  - malformed-missing-rule_text
  - malformed-empty-file
  - malformed-missing-file
  - malformed-unreadable
  - bound-bool-truthy-strings
  - malformed-bool-invalid
  - bound-numeric-bool
  - malformed-duplicate-name
  - bound-quoted-commas
  - interacts-verbose
- notes: file-local name dedup never consults the engine-global rule-name set (the dup raise fires at row 2 after row 1 loaded — partial load pinned by fingerprint). Happy arms pinned: exact-match header skip, explicit clause bound, truthy 'yes'/'1' strings coercing infer_edges/set_static, quoted comma-bearing rule_text, empty-name auto-naming through add_rule, and the loaded rules consumed by reason() (the infer_edges rule writes inferred team edges into the edge trace). Failure granularity pinned: a bad row raises row-wise, but an unquoted comma fails pandas' tokenizer wholesale ('Error reading CSV file ...'), loading nothing from that file. Named unobserved: the set_static flag is not rendered by the accessor fingerprint (its surface sits with type:Rule). Uncovered: malformed-header-mismatch, malformed-empty-file, malformed-bool-invalid, bound-numeric-bool, interacts-verbose, every raise_errors=False arm
- analysis: docs/analysis/surface/rules.md

## fn:add_rule_from_json
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:868
- status: equivalent
- cases: rule-from-json-basic, rule-from-json-malformed
- input classes:
  - happy-basic
  - happy-custom-thresholds-list
  - happy-custom-thresholds-dict
  - happy-weights
  - malformed-not-array
  - bound-empty-array
  - malformed-item-not-object
  - malformed-missing-rule_text
  - malformed-threshold-missing-field
  - malformed-threshold-dict-key
  - malformed-threshold-not-object
  - malformed-custom_thresholds-wrong-type
  - malformed-weights-not-list
  - malformed-invalid-json
  - malformed-missing-file
  - malformed-duplicate-name
  - interacts-thresholds-vs-clause-count
- notes: the only loader exposing custom_thresholds and weights — both accepted forms pinned as acceptance + parsed-rule fingerprints (list form, dict form with a string clause-index key parsed to int and unnamed clauses defaulted, and a weights list), but the fingerprint renders neither thresholds nor weights, so their *contents* are unobserved here (they sit with type:Threshold and the annotation-function rows). Malformed arms pinned: the four file/document faults plus two threshold faults — both banked with the same outer wrap as every loader-level ValueError ("Item 0: Failed to parse rule - Item 0, threshold 0: Invalid threshold - 'thresh'" — the KeyError key verbatim — and the non-integer dict key) — all six raising before any add_rule (closing fingerprint None — the rules global never initialized). Doubled item prefix pinned ("Item 0: Failed to parse rule - Item 0: ..."). Uncovered: bound-empty-array, malformed-missing-rule_text, malformed-threshold-not-object, malformed-custom_thresholds-wrong-type, malformed-weights-not-list, malformed-duplicate-name on this loader, interacts-thresholds-vs-clause-count, every raise_errors=False arm
- analysis: docs/analysis/surface/rules.md

## fn:add_annotation_function
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:1415
- status: equivalent
- cases: annotation-fn-two-arg, annotation-fn-six-arg, annotation-fn-unregistered-name, annotation-fn-reset-clears, annotation-fn-return-triple, annotation-fn-return-interval, annotation-fn-duplicate-name
- input classes:
  - happy-2arg
  - happy-6arg
  - malformed-wrong-arity
  - malformed-return-shape
  - bound-njit-wrapped
  - bound-defaulted-or-varargs
  - interacts-reset
  - interacts-reorder_clauses
  - interacts-duplicate-name
- notes: cased through the named-function registry (harness/reference_fns.py — committed reference functions selected by name; since the slice-7 conditional-njit accommodation, resolve() njit-wraps where numba imports — the oracle env — and hands the committed function plain where it does not — the rewrite env, so both engines consume the same committed source in the form their kernels require). Registration gate pinned: 3 positional args and a *args function (co_argcount 0) both TypeError with the pinned message naming the function and count; bound-njit-wrapped pinned on the dispatcher side (every registrand is an njit dispatcher, so the py_func unwrap runs in every banked registration). SEMANTICS pinned through reason() output, not registration state: the 2-arg form's derived bound (weight-scaled mean — and the weights parameter's consumption pinned differentially: default-weights combo [0.5,1] vs weights [0.5,1.5] combo2 [0.625,1] in one case) and the 6-arg extended form's qualified-grounding metadata (crowd(A)=[0.25,1] from 2 clause-0 groundings/8, with atom_trace OFF so the metadata flows through the extended-flag gate alone). interacts-reset pinned: reset_rules clears the registration and the re-added rule then raises the same NameError(\"name 'annotation' is not defined\") the never-registered arm banks (annotate's objmode output is only assigned inside the name-match loop, interpretation.py:1918-1930). Return-shape contract pinned (session 29): the pinned objmode exit coerces the registrand return to Tuple((float64, float64)) (interpretation.py:1918) — a 3-tuple raises ValueError('size mismatch for tuple, expected 2 element(s) but got 3') and an Interval return raises TypeError('bad argument type for built-in operation'), both messages screened byte-stable on the pin (2 fresh processes per arm, 2026-07-12) and reproduced at the rewrite's annotate seam (annotation-fn-return-triple / annotation-fn-return-interval — the slice-2 review L3 arms). The unbox is TUPLE-ONLY (session-29 review): a LIST return of any size — 2 or 3 alike — takes the same bad-argument TypeError, because the pinned unbox walks the value with PyTuple_GetItem and a non-tuple never reaches the size check (screened byte-stable on the pin, 2 fresh processes per size, 2026-07-12; the review corrected the rewrite's len()-based coercion, which accepted a size-2 list, to the tuple-check; seam test test_annotation_fn_list_return_raises_pinned_bad_argument_any_size; uncased — no committed reference function returns a list). Duplicate-name registration pinned (batch B3, annotation-fn-duplicate-name): the match loop has NO break — every same-named registrand runs and the LAST registration's result wins (the shadow's constant [0.5,0.75] banks, not clause_lower_mean's [0.25,1]); registered through the registry's shadow entries (key deliberately != __name__ — harness/reference_fns.py SHADOWS), the sharp asymmetry with the head side's break-on-first-match. Named unobserved: a PLAIN (non-njit) callable is accepted by the registration gate but reason() then fails numba argument typing (screened 2026-07-07: TypingError 'Cannot determine Numba type of <class tuple>' embedding engine-env paths — unbanked because the message is engine-environment text, guaranteed to differ across environments); interacts-reorder_clauses (the 6-arg case's graph has edges ≤ nodes, so the reorder pass never runs — the extended args' post-reorder clause-order contract is unexercised); element-level coercion faults (a 2-TUPLE of NON-NUMBERS reaching the float64 conversion) — no committed reference function returns one, and banking that arm needs its own pin screen first
- analysis: docs/analysis/surface/rules.md

## fn:add_head_function
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:1484
- status: equivalent
- cases: head-fn-grounding, head-fn-unregistered-name, head-fn-reset-clears, head-fn-ungrounded-var, head-fn-return-bare-string, head-fn-duplicate-name, head-fn-edge-rule-positions
- input classes:
  - happy-basic
  - happy-edge-rule-heads
  - bound-no-validation
  - malformed-return-shape
  - interacts-reset
  - interacts-head-fn-in-dsl
  - interacts-duplicate-name
  - malformed-ungrounded-fn-arg
- notes: cased through the named-function registry (conditional-njit resolve since slice 7 — see fn:add_annotation_function). The no-validation asymmetry pinned live: the SAME star_args_stub that TypeErrors at add_annotation_function registers here silently ({'raised': false}) and, unreferenced by any rule head, is inert — while the referenced head function grounds the head variable through the DSL's f(X) form and Processed(A):[1,1] derives (both halves of interacts-head-fn-in-dsl in one case). The unregistered-name arm is SILENT at the pin — _call_head_function's objmode loop finds no __name__ match and returns the pre-seeded empty grounding (interpretation.py:2330-2338), so the rule fires for no one and reason() completes with zero rule rows — the sharp asymmetry with the annotation side's NameError. interacts-reset pinned by the same silent-empty shape after reset_rules clears the registration (rule re-added via the add_rule step; head-fn-grounding is the derivation twin). The ungrounded-argument arm pinned by the slice-7 review (head-fn-ungrounded-var): a variable appearing only in the head function's argument list rides as ITSELF (interpretation.py:2300-2305), the function grounds the head to that literal name, and the unguarded apply-seam lookup (interpretation.py:583) raises the BARE builtins.KeyError — empty message, the pinned typed-dict getitem erases the key (the rewrite models this container raise shape via TypedComponentDict; pre-fix it raised the key-bearing KeyError). Edge-rule head-function forms pinned (session 29, head-fn-edge-rule-positions): f(X) in ONE edge-head position (LinkedOne(f(X), Y)) and in BOTH (LinkedBoth(f(X), f(Y))) each ground through the same resolver and derive the edge target on the existing edge — the default engine's non-infer-edges path keeps head pairs filtered to existing edges (interpretation.py:2273-2314). Return contract pinned (session 29, head-fn-return-bare-string): the pinned objmode block unboxes the registrand result to types.ListType(types.unicode_type) (interpretation.py:2332) — a bare string raises TypeError(\"can't unbox a <class 'str'> as a <class 'numba.typed.typedlist.List'>\"), screened byte-stable on the pin (2 fresh processes) and reproduced at the rewrite's call_head_function seam. Duplicate-name resolution pinned (batch B3's head twin, head-fn-duplicate-name): the loop BREAKS on the first __name__ match (interpretation.py:2334-2336) — the FIRST registration wins (the shadow's last-grounding pick banks over the real first-grounding picker), the sharp asymmetry with the annotation side's no-break last-wins. Named unobserved: a non-njit registration, though silently accepted, poisons reason() with a numba argument TypingError even when UNREFERENCED (the pyobject in the head_functions tuple fails kernel typing — screened 2026-07-07, unbanked: engine-environment message text); the unbox's element-dtype fault (a list of NON-STRINGS) — no committed reference function returns one, and banking that arm needs its own pin screen first
- analysis: docs/analysis/surface/rules.md

## fn:reset
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:487
- status: equivalent
- cases: reset-no-program, reset-with-program
- input classes:
  - no-program
  - with-program
- notes: does NOT clear settings, timestamp, clause maps, IPL, or grounding tables; leaves a live program half-cleared
- analysis: docs/analysis/surface/reason-and-state.md

## fn:reset_rules
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:517
- status: equivalent
- cases: reset-rules-no-program, reset-rules-with-program, annotation-fn-reset-clears, head-fn-reset-clears
- input classes:
  - no-program
  - with-program
- notes: clears rules + annotation/head functions; facts/graph/settings untouched. The function-registry half is now pinned behaviorally (was assertion-only): after reset_rules a re-added rule naming the previously-registered annotation function raises the unregistered-name NameError, and the head-function twin grounds to nothing (the two reset-clears cases)
- analysis: docs/analysis/surface/reason-and-state.md

## fn:reset_settings
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:561
- status: equivalent
- cases: reset-settings-restore
- input classes:
  - always
- notes: restores all 18 knobs to constructor defaults
- analysis: docs/analysis/surface/reason-and-state.md

## fn:get_rules
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:510
- status: equivalent
- cases: accessors-fresh-state, accessors-lifecycle, save-rule-trace-clause-reorder, reason-queries-filter, reason-queries-no-match
- input classes:
  - loaded
  - none
  - post-reason-filtered
- notes: returns the live global — reason(queries=...) permanently narrows what this returns, pinned by reason-queries-filter (post-reason fingerprint holds only the survivor rule) now that the capture constructs Query objects; the zero-survivor arm leaves __rules a plain empty list (fingerprint [], reason-queries-no-match — the one state where the accessor returns an empty list rather than None); the reorder pass also *replaces* __rules with a clause-reordered copy whenever edges outnumber nodes (pyreason.py:1598-1606), pinned by save-rule-trace-clause-reorder's post-reason fingerprint (popular(y) moved ahead of Friends(x,y)); fresh-import and post-reset returns are None. Named unobserved facet: the accessor fingerprint renders the ordered clause list but not thresholds, which the reorder pass permutes in step with the clauses (reorder_clauses.py:22-25) — the threshold surface's consumption is pinned behaviorally by the type:Threshold gate cases, but the permuted-thresholds facet of THIS accessor stays unrendered
- analysis: docs/analysis/surface/reason-and-state.md

## fn:get_logic_program
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:529
- status: equivalent
- cases: accessors-fresh-state, accessors-lifecycle
- input classes:
  - before-reason
  - after-reason
  - after-reset
- notes: reset() never nulls __program — distinguish no-program from program-with-cleared-interpretation; all three classes pinned via the structural fingerprint (None before any reason — even with graph/rules loaded; present holding the exact interpretation reason() returned; present with interp None after reset). Program.interp is the seam get_interpretation reads (pyreason.py:546), so the fingerprint holds a candidate engine's program object to that attribute surface
- analysis: docs/analysis/surface/reason-and-state.md

## fn:get_interpretation
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:538
- status: equivalent
- cases: accessors-fresh-state, accessors-lifecycle
- input classes:
  - happy
  - no-program
  - program-with-null-interp
- notes: raise vs return-None hinges on whether reset() ran with a live program — all three pinned: the no-program raise (builtins.Exception, 'No interpretation found. Please run `pr.reason()` first', banked via allow_raise on fresh import AND on loaded-but-unreasoned state), the happy return (identity with reason()'s return — a live reference, not a copy), and the post-reset None return without raising
- analysis: docs/analysis/surface/reason-and-state.md

## fn:get_time
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:549
- status: equivalent
- cases: hello-world, conv-perfect, conv-delta-interp, conv-delta-bound, persistent-off, persistent-on, inconsistency-ipl-resolve, inconsistency-ipl-override, reason-again-restart-true, reason-again-restart-false, reason-again-no-program, reason-bare-again-no-facts, reset-with-program, reset-no-program, reset-rules-with-program, reset-rules-no-program, reset-settings-restore, edge-rule-frames, store-off-accessors, store-off-atom-trace-flip, fp-version-on, update-mode-default, update-mode-override, update-mode-junk-string, allow-ground-rules-on, allow-ground-rules-off, graph-attr-parsing-on, graph-attr-parsing-off, static-graph-facts-on, static-graph-facts-off, save-graph-attrs-to-trace-on, save-graph-attrs-to-trace-off, canonical-on, canonical-last-write, abort-on-inconsistency-default, abort-on-inconsistency-on, memory-profile-default, memory-profile-on, reverse-digraph-default, reverse-digraph-on, load-graphml-basic, load-graphml-no-attr-parse, graphml-attr-coercions, graphml-empty, output-to-file-default, output-to-file-on, output-file-name-custom, output-file-name-inert, parallel-computing-default, parallel-computing-on, parallel-fp-precedence, perf-ladder-small, perf-ladder-medium, perf-ladder-large
- input classes:
  - happy
  - no-interpretation
  - null-interp-attribute
- notes: returns interp.time + 1; the post-reset null-interp path raises AttributeError instead of returning 0 (confirmed at the pin; pinned by reset-with-program's allow_raise probe)
- analysis: docs/analysis/surface/reason-and-state.md

## fn:reason
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:1497
- status: equivalent
- cases: hello-world, conv-perfect, conv-delta-interp, conv-delta-bound, persistent-off, persistent-on, inconsistency-ipl-resolve, inconsistency-ipl-override, reason-again-restart-true, reason-again-restart-false, reason-again-no-program, reason-bare-again-no-facts, reset-with-program, reset-no-program, reset-rules-with-program, reset-rules-no-program, reset-settings-restore, edge-rule-frames, store-off-accessors, store-off-atom-trace-flip, fp-version-on, update-mode-default, update-mode-override, update-mode-junk-string, allow-ground-rules-on, allow-ground-rules-off, graph-attr-parsing-on, graph-attr-parsing-off, static-graph-facts-on, static-graph-facts-off, save-graph-attrs-to-trace-on, save-graph-attrs-to-trace-off, canonical-on, canonical-last-write, abort-on-inconsistency-default, abort-on-inconsistency-on, memory-profile-default, memory-profile-on, reverse-digraph-default, reverse-digraph-on, load-graphml-basic, load-graphml-no-attr-parse, graphml-attr-coercions, graphml-empty, output-to-file-default, output-to-file-on, output-file-name-custom, output-file-name-inert, parallel-computing-default, parallel-computing-on, parallel-fp-precedence, reason-queries-filter, reason-queries-no-match, reason-queries-no-match-edge-heavy, perf-ladder-small, perf-ladder-medium, perf-ladder-large
- input classes:
  - happy-fresh
  - again-resume
  - again-but-no-program
  - again-assert-path
  - conv-perfect
  - conv-delta-interp
  - conv-delta-bound
  - timesteps-cap
  - timesteps-neg1-run-to-convergence
  - queries-filter
  - restart-true-resume
  - restart-false-continue
  - memory-profile-on
  - no-graph
  - no-rules
  - trace-suppression-interaction
  - clause-reorder
  - output-to-file
- notes: the spine item; clears fact globals on exit (so a bare again-resume raises TypeError — pinned), permanently filters __rules under queries (queries-filter now pinned by reason-queries-filter/-no-match: predicate-only match, one-survivor narrowing, and the zero-survivor numba ValueError 'cannot compute fingerprint of empty list'; the self-recursive-rule query crash and multi-survivor ordering hazards are recorded on type:Query's row), mutates atom_trace when store is off. restart=True resets interp.time while the rule trace keeps prior-run events, so trace-reconstructing accessors (filter_and_sort_*, get_dict) raise KeyError after it — pinned behavior, oracle-bug-candidate once a rewrite exists
- analysis: docs/analysis/surface/reason-and-state.md

## fn:save_rule_trace
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:1645
- status: equivalent
- cases: save-rule-trace-basic, save-rule-trace-atom-trace-off, save-rule-trace-store-off, save-rule-trace-clause-reorder, ipl-atom-trace-off-trace
- input classes:
  - happy
  - store-off-assert
  - atom-trace-columns
  - folder-variants
  - clause-map-reorder
- notes: depends on module-global timestamp + clause maps from the most recent reason(); writes rule_trace_{nodes,edges}_{timestamp}.csv (output.py:103-104) — the reason-time wall-clock stamp in the names is canonicalized by the save_rule_trace probe under the same run-schedule rationale as the session-10 .txt stamp (TRACE_TS_RE in harness/capture.py), contents compared exactly. Characterization (scoped): with atom_trace off, fact-, rule-, and inconsistency-triggered rows bank an empty trace name (interpretation.py:298, :374, :1544-1549, :1663-1668, resolve_inconsistency_* :1969-1974; interpretation_fp.py mirrors), so for them 'Occurred Due To' stays '-' and output.py's r[7]-name fallback (output.py:23-25) never fires — contra the analysis file's off-arm description ("comes from the rule name r[7]"). The fallback is NOT dead outright: IPL complement rows bank 'IPL: <label>' unconditionally (interpretation.py:304, :308, :380, :384, :1582, :1599; fp mirrors), so with atom_trace off those rows show 'IPL: <label>' via exactly this fallback (pinned by the committed ipl-atom-trace-off-trace case, session 13: friends graph + the yaml-loaded [popular, unpopular] pair, atom_trace off — the saved node CSV shows '-' on all 6 popular rows and 'IPL: popular' on all 6 unpopular rows). Clause-map reorder pinned with a non-identity map (edge-clause-first rule): CSV Clause-i columns map back to author order while get_rules shows the reordered live rule. A caller folder is passed through verbatim; a nonexistent folder raises pandas' OSError (screened, not cased — the probe creates its named subfolder to keep the refusal from wearing the engine label; the rewrite reproduces the exact OSError shape — pandas' check_parent_directory message, never a bare open() FileNotFoundError — fixed and seam-tested in the slice-6 review, tests/test_rewrite_output_surface.py::test_save_rule_trace_missing_folder_raises_pinned_oserror)
- analysis: docs/analysis/surface/reason-and-state.md

## fn:get_rule_trace
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:1658
- status: equivalent
- cases: hello-world, conv-perfect, conv-delta-interp, conv-delta-bound, persistent-off, persistent-on, inconsistency-ipl-resolve, inconsistency-ipl-override, reason-again-restart-true, reason-again-restart-false, reason-again-no-program, reset-with-program, reset-rules-with-program, reset-settings-restore, edge-rule-frames, store-off-accessors, fp-version-on, update-mode-default, update-mode-override, update-mode-junk-string, allow-ground-rules-on, allow-ground-rules-off, graph-attr-parsing-on, graph-attr-parsing-off, static-graph-facts-on, static-graph-facts-off, save-graph-attrs-to-trace-on, save-graph-attrs-to-trace-off, canonical-on, canonical-last-write, abort-on-inconsistency-default, abort-on-inconsistency-on, memory-profile-default, memory-profile-on, reverse-digraph-default, reverse-digraph-on, load-graphml-basic, load-graphml-no-attr-parse, graphml-attr-coercions, output-to-file-default, output-to-file-on, output-file-name-custom, output-file-name-inert, parallel-computing-default, parallel-computing-on, parallel-fp-precedence
- input classes:
  - happy
  - store-off-assert
  - atom-trace-columns
  - empty-trace
- notes: fixed 10-column header plus optional Clause-i columns; event order is contract; the empty-trace shape (header, zero rows) is pinned by reset-settings-restore's post-restore run
- analysis: docs/analysis/surface/reason-and-state.md

## fn:filter_and_sort_nodes
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:1672
- status: equivalent
- cases: hello-world, conv-perfect, conv-delta-interp, conv-delta-bound, persistent-off, persistent-on, inconsistency-ipl-resolve, inconsistency-ipl-override, reason-again-restart-true, reason-again-restart-false, reason-again-no-program, store-off-accessors, fp-version-on, update-mode-default, update-mode-override, update-mode-junk-string, allow-ground-rules-on, allow-ground-rules-off, graph-attr-parsing-on, graph-attr-parsing-off, static-graph-facts-on, static-graph-facts-off, save-graph-attrs-to-trace-on, save-graph-attrs-to-trace-off, canonical-on, canonical-last-write, abort-on-inconsistency-default, abort-on-inconsistency-on, memory-profile-default, memory-profile-on, reverse-digraph-default, reverse-digraph-on, load-graphml-basic, load-graphml-no-attr-parse, graphml-attr-coercions, output-to-file-default, output-to-file-on, output-file-name-custom, output-file-name-inert, parallel-computing-default, parallel-computing-on, parallel-fp-precedence, perf-ladder-small, perf-ladder-medium, perf-ladder-large
- input classes:
  - happy
  - store-off-assert
  - bound-filter
  - sort-lower
  - sort-upper
  - descending-toggle
  - label-not-present
  - empty-timestep
  - multi-label
- notes: frame count is interp.time + 1; latest-change-wins relies on chronological trace append order
- analysis: docs/analysis/surface/reason-and-state.md

## fn:filter_and_sort_edges
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:1688
- status: equivalent
- cases: edge-rule-frames, store-off-accessors, graph-attr-parsing-on, graph-attr-parsing-off, static-graph-facts-on, static-graph-facts-off, save-graph-attrs-to-trace-on, save-graph-attrs-to-trace-off, reverse-digraph-default, reverse-digraph-on, load-graphml-basic, load-graphml-no-attr-parse, graphml-attr-coercions
- input classes:
  - happy
  - store-off-assert
  - bound-filter
  - sort-lower
  - sort-upper
  - descending-toggle
  - label-not-present
  - empty-timestep
  - multi-label
  - edge-component-shape
- notes: empty and non-empty frames take different reconstruction branches (component tuples rebuilt from a two-level index vs fabricated [component, *labels] columns) that normalize to the same column list — edge-rule-frames pins both branches in one probe (t=0 empty frame, t≥1 tuple components); store-off assert pinned by store-off-accessors
- analysis: docs/analysis/surface/reason-and-state.md

## type:Rule
- oracle anchor: oracle/pyreason/pyreason/scripts/rules/rule.py:4
- status: equivalent
- cases: hello-world, conv-perfect, conv-delta-interp, conv-delta-bound, persistent-off, persistent-on, inconsistency-ipl-resolve, inconsistency-ipl-override, rule-text-malformed, reason-again-restart-true, reason-again-restart-false, reason-again-no-program, reason-bare-again-no-facts, reset-with-program, reset-no-program, reset-rules-with-program, reset-rules-no-program, reset-settings-restore, edge-rule-frames, store-off-accessors, store-off-atom-trace-flip, fp-version-on, update-mode-default, update-mode-override, update-mode-junk-string, allow-ground-rules-on, allow-ground-rules-off, graph-attr-parsing-on, graph-attr-parsing-off, static-graph-facts-on, static-graph-facts-off, save-graph-attrs-to-trace-on, save-graph-attrs-to-trace-off, canonical-on, canonical-last-write, abort-on-inconsistency-default, abort-on-inconsistency-on, memory-profile-default, memory-profile-on, reverse-digraph-default, reverse-digraph-on, load-graphml-basic, load-graphml-no-attr-parse, graphml-attr-coercions, graphml-empty, output-to-file-default, output-to-file-on, output-file-name-custom, output-file-name-inert, parallel-computing-default, parallel-computing-on, parallel-fp-precedence, perf-ladder-small, perf-ladder-medium, perf-ladder-large
- input classes:
  - happy-text-only
  - happy-full-args
  - bound-param-order-swap
  - interacts-all-dsl-classes
  - interacts-custom_thresholds-list-vs-dict
  - interacts-weights
- notes: thin wrapper — all validation is in parse_rule; constructor arg order differs from parse_rule's
- analysis: docs/analysis/surface/rules.md

## type:Fact
- oracle anchor: oracle/pyreason/pyreason/scripts/facts/fact.py:5
- status: equivalent
- cases: hello-world, conv-perfect, conv-delta-interp, conv-delta-bound, persistent-off, persistent-on, inconsistency-ipl-resolve, inconsistency-ipl-override, fact-text-malformed, reason-again-restart-true, reason-again-restart-false, reason-again-no-program, reason-bare-again-no-facts, reset-with-program, reset-no-program, reset-rules-with-program, reset-rules-no-program, reset-settings-restore, edge-rule-frames, store-off-accessors, store-off-atom-trace-flip, fp-version-on, update-mode-default, update-mode-override, update-mode-junk-string, allow-ground-rules-on, allow-ground-rules-off, canonical-on, canonical-last-write, abort-on-inconsistency-default, abort-on-inconsistency-on, memory-profile-default, memory-profile-on, output-to-file-default, output-to-file-on, output-file-name-custom, output-file-name-inert, parallel-computing-default, parallel-computing-on, parallel-fp-precedence, perf-ladder-small, perf-ladder-medium, perf-ladder-large
- input classes:
  - happy-node
  - happy-edge
  - happy-explicit-bound
  - happy-boolean-bound
  - happy-negation
  - bound-negated-boolean
  - bound-negated-interval
  - bound-interval-endpoints
  - bound-underscore-predicate
  - bound-component-leading-digit
  - param-static-flag
  - param-times
  - malformed-empty-text
  - malformed-predicate-leading-digit
  - malformed-predicate-badchar
  - malformed-arity
  - malformed-out-of-range
  - malformed-inverted-interval
  - malformed-double-negation
  - malformed-multi-colon
- notes: no validation of name/time/static at this layer; component type polymorphic (str node, tuple edge)
- analysis: docs/analysis/surface/facts-and-graph.md

## type:Query
- oracle anchor: oracle/pyreason/pyreason/scripts/query/query.py:4
- status: equivalent
- cases: query-construct, reason-queries-filter, reason-queries-no-match, reason-queries-no-match-edge-heavy
- input classes:
  - node-default-bound
  - negated
  - explicit-bounds
  - edge-vs-node
  - whitespace
  - malformed-no-paren
  - malformed-negated-with-bounds
  - malformed-bad-float
- notes: all eight construction classes pinned by query-construct's parse fingerprints — the two silent misparses banked as data (no-paren truncates BOTH pred and component to pred_comp[:-1]/[0:-1]: 'popularMary' → pred 'popularMar'; '~pred(x):[l,u]' takes the ':' branch and keeps '~' in the predicate name, bounds [l,u] — the unreconciled-branches corner), bad-float the one raise (ValueError from float()). Consumption pinned by the reason(queries=...) pair: filtering matches by predicate ONLY (bounds/component ignored, filter_ruleset.py:17) and permanently narrows __rules (post-reason get_rules holds only the survivor); ZERO survivors leave __rules a plain empty list and reason() raises numba's ValueError 'cannot compute fingerprint of empty list' at kernel dispatch — but ONLY when the clause-reorder rebuild never ran (edges <= nodes, reason-queries-no-match): on an edge-heavy graph the reorder arm rebuilds even the emptied ruleset as a fresh numba typed list (pyreason.py:1603), which still fingerprints, and the pin reasons to completion with zero rules (reason-queries-no-match-edge-heavy — the slice-6 review's discriminating probe; the pre-fix rewrite raised on both arms, fixed via TypedRuleList). Unobserved facets, each screened 2026-07-07: a query matching a SELF-RECURSIVE rule's head crashes the process outright (unbounded recursion in filter_ruleset through the clause targets; SIGSEGV before Python's RecursionError — no artifact, so un-caseable; the rewrite's divergence here is recorded as DIV-0001); multi-survivor filter ORDER rides list(set(...)) (filter_ruleset.py:34) — screened stable across 4 fresh runs but address-derived by construction, so committed cases keep survivor sets ≤ 1; interpretation.query() (the Query-consuming method on the interpretation object) is not a module-level row and stays unobserved. Rewrite decision (session 21, executing the ledger-14 guard-the-recursion contract): the rewrite's filter_ruleset expands each predicate at most once, so the self-recursive-match input TERMINATES and returns the reachable rule set instead of crashing — a deliberate divergence confined to that un-caseable input (the reachable-rule SET is identical on every acyclic ruleset, which is all any committed case can exercise), seam-tested at tests/test_rewrite_output_surface.py::test_filter_ruleset_terminates_on_self_recursive_rule. **DIV-0001 (adjudicated 2026-07-11, session 25, batch item A1)**: the operator accepted the guarded expansion as documented, tested intentional behavior per AC-6 (docs/divergences/DIV-0001.md)
- analysis: docs/analysis/surface/reason-and-state.md

## type:Threshold
- oracle anchor: oracle/pyreason/pyreason/scripts/threshold/threshold.py:1
- status: equivalent
- cases: threshold-construct, threshold-number-gate-default, threshold-number-gate-two, threshold-number-gate-clause-level, threshold-dict-gate, threshold-percent-total
- input classes:
  - happy-number-total
  - happy-percent-available
  - bound-all-quantifiers
  - malformed-bad-quantifier
  - malformed-bad-quantifier-type
  - malformed-quantifier-type-shape
  - bound-thresh-unvalidated
  - interacts-to_tuple
  - interacts-forall
- notes: construction pinned by threshold-construct (all five quantifiers accepted; ValueError 'Invalid quantifier'/'Invalid quantifier type' on unknown members; a bare-string quantifier_type fails the same membership check on its characters; a length-1 quantifier_type raises IndexError 'tuple index out of range'; thresh stored unvalidated — negative and string values banked verbatim through to_tuple). Accepted-threshold SEMANTICS pinned by the gate cases (the gap the rule-from-json rejections left): a number threshold gates at the CLAUSE level — the qualifying-grounding count across the whole clause, not per head grounding (check_node_grounding_threshold_satisfaction interpretation.py:1364-1377; greater_equal 2 with one whole-graph qualifier kills the rule everywhere while the default twin derives; the -two/-default twins alone cannot tell clause-level from per-head gating — their lone head also saw the lone qualifier — so threshold-number-gate-clause-level banks the discriminator: two disconnected Friends pairs put ONE qualifier in each head's neighborhood but 2 in the clause's whole-graph grounding, and greater_equal 2 fires for BOTH heads) — the dict form's parser-defaulted clause 0 reaches the same consumed thresholds (rule_parser.py:169-173), and percent/total is the qualified/grounding ratio against thresh*0.01 (both percent arms in threshold-percent-total: 2/2 fires, 1/2 does not). Uncovered/unobserved: interacts-forall (the parser-synthesized percent-100 threshold for forall clauses, rule_parser.py:79-81 — not cased here, the forall DSL surface sits with dsl:rule-text); the 'available' quantifier-type at CONSUMPTION (construction banked only; the available branch recomputes the base count from [0,1]-bounded labels, interpretation.py:1371-1372); less/less_equal/greater/equal at consumption (accepted at construction; only greater_equal consumed by a committed case); the parser's float64 coercion of thresh (rule_parser.py:160) is invisible in the banked fingerprints — behavioral only. Equivalent as of session 17: all six covering cases pass oracle-vs-rewrite (threshold-construct in results-phase3-slice1, the five consumption cases in results-phase3-slice2); the named-unobserved arms above are additionally seam-tested in the rewrite (available-at-consumption, tests/test_rewrite_reasoning_core.py) but stay unbanked at this boundary
- analysis: docs/analysis/surface/rules.md

## type:Interval
- oracle anchor: oracle/pyreason/pyreason/scripts/numba_wrapper/numba_types/interval_type.py:13
- status: equivalent
- cases: interval-ops
- input classes:
  - closed-happy
  - closed-static
  - inverted-bounds
  - intersection-empty
  - reset-semantics
  - has-changed
  - contains
  - equality
  - prev-seed-mismatch
- notes: the Python-proxy arm pinned by interval-ops' four fixed pipelines through the aliased public constructor (pyreason.interval.closed): construction seeds prev=current and casts to float64 (integral floats reduce in canonical form; the pinned repr '[l,u]' banked verbatim); equality and hash ignore static and prev (the static-flag-only pair compares equal); containment is bound-inclusion both ways; inverted bounds (l>u) construct unvalidated and intersection clamps any empty result to [0,1] (inverted and disjoint pairs both banked); reset() copies current into prev then sets [0,1] — and reset() itself IGNORES the static flag (the is_static guard lives at the engine call site, interpretation.py:265-273, not in the type); has_changed flips exactly at the reset transition. prev-seed-mismatch: the PROXY arm is pinned — the post-reset intersection's result carries prev = self's CURRENT bounds ([0,1] after reset; interval.py:69) — while the JITTED overload_method arm (seeds from self's prev, interval_type.py:63) is named unobserved: it is only reachable by compiling new jitted code, which is not part of the public surface; its engine-internal effect is embedded in every reasoning case's bounds but never isolated. The rewrite's single core pins the PROXY arm (prev = self's current bounds, src/pyreason/interval.py:90-91) — **blessed by the operator 2026-07-11 (session 25, batch item B25)** as the contractual seeding, it being the only publicly observable arm
- analysis: docs/analysis/surface/reason-and-state.md

## type:Label
- oracle anchor: oracle/pyreason/pyreason/scripts/numba_wrapper/numba_types/label_type.py:16
- status: equivalent
- cases: label-ops
- input classes:
  - construct
  - equality
  - hash
  - get-value
  - boxing-roundtrip
- notes: the Python-side value class pinned by label-ops through the aliased public class (pyreason.label.Label): get_value/str/repr echo the string; equality and hash are by string value alone (same-text distinct objects equal and hash-equal, different texts neither) — banked as RELATIONS, never raw hash numbers; the empty-string label constructs and behaves identically; and equality against a non-Label raises AttributeError(\"'str' object has no attribute 'get_value'\") because the pinned __eq__ calls get_value() on its argument BEFORE its isinstance guard (label.py:9-10). Named unobserved: the construct class's non-string REJECTION is jit-context-only (the numba typer, label_type.py:30-35 — Python-side Label(5) stores the 5 silently, out of this row's public reach and not banked); boxing-roundtrip is engine-internal (its effect is implicit in every reasoning case's trace labels but never isolated at this boundary)
- analysis: docs/analysis/surface/reason-and-state.md

## dsl:rule-text
- oracle anchor: oracle/pyreason/pyreason/scripts/utils/rule_parser.py:17
- status: equivalent
- cases: hello-world, conv-perfect, conv-delta-interp, conv-delta-bound, persistent-off, persistent-on, inconsistency-ipl-resolve, inconsistency-ipl-override, rule-text-malformed, reason-again-restart-true, reason-again-restart-false, reason-again-no-program, reason-bare-again-no-facts, reset-with-program, reset-no-program, reset-rules-with-program, reset-rules-no-program, reset-settings-restore, edge-rule-frames, store-off-accessors, store-off-atom-trace-flip, fp-version-on, update-mode-default, update-mode-override, update-mode-junk-string, allow-ground-rules-on, allow-ground-rules-off, graph-attr-parsing-on, graph-attr-parsing-off, static-graph-facts-on, static-graph-facts-off, save-graph-attrs-to-trace-on, save-graph-attrs-to-trace-off, canonical-on, canonical-last-write, abort-on-inconsistency-default, abort-on-inconsistency-on, memory-profile-default, memory-profile-on, reverse-digraph-default, reverse-digraph-on, load-graphml-basic, load-graphml-no-attr-parse, graphml-attr-coercions, graphml-empty, output-to-file-default, output-to-file-on, output-file-name-custom, output-file-name-inert, parallel-computing-default, parallel-computing-on, parallel-fp-precedence, perf-ladder-small, perf-ladder-medium, perf-ladder-large
- input classes:
  - happy-node-rule
  - happy-edge-rule
  - malformed-non-string
  - malformed-empty
  - malformed-arrow-count
  - malformed-empty-head
  - happy-empty-body
  - bound-whitespace-collapse
  - happy-delta-t
  - bound-zero-delta-default
  - bound-delta-t-uint16
  - malformed-multichar-delta
  - happy-multi-clause
  - malformed-trailing-comma
  - malformed-clause-no-parens
  - malformed-clause-multi-colon
  - happy-explicit-bound
  - bound-default-interval
  - bound-true-false-shorthand
  - malformed-bound-arity
  - malformed-bound-nonnumeric
  - malformed-bound-nan
  - malformed-bound-out-of-range
  - malformed-bound-inverted
  - happy-negated-clause
  - bound-negated-explicit
  - malformed-double-negation-body
  - malformed-double-negation-head
  - bound-negated-head
  - bound-negated-ann-fn-noop
  - happy-head-bound
  - happy-head-ann-fn
  - malformed-head-multi-colon
  - malformed-head-no-parens
  - malformed-head-bracketed-ann-fn
  - bound-head-no-variable
  - happy-head-simple-vars
  - happy-head-function
  - malformed-predicate-name
  - malformed-component-name
  - happy-comparison-clause
  - happy-forall
  - malformed-forall-unclosed
  - malformed-forall-no-inner-pred
  - interacts-forall-custom_thresholds
  - happy-thresholds-list
  - malformed-thresholds-list-length
  - happy-thresholds-dict
  - malformed-thresholds-dict-empty
  - malformed-thresholds-dict-negative-key
  - malformed-thresholds-dict-key-oob
  - bound-thresholds-none
  - happy-weights-default
  - happy-weights-array
  - malformed-weights-nonarray
  - malformed-weights-length
  - malformed-weights-nonnumeric
  - malformed-weights-nonfinite
  - malformed-weights-negative
  - interacts-infer_edges-node
  - interacts-infer_edges-edge
  - interacts-set_static
- notes: the deepest DSL; the doubled-delimiter clause splitter and the uint16 delta_t cast are the named hazards
- analysis: docs/analysis/surface/rules.md

## dsl:fact-text
- oracle anchor: oracle/pyreason/pyreason/scripts/utils/fact_parser.py:28
- status: equivalent
- cases: hello-world, conv-perfect, conv-delta-interp, conv-delta-bound, persistent-off, persistent-on, inconsistency-ipl-resolve, inconsistency-ipl-override, fact-text-malformed, reason-again-restart-true, reason-again-restart-false, reason-again-no-program, reason-bare-again-no-facts, reset-with-program, reset-no-program, reset-rules-with-program, reset-rules-no-program, reset-settings-restore, edge-rule-frames, store-off-accessors, store-off-atom-trace-flip, fp-version-on, update-mode-default, update-mode-override, update-mode-junk-string, allow-ground-rules-on, allow-ground-rules-off, canonical-on, canonical-last-write, abort-on-inconsistency-default, abort-on-inconsistency-on, memory-profile-default, memory-profile-on, output-to-file-default, output-to-file-on, output-file-name-custom, output-file-name-inert, parallel-computing-default, parallel-computing-on, parallel-fp-precedence, perf-ladder-small, perf-ladder-medium, perf-ladder-large
- input classes:
  - happy-node-default-true
  - happy-edge
  - happy-explicit-true-false
  - happy-interval
  - dsl-whitespace-insensitive
  - dsl-negation-node
  - dsl-negation-boolean-flip
  - dsl-negation-interval-complement
  - bound-predicate-charset
  - bound-component-charset
  - bound-interval-endpoints
  - malformed-empty
  - malformed-double-negation
  - malformed-multi-colon
  - malformed-empty-predcomp
  - malformed-no-parens
  - malformed-paren-count
  - malformed-paren-order
  - malformed-empty-component
  - malformed-edge-arity
  - malformed-empty-edge-component
  - malformed-predicate-leading-digit
  - malformed-predicate-badchar
  - malformed-interval-no-brackets
  - malformed-interval-empty
  - malformed-interval-arity
  - malformed-interval-nonnumeric
  - malformed-interval-out-of-range
  - malformed-interval-inverted
- notes: predicate and component charsets differ; all spaces stripped pre-parse; negated intervals round to 10 places
- analysis: docs/analysis/surface/facts-and-graph.md

## setting:verbose
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:86
- status: equivalent
- cases: hello-world, conv-perfect, conv-delta-interp, conv-delta-bound, persistent-off, persistent-on, inconsistency-ipl-resolve, inconsistency-ipl-override, reason-again-restart-true, reason-again-restart-false, reason-again-no-program, reason-bare-again-no-facts, reset-with-program, reset-no-program, reset-rules-with-program, reset-rules-no-program, reset-settings-restore, edge-rule-frames, store-off-accessors, store-off-atom-trace-flip, fp-version-on, update-mode-default, update-mode-override, update-mode-junk-string, allow-ground-rules-on, allow-ground-rules-off, graph-attr-parsing-on, graph-attr-parsing-off, static-graph-facts-on, static-graph-facts-off, save-graph-attrs-to-trace-on, save-graph-attrs-to-trace-off, canonical-on, canonical-last-write, abort-on-inconsistency-default, abort-on-inconsistency-on, memory-profile-default, memory-profile-on, reverse-digraph-default, reverse-digraph-on, load-graphml-basic, load-graphml-no-attr-parse, graphml-attr-coercions, graphml-empty, output-to-file-default, output-to-file-on, output-file-name-custom, output-file-name-inert, parallel-computing-default, parallel-computing-on, parallel-fp-precedence, perf-ladder-small, perf-ladder-medium, perf-ladder-large
- input classes:
  - default-true-prints
  - nondefault-false-silent
  - forwarded-to-engine
  - type-reject
- notes: print-gating only — reasoning results identical either way
- analysis: docs/analysis/surface/settings.md

## setting:output_to_file
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:94
- status: equivalent
- cases: output-to-file-default, output-to-file-on, output-file-name-custom, output-file-name-inert
- input classes:
  - default-false-stdout
  - nondefault-true-redirect
  - interaction-filename
  - type-reject
- notes: rebinds sys.stdout to ./{output_file_name}_{wall-clock}.txt opened for append (pyreason.py:1513-1514, re-opened onto the same name at :1541-1542) and never restores or flushes it — process-global side effect; the harness's output_file probe (session 10) confines the file to a per-capture directory, flushes, and compares name (timestamp-canonicalized — recorded rationale in harness/capture.py) and contents exactly; the redirect moves reason-time prints only — reasoning digests matched the default twin's at authoring. Uncovered classes: type-reject (setter TypeError at pyreason.py:255; family-wide, needs a raising-probe form)
- analysis: docs/analysis/surface/settings.md

## setting:output_file_name
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:102
- status: equivalent
- cases: output-to-file-default, output-to-file-on, output-file-name-custom, output-file-name-inert
- input classes:
  - default-name
  - nondefault-name
  - inert-when-output-false
  - type-reject
- notes: interpolated verbatim into the redirect path, no path validation (setter pyreason.py:260-270); its only consumption sites are the output_to_file-guarded opens (pyreason.py:1514/:1542), so with the redirect off a set name writes nothing anywhere — pinned by output-file-name-inert's empty confined directory. Uncovered classes: type-reject (setter TypeError at pyreason.py:268; family-wide, needs a raising-probe form)
- analysis: docs/analysis/surface/settings.md

## setting:graph_attribute_parsing
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:110
- status: equivalent
- cases: graph-attr-parsing-on, graph-attr-parsing-off, load-graphml-basic, load-graphml-no-attr-parse, graphml-attr-coercions
- input classes:
  - default-true-parse
  - nondefault-false-skip
  - read-at-load-time
  - interaction-static
  - type-reject
- notes: load-time knob — must be set before load_graph/load_graphml
- analysis: docs/analysis/surface/settings.md

## setting:abort_on_inconsistency
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:118
- status: equivalent
- cases: abort-on-inconsistency-default, abort-on-inconsistency-on
- input classes:
  - dead-knob
  - type-reject
- notes: dead knob at the pin — in the engine package the name appears only inside _Settings (pyreason.py:49/:70/:118-123/:284-294; zero hits under scripts/, grep-verified session 8); the twin pair's reasoning digests are equal on an inconsistency-triggering program, only the readback differs
- analysis: docs/analysis/surface/settings.md

## setting:memory_profile
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:126
- status: equivalent
- cases: memory-profile-default, memory-profile-on, memory-profile-output-on
- input classes:
  - default-false-direct
  - nondefault-true-profiled
  - interaction-output
  - type-reject
- notes: observational wrapper; interpretation unchanged. interaction-output pinned by memory-profile-output-on under the operator-approved (2026-07-07) peak-MB canonicalization: the redirect file carries output-to-file-on's print shape plus the profiled branch's peak line (pyreason.py:1520), whose number is run-varying measurement (103.20 vs 103.53 MB across identical fresh processes at screening) — the output_file probe's per-case canonicalize_peak_mb opt-in reduces exactly that number to '<peak-mb>' (PEAK_MB_RE rationale at the definition site in harness/capture.py; the flag is validation-gated to memory_profile cases) while every other character compares exactly. Uncovered: type-reject (family-wide)
- analysis: docs/analysis/surface/settings.md

## setting:reverse_digraph
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:134
- status: equivalent
- cases: reverse-digraph-default, reverse-digraph-on
- input classes:
  - default-false-asis
  - nondefault-true-reversed
  - forwarded-to-engine
  - read-at-load-time
  - type-reject
- notes: split read — reversal at load time over the load_graphml path only (load_graph never reads the knob: pyreason.py:589-599); the flag is also snapshotted into the Program (pyreason.py:1609), but engine-side that copy is only stored and threaded (interpretation.py:69/:232/:242, mirrored in the fp and parallel kernels) and never consumed in any kernel body (grep-verified session 9) — a dead snapshot, contra the analysis note that it is "re-read at reason time". Uncovered classes: forwarded-to-engine (no behavioral observable beyond the snapshot), type-reject (setter TypeError at pyreason.py:319; a settings raise during input application fails the capture, so it needs its own probe form)
- analysis: docs/analysis/surface/settings.md

## setting:atom_trace
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:143
- status: equivalent
- cases: hello-world, conv-perfect, conv-delta-interp, conv-delta-bound, persistent-off, persistent-on, inconsistency-ipl-resolve, inconsistency-ipl-override, reason-again-restart-true, reason-again-restart-false, reason-again-no-program, reason-bare-again-no-facts, reset-with-program, reset-no-program, reset-rules-with-program, reset-rules-no-program, reset-settings-restore, edge-rule-frames, store-off-atom-trace-flip, fp-version-on, update-mode-default, update-mode-override, update-mode-junk-string, allow-ground-rules-on, allow-ground-rules-off, graph-attr-parsing-on, graph-attr-parsing-off, static-graph-facts-on, static-graph-facts-off, save-graph-attrs-to-trace-on, save-graph-attrs-to-trace-off, canonical-on, canonical-last-write, abort-on-inconsistency-default, abort-on-inconsistency-on, memory-profile-default, memory-profile-on, reverse-digraph-default, reverse-digraph-on, load-graphml-basic, load-graphml-no-attr-parse, graphml-attr-coercions, output-to-file-default, output-to-file-on, output-file-name-custom, output-file-name-inert, parallel-computing-default, parallel-computing-on, parallel-fp-precedence
- input classes:
  - default-false-notrace
  - nondefault-true-trace
  - forced-off-by-store
  - interaction-rule-trace
  - type-reject
- notes: reason() mutates this knob live when store_interpretation_changes is off
- analysis: docs/analysis/surface/settings.md

## setting:save_graph_attributes_to_trace
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:152
- status: equivalent
- cases: save-graph-attrs-to-trace-on, save-graph-attrs-to-trace-off, graphml-attr-coercions
- input classes:
  - default-false-exclude
  - nondefault-true-include
  - interaction-store
  - type-reject
- notes: trace contents only, never derived bounds
- analysis: docs/analysis/surface/settings.md

## setting:canonical
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:161
- status: equivalent
- cases: canonical-on, canonical-last-write
- input classes:
  - alias-of-persistent
  - last-write-wins
  - naming-mismatch
  - type-reject
- notes: pure alias — getter and setter share persistent's field; indistinguishable differentially
- analysis: docs/analysis/surface/settings.md

## setting:persistent
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:170
- status: equivalent
- cases: persistent-off, persistent-on, static-graph-facts-on, static-graph-facts-off, canonical-on, canonical-last-write
- input classes:
  - default-false-nonpersistent
  - nondefault-true-persistent
  - interaction-static
  - interaction-canonical
  - type-reject
- notes: drives the per-timestep bound reset; static bounds escape it in both modes
- analysis: docs/analysis/surface/settings.md

## setting:inconsistency_check
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:178
- status: equivalent
- cases: inconsistency-ipl-resolve, inconsistency-ipl-override
- input classes:
  - default-true-resolve
  - nondefault-false-override
  - type-reject
- notes: the true inconsistency governor (contrast the dead abort_on_inconsistency)
- analysis: docs/analysis/surface/settings.md

## setting:static_graph_facts
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:186
- status: equivalent
- cases: static-graph-facts-on, static-graph-facts-off
- input classes:
  - default-true-static
  - nondefault-false-fluent
  - read-at-load-time
  - interaction-persistent
  - type-reject
- notes: load-time knob stamped onto generated graph-attribute facts
- analysis: docs/analysis/surface/settings.md

## setting:store_interpretation_changes
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:194
- status: equivalent
- cases: store-off-accessors, store-off-atom-trace-flip
- input classes:
  - default-true-store
  - nondefault-false-nostore
  - interaction-atom-trace
  - type-reject
- notes: off breaks every post-run accessor by assert (pinned as four probes over three assert sites — get_rule_trace's single assert precedes the node/edge split and reuses the "save rule trace" message); force-mutates atom_trace at reason start (pinned via get_setting probes: true before reason, false after, store itself unchanged)
- analysis: docs/analysis/surface/settings.md

## setting:parallel_computing
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:203
- status: equivalent
- cases: parallel-computing-default, parallel-computing-on, parallel-fp-precedence
- input classes:
  - default-false-standard
  - nondefault-true-parallel
  - interaction-fp-precedence
  - type-reject
- notes: engine-selection knob; masks fp_version entirely when set (dispatch order at program.py:42-46, pinned behaviorally by parallel-fp-precedence — both knobs true digests the parallel shape, not fp's). The parallel kernel's entire source diff from the serial optimized kernel is the decorator flip parallel=False→True at interpretation_parallel.py:241 (rules loop prange at :571); on the pair's one-rule program (prange width 1 — thread scheduling cannot reorder trace appends) the on-twin digest-equals the default twin on every reasoning probe. Characterization (session 10): the parallel compile took ~174s cold but caches across fresh processes (~3s warm) on numba 0.59.1/darwin — the pin's no-caching belief, written at three sites (getter docstring pyreason.py:204-205, setter docstring :410-411, dispatch comment program.py:41 "We cannot parallelize with cache on"), is refuted on this machine; the decorator itself is cache=True AND parallel=True, and the compiled parallel kernel's single cache file persists unrewritten across every subsequent fresh-process capture (review corroboration, session 10 review report). Uncovered: type-reject (family-wide); multi-rule prange scheduling (trace order under a prange of width >1 is deliberately unexercised — potential nondeterminism there is its own characterization case)
- analysis: docs/analysis/surface/settings.md

## setting:update_mode
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:212
- status: equivalent
- cases: update-mode-default, update-mode-override, update-mode-junk-string
- input classes:
  - default-intersection
  - nondefault-override
  - unvalidated-string
  - type-reject
- notes: any string other than 'override' silently behaves as intersection — no domain validation (every consumption site is a string-equality against 'override'); the junk-string case digest-equals its default twin on all reasoning probes, verified at authoring; override replaces bounds via set_lower_upper and skips the intersection, observable as a rule whose clause bound the replaced interval fails
- analysis: docs/analysis/surface/settings.md

## setting:allow_ground_rules
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:220
- status: equivalent
- cases: allow-ground-rules-on, allow-ground-rules-off
- input classes:
  - default-false-nonground
  - nondefault-true-ground
  - redundant-branch
  - type-reject
- notes: grounding-path knob consumed inside _ground_rule — on, a clause/head constant naming a real graph node grounds directly to that node; off, the same token is an ordinary variable even when a node of that name exists (the pair pins one influenced() derivation vs two on identical inputs)
- analysis: docs/analysis/surface/settings.md

## setting:fp_version
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:228
- status: equivalent
- cases: fp-version-on, parallel-fp-precedence
- input classes:
  - default-false-optimized
  - nondefault-true-fp
  - interaction-parallel-precedence
  - type-reject
- notes: selects interpretation_fp; only reachable when parallel_computing is off — the interaction-parallel-precedence class is pinned by parallel-fp-precedence (both knobs true: digests match the parallel shape, and trace-node/nodes-popular do not match fp-version-on's banked fp shape). On identical hello-world inputs the fp engine's final bounds match the optimized engine's but its traces do not (fp-counter values, event order, duplicated atom-trace groundings) and frame row order differs at the last step — the pinned engine-variant asymmetry the session-6 ledger flagged for adjudication; ADR 0003 answers it (one semantics core under two pinned iteration schedules, `fp_mode`), **confirmed by the operator 2026-07-11 (session 25, batch item B19)** as the recorded answer, closing that carried item. **B17 → DIV-0003 (implemented session 29, direction pre-authorized by the operator 2026-07-11)**: the fp+infer_edges arm — both engines crash at the same `_add_edge` existing-edge seam, the pin with the payload-less typed-dict KeyError() (2/2 fresh-process screens 2026-07-12), the rewrite now with the adjudicated honest STABLE message naming the edge and timestep (DIV-0002's shape, as directed). The arm stays case-less by construction: the raise messages differ by adjudicated design and the harness's only comparison-policy form is a numeric tolerance, so docs/divergences/DIV-0003.md plus the pin-side e2e reproducer (tests/test_div_0003_reproducer.py) and the fast-tier seam twin carry the evidence. Phase-4 hazard (B16, operator-flagged 2026-07-11): the fp schedule cannot terminate on timesteps=-1 (kept for equivalence) — the workload ladder must never combine fp_version=True with timesteps=-1
- analysis: docs/analysis/surface/settings.md
