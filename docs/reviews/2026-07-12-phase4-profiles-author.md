<!-- doccode: pyreason-rewrite-docs-reviews-2026-07-12-phase4-profiles-author -->
# Author report — session 27: rewrite baselines confirmed, Phase-4 profiles banked

Packet: (1) rewrite-side confirmed AC-4 baselines, (2) the profiling
deliverable naming where time goes in both engines, (3) the two
cold-pickup-drill doc gaps (bench staging one-liner; profile-results
gitignore). Author: campaign worker, session 27 (2026-07-12).

## Methodology

**Baselines.** Same discipline, runner, machine, and power state as the
oracle's numbers of record ([oracle-baselines.md](../perf/oracle-baselines.md)):
`harness/bench.py`, fresh process per measurement under `/usr/bin/time -l`,
`PYTHONHASHSEED=0`, AC power attached (battery 80%, not charging),
session otherwise idle. Screen-then-confirm: one smoke run per rung first
(reason(): small 0.004 s, medium 0.617 s, large 18.236 s — all consistent
with the session-26 screens of 0.004 / 0.61 / 17.6 s, the large smoke
sitting where a lone run is documented to sit relative to a series), then
the confirmation series of **7 fresh processes per rung** in a single
invocation via the new `scripts/bench-ladder` helper (dogfooded for the
run that produced the banked numbers). The rewrite has **no compile cache**
— there is no warm/cold precondition to state and no analogue of the
oracle's one-time 157 s cache build; every fresh process is the engine's
true cold state (stated in the banked doc where the oracle doc banks its
cache context).

**Profiles.** New committed driver `harness/profile.py` (stdlib
cProfile/pstats; pure extraction/formatting layer covered by 6 fast-tier
tests with `proves:` docstrings): one in-process run per rung under the
engine interpreter, profiler active around `reason()` only, emitting a
pstats dump + top-25 tables by cumulative and by self time
(artifacts: gitignored `results-phase4-profile/rewrite-2026-07-12/`).
cProfile overhead measured by comparing profiled wall vs the unprofiled
banked median — medium 2.588 vs 0.655 s (4.0×), large 79.310 vs 18.792 s
(4.2×) — so the profile is quoted as a distribution only; wall-clock
claims come solely from bench. The oracle side is per-stage wall-clock
**reused** from the banked n=7 report
(`results-phase4-baselines/oracle-baselines-2026-07-12/bench-report.json`),
not re-measured; per-function profiling of the oracle is meaningless by
construction (jitted hot loop).

## Confirmed rewrite numbers (n = 7 medians, band = min…max)

Banked in [rewrite-baselines.md](../perf/rewrite-baselines.md):

| rung | reason() | cold-start | peak RSS |
|---|---|---|---|
| small | 0.0041 s (0.0041…0.0041) | 0.068 s (0.067…0.069) | 39.7 MiB |
| medium | 0.655 s (0.654…0.656) | 0.719 s (0.718…0.721) | 45.9 MiB |
| large | 18.792 s (18.124…18.940) | 18.857 s (18.189…19.004) | 68.8 MiB |

## The floor comparison per rung (the charter's question)

Verdicts by the banked tie rule (delta inside the noise band = tie):

- **small: rewrite faster** — 0.0041 s vs oracle 2.992 s (2.922…3.053);
  bands disjoint by three orders of magnitude (~730×).
- **medium: rewrite faster** — 0.655 s vs 3.611 s (3.529…3.625); bands
  disjoint (~5.5×).
- **large: tie within the band** — 18.792 s (18.124…18.940) vs 17.977 s
  (17.178…18.524). Median-to-median Δ = +0.815 s (+4.5%), smaller than
  the oracle's own same-config series spread (1.346 s); the bands overlap
  (18.124–18.524). The rewrite is **not worse than the oracle beyond the
  band** — the floor holds on the large rung.
- **cold-start: rewrite faster** — 0.068 s vs 4.376 s (4.267…4.477),
  ~65×, bands disjoint.
- **peak RSS: rewrite smaller on every rung** (39.7/45.9/68.8 vs
  293.4/303.7/328.6 MiB).

**Verdict on the session-26 screen-level observation:** *confirmed* for
small/medium/cold-start (faster beyond the band) and *refined* for large
— the screens' "parity" is a genuine tie, not a win: the rewrite median
lands 0.27 s above the oracle's band max, but inside the tie criterion.
The rewrite's large series shows the same monotonic upward thermal drift
the oracle's did (18.12 → 18.94 s run-by-run), so the band comparison is
like-for-like: both are back-to-back-series bands, and both series ran
their rungs in the same staged-dir order (alphabetical:
large → medium → small), putting the large rung at the same series
position in each engine's run.

## Top hotspots (reference core, large rung; % of profiled reason time)

Banked in [profile-phase4.md](../perf/profile-phase4.md). Grounding's
clause-satisfaction walk holds **93.8% cumulative** (edge-clause arm
65.8%); by self time:

| function | self % | calls |
|---|---|---|
| `World.is_satisfied` | 19.5 | 40.7M |
| `Label.__eq__` | 14.6 | 41.4M |
| `Label.__hash__` | 13.9 | 43.4M |
| `Interval.__contains__` | 12.0 | 40.5M |

plus their induced primitives (`hash`, `isinstance`, `Label.__str__`,
`get_value`, `lower`/`upper`) at 2.6–3.2% each — the grounding chain and
its value-type primitives together carry ≈ 96% of self time. Call counts
tie 1:1 to the source (one `__str__` per `__hash__`; one
`get_value` + `isinstance` per `__eq__`), so the attribution is
structural. Medium shows the same hot set in the same order
(scale-stable). Oracle decomposition: ≈ 1.38 s import + ≈ 1.9 s setup
(both near scale-invariant) + an ≈ 3.0 s in-reason per-call floor
(reason() never measured below 2.922 s on any rung, including the rung
whose whole workload the rewrite finishes in 4 ms) — session 26's
screened "~2.7 s" refines to ≈ 3.0 s confirmed.

## Drill gap fixes

- `scripts/bench-ladder <engine> <tag> [repeats]` — the staging idiom as
  a one-liner (scratch-dir staging + single-invocation series); both
  baselines docs now carry it in their Reproduction blocks, covering both
  engines.
- `results-phase4-profile/` added to `.gitignore` under the existing
  phase-4 rebuildable-artifacts convention.

## Evidence and reproduction

```
uv run pytest -m "not e2e"                # 288 passed, 4 deselected
scripts/bench-ladder scripts/rewrite-python rewrite-baselines-2026-07-12 7
PYTHONHASHSEED=0 scripts/rewrite-python -m harness.profile \
  --case harness/cases/perf-ladder-medium.json \
  --out-dir results-phase4-profile/rewrite-2026-07-12 --top 25
PYTHONHASHSEED=0 scripts/rewrite-python -m harness.profile \
  --case harness/cases/perf-ladder-large.json \
  --out-dir results-phase4-profile/rewrite-2026-07-12 --top 25
```

No e2e runs: this packet adds no harness cases and touches none; ladder
equivalence was verified twice in session 26 and is not re-claimed here.

## Commits

- `c774312` — rewrite baselines + `scripts/bench-ladder` + oracle-doc
  reproduction one-liner.
- `d211c40` — `harness/profile.py` + 6 fast-tier tests +
  `results-phase4-profile/` gitignore.
- `51f33e7` — `docs/perf/profile-phase4.md`.
- (this commit) — author report.

## Deviations

- **Series-order note (transparency, not a defect):** the oracle's
  banked series and the rewrite's both ran all three rungs in one
  staged-dir invocation, which sorts cases alphabetically
  (large → medium → small), so the large rung leads both series and the
  thermal-drift position is comparable across engines.
- **cProfile overhead is large (~4×)** on this per-call-dense pure-Python
  code — expected, measured, and quoted beside every profile artifact;
  no profiled number is used as a wall-clock claim anywhere.
- No other deviations from the packet; no dependency changes; oracle tree
  untouched (stage decomposition reused from banked artifacts).
