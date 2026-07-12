<!-- doccode: pyreason-rewrite-docs-reviews-2026-07-11-session25-adjudication-author -->
# Session 25 — recording the Phase-3 batch adjudication + the DIV-0002 loader guard (author report)

- session: 25 · 2026-07-11 · author packet
- verdict: **done** — the operator adjudication of 2026-07-11 is recorded
  across both DIV records, the batch document, and the board, and the
  DIV-0002 option-(a) guard is implemented and seam-tested; fast tier
  **271 passed** (`uv run pytest -m "not e2e"`; was 270 — one provisional
  test flipped, one guard-parity test added), the packet's one touched e2e
  **1 passed** (`uv run pytest tests/test_div_0002_reproducer.py -m e2e`,
  live oracle env).
- commits: `ec92405` (docs: the adjudication record), `8310954` (the
  DIV-0002 guard + tests + behavior-description docs), plus this report.

## Part 1 — what was recorded, and where

**The verdict of record (operator, 2026-07-11):** all 44 batch
recommendations accepted as written. A1/DIV-0001 option (a); A2/DIV-0002
option (a); B1–B34 keep matching the pin, with three direction decisions —
B17 (fp+infer_edges KeyError payload takes DIV-0002's shape whenever that
arm is ever cased), B19 (ADR 0003 confirmed as the recorded answer to the
session-6 fp-trace-asymmetry question, closing that carried item), B25
(Interval intersection proxy-arm prev-seeding blessed); B16 stays KEEP for
equivalence and remains the flagged Phase-4 hazard (never combine
`fp_version=True` with `timesteps=-1`); Part C recorded, no decisions
needed, none taken.

- `docs/divergences/DIV-0001.md` — status `queued-for-operator` →
  `adjudicated`; classification `intentional-divergence-proposed` →
  accepted intentional divergence (documented, tested intentional behavior
  per AC-6); verdict = option (a), dated 2026-07-11, adjudicating session
  25. Field set unchanged (the AC-6 seam contract); the filing history
  stays inside the classification and verdict fields.
- `docs/divergences/DIV-0002.md` — same status flip; verdict = option (a),
  2026-07-11, session 25. The observed rewrite arm and a new
  `adjudicated behavior` field describe the guard in present tense (the
  pre-adjudication acceptance is kept as the superseded
  `provisional behavior`, marked as the record of the fork). Title updated
  ("…the rewrite a stable one") to stay present-tense true.
- `docs/ledger/phase3-adjudication-batch.md` — `## Adjudication record`
  appended at the end; no existing section renumbered or edited.
- `docs/surface.md` — **no row was at `divergent-queued`** (verified:
  `grep -n "status:" docs/surface.md` shows only
  equivalent/uncovered/cased), so no status field moved; the coverage
  fraction is unchanged and the AST-scan gate
  (`tests/test_surface_inventory.py`, 6 passed) stays green with row ids
  and kinds untouched. Notes updated: `type:Query` (DIV-0001 adjudicated,
  A1), `fn:load_inconsistent_predicate_list` (DIV-0002 adjudicated with
  the new rewrite arm and message, A2), `setting:fp_version` (B19
  confirmation + B17 recorded direction + the B16 Phase-4 hazard),
  `type:Interval` (B25 proxy-arm blessing).
- `docs/adr/0003-fp-schedule-one-semantics-core.md` — read in full: it
  carries `status: accepted` and **no** awaiting-operator marker, so per
  the packet it was left alone. The "awaiting the operator's word"
  language lived in the batch document (B19), which now carries the
  confirmation.
- **B17 board-carrier deviation (recorded, not silent):** grepping the
  board for `infer_edges`/`B17`/the fp KeyError showed **no row
  previously carried the observation** (it was carried in ledgers and the
  slice-4 review only). The recorded direction was added to
  `setting:fp_version`'s notes — the row whose surface the fp-mode
  `_add_edge` arm lives under — with the observation itself restated so
  the note stands alone.

## Part 2 — the DIV-0002 guard

**Seam.** The pinned failure point is `parse_ipl`'s append into
`typed.List(Tuple((label_type, label_type)))`
(oracle/pyreason/pyreason/scripts/utils/yaml_parser.py:194): `unbox_label`
reads each Label's `_value` as a numba string (label_type.py:86-94), so
exactly the entries with a non-str `_value` are rejected — and the pinned
`Label` constructor coerces nothing, so that is exactly the non-str YAML
entries. The rewrite's guard (`ipl_pair`, `src/pyreason/_state.py`) fires
per pair inside the parse loop of
`src/pyreason/_loaders.py::load_inconsistent_predicate_list`, before the
rebind — the same logical point, preserving the pin's parse-then-assign
shape (a raise leaves the prior IPL untouched) and the pin's arm ordering
(the short-pair IndexError still fires at `labels[1]` subscripting, before
the guard; str entries pass through unchanged).

**Chosen message and rationale.**
`IPL entries must be strings; got {type(value).__name__}: {value!r}` —
e.g. `IPL entries must be strings; got int: 1`. Stable: built only from
the entry's type name and repr, deterministic for every value YAML
safe_load can produce (str/int/float/bool/None/list/dict/date); no
addresses, no environment paths. Honest: it names the offending entry and
states the actual contract (IPL labels must be strings) instead of
imitating the pin's garbage-memory code-point text, which is
unreproducible by construction (that fact lives in the DIV record).

**Guard-parity check (result: one other entry point, covered).**
`grep -rn "state.ipl"` over `src/pyreason/` finds exactly two append
sites: the loader loop (`_loaders.py:632`) and `add_inconsistent_predicate`
(`_state.py`), whose pinned twin appends into the *same* typed list
(oracle pyreason.py:629) and fails the identical unbox. The guard
therefore lives at the shared choke point `ipl_pair`, used by both; the
add path also reproduces the pin's side effect that a first failed add
leaves the IPL created-but-empty (the pin binds the empty typed list
before the failing append). No other rewrite code path constructs or
appends IPL pairs (`reset()` and the Program handoff only rebind/read).

**Tests.**
- `tests/test_rewrite_state_loaders.py::test_ipl_yaml_nonstring_entries_raise_stable_valueerror`
  — the flipped test (was `…_load_provisionally`): asserts the exact
  ValueError message at the loader seam and that the previously-held IPL
  survives the raise. `proves:` docstring updated to the adjudicated
  behavior, referencing DIV-0002 adjudicated.
- `tests/test_rewrite_state_loaders.py::test_add_inconsistent_predicate_nonstring_raises_the_same_guard`
  — new guard-parity seam test (same message via the add path;
  created-but-empty IPL side effect).
- `tests/test_div_0002_reproducer.py` — pin-side assertions **unchanged**
  (still asserts the pin's ValueError type + character-not-in-range
  message shape); only the module and test docstrings that described the
  rewrite's pre-adjudication acceptance were updated.

**No committed case changes verdict — inspection argument.** (1) Every
committed IPL fixture (`harness/fixtures/ipl.yaml`, `ipl-null.yaml`,
`ipl-missing-key.yaml`, `ipl-short-pair.yaml`, `ipl-bad.yaml`) either
carries only string entries or fails before the append seam (null → loop
never runs; missing key → KeyError at subscript; short pair → IndexError
at `labels[1]`, evaluated before the guard; bad YAML → ParserError at
safe_load) — so the guard is never reached with a rejecting value. (2) The
add path cannot be reached with non-strings by any committed case either:
the harness validates `inputs.ipl` as string pairs at case-load
(`harness/capture.py:594-598`) before any engine runs. (3) For string
inputs the guard is a pass-through (`isinstance(v, str)` then the same
`Label` construction as before). Per the test-tier discipline this is
verified by inspection, not a corpus run; the full sweep is a
phase-boundary packet.

## Test evidence (exact commands)

- `uv run pytest -m "not e2e"` → **271 passed, 4 deselected** (run
  standalone and again by the pre-commit hook on commit `8310954`).
- `uv run pytest tests/test_div_0002_reproducer.py -m e2e` → **1 passed**
  (live oracle env, 2.33s).
- `uv run pytest tests/test_surface_inventory.py -q` → **6 passed** (the
  board gate, after the notes edits).

## Deviations

- The B17 direction landed on `setting:fp_version`'s notes because no
  board row previously carried the observation (see Part 1). Nothing else
  deviates from the packet.
