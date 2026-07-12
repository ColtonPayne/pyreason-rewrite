# Session 34 — the window-close drill passes after self-repair; every criterion closed or externally gated (verdict-of-record)

Date: 2026-07-12

## Verdict

**The AC-7 window-close pickup drill is banked as PASSED-after-repair,
and this entry is the window-close verdict-of-record.** Drill 1 (cold
Opus, committed repo only) reconstructed the campaign's state correctly
on every substantive point and proved the resume path live (preflight
10/10, fast tier 330, oracle gate, the harness spine e2e) — and
surfaced three committed-state defects: a README front door still
claiming the campaign hadn't started, an oracle-env rebuild recipe
naming the wrong interpreter (3.12 vs the 3.10.20 of record), and an
undocumented 20-minute e2e runtime. All three fixed at green; **the
re-drill (a second cold Opus agent) reports "no substantive gaps"** and
independently confirms front door ≡ ledger, recipe ≡ environment,
runtime warned.

**State of every criterion at the window's close:**

| criterion | state | evidence of record |
|---|---|---|
| AC-0 substrate | green, standing | preflight 10/10 (re-proven cold twice today) |
| AC-1 inventory | closed | docs/surface.md, 52 rows, AST-gated |
| AC-2 harness | closed | the spine + durability (s31); self-proved oracle-vs-oracle |
| AC-3 equivalence | **52/52 `equivalent`** | session-32 sweep: 116/116, one clean invocation |
| AC-4 performance | floor cleared, all rungs, disjoint bands | ladder baselines; Pokec ~101× real-scale |
| AC-5 maintainability | closed 5/5 | session-33 audit + review |
| AC-6 divergences | 3 records, all adjudicated | docs/divergences/DIV-0001..3 |
| AC-7 pickup contract | drill + re-drill PASSED | docs/reviews/2026-07-12-ac7-window-drill.md |

## Evidence

- **Drill report (both drills, the fixes, the re-drill result):**
  [docs/reviews/2026-07-12-ac7-window-drill.md](../reviews/2026-07-12-ac7-window-drill.md)
- **Tests:** fast tier 330 passed / 6 deselected at the fix commit and
  in both cold drills; oracle pin byte-clean throughout.

## Committed

- `652863b` — drill report + the three committed-state fixes (README
  status now defers to the ledger; oracle_smoke recipe pinned to 3.10
  with the ADR pointer; e2e runtime warning).
- (this commit) — ledger: session 34 banked; campaign log continued;
  re-drill result appended to the drill report.

## NEXT

**Nothing unblocked remains in-repo; the open threads are externally
gated.** In order: (1) **the repo-publication parameters** (operator:
host/visibility, name, whether `results-*` dirs ship — asks stated in
session 33); (2) **the lab-box results** under the standing waiver: the
sanders overnight batch (200k band, 25k equivalence anchor,
parallel-mode validation) folds into Pokec report v3, and the queued
v2.3.0-vs-v3.0.0 discriminating run confirms or revises the
grounding-rework attribution. A fresh session picks up with `/campaign`
when either gate opens; the resume point is this file.

## Deviations

- The drill fixes were applied by the orchestrator directly (three
  small doc corrections) rather than through the two-agent shape; the
  re-drill is their independent verification, per AC-7.4's own
  fix-and-re-drill loop.

## Asks queued

- **Repo publication** (carried from session 33, blocking that thread
  only): host/visibility (recommendation private-first), name (default
  `pyreason-rewrite`), raw results dirs in or out (recommendation out).

## Divergences

- None opened or updated.

## Friction

- Carried: the uncommitted operator-side edit to
  docs/perf/pokec-scaling-report.md remains in the working tree by
  design (both drills recognized it from the ledger note and left it).

## Idea seeds

- The drill's self-repair loop (gap → fix → cold re-drill) worked
  end-to-end in one session; worth carrying as the standing pattern for
  any future stale-front-door class of defect.
