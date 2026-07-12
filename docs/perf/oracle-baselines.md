<!-- doccode: pyreason-rewrite-docs-perf-oracle-baselines -->
# Oracle performance baselines — the AC-4 numbers of record (2026-07-12)

The pinned oracle (`e1a94af3`, v3.6.0, `oracle-env/` non-editable install)
measured over the committed workload ladder ([ladder.md](ladder.md)) on the
campaign machine. These are the comparison bars for the rewrite's Phase-4
floor verdict; thresholds beyond the parity floor are proposed only against
these numbers. Sub-band deltas are ties.

## Machine and conditions

- **Chip:** Apple M2 Max (`arm64`); **macOS** 26.3.
- **Power state:** AC power attached throughout (battery 80%, not
  charging); interactive session otherwise idle, no other heavy load.
- **Engine interpreter:** oracle-env Python **3.10.20** (the same
  interpreter the equivalence harness runs engine A with); parent runner
  under the campaign venv (Python 3.13.11); `PYTHONHASHSEED=0` (the
  harness's pinned env fingerprint).
- **Numba kernel cache: warm.** `oracle-env/...//pyreason/cache` stood at
  101 kernel indexes / 110 MB, in place since the Phase-3 sweeps — every
  baseline run below loads kernels from that cache; none builds it.

## Method

`harness/bench.py` (committed this session): one **fresh process per
measurement** under `/usr/bin/time -l`, no probes, so the measured window
is exactly `import pyreason` → input setup → `reason()`. Peak memory =
the OS's per-child `wait4` peak RSS (bytes on macOS), covering the whole
child process. Screen-then-confirm: each rung was smoke-screened once
(numbers in ladder.md) before the confirmation series; the confirmation is
**7 repeats per rung** (7 fresh processes — cold-start therefore also has
7 fresh-process observations), medians banked with the **control-repeat
noise band** (spread = max − min of the same-config repeats) beside every
number. Raw per-run values live in the run artifacts (gitignored
`results-phase4-baselines/oracle-baselines-2026-07-12/`, re-derivable via
the reproduction commands below); the aggregates here are the record.

## One-time cache build — context only, never the comparison bar

With the warm cache set aside (and restored byte-for-byte afterward), one
small-rung run paid the oracle's first-ever kernel compilation inside
`reason()`:

| metric | value |
|---|---|
| import | 1.31 s |
| setup | 1.70 s |
| reason (includes full numba compile) | **157.0 s** |
| peak RSS | 1662 MiB |
| whole child wall | 161.3 s |

Banked as context per the charter: a rewrite with no cache-build phase
would flatter itself against this number, so it is **never** used as a
bar. (Single observation by design — a one-time phenomenon, not a
distribution.)

## Baselines per rung — medians with the noise band (n = 7)

All times seconds; band = (min … max), spread in brackets. Peak RSS in
MiB (of the whole child: import + setup + reason, no probes).

| rung | import | setup | reason() | cold-start (import + first reason) | peak RSS |
|---|---|---|---|---|---|
| **small** | 1.380 (1.335…1.484) [0.149] | 1.864 (1.807…1.885) [0.078] | **2.992** (2.922…3.053) [0.131] | **4.376** (4.267…4.477) [0.209] | **293.4** (292.1…296.2) [4.1] |
| **medium** | 1.383 (1.356…1.401) [0.046] | 1.957 (1.937…1.977) [0.040] | **3.611** (3.529…3.625) [0.096] | 4.981 (4.919…5.013) [0.094] | **303.7** (302.7…305.4) [2.6] |
| **large** | 1.389 (1.311…1.403) [0.092] | 2.000 (1.905…2.041) [0.136] | **17.977** (17.178…18.524) [1.346] | 19.341 (18.570…19.918) [1.348] | **328.6** (327.9…329.9) [2.0] |

- **The cold-start bar** is the small rung's cold-start column
  (**4.376 s median, band 4.267–4.477**): fresh-process import + first
  `reason()`, numba cache warm — the charter's cold-start definition.
  Medium/large cold-start columns are recorded for completeness (every
  fresh-process run is a first-`reason()` run under this method).
- **Peak-RSS floor:** ~292 MiB before any scale effect — the numba/llvmlite
  runtime plus cached-kernel loading dominates the oracle's footprint;
  a decade of workload growth adds only ~35 MiB.

## Measurement behavior notes (honest characterization)

- **Small/medium are stable and unimodal**: reason() spreads of 0.131 s
  (4.4% of median) and 0.096 s (2.7%).
- **The large rung drifts monotonically upward within the series**
  (reason(): 17.18, 17.31, 17.63, 17.98, 18.23, 18.41, 18.52 s run-by-run
  — spread 1.35 s, 7.5% of median), consistent with sustained-load
  thermal/scheduler settling rather than bimodality; the earlier isolated
  smoke runs (17.15 s bench, 17.12 s capture) sit at the series' low end,
  i.e. a lone large run measures faster than the tail of a back-to-back
  series. The full 17.18–18.52 band is therefore the honest noise band
  for large-rung comparisons; rewrite-vs-oracle deltas inside it are ties.
- **The oracle's fixed per-run cost floor**: import ≈ 1.38 s and
  setup ≈ 1.9 s are nearly scale-invariant across a 40× edge-count range,
  and small→medium moves reason() only 2.99 → 3.61 s — per-call fixed
  overhead dominates the pinned engine below the large rung's join-rule
  workload. Any rewrite throughput comparison must therefore quote the
  rung, not an aggregate.

## Reproduction

```
# confirmation series (the numbers above); cases staged into one dir so a
# single invocation writes one report:
mkdir -p /tmp/ladder && cp harness/cases/perf-ladder-*.json /tmp/ladder/
PYTHONHASHSEED=0 uv run python -m harness.bench \
  --engine oracle-env/bin/python --cases /tmp/ladder \
  --repeats 7 --tag oracle-baselines-2026-07-12
# per-rung smoke screen (single repeat):
PYTHONHASHSEED=0 uv run python -m harness.bench \
  --engine oracle-env/bin/python --cases harness/cases/perf-ladder-small.json \
  --repeats 1 --tag smoke
# cache-build context number: set oracle-env's pyreason/cache aside, run the
# small rung once as above, then delete the newly built cache and restore
# the original directory (done once, 2026-07-12; see the table above).
```
