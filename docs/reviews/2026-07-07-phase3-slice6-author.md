<!-- doccode: pyreason-rewrite-docs-reviews-2026-07-07-phase3-slice6-author -->
# Phase 3, slice 6 — the output surface (author report)

- session: 21 · 2026-07-07 · author packet
- verdict: **13/13 equivalence PASS** oracle-vs-rewrite (`results-phase3-slice6/report.json`, exit 0, ALL PASS; 4 fresh-process captures per case, same-engine repeats digest-stable, PYTHONHASHSEED=0); fast tier **257 passed** (242 existing + 15 new seam tests)
- code: `8a7d961` (engine + 15 seam tests), `9dfcbbd` (results-dir gitignore), `b69f7b5` (board flips), plus this commit (report)
- board: 18 surface rows flip to `equivalent` — **47/52**
- DIV records: none — no cross-engine mismatch surfaced on any committed case
- ADR: none — ADRs 0002/0003 still hold unchanged (rationale below)

## Where the session started

None of the packet's four families had a rewrite surface to hit:

- **output-to-file / output-file-name (4 cases)** — the rewrite's `reason()`
  never consulted `output_to_file` or `output_file_name`; the `output_file`
  probe would have read the confined directory back empty on the on-arms.
- **memory-profile (3 cases)** — no profiled branch existed; the pinned
  branch's backend (`memory_profiler`) is a dependency this campaign never
  installs, so the observable output shape needed a stdlib-only equivalent.
- **save_rule_trace (4 cases)** — the facade had no `save_rule_trace`
  binding at all; the probe would have failed capture on a missing binding.
- **reason-queries (2 cases)** — `filter_ruleset` existed (written with the
  reorder plumbing) but had never been consumed by a committed case, and the
  zero-survivor arm's pinned raise had no reproduction.

The slice therefore reduced to: land the `reason()`-adjacent output
machinery inside the existing one-core design, honor the banked
query-filter recursion-crash contract, seam-test the I/O, and bank the
13-case proof.

## The pinned semantics, and how the rewrite reproduces them

**The stdout redirect (pyreason.py:1511-1514/:1541-1542).** `reason()`
stamps `time.strftime('%Y%m%d-%H%M%S')` and, with `output_to_file` on,
rebinds the process's `sys.stdout` to `./{output_file_name}_{stamp}.txt`
opened for **append** — then `_reason` re-opens the same name at its own
top, and nothing ever restores or flushes the rebind. The rewrite's
`_state.reason`/`_state._reason` reproduce both open sites (including the
double-open — the first file object takes no writes in either engine), so
the whole verbose reasoning print stream lands in the file: the pinned
`Filtering rules based on queries` (printed under verbose whether or not
queries exist), the edge-heavy `Optimizing rules...` line, `Timestep: 0..2`,
the blank-line-prefixed `Converged at time: 2`, and
`Fixed Point iterations: 3` — all already present at the rewrite's
interpretation-loop print sites (deliberately mirrored in earlier slices,
proven byte-for-byte for the first time here: the redirect-file contents
compare exactly, `A==B content: True` on every capture pair). The name
knob interpolates verbatim (`campaign_redirect_<stamp>.txt`), and with the
redirect off a set name writes nothing anywhere — the inert case's probe
reads the confined directory back empty in both engines.

**The memory-profile line (pyreason.py:1517-1527), stdlib-only (AC-2).**
The pin wraps either dispatch arm in
`mp.memory_usage(..., max_usage=True, retval=True)` and prints
`\nProgram used {peak} MB of memory` after the reasoning completes. Only
the line's fixed text and having-a-number shape are contractual — the
number is run-varying measurement in both engines (screened 103.20 vs
103.53 MB at case authoring) and the harness's operator-approved
`canonicalize_peak_mb` reduces exactly it to `<peak-mb>`. The rewrite
measures peak RSS with the stdlib `resource` module
(`ru_maxrss` before/after, bytes on darwin) — **no memory_profiler, no
new dependency of any kind** — and prints the pinned line verbatim around
its own number. Seam-tested both ways: the line matches the harness's
PEAK_MB_RE shape, and a profiled `reason()` leaves `memory_profiler`
absent from `sys.modules`. The interaction case's redirect file carries
output-to-file-on's exact print shape plus the canonicalized peak line as
its last line, digest-equal cross-engine.

**save_rule_trace (pyreason.py:1645-1655, output.py:99-105).** The pinned
call asserts change storage on (the get_rule_trace-shared message — banked
verbatim by the store-off case as `builtins.AssertionError`), then writes
`rule_trace_{nodes,edges}_{timestamp}.csv` under the caller's folder via
pandas `to_csv(index=False)`. The rewrite renders the same trace frames the
(already-proven) `get_rule_trace` view builds and writes them with the
stdlib csv module to the pandas byte shape: comma-delimited, QUOTE_MINIMAL
double-quote quoting, `os.linesep` row ends, None/NaN cells empty, every
other cell str()-rendered (clause-grounding lists as their Python reprs,
quoted where commas demand). The timestamp is the reason-time stamp now
carried on `EngineState.timestamp`, canonicalized by the probe under the
recorded run-schedule rationale; contents compare exactly. The basic case
pins the happy path + folder passthrough (default `./` and a named
subfolder receive byte-identical files) + the Clause-1..4 atom-trace
columns; the atom-trace-off twin pins the fixed 10-column header with `-`
placeholders (the r[7]-name fallback never firing on this IPL-free
program); the clause-reorder case pins the map plumbing from both sides on
an edge-clause-first rule — post-reason `get_rules` shows the reordered
live rule while the saved CSV's clause columns map back to the author's
order.

**reason(queries=...) (pyreason.py:1591-1595, filter_ruleset.py).**
Filtering matches by predicate ONLY, transitively through surviving rules'
clause targets, and permanently narrows the live rule list.
`reason-queries-filter` pins the one-survivor arm: post-reason `get_rules`
holds only `cool_rule`, the trace carries cool derivations and no busy row
even though `owner(John)` would have fired `busy_rule`.
`reason-queries-no-match` pins the zero-survivor arm: the filter leaves a
plain empty list (post-raise `get_rules` fingerprint `[]` in both engines)
and `reason()` raises `builtins.ValueError` /
`cannot compute fingerprint of empty list` — at the pin that raise is
numba failing to fingerprint the empty plain list at kernel dispatch; the
rewrite raises it verbatim at the same seam (`Program.reason`, after the
Interpretation is constructed and assigned, so the post-raise program
holds a live interp exactly as the pin's does — seam-tested). The raise is
co-extensive with the pin's trigger by construction: only `filter_ruleset`
produces an empty rule list in either engine (both loaders leave a
zero-rule load as None → the no-rules Exception upstream).

**The recursion-crash contract, executed (the one deliberate divergence —
un-caseable input, no committed case touched, so no DIV record per the
convention).** At the pin, a query matching a self-recursive rule's head
crashes the process outright (unbounded recursion through the clause
targets; SIGSEGV before Python's RecursionError — screened session 14, no
artifact, so un-caseable). The banked design input (ledger session 14 idea
seeds: "bound or guard the query-filter recursion") is executed here: the
rewrite's `filter_ruleset` expands each predicate at most once, which
terminates on every cyclic ruleset and returns the identical reachable-rule
SET on every acyclic one — all any committed case can exercise, so the
committed pair still compares exactly. Recorded on type:Query's board row
and seam-tested
(`test_filter_ruleset_terminates_on_self_recursive_rule`); the pinned
de-duplication through `list(set(...))` is kept, so multi-survivor order
stays unpinned and committed cases keep survivor sets ≤ 1.

## Design: no ADR needed

Everything lands inside ADR 0002's explicit-state spine and ADR 0003's
one-core shape: one new `EngineState` field (`timestamp` — pinned
module-global state that two consumers share), two small helpers in
`_state` (`_peak_memory_mb`, `_redirect_stdout_to_output_file`), one pure
writer in `_output` over the existing Frame view, a one-line facade
delegation, and two scoped edits in `_program` (the dispatch-seam raise;
the guarded recursion). No new engine concepts, no schedule changes, no
state-shape changes beyond the one field. The stdout rebind is the one
process-global side effect and it is the pinned behavior itself,
reproduced at the pinned seam — not a design choice available to make.

## Per-case verdicts (all PASS, `results-phase3-slice6/`)

Wall-clock from the run's artifacts (capture-internal timing; `import_s` +
total reason/steps seconds, engine A = pinned oracle, engine B = rewrite;
rewrite step times round to ~0.000 at the artifact's 3-decimal resolution):

| case | verdict | oracle import/reason (s) | rewrite import/reason (s) |
|---|---|---|---|
| memory-profile-default | pass | 1.29 / 2.789 | 0.056 / 0.000 |
| memory-profile-on | pass | 1.30 / 2.997 | 0.057 / 0.001 |
| memory-profile-output-on | pass | 1.30 / 3.055 | 0.055 / 0.001 |
| output-file-name-custom | pass | 1.33 / 2.948 | 0.056 / 0.000 |
| output-file-name-inert | pass | 1.33 / 2.912 | 0.054 / 0.000 |
| output-to-file-default | pass | 1.33 / 2.931 | 0.055 / 0.000 |
| output-to-file-on | pass | 1.34 / 2.986 | 0.056 / 0.001 |
| reason-queries-filter | pass | 1.34 / 2.793 | 0.059 / 0.000 |
| reason-queries-no-match | pass | 1.38 / 2.219 | 0.060 / 0.000 |
| save-rule-trace-atom-trace-off | pass | 1.35 / 2.956 | 0.061 / 0.000 |
| save-rule-trace-basic | pass | 1.38 / 2.956 | 0.058 / 0.000 |
| save-rule-trace-clause-reorder | pass | 1.38 / 2.953 | 0.061 / 0.000 |
| save-rule-trace-store-off | pass | 1.37 / 2.948 | 0.058 / 0.000 |

Pass criterion per case: 4 fresh-process captures (a1/a2/b1/b2), same-engine
repeats digest-stable, A-vs-B probe digests equal (the redirect files and
trace CSVs compare as full contents, timestamp/peak-MB canonicalized under
the recorded rationales; everything else exact). The results directory is
untracked per the slice convention; `results/` and the slice-1..5 dirs were
not written to. A 3-case screen (`save-rule-trace-basic`,
`memory-profile-output-on`, `reason-queries-no-match`) ran first per the
screen-then-confirm doctrine, then the full 13.

## Seam tests (fast tier 257 = 242 + 15)

`tests/test_rewrite_output_surface.py` — every test carries a `proves:`
docstring and tests the I/O seam in a confined tmp cwd, not just the pure
helpers: sys.stdout identity across the rebind (and its absence on the
inert arm), redirect files read back by name-pattern and contents, the
peak-MB line's shape on stdout and its placement in the redirect file, the
stdlib-only guarantee (`memory_profiler` not in `sys.modules` after a
profiled run), the CSV pair's names/header/cells round-tripped against the
trace frame, folder-variant byte identity, the store-off assert firing
before any write (cwd stays empty), permanent query narrowing, the
no-match raise + post-raise state (empty rule list, program holding a live
interp), transitive body-support survival, and the recursion guard's
termination on the self-recursive input.

## Board

18 rows flip to `equivalent` — computed mechanically (every `cased` row
whose full case list ⊆ the oracle-vs-rewrite passed set across
`results-phase3-slice1..6`):

`fn:load_graph`, `fn:add_fact`, `fn:add_rule`, `fn:get_rules`,
`fn:get_time`, `fn:reason`, `fn:get_rule_trace`, `fn:filter_and_sort_nodes`,
`type:Rule`, `type:Fact`, `type:Query`, `dsl:rule-text`, `dsl:fact-text`,
`setting:verbose`, `setting:output_to_file`, `setting:output_file_name`,
`setting:memory_profile`, `setting:atom_trace`.

New fraction: **47/52** (was 29/52). The 5 rows still `cased` are exactly
the gated remainder the session-20 ledger predicted: the registrand family
(`fn:add_annotation_function`, `fn:add_head_function`, `fn:reset_rules` —
gated on the harness conditional-njit accommodation) and the IPL-file-fed
rows (`fn:load_inconsistent_predicate_list`, and `fn:save_rule_trace`,
whose case list includes `ipl-atom-trace-off-trace` — now unblocked by the
approved pyyaml ask but not yet run oracle-vs-rewrite). Inventory gate
green (`tests/test_surface_inventory.py`, 6 passed).

## Divergences and observations

- **DIV records: none.** All 13 committed cases compare equal.
- **Deliberate divergence on an un-caseable input (recorded, not DIV'd):**
  the query-filter recursion guard above — the pin crashes, the rewrite
  terminates; no committed case can reach the difference, the board row
  and a seam test carry it.
- **No new oracle-bug candidates.** The pinned behaviors reproduced here
  that read as hazards were already recorded on the board (the
  never-restored stdout rebind; the zero-survivor reason() raise; the
  SIGSEGV contract).

## Deviations from the packet

None. No installs, no oracle-tree writes, no dependency changes (the
memory-profile path is stdlib `resource` — the one place a dependency
temptation existed, foreclosed by AC-2); the full e2e sweep was not run
(fast tier + the 13 packet cases + the 3-case screen only, per the
test-tier rule).

## Open follow-ups

- The IPL file family (4 cases, pyyaml now approved) and the registrand
  family (5 cases, harness `reference_fns.resolve()` accommodation) are
  the whole un-run remainder before the Phase-3 breadth boundary sweep.
- Carried unchanged from prior slices: `type-reject` probe form for the
  settings family; `raise_errors=False` warn-skip arms;
  `interacts-unknown-predicate`; multi-rule prange characterization.

## Repro

```
uv run pytest -m "not e2e"                       # fast tier: 257 passed
mkdir -p /tmp/slice6-cases && for c in output-to-file-default output-to-file-on \
  output-file-name-custom output-file-name-inert memory-profile-default \
  memory-profile-on memory-profile-output-on save-rule-trace-basic \
  save-rule-trace-atom-trace-off save-rule-trace-clause-reorder \
  save-rule-trace-store-off reason-queries-filter reason-queries-no-match; do \
  cp harness/cases/$c.json /tmp/slice6-cases/; done
PYTHONHASHSEED=0 uv run python -m harness.run --cases /tmp/slice6-cases \
  --engine-a oracle-env/bin/python --engine-b scripts/rewrite-python \
  --results results-phase3-slice6    # 13/13 ALL PASS (use a fresh --results dir to re-run)
```
