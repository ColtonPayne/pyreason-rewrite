# Review — parallel_computing + output_to_file/output_file_name cases (session 10)

Reviewer: session 10 agent 2 (independent reviewer-fixer; no shared context with the
author). Scope: commits `5b0d8af` (output_file probe capture extension + seam tests),
`e806b60` (4 output cases), `fa77593` (3 parallel cases), `c752584` (board flips),
against the author report
[2026-07-07-parallel-and-file-output-cases-raw.md](2026-07-07-parallel-and-file-output-cases-raw.md).
Every claim re-derived against the pinned source at `e1a94af33e1f`; oracle tree
verified clean before and after all runs.

## Verdict

**Sound.** 0 High / 0 Medium / 3 Low. One Low fixed on the board (F2); two Low are
evidence-precision notes recorded here with the corroboration that settles them
(F1, F3). Post-fix rerun — the verdict-of-record — is green: fast tier 70 passed,
all 7 cases ALL PASS with same-engine repeats.

## What was verified independently

**Pinned anchors (all real, all cited correctly).**
- Defaults `pyreason.py:67/:68/:80`; getters `:94-99/:102-107/:203-209`; setters
  `:247-258/:260-270/:408-419` — line-exact.
- The redirect: `__timestamp` stamped at `:1511`; `sys.stdout = open(f"./{...}_{__timestamp}.txt", "a")`
  at `:1513-1514` and re-opened onto the same name at `:1541-1542`; never flushed,
  closed, or restored. `output_file_name` has exactly those two consumption sites
  (grep-verified) — the inert-when-output-false class is real.
- Dispatch `program.py:42-46`: `_parallel_computing` checked before `_fp_version`,
  else serial optimized — precedence order as cased.
- `diff interpretation.py interpretation_parallel.py` → exactly one line, the
  `parallel=False→True` decorator flip at `interpretation_parallel.py:241`.
  The kernel has exactly one prange loop (`:571`, `for i in prange(len(rules))`,
  threadsafe merge comment `:564`) — the width-1 argument in
  `parallel-computing-on`'s purpose reads correctly: one rule → one iteration →
  no append reordering possible.
- The verbose print sites the redirect file captures: `pyreason.py:1593/:1601`,
  `interpretation.py:238/:257-258/:660/:667/:677` — the banked 8-line file content
  matches these exactly (Filtering → Optimizing → Timestep 0-2 → blank+Converged →
  Fixed Point iterations: 3).

**Capture extension (`5b0d8af`).**
- Validation parity: faults exit 2; the blanket forbid is replaced by a targeted
  rule (`output_to_file === true` requires ≥1 `output_file` probe, checked in both
  case forms via `_all_probes`); explicit false validates bare; `allow_raise`
  refused on the kind with a reasoned message. No `FORBIDDEN_SETTINGS` remnant, no
  dead scaffolding.
- Confinement: `args.out` resolved absolute before any chdir; the case file is
  read before the chdir; `fresh_output_dir` derives strictly from the artifact
  path (`aN.json → aN.outdir` inside `results/<case>/`, gitignored) and clears
  stale files per capture; non-output cases never chdir. The oracle clone stayed
  clean throughout (porcelain empty); nothing written outside the repo.
- Probe behavior: flush-then-glob is correct — the engine's never-flushed redirect
  handle *is* the capture's `sys.stdout`, so the flush lands buffered prints before
  the read; empty list is the compared no-file observation; sort order and non-txt
  exclusion tested. `run_case` prints nothing to stdout before the probe runs, so
  the file content is engine text only (confirmed by the banked content).
- Canonicalization rationale recorded at the definition site: only the wall-clock
  stamp (`OUTPUT_TS_RE`) is canonicalized — `pyreason.py:1511` is run schedule, not
  engine behavior; name, count, and contents compare exactly. The author's own note
  stands: a user-chosen name ending in `_\d{8}-\d{6}` would also canonicalize —
  harmless for equality (both sides canonicalize identically); future case authors
  should avoid pathological names.
- Seam tests: all seven new/changed tests' `proves:` docstrings match their
  assertions; the partition test forces a reason-block ruling on any future kind.

**Cases and cross-case claims (re-derived from the banked artifacts, then again
from my own rerun's artifacts).**
- All four output cases' reasoning digests (`nodes-popular`, `trace-node`,
  `trace-edge`, `time`) identical cross-case — the redirect moves prints, never
  reasoning. On-file vs custom-file contents byte-identical; only the
  canonicalized basename differs (`pyreason_output_` vs `campaign_redirect_`).
  Inert and default twins read the confined directory back empty.
- `parallel-computing-on` ≡ `parallel-computing-default` on every reasoning probe;
  `parallel-fp-precedence` ≡ `parallel-computing-on` on every reasoning probe and
  ≠ `fp-version-on` on `trace-node`/`nodes-popular` (`trace-edge`/`time` match
  vacuously — empty edge trace, get_time 3, as the case text says honestly).
- The knob-discrimination question (does the on-twin prove the knob does
  anything?): the pair alone would not — kernels digest-equal here by design, and
  the readback only proves storage. The **precedence case** carries the behavioral
  proof: with both knobs true the digests take the parallel/optimized shape, not
  fp's — if `parallel_computing` were dead, fp_version would have selected the fp
  kernel and the digests would differ. The trio jointly discriminates. Verified
  digest-by-digest.
- Board (`c752584`): 35/52 cased + 17 uncovered = 52 rows, counts exact; case ids
  ride every row their programs exercise (spot-checked across fn/type/dsl/setting
  rows); nothing claims `equivalent`; the parallel row's equality claim is scoped
  to "the pair's one-rule program (prange width 1)" with multi-rule scheduling
  named uncovered — no overclaim.

## Findings

**F1 (Low) — the caching characterization's banked-evidence citation was
imprecise; corroboration now recorded.** The author's finding 1 cites "the banked
`timing.reason_s` in `results/parallel-computing-on/*.json`" alongside the
scratchpad smoke screens. The banked warm timings alone do not discriminate
compile-from-cache: the serial twin's `reason_s` is statistically identical
(~2.7s vs ~2.8s — in-process cache-load overhead dominates both). The cold ~174s
half of the measurement lives only in the (legitimate, screen-then-confirm) smoke
run. What settles the claim in-repo/in-env: the parallel kernel's single cache
file `oracle-env/.../pyreason/cache/interpretation_*/interpretation_parallel.Interpretation.reason-240.py310.1.nbc`
(10.3 MB, mtime Jul 7 00:41 — the author's cold smoke) was **never rewritten** by
the author's four fresh-process captures at 00:47 (~2.8s each) nor by this
review's rerun (~2.9s) — nine-plus fresh processes reusing one compiled artifact.
The docstring's "re-compiled at each run" cannot survive that. No code change;
corroboration recorded here and referenced from the board.

**F2 (Low, fixed) — the no-caching refutation was scoped to one pinned site; the
belief is written at three.** The board note cited only the getter docstring
(`pyreason.py:204-205`). The identical claim appears in the setter docstring
(`pyreason.py:410-411`) and, differently phrased, in the dispatch comment at
`program.py:41` ("We cannot parallelize with cache on") — while the decorator
itself is `cache=True, parallel=True` and demonstrably caches. This matters for
the rewrite: the belief is pervasive in the pin, not a one-off slip. **Fixed:**
the `setting:parallel_computing` board note now names all three sites and the
cache-file corroboration. (The committed case purpose cites only 204-205, which
is accurate as far as it goes; left untouched to keep the rerun's
verdict-of-record on unedited case text.)

**F3 (Low, no change) — the precedence case's ≠-fp half leans on prior-session
banked artifacts; verified acceptable.** `parallel-fp-precedence`'s harness
verdict self-proves only parallel-vs-parallel; the ≠-fp comparison rides
`results/fp-version-on/*.json` from a prior session. Checked: the oracle pin has
not moved since that run, the artifacts carry the same env fingerprint
(PYTHONHASHSEED=0, same interpreter), and I re-derived the digest comparison
myself at review time (trace-node/nodes-popular differ, trace-edge/time equal
vacuously) — both before and after my rerun. Rerunning fp-version-on would add
nothing and sits outside this packet's e2e budget. Acceptable as banked; the
phase-boundary full-corpus sweep will refresh every artifact anyway.

Also scrutinized, no finding: the `*.txt` glob observing more than the engine's
basename (safe — the directory is fresh per capture, and the trace savers write
only on explicit `save_rule_trace`, not probed here); probe ordering in steps form
being convention rather than validation (documented at the dispatch site; the
one-step form runs all probes post-reason regardless); the double-open handle leak
at `pyreason.py:1541` (no print can land on the first handle between the two opens
on these cases — content evidence confirms exactly one file, 8 lines);
`case_wants_output_dir` truth table (covers knob-true and probe-presence in both
case forms; no step op can turn the knob on).

## Fixes applied by the reviewer

1. `docs/surface.md` `setting:parallel_computing` notes — F2: all three pinned
   no-cache sites named; cache-file corroboration referenced.

## Post-fix rerun (verdict-of-record)

- `uv run pytest -m "not e2e"` → **70 passed**.
- Each of the 7 cases via
  `uv run python -m harness.run --cases harness/cases/<case>.json --engine-a oracle-env/bin/python`
  → **ALL PASS** (4 fresh-process captures each, PYTHONHASHSEED=0, same-engine
  repeats compared by exact digest): output-to-file-default, output-to-file-on,
  output-file-name-custom, output-file-name-inert, parallel-computing-default,
  parallel-computing-on, parallel-fp-precedence.
- Cross-case digest checks re-derived on the rerun's artifacts — all of §3's
  claims reproduce.
- Oracle tree clean at `e1a94af33e1f` before and after; no full-corpus sweep run
  (phase-boundary property preserved).
