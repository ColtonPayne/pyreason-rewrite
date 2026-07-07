# Author report — accessor/trace-output cluster cases (session 12, raw)

Packet: session 11's NEXT — open the breadth phase on the four uncovered
accessor/trace-output fn rows in one coherent packet: `fn:get_rules`,
`fn:get_logic_program`, `fn:get_interpretation`, `fn:save_rule_trace`. Read
each anchor at the pin, enumerate input classes per row, extend the capture
with the fingerprint-probe design (the carried idea seed) plus a trace-file
probe under the session-10 confinement discipline, case the enumerated
classes over existing committed programs, run targeted, flip the rows.

Author: session 12 agent 1. Oracle pin `e1a94af33e1f`, oracle tree read-only
throughout. Engine fingerprint in every banked artifact: pyreason 3.6.0,
python 3.10.20, darwin, PYTHONHASHSEED=0.

## Verdict

**All four rows flipped to cased. 6 new cases, each ALL PASS oracle-vs-oracle
with same-engine repeats green (4 fresh-process captures per case, exact
digests). Fast tier 77 passed (was 70; +7 seam tests). Two new probe kinds
(`accessor_fingerprint`, `save_rule_trace`) with validation parity. One
characterization finding recorded against the analysis file's off-arm
description of the trace-name fallback.**

## 1. Pin reading (file:line anchors)

All four anchors read at the pin before any design; every claim below was
then screened live in `oracle-env` (section 3).

- **get_rules** — `oracle/pyreason/pyreason/pyreason.py:510-514`: returns the
  live `__rules` global — a `numba.typed.List` of internal rule objects, or
  `None` before any add / after `reset`/`reset_rules` (`:522`). Two mutation
  paths make "live" load-bearing: `reason(queries=...)` permanently narrows
  the global (`:1594-1595`), and the reorder pass *replaces* it with a
  clause-reordered copy whenever the graph has more edges than nodes
  (`:1598-1606`, `scripts/utils/reorder_clauses.py:6-30` — node clauses moved
  ahead of edge clauses, map `{new_index: original_index}` banked in
  `__clause_maps`).
- **get_logic_program** — `pyreason.py:529-535`: returns the `__program`
  global (`Program` or `None`). `None` until the first `reason()` constructs
  one (`:1609`); `reset()` never nulls it — `reset_graph()` only sets
  `program.interp = None` (`scripts/program/program.py:69-71` region, `interp`
  attr set at `program.py:29`).
- **get_interpretation** — `pyreason.py:538-546`: raises bare
  `Exception('No interpretation found. Please run `pr.reason()` first')` when
  `__program is None` (`:544-545`); otherwise returns `__program.interp` —
  which is `None` after a reset with a live program (the guard checks only
  the program, not the interp). `get_time` (`:549-558`) swallows exactly the
  raise path into `0`.
- **save_rule_trace** — `pyreason.py:1645-1655`: asserts
  `settings.store_interpretation_changes` (`:1652`, message shared with
  `get_rule_trace`'s assert at `:1666`), then constructs
  `Output(__timestamp, __clause_maps)` (`:1654`) and writes
  `rule_trace_nodes_{ts}.csv` + `rule_trace_edges_{ts}.csv` into `folder`
  (`scripts/utils/output.py:99-106`), default `'./'` — i.e. the process cwd.
  `__timestamp = time.strftime('%Y%m%d-%H%M%S')` at reason time
  (`pyreason.py:1511`) — the same wall-clock stamp shape the session-10
  output_file probe canonicalizes. Column shape: fixed 10-column header, plus
  `Clause-i` columns only when `interpretation.atom_trace` (`output.py:13`,
  `:44-47`); the clause map reorders the Clause columns back to author order
  via `_reorder_row` (`output.py:92-97`, `:114-123`).

## 2. Input-class enumeration per row

- **fn:get_rules** — `loaded` (typed list after add; post-reason the replaced
  reordered copy), `none` (fresh import AND post-reset — `None`, never an
  empty list), `post-reason-filtered` (**stays uncovered**: needs
  `reason(queries=...)`; the capture's `REASON_ARGS` deliberately excludes
  `queries` until the harness can construct Query objects — `type:Query` is
  its own uncovered row).
- **fn:get_logic_program** — `before-reason` (`None`, even with graph+rules
  loaded), `after-reason` (present, holding the exact interpretation
  `reason()` returned), `after-reset` (same object, `interp` nulled). All
  three cased.
- **fn:get_interpretation** — `happy` (returns the live reason-return
  reference), `no-program` (the pinned raise), `program-with-null-interp`
  (returns `None` without raising). All three cased.
- **fn:save_rule_trace** — `happy`, `store-off-assert`, `atom-trace-columns`
  (both arms), `folder-variants` (default `'./'` vs a named subfolder;
  the nonexistent-folder arm screens as pandas'
  `OSError: Cannot save file into a non-existent directory` — recorded, not
  cased, because the probe pre-creates its named subfolder so a missing
  directory can never wear the engine label), `clause-map-reorder`
  (non-identity map). All five cased.

## 3. Screen (screen-then-confirm)

One scratch script (scratchpad, not committed) run once under
`PYTHONHASHSEED=0 oracle-env/bin/python` before any harness code changed.
Confirmed, in one process: fresh state (`None`/`None`/raise/`get_time`→0);
loaded-unreasoned fingerprint renders through boxed numba objects (typed-list
iteration, `Label.get_value`, interval lower/upper, plain-int delta); the
post-reason `__rules` replacement (new typed-list object; edge-first rule's
`popular(y)` moved to front); `program.interp is reason_return` and
`get_interpretation() is reason_return` both `True`, `interp.time == 2`
plain int; both CSVs written with the `%Y%m%d-%H%M%S` stamp; the folder
variant writing identical files into `traces/`; the nonexistent-folder
OSError; the store-off AssertionError text; post-reset
`None`/same-program-null-interp/return-`None`.

## 4. What was built

`harness/capture.py` (commit `de547d0`):

- **`accessor_fingerprint` probe kind** — field `accessor` ∈ {`rules`,
  `logic_program`, `interpretation`} (validated; unknown name is exit-2
  usage, top-level and in-step alike). Renders the accessor's return as
  canonical data: `None` passes through in every branch (the before-load /
  after-reset observations); `rules` becomes per-rule dicts via
  `rule_fingerprint` — name, type, target, head variables, delta, bound, and
  the **ordered clause list** (deeper than `parse_fingerprint`'s
  clause-count on purpose: reorder makes clause order part of the accessor's
  contract); `logic_program` and `interpretation` reduce structurally to
  presence + identity-with-the-last-reason-return (the pinned accessors
  return live references — `pyreason.py:535`/`:546` — so identity is
  contract; an engine handing back a copy cannot compare equal).
  `Program.interp` is the exact attribute `get_interpretation` reads at the
  pin, recorded as the seam the fingerprint holds a candidate program object
  to. Standalone kind (not interpretation-consuming) — the before-any-reason
  returns are the point. `allow_raise` permitted (the no-program raise banks
  as data).
- **`save_rule_trace` probe kind** — calls the engine's `save_rule_trace`
  with the capture's interpretation, into the confined per-capture directory
  (`case_wants_output_dir` now covers this kind — the pinned default folder
  is the cwd, so without confinement CSVs would land in the repo root), or
  into a named subfolder validated to a single plain path segment
  (`TRACE_FOLDER_RE`; separators/`..`/absolute refused, exit 2) and created
  before the call. Omitting `folder` exercises the pinned default. Readback:
  every `.csv` in the target, sorted, names stamp-canonicalized
  (`TRACE_TS_RE`, rationale recorded at the definition site — identical
  run-schedule reasoning to the session-10 `OUTPUT_TS_RE`), contents
  verbatim, compared exactly. Interpretation-consuming (requires a reason);
  `allow_raise` legal (the store-off assert is engine behavior).

`tests/test_capture_validation.py` (+7, fast tier 70 → 77): accessor-name
validation both case forms; no-reason-block legality for accessor probes;
the three-accessor rendering unit test (None passthrough, clause-list
fingerprint, identity flags both polarities, null-interp branch); folder
confinement validation; save_rule_trace's reason requirement; cwd
confinement trigger; call-and-readback unit test (default vs subfolder,
stamp canonicalization, sorted names). The kind-partition tripwire updated
to the new five standalone kinds.

## 5. Cases and runs

Six cases (commit `7921f97`), all over the committed hello-world program (or
its edge-first-rule variant — same graph, same fact):

| case | pins | verdict |
|---|---|---|
| accessors-fresh-state | pristine module: rules `null`, program `null`, interp raise, `get_time` 0 | pass |
| accessors-lifecycle | steps: loaded (author-order fingerprint, program `null`, interp raise) → reason (replaced rules, identity flags true, time 3) → reset (rules `null`, `interp_present` false, interp returns `null` unraised) | pass |
| save-rule-trace-basic | happy + folder-variants + atom-trace-on columns; `srt-default` and `srt-subfolder` bank byte-identical CSV pairs; `trace-node` cross-view | pass |
| save-rule-trace-atom-trace-off | 10-column CSVs, `Old Bound` `-`, `Occurred Due To` `-` (finding, §6) | pass |
| save-rule-trace-store-off | AssertionError banked, message verbatim from `pyreason.py:1652` | pass |
| save-rule-trace-clause-reorder | non-identity map: `rules-post-reason` fingerprint shows `popular(y)` first; CSV `Clause-1` carries the Friends groundings (author order restored) | pass |

Runs (all from repo root):

```
uv run pytest -m "not e2e"          # 77 passed, 2 deselected — before and after case authoring
PYTHONHASHSEED=0 uv run python -m harness.run --cases harness/cases/accessors-lifecycle.json --engine-a oracle-env/bin/python   # screen: pass, 24.1 s
# then identically for: accessors-fresh-state, save-rule-trace-basic,
# save-rule-trace-atom-trace-off, save-rule-trace-store-off,
# save-rule-trace-clause-reorder — each ALL PASS (1 case(s))
```

Self-proof mode: 4 fresh-process captures per case; same-engine repeats
compared by exact digest — green for all six (any instability would have
judged `irreproducible`, none did). No other e2e was run; the 53-case corpus
sweep is session 11's banked verdict and was not rerun.

## 6. Findings / characterizations

1. **Trace names are empty when atom_trace is off — the CSV's `Occurred Due
   To` fallback is dead at the pin.** With `atom_trace=False`, every row of
   the node CSV shows `Occurred Due To` = `-`. Root cause, forced by source:
   `_update_node` sets `meta_name = ''` unless `atom_trace`
   (`interpretation.py:1543-1548`; same shape at the direct-append sites
   `:299` via `facts_to_be_applied_node_trace[i] if atom_trace else ''`), so
   `output.py:23-25`'s `if not interpretation.atom_trace and r[7] != ''`
   branch can never fire on any reachable path — the analysis file's
   off-arm description ("'Occurred Due To' comes from the rule name r[7]")
   describes the code's intent, not its behavior. Recorded on the board row.
   Rewrite-relevant: a rewrite that "fixes" this by carrying names would
   diverge on this case.
2. **The clause-map machinery pinned from both sides.** On an
   edge-clause-first rule over the friends graph (7 edges > 5 nodes), the
   live `__rules` global is replaced with the reordered copy (get_rules
   fingerprint: `popular(y)` ahead of `Friends(x,y)`), while the saved CSV's
   `Clause-1..4` columns are mapped back to the author's order (`Clause-1` =
   Friends edge groundings). A rewrite reproducing the trace but not the
   live-global mutation (or vice versa) fails exactly one of the two probes.
3. **Live-reference identity is observable contract.** `get_interpretation()`
   and `get_logic_program().interp` are both `is`-identical to `reason()`'s
   return at the pin — banked as boolean flags, so a copy-returning engine
   diverges.
4. **The raise/None/0 triple.** No-program: `get_interpretation` raises bare
   `builtins.Exception`; post-reset-with-program: returns `None` unraised;
   `get_time` maps only the raise path to `0`. All three banked.

## 7. Uncovered classes (named, not absorbed)

- `fn:get_rules` / `post-reason-filtered` — needs `reason(queries=...)`;
  `REASON_ARGS` excludes `queries` until the capture can construct Query
  objects (`type:Query` is its own uncovered row). Named on the board.
- `fn:save_rule_trace` nonexistent-folder arm — screens as pandas' OSError;
  deliberately not cased (the probe pre-creates its subfolder so a missing
  directory is never mislabeled engine behavior). Noted on the board inside
  folder-variants.

## 8. What the reviewer should scrutinize

- **The fingerprint's identity flags** (`is_reason_return`,
  `interp_is_reason_return`): is `is`-identity across the capture's local
  variable the right seam, especially in the steps form where the
  interpretation only advances on successful reason steps?
- **`rule_fingerprint` depth**: it renders clauses but not thresholds/
  weights/edges/static — is the omission defensible for these rows (those
  surfaces belong to type:Rule/dsl:rule-text rows), or does it under-pin the
  reordered thresholds (`reorder_clauses.py:25` reorders thresholds too, and
  no probe observes that)?
- **`TRACE_FOLDER_RE`** (`^[A-Za-z0-9][A-Za-z0-9._-]*$`): confirm it cannot
  admit an escaping path on this platform.
- **The store-off case** banks only the raise record — is one probe enough,
  or should it also observe the confined directory's emptiness (the current
  `output_file` probe reads `.txt` only, so CSV-absence is unobserved)?
- **parse_fingerprint vs rule_fingerprint duplication** — kept separate so
  banked expect_raise digests don't shift; reviewer may prefer unification.

## Commits

- `de547d0` — harness: accessor_fingerprint + save_rule_trace probe kinds
- `7921f97` — harness: six cases over the accessor/trace-output cluster
- (this commit) — docs: board flips for the four rows + this report
