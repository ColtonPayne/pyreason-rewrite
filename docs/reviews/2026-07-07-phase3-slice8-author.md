<!-- doccode: pyreason-rewrite-docs-reviews-2026-07-07-phase3-slice8-author -->
# Phase 3, slice 8 — the IPL file family (author report)

- session: 23 · 2026-07-07 · author packet
- verdict: **4/4 IPL-family cases equivalence PASS** oracle-vs-rewrite
  (`results-phase3-slice8/report.json`, exit 0, ALL PASS — 4 fresh-process
  captures per case, same-engine repeats digest-stable a1==a2 and b1==b2,
  cross-engine a==b, PYTHONHASHSEED=0); fast tier **269 passed** (265
  existing + 4 new seam tests)
- code: `409298e` (the IPL YAML loader + facade + 4 seam tests), `5de8c72`
  (board flips + slice-8 gitignore), plus this commit (report)
- board: the last 2 rows flip to `equivalent` — **52/52**
- DIV records: none — no cross-engine mismatch on any committed case
- ADR: none — rationale below

## Where the session started

The IPL family was the board's last un-run gate (session 22's NEXT,
verbatim): 4 committed cases (`ipl-load-basic`, `ipl-load-malformed`,
`ipl-load-null-overwrite`, `ipl-atom-trace-off-trace`) and 5 committed
fixtures existed, the harness already carried
`load_inconsistent_predicate_list` in its `APPLY_OPS`, and pyyaml 6.0.3 was
already in the campaign env (operator-approved, `pyproject.toml` +
`uv.lock`; verified live: `uv run python -c "import yaml;
print(yaml.__version__)"` → 6.0.3, and the oracle env's own pinned pyyaml
is also 6.0.3 — untouched). The one missing piece was the rewrite side:
the facade had `add_inconsistent_predicate` but no
`load_inconsistent_predicate_list` at all. No installs, no dependency
changes, nothing added anywhere.

## What landed (AC-2)

**`src/pyreason/_loaders.py::load_inconsistent_predicate_list`** (~10
lines of logic) plus the one-line facade delegate in
`src/pyreason/__init__.py`, mirroring the pinned shape read directly from
the read-only oracle (`pyreason.py:611-618` →
`yaml_parser.parse_ipl`, `yaml_parser.py:187-196`):

- **safe-load only** — `yaml.safe_load(file)` is the single YAML entry
  point, exactly the pin's call; no other loader class is reachable.
- **zero validation of its own** — every malformed arm is the underlying
  operation's raise, in the pin's order: `open()` first
  (FileNotFoundError), `safe_load` second (yaml.parser.ParserError whose
  message embeds the stream path — the harness resolves both engines'
  fixture paths against the same repo root, so the text compares exactly),
  the `['ipl']` subscript third (KeyError, message the quoted key
  `"'ipl'"`), and per-pair `labels[1]` last (IndexError 'list index out of
  range').
- **null-'ipl:' semantics** — a null value fails the pin's `is not None`
  guard and reduces to an **empty list, not None**: a null file still
  overwrites.
- **wholesale rebind, parse-first** — the state's IPL is replaced only
  after a complete parse (the pin's parse-then-assign split across
  `parse_ipl`/the global rebind); any raise leaves the prior IPL
  untouched. Contrast `add_inconsistent_predicate`'s append — the
  overwrite-not-merge distinction is exactly what
  `ipl-load-null-overwrite` banks.

**Why no ADR:** the loader is a pinned-shape transcription into the
existing `_loaders.py` family (ADR-established explicit-state facade
pattern, one more file-taking entry point beside the five committed
loaders). No new architecture, no contradicted decision; the design
rationale lives in the module docstring and this report.

## Per-case verdicts (all PASS, `results-phase3-slice8/`, one invocation)

Wall-clock from the artifacts' capture-internal timing (import_s / summed
step seconds; engine A = pinned oracle, engine B = rewrite):

| case | verdict | oracle a1 (s) | oracle a2 (s) | rewrite b1/b2 (s) |
|---|---|---|---|---|
| ipl-load-basic | pass | 1.41 / 2.88 | 1.31 / 2.90 | 0.07 / ~0.000 |
| ipl-load-malformed | pass | 1.38 / — | 1.43 / — | 0.07 / — |
| ipl-load-null-overwrite | pass | 1.41 / 3.06 | 1.49 / 3.06 | 0.11 / ~0.000 |
| ipl-atom-trace-off-trace | pass | 1.50 / 3.00 | 1.35 / 3.08 | 0.11 / ~0.000 |

Screen-then-confirm ran on the cheapest case: `ipl-load-malformed` (no
reason step) screened standalone first (PASS), the full 4 committed after.
Total run ~25 s wall — no numba-compile-heavy signatures in this family.

**What the 4 passes prove, semantically** (spot-read from the banked
artifacts, compared digest-equal cross-engine):

- **ipl-load-basic** — the yaml-loaded [popular, unpopular] pair's effect
  through reason(): 6 complement `unpopular [0.0,0.0]` rows named
  `IPL: popular`, Triggered By `IPL`, in the node trace (the happy-basic
  class observed through reasoning, not a stored value).
- **ipl-load-malformed** — all four raise arms banked as four **distinct
  exception types with exact messages**: `builtins.FileNotFoundError`
  (`[Errno 2] ... no-such-ipl.yaml`), `builtins.KeyError` (`'ipl'`),
  `builtins.IndexError` (`list index out of range`), and
  `yaml.parser.ParserError` (multi-line, embedding the repo-resolved
  `ipl-bad.yaml` path + parse position) — byte-equal cross-engine, no
  canonicalization anywhere.
- **ipl-load-null-overwrite** — `add_inconsistent_predicate('popular',
  'unpopular')` first, then the null-'ipl:' file: **zero** unpopular rows
  anywhere in the trace — the wholesale-overwrite semantics and the
  bound-ipl-null acceptance in one observation (ipl-load-basic is the
  rows-present twin).
- **ipl-atom-trace-off-trace** — with atom_trace off, the saved node CSV
  shows `Occurred Due To` = `-` on every fact- and rule-triggered popular
  row and `IPL: popular` on all 6 unpopular complement rows —
  output.py:23-25's r[7]-name fallback firing exactly where the pin makes
  it reachable (session-12 H1, now banked cross-engine). This also closes
  `fn:save_rule_trace`'s last un-run covering case.

## Seam tests (fast tier 269 = 265 + 4; AC-3)

All in `tests/test_rewrite_state_loaders.py`, each with a `proves:`
docstring, each reading a **real committed YAML fixture** through the
loader — the same files the equivalence cases load:

- `test_ipl_yaml_happy_fixture_replaces_prior_pairs` — the pair loads as a
  Label pair AND replaces (never merges with) a previously-added pair.
- `test_ipl_yaml_null_value_loads_an_empty_list` — null-'ipl:' loads `[]`
  (not None), erasing a prior add.
- `test_ipl_yaml_malformed_arms_raise_and_leave_prior_ipl` — the four
  distinct exception types with exact messages where deterministic, and
  the parse-before-rebind property (prior IPL untouched after every
  raise).
- `test_facade_ipl_loader_reads_through_the_public_api` — the public
  `pyreason.load_inconsistent_predicate_list` I/O seam the harness
  actually drives, landing the pair in the module's one EngineState.

## Board (AC-4)

Both remaining `cased` rows flip to `equivalent` by the mechanical rule
(full case list ⊆ the oracle-vs-rewrite passed set across
`results-phase3-slice1..8`, checked mechanically over every
`report.json`):

- `fn:load_inconsistent_predicate_list` — all 4 covering cases passed this
  slice.
- `fn:save_rule_trace` — save-rule-trace-basic/-atom-trace-off/-store-off/
  -clause-reorder (slice 6) + ipl-atom-trace-off-trace (this slice).

New fraction: **52/52** (was 50/52). Inventory gate green
(`tests/test_surface_inventory.py`, 6 passed). No board row remains
`uncovered`, `cased`, or `divergent-queued`.

## Divergences and observations (AC-5)

- **DIV records: none.** All 4 cases compare equal; the compare layer is
  untouched — nothing absorbed, nothing loosened.
- **No new oracle-bug candidates.** The pinned behaviors banked here (the
  zero-validation loader, the four raw raise arms, the null-overwrite)
  were already recorded on the board as pin behavior; nothing newly
  suspect surfaced.
- Observation: both environments carry pyyaml 6.0.3, so the ParserError
  text is version-identical by construction; a future oracle-env rebuild
  pinning a different pyyaml could move that message — the fixture-level
  exact compare would catch it loudly, not silently.

## What remains un-run on the board after this slice (for the boundary sweep)

- **Zero rows remain un-run**: every one of the 52 rows is `equivalent`,
  each covering case banked as an oracle-vs-rewrite PASS in some slice.
  What has **never** run is the whole corpus in **one invocation** — every
  banked verdict is slice-scoped, and `report.json` is last-writer-wins
  per results dir (the carried sweep-durability follow-up). That single
  full-corpus run is exactly the boundary-sweep session's job.
- **Adjudication batch, prepared and carried**: DIV-0001 (the
  query-filter recursion guard, `docs/divergences/DIV-0001.md`) plus the
  oracle-bug-candidate observations recorded in board notes and prior
  reports (restart=True trace-KeyError family, the graphml silent
  coercion quirks O1/O2, fp+`infer_edges` exception-payload asymmetry) —
  the operator adjudicates the whole batch at the Phase-3 boundary per
  the session-22 instruction.
- **Uncovered input classes / named-unobserved facets** stay recorded
  per-row in `docs/surface.md` notes (e.g. bound-ipl-empty-list and the
  IPL-survives-reset() interaction on this slice's row; the
  registrand-behavior L3/L4 arms; edge-rule head-function forms) — none
  gate a row, all are post-boundary packet material.

## Deviations from the packet

None. No installs or dependency changes anywhere (both envs' pyyaml left
exactly as found); no oracle-tree writes (byte-clean at `e1a94af33e1f`,
checked post-run); no full corpus sweep (fast tier + the 4 packet cases +
the 1-case screen only).

## Repro

```
uv run pytest -m "not e2e"          # fast tier: 269 passed, 3 deselected
mkdir -p /tmp/slice8-cases && for c in ipl-load-basic ipl-load-malformed \
  ipl-load-null-overwrite ipl-atom-trace-off-trace; do \
  cp harness/cases/$c.json /tmp/slice8-cases/; done
PYTHONHASHSEED=0 uv run python -m harness.run --cases /tmp/slice8-cases \
  --engine-a oracle-env/bin/python --engine-b scripts/rewrite-python \
  --results results-phase3-slice8-review   # 4/4 ALL PASS (fresh dir for a re-run)
```
