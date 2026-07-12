<!-- doccode: pyreason-rewrite-docs-reviews-2026-07-12-case-seed-batch-author -->
# Session 30 — the carried case-seed batch (author report)

- session: 30 · 2026-07-12 · author packet (the remaining carried CASE SEEDS, one batch)
- scope: seed families 1–4 from the packet — the loaders' `raise_errors=False`
  warn-skip arms, the loader-input widenings (ragged CSV, non-numeric bounds in
  files, weights dtypes, delta_t boundaries), `interacts-unknown-predicate`, and
  the O1/O2 graphml coercion arms (batch §B23/§B24)
- verdict: **18 arms screened → 18 bankable → 10 cases added, ALL PASS 10/10
  oracle-vs-rewrite** (fresh run of the committed case content into
  `results-session30-seeds/`, gitignored; every case's same-engine repeats
  digest-stable). **Zero un-bankable arms, zero divergences.** Two rewrite gaps
  the screens exposed were fixed to pinned behavior (delta uint16 wrap; np.array
  weights-conversion semantics) with 8 fast-tier seam tests. Fast tier **305
  passed, 5 deselected** (was 297 + the 8 new tests), inventory gate green.

## State-recovery note (interruption of record)

The authoring session was terminated mid-run by a transient API connection
error after the final harness run and resumed with all work UNCOMMITTED. On
resume I verified against the actual tree before proceeding: `git log` ended at
`9181767` (session-29 ledger); `git status` showed the three modified files
(`.gitignore`, `src/pyreason/_rule_parser.py`, `tests/test_rewrite_dsl_parsers.py`)
and all 24 new untracked files (10 cases + 13 fixtures + this report's inputs)
intact on disk with the content I authored; `results-session30-seeds/` held the
pre-interruption ALL PASS run. I re-inspected the full uncommitted diff,
re-ran the fast tier (green), committed at green checkpoints, wiped the results
dir, and re-ran the harness against the **committed** case content
(`git show HEAD:harness/cases/<id>.json`) — ALL PASS 10/10 fresh. No claim in
this report rests on pre-interruption output alone.

## Screen-then-case protocol

Every arm was screened at the pin FIRST, as a draft case through the harness's
self-proof mode (`--engine-a oracle-env/bin/python` alone): each case runs in
**4 fresh oracle processes** (two independent pairs) and the runner reds on any
digest instability — the C1-family screen, mechanized. All 10 drafts came back
`pass` (deterministic + stable), so every arm was caseable; nothing joined the
un-bankable board list this session. Harness treatment of warnings checked
before authoring (packet item 1): `harness/capture.py` banks only probe
outputs; loader warnings ride stderr into the runner's diagnostic `.log`,
never compared — so the warn-skip cases bank the *post-load state* (rules
fingerprint, or reasoning over the loaded facts), which is the skip semantics
itself.

## Triage table

| # | seed arm | pin screen outcome (stable, 4 fresh processes) | disposition |
|---|---|---|---|
| 1 | `add_rules_from_file` warn-skip | already banked since session 16 (`rules-from-file-malformed` line-skip + name-gap) | no new case — noted |
| 2 | `add_rule_from_csv` `raise_errors=False` | missing rule_text / dup name / unparseable text SKIP; invalid bool cell 'maybe' warns and LOADS with default | **cased** `rule-from-csv-warn-skip` |
| 3 | `add_rule_from_json` `raise_errors=False` | non-object, missing rule_text, threshold-missing-field, non-convertible weights, non-list weights, dup name all skip → fingerprint wsj_good+wsj_last | **cased** `rule-from-json-warn-skip` |
| 4 | `add_fact_from_csv` `raise_errors=False` | bad fact_text/bound + dup SKIP; bad start_time LOADS start=0; bad end_time LOADS end=start (fires only at start); bad static LOADS non-static | **cased** `fact-from-csv-warn-skip` |
| 5 | `add_fact_from_json` `raise_errors=False` | same asymmetry on the item path; start_time `[1]` takes the TypeError branch → default 0 | **cased** `fact-from-json-warn-skip` |
| 6 | ragged CSV: row wider than first | wholesale ValueError, pandas C-tokenizer text, line = record ordinal; nothing loads | **cased** `fact-csv-ragged` |
| 7 | ragged CSV: FIRST row widest | extra trailing column silently ignored; later short rows pad to defaults | **cased** `fact-csv-ragged` |
| 8 | non-numeric interval bounds in fact files | skip arm on both loaders (CSV `"beta(A):[abc,1]"`, JSON `delta(A):[nope,1]`); raise arm already banked (`fact-from-json-malformed`) | **cased** inside the two fact warn-skip fixtures |
| 9 | weights dtypes: ints / numeric strings / booleans | all convert through np.array(dtype=float64) and load | **cased** `rule-json-weights-dtypes` |
| 10 | weights nested `[[1,2]]` | **pin ACCEPTS** — np len() = top-level row count passes the one-clause length check | **cased**; rewrite gap → fixed |
| 11 | weights `["heavy"]` | `builtins.Exception` "Item 0: Unexpected error - ..." (TypeError falls past the ValueError catch) | **cased** |
| 12 | weights length / negative / NaN-literal | single-wrapped loader ValueError with the parser's own text (json.load accepts a bare NaN) | **cased** (one fixture per raise arm) |
| 13 | delta none / `<-0` / `<-65535` | 0 / 0 / 65535 in the parse fingerprint | **cased** `rule-delta-variants` |
| 14 | delta `<-65536` / `<-70000` | **wraps to 0 / 4464** (the pinned numba.types.uint16 cast) | **cased**; rewrite gap → fixed |
| 15 | delta 0 end-to-end | the `<-0` rule fires in the SAME timestep its body fact applies; the `<-1` chain fires one later | **cased** `delta-zero-rule` |
| 16 | `interacts-unknown-predicate` (closed-world, never grounded) | all-nodes fallback grounding fires the [0,0]-clause rule for every node at t=1; the plain never-grounded edge rule alongside is fully silent | **cased** `closed-world-unknown-predicate` |
| 17 | O1: `'1,0'` inverted pair, node AND edge (§B23) | no t=0 row; later facts never stick; node filter frozen at inverted [1,0] from t=1 vs edge resolving to [0,1] with resolve rows — the node/edge asymmetry | **cased** `graphml-static-pin` |
| 18 | O2: whitespace pairs `'1, 1'` / `'0, 1'` / `'-0,1'` (§B24) | `'1, 1'` → [1,1] under the bare key; the other two coerce vacuous and vanish (int strips spaces; int('-0')=0) | **cased** `graphml-static-pin` |

Tally: **18 arms screened / 10 cases added / 10 PASS / 0 un-bankable / 0
divergences filed / 2 rewrite fixes.**

## The two rewrite fixes (screens forced them; commit 92eed57)

Both surfaced as `divergent` on the first oracle-vs-rewrite run of the drafts —
exactly the two arms where the rewrite had modeled the pinned ndarray/numba
seam with plain-Python shortcuts:

1. **delta uint16 wrap** — the pinned constructor casts delta_t through
   `numba.types.uint16` (oracle rule_parser.py:243); the rewrite kept a plain
   int, so `<-65536` fingerprinted 65536 vs the pin's 0. Fix:
   `int(delta_t) % 65536` at the same seam
   (`src/pyreason/_rule_parser.py`), with a 5-arm parametrized seam test.
2. **np.array weights conversion** — the pinned
   `np.array(weights, dtype=float64)` accepts rectangular NESTED numeric lists
   (len = top-level row count, so `[[1,2]]` passes a one-clause length check)
   and converts `None` to NaN (taking the finiteness raise, not the conversion
   raise — verified against the pinned numpy live, plus a two-engine spot
   check: both raise the identical finiteness ValueError on `weights=[None]`).
   The rewrite's flat `float()` loop raised on both. Fix: `_weights_to_floats`
   mimics exactly those observable arms (rectangularity enforced, ragged →
   the pinned TypeError wrap; finiteness/sign checks over flattened leaves);
   3 seam tests pin nested acceptance, the None finiteness raise, and the
   ragged conversion raise.

Fixes are equivalence work, not improvements — both reproduce pinned behavior
verbatim; the divergent verdicts flipped to pass with no case edits.

## Cases added (all `runtime_class: smoke`; ALL PASS 10/10)

`rule-from-csv-warn-skip`, `rule-from-json-warn-skip`,
`fact-from-csv-warn-skip`, `fact-from-json-warn-skip` (the skip-vs-
load-with-default asymmetry, observed via rules fingerprints / reasoning),
`fact-csv-ragged` (the whole-file vs silently-widened asymmetry),
`rule-json-weights-dtypes` (3 acceptance + 4 raise arms + nested acceptance),
`rule-delta-variants` (5 fingerprint arms), `delta-zero-rule` (firing
schedule), `closed-world-unknown-predicate` (corpus seed),
`graphml-static-pin` (corpus seed — §B23/§B24, the slice-5 review's O1/O2
probes finally cased). 13 new committed fixtures under `harness/fixtures/`.

One honest note on `graphml-static-pin`: under the default
`static_graph_facts=true`, the static graph-fact re-application freezes later
facts out on EVERY graph-stated label, not only the inverted-pair one — the
O1-discriminating observables are the t=0 silence, the node-side frozen
inverted [1,0] vs the edge-side [0,1] resolve rows, and the no-change trace
shapes; the case purpose describes exactly those. The un-collided
world-state-only form of the static pin remains as the slice-5 review recorded
it.

## Board deltas (commit 7cc5678)

- `fn:add_rule_from_csv` / `fn:add_rule_from_json` / `fn:add_fact_from_csv` /
  `fn:add_fact_from_json`: warn-skip coverage recorded; uncovered lists
  rewritten to name only the remaining raise halves (+ bound-header-mismatch,
  bound-empty-array, threshold arms).
- `fn:add_fact_from_csv`: new classes `malformed-ragged-wide-row`,
  `bound-ragged-first-row-wide`; `malformed-bad-fact_text`,
  `malformed-nonint-time` (both halves), `interacts-duplicate-name-intrafile`
  now banked on this loader.
- `fn:add_rule_from_json`: new classes `bound-weights-dtypes`,
  `bound-weights-nested`, `malformed-weights-nonconvertible-entry`.
- `fn:load_graphml`: new classes `malformed-attr-inverted-pair`,
  `bound-attr-whitespace-pair` (O1/O2 off the follow-up list and onto the row).
- `fn:add_closed_world_predicate`: `interacts-unknown-predicate` moves from
  the uncovered list to banked.
- `dsl:rule-text` / `type:Rule`: the three new construct/e2e cases appended;
  delta and weights notes updated with the banked wrap values.
- Class descriptions added to `docs/analysis/surface/rules.md` and
  `facts-and-graph.md` per the board convention. Inventory gate green.

## Hygiene

- Oracle tree byte-clean, HEAD = `e1a94af33e1f` = oracle/PIN. No installs, no
  dependency changes (`git diff 9181767..HEAD -- pyproject.toml uv.lock`
  empty). No writes outside the repo (scratchpad used for draft staging and
  screen artifacts). `results-session30-seeds/` gitignored. No full e2e sweep —
  fast tier + the 10 packet cases only. Hooks ran on every commit (the corpus
  link check passed on the board and report commits).

## Repro

```
# fast tier (305 passed, 5 deselected)
uv run pytest -m "not e2e"

# the 10-case batch, oracle vs rewrite (ALL PASS (10 case(s)), exit 0)
mkdir -p /tmp/seed-batch-cases && for c in rule-from-csv-warn-skip \
  rule-from-json-warn-skip fact-from-csv-warn-skip fact-from-json-warn-skip \
  fact-csv-ragged rule-json-weights-dtypes rule-delta-variants \
  delta-zero-rule closed-world-unknown-predicate graphml-static-pin; do \
  cp harness/cases/$c.json /tmp/seed-batch-cases/; done
PYTHONHASHSEED=0 uv run python -m harness.run --cases /tmp/seed-batch-cases \
  --engine-a oracle-env/bin/python --engine-b scripts/rewrite-python \
  --results results-session30-seeds-repro

# the pin screen (self-proof mode; ALL PASS (10 case(s)) = stable at the pin)
PYTHONHASHSEED=0 uv run python -m harness.run --cases /tmp/seed-batch-cases \
  --engine-a oracle-env/bin/python --results /tmp/seed-batch-screen
```
