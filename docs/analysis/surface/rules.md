# Input equivalence classes — rules surface

Pin `e1a94af3` (v3.6.0). API module `oracle/pyreason/pyreason/pyreason.py`; parser
`oracle/pyreason/pyreason/scripts/utils/rule_parser.py`. Source-read only.

Class-ids cite `file:line` where a source branch creates the class. Hypotheses from the
operator's analysis corpus are labelled `hypothesis(...)` and are unverified.

---

## fn:add_rule

**anchor**: `pyreason.py:632` (hint correct).

**contract**: Appends an already-constructed `Rule`'s inner numba rule object to the
module-global `__rules` list, auto-naming it `rule_<len>` when unnamed and warning on a
duplicate name.

**input classes**:
- `happy-basic`: first `Rule` added to an empty engine; `__rules` is `None` and is
  lazily allocated as a numba typed list (`pyreason.py:638-639`).
- `happy-named`: rule carries an explicit name from its constructor; name is recorded in
  `__rules_name_set` (`pyreason.py:648`).
- `bound-unnamed-autoname`: rule name is `None`; engine assigns `rule_{len(__rules)}`
  (`pyreason.py:642-643`) — index is position-dependent, so ordering of `add_rule` calls
  changes generated names.
- `malformed-duplicate-name`: name already in `__rules_name_set`; warns (does not raise or
  dedupe) and still appends, producing an ambiguous trace (`pyreason.py:645-649`).
- `interacts-append-order`: two rules with the same auto-name collision can occur if one is
  explicitly named `rule_0` and another is auto-named `rule_0` — warn-only.
- `interacts-reset`: `reset_rules`/`reset` clears `__rules`, `__rules_name_set`
  (`pyreason.py:522-525`); auto-naming counter effectively restarts.

**notes**: Mutates module globals `__rules` and `__rules_name_set`. No parsing here — all
validation already happened in the `Rule` constructor. Duplicate names are never rejected,
only warned. The `reorder_clauses` optimization is applied later inside `_reason`
(`pyreason.py:1598-1606`), not here.

---

## fn:add_rules_from_file

**anchor**: `pyreason.py:652` (hint correct).

**contract**: Reads a text file, treats each non-empty non-`#` line as one rule-text DSL
string, constructs a `Rule(line, f'rule_{i+offset}', infer_edges)` per line and adds it;
`raise_errors` toggles raise-vs-warn-and-skip on a parse failure.

**input classes**:
- `happy-multi-rule`: several valid rule lines; each parsed and appended, `loaded_count`
  incremented (`pyreason.py:676-679`).
- `happy-comments-and-blanks`: lines that are empty after `rstrip()` or whose first char is
  `#` are filtered out before parsing (`pyreason.py:670`).
- `bound-empty-file`: no surviving lines → loop runs zero times, nothing added.
- `bound-name-offset`: generated names are `rule_{i+rule_offset}` where `rule_offset` is the
  current `len(__rules)` (`pyreason.py:675`,`678`) — names depend on rules already loaded,
  and collide with `add_rule`'s own auto-naming scheme.
- `malformed-line-raise`: a line fails to parse and `raise_errors=True` → `ValueError`
  wrapping line number and text (`pyreason.py:681-682`); loading stops.
- `malformed-line-skip`: same failure with `raise_errors=False` (default) → warn, increment
  `error_count`, continue (`pyreason.py:683-684`).
- `malformed-missing-file`: `open` raises `FileNotFoundError` (uncaught here; propagates).
- `interacts-infer_edges`: the single `infer_edges` flag is applied uniformly to every line
  (`pyreason.py:678`); node rules silently ignore it (parser forces False, see dsl item).
- `interacts-verbose`: `settings.verbose` gates the load/error summary print
  (`pyreason.py:686-689`).
- `bound-inline-comma`: a rule line containing a comment-like `#` mid-line is NOT stripped
  (only first-char `#` filters); commas inside the line are handled by the DSL splitter, but
  there is no CSV-style quoting here.

**notes**: A `#` only comments a line when it is the very first character; leading whitespace
before `#` defeats the filter because `rstrip` only trims the right side. `raise_errors`
default is `False` here (unlike CSV/JSON which default `True`).

---

## fn:add_rule_from_csv

**anchor**: `pyreason.py:753` (hint correct).

**contract**: Reads a CSV (all cells as strings, NA-preservation off) whose columns are
`rule_text, name, infer_edges, set_static`, optionally skipping an exact header row, and
adds one `Rule` per data row; `raise_errors` (default `True`) toggles raise-vs-warn-skip.

**input classes**:
- `happy-full-row`: all four columns present and valid (`pyreason.py:824-848`).
- `happy-minimal-row`: only `rule_text`; missing optional columns default to
  `None`→`False`/no-name (`pyreason.py:829-834`,`704-705`).
- `happy-header-present`: first row exactly equals `['rule_text','name','infer_edges',
  'set_static']` → skipped (`pyreason.py:803-806`).
- `malformed-header-mismatch`: a header row that is not an exact match is treated as a data
  row and likely fails rule parsing (`pyreason.py:805`).
- `malformed-missing-rule_text`: empty column 0 → raise or warn-skip
  (`pyreason.py:817-822`).
- `malformed-empty-file`: `pd.errors.EmptyDataError` or `df.empty` → warn and return, no
  raise (`pyreason.py:792-800`).
- `malformed-missing-file`: `FileNotFoundError` re-raised with message
  (`pyreason.py:790-791`).
- `malformed-unreadable`: other pandas read exception → `ValueError` (`pyreason.py:795-796`).
- `bound-bool-truthy-strings`: `infer_edges`/`set_static` cells accept
  `true/1/yes/t/y` (True) and `false/0/no/f/n/''` (default) case-insensitively via
  `_parse_bool_param` (`pyreason.py:708-713`).
- `malformed-bool-invalid`: any other bool string → raise or warn+default
  (`pyreason.py:714-718`).
- `bound-numeric-bool`: an int/float cell is coerced with `bool()` (`pyreason.py:719-720`);
  as a string cell from `dtype=str`, this path is unreachable — cells are always strings.
- `malformed-duplicate-name`: a name repeated within the same file → raise or warn-skip via
  a file-local `loaded_name_set` (`pyreason.py:837-844`) — separate from the engine-global
  `__rules_name_set`, so a name colliding with a previously loaded rule is NOT caught here.
- `bound-quoted-commas`: a `rule_text` containing commas must be double-quoted so pandas
  keeps it one cell (docstring `pyreason.py:759-777`).
- `interacts-verbose`: summary print gated on `settings.verbose` (`pyreason.py:862-865`).

**notes**: Reads with `header=None, dtype=str, keep_default_na=False`, so every cell is a
raw string and empty cells are `''` not `NaN`. Row numbers in messages are `idx+1` where
`idx` is the pandas index (header-inclusive), which can be off-by-one relative to the user's
mental line count. `raise_errors` default `True`.

---

## fn:add_rule_from_json

**anchor**: `pyreason.py:868` (hint correct).

**contract**: Parses a JSON array of rule objects (`rule_text` required; optional `name`,
`infer_edges`, `set_static`, `custom_thresholds`, `weights`), builds a `Rule` per object and
adds it; `raise_errors` (default `True`) toggles raise-vs-warn-skip. This is the only loader
exposing `custom_thresholds` and `weights`.

**input classes**:
- `happy-basic`: array of objects with just `rule_text` (`pyreason.py:940-958`).
- `happy-custom-thresholds-list`: `custom_thresholds` is a list of threshold objects, one
  per clause; each built via `Threshold(...)` (`pyreason.py:975-996`).
- `happy-custom-thresholds-dict`: `custom_thresholds` is a `{clause_idx: threshold}` map;
  string keys coerced to int (`pyreason.py:997-1026`); unspecified clauses default later in
  the parser.
- `happy-weights`: `weights` is a numeric list passed through to the parser
  (`pyreason.py:1036-1046`).
- `bound-weights-dtypes`: the list rides into `np.array(weights, dtype=float64)`
  (`rule_parser.py:208-212`), so ints, numeric strings (`"0.5"`), and booleans all
  convert and load (case rule-json-weights-dtypes).
- `bound-weights-nested`: a RECTANGULAR nested numeric list (`[[1,2]]`) converts to a
  2-D array whose `len()` is the top-level row count — it passes a one-clause rule's
  length check and LOADS; contents unobserved at this seam (case
  rule-json-weights-dtypes, weights-nested probe; screened at the pin 2026-07-12).
- `malformed-weights-nonconvertible-entry`: a non-convertible entry (`["heavy"]`, a
  ragged nested list) → the parser's `TypeError` falls past the loader's `ValueError`
  catch into the `except Exception` wrap → `builtins.Exception` "Item i: Unexpected
  error - weights must be a numpy array or convertible to one, got list"
  (`pyreason.py:1068-1072`; case rule-json-weights-dtypes).
- `malformed-not-array`: top-level JSON is not a list → `ValueError` (`pyreason.py:927-928`).
- `bound-empty-array`: empty array → warn and return (`pyreason.py:930-932`).
- `malformed-item-not-object`: an element is not a dict → raise or warn-skip
  (`pyreason.py:942-947`).
- `malformed-missing-rule_text`: absent/blank `rule_text` → raise or warn-skip
  (`pyreason.py:950-956`).
- `malformed-threshold-missing-field`: a threshold object missing `quantifier`/
  `quantifier_type`/`thresh`, or a bad value → `KeyError/ValueError/TypeError` caught, rule
  skipped (`pyreason.py:985-996`,`1015-1026`).
- `malformed-threshold-dict-key`: non-integer dict key → raise or warn-skip
  (`pyreason.py:1001-1007`).
- `malformed-threshold-not-object`: list/dict element not a dict → raise or warn-skip
  (`pyreason.py:991-996`,`1021-1026`).
- `malformed-custom_thresholds-wrong-type`: value neither list nor dict → raise or warn-skip
  (`pyreason.py:1027-1032`).
- `malformed-weights-not-list`: `weights` not a list → raise or warn-skip
  (`pyreason.py:1039-1044`).
- `malformed-invalid-json`: `json.JSONDecodeError` → `ValueError` (`pyreason.py:922-923`).
- `malformed-missing-file`: `FileNotFoundError` re-raised (`pyreason.py:920-921`).
- `malformed-duplicate-name`: name repeated within file via file-local `loaded_name_set`
  (`pyreason.py:1049-1056`) — again not cross-checked against engine-global names.
- `interacts-thresholds-vs-clause-count`: threshold list length or dict max-key are only
  validated downstream in `parse_rule` (`rule_parser.py:156-168`), not here — a mismatch
  surfaces as an item-level parse error.

**notes**: `infer_edges`/`set_static` reuse `_parse_bool_param` and here can be genuine
JSON bools/ints/strings. `custom_thresholds` dict keys are `int()`-coerced from JSON string
keys. `raise_errors` default `True`.

---

## fn:add_annotation_function

**anchor**: `pyreason.py:1415` (hint correct).

**contract**: Registers a user annotation function into the module-global
`__annotation_functions` list after gating its arity to exactly 2 or exactly 6 positional
parameters.

**input classes**:
- `happy-2arg`: `fn(annotations, weights)` → appended (`pyreason.py:1472-1481`).
- `happy-6arg`: `fn(annotations, weights, qualified_nodes, qualified_edges, clause_labels,
  clause_variables)` → appended (`pyreason.py:1430-1446`).
- `malformed-wrong-arity`: any argcount other than 2 or 6 → `TypeError`
  (`pyreason.py:1473-1479`).
- `bound-njit-wrapped`: a `numba.njit` dispatcher is unwrapped via `getattr(function,
  'py_func', function)` before counting args (`pyreason.py:1471`); a plain Python function
  with no `py_func` is measured directly.
- `bound-defaulted-or-varargs`: `co_argcount` counts declared positional params only and
  ignores `*args`/defaults — a `*args` function reports 0 and is rejected
  (`pyreason.py:1472`).
- `interacts-reset`: `reset`/`reset_rules` clears `__annotation_functions`
  (`pyreason.py:524`).
- `interacts-reorder_clauses`: the 6-arg extended contract's per-clause lists follow the
  post-`reorder_clauses` order, so callers must match by predicate+variable role not
  position (docstring `pyreason.py:1448-1451`).

**notes**: The `njit` decoration is NOT enforced (the assertion is commented out,
`pyreason.py:1466`); only arity is checked. Registration is append-only and order-preserving;
functions are referenced by name from rule heads at reasoning time.

---

## fn:add_head_function

**anchor**: `pyreason.py:1484` (hint correct).

**contract**: Appends a user head function to the module-global `__head_functions` list with
no validation.

**input classes**:
- `happy-basic`: any callable → appended (`pyreason.py:1494`).
- `bound-no-validation`: no arity or `njit` gate at all (`pyreason.py:1491-1494`); an invalid
  signature is only discovered inside the reasoning loop.
- `interacts-reset`: `reset`/`reset_rules` clears `__head_functions` (`pyreason.py:525`).
- `interacts-head-fn-in-dsl`: only functions named in a rule head (`f(X, Y)` form, parsed
  into `head_fns`) actually invoke this registry; an unreferenced registration is inert.

**notes**: Unlike `add_annotation_function`, there is no arity check here — the two sibling
registrars are asymmetric. Append-only, order-preserving, mutates module global.

---

## type:Rule

**anchor**: `scripts/rules/rule.py:4` (class); constructor `rule.py:11`.

**contract**: Thin user-facing wrapper whose `__init__` immediately delegates to
`rule_parser.parse_rule(rule_text, name, custom_thresholds, infer_edges, set_static,
weights)` and stores the resulting numba rule object on `self.rule`.

**input classes**:
- `happy-text-only`: `Rule(rule_text)` with all else defaulted — `name=None`,
  `infer_edges=False`, `set_static=False`, `custom_thresholds=None`, `weights=None`
  (`rule.py:11`).
- `happy-full-args`: every keyword supplied; all forwarded verbatim to `parse_rule`
  (`rule.py:22`).
- `bound-param-order-swap`: constructor signature order is `(rule_text, name, infer_edges,
  set_static, custom_thresholds, weights)` but it calls `parse_rule` with args reordered to
  `(rule_text, name, custom_thresholds, infer_edges, set_static, weights)` (`rule.py:22`) —
  positional misuse is a live footgun; the mapping is only correct because it is explicit.
- `interacts-all-dsl-classes`: every malformed/boundary class enumerated under
  `dsl:rule-text` propagates through this constructor unchanged (it adds no validation).
- `interacts-custom_thresholds-list-vs-dict`: forwarded as-is; list vs dict semantics
  resolved in `parse_rule` (`rule_parser.py:156-179`).
- `interacts-weights`: forwarded as-is; validated in `parse_rule` (`rule_parser.py:203-230`).

**notes**: `Rule` holds NO state beyond `self.rule`; it does no validation itself. The
public `pyreason.Rule` re-exports this class. Construction is where all parse-time errors are
raised, so a differential harness should exercise the DSL classes through `Rule(...)`
directly.

---

## type:Threshold

**anchor**: `scripts/threshold/threshold.py:1` (class); constructor `threshold.py:14`.

**contract**: Value object holding `(quantifier, quantifier_type, thresh)` for a clause
threshold, validating the quantifier and quantifier-type strings at construction and
exposing `to_tuple()` for numba conversion.

**input classes**:
- `happy-number-total`: e.g. `Threshold('greater_equal', ('number','total'), 1)`
  (`threshold.py:24-32`).
- `happy-percent-available`: any valid combination of the enumerated members.
- `bound-all-quantifiers`: `greater_equal`, `greater`, `less_equal`, `less`, `equal`
  accepted (`threshold.py:24`).
- `malformed-bad-quantifier`: any other quantifier string → `ValueError("Invalid
  quantifier")` (`threshold.py:24-25`).
- `malformed-bad-quantifier-type`: `quantifier_type[0]` not in `{number,percent}` or
  `quantifier_type[1]` not in `{total,available}` → `ValueError` (`threshold.py:27-28`).
- `malformed-quantifier-type-shape`: `quantifier_type` given as a string (e.g.
  `'number'`) indexes characters `[0]`/`[1]` (`'n'`,`'u'`) and fails the membership check;
  a length-1 tuple raises `IndexError` at `[1]` (`threshold.py:27`).
- `bound-thresh-unvalidated`: `thresh` is stored with NO validation
  (`threshold.py:32`) — negatives, floats, values `>` clause count, non-numerics all pass.
  `hypothesis(BUG-negative-thresh)`: absolute counts should reject negative `thresh`
  (`BUG_LOG.md:528,548-550`).
- `interacts-to_tuple`: `to_tuple()` returns the raw stored triple
  (`threshold.py:41`); `thresh` is later coerced to `float64` when appended in the parser
  (`rule_parser.py:148,160,171`).
- `interacts-forall`: the parser synthesizes `Threshold('greater_equal',('percent','total'),
  100)` for `forall(...)` clauses (`rule_parser.py:81`).

**notes**: `quantifier_type` is expected to be a 2-tuple but only its `[0]`/`[1]` are
checked; extra elements are silently ignored. No coupling of `thresh` to `quantifier_type`
(a `percent` threshold of `500` is accepted). Immutable in practice (no setters).

---

## dsl:rule-text

**anchor**: parser entry `scripts/utils/rule_parser.py:17` (`parse_rule`); the DSL is the
`rule_text` string it consumes.

**contract**: Parses a `head <- body` rule string into a numba `Rule`: strips all spaces,
splits on a single `<-`, extracts an optional leading integer `delta_t` (the `<-N` timestep
offset), splits the body into predicate clauses with intervals/negation/comparison operators,
resolves the head predicate, bound-or-annotation-function, and head negation/functions, and
attaches per-clause thresholds and weights.

**input classes**:

Entry / structure
- `happy-node-rule`: `head(X) <- body(X)` single head var → `rule_type='node'`
  (`rule_parser.py:109`).
- `happy-edge-rule`: two head vars → `rule_type='edge'` (`rule_parser.py:109`).
- `malformed-non-string`: `rule_text` not `str` → `TypeError` (V1, `rule_parser.py:20-21`).
- `malformed-empty`: empty/whitespace-only → `ValueError` (V2, `rule_parser.py:24-25`).
- `malformed-arrow-count`: zero or ≥2 `<-` → `ValueError` (V3, `rule_parser.py:28-33`).
- `malformed-empty-head`: nothing before `<-` → `ValueError` (V4, `rule_parser.py:42-43`).
- `happy-empty-body`: nothing after `<-` → unconditional rule, `delta_t=0`, no clauses
  (`rule_parser.py:46-49`).
- `bound-whitespace-collapse`: all spaces removed before parsing
  (`rule_parser.py:36`), so `pred(A, B)` and `pred(A,B)` are identical; spaces inside names
  are impossible.

delta_t / timestep
- `happy-delta-t`: body begins with digits, e.g. `head(X) <-2 body(X)` → `delta_t=2`,
  digits consumed (`rule_parser.py:52-64`).
- `bound-zero-delta-default`: no leading digits → `delta_t=0` (`rule_parser.py:61-62`).
- `bound-delta-t-uint16`: `delta_t` cast `numba.types.uint16(delta_t)` at
  `rule_parser.py:243`. `hypothesis(BUG-057)`: values `>65535` wrap silently
  (`BUG_LOG.md:1921-1938`).
- `malformed-multichar-delta`: multiple leading digits are all consumed as one integer
  (`rule_parser.py:54-59`), so `<-10body` is `delta_t=10`, not `1` + `0body`.

Body clause splitting
- `happy-multi-clause`: comma-separated clauses split via the double-`)`/`]` trick
  (`rule_parser.py:277-290`).
- `malformed-trailing-comma`: trailing or double comma yields an empty clause → `ValueError`
  (V7, `rule_parser.py:292-299`).
- `malformed-clause-no-parens`: body clause missing `(` → `ValueError` (V8,
  `rule_parser.py:117-119`); missing `)` → `ValueError` (`rule_parser.py:121-123`).
- `malformed-clause-multi-colon`: a clause not splitting into exactly `predicate:bound`
  → `ValueError` (V9, `rule_parser.py:325-328`).

Bounds
- `happy-explicit-bound`: `pred(X):[l,u]` parsed to floats (`rule_parser.py:501-546`).
- `bound-default-interval`: no bound → `[1,1]` attached (`rule_parser.py:318-319`).
- `bound-true-false-shorthand`: `:True`→`[1,1]`, `:False`→`[0,0]`, case-insensitive, only
  when followed by `,`/`)`/end (body `rule_parser.py:262-275`; head
  `rule_parser.py:378-385`).
- `malformed-bound-arity`: not exactly 2 comma values → `ValueError` (V10,
  `rule_parser.py:514-516`).
- `malformed-bound-nonnumeric`: non-float bound value → `ValueError`
  (`rule_parser.py:521-528`).
- `malformed-bound-nan`: `NaN` rejected (`rule_parser.py:531-534`); `Inf` is rejected
  indirectly by the `[0,1]` range check.
- `malformed-bound-out-of-range`: value `<0` or `>1` → `ValueError` (V10,
  `rule_parser.py:537-540`).
- `malformed-bound-inverted`: `lower>upper` → `ValueError` (V10, `rule_parser.py:543-544`).

Negation
- `happy-negated-clause`: `~pred(X)` → bound `[0,0]` (`rule_parser.py:315-317`).
- `bound-negated-explicit`: `~pred(X):[l,u]` → strip `~`, invert to `[1-u,1-l]`
  (`rule_parser.py:311-314`,`337-339`).
- `malformed-double-negation-body`: `~~` in a body clause → `ValueError`
  (`rule_parser.py:302-304`).
- `malformed-double-negation-head`: `~~` in head → `ValueError` (`rule_parser.py:356-357`).
- `bound-negated-head`: `~pred(X)` / `~pred(X):[l,u]` head strips `~`, inverts resolved bound
  (`rule_parser.py:373-397`).
- `bound-negated-ann-fn-noop`: `~pred(X):fn` — negation flag is recorded but the ann-fn
  default `[0,1]` is a parse-time no-op; documented that runtime inversion needs the flag
  plumbed onto `Rule` (`rule_parser.py:409-412`).

Head predicate / bound / annotation
- `happy-head-bound`: `pred(X):[l,u]` head with explicit interval (`rule_parser.py:394-399`).
- `happy-head-ann-fn`: head suffix that is not a bound → annotation function name, default
  bound `[0,1]` (`rule_parser.py:400-413`).
- `malformed-head-multi-colon`: `>1` colon in head → `ValueError` (V6,
  `rule_parser.py:366-368`).
- `malformed-head-no-parens`: head lacks `(` or `)` → `ValueError` (V5,
  `rule_parser.py:360-363`).
- `malformed-head-bracketed-ann-fn`: an ann-fn name containing `[`/`]` that fails
  `_is_bound` → `ValueError` noting brackets are disallowed in ann-fn names
  (`rule_parser.py:402-408`).
- `bound-head-no-variable`: zero head variables after parens → `ValueError`
  (`rule_parser.py:101-102`).

Head functions
- `happy-head-simple-vars`: `head(X, Y)` → two plain variables (`rule_parser.py:478-482`).
- `happy-head-function`: `head(f(X, Y))` → a `__temp_var_N` placeholder plus `head_fns`
  entry (`rule_parser.py:462-477`); nested-paren aware comma split (`rule_parser.py:441-456`).

Names / regex
- `malformed-predicate-name`: head or body predicate not matching
  `^[a-zA-Z_][a-zA-Z0-9_.\-]*$` → `ValueError` (digit-leading gets a specific message)
  (`rule_parser.py:487-492`, called `89`,`125`).
- `malformed-component-name`: a variable not matching `^[a-zA-Z0-9_][a-zA-Z0-9_.@\-]*$` →
  `ValueError` (`rule_parser.py:495-498`, called `106`,`136`).

Comparison clauses
- `happy-comparison-clause`: a body clause containing `<=`,`>=`,`<`,`>`,`==`,`!=` →
  `clause_type='comparison'` (`rule_parser.py:185-187`,`570-577`).

forall
- `happy-forall`: `forall(pred(vars))` clause → injects
  `Threshold('greater_equal',('percent','total'),100)` at that clause index and unwraps to
  the inner predicate (`rule_parser.py:70-82`).
- `malformed-forall-unclosed`: `forall(...)` not ending in `)` → `ValueError` (V14,
  `rule_parser.py:72-74`).
- `malformed-forall-no-inner-pred`: inner lacks `(`/`)` → `ValueError`
  (`rule_parser.py:77-78`).
- `interacts-forall-custom_thresholds`: forall writes into `custom_thresholds` as a dict
  keyed by clause index (`rule_parser.py:79-81`); if the caller passed a `list`, this mutates
  a list element by integer index — a subtle list/dict interaction.

Custom thresholds
- `happy-thresholds-list`: list length must equal clause count (`rule_parser.py:156-158`).
- `malformed-thresholds-list-length`: mismatch → `ValueError` (`rule_parser.py:157-158`).
- `happy-thresholds-dict`: sparse map; missing clauses default to
  `('greater_equal',('number','total'),1.0)` (`rule_parser.py:169-173`).
- `malformed-thresholds-dict-empty`: empty dict → `ValueError` (V12,
  `rule_parser.py:163-164`).
- `malformed-thresholds-dict-negative-key`: any key `<0` → `ValueError`
  (`rule_parser.py:165-166`).
- `malformed-thresholds-dict-key-oob`: `max(key) >= num_clauses` → `ValueError`
  (`rule_parser.py:167-168`).
- `bound-thresholds-none`: `None`/falsy → every clause gets the default threshold
  (`rule_parser.py:177-179`).

Weights
- `happy-weights-default`: `None` → `np.ones(num_clauses)` (`rule_parser.py:203-204`).
- `happy-weights-array`: length must equal clause count (`rule_parser.py:214-216`).
- `malformed-weights-nonarray`: non-`ndarray` coerced via `np.array(..., float64)`; failure
  → `TypeError` (`rule_parser.py:208-212`).
- `malformed-weights-length`: length mismatch → `ValueError` (`rule_parser.py:215-216`).
- `malformed-weights-nonnumeric`: non-numeric dtype → `TypeError` (`rule_parser.py:219-220`).
- `malformed-weights-nonfinite`: any NaN/Inf → `ValueError` (`rule_parser.py:222-223`).
- `malformed-weights-negative`: any value `<0` → `ValueError` (`rule_parser.py:226-227`).

infer_edges
- `interacts-infer_edges-node`: for a node rule `infer_edges` is forced to `False`
  (`rule_parser.py:140-141`) regardless of caller input.
- `interacts-infer_edges-edge`: for an edge rule, `edges=(head_variables[0],
  head_variables[1], target)` (`rule_parser.py:196-199`) — assumes exactly two head vars.

set_static
- `interacts-set_static`: passed through to the `Rule` constructor unchanged
  (`rule_parser.py:243`); parser does not act on it.

**notes**: The double-character split trick (`)`→`))`, `]`→`]]`, split on `),`/`],`, restore)
is the fragile core of body splitting (`rule_parser.py:277-290`) — malformed bracketing can
produce surprising clause boundaries. `:True`/`:False` conversion happens BEFORE delimiter
doubling by design (comment `rule_parser.py:260-261`). `delta_t` is `uint16` (overflow
hypothesis BUG-057). The clause order produced here is NOT final: `reorder_clauses`
(`scripts/utils/reorder_clauses.py:6`) later moves node clauses ahead of edge clauses and
reorders the parallel `thresholds` list, but ONLY when `len(graph.edges) > len(graph.nodes)`
(`pyreason.py:1599`) — annotation/head functions receiving per-clause structure must key on
predicate+variable role, not body position. `custom_thresholds` may arrive as a list or dict
and the forall path can inject dict-style keys into it. `weights` and `thresh` values are
coerced to `float64` for numba.
