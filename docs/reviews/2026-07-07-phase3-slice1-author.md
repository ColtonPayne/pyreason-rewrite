<!-- doccode: pyreason-rewrite-docs-reviews-phase3-slice1-author -->
# Phase 3, slice 1 — author report: the rewrite package's opening slice

- session: 16 · date: 2026-07-07 · author packet
- verdict: **12/12 oracle-vs-rewrite PASS** (`results-phase3-slice1/report.json`),
  fast tier **171 passed** (104 preexisting + 67 new), zero DIV records needed
- code commit: `bc252b3`; layout decision: [ADR 0001](../adr/0001-rewrite-package-layout.md)

## What was built, and why shaped that way

`src/pyreason/` — the rewrite package's opening slice, covering exactly the
surface the 12 reason-free corpus cases and their seam tests consume:

| piece | file(s) | shape rationale |
|---|---|---|
| module-global facade | `__init__.py` | the pinned public surface is module-global (`import pyreason as pr`), and the capture drives exactly that; every function is a one-line delegation |
| explicit state | `_state.py` (`EngineState` + `add_rule`/`add_fact`) | the charter's no-hidden-state bar: everything the oracle keeps in module globals lives on one constructible, swappable object; the facade holds exactly one |
| settings | `_settings.py` | all 18 pinned knobs via one validating descriptor class (`_Knob`), pinned defaults + TypeError texts; `canonical` aliases the `persistent` store as at the pin. Full-surface on purpose — the packet's one allowed exception (rationale in ADR 0001 §Decision 5) |
| value types | `interval.py`, `label.py`, `threshold.py` | pure-Python reimplementations of the pinned proxy/plain classes, including the proxy-arm prev-bound seeding, the get_value-before-isinstance AttributeError, and the unvalidated `thresh` |
| text-DSL parsers | `_fact_parser.py`, `_rule_parser.py`, `_query_parser.py` | statement-for-statement translations of the pinned parsers so every raise arm fires on the same inputs with the same text; numba containers become plain lists |
| public constructors | `rule.py`, `fact.py`, `query.py` | pinned signatures, eager parsing in `__init__` (validating entry points, not retrofits) |
| rule record | `_rule_ir.py` | stores the parser's full output; exposes only the getters today's surface consumes |
| loader family | `_loaders.py` | the five pinned loaders as pure functions over `EngineState`; row/item wrap-and-rewrap structure mirrored so doubled prefixes, warn-skip arms, and partial loads reproduce; CSV read through stdlib `csv` reproducing the observable pandas arms |
| engine-B wrapper | `scripts/rewrite-python` | how the harness reaches the package without any install (ADR 0001) |

Deliberately reproduced (not repaired) oracle behaviors, each carried by a
banked case and a seam test: Query's two silent misparses, Label's
plain-string equality raise, inverted intervals constructing unvalidated,
Threshold's unvalidated `thresh` + IndexError shape fault,
`add_rules_from_file`'s name gaps and raise-after-partial-load,
the loaders' duplicate-name raise after earlier rows loaded, and
`add_fact_from_json`'s verbose-ungated closing print. Improving any of these
is an AC-6 adjudication proposal, not a slice-1 decision.

## Acceptance criteria, answered

1. **Package + ADR + shadowing.** Package exists as above;
   `docs/adr/0001-rewrite-package-layout.md` committed (sets the MADR-lite,
   `NNNN-slug.md` convention). Shadowing verified both directions with the
   repo root explicitly on sys.path (capture conditions):
   engine A resolves `oracle-env/.../site-packages/pyreason/__init__.py`,
   version 3.6.0; engine B resolves `src/pyreason/__init__.py`, 0.1.0.dev0.
   The run artifacts carry the same evidence
   (`results-phase3-slice1/*/a1.json` engine = oracle-env executable /
   pyreason 3.6.0; `b1.json` = .venv executable / 0.1.0.dev0).
2. **Fast tier.** `uv run pytest -m "not e2e"` → **171 passed, 2 deselected**
   (also enforced by the pre-commit hook on every commit here). 67 new seam
   tests across `tests/test_rewrite_value_types.py`,
   `tests/test_rewrite_dsl_parsers.py`, `tests/test_rewrite_state_loaders.py`,
   every one with a `proves:` docstring; malformed-input assertions use the
   banked message text verbatim.
3. **12-case run.** 12/12 pass, table below. Artifacts under
   `results-phase3-slice1/` (gitignored like `results/` — verdict of record
   is `report.json` + this table). **Zero divergences → no DIV records.**
   Additionally, every rewrite `b1` probe digest equals the banked
   phase-boundary sweep's oracle `a1` digest (`results/<case>/a1.json`),
   85/85 probes across the 12 cases — the rewrite matches not just a fresh
   oracle run but the banked verdict-of-record bytes.
4. **surface.md.** Rows flipped to `equivalent`: **`type:Interval`**
   (cases: interval-ops) and **`type:Label`** (cases: label-ops) — the only
   two rows whose full `cases` lists sit inside the 12. Every other row
   touched by these cases (the loader fn rows, type:Rule/Fact/Query/Threshold,
   the dsl rows, fn:get_* rows, setting:verbose) keeps `cased`: their case
   lists include reason-bearing cases outside this packet. Coverage:
   **2/52 rows equivalent-or-adjudicated (3.8%)**, from 0/52. Inventory gate
   green (in the 171).
5. **Hygiene.** All work committed; `git -C oracle/pyreason status
   --porcelain` empty and the oracle pin untouched; no installs, no
   dependency or build-system changes (pytest `pythonpath` gained `"src"` —
   a test-runner path entry, per packet explicitly not an install); no
   writes outside the repo (scratch files in the session scratchpad);
   banked `results/` unmodified (read only).

## Per-case verdicts (oracle-vs-rewrite, 4 fresh captures each)

Wall-clock is per full case (a1+a2+b1+b2 + judging), measured by a separate
identical per-case run; the verdicts of record are the single combined run
in `results-phase3-slice1/report.json` (identical 12/12 pass).

| case | verdict | probes | wall |
|---|---|---|---|
| accessors-fresh-state | pass | 4 | 3.0s |
| fact-from-csv-malformed | pass | 4 | 3.0s |
| fact-from-json-malformed | pass | 6 | 3.3s |
| fact-text-malformed | pass | 16 | 3.0s |
| interval-ops | pass | 4 | 3.4s |
| label-ops | pass | 2 | 3.0s |
| query-construct | pass | 8 | 3.1s |
| rule-from-csv-malformed | pass | 5 | 5.2s |
| rule-from-json-malformed | pass | 7 | 3.1s |
| rule-text-malformed | pass | 13 | 4.2s |
| rules-from-file-malformed | pass | 5 | 5.2s |
| threshold-construct | pass | 11 | 3.0s |

## Hand-matched exception strings (third-party-origin text reproduced with stdlib)

Exactly one message class originates in a library the rewrite env lacks:

- **pandas C-tokenizer text** (`rule-from-csv-malformed / unquoted-comma`):
  `Error tokenizing data. C error: Expected {n} fields in line {m}, saw {k}\n`
  — trailing newline included — raised when a row is wider than the first
  row, inside the oracle's own `Error reading CSV file {path}: ` wrap.
  Reproduced verbatim as `_TOKENIZER_MSG` in `src/pyreason/_loaders.py`;
  proven equal by the case pass and by
  `test_rule_csv_wide_row_raises_pinned_tokenizer_text`.

Not hand-matched (same stdlib text in both interpreters, verified 3.10.20 vs
3.13.11 before coding): `float()` conversion messages, `json` decode
position messages, `IndexError: tuple index out of range`, `open()`'s
`[Errno 2]` text. The pandas `EmptyDataError` arm is behavioral (warn +
return, no compared message) and is reproduced by the empty-rows check.

## Deviations from the pin, all in unexercised arms (honest-gap list)

None of these is observable by any committed case; each is a candidate for a
future case before anything relies on it:

- **Ragged-short CSV rows** are padded with `''`; pandas pads with NaN
  (which would coerce `static` to True and name to `'nan'`-ish shapes).
  Recommend a `fact-from-csv` ragged-row case when the CSV rows next open.
- **Rule `weights`** validate as a float list, not an ndarray: identical
  reachable outcomes for the list input the public constructor exposes; the
  pinned dtype-check message arm is unreachable in this implementation.
- **`delta_t`** is a plain int; the pinned `numba.types.uint16` wrap above
  65535 is not reproduced.
- **Read-wrap excepts** are narrowed to the reachable fault families
  (`csv.Error`/`OSError`/tokenizer; `OSError`/`UnicodeDecodeError` for JSON)
  where the pin catches all `Exception` — same observable arms, narrower net.

## Reproduction commands (from the repo root)

```
# fast tier (AC-2 evidence)
uv run pytest -m "not e2e"

# shadowing check, both directions (AC-1 evidence)
oracle-env/bin/python -c "import sys; sys.path.insert(0, '.'); import pyreason; print(pyreason.__file__, pyreason.__version__)"
scripts/rewrite-python  -c "import sys; sys.path.insert(0, '.'); import pyreason; print(pyreason.__file__, pyreason.__version__)"

# the 12-case oracle-vs-rewrite run (AC-3 evidence)
mkdir -p /tmp/phase3-slice1-cases && for c in accessors-fresh-state \
  fact-from-csv-malformed fact-from-json-malformed fact-text-malformed \
  interval-ops label-ops query-construct rule-from-csv-malformed \
  rule-from-json-malformed rule-text-malformed rules-from-file-malformed \
  threshold-construct; do cp harness/cases/$c.json /tmp/phase3-slice1-cases/; done
PYTHONHASHSEED=0 uv run python -m harness.run --cases /tmp/phase3-slice1-cases \
  --engine-a oracle-env/bin/python --engine-b scripts/rewrite-python \
  --results results-phase3-slice1

# rewrite-vs-banked-sweep digest cross-check (85/85 probes)
uv run python -c "
import json
cases = [p.stem for p in __import__('pathlib').Path('/tmp/phase3-slice1-cases').glob('*.json')]
assert all(json.load(open(f'results/{c}/a1.json'))['digests']
           == json.load(open(f'results-phase3-slice1/{c}/b1.json'))['digests']
           for c in cases), 'digest mismatch'
print('ALL MATCH', len(cases), 'cases')"
```

## Queued-ask recommendations

- **pyyaml (already queued by the orchestrator):** unchanged —
  `load_inconsistent_predicate_list` and `ipl-load-malformed` stay out until
  the operator adjudicates the dependency. No part of this slice pre-shapes
  that decision.
- **Packaging (`[build-system]` / editable install):** **not recommended
  now.** The src-tree + wrapper + pytest-pythonpath layout covers every
  consumer this campaign has (harness, fast tier) with zero install surface;
  real packaging only earns its keep if an external consumer appears. ADR
  0001 records that this is a decision to revisit deliberately, not drift
  into.
