<!-- doccode: pyreason-rewrite-docs-adr-0004 -->
# ADR 0004 — Execution layer: the pure-Python core with the session-28 optimizations ships

- status: accepted (operator-signed)
- date: 2026-07-12
- session: 33 (Phase 4, execution-layer closure)

## Context

The charter commits the execution-layer choice to the operator (Methodology,
phase 4; AC-4's floor verdict lands with this choice). The decision memo
([docs/perf/execution-layer-options.md](../perf/execution-layer-options.md),
session 28) put three options in front of the operator with measured numbers —
all n = 7 medians with (min…max) bands from the committed baseline reports
([rewrite-baselines.md](../perf/rewrite-baselines.md),
[oracle-baselines.md](../perf/oracle-baselines.md)); deltas inside the noise
band are ties. Cited, not re-measured:

| rung, reason() | rewrite post-spike (B) | rewrite pre-spike (A, session 27) | oracle |
|---|---|---|---|
| small | 0.0028 s (0.0028…0.0028) | 0.0041 s | 2.992 s (2.922…3.053) |
| medium | 0.151 s (0.151…0.153) | 0.655 s | 3.611 s (3.529…3.625) |
| large | 1.226 s (1.224…1.240) | 18.792 s (18.124…18.940) | 17.977 s (17.178…18.524) |

Cold-start (small rung, fresh process to first `reason()` return): rewrite
0.067 s vs oracle 4.376 s (~65×, disjoint bands). Large-rung peak RSS:
67.1 MiB vs 328.6 MiB (~4.9×). Every band-clearing claim above traces to the
session-27 baseline reports and the session-28 spike review's independent
re-measurement.

- **Option A** — ship the session-27 pre-spike core: strictly dominated by B
  (the spike changed no observable behavior, added no dependency, ~40 lines).
- **Option B** — A plus the session-28 zero-dependency optimizations (commits
  `c56d238`, `c218f45`, `958523a`, `ca600a3`): large-rung 14.7× vs the oracle
  band, medium 4.3×, small 1.47×, all bands disjoint.
- **Option C** — a dependency-bearing acceleration spike (numpy / numba behind
  a kernel seam / C-level compilation). The post-spike large-rung profile is
  flat (grounding subtree down to 25.4% cumulative; a perfect elimination buys
  ≤ 1.34×), so every C sub-option spends a dependency, a version ceiling, or a
  second implementation surface against a bounded win.

The memo's Pokec addendum ([pokec-scaling-report.md](../perf/pokec-scaling-report.md))
added the real-scale point: on the 10k rung of a real diffusion workload the
rewrite is **~101× faster than the pinned oracle on identical inputs** (26.7 s
vs 2,620–2,701 s, equivalence PASS), and the paper-era engine's
neighborhood-scoped grounding (measured scaling exponent 0.98 vs the modern
global grounder's ~1.87) names a further *algorithmic, zero-dependency*
headroom class — bounding Option C's appeal from the other side.

## Decision

**Option B is the campaign's execution layer — operator-signed 2026-07-12.**
The shipped engine is the pure-Python core (`src/pyreason/`, ADR 0001–0003)
with the session-28 optimization commits. The C-track closes unopened: no
dependency ask granted, no kernel seam built, no spike session run.

### Evidence of record

- **Baselines:** session 27 (ladder + cold-start + RSS,
  [2026-07-11-phase4-ladder-baselines-author.md](../reviews/2026-07-11-phase4-ladder-baselines-author.md),
  reviewed) and session 28 (the spike and its post-spike bands,
  [2026-07-12-phase4-spike-author.md](../reviews/2026-07-12-phase4-spike-author.md),
  independently re-measured in
  [the review](../reviews/2026-07-12-phase4-spike-review.md)).
- **Equivalence:** the session-32 Phase-4 boundary sweep — the full 116-case
  corpus, oracle-vs-rewrite, **116/116 PASS in one clean invocation**
  (`resumed: false`), zero divergences, banked over exactly this tree state
  ([author](../reviews/2026-07-12-phase4-boundary-sweep-author.md),
  [review, approved zero fixes](../reviews/2026-07-12-phase4-boundary-sweep-review.md)).
  With B signed, that sweep stands as the verdict-of-record of the chosen
  layer; no re-sweep is owed (an A or C choice would have changed the tree).
- **Real-scale:** the Pokec replication's ~101× point and its equivalence
  PASS, above.

### AC-5.5 — the version-headroom statement

The shipped core is pure Python end to end:

- **`requires-python = ">=3.11"` with no stated ceiling**
  (`pyproject.toml`) — no upper bound exists anywhere in the tree.
- **No JIT, no compiled extension, no build step.** The package has no
  `[build-system]` table (ADR 0001), ships no wheel-compiled code, and
  `src/pyreason/` imports no acceleration machinery (mechanized check:
  `grep -rniE "import (numba|numpy|cython|cffi)|from (numba|numpy|cython|cffi)" src/pyreason/`
  → 0 matches; likewise `ctypes`).
- **The runtime dependency surface is two pure-Python libraries and nothing
  else** (`pyproject.toml` `dependencies`): `networkx>=3.6.1` — the pinned
  public API's graph input type, a dependency the oracle also carries — and
  `pyyaml>=6.0.3` — the pinned YAML rule/IPL file-loader parity. Neither pins
  an interpreter version; neither is a JIT or compiled-kernel dependency. (The
  memo's "zero dependencies" shorthand meant *zero added by the spike* and
  *zero version-sensitive*; this ADR states the exact surface.)
- **Evidence the headroom is real, not asserted:** the pinned oracle requires
  `numba==0.59.1` (`oracle/pyreason/requirements.txt:4`), which is why the
  oracle lives in a dedicated Python 3.10.20 environment (`oracle-env/`) —
  the interpreter-ceiling cost AC-5.5 names. The rewrite ran the entire
  116-case equivalence corpus and the full fast tier as engine B on **Python
  3.13.11** (the campaign venv), three minor versions past the oracle
  environment, with no version-conditional code anywhere in `src/pyreason/`.

### The named post-decision headroom seed (deferred)

**Neighborhood-scoped grounding for one-hop-anchored rules** — the paper-era
mechanism the Pokec report measured at exponent 0.98 (O(E) per timestep)
against the modern global grounder's ~1.87. It is the next order of magnitude
on diffusion workloads *without leaving pure Python*. Explicitly deferred, not
started: any grounding-scope change touches the reasoning core's observable
behavior surface, so it carries a full equivalence-proof burden — the
116-case corpus plus a diffusion-shaped case family oracle-vs-rewrite, and
adjudication of any divergence — before adoption. Nothing in this decision
depends on it landing.

## Consequences

- **AC-5.1 stays one-engine by construction.** The single core is the only
  execution path; no acceleration seam exists, so the accelerated-vs-fallback
  parity case family remains **vacuously satisfied** — per the charter it
  becomes a live obligation only with the first acceleration seam, and
  building it speculatively is forbidden dead scaffolding.
- **No compile floor.** The rewrite keeps its cold-start class (no kernel
  cache to build, warm, or carry — the oracle pays ≈ 3.0 s per fresh-process
  `reason()` plus ≈ 1.4 s import for its JIT floor).
- The boundary sweep of record binds to this tree; any future engine change
  re-earns its evidence through the harness per the standing discipline.
- The deferred grounding-scope seed is recorded here and in the Pokec report;
  picking it up is a new decision with its own evidence bar, not a leftover
  obligation of this one.
