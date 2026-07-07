<!-- doccode: pyreason-rewrite-docs-reviews-phase3-slice3-author -->
# Phase 3, slice 3 — author report: the cross-run state lifecycle

- session: 18 · date: 2026-07-07 · author packet
- verdict: **14/14 oracle-vs-rewrite PASS** (`results-phase3-slice3/report.json`,
  gitignored rebuildable artifacts per the slice-1/2 convention),
  fast tier **209 passed** (195 preexisting + 14 new), zero DIV records needed
- code commits: `a85886a` (engine + seam tests), `f2f9b29` (surface flips +
  evidence banking); no new ADR — 0002 still describes the truth (below)

## What the lifecycle semantics turned out to be at the pin

Re-verified line-by-line at e1a94af3 before implementing; every banked
observation the packet named as a design input held:

- **`reset()` is a PARTIAL clear** (pyreason.py:487-507): facts
  (`__node_facts`/`__edge_facts` → None, name ledger cleared), the
  closed-world set, and the graph global go; `reset_rules()` is called for
  the rules half. What SURVIVES: settings, `__ipl`, `__clause_maps`, the
  graph-parse products (`__non_fluent_graph_facts_*`,
  `__specific_graph_*_labels` — the banked grounding-tables-survive-reset
  observation, confirmed at the pin), and **the `__program` object itself**
  — `reset_graph()` nulls its graph and interp but `__program` is never
  re-Noned. Consequences, all banked and now reproduced: `get_logic_program`
  returns the same half-cleared object; `get_interpretation` returns None
  *without raising* (distinct from the no-program raise);
  `get_time` trips `AttributeError: 'NoneType' object has no attribute
  'time'` because the null-interp access sits OUTSIDE its try (pyreason.py:
  554-558); a caller's stale interpretation still renders the full trace
  (clause maps survived).
- **`reset_rules()`** (pyreason.py:517-527): rules, the rule-name ledger,
  AND both callable registries (annotation/head functions) clear together;
  the program keeps its interpretation, so `get_time` still answers — the
  observable contrast with `reset()`.
- **`reset_settings()`** (pyreason.py:561-565): knob defaults only; nothing
  else moves.
- **`reason(again=True)` with no program** short-circuits to a fresh run
  (`not again or __program is None`, pyreason.py:1516) — silent degrade,
  not an assert.
- **A bare `again` with no fact added since** raises
  `TypeError('List() argument must be iterable')`: `_reason` clears the
  fact globals to None on exit (pyreason.py:1622-1624) and `_reason_again`
  converts them via `numba.typed.List(None)` (pyreason.py:1636). Same raise
  after a `reset()` + `again` (the half-cleared ordering interaction).
- **`restart=False`** continues the timeline (`tmax = interp.time +
  timesteps`, program.py:57); **`restart=True`** zeroes `time` and
  `prev_reasoning_data[0]` under an INTACT trace (program.py:54-56 +
  interpretation.py `_start_fp`), so the trace-reconstructing views
  (`get_dict`, `filter_and_sort_nodes`) hit trace rows whose t exceeds the
  reset clock and raise `KeyError(1)`.
- **`persistent`** gates the per-timestep widen-to-[0,1] of every
  non-static bound (interpretation.py:260); the filter frames are
  change-driven and therefore IDENTICAL under both knob positions on this
  program — the observable difference lives in `get_dict`'s persistent arm,
  which stamps each change onto every later timestep (interpretation.py:
  707-740; the banked on/off interp-dict diff is exactly Mary@t1,2 +
  Justin@t2). **`canonical`** is a pure alias (setter and getter share
  persistent's field, pyreason.py:357/:167) with last-write-wins.

## How the rewrite reproduces them

Everything landed inside the existing explicit-state design — three small
additions, no reshaping:

- `_state.reset(state)` / `_state.reset_rules(state)` (`src/pyreason/_state.py`)
  mirror the pinned partial clears field-for-field over `EngineState`; the
  facade grew three one-line delegations (`reset`, `reset_rules`,
  `reset_settings` — the last calls the already-landed `Settings.reset()`).
  Session 17's scaffolding earned its keep unchanged: the pinned-verbatim
  `Program.reset_graph/reset_rules/reset_facts` stubs and the wired
  `again`/`reason_again` dispatch are now load-bearing and proven (slice-2
  review L2 resolved — no correction needed).
- `_reason_again` gained the pinned sharp edge: fact lists still None →
  `TypeError('List() argument must be iterable')`, reproduced
  message-for-message with a comment naming pyreason.py:1636 (the rewrite
  has no numba.typed.List; the pinned raise's observable is the contract).
- `Interpretation.get_dict()` (`src/pyreason/_interpretation.py`): the
  trace-rebuilt `{t: {component: {label: (l, u)}}}` view over plain dicts
  (the pinned InterpretationDict's canonical form), with the persistent
  forward-stamping arm and the same KeyError when a trace row's t exceeds
  `self.time`. The oracle's per-component default-read of (0, 1) on a
  MISSING key is a getter behavior invisible to the capture's items()-based
  canonicalization; the compared shape is the stored entries, which match.
- Nothing else needed code: the persistent/canonical loop behavior, the
  restart arms, the accessor returns, and the `filter_and_sort` KeyError
  were already carried by the slice-1/2 machinery and are now proven over
  this case family.

**AC-1 (design):** no new hidden state — the facade still wraps exactly one
`EngineState`; the reset family is pure functions over it; every new
observable is either a field clear or a view. ADR 0002's state/step/trace
description is unchanged by this slice, so no ADR 0003: the one
design-adjacent choice (raising the pinned TypeError message explicitly
rather than transliterating a numba container) is a line-level
meaning-for-meaning call of the kind ADR 0002 §Decision 2 already licenses.

## Acceptance criteria, answered

1. **Explicit state, one core.** Answered above — three additions inside
   the existing design, facade unchanged in shape, no ADR needed and the
   report says why.
2. **Fast tier.** `uv run pytest -m "not e2e"` → **209 passed, 2
   deselected**. 14 new seam tests in
   `tests/test_rewrite_state_lifecycle.py`, all at the module-global
   facade, each with a `proves:` docstring: the reset family's exact
   clear/survive splits (no-program and with-program classes, the
   half-cleared program's accessor trio, stale-trace consumability,
   settings/clause-map survival, the post-reset raise pair), the
   again/restart arms (no-program degrade, bare-again TypeError,
   restart-false timeline continuation, restart-true clock-reset KeyErrors),
   and persistent/canonical (per-timestep reset vs static escape, get_dict
   forward stamping, the alias driving the loop). Two authoring
   expectations were corrected against the banked artifacts during
   development (atom-off traces carry '-' placeholders; persistent-on
   differs from -off only in get_dict) — the artifacts, not intuition, are
   the source of truth the tests encode.
3. **14-case run: 14/14 PASS** into `results-phase3-slice3/`. Per case: 4
   fresh-process captures, same-engine repeats digest-stable, A-vs-B equal.
   **Zero divergences → no DIV records** (docs/divergences/ stays
   nonexistent).
4. **surface.md: five rows flipped to `equivalent`** — `fn:reset`,
   `fn:reset_settings`, `fn:get_logic_program`, `fn:get_interpretation`,
   `setting:canonical`: each row's full `cases` field now sits inside the
   39 cases passed across sessions 16–18 (verified mechanically by subset
   check over the three slice results dirs). Notably NOT flipped:
   `fn:reset_rules` (its cases also include annotation-fn-reset-clears and
   head-fn-reset-clears, not yet run against the rewrite) and
   `setting:persistent` (static-graph-facts-on/off outstanding); `fn:reason`
   and `fn:get_time` remain far from closure (50+ cases each). Coverage:
   **8/52 rows equivalent-or-adjudicated (15.4%)**, from 3/52. Inventory
   gate green (in the 209).
5. **Hygiene.** `git status` clean at close; `git -C oracle/pyreason status
   --porcelain` empty, pin untouched; no installs or dependency changes;
   banked `results/`, `results-phase3-slice1*/`, `results-phase3-slice2*/`
   unmodified (`results/` consumed read-only as diff targets); case staging
   and the screen run confined to the session scratchpad. One correction
   during the session: the evidence commit initially tracked the slice-3
   artifacts; amended (local, unpushed) to the established
   gitignore-the-results-dir convention before anything else stacked on it.

## Per-case verdicts (oracle-vs-rewrite, 4 fresh captures each)

Wall-clock is the artifact-recorded per-capture engine time (import +
steps/reason) for each engine's first capture; verdicts of record are
`results-phase3-slice3/report.json`. Full run: 3m01s wall.

| case | verdict | oracle a1 (import + run) | rewrite b1 (import + run) |
|---|---|---|---|
| reset-no-program | pass | 1.34s + 0.00s | 0.06s + 0.00s |
| reset-with-program | pass | 1.36s + 2.98s | 0.06s + 0.00s |
| reset-rules-no-program | pass | 1.39s + 0.00s | 0.06s + 0.00s |
| reset-rules-with-program | pass | 1.35s + 3.00s | 0.06s + 0.00s |
| reset-settings-restore | pass | 1.37s + 3.01s | 0.06s + 0.00s |
| accessors-lifecycle | pass | 1.32s + 2.50s | 0.06s + 0.00s |
| reason-again-no-program | pass | 1.34s + 2.94s | 0.06s + 0.00s |
| reason-again-restart-false | pass | 1.36s + 3.00s | 0.06s + 0.00s |
| reason-again-restart-true | pass | 1.38s + 3.03s | 0.06s + 0.00s |
| reason-bare-again-no-facts | pass | 1.44s + 2.96s | 0.06s + 0.00s |
| persistent-off | pass | 1.35s + 2.89s | 0.06s + 0.00s |
| persistent-on | pass | 1.35s + 2.92s | 0.06s + 0.00s |
| canonical-on | pass | 1.35s + 2.93s | 0.06s + 0.00s |
| canonical-last-write | pass | 1.30s + 2.89s | 0.06s + 0.00s |

(The oracle's run seconds are dominated by numba kernel-cache loading on
first reason(); the rewrite's sub-millisecond steps round to 0.00. Import
weight and cache mechanics, not a speed claim — none is made or licensed by
this table.)

## Deliberately-reproduced oracle behaviors (AC-6 candidates, not blessed)

Each reproduced because matching the pin is the default meaning of correct
(equivalence-PASS); each is named here as an oracle-bug-candidate follow-up
rather than silently absorbed, per the charter's divergence semantics:

- **The half-cleared program after `reset()`** — `get_time` raises
  `AttributeError` on `None.time` instead of answering 0 (the no-program
  path's behavior), because `reset()` nulls the interp but never the
  program. A rewrite-preferred design would re-None the program (making
  reset-then-get_time answer 0 uniformly); provisionally matched instead.
- **`restart=True` resumes under an intact trace** — the clock resets to 0
  while the t=1,2 trace rows survive, so `Interpretation.get_dict` and
  `filter_and_sort_nodes` crash with `KeyError(1)` on a successfully
  returned interpretation. The case record itself names this the
  oracle-bug-candidate once a rewrite exists to diverge; that rewrite now
  exists and reproduces it deliberately.
- **The bare-again `TypeError('List() argument must be iterable')`** — an
  implementation-artifact message (numba's container constructor) standing
  in for a real "no facts to resume with" signal; reproduced
  message-for-message.
- **`again=True` with no program silently degrades to a fresh run** rather
  than asserting — pinned short-circuit, reproduced.
- **Grounding tables survive `reset()`** (graph-parse products, clause
  maps, IPL) — the state-contamination family's banked observation,
  confirmed at the pin and reproduced by leaving those `EngineState` fields
  untouched in `reset()`.

If the operator wants any of these improved, the path is the charter's:
file the DIV record proposing intentional-divergence with a failing test,
keep matching the pin until adjudicated.

## Deviations from the packet spec

None of substance. Two notes: (1) the evidence-banking commit was amended
once to honor the results-dir gitignore convention (hygiene section); (2)
the packet's e2e command shape was followed exactly, plus one 2-case screen
run into the scratchpad first (screen-then-confirm) — reset-with-program
and reason-again-restart-true, the two sharpest cases, before the full 14.

## Repro commands

```
# fast tier (209 passed, 2 deselected)
uv run pytest -m "not e2e"

# the new seam tests alone
uv run pytest tests/test_rewrite_state_lifecycle.py -q

# the 14-case oracle-vs-rewrite run (stage into a scratch dir first)
mkdir -p /tmp/slice3-cases && for c in reset-no-program reset-with-program \
  reset-rules-no-program reset-rules-with-program reset-settings-restore \
  accessors-lifecycle reason-again-no-program reason-again-restart-false \
  reason-again-restart-true reason-bare-again-no-facts persistent-off \
  persistent-on canonical-on canonical-last-write; do \
  cp harness/cases/$c.json /tmp/slice3-cases/; done
PYTHONHASHSEED=0 uv run python -m harness.run --cases /tmp/slice3-cases \
  --engine-a oracle-env/bin/python --engine-b scripts/rewrite-python \
  --results results-phase3-slice3
```

## Queued-ask recommendations

None new. The pyyaml ask stays queued untouched (nothing in this packet
needed it). No adjudication asks arise from this slice: every candidate
behavior above is reproduced-and-named, not divergence-proposed.
