<!-- doccode: pyreason-rewrite-docs-reviews-2026-07-07-phase3-slice6-review -->
# Phase 3, slice 6 — the output surface (independent review)

- session: 21 · 2026-07-07 · reviewer-fixer packet (no shared context with the author)
- scope reviewed: the full diff `a9598ee..dae7345` as a coherent whole, graded
  against the pinned source at `e1a94af33e1f` and the slice-6 packet spec
  (session-20 NEXT)
- verdict: **packet FAILS as landed — two rewrite defects, both found by
  review probes, both fixed by this review; the corrected slice passes.**
  Author's 13/13 claim reproduced independently pre-fix (13/13 PASS); the
  discriminating probes then refuted two of the author's semantic claims.
  Post-fix evidence: **14/14 pass** (the 13 packet cases + the review's
  regression case) into `results-phase3-slice6-review/`; fast tier **259
  passed** (257 + 2 review seam tests); **5/5 reviewer discriminating probes
  pass or expose-then-pass**; board **47/52 confirmed mechanically** (18
  flips, no missed or premature flip). One records fix: the query-filter
  recursion guard is a real standing intentional divergence with no operator
  adjudication on file, so the review filed **DIV-0001**
  (`intentional-divergence-proposed`, queued-for-operator) with a pin-side
  reproducer test — the campaign's first divergence record.

## Findings, by severity

**F1 (rewrite-defect, fixed) — the empty-ruleset raise over-fired: the pin
completes on the edge-heavy arm.** The author's claim "the raise is
co-extensive with the pin's trigger by construction: only filter_ruleset
produces an empty rule list" missed that the pinned clause-reorder arm
(pyreason.py:1598-1606) rebuilds `__rules` as a **fresh numba typed list**
even when the query filter left it empty — and an empty *typed* list still
fingerprints at kernel dispatch. Probed live on the pin (the popular graph,
7 edges > 5 nodes, `queries=[famous(Mary)]`): the **oracle completes** —
`time=3`, `get_rules()` = `[]`, fact application runs with zero rules —
while the committed rewrite raised `ValueError('cannot compute fingerprint
of empty list')`. A genuine cross-engine divergence on a *caseable* input.
Fix: `_program.TypedRuleList` (a list subclass modeling the pin's list
KINDS — add_rule at :639 and the reorder arm at :1603 build typed lists;
only filter_ruleset hands back a plain list, filter_ruleset.py:34); the
dispatch-seam guard now raises only on an empty **plain** list, exactly the
pin's trigger. Banked as the committed regression case
`reason-queries-no-match-edge-heavy` (passes both engines post-fix), the
seam test `test_reason_queries_no_match_edge_heavy_completes`, and
corrections to the overbroad sentence in `reason-queries-no-match`'s
purpose and type:Query's board note.

**F2 (rewrite-defect, fixed) — save_rule_trace into a nonexistent folder
raised the wrong error shape, and the docstring claimed otherwise.** The
author's `_output.save_rule_trace` docstring asserted "a nonexistent folder
raises the open()'s own error like the pin's pandas write does" — false on
both halves. Screened both engines: the pin (pandas 2.3.3) raises
**`builtins.OSError | Cannot save file into a non-existent directory:
'missing_dir'`** (pandas io/common.py `check_parent_directory`, hit before
any write), the committed rewrite raised `builtins.FileNotFoundError |
[Errno 2] No such file or directory: 'missing_dir/rule_trace_nodes_….csv'`.
The fn:save_rule_trace board row already recorded the pinned OSError
("screened, not cased — the probe creates its named subfolder"), so the pin
observation existed; the engine just didn't honor it. This arm is
deliberately outside harness reach (the save_rule_trace probe mkdirs its
subfolder first, by design), so it stays screen-evidenced: fix reproduces
the pinned check (parent `is_dir()` before open, exact message via the
pathlib parent, exact type `OSError` — never the FileNotFoundError
subclass), seam-tested
(`test_save_rule_trace_missing_folder_raises_pinned_oserror`), docstring
corrected, board note extended. Post-fix screens: byte-identical raise
records both engines.

**F3 (records, fixed by filing) — the recursion-guard divergence had no
adjudication record.** The author skipped a DIV record on the ground that
no committed case reaches the divergence. The trail supports the *design*
(session-14 ledger banks the SIGSEGV screen and seeds "bound or guard the
query-filter recursion … a natural intentional-divergence candidate";
session-20's NEXT names the crash contract a design input) but nothing in
the ledger is an **operator adjudication** of an intentional divergence,
which AC-6 requires ("intentional divergences are operator-adjudicated,
each with its failing-test reproducer" — queue-and-continue). Filed
**`docs/divergences/DIV-0001.md`**: classification
`intentional-divergence-proposed`, status `queued-for-operator`,
provisional behavior = the guarded expansion, reproducer =
`tests/test_div_0001_reproducer.py` (e2e-marked subprocess run of the pin
on the self-recursive-match input — re-screened this session: the pinned
process dies, no artifact) + the author's rewrite-side seam test. The
divergence itself is correctly designed and honestly documented on the
board; only the record was missing.

## Semantic fidelity to the pinned output surface

Read side-by-side, not trusted from the report:

- **The stdout redirect** — `_state.reason` reproduces pyreason.py:1508-1514
  exactly: stamp `time.strftime('%Y%m%d-%H%M%S')` onto the state (the pin's
  `__timestamp` module global, `''` initial at :480 — matched by
  `EngineState.timestamp`), then `sys.stdout = open(f"./{name}_{stamp}.txt",
  "a")` when `output_to_file` is on; `_reason` re-opens the same name at its
  top (:1541-1542, the double-open, first file object takes no writes);
  `_reason_again` does not re-open (matching the pin); nothing restores or
  flushes. The interpolation is verbatim, the inert arm writes nothing.
- **The memory-profile line** — the pin wraps either dispatch arm and prints
  `\nProgram used {mem_usage-start_mem} MB of memory` (:1516-1527). The
  rewrite mirrors the branch structure on both arms (fresh and again) and
  prints the identical fixed text around a stdlib `resource`-module
  peak-RSS difference — the number is run-varying measurement in both
  engines and only the operator-approved `canonicalize_peak_mb` reduces it,
  declared on exactly the one case whose redirect file carries the line
  (memory-profile-output-on). No memory_profiler import anywhere
  (seam-tested via `sys.modules`); AC-2 holds — `git diff a9598ee..HEAD --
  pyproject.toml uv.lock` empty.
- **save_rule_trace** — facade assert message matches the pinned :1652
  verbatim (banked by the store-off case as `builtins.AssertionError`
  before any write); file names `rule_trace_{nodes,edges}_{timestamp}.csv`
  joined with os.path.join like output.py:102-104; the CSV writer targets
  pandas `to_csv(index=False)` byte shape (QUOTE_MINIMAL, os.linesep row
  ends, None → '', str()-rendered cells) over the already-proven
  get_rule_trace Frame — the committed cases' full-content compares plus my
  edge-rows probe are the byte evidence. Clause reordering renders through
  the pinned `_reorder_row` map semantics (author-order columns, None fill).
- **reason(queries=…)** — `filter_ruleset` matches the pin predicate-only
  (`Label`-typed both sides), iterates the FULL rule list at every level,
  keeps the `list(set(...))` dedup (multi-survivor order unpinned — the
  committed cases and my order-sensitive probes keep survivor sets ≤ 1),
  and applies per-query with a fresh `seen`. The seen-guard returns the
  identical reachable-rule set on every acyclic ruleset (expansion of a
  predicate is a pure function of the predicate, so memoizing changes
  multiplicity, never the union — and the dedup erases multiplicity); on
  cyclic rulesets it terminates where the pin dies — DIV-0001. The
  zero-survivor raise sits at the pinned seam (Program.reason, after the
  Interpretation is constructed and assigned — matching program.py:50's
  `start_fp` dispatch position) and now fires on exactly the pin's trigger
  (F1).

## Discriminating probes (overfitting hunt) — 5 probes, both engines

Probe cases in the session scratchpad through the same harness,
PYTHONHASHSEED=0, oracle-env vs scripts/rewrite-python:

| probe | seam it pins beyond the 13 cases | verdict |
|---|---|---|
| reason-queries-no-match-edge-heavy | the reorder-arm × query-emptied-ruleset interaction: edges > nodes rebuilds the empty list as a typed list and the pin COMPLETES with zero rules | **exposed F1** — pre-fix rewrite raised; fixed, committed as a regression case, passes both engines |
| missing-folder screens (both engines) | save_rule_trace into a nonexistent folder — the arm the harness's mkdir-first probe deliberately can't reach | **exposed F2** — pre-fix raise shapes differed; fixed, byte-identical post-fix |
| rv-queries-multi-one-survivor | a two-query list where the second matches nothing: per-query extend + set dedup leaves exactly cool_rule; trace carries cool, no busy | pass |
| rv-queries-multi-both-survive | both queries match, both rules survive (order-immune probes only — survivor order rides `list(set(...))`): cool(Mary) and busy(John) both derive | pass |
| rv-save-rule-trace-edge-rows | the edges CSV with REAL derivation rows + atom-trace Clause-i columns (every committed save-rule-trace case writes a header-only edges CSV) — edge-head rule `trusted(x,y) <-1 popular(x), Friends(x,y)` | pass |

## Independent rerun

- Fast tier: `uv run pytest -m "not e2e"` → **257 passed** on the author's
  tree (claim confirmed), **259 passed** post-fix (the 2 review seam tests).
- 13-case rerun on the author's tree: **ALL PASS (13)**, exit 0 —
  the author's verdict reproduces; the defects live outside the committed
  cases' reach, which is exactly what the probes were for.
- Post-fix rerun (the fix touches the shared dispatch path, so the full
  packet set re-ran, not just the touched cases): fresh
  `results-phase3-slice6-review/` (gitignored by the author's `9dfcbbd`) →
  **ALL PASS (14 cases)** = 13 packet cases + the regression case, 4
  fresh-process captures each, same-engine repeats digest-stable.
- DIV-0001 pin-side reproducer: `uv run pytest
  tests/test_div_0001_reproducer.py -m e2e` → 1 passed (the pinned process
  dies on the self-recursive-match input; e2e-marked, gate-deselected).

## surface.md — 18 flips verified mechanically

Recomputed, not trusted: `git diff b69f7b5~1..b69f7b5` flips exactly 18
rows `cased → equivalent`; the union of `status: pass` verdicts across the
banked `results*/report.json` dirs covers every case in every `equivalent`
row's case list (no unsupported flip) and **no `cased` row's full list is
covered** (no missed flip); count **47/52 correct**. The 5 remaining
`cased` rows are exactly the predicted gated remainder (registrand family ×3,
`fn:load_inconsistent_predicate_list`, `fn:save_rule_trace` via
`ipl-atom-trace-off-trace`). The review's regression case was added to the
fn:reason and type:Query case lists (both already equivalent; the case
passes in the review run, so the flip invariant holds).

## Tests

The 15 author seam tests read line-by-line: every `proves:` docstring
matches its assertions; they test the I/O seam in a confined tmp cwd
(redirect files read back by name-pattern and contents, sys.stdout identity
both arms, the peak line's placement in the redirect file, CSV cells
round-tripped against the Frame, the store-off assert firing before any
write, post-raise program state). Pin citations spot-checked — accurate.
The two wrong author claims lived in a code comment (`Program.reason`) and
a docstring (`_output.save_rule_trace`), both now corrected; no `proves:`
line overstated. Review adds 2 seam tests (F1, F2 above) + the e2e-marked
DIV-0001 reproducer.

## Design bars (AC-5)

The author's diff stays inside ADR 0002/0003 as claimed: one state field
(`timestamp`), two `_state` helpers, one pure writer, one facade delegation,
two scoped `_program` edits. The review fix adds `TypedRuleList` — not a new
engine concept but a marker for a distinction the pin already carries (which
rule lists ride numba typed lists), consumed at exactly one seam; no state
shape or schedule change. The no-new-ADR claim survives the fixes.

## Hygiene

- No installs, no dependency changes: `git diff a9598ee..HEAD --
  pyproject.toml uv.lock` empty (before and after fixes).
- Oracle tree byte-clean: `git -C oracle/pyreason status --porcelain` empty,
  HEAD = `e1a94af33e1f…` = oracle/PIN.
- `git ls-files 'results*'` → 0 tracked files; the slice-6 results dirs are
  gitignored; banked prior-slice dirs untouched.
- No security framing in the session diff (scanned).
- Full e2e sweep not run (fast tier + the 14 cases + 5 probes + the one
  e2e-marked reproducer only, per the wall-clock rule).

## Verdict

**The packet's engine work is faithful where its cases look, and the
committed evidence is honest — but it shipped two divergences its cases
could not see, both caught by review probes and fixed in-review:** the
query-emptied-ruleset raise now fires on exactly the pinned trigger (plain
list at dispatch, not any empty ruleset), and save_rule_trace's
missing-folder refusal now wears the pinned pandas OSError shape. With the
fixes and DIV-0001 on file, the output surface stands at 14/14
oracle-vs-rewrite PASS, fast tier 259, board 47/52 — and the campaign's
divergence ledger now has its first, properly queued record.

## Repro

```
# fast tier (259 post-fix)
uv run pytest -m "not e2e"

# the 14-case rerun (13 packet cases + the regression case)
mkdir -p /tmp/slice6-review-cases && for c in output-to-file-default \
  output-to-file-on output-file-name-custom output-file-name-inert \
  memory-profile-default memory-profile-on memory-profile-output-on \
  save-rule-trace-basic save-rule-trace-atom-trace-off \
  save-rule-trace-clause-reorder save-rule-trace-store-off \
  reason-queries-filter reason-queries-no-match \
  reason-queries-no-match-edge-heavy; do \
  cp harness/cases/$c.json /tmp/slice6-review-cases/; done
PYTHONHASHSEED=0 uv run python -m harness.run --cases /tmp/slice6-review-cases \
  --engine-a oracle-env/bin/python --engine-b scripts/rewrite-python \
  --results results-phase3-slice6-review-repro

# DIV-0001 pin-side reproducer (e2e-marked, needs oracle-env)
uv run pytest tests/test_div_0001_reproducer.py -m e2e

# F2 screen (both engines): reason once, then save_rule_trace(interp,
# 'missing_dir') — both raise builtins.OSError
# "Cannot save file into a non-existent directory: 'missing_dir'"
```
