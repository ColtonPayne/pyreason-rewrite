<!-- doccode: pyreason-rewrite-docs-adr-0003 -->
# ADR 0003 — Engine-variant knobs: one semantics core, a second pinned schedule for fp_version

- status: accepted
- date: 2026-07-07
- session: 19 (Phase 3, knob-arm semantics slice)

## Context

The pinned oracle ships three near-copy ~2400-line engine variants and two
knobs that select among them: `parallel_computing` picks
`interpretation_parallel`, else `fp_version` picks `interpretation_fp`, else
the default `interpretation` runs (program.py:42-47). AC-5 names the
triplication the anti-goal and requires the rewrite to run ONE reasoning-core
implementation for every knob combination, with equivalence judged at the
public API's outputs. The slice-4 packet sharpened the bar: the knobs must
not introduce a second code path through the reasoning loop *beyond what
output equivalence forces*, and any forced branch must be the minimal honest
shape, named explicitly.

What the pin actually emits, from the banked session-15 artifacts and a
normalized body diff of the three variants:

- **parallel_computing is output-invisible on the pinned surface.** The
  parallel variant's entire source diff from the default kernel is the
  decorator flip `@numba.njit(parallel=False -> True)`
  (interpretation_parallel.py:241), and the banked `parallel-computing-on`
  and `parallel-fp-precedence` artifacts digest-equal the default twin on
  every reasoning probe. Its one internal init difference (the specific-label
  stamping defect below) is invisible after t=0 fact application.
- **fp_version is output-DISTINCT.** The banked `fp-version-on` artifact
  differs from the default kernel's on `trace-node` and `nodes-popular`:
  different fp-counter values, different trace event order (fact rows sort
  before the rule rows their pass produced), duplicated atom-trace
  groundings, and a different last-step frame row order — same final bounds.
  No post-processing of the default schedule's trace can honestly produce
  that artifact: the duplications come from per-timestep world dicts feeding
  globally accumulating predicate maps, information the default schedule
  never generates.
- **The variants share their semantics verbatim.** A normalized body diff of
  `interpretation.py` vs `interpretation_fp.py` at the pin shows
  `_ground_rule`, every grounding/threshold/satisfaction helper, `annotate`,
  `check_consistent_*`, and `resolve_inconsistency_*` line-identical (modulo
  the fp variant's dropped `num_ga` plumbing and one try/except wrapper);
  `reason` (the orchestration), the `_add_*`/`_update_*` container
  plumbing, and the init shape differ — and so do two views: the fp
  variant's `get_dict` carries a stale-loop-variable defect that lands every
  edge trace row on the LAST edge in `self.edges`
  (interpretation_fp.py:852-854; reproduced in fp_mode, session-19 review),
  and the fp `query`/`delete_*`/`add_edge` gym-facing methods take the
  t-keyed shape — outside the pinned public surface this campaign compares,
  so not transcribed.
- **The pinned Program stamps specific labels onto only the default class**
  (program.py:34-38, upstream's own `#TODO` marks it), so the fp and
  parallel variants always reason with empty specific-label maps.

## Decision

1. **One semantics core, parametrized by container.** The shared operations
   in `_interpretation.py` — `_ground_rule`, `_apply_fact`,
   `_update_component`, `resolve_inconsistency_*`, `annotate`, `_add_node`,
   `_add_edge(s)` — exist once and take the world dicts they operate on as
   parameters. The default schedule passes the whole component->World maps;
   the fp schedule passes one timestep's map. No semantic body is
   duplicated anywhere.
2. **Two schedule functions.** `reason` (unchanged, ADR 0002) remains the
   default schedule. `reason_fp` transcribes the pinned fp orchestration
   (interpretation_fp.py:251-807): whole-run timestep sweeps per pass,
   conclusions applied between passes with the pass counter, per-timestep
   convergence-counter resets, the delta-0 update-flag clear, pass-level
   perfect convergence, and the `max_t_changes + 1` end time. It is selected
   inside the one `Interpretation` (`fp_mode`), whose init takes the pinned
   fp state shape (t-keyed world dicts, no world seeding, predicate maps
   seeded from the — empty — specific labels) when active.
3. **parallel_computing selects NO schedule.** The dispatch in
   `Program.reason` is `fp_mode = fp_version and not parallel_computing` —
   the exact pinned precedence — and every non-fp combination runs the
   default schedule, because that is what the pin observably emits. The
   knob's readback is untouched settings state.
4. **The stamping defect is reproduced at the pinned seam.**
   `Program.reason` hands empty specific-label maps to the fp path
   (program.py:34-38 reproduced); the closed-world list rides to both paths
   as the pin stamps it onto all variants. Filed in the session report as an
   oracle-bug-candidate follow-up, per AC-6.

## Consequences

- The public views (`get_rule_trace`, `filter_and_sort_*`, `get_dict`,
  `get_time`) consume only the trace lists and `time`, which both schedules
  produce in their pinned shapes. One view branches on the knob by pinned
  necessity: `get_dict` in fp_mode reproduces the fp variant's
  stale-edge-variable defect (every edge row lands on the last edge —
  session-19 review probe `probe-fp-getdict-edges`, verified against the
  installed oracle).
- The fp schedule inherits the pin's non-termination on `timesteps=-1`
  (the fp timestep sweep has no exit when tmax is -1,
  interpretation_fp.py:272-273). Deliberately reproduced, not fixed; a case
  pinning that arm would need a timeout-shaped probe and is out of scope.
- `num_ga` (unobserved by any pinned public probe) is tracked only by the
  default schedule, as at the pin; the shared helpers gate their counts on
  `fp_mode` rather than guessing an index shape the fp variant never had.
- ADR 0002's design otherwise stands: one explicit Interpretation object,
  transcribed loops, banked-copy traces.
