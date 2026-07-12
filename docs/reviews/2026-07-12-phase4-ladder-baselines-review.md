<!-- doccode: pyreason-rewrite-docs-reviews-phase4-ladder-baselines-review -->
# Session-26 independent review — the AC-4 ladder and the oracle baselines

- Session: 26 (review pass, 2026-07-12)
- Reviewer: independent reviewer-fixer (Fable), no shared context with the
  author; reviewed from the committed evidence
- Scope: `8c43efc` (ladder + fixtures + rationale), `f81855d` (bench runner
  + tests), `fff0eff` (banked baselines), `7a5d127` (author report)
- Fixes applied by this review: `8f4213b`

## Verdict

**Approved with fixes.** The ladder meets the charter's AC-4 design bar,
B16 is structural in the design, the runner's timing boundaries are clean
and honestly documented, the banked numbers match the raw run artifacts
exactly, and every reproduced claim reproduced. Three findings, none
touching a banked number: one latent path bug in the runner's parent/child
seam (reachable only under a foreign-cwd invocation), two doc precisions.

## What was verified (with the evidence that forces each claim)

### Design (ladder + cases + fixtures)

- **Rationale coherent**: the rung dimensions scale what the pinned engine
  spends time on — grounding (the large rung's 4-clause join is the
  superlinear stressor), rule firing / interval updates (chain depth 2→3→5),
  and per-timestep fact application (staggered windows keep late timesteps
  doing real work). The medium rung's flatness on the oracle (~2.7 s fixed
  floor swamps chain grounding) is stated candidly rather than hidden.
- **B16 structural**: every rung declares an explicit positive `timesteps`
  (10/40/75) and no rung sets `fp_version` at all; stated in ladder.md and
  in each case's `purpose`. The cited hang site verified in the oracle
  source: `t==tmax` is the only timestep-loop exit
  (`oracle/pyreason/pyreason/scripts/interpretation/interpretation_fp.py:272-273`).
- **No `output_to_file`** (B34) in any rung; `verbose=false` everywhere.
- **Corpus seam contract**: all three case records carry id · purpose ·
  inputs · probes · comparison · surface_items · provenance `perf ladder` ·
  runtime_class (smoke/standard/long). The 11 surface items listed per case
  match the 11 board rows the case ids were appended to
  (`grep -c perf-ladder-small docs/surface.md` → 11; statuses unchanged).
- **Fixtures reproducible**: `uv run python tools/gen_perf_fixtures.py` →
  3× "up to date" (the script compares generated text to disk and errors on
  drift). Parsed fixtures match the committed table exactly — 50/150,
  400/2400, 1000/6000 nodes/edges; directed; no self-loops or duplicate
  pairs; every edge exactly one of rel0/rel1/rel2 with value 1.

### Runner (`harness/bench.py`)

- **Timing boundaries**: the child validates the case *before* starting any
  timer; `import_s` wraps `import pyreason` alone; `setup_s` wraps
  settings/graph/rules/facts/ipl; `reason_s` wraps `reason()` alone; no
  probes run. Verified that nothing in the child's pre-import path
  (`harness.capture` → `harness.reference_fns`, `harness.compare`) imports
  pyreason at module scope, so the import window is clean. The doc's
  description matches the code.
- **Reuse, not duplication**: the child calls capture.py's
  `validate_case`/`apply_settings`/`build_graph`/`build_rule`/
  `add_fact_from_args`/`build_reason_args`; the parent mirrors
  `harness.run`'s subprocess seam (`cwd=REPO`, `PYTHONHASHSEED=0`).
- **Peak RSS**: `/usr/bin/time -l` on this macOS reports
  `maximum resident set size` in **bytes** (verified against live output);
  last-match-wins parsing defends against a child echoing a look-alike
  line. The stated rejection of `RUSAGE_CHILDREN` (monotonic across
  children) is correct.
- **Aggregation honest**: median/min/max/spread per metric, raw values
  banked in the report JSON; `cold_start_s = import_s + reason_s` per run
  (the charter's definition verbatim — setup excluded, and documented as
  such); a failed or partial child payload fails the invocation. The 11
  fast-tier tests assert exactly what their `proves:` docstrings say.
- **No speculative scaffolding**: the only rewrite-side surface is the
  `--engine` parameter.

### Numbers (sampled re-verification, per the review's cost discipline)

- **Banked vs raw**: every median, band, and spread in
  `docs/perf/oracle-baselines.md` matches the raw
  `results-phase4-baselines/oracle-baselines-2026-07-12/bench-report.json`
  aggregates exactly (n=7 per rung; the large rung's monotonic 17.18→18.52 s
  run sequence is in the raw values as characterized).
- **Machine identity**: Apple M2 Max / macOS 26.3 / oracle-env Python
  3.10.20 / parent 3.13.11 / AC power (80%, not charging) — all confirmed
  live on the machine and in the report's machine block.
- **Cache-warm precondition**: `oracle-env/.../pyreason/cache` holds 101
  `.nbi` kernel indexes / 110 MB, matching the doc; the reviewer's control
  repeats show ~1.3 s imports and ~2.8 s small-rung reason() — warm-cache
  behavior, proving the cache-build measurement's restore left the warm
  cache in place.
- **Control repeats (one per claim, machine otherwise idle)**:
  - medium: reason **3.359 s** vs band 3.529–3.625 (4.8% below min);
    peak RSS **304.2 MiB** vs band 302.7–305.4 (inside).
  - small: reason **2.804 s** vs band 2.922–3.053; cold-start **4.100 s**
    vs band 4.267–4.477 (both ~4% below min); peak RSS **291.9 MiB** vs
    band 292.1–296.2 (0.2 MiB under the edge).
  - A third small-rung run during fix verification: reason 2.741 s.

  The timing repeats land consistently *just below* the banked bands —
  exactly where the author's own smoke screens sit (2.73 / 3.27 s). This is
  the doc's lone-run-vs-back-to-back-series effect, not fabrication or a
  methodology error: the bands are same-config series bands and are mildly
  conservative as bars for a lone run. The review added that
  generalization to the doc's behavior notes (finding 3) rather than
  leaving it large-rung-specific. Memory repeats sit inside/at the bands.
- **Cache-build context number**: clearly labeled context-not-bar in its
  own section, single observation by design; the rewrite-faster screen
  observation lives in ladder.md/author report explicitly labeled as
  single smoke runs — no confirmed cross-engine claim is made anywhere.

### Equivalence and tests (reproduced fresh)

- `uv run pytest -m "not e2e"` → **282 passed, 4 deselected** (author's
  count confirmed; green again after the review fix, rerun by the
  pre-commit hook on `8f4213b`).
- `uv run pytest tests/test_bench_runner.py -q` → **11 passed**.
- Ladder equivalence, fresh results dir, the author's exact command shape:
  `PYTHONHASHSEED=0 uv run python -m harness.run --cases <dir with the 3
  perf-ladder cases> --engine-a oracle-env/bin/python --engine-b
  scripts/rewrite-python --results results-phase4-ladder-review` →
  **ALL PASS (3 case(s))**, exit 0. No other e2e was run.

## Findings and fixes (`8f4213b`)

1. **bench.py parent/child path disagreement** (latent, loud-failure): the
   parent resolved a relative `--cases`/`--results` against the invoker's
   cwd while children resolve against `cwd=REPO`, so a foreign-cwd
   invocation (reachable only via PYTHONPATH-style launch — `uv run -m`
   already requires the repo root) wrote the child payload and the parent's
   artifacts to different trees and failed with "unreadable child payload".
   Fixed by resolving both paths in the parent before any child sees them;
   verified by a live foreign-cwd run with a relative `--results` (exit 0,
   artifacts in the invoker-relative dir). No banked number is affected —
   the baselines ran from the repo root where the paths agree.
2. **ladder.md stagger formula**: `start = i mod (timesteps/2)` is only
   exact for even timesteps; the large rung (75) actually uses mod 37 —
   the committed facts' starts are 0..36. Now reads `⌊timesteps/2⌋`.
3. **Baselines behavior note generalized**: the lone-run-faster effect was
   documented only for the large rung; the review's control repeats show it
   on small/medium too. One sentence added marking the bands as
   back-to-back-series bands, citing both the author's smokes and the
   review's repeats.

Down-rated (noted, not acted on): `parent_main` reads the case id with a
bare `json.loads` (an unparseable committed case would traceback rather
than emit a named fault — still loud, and the child validates the same
file); the two IDE type-checker diagnostics on bench.py (`str | None`,
`__doc__`) are project-config noise — the union syntax is the codebase
convention (capture.py, 9 uses) and both engine interpreters are ≥ 3.10.

## Reproduction (this review's exact commands)

```
uv run pytest -m "not e2e"                        # 282 passed, 4 deselected
uv run pytest tests/test_bench_runner.py -q      # 11 passed
uv run python tools/gen_perf_fixtures.py         # 3x "up to date"

# equivalence, fresh results dir (stage the 3 ladder cases into one dir):
PYTHONHASHSEED=0 uv run python -m harness.run --cases <staged-dir> \
  --engine-a oracle-env/bin/python --engine-b scripts/rewrite-python \
  --results results-phase4-ladder-review          # ALL PASS (3 case(s))

# sampled control repeats (one per spot-checked claim):
PYTHONHASHSEED=0 uv run python -m harness.bench --engine oracle-env/bin/python \
  --cases harness/cases/perf-ladder-medium.json --repeats 1 \
  --results <scratch> --tag review-medium         # reason 3.359s, RSS 304.2 MiB
PYTHONHASHSEED=0 uv run python -m harness.bench --engine oracle-env/bin/python \
  --cases harness/cases/perf-ladder-small.json --repeats 1 \
  --results <scratch> --tag review-small          # reason 2.804s, cold 4.100s
```
