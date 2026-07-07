<!-- doccode: pyreason-rewrite-docs-reviews-phase3-slice2-review -->
# Phase 3, slice 2 — independent review: the default-path reasoning spine

- session: 17 · date: 2026-07-07 · reviewer packet (no shared context with the author)
- author commits reviewed: `56b0559`, `0ad3fa4`, `1b55fe7` · author report:
  [2026-07-07-phase3-slice2-author.md](2026-07-07-phase3-slice2-author.md) ·
  design record: [ADR 0002](../adr/0002-reference-core-state-step-trace.md)
- review commit: this one (report + `.gitignore` line for the review results
  dir; **no engine-code fixes were needed**)
- verdict: **packet PASSES with zero High/Medium findings and zero code
  changes.** Post-review evidence: fast tier **195 passed, 2 deselected**
  (rerun by the reviewer), independent 13-case rerun **13/13 pass**
  (`results-phase3-slice2-review/`), author's banked-digest claim recomputed
  **39/39 equal** AND the reviewer's fresh rewrite captures also equal the
  banked session-15 sweep **39/39**, **10 reviewer-constructed
  discriminating probes — all 10 match cross-engine** (9 through the
  harness, 1 direct two-engine script for the registered-function arms the
  harness cannot carry). Zero divergences → zero DIV records.

## How the review was run

The semantic-fidelity lens came first. The whole rewrite core was read
side-by-side against the pinned source:

- `_interpretation.py` against `interpretation.py:240-686` (the temporal
  loop), `:809-1281` (`_ground_rule`), `:1506-1740` (`_update_node/_edge`),
  `:1914-1931` (`annotate`), `:1960-2083` (inconsistency resolution),
  `:2086-2145` (`_add_node/_add_edge/_add_edges`), `:2181-2200`
  (`float_to_str`), and the `Interpretation` init/`_start_fp` scaffolding;
- `_grounding.py` against `:1284-1503` and `:2230-2338` (satisfaction,
  thresholds, clause grounding, refinement, head functions);
- `_world.py`/`interval.py` against `world_type.py` (the jitted `update`
  replaces the dict entry with a NEW interval whose prev bounds ride
  through) and `interval_type.py` (both intersection arms, `closed`'s
  prev-seeding, `reset`, `copy`);
- `_program.py`/`_state.py`/`__init__.py` against `program.py` and
  `pyreason.py:520-700/1490-1701` (reason dispatch, fact merge order, the
  store-off atom-trace flip, queries filtering, edge-heavy clause
  reordering, the post-run fact clear, accessors, `get_time`);
- `_output.py` against `output.py` + `filter.py` (row cells, ragged-row
  padding — verified empirically that the pinned object-dtype DataFrames pad
  with `None`, matching `Frame`; the clause-map re-render; the
  latest-change/stable-sort/default-cell filter pipeline);
- `_graph.py` against `graphml_parser.py` (the coercion ladder verbatim,
  including the bool-rides-as-int arm and the exact "Added N ..." print).

Checked load-bearing details that could not hide behind the 13 cases:
grounding candidate derivation for all four edge-clause cases; the
clause-level threshold gate's arithmetic (number/percent × total/available,
the percent-zero-candidates False arm, the *number* branch never consulting
the denominator); reference-vs-value semantics of every trace append (the
pinned intervals are numba structrefs — reference types — so the rewrite
appending live objects where the pin appends live references, and copying
exactly where the pin calls `.copy()`, is meaning-for-meaning); the
`in_loop`/`update` threadsafe-flag merge collapsing to in-place flag writes
(equivalent because nothing reads `update` between a delta-0 enqueue and
the merge point at the pin); the static-fact re-enqueue and the node/edge
static-arm trace asymmetry; the convergence bookkeeping (what counts as a
change, prev-bound seeding, the `t += 1` before every converged break, the
skipped `num_ga` append on break).

Then the overfitting hunt: 13 cases cannot pin a reasoning engine, so ten
probe programs were constructed specifically to split plausible-but-wrong
semantics from the pinned ones, and run through **both** engines
(`oracle-env/bin/python` vs `scripts/rewrite-python`, fresh processes,
`PYTHONHASHSEED=0`). None of them reuse a committed case's program.

## The discriminating probes, and each one's both-engine outcome

Harness probes (4 captures each, judged by the committed runner; artifacts
in the session scratchpad, every probe case and the direct script quoted
verbatim in [the raw companion](2026-07-07-phase3-slice2-review-raw.md)):

| probe | what it splits | outcome |
|---|---|---|
| probe-fp-delta0 | delta-0 rule chain: inner fixed-point re-entry, fp counter per pass (rows carry fp 0/1/2/3), reset-starved regrounding at t=1, perfect convergence at t=1 | pass (identical) |
| probe-threshold-edges | boundary arithmetic: 2/3 vs percent 66.66 (fires) and 66.67 (does not); `equal` percent on an exact half; `less_equal 0` satisfied by an EMPTY qualifying set (rule still fires, empty clause column); percent/**available** re-basing the denominator on label carriers (1/2 ≥ 50% fires where total's 1/3 would not) | pass (identical) |
| probe-inconsistency | both pinned inconsistency-message arms (the IPL grounding-conflict text and the `float_to_str` "[0.000, 0.200] to [1.000, 1.000]" text), [0,1]+static resolution rows, IPL rows on the way in | pass (identical) |
| probe-fact-window | fact active only [2,4] + delta-2 rule under perfect convergence: window bookkeeping, reset starvation after the window, convergence at the max enqueued conclusion time (t=6, get_time 7) | pass (identical) |
| probe-edge-chain | two-clause edge-head rule over a triangle: head-pair enumeration filtered to existing edges, per-head temp-grounding refinement, per-head-filtered clause columns | pass (identical) |
| probe-conv-count-one | convergence_threshold=1: whether graph-attribute fact updates count toward changes_cnt at t=0 (they do — convergence defers to t=1) | pass (identical) |
| probe-conv-bound-arith | delta-bound arithmetic on partial bounds ([0.4,0.6] fact, [0.5,1] head): per-timestep max deltas 0.6/0.5/0 against 0.35 — re-derived unchanged bounds contribute zero | pass (identical) |
| probe-static-fact | static user facts riding forward; the static-arm trace asymmetry made *visible* by second static facts with different bounds: the node arm banks the FACT's bound ([0.25,1]) while the edge arm banks the live WORLD bound ([0.5,1]) | pass (identical) |
| probe-clause-reorder | edge-heavy graph (4 edges > 3 nodes): live rule reordered node-first (accessor fingerprint) while trace clause columns render back in author order through the clause map | pass (identical) |

Direct two-engine probe (the harness cannot carry registered callables into
the rewrite env — see finding L1): one script run under each engine binary,
oracle registrands njit-wrapped exactly as `harness/reference_fns.resolve`
does, rewrite registrands plain; oracle kernel-cache snapshot/restored
around the run the way the capture does for registrand cases. Program: a
2-arg annotation function (weighted lower mean), the 6-arg extended form
(clause-0 grounding count / 8), a **negated-head** rule with an annotation
function (the `(1-u, 1-l)` flip arm at interpretation.py:588-589), and a
registered head function grounding `Processed(pick_first(V))`. Every trace
row identical, including `w(A) [0.6875,1.0]`, `z(A) [0.25,1.0]`,
`neg(A) [0.0,0.3125]`, both head-fn firings, and get_time — all matching
the hand-derivation from the pinned source. (The only diff line between the
two outputs is the oracle env's import-time "torch is not installed"
banner, which is not part of any compared surface.)

## Findings

**High: none. Medium: none.**

- **L1 (Low, harness boundary — no code change this packet).** Registered
  annotation/head functions are structurally uncoverable cross-engine
  through the committed harness: `harness/reference_fns.resolve()` njit-
  wraps inside the engine env, and the campaign env carries no numba, so a
  registrand case fails the rewrite capture at resolve time. This packet's
  registered-function arms therefore ride on seam tests plus this review's
  out-of-harness probe (which matched exactly). Before the
  `fn:add_annotation_function`/`fn:add_head_function` rows can flip to
  equivalent, the harness needs an accommodation (e.g. resolve() only
  njit-wrapping when numba imports). Queued as follow-up work, not a defect
  in this packet's claims — the author claimed those rows `cased` and
  flipped only `type:Threshold`.
- **L2 (Low, accepted with rationale — not fixed).** `Program.reset_graph/
  reset_rules/reset_facts` (6 lines) have no consumer yet — the reset
  family is an explicitly deferred packet. Strictly this is scaffolding
  beyond what the current cases + seam tests consume; it is kept because it
  is the pinned Program surface verbatim, the reset packet lands next, and
  delete-then-re-add is churn without risk reduction. The same reasoning
  covers the wired-but-unproven `again`/`reason_again` dispatch, which the
  author's report names arm-by-arm with no equivalence claim.
- **L3 (Low, noted only).** `annotate()`'s return shape is looser than the
  pin at an unpinned boundary: the pinned objmode block coerces the
  registrand's return to `(float64, float64)` (an exotic return shape fails
  numba coercion at reason time), while the rewrite accepts anything
  indexable at [0]/[1]. Unreachable through the committed reference
  functions; belongs to the future registrand-behavior packet.
- **L4 (Low, noted only).** `_grounding._satisfies_threshold` returns
  `None` (falsy) for a quantifier-type outside number/percent, where the
  pinned jitted version would fail compilation-side. Unreachable: the
  `Threshold` constructor validates membership, and the parser only
  synthesizes valid tuples.

Also verified as *sound* (candidate concerns that did not become findings):
the narrowed `except KeyError`(+`AttributeError`) replacing the pin's
blanket `except Exception` — traced every reachable default-path arm of
`_update_component` and the satisfaction guards; no arm exists where the
pinned blanket catch fires mid-body after partial mutation, so the
narrowing is behavior-preserving exactly as ADR 0002 §Decision 5 argues.
The omitted `edges_to_be_added_node_rule` container — confirmed nothing
feeds it at the pin (node-rule appends discard the edges field; the
container is filtered but always empty). The collapsed threadsafe buffers —
merge order is rule order, grounding is sequential at the pin
(`parallel=False`), and the `update=False` write is unobserved between
enqueue and merge. `Frame` vs pandas — the capture consumes only
`columns`/`itertuples(index=False, name=None)`/`empty`, and the pinned
object-dtype frames pad ragged rows with `None` (checked against the banked
artifacts and live pandas), which `Frame` reproduces.

## The claimed evidence, independently

- **Fast tier:** `uv run pytest -m "not e2e"` → **195 passed, 2
  deselected** (matches the author's claim; includes the surface-inventory
  gate).
- **13-case rerun:** fresh 4-capture differential run into
  `results-phase3-slice2-review/` → **13/13 pass** (report.json is the
  verdict of record; same-engine repeats digest-stable for all 13).
- **Digest cross-checks recomputed:** author's banked run
  (`results-phase3-slice2/<c>/b1.json`) vs session-15 sweep
  (`results/<c>/a1.json`) → **39/39 probe digests equal**; the reviewer's
  fresh run (`results-phase3-slice2-review/<c>/b1.json`) vs the same banked
  sweep → **39/39 equal**.

## Design bars (charter AC-5, Phase-3 shape)

- **Pure functions over explicit state:** all run state lives on
  `Interpretation`; the loop/grounding/update functions are module-level
  over it; `EngineState` carries everything the pin keeps in module
  globals; the facade holds exactly one `_state_obj` and delegates in one
  line per function. The seam tests swap fresh states through the facade —
  the embedder path is real, not decorative.
- **One engine, no second core:** `Program.reason` builds the one
  `Interpretation` regardless of the parallel/fp knobs (their
  distinguishing cases will adjudicate those arms later, as the author
  says).
- **No numba-idiom transliteration, no gratuitous divergence:** the three
  collapses (buffers, shared `_update_component` with the per-kind
  static-arm asymmetry kept, omitted dead container) are each argued in ADR
  0002 and verified here; everything else is meaning-for-meaning with the
  pin's control flow.
- **ADR 0002 honesty:** accurate — including its non-claims (the
  wired-but-unproven arms stay uncased and say so).

## Tests and surface.md

The 20 new seam tests all drive the facade
(`load_graph/add_rule/add_fact/reason` in; trace/filter/get_time out);
every `proves:` docstring was read against its assertions and none
overstates (the threshold, convergence, closed-world, IPL, head/annotation
function, reorder, and store-off claims each match what the test pins).
surface.md: `type:Threshold` → `equivalent` is honest — all six cases in
its `cases` field passed oracle-vs-rewrite (threshold-construct in
`results-phase3-slice1`, the five consumption cases in
`results-phase3-slice2`, re-verified from both banked report.json files);
no other row moved; 3/52 equivalent confirmed by count.

## Hygiene

`git -C oracle/pyreason status --porcelain` empty and HEAD equals the PIN
(`e1a94af33e1f`); no dependency or lockfile changes in any reviewed commit;
banked `results/`, `results-phase3-slice1*/`, `results-phase3-slice2/`
untouched (mtimes predate the review; reads only); the review run went to
the fresh `results-phase3-slice2-review/` (now gitignored like its
siblings); probe cases, scripts, and artifacts confined to the session
scratchpad; commit messages match what the commits contain.

## Final verdict

**PASS.** The reasoning spine is a faithful reproduction of the pinned
default-settings engine on every surface this review could reach: 13/13
committed cases (independently rerun), 78 banked-digest equalities across
the two cross-checks, and 10/10 reviewer-constructed discriminating probes
— including the arms no committed case covers (delta-0 fixed-point
re-entry, threshold boundary arithmetic on all four quantifier-type
combinations, both inconsistency-message arms, fact windows, static-arm
trace asymmetry, clause reordering, and registered annotation/head
functions with the negated-head flip). Zero divergences; zero DIV records;
zero fixes required.
