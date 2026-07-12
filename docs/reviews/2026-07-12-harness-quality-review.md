<!-- doccode: pyreason-rewrite-docs-reviews-2026-07-12-harness-quality-review -->
# Session 31 — independent review: the harness-quality seed batch

- session: 31 · 2026-07-12 · reviewer-fixer packet (no shared context with
  the author)
- scope: commits `bc1fab7` (artifact case echo + per-probe timing),
  `00c2e61` (per-case sweep durability/resume), `95b65eb` (pyyaml parity
  tripwire), `0f6e637` (resume e2e), `f21b296` (case
  `parallel-computing-multirule`), `d857784` (board row + the
  [session-31 author report][pyreason-rewrite-docs-reviews-2026-07-12-harness-quality-author]);
  plus the orchestrator-flagged .gitignore hygiene item.
- verdict: **approved with fixes.** Every packet claim re-verified — the
  durability semantics survived all five attack lines, the prange
  characterization reproduced on a fresh re-screen, and the new case banked
  oracle-vs-rewrite PASS again under this review. The code needed no
  changes; three fast-tier coverage gaps (untested claims the code already
  honored) were closed in `9ae5f64`, the ignore accretion consolidated in
  `dda37d4`, and a two-spot key-name typo in the author report
  (`probe_s` → `probes_s`) corrected with this report's commit.

## 1. Durability semantics (`00c2e61`, harness/run.py) — the risky change

### (a) Completion lies — can a marker vouch for altered artifacts?

No. `completed_marker` (run.py:148-178) re-verifies **every** listed
artifact's sha256 against the file's current bytes on every resume decision
— the marker is never trusted blindly; a truncated, altered, or deleted
artifact invalidates the whole case and it re-runs from scratch. The
designed behavior is stated in three places (module docstring, the
function's docstring, the author report §1) and they agree. The
absent-artifact state is itself recordable (`file_digest` → `null` for a
capture that exited nonzero without writing), so an error-verdict case
resumes to the identical error verdict rather than silently retrying.
Verified live: truncation (author's e2e), and outright deletion under an
intact marker (this review's exercise + new test) — both re-ran the case.

### (b) Identity confusion — mixing results dirs

Refused by re-run, never by mixing: the marker records engine-a/engine-b
executables, the pinned hash seed, and the case file's byte digest;
`completed_marker` returns None on any mismatch and the stale marker is
unlinked *before* the first re-capture, so an interruption mid-recapture
cannot pair an old marker with a refreshed dir. The case-file-digest
mismatch path is unit-tested (`test_identity_mismatch_invalidates_the_marker`
edits the case file and asserts a full re-capture), as is the
changed-engine path. Conservative direction confirmed: a same-engine
different-path-spelling invocation re-runs (identity is the string), which
can only cost captures, never mix them.

### (c) Report equality — resumed verdicts vs single-invocation verdicts

The claim rests where the author says it rests: verdicts derive from the
on-disk artifacts through the same pure `judge_case` on both paths
(run.py:229-232 judges after either branch), and the marker carries no
authority over the verdict (only the recorded exit codes feed
`load_artifact`'s taxonomy). The author's e2e (`tests/test_resume_e2e.py`)
does prove the equality claim — clean run, marker-delete + artifact-truncate
interruption, resume, verdict-list equality, plus the untouched case's
artifact mtimes held constant (re-judged, not re-captured). Re-run under
this review: **1 passed (~30 s)**. Independently reproduced live with the
third damage shape (artifact deleted outright, marker intact): resumed
verdicts equal the clean run's, only the two damaged cases recaptured.
Partial-coverage judgment: the e2e was adequate for the equality claim; the
gaps were in the *honesty* and *damage-shape* corners, closed in `9ae5f64`
(fast tier, not the e2e — the shapes need no live engine).

### (d) Honesty — `resumed: false` on a resumed invocation

Impossible by construction (`"resumed": bool(prior_ids)`, run.py:278) and
now impossible by test: the all-complete resume (every case prior-complete,
zero recaptures) was the untested corner — verified live
(`RESUMED — 3 prior-complete, 0 captured this invocation`, resume block
`{"resumed": true, ..., "captured_this_invocation": []}`) and pinned in the
extended main()-level fast test. Note the deliberate asymmetry, which is
correct: a re-invocation over a dirty dir that finds **no** valid marker
recaptures everything and reports `resumed: false` — nothing was reused, so
the report *is* a single invocation's.

### (e) Backward compatibility

- Report: `engine_a`/`engine_b`/`hashseed`/`verdicts` unchanged in content;
  verdict entries carry no new keys; `resume` is additive.
- Artifacts: schema stays 1; `case` and `timing.probes_s` are additive.
- Digests: per-probe digests are computed over the probe map only
  (capture.py:1255 `{pid: digest(value) for pid, value in probes.items()}`);
  `timing` and `case` sit outside. The compare layer (`harness/compare.py`)
  never reads `timing` or `case` (grep-verified), and `judge_case` compares
  `digests` and `probes` only — the volatile additions cannot perturb a
  digest or move a verdict.
- Consumers: `harness/bench.py` reads only its own `bench-report.json`;
  `harness/profile.py` and tools/ touch neither `run_case` nor
  `report.json`. The `run_case` return-shape change (dict → tuple) has no
  consumer outside run.py's `main` and the tests, both updated.
- The marker's per-file sha256 *does* cover the volatile timing values —
  correct, since it is an integrity record of the exact bytes that were
  judged, never compared across invocations.

## 2. Artifact case echo + per-probe timing (`bc1fab7`)

- The echo is the **parsed** case re-serialized (canonical equality with
  the case JSON, not byte-for-byte) — exactly what the docstring claims
  ("echoed verbatim from the parsed case file"). Attacked for mutation:
  the one case-derived dict that gets popped (`call_apply_input`,
  capture.py:783-787) copies first (`args = dict(args)`); no other site
  mutates the case record, so the echo is faithful.
- Error paths: the two post-parse error artifacts (invalid case → exit 2,
  engine failure → exit 1) carry the echo; the pre-parse unreadable-file
  artifact correctly cannot. Was code-true but untested — now pinned by
  `test_error_artifacts_echo_the_case_record` (`9ae5f64`).
- `timing.probes_s` rides outside the digested probe map in both case
  forms (author's three tests + the digest-inputs check under (e) above).

## 3. pyyaml parity tripwire (`95b65eb`)

Right seam: `yaml.__version__` is the version the running interpreter
actually imports — the one thing uv.lock cannot vouch for (a rebuilt venv,
a stray site-packages). Cross-checked: `yaml.__version__` and
`importlib.metadata.version("pyyaml")` both report 6.0.3 in the campaign
env; uv.lock and pyproject pin `>=6.0.3`; the operator approval is where
the message says it is (docs/ledger/session-22.md). The `proves:` docstring
matches the assertion; the failure message carries the full re-screen
protocol (the four ipl-* cases, oracle-vs-rewrite, ALL PASS before the
expectation moves) — actionable as required.

## 4. The prange case + characterization (`f21b296`, `d857784`)

- **Re-screen (this review, at the pin, oracle untouched):** the committed
  case run as a `harness.run` self-proof — 4 fresh oracle processes,
  `PYTHONHASHSEED=0` — **ALL PASS**: width-3 prange determinism reproduces
  (exceeds the 2-fresh-process bar for this review).
- **Serial parity spot check:** a scratchpad serial twin
  (`parallel_computing: false`, same program) captured once in the oracle
  env; all five reasoning probes (`nodes-popular`, `nodes-trendy`,
  `trace-node`, `trace-edge`, `time`) digest-equal the parallel arm's;
  only the knob echo (`par-knob`) differs, as it must.
- **Oracle-vs-rewrite:** re-run fresh — **ALL PASS (1 case(s))**.
- **Board note faithful:** determinism claimed only at the screened
  width/config on this machine (numba 0.59.1/darwin), the mechanism
  question explicitly unclaimed, rule-order attribution described as
  behavior-in-both-engines — all matching the screens. Oracle line refs
  verified at the pin (decorator `parallel=True` at
  interpretation_parallel.py:241, rules-loop `prange` at :571).
- **Comparison policy sound:** exact comparison everywhere is right —
  rule order is fixed *within* the case, and the claimed equal-bound row
  reordering is a cross-rule-order effect, identical cross-engine (borne
  out by the cross-engine PASS with an exact policy).

## 5. Hygiene: .gitignore consolidation (`dda37d4`)

22 per-results-dir lines (accreted per sweep) replaced by one `results*/`
directory glob; verified `git ls-files 'results*'` is empty first, so the
glob can hide no tracked file. The untracked-unignored
`results-session30-review/` now falls under it (`git check-ignore`
verified).

## Fixes applied by this review

- `9ae5f64` — three fast-tier coverage gaps closed (all-complete resume
  honesty at main() level; deleted-artifact-under-intact-marker shape;
  error-artifact case echo). Each was verified live before the test was
  written; no engine or harness code needed changing.
- `dda37d4` — the .gitignore consolidation above.
- (this commit) — author-report key-name typo: two `probe_s` mentions
  corrected to the actual artifact key `probes_s`.

## Evidence & reproduction

- Fast tier: `uv run pytest -m "not e2e"` → **321 passed, 6 deselected**
  (author's 320 + this review's one new test; two findings extended
  existing tests).
- Resume e2e: `uv run pytest tests/test_resume_e2e.py -m e2e` →
  **1 passed** (~30 s).
- Prange self-proof re-screen:
  `uv run python -m harness.run --cases harness/cases/parallel-computing-multirule.json --engine-a oracle-env/bin/python --results <scratch>`
  → **ALL PASS (1 case(s))**.
- Oracle-vs-rewrite:
  `uv run python -m harness.run --cases harness/cases/parallel-computing-multirule.json --engine-a oracle-env/bin/python --engine-b scripts/rewrite-python --results <scratch>`
  → **ALL PASS (1 case(s))**.
- Live durability exercise (scratchpad, 3-case mini corpus, oracle
  self-proof): clean sweep → delete one marker + delete one artifact →
  resume (verdicts equal, 2 recaptured) → re-invoke all-complete
  (verdicts equal, `resumed: true`, 0 recaptured).

## Hygiene

Oracle tree untouched (read-only reads only; the pin sits at
e1a94af33e1f). No installs, no dependency changes, no writes outside the
repo but the session scratchpad. Full e2e suite not run (not this packet).

<!-- links:begin -->
[pyreason-rewrite-docs-reviews-2026-07-12-harness-quality-author]: 2026-07-12-harness-quality-author.md
<!-- links:end -->
