<!-- doccode: pyreason-rewrite-docs-reviews-phase4-ladder-baselines-author -->
# Phase 4 opens — the AC-4 workload ladder and the oracle baselines (author report)

- Session: 26 (packet dispatched 2026-07-11; screens and measurements ran
  2026-07-12 — the sitting crossed midnight, measurement date recorded in
  the baselines doc)
- Author: campaign worker (Fable)
- Deliverables: committed ladder ([docs/perf/ladder.md](../perf/ladder.md)),
  benchmark runner (`harness/bench.py` + `tests/test_bench_runner.py`),
  banked baselines ([docs/perf/oracle-baselines.md](../perf/oracle-baselines.md))
- Commits: `8c43efc` (ladder + fixtures + rationale), `f81855d` (runner +
  tests), `fff0eff` (banked baselines), plus this report

## Verdict

**Done.** The three-rung ladder is committed as harness cases (performance
and equivalence share inputs), the three-case oracle-vs-rewrite harness run
is **3/3 PASS**, the stdlib-only benchmark runner is committed with its pure
layer under 11 fast-tier tests (fast tier **282 passed, 4 deselected**), and
the oracle baselines are banked with 7-repeat medians, control-repeat noise
bands, the separately-labeled one-time cache-build context number, and the
machine identity. The B16 hazard is structural in the ladder design.

## Design decisions

1. **Ladder cases are ordinary harness cases** (`perf-ladder-{small,medium,
   large}`, provenance `perf ladder`, runtime classes smoke/standard/long) —
   one-step form, `load_graphml` over committed fixtures, tier-chain rules,
   staggered-window facts, two `filter_sort_nodes` probes + `get_time`.
   Default engine config: no `fp_version`, no `parallel_computing`, no
   `output_to_file` (B34); `verbose=false` follows the spine-case
   convention (per-step console printing is run schedule, not reasoning
   work). **B16 is structural twice over:** every rung declares an explicit
   positive `timesteps`, and no rung touches `fp_version` at all — stated
   in ladder.md and in each case's `purpose`.
2. **Fixtures from a committed, seeded, stdlib generator**
   (`tools/gen_perf_fixtures.py`): ring backbone (connectivity + every
   relation label in every neighborhood) plus seeded random extra edges;
   regeneration is byte-identical and the script *errors on drift* unless
   `--write` is passed. No randomness at measure time.
3. **Scaling dimensions** (recorded rationale in ladder.md): graph size,
   rule count/chaining depth, timesteps, fact volume — chosen against what
   the engine spends time on (grounding, rule firing/interval updates,
   per-timestep fact application; staggered fact windows keep state
   changing so late timesteps do real work). The large rung adds the
   4-clause hello-world join shape at scale — the grounding stressor.
4. **Benchmark runner reuses, never duplicates**: `harness/bench.py`'s
   child imports capture.py's validated input-application helpers
   (`validate_case`, `apply_settings`, `build_graph`, `build_rule`,
   `add_fact_from_args`, `build_reason_args`) and runs **no probes**, so
   the measured window is exactly import → setup → reason. One fresh
   process per measurement (capture.py's subprocess seam), `PYTHONHASHSEED=0`
   like `harness.run`. The runner takes `--engine`, so the same tool
   measures the rewrite later; nothing rewrite-specific was built.
5. **Peak memory metric**: per-child peak RSS from `/usr/bin/time -l`
   (macOS reports bytes, sourced from `wait4`'s per-child rusage).
   `resource.getrusage(RUSAGE_CHILDREN)` was rejected because that counter
   is monotonic across successive children — repeats would contaminate
   each other. Documented as peak-of-process over import+setup+reason.
6. **Noise band**: spread (max − min) of same-config repeats, banked
   beside every median; raw per-run values ride in the report JSON so the
   aggregates are re-derivable. A failed child run fails the whole bench
   invocation — no partial series can aggregate silently.

## Screen results (screen-then-confirm, every rung screened before sizing was committed)

Sizes were tuned by cheap single-run screens before anything was committed
— two revisions driven by screens, recorded here deliberately:

| iteration | rung sizes (nodes/edges/timesteps) | oracle reason() screen | rewrite reason() screen | action |
|---|---|---|---|---|
| draft 1 | 50/150/10 · 200/800/25 · 500/2500/50 | 2.73 / 2.85 / 4.03 s | 0.004 / 0.07 / 1.47 s | medium & large sat on the oracle's ~2.7 s fixed-overhead floor — not discriminating; grew large |
| draft 2 | large → 1000/6000/75 | large 17.12 s | large 17.59 s | large now stresses grounding at scale (join rule dominates); grew medium |
| committed | 50/150/10 · 400/2400/40 · 1000/6000/75 | 2.73 / 3.27 / 17.12 s | 0.004 / 0.61 / 17.59 s | all rungs ≪ 3 min single-run; committed |

Every screened rung was digest-equal oracle-vs-rewrite at screen time
(single captures compared by digest before the harness run). A noteworthy
screen finding banked in the baselines doc: the pinned oracle's per-run
fixed cost (import ≈ 1.38 s, setup ≈ 1.9 s, reason floor ≈ 2.7 s) is
nearly scale-invariant below the large rung, while the pure-Python rewrite
is *faster* than the oracle on small/medium and at parity on large — the
Phase-4 floor conversation will be rung-specific.

## Equivalence of the ladder cases (this packet's only e2e)

```
PYTHONHASHSEED=0 uv run python -m harness.run --cases <dir with the 3 perf-ladder cases> \
  --engine-a oracle-env/bin/python --engine-b scripts/rewrite-python \
  --results results-phase4-ladder
```

→ `pass perf-ladder-large` / `pass perf-ladder-medium` /
`pass perf-ladder-small` — **ALL PASS (3 case(s))**, 12 captures (two
same-engine repeat pairs per case), report at
`results-phase4-ladder/report.json` (gitignored per the results
convention). No other e2e was run; the full-corpus sweep is not this
packet's to run. Board: the three case ids appended to the `cases`
columns of the 11 already-`equivalent` rows they cover (statuses
unchanged, per the board's conventions); board gate green.

## Banked baseline numbers (the record lives in docs/perf/oracle-baselines.md)

Machine: Apple M2 Max, macOS 26.3, AC power, oracle-env Python 3.10.20,
numba cache **warm** (101 kernel indexes / 110 MB standing since Phase 3 —
checked before measuring, as the packet required). n = 7 fresh processes
per rung; median (band) [spread]:

| rung | reason() s | cold-start s | peak RSS MiB |
|---|---|---|---|
| small | 2.992 (2.922…3.053) [0.131] | **4.376** (4.267…4.477) [0.209] | 293.4 [4.1] |
| medium | 3.611 (3.529…3.625) [0.096] | 4.981 [0.094] | 303.7 [2.6] |
| large | 17.977 (17.178…18.524) [1.346] | 19.341 [1.348] | 328.6 [2.0] |

- **Cache-build context** (never the bar): with the warm cache set aside,
  one small-rung run paid 157.0 s of reason-time compilation at 1662 MiB
  peak; the pre-existing cache directory was restored afterward and
  verified back in place (the confirmation series that followed shows
  warm-cache numbers, proving the restore).
- **Honest characterization**: small/medium unimodal and tight; the large
  rung drifts monotonically upward within a back-to-back series
  (17.18 → 18.52 s over 7 runs, consistent with sustained-load thermal
  settling) — the full band is banked as the noise band rather than
  averaged away.

## Reproduction (exact commands, with pass counts)

```
uv run pytest -m "not e2e"                         # 282 passed, 4 deselected
uv run pytest tests/test_bench_runner.py -q       # 11 passed
uv run python tools/gen_perf_fixtures.py          # 3x "up to date" (fixture-drift guard)

mkdir -p /tmp/ladder && cp harness/cases/perf-ladder-*.json /tmp/ladder/
PYTHONHASHSEED=0 uv run python -m harness.run --cases /tmp/ladder \
  --engine-a oracle-env/bin/python --engine-b scripts/rewrite-python \
  --results results-phase4-ladder                  # ALL PASS (3 case(s))

PYTHONHASHSEED=0 uv run python -m harness.bench --engine oracle-env/bin/python \
  --cases /tmp/ladder --repeats 7 --tag oracle-baselines-2026-07-12
                                                   # exit 0; report JSON with medians+bands
```

## Deviations

- **Ladder sizes revised twice during screening** (medium 200→400 nodes,
  large 500→1000) before anything was committed — the screen-then-confirm
  loop doing its job; both drafts and their screens are tabled above.
- **`verbose=false` in the ladder cases** where the packet said "default
  engine config": the packet's enumeration (no fp_version /
  parallel_computing / output_to_file) is honored exactly; verbose was
  additionally pinned off following every committed spine case, so console
  printing never rides a timing window. Recorded as a design choice, not
  silently.
- **`oracle-env`'s kernel-cache directory was set aside and restored** for
  the one cache-build context measurement — runtime state of the dedicated
  environment (the harness itself snapshots/restores this directory for
  registrand cases); `oracle/pyreason/` was never touched and the pin
  never moved.
- **Report filename keeps the packet's 2026-07-11 date** while the
  measurements themselves are dated 2026-07-12 inside the docs (the
  sitting crossed midnight).
- `docs/perf/ladder.md` briefly used plain-text references to the
  then-unwritten baselines doc because the corpus link gate (correctly)
  refuses forward links; commit `fff0eff` restored real links once the
  file existed.

## Follow-ups queued for later packets (not built speculatively)

- Rewrite-side baselines over the same rungs (`--engine
  scripts/rewrite-python`) — the runner takes the engine parameter; the
  screens above suggest the rewrite wins small/medium and ties large, but
  **no claim is made until measured with bands**.
- Profiling (where time goes per engine) is the next charter step after
  baselines; nothing profiled this session.
- If a knob-position ladder (e.g. fp_version) is ever wanted, it must be
  new committed rungs with explicit bounds — B16 forbids `fp_version` +
  `timesteps=-1` structurally.
