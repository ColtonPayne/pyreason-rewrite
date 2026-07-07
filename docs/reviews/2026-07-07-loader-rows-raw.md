# Author report — loader/semantic fn rows + the two approved canonicalization arms (session 13, agent 1)

Author: session 13 agent 1 (work-packet executor; report is raw — the
independent review gate has not seen this work yet). Oracle pin
`e1a94af33e1f` (v3.6.0), tree verified clean before and after; preflight
10/10 at session start.

## What the packet asked

Session 12's NEXT, operator-adjudicated 2026-07-07: (A) the approved
apply-inputs-expecting-raise probe form; (B) the approved `memory_profile`
peak-MB canonicalization plus the `memory_profile` × `output_to_file`
interaction case; (C) case the seven un-gated loader/semantic fn rows —
`add_rules_from_file`, `add_fact_from_json`, `add_fact_from_csv`,
`add_rule_from_json`, `add_rule_from_csv`,
`load_inconsistent_predicate_list`, `add_closed_world_predicate` — plus the
session-12 seed (the IPL-with-atom-trace-off trace arm). Out of scope and
untouched: the 4 type rows and the two callable-registering functions.

## Verdict

All three parts landed. The harness gained the `apply_input` probe form
(the same ops double as multi-step step ops) and the gated
`canonicalize_peak_mb` opt-in on `output_file`; 17 cases took the corpus
59 → 76; all seven rows flipped to `cased` with uncovered facets named;
fast tier 77 → 90. Every case: targeted oracle-vs-oracle ALL PASS, 4
fresh-process captures, same-engine repeats by exact digest,
`PYTHONHASHSEED=0`. No corpus sweep (per the wall-clock rule; note for the
reviewer: `rule_fingerprint` and every existing probe are untouched — the
capture changes are purely additive kinds/ops/flags, so no committed case's
digests can have moved).

## Part A — the `apply_input` probe form (commit `300bf3f`)

Design, and why it has two surfaces:

- **Probe kind `apply_input`** (both case forms' probe lists): applies one
  loader-family input and records the outcome either way — a raise as the
  module-qualified type + message (the `raise_record` shape the step
  machinery already banks), an acceptance as `{"raised": false}` with the
  loaded state observed by the probes that follow (accessor fingerprints for
  rule loaders). `allow_raise` is banned (the probe records raises itself —
  the `expect_raise` convention), and the loader callable is resolved by
  `getattr` *outside* the try so an engine missing the binding fails the
  capture instead of banking an AttributeError as behavior.
- **The same ops as step ops**: fact loaders and
  `load_inconsistent_predicate_list`/`add_closed_world_predicate` have no
  accessor — their only observable is the reasoning that consumes them, and
  in the one-step form probes run *after* `inputs.reason`. A loader step
  before a probed reason step closes that ordering gap; a step op that
  raises already banks its outcome record, so the expecting-raise semantics
  are identical on both surfaces. Validation is one shared `_apply_fault`
  (authoring faults exit 2 in both case forms — the packet's parity
  requirement).
- **Path spellings pin the declared existence state.** `path` must name a
  committed repo-relative fixture (existence-checked like `graphml_path` — a
  typo'd happy arm must never bank FileNotFoundError as engine behavior and
  pass self-proof); `missing_path` must NOT exist (a case cannot claim a
  missing-file observation while banking a load). Both are repo-confined.
  Kwargs are whitelisted per op against the pinned signatures
  (`add_rules_from_file`: `infer_edges`/`raise_errors`; the four CSV/JSON
  loaders: `raise_errors`; the IPL loader: none), values boolean —
  a typo'd kwarg cannot bank the engine's TypeError.
- **No dead scaffolding**: every op is consumed by a committed case on at
  least one surface, the probe-kind surface by the six malformed cases, the
  step-op surface by the eight happy/semantic steps cases; +13 seam tests.
- **Not implemented on purpose**: a settings arm (the `type-reject` family
  is out of scope this packet) and `load_graphml` (its two malformed arms
  are named future unlocks on the board; adding the op without a consuming
  case would be dead scaffolding).

## Part B — the peak-MB canonicalization (commits `300bf3f` case `0527526`)

`PEAK_MB_RE` at its definition site in `harness/capture.py` carries the
rationale: the profiled branch prints `\nProgram used {peak} MB of memory`
(`pyreason.py:1520` non-again / `:1526` again-branch mirror at the pin), and
under `output_to_file` that line lands in the redirect file the
`output_file` probe compares. Screened live: 103.203125 vs 103.53125 MB
across two identical fresh processes — run-varying measurement, the same
run-schedule reasoning as `OUTPUT_TS_RE`/`TRACE_TS_RE`. The reduction
touches exactly the number (`Program used <peak-mb> MB of memory`); the
line's fixed text and every other character compare exactly. Per AC-2 the
normalization is per-case opt-in (`canonicalize_peak_mb` on the probe,
rationale restated in the case record) and validation-gated to
`settings.memory_profile: true` cases — nothing else at the pin writes the
line, so the canonicalization can never mask other engine text. Without the
flag the identical content is untouched (seam-tested), so no existing case's
comparison changes.

The consuming case `memory-profile-output-on` pins the `interaction-output`
class: the redirect file carries output-to-file-on's exact verbose print
shape plus the canonicalized peak line; reasoning probes and both knob
readbacks ride along.

One incidental engineering note (harness-side, not engine behavior): a
scratch screen of this interaction initially hung — `memory_profiler`'s
monitor child is spawned on darwin and re-imports `__main__`, and the
unguarded scratch script re-ran the whole program in the child. The
harness capture is immune (its `__main__` is guarded), which is why the
committed memory-profile cases have always run clean.

## Part C — what I read at each anchor, and what the cases pin

### fn:add_rules_from_file (`pyreason.py:652-690`)
Read: line filter (`rstrip() != '' and [0] != '#'` — comments only when
first char, whitespace-indented `#` lines are parse attempts), the
`rule_{i+rule_offset}` naming over the *filtered* list with
`rule_offset = len(__rules)`, `raise_errors=False` default (warn + skip),
the raise wrap `Line {i+1}: Failed to parse rule '{r}' - {e}`, bare
`open()` for missing files.
Cases: `rules-from-file-basic` (offset naming with one inline rule
preloaded → `[popular_rule, rule_1, rule_2]`; comment + blank skipped; the
file-loaded chain fires in the trace) and `rules-from-file-malformed`
(missing file → bare errno FileNotFoundError; raise arm loads line 1 *then*
raises — partial load pinned by fingerprint `[rule_0]`; skip arm leaves the
`rule_1`/`rule_3` name gap because `i` advances over failed lines).

### fn:add_rule_from_csv (`pyreason.py:753-866`)
Read: `pd.read_csv(header=None, dtype=str, keep_default_na=False)`, its
three except arms (FileNotFoundError with the loader's own message /
EmptyDataError → warn + return / everything else → `Error reading CSV
file ...`), exact-match header skip, `_parse_bool_param`'s truthy-string
table, file-local `loaded_name_set` (never the engine-global set), the
row-wise doubled-prefix raise wrap.
Cases: `rule-from-csv-basic` (header skip, explicit clause bound, truthy
`'yes'`/`'1'`, quoted commas, auto-name, the `infer_edges` rule writing
inferred `team` edges into the edge trace) and `rule-from-csv-malformed`
(missing file; missing rule_text; duplicate name raising at row 2 after
row 1 loaded — fingerprint `[same_name]`; the unquoted-comma row failing
pandas' tokenizer *wholesale* so nothing from that file loads — the
row-wise vs whole-file failure asymmetry in one case). Named unobserved:
`set_static` is not rendered by the accessor fingerprint.

### fn:add_rule_from_json (`pyreason.py:868-1080`)
Read: the three file/except arms, the not-array check, item-not-object,
the threshold loop (list form; dict form with `int(key_str)` and
per-key `Threshold(...)` construction — `KeyError`/`ValueError`/`TypeError`
folded into `Invalid threshold - {te}`), weights must-be-list, the outer
re-wrap that *doubles* the item prefix.
Cases: `rule-from-json-basic` (four accepted items: plain, thresholds-list,
thresholds-dict, weights — fingerprint pins names/targets/clauses in item
order; thresholds/weights contents unobserved by the fingerprint, named on
the board) and `rule-from-json-malformed` (six raises: missing file, bad
syntax, not-array, item-not-object with the doubled prefix, threshold
missing `'thresh'` — the KeyError key verbatim in the message — and the
non-integer dict key; closing fingerprint `None` pins that all six raised
before any `add_rule`).

### fn:add_fact_from_json (`pyreason.py:1168-1292`) / fn:add_fact_from_csv (`:1294-1412`)
Read: the shared `_parse_and_validate_fact_params` (int coercions with
raise-or-warn arms; the end_time-defaults-to-start_time behavior lives on
the `raise_errors=False` path only), the JSON loader's *unconditional*
summary print vs the CSV loader's verbose gate, header exact-match, the
shared auto-name counter in `add_fact` spanning node+edge lists.
Cases: `fact-from-json-basic` / `fact-from-csv-basic` (loaded state
observed through the reason trace — given names, `fact_1`/`fact_2`
auto-names, windows, interval bounds, static coercions, the quoted
comma-bearing edge fact on the edge trace, the short two-field CSV row
padded by the reader) and the two malformed cases (missing file — each CSV
loader's own message vs the JSON loader's; bad start_time; missing
fact_text; the single-prefix parser raise `Missing closing parenthesis in
fact` vs the doubled loader-level prefix; intra-file duplicate name; fact
flavored not-array message; the zero-byte CSV warning-and-returning without
a raise). Named unobserved: the loaders' partial-load state after a raise
(no fact accessor exists at the pin); the JSON loader's unconditional
print (pre-reason process stdout, never compared).

### fn:load_inconsistent_predicate_list (`pyreason.py:611-618`, `yaml_parser.py:187-196`)
Read: `parse_ipl` — bare `open()`, `yaml.safe_load`, `ipl_yaml['ipl']`
(KeyError), `labels[0]/labels[1]` (IndexError), null key → empty list, and
the wholesale rebind of `__ipl` (contrast `add_inconsistent_predicate`'s
append).
Cases: `ipl-load-basic` (semantic: every popular derivation banks an
unpopular complement row named `IPL: popular`, Triggered By `IPL`),
`ipl-load-null-overwrite` (an inline-added pair then the null yaml → zero
complement rows: overwrite-not-merge and the null acceptance in one
observation), `ipl-load-malformed` (four distinct exception types:
FileNotFoundError / `KeyError: 'ipl'` / IndexError / yaml.parser.ParserError
whose message embeds the repo-resolved fixture path — identical for both
engines run from this repo, exact compare, no canonicalization needed),
and the session-12 seed `ipl-atom-trace-off-trace` (below).

### fn:add_closed_world_predicate (`pyreason.py:1122-1130`, `:1613-1617`; `interpretation.py:1757-1775`)
Read: the bare `set.add`, `reset()` clearing the set (`:491/:497`), the
conversion to a numba Label list at reason time, and the consumption seam:
`is_satisfied_node`'s CWA branch treats a *missing* or `[0,1]` label as
`[0,0]` — but only for groundings that reach the check. First screen
attempt taught the grounding subtlety: when the clause predicate is in the
predicate map, `get_rule_node_clause_grounding` (`interpretation.py:1396-
1402`) draws candidates from the map (only nodes that *have* the
predicate), so a single-clause rule never shows the CWA. The cased program
grounds `x` by a `Friends(x,y)` clause first; the `busy(x):[0,0]`
clause then filters those groundings through the CWA branch.
Cases: `closed-world-on` / `closed-world-off` — the on twin derives
`available(John)`/`available(Justin)` (never-stated nodes) while `busy(Mary)`
= `[1,1]` still fails the `[0,0]` clause; the off twin derives no available row.
Duplicate add pinned as a set no-op (the on twin applies it twice).
**Un-bankable arm, screened and named instead of cased:** the non-string
add is silent (a bare `set.add`), and the raise surfaces only at `reason()`
from the numba Label conversion with a *run-varying* message (`character
U+5582710 is not in range` / `U+e56710` across two identical runs — a
pointer-like value). Under exact compare and same-engine-repeat discipline
that can never bank; a canonicalization would need its own recorded policy
and would pin nothing of value. The empty-string add was screened inert
(adds and reasons; no behavior change on a program whose rules never name
an empty predicate) — not cased, named on the board.

### The session-12 seed — `ipl-atom-trace-off-trace`
The review-H1 screen, now a committed case: friends graph + popular rule +
fact + the yaml-loaded pair, `atom_trace` off, `save_rule_trace` view. The
node CSV pins `Occurred Due To = '-'` on all 6 popular rows (fact/rule
append sites bank empty names with atom_trace off) and `'IPL: popular'` on
all 6 unpopular rows (the IPL append sites bank names unconditionally) —
`output.py:23-25`'s fallback firing exactly where the pin makes it
reachable. Verified in the banked artifact with a real CSV parse.

## Evidence — exact reproduction

From the repo root:

```
uv run pytest -m "not e2e"
# 90 passed, 2 deselected

PYTHONHASHSEED=0 uv run python -m harness.run \
  --cases harness/cases/<case>.json --engine-a oracle-env/bin/python
# for each of: rules-from-file-basic, rules-from-file-malformed,
#   rule-from-csv-basic, rule-from-csv-malformed, rule-from-json-basic,
#   rule-from-json-malformed, fact-from-json-basic, fact-from-json-malformed,
#   fact-from-csv-basic, fact-from-csv-malformed, ipl-load-basic,
#   ipl-load-null-overwrite, ipl-load-malformed, ipl-atom-trace-off-trace,
#   closed-world-on, closed-world-off, memory-profile-output-on
# each: ALL PASS (1 case(s)) — self-proof mode, 4 fresh-process captures,
# same-engine repeats by exact digest
```

Artifacts were spot-checked beyond the PASS verdicts (guard against a
vacuous both-sides-wrong pass): every malformed arm's banked exception
matches the pre-authoring screen; the fingerprints show the exact expected
name lists; the ipl-off CSV was re-parsed with a real CSV reader
(`('popular','-')×6`, `('unpopular','IPL: popular')×6`); the redirect file
shows the canonicalized peak line plus the verbose print shape.

## Canonicalization / normalization inventory (AC-2)

- `canonicalize_peak_mb` on `memory-profile-output-on`'s `output_file`
  probe — rationale at `PEAK_MB_RE`'s definition site and in the case
  record; per-case opt-in, validation-gated to memory_profile cases.
- Nothing else. All 16 other cases compare exactly (`comparison.probes`
  empty). Exception messages embedding repo-resolved fixture paths compare
  exactly by construction (both engines run from this repo — same property
  the artifact `.log` paths already rely on).

## Refuted / corrected along the way

- My first CWA screen (single-clause rule) showed *no* effect — not an
  engine surprise but a grounding-order fact (`interpretation.py:1396-1402`
  draws candidates from the predicate map when the predicate is known).
  The cases encode the two-clause shape; the board note carries the seam.
- My first `rules.csv` draft had an unquoted comma inside a bound — pandas
  fails that file wholesale. Rather than discard it, that behavior became
  the `unquoted-comma` arm (`malformed-unreadable` class).

## Blockers / asks

None. No dependency, pin, or out-of-repo need arose; no operator gate was
touched. The one un-bankable arm (CWA non-string reason-time raise, message
run-varying) is recorded above and on the board rather than decided.

## Idea seeds

- The four raise_errors=False warn-and-skip arms of the CSV/JSON loaders
  are uniformly uncased (only `add_rules_from_file`'s default-False skip
  arm is pinned). One case per loader family would close them cheaply now
  that the fixtures exist.
- `type-reject` family-wide: a settings arm for `apply_input` (op =
  setattr on a named knob) would unlock the 18 rows' type-reject class in
  one stroke — deliberately not built this packet (out of scope, would have
  been dead scaffolding); the validation shape is ready for it.
- `load_graphml`'s missing-file/bad-content arms: add `load_graphml` to
  `APPLY_FILE_OPS` with a consuming case — the `missing_path` spelling was
  designed for exactly this.
- Carried from session 12: the named-function registry for
  `add_annotation_function`/`add_head_function`; `probe_s` timing;
  multi-path `--cases`; multi-rule prange characterization; `REASON_ARGS`
  from the pinned signature; artifact-schema echo of `inputs`.
