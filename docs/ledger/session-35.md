<!-- doccode: pyreason-rewrite-docs-ledger-session-35 -->
# Session 35 — the lab thread lands: Pokec replicated at scale, the paper verified, the regression bisected to its lines

Date: 2026-07-12/13 (operator-driven interactive session under the lab-compute waiver)

## Verdict

**The campaign's first lab-compute thread is complete and every number is final**
([the report of record](../perf/pokec-scaling-report.md), status FINAL). (1) The
operator waived the no-lab-compute rule for scaling experiments —
[banked, scoped, revocable](lab-compute-waiver.md) — and `sanders.syr.edu` was
bootstrapped with every install [logged](../lab/sanders-install-log.md). (2) The
paper's §4.2 Pokec experiment was reconstructed from the public SNAP dataset
(disclosed model; §4.1's Honda data is not public — spiked, synthetic-twin fallback
named) and **equivalence holds on real data at scale: 10k and 25k rungs ALL PASS
oracle-vs-rewrite, row-identical counts**, the 25k anchor at **123×** rewrite advantage
(27,320 s vs 221.9 s) — the campaign's largest proven-equivalent case. (3) **The
paper's headline runtime claim is verified in substance on the paper-era engine**
(pyreason 1.2.4: full 1.6M-node Pokec in 60.6–61.1 min, n=2, 0.83% band, deterministic,
vs the claimed 42 min) and is unreachable on the pinned engine. (4) The gap is a
**bisected upstream regression** (~195× vs paper era at 10k): ×18.4 at PR #43's
global-grounder rework (v3.0.0), ÷4.4 recovered by v3.1.0, then **×46.7 at v3.3.0 —
whose dominant ×9.4 is forced by a hunk-revert run to upstream's fix of the operator's
own BUG-138** (threshold checking semantically broken until 2026-02; the fix is right,
its implementation re-derives qualified groundings in the hot loop), ×~4.9 residual
unattributed at hunk level. The rewrite ships the corrected semantics at ~1.8× the
speed of the last incorrect-fast release. (5) Protocol integrity: `--parallel N` landed
validated (n=7 seq vs par medians 26.806/26.796 s), the Linux RSS seam landed tested,
the 200k band closed the full-scale projection at ~21 days (exponent 2.09) and the
operator's no-full-scale-rewrite decision is recorded in the report. Fast tier **328**.

## Evidence

- **Report of record:** [docs/perf/pokec-scaling-report.md](../perf/pokec-scaling-report.md)
  — reconstruction, equivalence tables, all bands, the paper-verification block, the
  dated regression timeline with the revert-run decomposition, operator decisions.
- **Waiver + install log:** [lab-compute-waiver.md](lab-compute-waiver.md),
  [docs/lab/sanders-install-log.md](../lab/sanders-install-log.md) (complete, incl.
  the bisection envs and the campaign-authored drivers).
- **Artifacts:** on sanders under `~crpayne/pyreason-campaign/` (results dirs,
  paper-era + discrim logs); key sets mirrored to the laptop's gitignored
  `results-pokec-sanders/`. Equivalence runs carry the standard four-capture markers.
- **Execution-layer tie-in:** the memo's
  [Pokec addendum](../perf/execution-layer-options.md) (evidence strengthens the
  signed Option B; neighborhood grounding named as zero-dependency headroom).
- **Tests:** fast tier 328 passed (bench parallel/Linux seams, Pokec generator pure
  layer); sanders-side fast tier green minus the 3 substrate-bound preflight tests
  (expected off-laptop).

## Committed (this thread)

- `cf20e71` — waiver banked; CLAUDE.md amended; install log opened.
- `bae3a5f` — Pokec rig: generator, cases, bench Linux seam.
- `1d72d23` — bench `--parallel N` + tests.
- `03862f4` — 10k oracle band corrected to raw artifacts (session-33 review fix).
- `9c40221` — report v3: 200k band, ~21-day projection, parallel validation.
- `0f5d788` — the bisection + revert-run attribution; install log rows.
- `5be196c` — the full dated timeline, paper release to pin.
- (this commit) — report FINAL + 25k verdict; session 35 banked; campaign log.

## NEXT

**Externally gated, as before:** (1) the repo-publication parameters (carried from
session 33); (2) **new operator forks from this thread** — whether to take the
upstream-contribution path (the efficient BUG-138 fix + the §4.2-shaped benchmark
suggestion + the regression report; post-window per charter) and whether to schedule
the neighborhood-grounding optimization thread (post-decision work, Option-B+
territory). The sanders environment stays as logged under the standing waiver; say the
word to tear it down instead. A fresh session picks up with `/campaign` when a gate
opens; the resume point is this file.

## Deviations

- Ran as an operator-driven interactive thread (not `/campaign`-orchestrated); the
  operator directed protocol amendments in-session (n=7-parallel repeats, n=1
  sequential references), all recorded in the report.
- Three VPN drops mid-thread (environment, not work): tmux + per-case durability meant
  zero loss; the monitor resumed silently each time.

## Asks queued

- Publication parameters (carried, blocking that thread).
- Upstream path and neighborhood-grounding scheduling (new, non-blocking — operator
  forks stated in NEXT).

## Divergences

- None opened; 10k and 25k equivalence PASS (four records total, all adjudicated).

## Idea seeds

- Neighborhood-scoped grounding as a zero-dependency rewrite optimization class
  (banked in the report + memo addendum).
- Upstream: an efficient BUG-138 fix (filter once, reuse) and a §4.2-shaped perf
  benchmark in CI — the compounding went unnoticed for lack of one.
- The instance-vs-type pet-node bracket as a general technique: when a paper's setup
  is unpublished, bracket it with structural extremes instead of guessing.
