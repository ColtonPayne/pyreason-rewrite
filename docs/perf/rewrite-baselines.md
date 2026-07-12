<!-- doccode: pyreason-rewrite-docs-perf-rewrite-baselines -->
# Rewrite performance baselines — the AC-4 confirmed numbers (2026-07-12)

The pure-Python reference core (engine B, `scripts/rewrite-python`:
campaign venv + `src/` on `PYTHONPATH`) measured over the committed
workload ladder ([ladder.md](ladder.md)) on the campaign machine, same
method, same session-day conditions, and same runner as the oracle's
numbers of record ([oracle-baselines.md](oracle-baselines.md)). These are
the rewrite side of the Phase-4 floor verdict; sub-band deltas are ties.

## Machine and conditions

- **Chip:** Apple M2 Max (`arm64`); **macOS** 26.3.
- **Power state:** AC power attached throughout (battery 80%, not
  charging); interactive session otherwise idle, no other heavy load —
  the same state recorded for the oracle series.
- **Engine interpreter:** campaign venv Python **3.13.11** via
  `scripts/rewrite-python` (the same interpreter the equivalence harness
  runs engine B with); `PYTHONHASHSEED=0` (the harness's pinned env
  fingerprint).
- **No compile cache exists to warm.** The reference core is pure Python:
  it has no kernel-compilation phase and no on-disk cache, so there is no
  rewrite analogue of the oracle's one-time 157 s cache build (banked as
  context in oracle-baselines.md) and no warm/cold cache precondition to
  state — every fresh process is already the engine's true cold state.

## Method

Identical to the oracle series: `harness/bench.py`, one **fresh process
per measurement** under `/usr/bin/time -l`, no probes, measured window
exactly `import pyreason` → input setup → `reason()`; peak memory is the
OS's per-child `wait4` peak RSS. Screen-then-confirm: each rung
smoke-screened once (reason(): small 0.004 s, medium 0.617 s, large
18.236 s — consistent with the single-run screens recorded in ladder.md),
then the confirmation series of **7 repeats per rung** in one invocation
via `scripts/bench-ladder` (all three rungs in one report; series order
large → medium → small). Medians banked with the control-repeat noise
band (spread = max − min) beside every number. Raw per-run values live in
the gitignored run artifacts
(`results-phase4-baselines/rewrite-baselines-2026-07-12/`, re-derivable
via the reproduction commands below); the aggregates here are the record.

## Baselines per rung — medians with the noise band (n = 7)

All times seconds; band = (min … max), spread in brackets. Peak RSS in
MiB (whole child: import + setup + reason, no probes).

| rung | import | setup | reason() | cold-start (import + first reason) | peak RSS |
|---|---|---|---|---|---|
| **small** | 0.064 (0.063…0.065) [0.002] | 0.0021 (0.0021…0.0021) [0.0001] | **0.0041** (0.0041…0.0041) [0.0000] | **0.068** (0.067…0.069) [0.002] | **39.7** (39.6…39.8) [0.2] |
| **medium** | 0.064 (0.063…0.067) [0.003] | 0.020 (0.020…0.020) [0.0004] | **0.655** (0.654…0.656) [0.002] | 0.719 (0.718…0.721) [0.004] | **45.9** (45.7…46.0) [0.3] |
| **large** | 0.065 (0.060…0.070) [0.010] | 0.049 (0.047…0.051) [0.004] | **18.792** (18.124…18.940) [0.816] | 18.857 (18.189…19.004) [0.815] | **68.8** (68.2…69.0) [0.8] |

- **The cold-start bar** is the small rung's cold-start column
  (**0.068 s median, band 0.067–0.069**): fresh-process import + first
  `reason()`. No cache is involved on either side of the import.
- **Peak-RSS floor:** ~40 MiB before any scale effect; the ladder's
  40× edge-count range adds ~29 MiB (39.7 → 68.8).

## Side-by-side vs the oracle's banked bands (n = 7 both sides)

Oracle numbers from [oracle-baselines.md](oracle-baselines.md); verdicts
follow the banked tie rule — a cross-engine delta smaller than the noise
band is a tie.

| metric | rewrite median (band) | oracle median (band) | verdict |
|---|---|---|---|
| small reason() | 0.0041 (0.0041…0.0041) | 2.992 (2.922…3.053) | **rewrite faster** (~730×; bands disjoint) |
| medium reason() | 0.655 (0.654…0.656) | 3.611 (3.529…3.625) | **rewrite faster** (~5.5×; bands disjoint) |
| large reason() | 18.792 (18.124…18.940) | 17.977 (17.178…18.524) | **tie within the band** (Δ median +0.815 s, +4.5% — smaller than the oracle's own 1.346 s series spread; bands overlap 18.124–18.524) |
| cold-start (small) | 0.068 (0.067…0.069) | 4.376 (4.267…4.477) | **rewrite faster** (~65×; bands disjoint) |
| small peak RSS (MiB) | 39.7 (39.6…39.8) | 293.4 (292.1…296.2) | **rewrite smaller** (~7.4×) |
| medium peak RSS (MiB) | 45.9 (45.7…46.0) | 303.7 (302.7…305.4) | **rewrite smaller** (~6.6×) |
| large peak RSS (MiB) | 68.8 (68.2…69.0) | 328.6 (327.9…329.9) | **rewrite smaller** (~4.8×) |

**Floor verdict input (the charter's question, per rung):** the reference
core is faster than the oracle beyond the noise band on the small and
medium rungs and on cold-start, and **not worse than the oracle beyond
the band on the large rung** (tie). The session-26 screen-level
observation is therefore *confirmed* for small/medium (faster) and
*refined* for large: the screens' "parity" is a genuine tie, not a win —
the rewrite's large-rung median lands 0.27 s above the oracle's band max,
but the median-to-median delta (0.815 s) is inside the oracle's own
same-config spread (1.346 s) and the two series' bands overlap.

## Measurement behavior notes (honest characterization)

- **Small/medium are extremely stable within a series**: reason() spreads
  of 0.0000 s and 0.002 s (0.3% of the medium median) — pure-Python
  execution with no JIT/cache variance. The oracle-side lone-run-vs-series
  effect *does* have a rewrite analogue at the medium rung: isolated
  single runs (the author's smoke 0.617 s; the review's control repeat
  0.623 s) land ~5% below the series band's low edge, so the banked band
  is a back-to-back-series band, mildly conservative as a bar for a lone
  run — the same characterization banked for the oracle. The small rung
  shows no visible effect (lone runs land in-band).
- **The large rung shows the same sustained upward drift as the oracle's
  series** (reason(): 18.12, 18.41, 18.67, 18.79, 18.87, 18.94, 18.88 s
  run-by-run — rising through run 6 and easing slightly at the tail,
  where the oracle's series rose strictly; spread 0.816 s, 4.3% of
  median), consistent with
  sustained-load thermal/scheduler settling; the isolated smoke run
  (18.24 s) sits near the series' low end. The full 18.12–18.94 band is
  the honest noise band for large-rung comparisons.
- **The rewrite's fixed per-run cost is ~0.07 s** (import ≈ 0.064 s,
  setup 0.002–0.049 s scaling with input size) versus the oracle's
  ≈ 3.3 s pre-reason floor — the oracle's fixed per-call overhead
  decomposition is banked in the Phase-4 profile report
  (`docs/perf/profile-phase4.md`).

## Post-spike baselines (session 28, 2026-07-12) — after the algorithmic spike

The numbers above remain the session-27 pre-spike record. This section
banks the same measurement (same machine class, same method, same
runner, n = 7 per rung via `scripts/bench-ladder`, `PYTHONHASHSEED=0`)
after the four kept spike candidates of session 28 (commits `c56d238`
memoized node-arm per-head clause re-check, `c218f45` cached Label
hash, `958523a` hoisted qualified-grounding scans, `ca600a3` loader
label canonicalization). Equivalence evidence for the kept set: fast
tier 288 passed, ladder-3 oracle-vs-rewrite ALL PASS, plus a 16-case
stratified grounding-heavy sample ALL PASS (author report,
`docs/reviews/2026-07-12-phase4-spike-author.md`).

| rung | import | setup | reason() | cold-start (import + first reason) | peak RSS |
|---|---|---|---|---|---|
| **small** | 0.064 (0.063…0.064) [0.001] | 0.0021 (0.0021…0.0021) [0.0001] | **0.0028** (0.0028…0.0028) [0.0000] | **0.067** (0.066…0.067) [0.001] | **39.6** (39.6…39.8) [0.2] |
| **medium** | 0.065 (0.063…0.065) [0.002] | 0.020 (0.019…0.020) [0.0004] | **0.151** (0.151…0.153) [0.002] | 0.216 (0.215…0.217) [0.002] | **45.8** (45.6…46.0) [0.4] |
| **large** | 0.066 (0.064…0.083) [0.019] | 0.048 (0.048…0.049) [0.001] | **1.226** (1.224…1.240) [0.017] | 1.294 (1.288…1.315) [0.027] | **67.1** (66.6…68.7) [2.1] |

Versus the pre-spike record and the oracle bands (verdicts by the same
tie rule):

| metric | post-spike (band) | pre-spike (band) | oracle (band) | verdict |
|---|---|---|---|---|
| small reason() | 0.0028 (0.0028…0.0028) | 0.0041 (0.0041…0.0041) | 2.992 (2.922…3.053) | **1.46× vs pre-spike** (bands disjoint); ~1070× vs oracle |
| medium reason() | 0.151 (0.151…0.153) | 0.655 (0.654…0.656) | 3.611 (3.529…3.625) | **4.3× vs pre-spike** (bands disjoint); ~24× vs oracle |
| large reason() | 1.226 (1.224…1.240) | 18.792 (18.124…18.940) | 17.977 (17.178…18.524) | **15.3× vs pre-spike, 14.7× vs oracle** (all three bands disjoint — the session-27 tie becomes a win) |
| cold-start (small) | 0.067 (0.066…0.067) | 0.068 (0.067…0.069) | 4.376 (4.267…4.477) | tie vs pre-spike (import dominates; bands touch); ~65× vs oracle |
| large peak RSS (MiB) | 67.1 (66.6…68.7) | 68.8 (68.2…69.0) | 328.6 (327.9…329.9) | tie vs pre-spike (bands overlap); ~4.9× smaller than oracle |

The large rung's post-spike series is far more stable than the
pre-spike one (spread 0.017 s = 1.4% of median, vs 0.816 s = 4.3%):
the run is now too short for the sustained-load drift the pre-spike
series showed. The post-spike per-function profile is banked in
`results-phase4-profile/rewrite-postspike-2026-07-12/` and summarized
in the session-28 author report; the pre-spike profile report
([profile-phase4.md](profile-phase4.md)) remains the record of the
pre-spike distribution.

## Reproduction

```
# post-spike confirmation series (the session-28 numbers):
scripts/bench-ladder scripts/rewrite-python rewrite-postspike-2026-07-12 7
# pre-spike confirmation series (the session-27 numbers of record):
scripts/bench-ladder scripts/rewrite-python rewrite-baselines-2026-07-12 7
# per-rung smoke screen (single repeat, one rung):
PYTHONHASHSEED=0 uv run python -m harness.bench \
  --engine scripts/rewrite-python \
  --cases harness/cases/perf-ladder-small.json --repeats 1 --tag smoke
# oracle side of the comparison table:
scripts/bench-ladder oracle-env/bin/python oracle-baselines-<date> 7
```
