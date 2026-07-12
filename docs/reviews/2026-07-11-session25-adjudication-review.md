<!-- doccode: pyreason-rewrite-docs-reviews-2026-07-11-session25-adjudication-review -->
# Session 25 — independent review of the adjudication recording + DIV-0002 guard

- session: 25 · 2026-07-11 · reviewer-fixer packet (no shared context with
  the author)
- scope reviewed: `ec92405` (adjudication recorded), `8310954` (the
  DIV-0002 option-(a) guard), `41f4397` (author report), against the
  operator adjudication of 2026-07-11, the AC-6 record contract, and the
  pinned source itself.
- verdict: **approved with fixes** — the adjudication is recorded
  faithfully (nothing missing, nothing invented) and the guard is at the
  right seam with the right type and correct parity, verified live against
  the pin; three staleness defects in the trailing docs were found and
  fixed in `b8b4774`.

## Seam verification against the pinned source (the load-bearing check)

Read directly at the pin (oracle e1a94af33e1f, untouched):

- `yaml_parser.py:187-196` — `parse_ipl` runs `yaml.safe_load`, builds a
  `numba.typed.List(Tuple((label_type, label_type)))`, and appends
  `(Label(labels[0]), Label(labels[1]))` per pair inside the loop; the
  caller (`pyreason.py`, `load_inconsistent_predicate_list`) assigns
  `__ipl = parse_ipl(path)` only after a complete parse. So the pin's
  failure point is per-pair, inside the loop, before the rebind — and the
  rewrite's guard (`ipl_pair` called from the loader's loop,
  `src/pyreason/_loaders.py:636`) fires at exactly that logical point,
  with the raise leaving the prior IPL untouched, matching the pin's
  parse-then-assign shape.
- `label_type.py:86-94` — `unbox_label` reads each Label's `_value` via
  `c.unbox(types.string, ...)` with no type check, so the rejected class
  is precisely "non-str `_value`", and the pinned `Label` constructor
  (`label.py`) stores its argument raw (coerces nothing). The rewrite's
  `isinstance(value, str)` guard rejects exactly that class.
- `pyreason.py:620-629` — `add_inconsistent_predicate` binds the empty
  typed list first, then appends into the same typed list, so it fails the
  identical unbox — and a first failed add leaves the IPL
  created-but-empty. The rewrite's add path reproduces both (guard raises
  after `state.ipl = []` is bound; asserted by the new parity test).

**Live pin probes** (oracle-env python, one-off scripts — not the corpus,
not the e2e suite):

- mixed pair `["a", 1]` through the pinned loader → `ValueError:
  character U+4f46710 is not in range [U+0000; U+10ffff]` at `_append`,
  process dies before COMPLETED. The rewrite on the same file raises
  `IPL entries must be strings; got int: 1` — same seam, same type,
  naming only the offending entry.
- a **str subclass** through the pinned add path → accepted (COMPLETED;
  a genuine PyUnicode object unboxes cleanly, type check or not). The
  rewrite accepts it too (`isinstance(value, str)` is True for
  subclasses; probed: the pair lands in `state.ipl`). So the guard
  rejects nothing the pin accepts.

Seam claim: **confirmed** — equivalent seam, same exception type
(`builtins.ValueError`), same rejected input class, no over-rejection.

## Guard parity

`grep -rn "ipl"` over `src/pyreason/` finds exactly two IPL append sites —
`_loaders.py:636` and `_state.py:144` — both routed through `ipl_pair`.
`_state.py:300-301` (program handoff) and `reset()` only rebind/read
(`reset()` does not touch `state.ipl` at all, matching the pinned
partial-clear). The facade and tests reach the add path only through
`_state.add_inconsistent_predicate`. Parity: **confirmed**.

## Adjudication-recording audit

Every operator decision is recorded, correctly and only as decided: A1 and
A2 verdicts (option (a), dated 2026-07-11, session 25) in the DIV records;
the `## Adjudication record` appended to the batch document (A1/A2, B17
direction, B19 ADR-0003 confirmation, B25 proxy-arm blessing, B16 as the
Phase-4 hazard with the exact fp_version/timesteps=-1 prohibition, Part C
recorded with no decisions); board notes on type:Query, type:Interval,
setting:fp_version, fn:load_inconsistent_predicate_list. Nothing invented
beyond the batch's own recommendations. ADR 0003 carries
`status: accepted` and no awaiting-marker — correctly left alone. The
author's B17 deviation (no board row previously carried the observation;
direction landed on setting:fp_version's notes) checks out and was
recorded, not silent. The e2e reproducer's pin-side assertions are
byte-identical (docstrings only changed). Both DIV records carry the full
AC-6 field set (id · case ids · surface items · observed · first-seen ·
classification · reproducer · status · provisional behavior · verdict).

## No-case-changes-verdict argument — checked by inspection (no corpus run)

(1) All five committed IPL fixtures verified by reading them: `ipl.yaml`
string pair; `ipl-null.yaml` null (loop never runs); `ipl-missing-key.yaml`
KeyError at subscript; `ipl-short-pair.yaml` IndexError at `labels[1]`,
evaluated in the argument position **before** `ipl_pair` is entered;
`ipl-bad.yaml` ParserError at safe_load. (2) `harness/capture.py:594-598`
verified: `inputs.ipl` is validated as string pairs at case-load, so no
committed case can reach the add path with a non-string. (3) For strings
the guard is a pass-through to the identical `Label` construction. The
argument holds.

## Findings

1. **DIV-0002 `reproducer` field stale (moderate — broken pointer in an
   AC-6 field; FIXED, `b8b4774`).** The field still named
   `test_ipl_yaml_nonstring_entries_load_provisionally` — deleted by the
   same commit that flipped the record — and described "the rewrite's
   current acceptance, marked provisional pending this record's
   adjudication" on a record whose status is `adjudicated`. Now names the
   two seam tests that exist.
2. **`fn:add_inconsistent_predicate` board row stale (moderate — board
   accuracy; FIXED, `b8b4774`).** The row owns the `malformed-non-str`
   input class, and the guard changed the rewrite's behavior at exactly
   this boundary, but its notes still read only "no dedup or name
   validation at this boundary". Guard parity is a headline claim of the
   code commit and the DIV record names this function — the row it lives
   on must say so. The note now carries the guard, the created-but-empty
   side effect, and the parity seam test.
3. **DIV-0002 `classification` tense (minor — consistency; FIXED,
   `b8b4774`).** DIV-0001's classification was updated to its
   post-adjudication state; DIV-0002's still read present-tense
   pre-guard ("the rewrite's plain-list transcription does not carry").
   Reworded as-filed/past-tense with the adjudication outcome appended.
4. **Down-rated, no change:** `docs/analysis/surface/facts-and-graph.md`
   lines 113/134 describe `malformed-non-str` speculatively ("behavior
   depends on Label accepting it") — but analysis docs are dated pin
   analyses, superseded by the DIV record; not churned. Historical
   ledgers/reviews naming the old provisional test are records of their
   sessions; correctly untouched (the author left them; agreed).

## Test evidence (after fixes)

- `uv run pytest -m "not e2e"` → **271 passed, 4 deselected** (matches the
  author's count; rerun standalone and by the pre-commit hook).
- `uv run pytest tests/test_div_0002_reproducer.py -m e2e` → **1 passed**
  (live oracle env).
- `uv run pytest tests/test_surface_inventory.py -q` → **6 passed** (board
  gate green after the row-note fix).
