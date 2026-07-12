<!-- doccode: pyreason-rewrite-docs-reviews-phase4-profiles-review -->
# Session-27 independent review — rewrite baselines and the Phase-4 profiles

- Session: 27 (review pass, 2026-07-12)
- Reviewer: independent reviewer-fixer (Fable), no shared context with the
  author; reviewed from the committed evidence
- Scope: `c774312` (rewrite baselines + `scripts/bench-ladder` + oracle-doc
  repro one-liner), `d211c40` (profile driver + tests + gitignore),
  `51f33e7` (profile report), `fc038cd` (author report)
- Fixes applied by this review: `a45374d`

## Verdict

**Approved with fixes.** The baselines obey screen-then-confirm, every
banked median/band/spread matches the raw n=7 artifacts exactly, the
large-rung TIE call is honest and plainly worded on both sides of the
charter's rule, the profile driver's window is clean, the report's tables
re-derive exactly from the pstats dumps on disk, and both sampled
spot-checks reproduced. Four findings, all doc-precision — none touches a
banked number, a verdict, or code.

## What was verified (with the evidence that forces each claim)

### Baselines (`docs/perf/rewrite-baselines.md`)

- **Raw-vs-banked, full recomputation** (not sampled — arithmetic is
  cheap): every median, band (min…max), and spread for import / setup /
  reason / cold-start / peak RSS on all three rungs matches an independent
  recomputation from
  `results-phase4-baselines/rewrite-baselines-2026-07-12/bench-report.json`
  (n=7 per rung; cold-start = per-run import+reason, the charter's
  definition; RSS bytes→MiB correct). The oracle side of the side-by-side
  table matches the oracle doc's numbers of record and the oracle raw
  report exactly.
- **Delta arithmetic**: ~730× (2.992/0.0041), ~5.5× (3.611/0.655),
  ~65× (4.376/0.068), RSS ~7.4×/6.6×/4.8×, large Δ median +0.815 s
  (+4.5%), rewrite median 0.268 s above the oracle band max, band overlap
  18.124–18.524 — all recomputed and correct.
- **The large-rung TIE call is honest under the charter's rule**: Δ median
  0.815 s < the oracle's own same-config spread 1.346 s, and the bands
  overlap — a tie by the banked rule, and the doc reports the lean
  plainly ("a genuine tie, not a win"; the rewrite median sits 0.27 s
  above the oracle's band max, stated in the doc's own words). No shading
  found; the regression-shaped fact leads the refinement sentence.
- **Method parity with the oracle series**: same runner (`harness/bench.py`,
  fresh process per measurement under `/usr/bin/time -l`,
  `PYTHONHASHSEED=0`), same n, same rung order (bench.py sorts case paths
  — large→medium→small for both engines, so the thermal-drift position is
  like-for-like as claimed), same machine facts confirmed live: Apple
  M2 Max / arm64 / macOS 26.3 / venv Python 3.13.11
  (`scripts/rewrite-python`) / oracle-env 3.10.20.
- **Cold-start framing fair**: the no-compile-cache statement is engine
  structure, not a flattering comparison — the oracle's 157 s cache build
  stays in its context-never-bar section, and the cold-start bar compared
  against is the oracle's *warm-cache* 4.376 s.
- **`c774312` touched the oracle doc's Reproduction block only** — the
  banked oracle numbers are byte-identical.

### Profile driver (`harness/profile.py`, tests)

- **Window correct**: case validated before any timing; import and setup
  run unprofiled; the profiler wraps exactly one `reason()` call; the
  profiled wall-clock is recorded so overhead is stated against the
  unprofiled banked median, never blended. Input application reuses
  capture.py's validated helpers (no duplication).
- **Rewrite-only by design and in fact**: the docstring states why oracle
  per-function profiling is meaningless (jitted hot loop → one opaque
  dispatcher frame); the artifacts on disk are rewrite-only; the report's
  oracle decomposition is reused bench data, not a profile.
- **The 6 fast-tier tests assert what their `proves:` docstrings say**
  (label shortening + pstats `~` convention, self-time denominator,
  cumulative/self ranking + truncation, named error on unknown sort key,
  empty-stats safety, recursion marker `nc/cc`). The pstats fixture's
  tuple shape matches the real convention.

### Profile report (`docs/perf/profile-phase4.md`)

- **Tables re-derived from the pstats dumps**: all ten large-rung
  self-time rows (self %, self s, cum %, calls) and every named
  cumulative claim (`_ground_rule` 95.2%, `check_all_clause_satisfaction`
  93.8%, edge arm 65.8%, node arm 28.4%, `_apply_fact` 1.7%,
  `_update_component` 1.3%) match an independent read of
  `perf-ladder-large.pstats` exactly; likewise the medium-rung figures
  (75.6% / 72.6% / 51.0%; top-4 self rows). Next-tier rows
  (`get_value` / `lower` / `upper`, 2.6% each) confirmed.
- **The 1:1 call-count ties hold**: `__hash__` = `__str__` =
  `builtins.hash` = 43,382,765; `__eq__` = `get_value` = `isinstance` =
  41,439,141 — the structural-attribution argument is real.
- **Percentage accounting**: denominator = sum of self times =
  `profiled_reason_s` in the JSON headers (79.310 s / 2.588 s);
  the ≈96% chain-plus-primitives claim recomputes to 96.4%; the ≈76%
  claim recomputes to 76.6%.
- **cProfile overhead disclosed and correct**: 79.310/18.792 = 4.22×,
  2.588/0.655 = 3.95×; the report and every artifact header quote the
  profile as distribution-only, and no profiled number is used as a
  wall-clock claim anywhere in the docs.
- **Oracle decomposition consistent with banked bench data**: import
  1.380/1.383/1.389, setup 1.864/1.957/2.000, reason floor never below
  2.922 s on any rung — all verified against the oracle raw report; the
  ≈3.3 s pre-reason + ≈3.0 s in-reason floor and the incremental-scale
  deltas (+0.619 vs +0.651; +14.366 vs +18.137) recompute exactly.
- **Acceleration-candidates section is measured statements**: every number
  cited (93.8/65.8/72.6/51.0%; 73,183 calls inducing 28,368,878) is in
  the dumps; direction statements are framed as candidates and the report
  promises no speedup numbers.

### Sampled spot-checks (one control repeat per claim, machine idle)

- **Bench, via the committed one-command path from a foreign cwd**
  (`scripts/bench-ladder` invoked from a scratch directory — the drill-gap
  fix works): medium reason **0.623 s** vs band 0.654–0.656; large
  **17.984 s** vs band 18.124–18.940; small **0.004 s** (in-band). The
  timing repeats land at/just below the bands' low edges — the documented
  lone-run-vs-series effect (and the trigger for finding 1 below). Memory
  repeats within ~1% of the bands.
- **Profile, medium rung re-run fresh**: ranking reproduced exactly —
  same top functions in the same order (`is_satisfied` 15.0% vs banked
  15.2%, `__hash__` 14.5%, `__eq__` 13.2% vs 13.3%, `__contains__` 9.2%
  vs 9.4%), *identical* call counts (1,057,198 / 1,522,311 / 1,264,319 /
  1,038,437 — the workload is deterministic), same cumulative shape
  (`_ground_rule` 75.2% vs 75.6%, edge arm 50.7% vs 51.0%); profiled
  reason 2.547 s vs the committed run's 2.588 s.

### Drill-gap fixes

- `scripts/bench-ladder`: resolves the repo from its own path, stages the
  three ladder cases into a `mktemp -d` scratch dir (cleaned on exit), and
  runs from the repo root — verified working from a foreign cwd (above).
- Both baselines docs carry a working Reproduction block (the bench-ladder
  one-liner exercised live; the long form preserved in the oracle doc).
- `results-phase4-profile/` present in `.gitignore`; nothing from any
  results dir is tracked.

### Tests

- `uv run pytest -m "not e2e"` → **288 passed, 4 deselected** (author's
  count confirmed; green again after the fixes — the pre-commit hook
  reran the corpus link check on `a45374d`).
- No e2e was run, per the review packet: this session added no harness
  cases and touched none; ladder equivalence was verified twice in
  session 26.

## Findings and fixes (`a45374d`) — all doc-precision

1. **rewrite-baselines.md mischaracterized the lone-run effect**: the
   behavior note claimed the oracle-side lone-run-vs-series effect "has no
   visible rewrite analogue" at small/medium, but the author's own medium
   smoke (0.617 s) and the review's control repeat (0.623 s) both land
   ~5% below the 0.654–0.656 series band. This is the sentence a future
   reader uses to judge a control repeat against the band, so it must be
   right. Now banks the effect for medium (small lone runs land in-band).
2. **"monotonic upward drift" on the rewrite's large series**: the printed
   run sequence itself ends with a dip (18.94 → 18.88); the oracle's series
   was strictly monotonic, the rewrite's is not. Reworded to match the
   printed runs.
3. **profile-phase4.md "top 10 ≈ 88%"**: the top-10 self-time sum is
   85.8% (88.4% is the top-*11* sum). Now reads ≈ 86%.
4. **"same ordering" scale-stability overstated**: `Label.__eq__` and
   `Label.__hash__` swap adjacent ranks 2–3 between medium and large —
   visible in the report's own two tables and reproduced by the review's
   fresh medium profile. The scale-stability bullet now states the swap;
   the conclusion (single spike target covers the ladder) survives intact.

Down-rated (noted, not acted on): the author report repeats the "same hot
set in the same order" phrasing (finding 4) — the author report is the
author's record and the corrected claim lives in the banked doc;
`harness/profile.py` does not mechanically refuse a non-rewrite
interpreter (docstring-only guard) — acceptable since running it under
oracle-env would only produce a meaningless-by-construction artifact, not
a wrong banked number; the review's medium control RSS (46.4 MiB) sits
0.4 MiB above the banked band — within ~1%, consistent with the
lone-run-vs-series conditions, no claim affected.

## Reproduction (this review's exact commands)

```
uv run pytest -m "not e2e"            # 288 passed, 4 deselected

# control repeat via the committed one-command path (run from a foreign cwd):
scripts/bench-ladder scripts/rewrite-python review-control-2026-07-12 1
#   -> medium reason 0.623s, large 17.984s, small 0.004s

# profile re-run, medium rung:
PYTHONHASHSEED=0 scripts/rewrite-python -m harness.profile \
  --case harness/cases/perf-ladder-medium.json \
  --out-dir results-phase4-profile/review-2026-07-12 --top 12
#   -> profiled reason 2.547s; same ranking, identical call counts
```
