# Surface analysis — facts and graph loading (pin e1a94af3, v3.6.0)

Input equivalence classes for the fact- and graph-loading public API. Source-only reading of
`oracle/pyreason/pyreason/pyreason.py` and the implementation modules under `scripts/`. Each
`## <kind:id>` section carries `anchor`, `contract`, `input classes`, `notes`. A differential
harness must prove each item over every listed class. Hypotheses seeded from the operator's
`pyreason-analysis` corpus are labelled `hypothesis(...)` and are unverified until a failing
differential case pins them.

Shared vocabulary: a **fact** carries a predicate `Label`, a component (node id string, or a
2-tuple of node ids for an edge), a bound `interval.closed(lower, upper)`, a `[start_time,
end_time]` activity window, and a `static` flag. Facts and the graph are accumulated in
module-global state (`__node_facts`, `__edge_facts`, `__graph`, `__ipl`,
`__closed_world_predicates`, the `__non_fluent_graph_facts_*` / `__specific_graph_*_labels`
grounding tables) and consumed lazily by `reason()` (pyreason.py:1576-1616). `reset()`
(pyreason.py:487) clears facts, graph, name set, and closed-world set but NOT the IPL,
annotation/head functions, or the graph-attribute grounding tables.

---

## fn:load_graphml

`anchor`: pyreason.py:569 (hint exact).

`contract`: Reads a GraphML file at `path` into a networkx `DiGraph` held in `__graph`, then,
when `graph_attribute_parsing` is on, grounds node/edge attributes into the non-fluent
graph-fact tables and specific-label maps; otherwise those tables are left empty.

`input classes`:
- `happy-basic`: valid GraphML path, `graph_attribute_parsing=True` (default) → graph loaded and attributes grounded (pyreason.py:577-581).
- `happy-no-attr-parse`: `graph_attribute_parsing=False` → graph loaded, all four grounding tables emptied (pyreason.py:582-586); no `graph-attribute-fact` facts materialize.
- `interacts-reverse_digraph`: `reverse_digraph=True` reverses every edge direction before grounding (graphml_parser.py:18-19); node ids preserved, edge tuples flipped.
- `interacts-static_graph_facts`: `static_graph_facts` (default True) is passed straight to `parse_graph_attributes` and stamped onto every graph-attribute fact's `static` flag (pyreason.py:581, graphml_parser.py:60/90); False makes them time-windowed at [0,0].
- `bound-empty-graph`: GraphML with zero nodes/edges → empty tables, no error; `parse_graph_attributes` prints "Added 0 ... facts".
- `bound-attr-numeric-in-range`: node/edge attribute numeric (or numeric-string) in [0,1] → treated as lower bound, upper forced to 1 (graphml_parser.py:35-39,65-69).
- `bound-attr-zero-one-edges`: attribute value exactly `0`, `1`, `0.0`, `1.0` → in-range branch (`1 >= value >= 0`), lower=value upper=1.
- `bound-attr-comma-pair`: string attribute of form `"a,b"` that `int()`-parses to a [0,1] pair → both bounds taken from the pair, label reset to bare key (graphml_parser.py:44-55,74-85).
- `malformed-attr-comma-float`: string attribute like `"0.3,0.7"` → `int("0.3")` raises, caught and swallowed (graphml_parser.py:54-55/84-85), so the pair path is skipped and the value falls to the numeric-single or `key-value` label branch. `hypothesis(graphml_parser_validation: int-not-float on comma bound)`.
- `malformed-attr-out-of-range`: numeric attribute outside [0,1] (e.g. `1.5`, `-0.2`, `7`) → NOT caught by the range guard, silently falls through to `label_str = f'{key}-{value}'` with bound [1,1] (graphml_parser.py:40-43). `hypothesis(graphml_parser_validation: out-of-range numeric should warn-and-skip)`.
- `malformed-attr-nonnumeric`: non-numeric string attribute → builds label `f'{key}-{value}'`, bound [1,1] (graphml_parser.py:40-43,70-73); no validation that the composed label matches predicate regex. `hypothesis(graphml_parser_validation: composed label may contain illegal chars)`.
- `malformed-attr-inverted-pair`: an in-range but INVERTED integer comma pair (`'1,0'`) — no ordering check on the pair branch (graphml_parser.py:44-55), so the out-of-order bound rides into the inconsistency machinery at application: no t=0 observable anywhere, later facts on the label never stick, the node filter shows the frozen inverted [1,0] from t=1 while the edge side resolves to [0,1] with visible resolve rows — the node/edge asymmetry (slice-5 review O1 / batch §B23; case graphml-static-pin). `hypothesis(graphml_parser_validation: inverted pair should raise or normalize)`.
- `bound-attr-whitespace-pair`: the comma-pair arm tolerates whitespace the numeric-string arm rejects — `int()` strips spaces (graphml_parser.py:48-49), so `'1, 1'` becomes the [1,1] bound under the bare key while `'0, 1'` and `'-0,1'` (`int('-0')` = 0) coerce to the vacuous [0,1] and vanish (slice-5 review O2 / batch §B24; case graphml-static-pin).
- `malformed-missing-file`: nonexistent path → `nx.read_graphml` raises (uncaught by pyreason).
- `malformed-bad-graphml`: malformed/non-GraphML content → networkx parse error propagates uncaught.

`notes`: Mutates five module globals (pyreason.py:574). Grounding tables persist across
`reset()` (reset() does not clear `__non_fluent_graph_facts_*` / `__specific_graph_*_labels`),
so a second `load_graphml`/`load_graph` overwrites them but a bare `reset()` then `reason()`
re-injects the previous graph's attribute facts. `parse_graph_attributes` unconditionally
`print`s a summary line regardless of `settings.verbose`. Reads `settings.reverse_digraph`,
`settings.graph_attribute_parsing`, `settings.static_graph_facts` at call time, so setting
changes after the call have no effect on the already-grounded tables.

---

## fn:load_graph

`anchor`: pyreason.py:589 (hint exact).

`contract`: Loads an in-memory networkx graph into `__graph` (coerced to `DiGraph`) and runs
the same attribute-grounding path as `load_graphml`.

`input classes`:
- `happy-digraph`: `nx.DiGraph` input, `graph_attribute_parsing=True` → loaded and grounded (pyreason.py:599-603).
- `happy-no-attr-parse`: `graph_attribute_parsing=False` → grounding tables emptied (pyreason.py:604-608).
- `interacts-static_graph_facts`: same static-flag stamping as load_graphml (pyreason.py:603).
- `bound-undirected-input`: `nx.Graph`/`MultiGraph` passed → `nx.DiGraph(graph)` coerces it, materializing a directed edge per undirected edge (graphml_parser.py:24); differs from load_graphml which reads from disk.
- `bound-empty-graph`: graph with no nodes/edges → empty tables.
- `bound-attr-numeric-in-range` / `bound-attr-comma-pair` / `malformed-attr-out-of-range` / `malformed-attr-nonnumeric`: identical attribute-grounding classes as load_graphml (same `parse_graph_attributes`), driven by attributes already on the in-memory graph.
- `divergence-no-reverse`: unlike `load_graphml`, `load_graph` does NOT consult `settings.reverse_digraph` (graphml_parser.py:23-25 never reverses); a `reverse_digraph=True` session reverses GraphML-loaded graphs but not `load_graph` graphs. `hypothesis(reverse_digraph asymmetry between the two loaders)`.

`notes`: Same five module globals mutated (pyreason.py:596). Because `load_graph` skips the
reverse step, `reverse_digraph` becomes a load-path-dependent knob — a named interaction a
harness must cover on both loaders. `nx.DiGraph(graph)` silently drops parallel edges from a
`MultiGraph`.

---

## fn:load_inconsistent_predicate_list

`anchor`: pyreason.py:611 (hint exact).

`contract`: Parses a YAML IPL file into `__ipl`, a numba list of `(Label, Label)` predicate
pairs used for inconsistency resolution during reasoning.

`input classes`:
- `happy-basic`: YAML with `ipl:` mapping to a list of 2-element pairs → each pair appended as `(Label, Label)` (yaml_parser.py:192-194).
- `bound-ipl-null`: `ipl:` present but null → guarded, returns empty list (yaml_parser.py:192).
- `bound-ipl-empty-list`: `ipl: []` → loop body never runs, empty IPL.
- `malformed-missing-ipl-key`: YAML lacking the top-level `ipl` key → `ipl_yaml['ipl']` raises `KeyError` (uncaught; yaml_parser.py:192).
- `malformed-short-pair`: a pair with fewer than 2 entries → `labels[1]` raises `IndexError` (yaml_parser.py:194).
- `malformed-missing-file`: nonexistent path → `open` raises `FileNotFoundError`.
- `malformed-bad-yaml`: non-YAML/invalid content → `yaml.safe_load` raises.

`notes`: Overwrites `__ipl` wholesale (pyreason.py:616-617) — not additive, unlike
`add_inconsistent_predicate`. `reset()` does NOT clear `__ipl`, so an IPL survives across
reasoning runs. Pairs longer than 2 silently ignore extra entries (only `labels[0]`,
`labels[1]` read).

---

## fn:add_inconsistent_predicate

`anchor`: pyreason.py:620 (hint exact).

`contract`: Appends a single `(Label(pred1), Label(pred2))` inconsistent pair to `__ipl`,
lazily initializing the list if empty.

`input classes`:
- `happy-basic`: two predicate name strings → lazily-init list, pair appended (pyreason.py:627-629).
- `interacts-additive-after-yaml`: called after `load_inconsistent_predicate_list` → appends to the existing `__ipl` (no re-init since not None), stacking file + programmatic pairs.
- `bound-same-predicate`: `pred1 == pred2` → self-inconsistent pair appended with no dedup/validation.
- `bound-duplicate-pair`: same pair added twice → both appended, no dedup.
- `malformed-empty-string`: `''` predicate → `Label('')` constructed with no validation at this layer.
- `malformed-non-str`: non-string arg → passed straight into `Label(...)`; behavior depends on `Label` accepting it.

`notes`: Lazily initializes `__ipl` only when None (pyreason.py:627), so it composes with a
prior `load_inconsistent_predicate_list` but a subsequent `load_...` overwrites everything
added here. No character validation on predicate names at this boundary (contrast the fact
parser's `_validate_predicate`). Survives `reset()`.

---

## fn:add_closed_world_predicate

`anchor`: pyreason.py:1122 (hint exact).

`contract`: Registers a predicate name in the module-global `__closed_world_predicates` set;
at reason() time each becomes a `Label` and any node/edge where that predicate is still
`[0,1]` (unknown) is treated as `[0,0]` (false) during rule satisfaction.

`input classes`:
- `happy-basic`: predicate name string → added to set (pyreason.py:1130); converted to `Label` at reason() (pyreason.py:1614-1617).
- `bound-duplicate`: same name added twice → set dedups, single entry.
- `bound-empty-string`: `''` → added; becomes `Label('')` at reason().
- `malformed-non-str`: non-hashable/non-string arg → `set.add` may raise (non-hashable) or store an odd key that fails at `Label(...)` conversion during reason().
- `interacts-unknown-predicate`: name never appearing in graph/rules → added but inert (no node/edge carries it).
- `interacts-reset`: after `reset()` the set is cleared (pyreason.py:497), unlike IPL/functions — a named lifecycle difference.

`notes`: The only fact/graph-group item that `reset()` actively clears alongside facts
(pyreason.py:491-497). Effect is deferred to reason(): registration does not validate the name
against loaded predicates. Conversion to numba `Label` list happens lazily
(pyreason.py:1613-1617), so a malformed entry surfaces at reason() time, not at add time.

---

## fn:add_fact

`anchor`: pyreason.py:1133 (hint exact).

`contract`: Appends an already-constructed `Fact` object to `__node_facts` or `__edge_facts`
by its `.type`, auto-naming unnamed facts and warning on duplicate names.

`input classes`:
- `happy-node`: `Fact` with `type=='node'` → appended to `__node_facts` via `fact_node.Fact(...)` (pyreason.py:1146-1155).
- `happy-edge`: `Fact` with `type=='edge'` → appended to `__edge_facts` via `fact_edge.Fact(...)` (pyreason.py:1156-1165).
- `bound-unnamed`: `fact.name is None` → auto-named `fact_{len(node)+len(edge)}` (pyreason.py:1147-1148,1157-1158); counter spans both lists.
- `interacts-duplicate-name`: name already in `__facts_name_set` → `warnings.warn` about ambiguous trace but the fact is STILL appended (pyreason.py:1150-1151,1160-1161).
- `bound-lazy-init`: first call with both lists None → both lazily created (pyreason.py:1141-1144).
- `interacts-name-counter-mixing`: interleaving node and edge adds → auto-name indices reflect combined length, so names are order-sensitive across the two lists.
- `malformed-static-window`: `static=True` with nonzero start/end → static overrides the window downstream (Fact stores both; static wins at reasoning).

`notes`: Mutates `__node_facts`, `__edge_facts`, `__facts_name_set` (pyreason.py:1139,1154,
1164). Duplicate names warn but do not dedup — the fact list can hold same-named facts.
Auto-name counter uses combined list length, making generated names sensitive to node/edge
interleaving order. `reset()` sets the fact lists to None and clears the name set. The `Fact`
is re-wrapped into a numba `fact_node`/`fact_edge` at add time (pyreason.py:1153,1163), reading
`.component`, `.pred`, `.bound`, `.start_time`, `.end_time`, `.static`.

---

## fn:add_fact_from_json

`anchor`: pyreason.py:1168 (hint exact).

`contract`: Reads a JSON array of fact objects, validates per-item params, constructs each via
the `Fact(fact_text=...)` text path, and calls `add_fact`; `raise_errors` toggles fail-fast
vs. warn-and-skip.

`input classes`:
- `happy-basic`: JSON array of objects each with `fact_text` (+ optional name/start/end/static) → each parsed and added (pyreason.py:1232-1276).
- `bound-empty-array`: `[]` → warns "empty array, no facts loaded", returns (pyreason.py:1222-1224).
- `bound-defaults`: object with only `fact_text` → start/end default 0, static False, name None (pyreason.py:1256-1258).
- `malformed-not-array`: top-level JSON not a list → `ValueError` "must contain an array" (pyreason.py:1219-1220).
- `malformed-item-not-object`: array element not a dict → raise or warn-skip per `raise_errors` (pyreason.py:1234-1239).
- `malformed-missing-fact_text`: missing/blank `fact_text` → raise or warn-skip (pyreason.py:1242-1248).
- `malformed-bad-fact_text`: `fact_text` failing the DSL parser → `ValueError` wrapped "Failed to parse fact" (pyreason.py:1278-1282).
- `malformed-nonint-time`: non-integer `start_time`/`end_time` → `int()` fails, raise or warn-and-default (helper pyreason.py:1099-1114); note default end_time falls back to start_time on error.
- `interacts-static_field`: `static` accepts True/False, 1/0, yes/no/t/f/y/n and case-insensitive strings via `_parse_bool_param` (pyreason.py:706-720); invalid string raises or defaults False.
- `interacts-duplicate-name-intrafile`: two items sharing a `name` → second raises or warn-skips as duplicate (pyreason.py:1264-1269) — this dedup is stricter than `add_fact`, which only warns.
- `malformed-missing-file`: nonexistent path → `FileNotFoundError` (pyreason.py:1212-1213).
- `malformed-bad-json`: invalid JSON syntax → `ValueError` "Invalid JSON format" (pyreason.py:1214-1215).

`notes`: `float`/`int` time coercion goes through the shared `_parse_and_validate_fact_params`
(pyreason.py:1080-1119); on invalid `end_time` the default is `start_time`, not 0 — a silent
coercion. Intra-file name uniqueness is enforced here (`loaded_name_set`) but does NOT consult
the global `__facts_name_set`, so a name unique within the file can still collide with a
previously-added fact (only warned by `add_fact`). ALWAYS `print`s a load summary regardless of
`settings.verbose` (pyreason.py:1290-1292) — differs from the CSV loader. `raise_errors`
defaults True.

---

## fn:add_fact_from_csv

`anchor`: pyreason.py:1294 (hint exact).

`contract`: Reads a CSV (no assumed header; all cells as strings) of up to 5 columns
`fact_text,name,start_time,end_time,static`, optionally skipping an exact header row, and adds
each row as a fact through the `Fact(fact_text=...)` path.

`input classes`:
- `happy-basic`: rows of `fact_text[,name,start,end,static]` → each parsed and added (pyreason.py:1359-1395).
- `happy-header`: first row exactly `fact_text,name,start_time,end_time,static` → skipped as header (pyreason.py:1348-1351).
- `bound-header-mismatch`: near-header first row (any deviation) → treated as a DATA row and likely raises on parse (pyreason.py:1350, docstring 1312).
- `bound-short-rows`: fewer than 5 columns → missing trailing columns treated as None via `len(row) >` guards (pyreason.py:1374-1377); e.g. `Viewed(Eve),,,,` yields name None, times 0, static False.
- `bound-empty-file`: completely empty file → `EmptyDataError`/`df.empty` warns "empty, no facts loaded", returns (pyreason.py:1336-1345).
- `malformed-missing-fact_text`: blank column 0 → raise or warn-skip (pyreason.py:1362-1367).
- `malformed-bad-fact_text`: column-0 text failing the DSL parser → wrapped `ValueError` (pyreason.py:1397-1401).
- `malformed-nonint-time`: non-integer time cell → coerce-or-default via helper (pyreason.py:1099-1114).
- `interacts-static_field`: static cell parsed by `_parse_bool_param` (True/1/yes/t/y etc.); empty string → default False (pyreason.py:712-713).
- `interacts-quoted-commas`: quoted `fact_text` containing a comma, e.g. `"HaveAccess(a,b)"` or `"Processed(N):[0.5,0.8]"` → pandas keeps it as one field so edge/interval facts survive CSV splitting (docstring 1319-1320).
- `malformed-ragged-wide-row`: a data row with MORE fields than the first row → the pandas C tokenizer fails the whole read ("Error tokenizing data. C error: Expected N fields in line L, saw M"; L is the record ordinal), wrapped as the loader's 'Error reading CSV file' ValueError — nothing loads from that file (pyreason.py:1340-1341; case fact-csv-ragged).
- `bound-ragged-first-row-wide`: when the FIRST row is the widest it fixes the field count — its extra trailing columns beyond the 5 the loader reads are silently ignored, and later narrower rows are padded with `''` (keep_default_na=False), taking the short-row defaults (case fact-csv-ragged).
- `interacts-duplicate-name-intrafile`: duplicate `name` across rows → raise or warn-skip (pyreason.py:1383-1388).
- `malformed-missing-file`: nonexistent path → `FileNotFoundError` (pyreason.py:1334-1335).

`notes`: Reads with `header=None, dtype=str, keep_default_na=False` (pyreason.py:1333) so every
cell is a string and blanks stay `''` rather than NaN — the coercion helpers rely on this.
Row indices in messages are `idx+1` (pyreason.py:1364). Unlike the JSON loader, the summary
`print` is gated on `settings.verbose` (pyreason.py:1409-1412). Header detection is an exact
list match after `.strip()` — a reordered or extra-column header silently becomes a data row.
Same intra-file-only name-uniqueness caveat as JSON (no cross-check against global
`__facts_name_set`). `raise_errors` defaults True.

---

## type:Fact

`anchor`: scripts/facts/fact.py:5 (class `Fact`; `__init__` at :6).

`contract`: Constructs an in-memory fact from a `fact_text` DSL string plus optional
name/start/end/static, delegating text parsing to `fact_parser.parse_fact` and wrapping the
predicate in a `Label`; the resulting object is what `add_fact` consumes.

`input classes`:
- `happy-node`: `'pred(subject)'` → `type='node'`, component is the bare id string, bound defaults `[1,1]` (fact.py:58-66, fact_parser.py:62-67,122-123).
- `happy-edge`: `'pred(a,b)'` → `type='edge'`, component is a 2-tuple (fact_parser.py:108-120).
- `happy-explicit-bound`: `'pred(x):[0.5,0.8]'` → interval bound parsed (fact_parser.py:130-168).
- `happy-boolean-bound`: `'pred(x):True'`/`':False'` (case-insensitive) → `[1,1]`/`[0,0]` (fact_parser.py:126-129).
- `happy-negation`: `'~pred(x)'` → bound `[0,0]` (fact_parser.py:63-65).
- `bound-negated-boolean`: `'~pred(x):True'` → flips to False, `'~pred(x):False'` → True (fact_parser.py:53-58).
- `bound-negated-interval`: `'~pred(x):[0.2,0.8]'` → `[1-upper,1-lower]` rounded to 10 places (fact_parser.py:60,164-168).
- `bound-interval-endpoints`: `[0,0]`, `[1,1]`, `[0,1]` → accepted (inclusive range checks fact_parser.py:154-157).
- `bound-underscore-predicate`: `'_Internal(x)'`, digits/dots/hyphens in predicate → allowed by `_PREDICATE_RE` (fact_parser.py:4).
- `bound-component-leading-digit`: component starting with a digit, or containing `@`/`.`/`-` → allowed by `_COMPONENT_RE` (fact_parser.py:5) even though predicates may not start with a digit.
- `param-static-flag`: `static=True` → start/end ignored downstream (fact.py:55, docstring).
- `param-times`: explicit `start_time`/`end_time` stored verbatim (no validation at this layer; fact.py:60-61).
- `malformed-empty-text`: `''`/whitespace → `ValueError` "cannot be empty" (fact_parser.py:30-31).
- `malformed-predicate-leading-digit`: `'123pred(x)'` → `ValueError` (fact_parser.py:13-14).
- `malformed-predicate-badchar`: `'Pred@name(x)'` → `ValueError` (fact_parser.py:12-16).
- `malformed-arity`: `'pred(a,b,c)'` → `ValueError` "exactly 2 components" (fact_parser.py:113-114).
- `malformed-out-of-range`: `'pred(x):[1.5,2.0]'` → `ValueError` out-of-range (fact_parser.py:154-157).
- `malformed-inverted-interval`: lower > upper → `ValueError` (fact_parser.py:160-161).
- `malformed-double-negation`: `'~~pred(x)'` → `ValueError` (fact_parser.py:41-42).
- `malformed-multi-colon`: more than one `:` → `ValueError` (fact_parser.py:37-38).

`notes`: All heavy validation lives in the DSL parser (see `dsl:fact-text`); the class itself
does no validation of name/time/static and stores them raw (fact.py:59-62). `name` defaults
None (auto-named later by `add_fact`). Whitespace inside `fact_text` is stripped globally
(`f.replace(' ', '')`, fact_parser.py:33) before parsing, so `'pred( x , y )'` normalizes to
`'pred(x,y)'`. Negated intervals round to 10 decimals to avoid float drift (fact_parser.py:166).
`.component` type is polymorphic: `str` for nodes, `tuple` for edges — downstream `add_fact`
branches on `.type`, not on the component type.

---

## dsl:fact-text

`anchor`: scripts/utils/fact_parser.py:28 (`parse_fact`; regexes at :4-5, validators at :8-24).

`contract`: The fact-text mini-language: parses `Predicate(component)` optionally with a `~`
negation prefix and a `:bound` suffix into `(pred, component, interval, fact_type)`; raises
`ValueError` on any malformed input.

`input classes`:
- `happy-node-default-true`: `'Pred(n)'` → bound `[1,1]`, node (fact_parser.py:62-67,126-127).
- `happy-edge`: `'Pred(a,b)'` → 2-tuple component, edge (fact_parser.py:108-120).
- `happy-explicit-true-false`: `':True'`/`':False'` any case → `[1,1]`/`[0,0]` (fact_parser.py:126-129).
- `happy-interval`: `':[l,u]'` with `0<=l<=u<=1` → `interval.closed(l,u)` (fact_parser.py:130-168).
- `dsl-whitespace-insensitive`: any embedded spaces removed before parse (fact_parser.py:33) — `'Pred ( a , b ) : [0.1, 0.9]'` valid.
- `dsl-negation-node`: leading `~` no bound → `[0,0]` (fact_parser.py:63-65).
- `dsl-negation-boolean-flip`: `~...:True`→False, `~...:False`→True (fact_parser.py:53-58).
- `dsl-negation-interval-complement`: `~...:[l,u]` → `[round(1-u,10),round(1-l,10)]` (fact_parser.py:60,164-168).
- `bound-predicate-charset`: predicate must match `^[a-zA-Z_][a-zA-Z0-9_.\-]*$` — underscore/digit/dot/hyphen allowed after first char, first char letter or `_` only (fact_parser.py:4,8-16).
- `bound-component-charset`: component must match `^[a-zA-Z0-9_][a-zA-Z0-9_.@\-]*$` — may start with a digit and may contain `@` (fact_parser.py:5,19-24); strictly wider than the predicate charset.
- `bound-interval-endpoints`: `[0,0]`, `[1,1]`, `[0,1]`, `[0.5,0.5]` → accepted (inclusive; fact_parser.py:154-160).
- `malformed-empty`: empty/whitespace-only → `ValueError` (fact_parser.py:30-31).
- `malformed-double-negation`: `'~~...'` → `ValueError` (fact_parser.py:41-42).
- `malformed-multi-colon`: `>1` colon → `ValueError` (fact_parser.py:37-38).
- `malformed-empty-predcomp`: bare `~` or empty before `:` → `ValueError` (fact_parser.py:70-71).
- `malformed-no-parens`: missing `(` or `)` → `ValueError` (fact_parser.py:74-77).
- `malformed-paren-count`: not exactly one `(` and one `)` → `ValueError` (fact_parser.py:80-83).
- `malformed-paren-order`: `)` before `(`, or `)` not at end → `ValueError` (fact_parser.py:86-93).
- `malformed-empty-component`: `'Pred()'` → `ValueError` "Component cannot be empty" (fact_parser.py:104-105).
- `malformed-edge-arity`: `>2` comma-separated components → `ValueError` "exactly 2" (fact_parser.py:113-114).
- `malformed-empty-edge-component`: `'Pred(a,)'`/`'Pred(,b)'` → per-component validation raises "cannot be empty" (fact_parser.py:117-118,21-22).
- `malformed-predicate-leading-digit`: predicate first char a digit → dedicated digit `ValueError` (fact_parser.py:13-14).
- `malformed-predicate-badchar`: predicate with `@`, space (post-strip impossible), etc. → charset `ValueError` (fact_parser.py:15-16).
- `malformed-interval-no-brackets`: bound not starting `[` or not ending `]` → `ValueError` (fact_parser.py:132-135).
- `malformed-interval-empty`: `':[]'` → `ValueError` "cannot be empty" (fact_parser.py:139-140).
- `malformed-interval-arity`: not exactly 2 comma values → `ValueError` (fact_parser.py:144-145).
- `malformed-interval-nonnumeric`: non-float interval value → `ValueError` wrapping the float error (fact_parser.py:147-150).
- `malformed-interval-out-of-range`: value <0 or >1 → `ValueError` (fact_parser.py:154-157).
- `malformed-interval-inverted`: lower > upper → `ValueError` (fact_parser.py:160-161).

`notes`: `f.replace(' ', '')` (fact_parser.py:33) strips ALL spaces, so a component or
predicate can never contain a space and spacing is never significant — a normalization the
harness must not assume is character-preserving. Only bare `true`/`false` (case-insensitive)
select the boolean branch; anything else routes to the interval branch and must be
bracket-delimited. Negated intervals are the sole place rounding occurs (10 places,
fact_parser.py:166). Predicate and component charsets DIFFER: components allow a leading digit
and `@`; predicates do not — a class author must not reuse one charset for the other. The
parser raises (never warns); the graphml attribute path deliberately reuses these regexes but
is specified to warn-and-skip instead — see `hypothesis(graphml_parser_validation)` notes on
`fn:load_graphml`.
