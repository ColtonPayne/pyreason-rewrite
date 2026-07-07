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
- status: cased
- cases: reverse-digraph-default, reverse-digraph-on, load-graphml-basic, load-graphml-no-attr-parse, graphml-attr-coercions, graphml-empty
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
- notes: mutates five module globals; grounding tables survive reset(); attribute-bound coercions are the hazard cluster — all silent at the pin (session 9: no malformed attribute value raises; values 0 and '0,1' coerce to the vacuous [0,1] and leave no observable row). Uncovered classes: interacts-static_graph_facts (stamping in effect in every happy case here; the interaction itself is proven over load_graph by the static-graph-facts pair), malformed-missing-file and malformed-bad-graphml (the capture's graphml_path input existence-checks fixtures, and a loader raise during input application would fail the capture — a raising-loader probe form is future work)
- analysis: docs/analysis/surface/facts-and-graph.md

## fn:load_graph
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:589
- status: cased
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
- status: uncovered
- cases: none
- input classes:
  - happy-basic
  - bound-ipl-null
  - bound-ipl-empty-list
  - malformed-missing-ipl-key
  - malformed-short-pair
  - malformed-missing-file
  - malformed-bad-yaml
- notes: overwrites __ipl wholesale (contrast add_inconsistent_predicate); IPL survives reset()
- analysis: docs/analysis/surface/facts-and-graph.md

## fn:add_inconsistent_predicate
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:620
- status: cased
- cases: inconsistency-ipl-resolve, inconsistency-ipl-override, abort-on-inconsistency-default, abort-on-inconsistency-on
- input classes:
  - happy-basic
  - interacts-additive-after-yaml
  - bound-same-predicate
  - bound-duplicate-pair
  - malformed-empty-string
  - malformed-non-str
- notes: additive, no dedup or name validation at this boundary
- analysis: docs/analysis/surface/facts-and-graph.md

## fn:add_closed_world_predicate
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:1122
- status: uncovered
- cases: none
- input classes:
  - happy-basic
  - bound-duplicate
  - bound-empty-string
  - malformed-non-str
  - interacts-unknown-predicate
  - interacts-reset
- notes: effect deferred to reason() (unknown [0,1] treated as [0,0]); cleared by reset() unlike IPL
- analysis: docs/analysis/surface/facts-and-graph.md

## fn:add_fact
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:1133
- status: cased
- cases: hello-world, conv-perfect, conv-delta-interp, conv-delta-bound, persistent-off, persistent-on, inconsistency-ipl-resolve, inconsistency-ipl-override, reason-again-restart-true, reason-again-restart-false, reason-again-no-program, reason-bare-again-no-facts, reset-with-program, reset-no-program, reset-rules-with-program, reset-rules-no-program, reset-settings-restore, edge-rule-frames, store-off-accessors, store-off-atom-trace-flip, fp-version-on, update-mode-default, update-mode-override, update-mode-junk-string, allow-ground-rules-on, allow-ground-rules-off, canonical-on, canonical-last-write, abort-on-inconsistency-default, abort-on-inconsistency-on, memory-profile-default, memory-profile-on, output-to-file-default, output-to-file-on, output-file-name-custom, output-file-name-inert, parallel-computing-default, parallel-computing-on, parallel-fp-precedence
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
- status: uncovered
- cases: none
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
- notes: invalid end_time silently defaults to start_time; summary print unconditional (differs from CSV loader)
- analysis: docs/analysis/surface/facts-and-graph.md

## fn:add_fact_from_csv
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:1294
- status: uncovered
- cases: none
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
- notes: header detection is an exact-match; every cell read as string with keep_default_na off
- analysis: docs/analysis/surface/facts-and-graph.md

## fn:add_rule
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:632
- status: cased
- cases: hello-world, conv-perfect, conv-delta-interp, conv-delta-bound, persistent-off, persistent-on, inconsistency-ipl-resolve, inconsistency-ipl-override, reason-again-restart-true, reason-again-restart-false, reason-again-no-program, reason-bare-again-no-facts, reset-with-program, reset-no-program, reset-rules-with-program, reset-rules-no-program, reset-settings-restore, edge-rule-frames, store-off-accessors, store-off-atom-trace-flip, fp-version-on, update-mode-default, update-mode-override, update-mode-junk-string, allow-ground-rules-on, allow-ground-rules-off, graph-attr-parsing-on, graph-attr-parsing-off, static-graph-facts-on, static-graph-facts-off, save-graph-attrs-to-trace-on, save-graph-attrs-to-trace-off, canonical-on, canonical-last-write, abort-on-inconsistency-default, abort-on-inconsistency-on, memory-profile-default, memory-profile-on, reverse-digraph-default, reverse-digraph-on, load-graphml-basic, load-graphml-no-attr-parse, graphml-attr-coercions, graphml-empty, output-to-file-default, output-to-file-on, output-file-name-custom, output-file-name-inert, parallel-computing-default, parallel-computing-on, parallel-fp-precedence
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
- status: uncovered
- cases: none
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
- notes: raise_errors defaults False here (CSV/JSON default True); # comments only when first char
- analysis: docs/analysis/surface/rules.md

## fn:add_rule_from_csv
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:753
- status: uncovered
- cases: none
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
- notes: file-local name dedup never consults the engine-global rule-name set
- analysis: docs/analysis/surface/rules.md

## fn:add_rule_from_json
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:868
- status: uncovered
- cases: none
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
- notes: the only loader exposing custom_thresholds and weights
- analysis: docs/analysis/surface/rules.md

## fn:add_annotation_function
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:1415
- status: uncovered
- cases: none
- input classes:
  - happy-2arg
  - happy-6arg
  - malformed-wrong-arity
  - bound-njit-wrapped
  - bound-defaulted-or-varargs
  - interacts-reset
  - interacts-reorder_clauses
- notes: arity gate (2 or 6) only; njit decoration not enforced; 6-arg contract follows post-reorder clause order
- analysis: docs/analysis/surface/rules.md

## fn:add_head_function
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:1484
- status: uncovered
- cases: none
- input classes:
  - happy-basic
  - bound-no-validation
  - interacts-reset
  - interacts-head-fn-in-dsl
- notes: no validation at all — asymmetric with add_annotation_function
- analysis: docs/analysis/surface/rules.md

## fn:reset
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:487
- status: cased
- cases: reset-no-program, reset-with-program
- input classes:
  - no-program
  - with-program
- notes: does NOT clear settings, timestamp, clause maps, IPL, or grounding tables; leaves a live program half-cleared
- analysis: docs/analysis/surface/reason-and-state.md

## fn:reset_rules
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:517
- status: cased
- cases: reset-rules-no-program, reset-rules-with-program
- input classes:
  - no-program
  - with-program
- notes: clears rules + annotation/head functions; facts/graph/settings untouched
- analysis: docs/analysis/surface/reason-and-state.md

## fn:reset_settings
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:561
- status: cased
- cases: reset-settings-restore
- input classes:
  - always
- notes: restores all 18 knobs to constructor defaults
- analysis: docs/analysis/surface/reason-and-state.md

## fn:get_rules
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:510
- status: uncovered
- cases: none
- input classes:
  - loaded
  - none
  - post-reason-filtered
- notes: returns the live global — reason(queries=...) permanently narrows what this returns
- analysis: docs/analysis/surface/reason-and-state.md

## fn:get_logic_program
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:529
- status: uncovered
- cases: none
- input classes:
  - before-reason
  - after-reason
  - after-reset
- notes: reset() never nulls __program — distinguish no-program from program-with-cleared-interpretation
- analysis: docs/analysis/surface/reason-and-state.md

## fn:get_interpretation
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:538
- status: uncovered
- cases: none
- input classes:
  - happy
  - no-program
  - program-with-null-interp
- notes: raise vs return-None hinges on whether reset() ran with a live program
- analysis: docs/analysis/surface/reason-and-state.md

## fn:get_time
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:549
- status: cased
- cases: hello-world, conv-perfect, conv-delta-interp, conv-delta-bound, persistent-off, persistent-on, inconsistency-ipl-resolve, inconsistency-ipl-override, reason-again-restart-true, reason-again-restart-false, reason-again-no-program, reason-bare-again-no-facts, reset-with-program, reset-no-program, reset-rules-with-program, reset-rules-no-program, reset-settings-restore, edge-rule-frames, store-off-accessors, store-off-atom-trace-flip, fp-version-on, update-mode-default, update-mode-override, update-mode-junk-string, allow-ground-rules-on, allow-ground-rules-off, graph-attr-parsing-on, graph-attr-parsing-off, static-graph-facts-on, static-graph-facts-off, save-graph-attrs-to-trace-on, save-graph-attrs-to-trace-off, canonical-on, canonical-last-write, abort-on-inconsistency-default, abort-on-inconsistency-on, memory-profile-default, memory-profile-on, reverse-digraph-default, reverse-digraph-on, load-graphml-basic, load-graphml-no-attr-parse, graphml-attr-coercions, graphml-empty, output-to-file-default, output-to-file-on, output-file-name-custom, output-file-name-inert, parallel-computing-default, parallel-computing-on, parallel-fp-precedence
- input classes:
  - happy
  - no-interpretation
  - null-interp-attribute
- notes: returns interp.time + 1; the post-reset null-interp path raises AttributeError instead of returning 0 (confirmed at the pin; pinned by reset-with-program's allow_raise probe)
- analysis: docs/analysis/surface/reason-and-state.md

## fn:reason
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:1497
- status: cased
- cases: hello-world, conv-perfect, conv-delta-interp, conv-delta-bound, persistent-off, persistent-on, inconsistency-ipl-resolve, inconsistency-ipl-override, reason-again-restart-true, reason-again-restart-false, reason-again-no-program, reason-bare-again-no-facts, reset-with-program, reset-no-program, reset-rules-with-program, reset-rules-no-program, reset-settings-restore, edge-rule-frames, store-off-accessors, store-off-atom-trace-flip, fp-version-on, update-mode-default, update-mode-override, update-mode-junk-string, allow-ground-rules-on, allow-ground-rules-off, graph-attr-parsing-on, graph-attr-parsing-off, static-graph-facts-on, static-graph-facts-off, save-graph-attrs-to-trace-on, save-graph-attrs-to-trace-off, canonical-on, canonical-last-write, abort-on-inconsistency-default, abort-on-inconsistency-on, memory-profile-default, memory-profile-on, reverse-digraph-default, reverse-digraph-on, load-graphml-basic, load-graphml-no-attr-parse, graphml-attr-coercions, graphml-empty, output-to-file-default, output-to-file-on, output-file-name-custom, output-file-name-inert, parallel-computing-default, parallel-computing-on, parallel-fp-precedence
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
- notes: the spine item; clears fact globals on exit (so a bare again-resume raises TypeError — pinned), permanently filters __rules under queries, mutates atom_trace when store is off. restart=True resets interp.time while the rule trace keeps prior-run events, so trace-reconstructing accessors (filter_and_sort_*, get_dict) raise KeyError after it — pinned behavior, oracle-bug-candidate once a rewrite exists
- analysis: docs/analysis/surface/reason-and-state.md

## fn:save_rule_trace
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:1645
- status: uncovered
- cases: none
- input classes:
  - happy
  - store-off-assert
  - atom-trace-columns
  - folder-variants
  - clause-map-reorder
- notes: depends on module-global timestamp + clause maps from the most recent reason()
- analysis: docs/analysis/surface/reason-and-state.md

## fn:get_rule_trace
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:1658
- status: cased
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
- status: cased
- cases: hello-world, conv-perfect, conv-delta-interp, conv-delta-bound, persistent-off, persistent-on, inconsistency-ipl-resolve, inconsistency-ipl-override, reason-again-restart-true, reason-again-restart-false, reason-again-no-program, store-off-accessors, fp-version-on, update-mode-default, update-mode-override, update-mode-junk-string, allow-ground-rules-on, allow-ground-rules-off, graph-attr-parsing-on, graph-attr-parsing-off, static-graph-facts-on, static-graph-facts-off, save-graph-attrs-to-trace-on, save-graph-attrs-to-trace-off, canonical-on, canonical-last-write, abort-on-inconsistency-default, abort-on-inconsistency-on, memory-profile-default, memory-profile-on, reverse-digraph-default, reverse-digraph-on, load-graphml-basic, load-graphml-no-attr-parse, graphml-attr-coercions, output-to-file-default, output-to-file-on, output-file-name-custom, output-file-name-inert, parallel-computing-default, parallel-computing-on, parallel-fp-precedence
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
- status: cased
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
- status: cased
- cases: hello-world, conv-perfect, conv-delta-interp, conv-delta-bound, persistent-off, persistent-on, inconsistency-ipl-resolve, inconsistency-ipl-override, rule-text-malformed, reason-again-restart-true, reason-again-restart-false, reason-again-no-program, reason-bare-again-no-facts, reset-with-program, reset-no-program, reset-rules-with-program, reset-rules-no-program, reset-settings-restore, edge-rule-frames, store-off-accessors, store-off-atom-trace-flip, fp-version-on, update-mode-default, update-mode-override, update-mode-junk-string, allow-ground-rules-on, allow-ground-rules-off, graph-attr-parsing-on, graph-attr-parsing-off, static-graph-facts-on, static-graph-facts-off, save-graph-attrs-to-trace-on, save-graph-attrs-to-trace-off, canonical-on, canonical-last-write, abort-on-inconsistency-default, abort-on-inconsistency-on, memory-profile-default, memory-profile-on, reverse-digraph-default, reverse-digraph-on, load-graphml-basic, load-graphml-no-attr-parse, graphml-attr-coercions, graphml-empty, output-to-file-default, output-to-file-on, output-file-name-custom, output-file-name-inert, parallel-computing-default, parallel-computing-on, parallel-fp-precedence
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
- status: cased
- cases: hello-world, conv-perfect, conv-delta-interp, conv-delta-bound, persistent-off, persistent-on, inconsistency-ipl-resolve, inconsistency-ipl-override, fact-text-malformed, reason-again-restart-true, reason-again-restart-false, reason-again-no-program, reason-bare-again-no-facts, reset-with-program, reset-no-program, reset-rules-with-program, reset-rules-no-program, reset-settings-restore, edge-rule-frames, store-off-accessors, store-off-atom-trace-flip, fp-version-on, update-mode-default, update-mode-override, update-mode-junk-string, allow-ground-rules-on, allow-ground-rules-off, canonical-on, canonical-last-write, abort-on-inconsistency-default, abort-on-inconsistency-on, memory-profile-default, memory-profile-on, output-to-file-default, output-to-file-on, output-file-name-custom, output-file-name-inert, parallel-computing-default, parallel-computing-on, parallel-fp-precedence
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
- status: uncovered
- cases: none
- input classes:
  - node-default-bound
  - negated
  - explicit-bounds
  - edge-vs-node
  - whitespace
  - malformed-no-paren
  - malformed-negated-with-bounds
  - malformed-bad-float
- notes: missing-paren input silently misparses; negation and explicit bounds are unreconciled branches
- analysis: docs/analysis/surface/reason-and-state.md

## type:Threshold
- oracle anchor: oracle/pyreason/pyreason/scripts/threshold/threshold.py:1
- status: uncovered
- cases: none
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
- notes: thresh stored unvalidated (negative/overlarge/non-numeric all pass) — corpus hypothesis attached
- analysis: docs/analysis/surface/rules.md

## type:Interval
- oracle anchor: oracle/pyreason/pyreason/scripts/numba_wrapper/numba_types/interval_type.py:13
- status: uncovered
- cases: none
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
- notes: two parallel implementations (jitted + pure-python proxy) whose intersection() prev-bound seeding diverges — differential-worthy
- analysis: docs/analysis/surface/reason-and-state.md

## type:Label
- oracle anchor: oracle/pyreason/pyreason/scripts/numba_wrapper/numba_types/label_type.py:16
- status: uncovered
- cases: none
- input classes:
  - construct
  - equality
  - hash
  - get-value
  - boxing-roundtrip
- notes: equality/hash by string value only — the mechanism behind predicate-map and world lookups
- analysis: docs/analysis/surface/reason-and-state.md

## dsl:rule-text
- oracle anchor: oracle/pyreason/pyreason/scripts/utils/rule_parser.py:17
- status: cased
- cases: hello-world, conv-perfect, conv-delta-interp, conv-delta-bound, persistent-off, persistent-on, inconsistency-ipl-resolve, inconsistency-ipl-override, rule-text-malformed, reason-again-restart-true, reason-again-restart-false, reason-again-no-program, reason-bare-again-no-facts, reset-with-program, reset-no-program, reset-rules-with-program, reset-rules-no-program, reset-settings-restore, edge-rule-frames, store-off-accessors, store-off-atom-trace-flip, fp-version-on, update-mode-default, update-mode-override, update-mode-junk-string, allow-ground-rules-on, allow-ground-rules-off, graph-attr-parsing-on, graph-attr-parsing-off, static-graph-facts-on, static-graph-facts-off, save-graph-attrs-to-trace-on, save-graph-attrs-to-trace-off, canonical-on, canonical-last-write, abort-on-inconsistency-default, abort-on-inconsistency-on, memory-profile-default, memory-profile-on, reverse-digraph-default, reverse-digraph-on, load-graphml-basic, load-graphml-no-attr-parse, graphml-attr-coercions, graphml-empty, output-to-file-default, output-to-file-on, output-file-name-custom, output-file-name-inert, parallel-computing-default, parallel-computing-on, parallel-fp-precedence
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
- status: cased
- cases: hello-world, conv-perfect, conv-delta-interp, conv-delta-bound, persistent-off, persistent-on, inconsistency-ipl-resolve, inconsistency-ipl-override, fact-text-malformed, reason-again-restart-true, reason-again-restart-false, reason-again-no-program, reason-bare-again-no-facts, reset-with-program, reset-no-program, reset-rules-with-program, reset-rules-no-program, reset-settings-restore, edge-rule-frames, store-off-accessors, store-off-atom-trace-flip, fp-version-on, update-mode-default, update-mode-override, update-mode-junk-string, allow-ground-rules-on, allow-ground-rules-off, canonical-on, canonical-last-write, abort-on-inconsistency-default, abort-on-inconsistency-on, memory-profile-default, memory-profile-on, output-to-file-default, output-to-file-on, output-file-name-custom, output-file-name-inert, parallel-computing-default, parallel-computing-on, parallel-fp-precedence
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
- status: cased
- cases: hello-world, conv-perfect, conv-delta-interp, conv-delta-bound, persistent-off, persistent-on, inconsistency-ipl-resolve, inconsistency-ipl-override, reason-again-restart-true, reason-again-restart-false, reason-again-no-program, reason-bare-again-no-facts, reset-with-program, reset-no-program, reset-rules-with-program, reset-rules-no-program, reset-settings-restore, edge-rule-frames, store-off-accessors, store-off-atom-trace-flip, fp-version-on, update-mode-default, update-mode-override, update-mode-junk-string, allow-ground-rules-on, allow-ground-rules-off, graph-attr-parsing-on, graph-attr-parsing-off, static-graph-facts-on, static-graph-facts-off, save-graph-attrs-to-trace-on, save-graph-attrs-to-trace-off, canonical-on, canonical-last-write, abort-on-inconsistency-default, abort-on-inconsistency-on, memory-profile-default, memory-profile-on, reverse-digraph-default, reverse-digraph-on, load-graphml-basic, load-graphml-no-attr-parse, graphml-attr-coercions, graphml-empty, output-to-file-default, output-to-file-on, output-file-name-custom, output-file-name-inert, parallel-computing-default, parallel-computing-on, parallel-fp-precedence
- input classes:
  - default-true-prints
  - nondefault-false-silent
  - forwarded-to-engine
  - type-reject
- notes: print-gating only — reasoning results identical either way
- analysis: docs/analysis/surface/settings.md

## setting:output_to_file
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:94
- status: cased
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
- status: cased
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
- status: cased
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
- status: cased
- cases: abort-on-inconsistency-default, abort-on-inconsistency-on
- input classes:
  - dead-knob
  - type-reject
- notes: dead knob at the pin — in the engine package the name appears only inside _Settings (pyreason.py:49/:70/:118-123/:284-294; zero hits under scripts/, grep-verified session 8); the twin pair's reasoning digests are equal on an inconsistency-triggering program, only the readback differs
- analysis: docs/analysis/surface/settings.md

## setting:memory_profile
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:126
- status: cased
- cases: memory-profile-default, memory-profile-on
- input classes:
  - default-false-direct
  - nondefault-true-profiled
  - interaction-output
  - type-reject
- notes: observational wrapper; interpretation unchanged. interaction-output remains uncovered but is now authorable: the output_file probe (session 10) can read the redirect file, yet under memory_profile the file would carry the run-varying peak-MB line (pyreason.py:1520), and the compare layer's per-probe policy supports only numeric tolerance, not text canonicalization — that recorded-canonicalization decision is the remaining blocker
- analysis: docs/analysis/surface/settings.md

## setting:reverse_digraph
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:134
- status: cased
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
- status: cased
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
- status: cased
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
- status: cased
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
- status: cased
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
- status: cased
- cases: inconsistency-ipl-resolve, inconsistency-ipl-override
- input classes:
  - default-true-resolve
  - nondefault-false-override
  - type-reject
- notes: the true inconsistency governor (contrast the dead abort_on_inconsistency)
- analysis: docs/analysis/surface/settings.md

## setting:static_graph_facts
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:186
- status: cased
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
- status: cased
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
- status: cased
- cases: parallel-computing-default, parallel-computing-on, parallel-fp-precedence
- input classes:
  - default-false-standard
  - nondefault-true-parallel
  - interaction-fp-precedence
  - type-reject
- notes: engine-selection knob; masks fp_version entirely when set (dispatch order at program.py:42-46, pinned behaviorally by parallel-fp-precedence — both knobs true digests the parallel shape, not fp's). The parallel kernel's entire source diff from the serial optimized kernel is the decorator flip parallel=False→True at interpretation_parallel.py:241 (rules loop prange at :571); on the pair's one-rule program (prange width 1 — thread scheduling cannot reorder trace appends) the on-twin digest-equals the default twin on every reasoning probe. Characterization (session 10): the parallel compile took ~174s cold but caches across fresh processes (~3s warm) on numba 0.59.1/darwin — the pinned docstring's no-caching claim (pyreason.py:204-205) is refuted on this machine. Uncovered: type-reject (family-wide); multi-rule prange scheduling (trace order under a prange of width >1 is deliberately unexercised — potential nondeterminism there is its own characterization case)
- analysis: docs/analysis/surface/settings.md

## setting:update_mode
- oracle anchor: oracle/pyreason/pyreason/pyreason.py:212
- status: cased
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
- status: cased
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
- status: cased
- cases: fp-version-on, parallel-fp-precedence
- input classes:
  - default-false-optimized
  - nondefault-true-fp
  - interaction-parallel-precedence
  - type-reject
- notes: selects interpretation_fp; only reachable when parallel_computing is off — the interaction-parallel-precedence class is pinned by parallel-fp-precedence (both knobs true: digests match the parallel shape, and trace-node/nodes-popular do not match fp-version-on's banked fp shape). On identical hello-world inputs the fp engine's final bounds match the optimized engine's but its traces do not (fp-counter values, event order, duplicated atom-trace groundings) and frame row order differs at the last step — a pinned engine-variant asymmetry a single-core rewrite must adjudicate, since one core cannot natively reproduce both knob positions' trace shapes
- analysis: docs/analysis/surface/settings.md
