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
| 10k | 121,716 | **26.7–26.9 s** (265 MB) | bench n=2: **2589–2611 s**; captures 2620/2701 (~880 MB) | 2677 (1.6 GB, **128% CPU**) | **~97×** |
| 25k | 406,355 | (equivalence run in flight) | (equivalence run in flight) | — | — |
| 50k | 884,238 | **1087–1093 s** = 18.2 min (1.63 GB) | — (projected ~1.4 d) | — | — |
| 200k | 4,009,047 | **25,557–25,679 s** = 7.1 h (n=2, spread 0.47%, 7.2 GB) | — (out of reach) | — | — |
| full | 30,622,564 | **projected ~21 days — not run (operator decision)** | projected years — not runnable | no better (see below) | — |

Rewrite bands are ≤0.5% of median at every rung — extremely tight.

### Scaling shape

Three-point fit (rewrite): 10k→50k gives exponent ~1.87 in friend edges; the
density-matched 50k→200k step steepens it to **~2.09** (time ×23.5 for edges ×4.53),
which is the **projection of record**: full-scale ≈ 25.6 ks × 7.64^2.09 ≈ **21 days per
repeat** — decisively superlinear for both engines (the oracle's 10k time is ~97× the
rewrite's on the identical case, so its curve can only sit higher). Mechanism: the
relevance-active set explodes per timestep on dense subgraphs (see the equivalence
counts). The paper's "sub-linear scaling" claim (§1, §4) fails directionally on this
workload on both modern engines — including the one we didn't write.

### Parallel-repeat validation (the operator's contamination check)

Rewrite 10k, n=7 sequential vs n=7 `--parallel 7` on the idle box: medians
**26.806 s vs 26.796 s**, bands 26.681–26.904 vs 26.755–26.937 (spreads 0.223 s /
0.183 s) — statistically indistinguishable, 7× wall-clock saved (29 s vs 3 m 20 s).
The `--parallel` mode is validated as uncontaminated at this working-set size; reports
stamp `parallel` either way.

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

**The full-scale verification run (1.2.4, complete Pokec, both rules, timesteps=8):**

| | Paper (2023, 96 vCPU EC2) | Measured (1.2.4, sanders, one core) |
|---|---|---|
| reason | 42 min | **60.6–61.1 min** (3,633.7 / 3,664.0 s, n=2, spread 0.83%) |
| setup (31M-edge graph load) | not separated | 16.4 min |
| peak RSS | 58.36 GB | 185 GB |
| scaling in edges (10k→200k→full) | "sub-linear" | **linear, x^0.98** |
| CPU | "supports CPU parallelism" | 100% of one core |

**Verification outcome: the paper's runtime claim is verified in substance on the
paper-era engine** — same order, same shape, on one core versus their 96 vCPUs
(consistent with the engine never really using more than one) — **and is not
reproducible on the pinned engine, where the gap is an upstream regression that the
release bisection below decomposes and (for its dominant step) forces to specific
lines.**

### The regression bisection (2026-07-13; revises session 33's single-cliff attribution)

Every PyPI release bracketing the cliffs, identical 10k inputs, one box — the full
timeline from the paper's release to the pin:

| Date | Release | reason (10k) | Step | What happened |
|---|---|---|---|---|
| 2023-03 | **1.2.4** (paper era) | **13.4 s** | baseline | Neighborhood-scoped grounder, O(E)/timestep — the engine the 42-min claim describes (full-scale verified at ~61 min above). Threshold checking semantically broken this whole era (BUG-138). |
| →2024-06 | 2.3.0 | 11.1 s | ~1.2× faster | Last of the fast class; rows 7,648 (era semantics). |
| 2024-12 | 3.0.0 | 203.8 s | **×18.4** | **PR #43**: general FOL grounder replaces the neighborhood grounder (session 33's candidate). Generality bought, O(E) lost. |
| 2025-08 | 3.1.0 | 46.8 s | **÷4.4 recovered** | Post-rework grounder optimization; rows now 8,006 (modern semantics). |
| 2025-11 | 3.2.0 | 46.9 s | flat | — |
| 2026-02 | **3.3.0** | **2,189 s** | **×46.7 — the dominant cliff** | Decomposed below: ×9.4 forced to the BUG-138 fix, ×~4.9 residual. |
| 2026-05 | 3.6.0 (**the pin**) | 2,589–2,701 s | ×1.19 drift | Where the campaign's oracle sits. |

Product: ≈234× vs 2.3.0, ≈195× vs the paper-era baseline. Two of the steps bought real
things — PR #43 bought the rule generality this campaign's corpus exercises; the
BUG-138 fix bought correct threshold semantics (broken for the paper's entire era) —
and no §4.2-shaped benchmark was in place to notice the compounding.

**The dominant cliff decomposes, with the majority forced by a revert-run.** The 3.3.0
window contains upstream commit `882f71d` "Fix BUG-138: Correct threshold checking by
filtering qualified groundings" — **BUG-138 is the operator's own clean-room catalogue
entry** (BUG_LOG_2 §BUG-138, severity CRITICAL: `check_all_clause_satisfaction` passed
the same grounding twice, defeating threshold checking). The fix is semantically right
and re-derives per-clause qualified groundings on every satisfaction check — in the hot
loop. Reverting exactly those two hunks in a scratch copy of 3.3.0 drops 2,189 s →
232 s: **9.4× forced to the BUG-138 fix as implemented** (output rows identical on this
workload either way — the threshold semantics don't bite here). The residual ~4.9×
(232 s vs 3.2.0's 46.9 s) lies elsewhere in the 3.3.0 window and is left unattributed
at hunk level (the interval float32→float64 commit was inspected and is implausible —
rare code path). So the pinned engine's ~55× gap vs 3.2.0 ≈ a correctness fix paid at
9.4× runtime, times an unattributed 4.9×, atop a net ~4× from the grounder generality
trade — and the rewrite (pin-equivalent semantics, 26.7 s) delivers the **corrected**
threshold semantics at ~1.8× the speed of the last **incorrect** fast release. An
efficient implementation of the BUG-138 fix (filter once, reuse) looks bounded and
upstream-contributable (post-window scope).

**The result-count divergence is reconstruction density, bracketed by experiment.**
Our rebuild reaches 1,158,131 relevance rows at t=8 (~71% of users) vs the paper's
~53k (~3.3%). A 10k variant with *instance-scoped* pet nodes (rule 2 structurally
inert) freezes at t=1 with exactly the seeds' one-hop halo — the paper's stall shape —
and the paper's own arithmetic sits just above that extreme (2,693 fully-relevant hubs
× ~19 friends ≈ 50,608, their exact partial count). So the paper's effective shared-pet
layer was far sparser than our stem-based rebuild; the engines agree with each other on
any given reconstruction (10k equivalence PASS; 1.2.4 within ~4.5% on ours). The memory
gap (185 vs 58 GB) follows the same cause: a saturating diffusion carries ~20× more
active atoms. Both engines' superlinear scaling numbers above are therefore claims
about *our* (denser, disclosed) reconstruction.

## Operator decisions of record (2026-07-12, approved in session)

- **No full-scale rewrite run** — the fitted scaling law is the characterization; a
  lone full-scale dot has no oracle to compare against and costs ~9.5 days.
- **Equivalence-at-scale anchor at the 25k rung** (largest overnight-feasible oracle
  rung) — queued to run after the 200k band closes.
- **Parallel-mode validation** of `--parallel` at 10k (n=7 sequential vs n=7 parallel)
  — queued in the same overnight batch.
- The paper-era full-scale verification runs n=2 (repeat in flight) for a minimal band.
- Oracle 10k clean protocol band: **reason median 2,600 s, spread 22 s (0.85%)** —
  banked above.

## Pending (v3, tonight/tomorrow morning)

1. The 200k rewrite band (n=2) → density-matched full-scale projection of record.
2. The paper-era full repeat (band).
3. The overnight results: parallel validation + the 25k equivalence verdict.

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
