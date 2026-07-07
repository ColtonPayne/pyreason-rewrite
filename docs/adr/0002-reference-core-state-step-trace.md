<!-- doccode: pyreason-rewrite-docs-adr-0002 -->
# ADR 0002 — Reference reasoning core: one explicit Interpretation, a transcribed step loop, banked-copy traces

- status: accepted
- date: 2026-07-07
- session: 17 (Phase 3, reasoning-spine slice)

## Context

The charter's Phase-3 shape is a pure-Python reference core: "write the hot
loop as pure functions over explicit state"; equivalence from the first
commit; expected to be slow, its job is meaning. The equivalence meaning is
fixed by the pinned oracle's default-settings engine (the non-parallel,
non-fp `interpretation.py` at e1a94af3) whose observable outputs — trace
rows and their ordering, per-timestep frames, `get_time`, raise types and
messages — the banked case artifacts already carry. Two constraints shape
the design: no dependency changes (so no pandas/numpy/numba in the rewrite
env), and AC-5's no-hidden-state bar.

## Decision

1. **State shape.** All run state lives on one `Interpretation` object
   (`_interpretation.py`): worlds + predicate maps per component kind,
   pending fact/rule queues with their index-aligned trace side-lists, the
   change trace, graph adjacency, and the resume counters (`time`,
   `prev_reasoning_data`). `Program` (`_program.py`) binds inputs to a fresh
   `Interpretation` per `reason()` and re-drives the same one on
   `reason_again` — `program.interp` is the accessor contract. `EngineState`
   gains the module-global surface the pinned facade keeps in globals
   (graph + attribute products, IPL, registered functions, closed-world
   names, clause maps); the facade stays one-line delegations.
2. **Step shape.** The temporal loop, grounding, and update functions are
   module-level functions over the explicit state, transcribed
   meaning-for-meaning from the pin: per timestep — non-persistent reset,
   due facts (nodes then edges), an inner fixed-point loop (due rule
   conclusions, then reground everything if anything updated; delta-0
   conclusions re-enter), then the convergence check
   (delta_interpretation | delta_bound | perfect). Threshold gating is
   clause-level, before head enumeration. Numba *idioms* are not
   transcribed: the per-rule threadsafe buffers collapse to direct appends
   (identical order — buffers were merged in rule order and grounding is
   sequential with parallelism pinned off), `_update_node`/`_update_edge`
   share one body (the pinned pair differs only in container identity...
   except the static-fact trace row, which stays per-kind: the pinned node
   arm banks the FACT's bound, the edge arm banks the live world bound),
   and `edges_to_be_added_node_rule` is omitted (nothing feeds it at the
   pin — node rules never carry edges to add).
3. **Trace shape.** Trace rows are 9-tuples
   `(t, fp, comp, label, bound-copy, consistent, triggered_by, name, msg)`
   plus an atom-detail list in lockstep when `atom_trace` is on; every
   banked bound is an explicit `.copy()` exactly where the pin copies, so
   later mutation cannot rewrite history. Views (`_output.py`) render
   through `Frame` — a value object exposing exactly the DataFrame surface
   the capture consumes (`columns`, `itertuples`, `empty`) with identical
   cells, row order, ragged-row None padding, and the clause-map reorder of
   rule rows' clause columns. No pandas: a dependency ask for
   display-parity alone is not warranted while every consumer compares
   cell-for-cell.
4. **Two interval arms, both kept.** The pin has two intersection
   implementations: the Python proxy seeds the result's previous bounds
   from self's CURRENT bounds (public `Interval.intersection`, banked by
   interval-ops), the jitted overload — which `World.update` compiles
   against — seeds from self's PREVIOUS bounds (`interval.intersect_jitted`
   here). The engine uses the jitted arm; preserved previous bounds are
   what make a re-derived unchanged bound count zero toward both
   convergence deltas. The divergence is a board item, not absorbed.
5. **Pinned quirks are reproduced, not repaired** (each also named in the
   session report): the unregistered-annotation-function NameError with the
   pinned message text (the objmode unbound-variable raise, reproduced as
   an explicit raise at the same decision point); the silent
   unregistered-head-function arm; the no-break annotation-function match
   loop (last same-named registrand wins); static facts riding forward
   without holding perfect convergence open; the parser-vs-annotation
   division of head-negation bound flipping. One deliberate narrowing: the
   pin's blanket `except Exception` guards around component lookup become
   `except KeyError` (+`AttributeError` in satisfaction checks) — the
   pinned semantics is "missing component/label never satisfies/updates",
   and a blanket catch would let a rewrite implementation fault silently
   bank as `(False, 0)` engine behavior.

## Consequences

- Equivalence evidence: all 13 proof-set cases' probe digests match the
  banked oracle artifacts, and the live 4-capture differential run is the
  session's committed verdict (`results-phase3-slice2/`).
- The non-default arms wired but not yet case-proven (again/restart,
  queries filtering with its unordered de-dup, override update mode,
  inconsistency resolution, infer-edges application, IPL propagation)
  follow the pinned control flow but stay `cased`/uncovered in
  docs/surface.md until their cases run — no equivalence claim rides on
  this ADR.
- Performance is explicitly out of scope for the reference core; grounding
  re-derives candidate sets per fixed-point pass exactly like the pin.
