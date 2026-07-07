<!-- doccode: pyreason-rewrite-docs-reviews-phase3-slice1-review -->
# Phase 3, slice 1 — independent review: the rewrite package's opening slice

- session: 16 · date: 2026-07-07 · reviewer packet (no shared context with the author)
- author commits reviewed: `bc252b3`, `b619a49` · author report:
  [2026-07-07-phase3-slice1-author.md](2026-07-07-phase3-slice1-author.md) ·
  layout: [ADR 0001](../adr/0001-rewrite-package-layout.md)
- review-fix commit: `fde0c62`
- verdict: **packet PASSES after two fixed Medium findings.** Post-fix
  evidence: fast tier **175 passed** (171 author + 4 review regression
  tests), independent 12-case rerun **12/12 pass**
  (`results-phase3-slice1-review/`), rewrite-vs-banked-oracle digests
  **85/85 equal**, overfitting probe **78/79 match** (the 1 is a documented
  numba-origin arm no case exercises, below).

## How the review was run

Every rewrite module was read side-by-side against the pinned source
(`oracle/pyreason/pyreason/pyreason.py`, `scripts/utils/{fact,rule,query}_parser.py`,
`scripts/threshold/threshold.py`, `scripts/components/label.py`,
`scripts/interval/interval.py` + `numba_types/interval_type.py:143-145`).
The fact parser, query parser, and rule parser are statement-for-statement
translations — every raise arm, message string, and quirk (space-strip,
leading-digit delta consumption, the two Query misparses, the head-bracket
re-raise sentence) was matched against the pin by eye and then by probe.
Label and Threshold are verbatim. The loaders mirror the pinned control flow
per function, including the doubled Row/Item prefixes, warn-skip arms,
partial-load-then-raise ordering, and the one unconditional
`add_fact_from_json` closing print.

The equivalence-honesty lens then went after the one place the rewrite
*cannot* be a translation: the CSV read seam, where the pin observes pandas
and the rewrite reimplements the observables over stdlib `csv`. A 74-probe
variant script (same-class inputs, none of them the committed fixtures:
different malformed bounds, different bad columns, blank lines, quoted
fields, ragged rows, non-UTF8 bytes, threshold/weights shapes, silent-
misparse variants) ran identically through `oracle-env/bin/python` and
`scripts/rewrite-python` and the canonical outcomes were diffed, plus four
targeted follow-up probes to pin exact semantics. That is what surfaced both
findings.

## Findings

### Medium (fixed) — tokenizer message line number counted physical lines, not records

`_loaders._numbered_rows` used `csv.reader.line_num` (the physical line a
record *ends* on). The pinned pandas C tokenizer reports the **record
ordinal**: a quoted field spanning two physical lines counts once, a skipped
blank line still counts one. Verified against the oracle env:

- wide row after a two-physical-line quoted record → oracle `line 2`,
  pre-fix rewrite `line 3` (probe `csv-embedded-newline-then-wide`);
- wide row after three blank lines → oracle `line 5`, matching only because
  blank records and blank lines count the same there (probes
  `csv-wide-after-blank`, `multi-blank`).

This is the exact input class the committed `unquoted-comma` fixture pins —
the fixture passed only because it has no quoted multi-line record. A
classic fixture-shaped pass; the class was not covered. **Fix:**
`_numbered_rows` now yields `enumerate(reader, start=1)` ordinals; two
regression tests pin the quoted-record and blank-line shapes
(`test_rule_csv_tokenizer_line_is_record_ordinal_not_physical_line`,
`test_rule_csv_blank_lines_count_in_tokenizer_line_number`).

### Medium (fixed) — non-UTF8 CSV leaked a raw UnicodeDecodeError

The pin wraps every non-missing-file CSV read fault as
`ValueError("Error reading CSV file {path}: {e}")` via `except Exception`.
The rewrite's deliberately narrowed net (`_TokenizeError, csv.Error,
OSError`) missed that **UnicodeDecodeError subclasses ValueError**, so a
non-UTF8 file propagated the raw decode error where the oracle raises the
wrap (probe `latin.csv`: oracle
`ValueError | Error reading CSV file ...: 'utf-8' codec can't decode byte
0xff in position 16: invalid start byte`; pre-fix rewrite
`UnicodeDecodeError | 'utf-8' codec can't decode byte 0xff ...`). The codec
text itself matched byte-for-byte, so the fix is one name in the except
tuple; pinned by
`test_rule_csv_non_utf8_file_takes_the_pinned_valueerror_wrap`.

### Low (corrected) — the ragged-short-row "deviation" was not a deviation

Author report and the `_loaders.py` docstring claimed the pinned pandas path
pads ragged-short rows with NaN (implying `'nan'` names and truthy statics).
Empirically false at the pin: `read_csv(..., dtype=str,
keep_default_na=False)` reads missing trailing cells as `''` — a short row
missing its name cell autonames `rule_1` identically in both engines (probe
`short-name.csv`). The rewrite's `''` padding was already equivalent; the
inaccurate claim is corrected in the docstring and pinned by
`test_rule_csv_short_row_pads_empty_missing_name_autogenerates`. Down-rated
to Low because the shipped behavior was right — only the documented
rationale was wrong.

### Low (documented, not fixed) — numba-origin raise on a non-numeric interval bound

`pyreason.interval.closed('a', 1)`: the oracle raises
`numba.core.errors.TypingError` (a numba compilation fault with an
environment-specific message); the rewrite raises
`ValueError("could not convert string to float: 'a'")`. No committed case or
declared `type:Interval` input class exercises a non-numeric bound, and the
numba exception type is unreproducible without numba — the same family as
the author's documented delta_t/uint16 and weights-ndarray gaps. Recorded
here so it is never a silent absorption: if a future case wants this arm, it
is an operator-adjudicated divergence, not a message to hand-match.

### Verified clean (the things hunted for and not found)

- **No overfitting beyond the tokenizer line number.** All fact-text,
  rule-text, query, threshold, weights, JSON-loader, and rules-file variant
  probes (74-probe script + 4 targeted) match the oracle post-fix, message
  text and warning lists included — 78/79 with the numba arm above the only
  exception.
- **No second core, no dead scaffolding.** Every facade function, RuleIR
  getter, and loader arm maps to a committed case probe or seam test; the
  18-knob Settings is the packet's one allowed exception and its defaults
  and TypeError texts match `pyreason.py:43-456` knob-for-knob (`canonical`
  correctly aliasing the `persistent` store).
- **Explicit-state shape holds.** All cross-call state sits on `EngineState`;
  the facade holds exactly one and delegates; parsers and loaders are pure
  functions over it (AC-5 shape as chartered).
- **`proves:` docstrings are accurate** — spot-checked all 67 author tests
  against their assertions; none overstates.

## Independent rerun (post-fix, verdicts of record for this review)

`PYTHONHASHSEED=0 uv run python -m harness.run --cases <staged-12> --engine-a
oracle-env/bin/python --engine-b scripts/rewrite-python --results
results-phase3-slice1-review` — per case 4 fresh captures, same-engine
repeats digest-stable, A-vs-B equal:

| case | verdict | | case | verdict |
|---|---|---|---|---|
| accessors-fresh-state | pass | | rule-from-csv-malformed | pass |
| fact-from-csv-malformed | pass | | rule-from-json-malformed | pass |
| fact-from-json-malformed | pass | | rule-text-malformed | pass |
| fact-text-malformed | pass | | rules-from-file-malformed | pass |
| interval-ops | pass | | threshold-construct | pass |
| label-ops | pass | | query-construct | pass |

**12/12 ALL PASS.** Cross-check against the banked phase-boundary sweep:
every rewrite `b1` probe digest equals the read-only `results/<case>/a1.json`
oracle digest — **85/85**. Engine identity re-verified from the artifacts:
every `a1` ran `oracle-env/bin/python` with pyreason 3.6.0, every `b1` ran
`.venv/bin/python` with 0.1.0.dev0. Shadowing re-verified live both
directions with the repo root explicitly first on `sys.path` (engine A
resolves the oracle-env site-packages package; engine B resolves
`src/pyreason/__init__.py`). Zero divergences in the rerun → no DIV records.

## surface.md and hygiene

- **Flips honest.** Exactly two `status:` lines changed in `b619a49`
  (`type:Interval`, `type:Label`); each row's full `cases` list
  (interval-ops / label-ops) sits inside the 12 and passed the independent
  rerun; every other touched row stays `cased`. 2/52 equivalent, 50 cased.
  Inventory gate green (in the 175).
- **Gates.** `git -C oracle/pyreason status --porcelain` empty, pin at
  `e1a94af3`; no installs or dependency changes (the pyproject diff is the
  pytest `pythonpath` entry the packet explicitly allows); `uv.lock`
  untouched; banked `results/` and `results-phase3-slice1/` read-only-used;
  no writes outside the repo (probe files in the session scratchpad); no
  security framing in any reviewed file or commit message;
  `results-phase3-slice1-review/` added to `.gitignore` beside its siblings.

## Reproduction (from the repo root)

```
uv run pytest -m "not e2e"                       # 175 passed, 2 deselected

mkdir -p /tmp/phase3-slice1-review-cases && for c in accessors-fresh-state \
  fact-from-csv-malformed fact-from-json-malformed fact-text-malformed \
  interval-ops label-ops query-construct rule-from-csv-malformed \
  rule-from-json-malformed rule-text-malformed rules-from-file-malformed \
  threshold-construct; do cp harness/cases/$c.json /tmp/phase3-slice1-review-cases/; done
PYTHONHASHSEED=0 uv run python -m harness.run --cases /tmp/phase3-slice1-review-cases \
  --engine-a oracle-env/bin/python --engine-b scripts/rewrite-python \
  --results results-phase3-slice1-review        # 12/12 ALL PASS
```

## Final packet verdict

**PASS.** 0 High · 2 Medium (both fixed in `fde0c62`, each with a
regression test and an oracle-env verification probe) · 2 Low (1 corrected
documentation claim, 1 documented numba-origin gap). The slice's equivalence
claims stand on the post-fix reruns above.
