# Review — accessor/trace-output cluster cases (session 12)

Reviewer: session 12 agent 2 (independent reviewer-fixer; no shared context
with the author). Scope: commits `de547d0` (probe kinds + seam tests),
`7921f97` (six cases), `e532987` (board flips + author report,
[raw report](2026-07-07-accessor-trace-cases-raw.md)). Every line of the
three diffs read against the pinned source (oracle pin `e1a94af33e1f`,
tree untouched). Fixes applied by the reviewer; the post-fix reruns below
are the session's verdict-of-record.

## Verdict

**Sound work with one refuted characterization.** The two probe kinds are
well-designed (validation parity, confinement intact, canonicalization
rationale at the definition sites), the six cases discriminate their
classes, and the board flips are otherwise accurate. But the session's
headline characterization — "`output.py:23-25` is dead code, never fires
on any reachable path" — **overclaims and is refuted by a live screen**:
IPL complement rows bank a nonempty `IPL: <label>` name unconditionally,
so the fallback fires exactly there when `atom_trace` is off. The claim
is true only for fact-, rule-, and inconsistency-triggered rows. Board,
case purpose, and analysis file corrected; all evidence rerun green.

## Findings

### High

**H1 — the dead-fallback characterization overclaims its scope
(refuted live).** The board note, the author report (§6.1), and commit
message `7921f97` state that with `atom_trace` off the engine banks empty
trace names, so `output.py:23-25`'s `Occurred Due To` fallback "never
fires on any reachable path — dead code". Verified against the pin, the
empty-name claim holds only for the fact/rule/inconsistency append sites:

- fact rows — `interpretation.py:298`, `:374` (`... if atom_trace else ''`);
- rule/fact update sites — `:1544-1549`, `:1663-1668` (`meta_name = ''`
  unless `atom_trace`; note the author's cite `:1543-1548` was off by one);
- inconsistency rows — `resolve_inconsistency_node`/`_edge`
  (`actual_name = ''` unless `atom_trace`, `:1969-1974`);
- `interpretation_fp.py` mirrors all three shapes.

But the **IPL complement appends bank `f'IPL: {l.get_value()}'`
unconditionally** — gated only on `store_interpretation_changes`, never on
`atom_trace`: `interpretation.py:304`, `:308`, `:380`, `:384`, `:1582`,
`:1599` (fp mirrors `:384`, `:388`, `:466`, `:470`, `:1700`, `:1717`,
`:1813`, `:1830`). So with `atom_trace` off and an inconsistent-predicate
pair loaded, `r[7] != ''` on every IPL row and the fallback fires.

Forced by a live screen (scratch script, `PYTHONHASHSEED=0
oracle-env/bin/python`): friends graph + popular rule + `popular(Mary)`
fact + `add_inconsistent_predicate('popular', 'unpopular')`,
`atom_trace=False`, `reason(timesteps=2)`, `save_rule_trace` — the node
CSV shows `Occurred Due To = '-'` on every popular row and
`'IPL: popular'` on every unpopular row (12 rows total, 6 of each). The
branch is behavior-bearing, not dead: a rewrite that dropped it would
diverge on any IPL-bearing program with `atom_trace` off.

The author's *observation* was correct for the cased programs (none load
an IPL); the *generalization* was not, and it was recorded on the board
as an unconditional claim. This is exactly the expensive failure mode the
charter names: a scope-unchecked generalization asserted as a finding.

**Fix applied:** `docs/surface.md` `fn:save_rule_trace` note rewritten to
the scoped characterization with both sets of append-site cites and the
screen; the IPL-with-atom-trace-off trace arm is named uncovered (no
committed case combines an IPL with `atom_trace` off and a trace view —
checked: the four inconsistency/abort cases run `atom_trace` elsewhere or
probe no trace CSV). Commit message `7921f97` is immutable; this report
and the board are the record. The rewrite-relevance flag in the author
report survives in sharpened form: a rewrite must keep the fallback for
IPL rows and must *not* invent names for fact/rule rows.

### Medium

**M1 — the committed case purpose contradicts the observed behavior (and
the author's own finding).** `save-rule-trace-atom-trace-off.json`'s
purpose said `Occurred Due To` "carries the rule/fact name from the trace
tuple instead of the atom-trace grounding" — the opposite of what the
case's own banked CSVs show (`'-'` on every row; the author's report §6
has it right). The purpose is the case's documented claim; left as
committed it re-asserts the analysis file's refuted description.
**Fix applied:** purpose rewritten to the observed `'-'` behavior, scoped
to this IPL-free program, citing `output.py:23-25`. (Purpose text does
not feed any probe; the case's probes and comparison are untouched —
rerun green below.)

**M2 — the refuted analysis-file description was left in place.**
`docs/analysis/surface/reason-and-state.md:56` ("'Occurred Due To' comes
from the rule name `r[7]`" in the off arm) was found refuted by the
author but only recorded "contra" on the board; prior sessions' practice
is to fix refuted analysis docs in-review. Its original text was also
wrong in the *other* direction (for fact/rule rows nothing comes from
`r[7]` — the names are empty). **Fix applied:** the off-arm sentence now
carries the verified two-sided behavior with the same cites as the board
note. The `fn:get_rule_trace` sibling entry (`:77`) only claims the
column-shape split, which stands.

### Low

**L1 — the reorder mutation's threshold half is unobserved.** The author
flagged this themselves (§8): `reorder_clauses.py:22-25` permutes
thresholds in step with clauses, and `rule_fingerprint` renders the
clause list but no thresholds — so `save-rule-trace-clause-reorder` pins
the clause half of the live-rule mutation only. Defensible scoping
(threshold rendering belongs to `type:Rule`'s row), but per the packet's
own rule the gap must stay *named*, not absorbed. **Fix applied:** one
sentence on the `fn:get_rules` board note naming the unobserved facet.

**L2 — the store-off case cannot see a write-then-raise engine.**
`save-rule-trace-store-off` banks only the raise record; the confined
directory's CSV-absence is unobserved. At the pin this is unreachable
(the assert at `pyreason.py:1652` precedes the `Output` construction at
`:1654`, so nothing can be written before the raise), and adding a
directory observation would complicate the probe's output shape for a
candidate-engine corner. **No fix** — recorded so the gap is a decision,
not an oversight.

## Verified good (checked, no finding)

- **Anchors:** every file:line cite in the report/board checked at the
  pin — `pyreason.py:510-514`, `:529-535`, `:538-546`, `:549-558`,
  `:1511` (`__timestamp`), `:1594-1595` (queries filter), `:1598-1606`
  (reorder), `:1645-1655`/`:1652`/`:1654`, `output.py:13`, `:23-25`,
  `:44-47`, `:92-97`, `:99-106`, `:114-123`, `reorder_clauses.py:6-30`,
  `program.py` `reset_graph` nulling `interp` — all accurate (one
  off-by-one, folded into H1's fix).
- **Validation parity:** unknown accessor name and non-confined folder
  are exit-2 authoring faults, top-level and in steps alike
  (`_probe_list_fault` covers both); `allow_raise` stays banned on
  `get_setting`/`output_file`/`expect_raise` and legal on both new kinds
  via the shared `run_probe_recorded` wrap — consistent semantics.
- **Confinement:** `case_wants_output_dir` extended to `save_rule_trace`
  (pinned default folder is the cwd — without this the CSVs would land in
  the repo root); `TRACE_FOLDER_RE` (`^[A-Za-z0-9][A-Za-z0-9._-]*$`)
  admits no separator, no backslash, no leading dot, no `..`, no absolute
  path, ASCII only — cannot escape the per-capture directory on this
  platform; non-string folders refused before the regex; the subfolder is
  created by the harness so a missing directory never wears the engine
  label. Non-output cases' capture path unaffected (no chdir without the
  triggering kinds — `accessors-*` run unconfined as before).
- **Canonicalization:** `TRACE_TS_RE` rationale recorded at the
  definition site, same run-schedule reasoning as `OUTPUT_TS_RE`;
  basenames and full contents compare exactly; interval-likes in
  `rule_fingerprint` reduce via `harness/compare.py`'s `[lower, upper]`
  duck-typing.
- **Discrimination:** the identity flags make a copy-returning engine
  fail (`is`-identity with the capture's last successful reason return —
  the exact seam `pyreason.py:535`/`:546` pin); `None` vs empty-list
  distinguishes a rewrite initializing the globals differently; a
  no-op `save_rule_trace` banks an empty file list; a non-raising
  store-off banks a file list where the oracle banks a raise record.
- **Tests:** all 7 new `proves:` docstrings match their assertions; the
  kind-partition tripwire correctly extends to the five standalone kinds.
- **Program reuse:** all six cases run the committed hello-world
  graph/rule/fact (clause-reorder uses the edge-first variant of the same
  rule, as claimed); no new fixture programs.
- **No dead scaffolding:** every added constant, branch, and validation
  clause is exercised by a test or a committed case.

## Post-fix reruns (verdict-of-record)

From the repo root:

```
uv run pytest -m "not e2e"
# 77 passed, 2 deselected

PYTHONHASHSEED=0 uv run python -m harness.run --cases harness/cases/<case>.json --engine-a oracle-env/bin/python
# for each of: accessors-fresh-state, accessors-lifecycle,
#   save-rule-trace-basic, save-rule-trace-atom-trace-off,
#   save-rule-trace-store-off, save-rule-trace-clause-reorder
# each: ALL PASS (1 case(s)) — self-proof mode, 4 fresh-process captures,
# same-engine repeats by exact digest
```

The 53-case corpus sweep is session 11's banked verdict and was not rerun
(no committed case's probes changed; the only case edit is purpose text).

## Repro for H1's refutation screen

```
PYTHONHASHSEED=0 oracle-env/bin/python <scratch>/ipl_fallback_screen.py
# friends graph + add_inconsistent_predicate('popular','unpopular'),
# atom_trace=False, reason(timesteps=2), save_rule_trace →
# node CSV rows alternate Occurred Due To: '-' (popular) / 'IPL: popular'
# (unpopular)
```
