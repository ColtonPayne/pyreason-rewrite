<!-- doccode: pyreason-rewrite-docs-perf-pokec-scaling-report -->
# Pokec scaling report — the paper's §4.2 experiment, oracle vs rewrite on lab compute

**Status: INTERIM (v1)** — 2026-07-12. Screens through 50k banked; the 200k rewrite rung
and the oracle 10k protocol band land tonight and finalize this report. Runs executed on
`sanders.syr.edu` under [the operator's lab-compute waiver](../ledger/lab-compute-waiver.md);
everything installed there is in [the install log](../lab/sanders-install-log.md).

## What was asked

Replicate the PyReason paper's §4.2 Pokec experiment (arXiv:2302.13482) at scale,
oracle-vs-rewrite, using the same performance harness and protocol as the banked ladder
baselines; verify the paper's published results with the pinned oracle either way.
(§4.1's Honda dataset is not public — spiked separately; a synthetic-twin arm is the
fallback there.)

## Reconstruction (disclosed)

- **Dataset**: public SNAP soc-Pokec, verified exact match to the paper's population —
  1,632,803 profiles / 30,622,564 friendship edges (gz integrity + line counts).
- **hasPet augmentation** rebuilt from the profiles' Slovak free-text `pets` column via a
  fixed stem map (`tools/gen_pokec_fixtures.py`): 748,299 hasPet edges over 15 pet-type
  nodes (paper: ~1.01M over 17 — their normalization is unpublished; ours is stricter).
- **Customers**: the paper's proportion (2,308 / 1,632,803), seeded deterministically as
  every k-th sorted pet-owner; the paper's actual 2,308 identities are unpublished, so
  Table 3's exact counts are not reproducible by anyone — convergence shape and magnitude
  are the comparable claims.
- **Rungs** are id-prefix induced subgraphs (10k/50k/200k/full). The 10k/50k rungs are
  early-adopter-dense (12.2 / 17.7 friend edges per user vs the full graph's 18.8);
  **the 200k rung (20.0/user) is nearly density-matched to full scale**, which is what
  makes tonight's 200k point the trustworthy anchor for the full-scale projection.
- Rules are the paper's two relevance rules verbatim; `timesteps=8` (the paper's
  convergence point), explicitly bounded per the ladder's B16 constraint.

## Method

Same rig as the banked baselines: `harness/bench.py` (fresh process per repeat,
import/setup/reason windows, per-child peak RSS, median + noise band), `harness/run.py`
for equivalence (four captures, same-engine repeats, pure judge). Extensions made for
this experiment, all committed and fast-tier-tested: a Linux RSS seam (GNU `time -v` /
child-rusage fallback, `maxrss_source` recorded), a `/proc/cpuinfo` machine-identity
path, and `--parallel N` (operator-requested concurrent repeats, stamped in the report so
a contention-mode run can never masquerade as the banked sequential protocol). Protocol
for the full-scale runs per the operator: **n=1 sequential reference + n=7 parallel** per
engine. Machine: sanders (lcs-pashakar-02), 512-core x86_64, 1.5 TB RAM, Ubuntu 24.04,
otherwise idle. Oracle env mirrors the laptop oracle-env exactly (Python 3.10.20, numba
0.59.1, pyyaml 6.0.3 …); oracle numba cache build on sanders: 201 s, context only.

## Results so far

### Equivalence — PASS at 10k on real data

`perf-pokec-10k` (10,000 users, 121,716 friend + 6,204 hasPet edges, 14 customers):
**ALL PASS** oracle-vs-rewrite — identical digests, same-engine repeats clean, and the
per-timestep relevance counts agree row-for-row:

| t | total | fully [1,1] | partially [0.6,1] |
|---|-------|-------------|--------------------|
| 0 | 14 | 14 | 0 |
| 1 | 186 | 89 | 97 |
| 3 | 5,371 | 2,201 | 3,170 |
| 5 | 7,755 | 3,150 | 4,605 |
| 7 | 7,982 | 3,245 | 4,737 |
| 8 | 8,006 | 3,250 | 4,756 |

Convergence shape matches the paper's (fast early spread, plateau by t≈7); the spread is
proportionally much wider than the paper's full-graph Table 3 (47.5% of the rung vs 3.1%
of the full graph) — the dense early-adopter subgraph at work, disclosed above.

### Performance (reason window, seconds; RSS peak-of-process)

| Rung | friend edges | rewrite | oracle (serial) | oracle (parallel_computing) | ratio |
|------|-------------|---------|-----------------|------------------------------|-------|
| 10k | 121,716 | **26.7 / 26.7** (265 MB) | **2701 / 2620** = 44–45 min (~880 MB) | 2677 (1.6 GB, **128% CPU**) | **~101×** |
| 50k | 884,238 | **1093 / 1087** = 18.2 min (1.63 GB) | — (projected ~31 h) | — | — |
| 200k | 4,009,047 | *running (n=2, ~5 h/repeat)* | — | — | — |
| full | 30,622,564 | *projected ~9.5 days (interim)* | *projected years — not runnable* | no better (see below) | — |

Oracle 10k numbers are the equivalence captures' timing echoes (a1/a2); the clean
n=2 bench band is running and lands in v2. Rewrite bands are ≤0.3% of median — extremely
tight.

### Scaling shape

Two-point fit (10k→50k, rewrite): reason time × **40.8** for edges × 7.27 → exponent
**~1.87 in edges** — decisively superlinear for both engines (the oracle's 10k time is
101× the rewrite's on the identical case, so its curve can only sit higher). Mechanism:
the relevance-active set explodes per timestep on dense subgraphs (see the equivalence
counts). The paper's "sub-linear scaling" claim (§1, §4) fails directionally on this
workload on both engines — including the engine we didn't write.

### The paper-verification finding: the paper is vindicated — upstream regressed ~200×

First, the negative results on the pinned build. The paper: full graph (30.6M edges),
same two rules, 8 timesteps, **42 minutes / 58.36 GB** on 96 vCPUs. The pinned oracle on
sanders (more machine): **45 minutes for 0.4% of that workload** — and
`parallel_computing=True` is wall-clock identical (2,677 s vs 2,701 s) at 2× the memory
with one hot core (128% CPU). The parallel dead-end is structural, not a tuning miss:
the pinned prange is **over rules** (`for i in prange(len(rules))`,
interpretation.py:571) and this experiment has two rules — parallel width 2, on any
hardware.

Then the positive identification. **pyreason 1.2.4** (2023-03-06, the release current at
the paper's publication; installed from PyPI into a logged scratch env) runs the
identical 10k inputs — same graphml fixture, same 14 customer facts, the two rules
mapped to its YAML `neigh_criteria` dialect — in **reason_s = 13.4 s** (1.1 GB RSS),
with result magnitude agreeing (7,648 relevance rows at t=8 vs the modern engines' 8,006
— era-semantics drift ~4.5%, no equivalence claimed). That is a **202× regression**
pin-vs-paper-era on the paper's own workload, and 13.4 s at 122k edges scales
(O(E)-shaped) straight into the neighborhood of the paper's full-graph 42 minutes.

The mechanism is visible in the source history. **1.2.4 grounds rules
neighborhood-scoped**: for each candidate node `n`, clause satisfaction receives only
`neighbors[n]` (`a = neighbors[n]` → `_is_rule_applicable(...)`) — per-rule per-timestep
work is O(Σ degree) = O(E) with jitted constants. **The pinned 2026 main grounds
globally**: the general FOL grounder (`_ground_rule`) builds clause candidate sets over
the whole graph's node/edge lists — the same clause-satisfaction subtree the Phase-4
profile clocked at ~94% of large-rung runtime. Upstream traded the paper's O(E)
neighborhood grounder for first-order generality (arbitrary variable patterns,
`infer_edges`) somewhere between 1.2.4 and today; the published performance describes an
engine that no longer ships.

**Verification outcome: the paper's performance claims are consistent with the
paper-era engine and NOT reproducible on the pinned engine; the gap is an upstream
algorithmic regression we can name, bound (202× at 10k), and date to the
post-1.2.4 grounding rework.** Memory is the one claim tracking on all three engines
(rewrite: 1.63 GB at 50k). A full-scale paper-era verification run (projected ~1 h) is
in progress via a 200k screen.

## Pending (v2, tonight)

1. The 200k rewrite band (n=2) → density-matched full-scale projection.
2. The oracle 10k clean protocol band (n=2).
3. The paper-era 200k screen → full-scale 1.2.4 verification run (projected ~1 h),
   the honest way to satisfy "verify the paper's results".
4. The operator's full-scale fork, with projected wall-clocks per option:
   full-scale rewrite (n=1 sequential + n=7 parallel ≈ one repeat's wall-clock ≈
   projected days), largest-feasible cross-engine equivalence rung, or stop at the
   characterization.

## Idea seeds

- **Neighborhood-scoped grounding as a rewrite optimization class**: for rules whose
  clauses are all target-anchored within one hop (this experiment's shape, and most
  diffusion workloads), grounding can be delta/neighborhood-driven like 1.2.4's —
  collapsing the superlinear term while keeping the single core and zero dependencies.
  Post-campaign / Option-B+ material; equivalence to the pinned semantics would need the
  same case-by-case proof discipline as everything else.
- Upstream-contribution triage: the 202× regression, dated and bounded, is first-class
  material if the campaign ever reports upstream (post-window scope).

## Artifacts

On sanders: `~/pyreason-campaign/pyreason-rewrite/results-pokec-{smoke,screen}/`;
mirrored to the laptop at `results-pokec-sanders/` (gitignored, like all results dirs).
Case generator: `tools/gen_pokec_fixtures.py`; cases `harness/cases/perf-pokec-*.json`;
fixtures regenerate on-box from the SNAP files.
