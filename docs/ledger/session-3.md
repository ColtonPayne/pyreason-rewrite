# Session 3 — the seed corpus grows: convergence, persistence, inconsistency, malformed DSL

Date: 2026-07-06 (same sitting as sessions 0–2)

## Verdict

The corpus grew 1 → 10 cases along session 2's NEXT — the three `reason()` convergence
modes under `timesteps=-1`, a `persistent` on/off pair, an IPL inconsistency pair on the
resolve and override paths, and the first malformed tranches of both text DSLs on a new
`expect_raise` probe kind — oracle-vs-oracle ALL PASS on all 10 (repeats green), the
capture extension survived a focused adversarial review (1 High + 3 Medium confirmed and
fixed), and the board stands at 16/52 rows `cased`.

## Evidence

- **Capture extension** (`harness/capture.py`): an `expect_raise` probe kind constructs
  `Rule`/`Fact` and records the outcome as data — module-qualified exception type +
  message on a raise, a parse fingerprint on acceptance (the review's High: a bare
  "accepted" would let two engines parse the same text differently and still compare
  equal). `inputs.reason` is now optional (guarded: interpretation-consuming probes still
  require it) and `inputs.ipl` feeds `add_inconsistent_predicate`.
- **Review gate:** [docs/reviews/2026-07-06-expect-raise.md](../reviews/2026-07-06-expect-raise.md)
  (one focused Opus reviewer — proportionate to a two-file spine extension; the raw file
  is committed beside it). All fixes regression-tested; residuals down-rated or deferred
  with recorded rationale, including the named future fork: cross-engine exception-message
  comparison policy is decided per-case when oracle-vs-rewrite runs exist.
- **The run:** `uv run python -m harness.run --cases harness/cases --engine-a
  oracle-env/bin/python` → ALL PASS, 10 cases × 4 fresh-process captures each,
  `PYTHONHASHSEED=0`; verdict-of-record banked as
  [session-3-oracle-vs-oracle.json](session-3-oracle-vs-oracle.json).
- **Termination screened before banking:** the `timesteps=-1` cases converge because the
  friends graph is acyclic along the diffusion direction — `conv-perfect` returns
  `get_time()=5`, the two delta modes 4. The first `delta_bound` capture paid a ~36.5s
  numba specialization compile (float threshold), warm thereafter — an AC-4-relevant
  cold-start observation.
- **Screening caught two case-authoring faults before they banked wrong:** the
  persistent pair's filter/trace probes cannot see per-timestep resets (resets are not
  trace events) — the `interpretation_dict` probe, whose `get_dict` branches on
  `persistent`, carries the contrast (t=1: on holds `popular(Mary)=[1,1]`, off shows the
  reset); and the pin's predicate regex accepts `-`/`.` (as the analysis corpus records),
  so the hyphenated shape banked as the `bound-predicate-charset` acceptance probe with
  `$` as the badchar representative.
- **Malformed tranches:** 13 rule-text probes (12 raise at the pin, the multi-digit
  delta silently consumed as `delta_t=10` — pinned by the fingerprint) and 16 fact-text
  probes (15 raise, 1 accepted boundary).
- **Gates:** fast tier 42 passed; links gate green on every commit; preflight 10/10 at
  session start.
- **Board:** `docs/surface.md` — 16 rows `cased` (persistent, inconsistency_check, and
  add_inconsistent_predicate flipped this session), 36 `uncovered`; `equivalent` still
  0/52 — no rewrite exists yet, `cased` marks harness coverage only.

## Committed

- `3a1d32b` — harness: expect_raise probe kind, optional reason, ipl input.
- `cc1e03d` — harness: the nine new cases.
- `bd4ebc0` — docs: board flips + the banked run.
- `5162857` — harness: the review's confirmed findings fixed; report + raw review.
- (this commit) — ledger: session 3 banked.

## NEXT

Case `reason()`'s resume semantics and the reset family: extend capture with a minimal
multi-step step list (a case declares an ordered sequence of `reason` / `reset` /
`reset_rules` / `reset_settings` steps with probes between them — today's single
`reason` block stays as the one-step form), then author cases from `docs/surface.md`
for `again-resume`, `restart-true-resume` vs `restart-false-continue`, and the
`fn:reset` / `fn:reset_rules` no-program vs with-program classes — run oracle-vs-oracle,
flip the covered rows, bank the run.

## Deviations

- The charter's review gate names complete features for the ≥2-reviewer form; the
  capture extension is a contained spine change, so it got the umbrella's scaled-down
  single-focused-reviewer form, with the report committed anyway (the spine's
  trustworthiness warrants the paper trail).

## Asks queued

None.

## Idea seeds

- The oracle's numba kernel recompiles per argument-type specialization
  (`convergence_bound_threshold` float vs int cost ~36.5s once) — cold-start for AC-4
  should measure a representative settings spread, not just defaults, and the
  execution-layer ADR should weigh per-specialization compile cost if numba is retained.
- `Interpretation.get_dict` reconstructs bounds from the rule trace (and forward-fills
  under `persistent`) rather than reading world state — an API accessor whose output is
  trace-derived is a redesign smell worth a deliberate contract decision in the rewrite.
