# Session 26 — Phase 4 opens: the AC-4 ladder is committed and the oracle baselines are banked

Date: 2026-07-12 (session started 2026-07-11)

## Verdict

**The AC-4 workload ladder exists and the oracle's baselines are the
campaign's numbers of record.** Three ladder rungs are committed as
harness cases (performance and equivalence share inputs — all three PASS
oracle-vs-rewrite), the B16 hazard is structural in the design (bounded
timesteps everywhere, no `fp_version` rung), the stdlib benchmark runner
is committed with its pure layer tested, and the oracle's cold-start,
per-rung throughput, and peak memory are banked with 7-repeat medians,
noise bands, and the cache-build context number separated from the bar.
Fast tier **282**; independent review approved-with-fixes, spot-checks
inside or explainably adjacent to the banked bands.

## Evidence

- **Ladder rationale:** [docs/perf/ladder.md](../perf/ladder.md) —
  small 50n/150e/10t · medium 400n/2400e/40t · large 1000n/6000e/75t
  with a join rule; seeded, reproducible fixture generator
  (`tools/gen_perf_fixtures.py`, regenerates byte-identical).
- **Baselines of record:**
  [docs/perf/oracle-baselines.md](../perf/oracle-baselines.md) —
  oracle on M2 Max / macOS 26.3 / oracle-env Python 3.10.20, numba
  cache warm, n=7 medians (band): small reason 2.992 s (2.922–3.053),
  293.4 MiB · medium 3.611 s (3.529–3.625), 303.7 MiB · large
  17.977 s (17.178–18.524, monotonic thermal drift characterized),
  328.6 MiB · cold-start 4.376 s (4.267–4.477) · cache-build context
  157.0 s / 1662 MiB (context, never the comparison bar).
- **Author report:**
  [docs/reviews/2026-07-11-phase4-ladder-baselines-author.md](../reviews/2026-07-11-phase4-ladder-baselines-author.md).
- **Independent review (approved-with-fixes):**
  [docs/reviews/2026-07-12-phase4-ladder-baselines-review.md](../reviews/2026-07-12-phase4-ladder-baselines-review.md)
  — design/runner/numbers verified; one control repeat per spot-checked
  claim landed inside or ~4–5% below the banked bands, matching the
  documented lone-run-vs-series effect; cache-warm precondition and
  machine identity confirmed live; three fixes (bench.py foreign-cwd
  path resolution, a ladder-doc formula, a baselines-doc note), none
  touching a banked number.
- **Screen-level observation (single runs, NOT a confirmed claim):**
  the pure-Python reference core ran *faster* than the oracle on the
  small and medium rungs (~0.004 s / ~0.61 s vs ~3 s) and at parity on
  large (17.6 vs 17.1 s) — the oracle carries a ~2.7 s fixed per-call
  overhead. The rewrite-side confirmed baseline run is Phase-4 work
  still ahead; if it holds, the AC-4 parity floor may already be met by
  the reference core on this ladder.
- **Tests:** `uv run pytest -m "not e2e"` → 282 passed, 4 deselected;
  ladder equivalence `harness.run` → ALL PASS (3 cases), twice
  (author + review, separate results dirs, both gitignored).

## Committed

- `8c43efc` — perf: the three ladder cases + seeded fixtures + rationale.
- `f81855d` — perf: harness/bench.py + 11 fast-tier tests.
- `fff0eff` — docs: oracle baselines banked as numbers of record.
- `7a5d127` — docs: session-26 author report.
- `8f4213b` — review fixes: bench.py path resolution; ladder/baselines doc corrections.
- `db5fb55` — docs: session-26 review report.
- (this commit) — ledger: session 26 banked; campaign log continued.

## NEXT

**Profile the oracle and the reference core on the committed ladder to
find where time actually goes** (charter phase 4: measured, not
assumed) — preceded in the same session by the owed **AC-7 mid-campaign
pickup drill**: a cold Opus subagent (explicit `model: 'opus'`), given
only the committed repo, states the campaign's state and executes this
NEXT far enough to prove it's executable; any gap between its reading
and the intended state is a defect in the committed state — fixed and
re-drilled before the campaign proceeds; drill and result banked.
Profiling shape: rewrite-side confirmed baselines through
`harness/bench.py` first (same screen-then-confirm discipline, same
rungs — this also tests the screen-level faster-than-oracle
observation), then per-phase profiles (cProfile on the reference core;
the oracle's own hot loop is jitted, so its profile is per-stage
wall-clock, not per-function) on the medium and large rungs. Output: a
committed profile report naming the hottest kernels — the input to the
acceleration-spike candidates (each spike is a later session; the
execution-layer commitment itself is an operator ask).

## Deviations

- None from the session shape or methodology.

## Asks queued

- None this session. (Ahead: acceleration-spike candidates will each
  ride an ask when proposed; the execution-layer commitment is
  operator-signed per charter.)

## Divergences

- None opened or updated; the ladder cases surfaced no divergence
  (3/3 PASS both runs).

## Idea seeds

- The oracle's ~2.7 s fixed per-call overhead (screened) as a
  first-class cold-start/latency story for the rewrite's consumer
  pitch — quantify properly with the rewrite-side confirmed baselines.
- Carried: registrand-behavior packet (L3/L4 arms); edge-rule
  head-function forms; sweep durability; `probe_s` timing; multi-rule
  prange characterization; pyyaml-version parity tripwire;
  artifact-schema `inputs` echo; `raise_errors=False` warn-skip arms.
