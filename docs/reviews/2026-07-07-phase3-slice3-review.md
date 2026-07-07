<!-- doccode: pyreason-rewrite-docs-reviews-phase3-slice3-review -->
# Phase 3, slice 3 — independent review: the cross-run state lifecycle

- session: 18 · date: 2026-07-07 · reviewer packet (no shared context with the author)
- author commits reviewed: `a85886a`, `f2f9b29`, `2466f2a` · author report:
  [2026-07-07-phase3-slice3-author.md](2026-07-07-phase3-slice3-author.md) ·
  design record: [ADR 0002](../adr/0002-reference-core-state-step-trace.md)
- review commit: this one (report + raw probe materials + `.gitignore` line
  for the review results dir; **no engine-code fixes were needed**)
- verdict: **packet PASSES with zero findings at any severity and zero code
  changes.** Post-review evidence: fast tier **209 passed, 2 deselected**
  (rerun by the reviewer; the 14 new lifecycle seam tests pass alone in
  0.06s), independent 14-case rerun **14/14 pass**
  (`results-phase3-slice3-review/`), digest cross-check **14/14** (reviewer's
  fresh rewrite `b1` digests equal the banked session-15 sweep's
  `results/<case>/a1.json` digests) plus oracle self-stability **14/14**
  (reviewer's fresh `a1` digests equal the banked sweep's), **all five
  claimed oracle-quirk reproductions verified against BOTH the pinned source
  and the installed oracle**, and **31 reviewer-constructed discriminating
  probe observations across 8 probe families — every one identical
  cross-engine**. Zero divergences → zero DIV records
  (`docs/divergences/` stays nonexistent).

## How the review was run

Semantic fidelity first. The slice's code was read line-by-line against the
pinned source at `e1a94af33e1f`:

- `_state.py` `reset`/`reset_rules` against `pyreason.py:487-527` — the
  clear/survive split is field-for-field: facts + name ledger + closed-world
  set + graph go on `reset()` (with `program.reset_facts()`/`reset_graph()`
  when a program exists, in the pinned order), rules + rule-name ledger +
  BOTH callable registries go on `reset_rules()` (with
  `program.reset_rules()`); settings, IPL, clause maps, and the graph-parse
  products survive both, and `__program` is never re-Noned — exactly the
  pin's partial clear, including the rebind-vs-clear asymmetry
  (`facts_name_set.clear()` vs `closed_world_predicates = set()`).
- The facade (`__init__.py`) against `pyreason.py:529-565` — `reset_settings`
  delegates to `Settings.reset()`; `get_logic_program`/`get_interpretation`/
  `get_time` reproduce the accessor trio including the null-interp access
  sitting outside `get_time`'s try.
- `_state.reason`/`_reason`/`_reason_again` against `pyreason.py:1497-1642` —
  the `not again or program is None` dispatch, the post-run fact clear at
  the end of `_reason` only (a resume does NOT clear the lists — see probe
  P4), and the explicit `TypeError('List() argument must be iterable')`
  standing in for `numba.typed.List(None)` at the same decision point
  (pyreason.py:1636). The add-fact path creates both lists together
  (pyreason.py:1133-1165 ↔ `_state.add_fact`), so the rewrite's
  either-is-None guard cannot fire on a state the pinned engine would
  accept.
- `_program.Program.reason_again`/`reset_*` against `program.py` — the
  `restart` tmax arms (`tmax` vs `interp.time + tmax`), the same-interp
  re-drive, and `reset_graph` nulling `interp` are verbatim. Session 17's
  accepted scaffolding (`Program.reset_graph/reset_rules/reset_facts`, the
  again-dispatch) is now consumed by `_state.reset`/`reset_rules` and the
  resume cases — load-bearing, no dead scaffolding.
- `_interpretation.py` `_start_fp`'s again/restart arm against
  `interpretation.py:218-236` (the `num_ga` append, the restart-only zeroing
  of `time` and `prev_reasoning_data[0]` under an untouched trace) and
  `get_dict()` against `interpretation.py:707-740` — the
  `range(self.time+1)` axis (whence the restart-true `KeyError(1)`), the
  trace-rebuilt entries, and the persistent forward-stamping arm. The
  oracle's `InterpretationDict.__getitem__` default-read of `(0, 1)` on a
  missing key was checked against `interpretation_dict.py`: it stores into
  `self.__dict__` and `items()` delegates there, and the harness `canonical()`
  reduces dicts via `items()` — so the author's claim that the default-read
  getter is invisible to the compared shape is correct, on both sides of the
  comparison.
- `_settings.py` against `pyreason.py:43-83/161-175/347-369` — the 17 stored
  defaults match `_Settings.reset()` value-for-value; `canonical` shares the
  `persistent` store exactly as the pinned setter pair does (the pinned
  `__canonical` field is dead — both setters write `__persistent`), so
  last-write-wins falls out of the shared store rather than being simulated.
- The persistent knob's loop effect against `interpretation.py:259-273` —
  the `t>0 and not persistent` widen of every non-static bound, position and
  guard identical in the rewrite loop.

Then the evidence was re-derived (below), the five claimed quirks were
reproduced against the installed oracle, and eight discriminating probe
families were constructed around the seams the 14 committed cases cannot
pin.

## The five claimed quirk reproductions — each verified twice

Each was verified (a) in the pinned source at the cited anchor and (b)
empirically against the installed oracle (`oracle-env/bin/python`, script
banked in [the raw materials](2026-07-07-phase3-slice3-review-raw.md)).
All five hold exactly as the author describes:

1. **Half-cleared program after `reset()`** — pinned at
   `pyreason.py:498-504` (program nulled nowhere) + `program.py:62-64`.
   Observed: `get_logic_program()` returns the SAME object
   (`is` comparison True), `program.interp` is None, `get_interpretation()`
   returns None without raising, `get_time()` raises
   `AttributeError: 'NoneType' object has no attribute 'time'`. The
   post-reset raise pair also observed: fresh `reason()` → the no-rules
   `Exception`; `reason(again=True)` → the fact-conversion `TypeError`.
2. **`restart=True` resumes under an intact trace** — pinned at
   `program.py:54-56` + `interpretation.py:221-223` (clock zeroed, trace
   untouched). Observed: `get_time()` answers 1, `get_dict()` raises
   `KeyError` with `args == (1,)`, `filter_and_sort_nodes` likewise.
3. **Bare-again `TypeError('List() argument must be iterable')`** — pinned
   at `pyreason.py:1622-1624` (the post-run clear) + `:1636` (the None
   conversion). Observed message-for-message, type `builtins.TypeError`
   (module-qualified, the harness's compared form).
4. **`again=True` with no program silently degrades to a fresh run** —
   pinned at `pyreason.py:1516`. Observed: first-ever call with `again=True`
   completes; `get_time()` answers 3 on the 2-timestep program.
5. **Grounding tables survive `reset()`** — pinned at `pyreason.py:487-507`
   (the globals list that is NOT touched). Observed in the oracle module's
   own globals after reset: `__specific_graph_node_labels` and
   `__clause_maps` non-None, `__ipl` still the built list. The IPL half is
   also observable through public behavior and matches cross-engine —
   probe P1 below shows the surviving IPL pair from a reset-away program
   stamping `unpopular` complement bounds into the NEXT program's run, and
   probe P6 shows the same through a no-reset program change.

## The overfitting hunt — 8 probe families, 31 observations, all identical

Direct two-engine script (the harness step schema carries no mid-sequence
`load_graph` or settings writes), canonicalized through the harness's own
`harness.compare.canonical_json` and the capture's DataFrame reduction, run
under `PYTHONHASHSEED=0` in both engines and diffed line-for-line — script
and full outputs in [the raw materials](2026-07-07-phase3-slice3-review-raw.md):

| probe | seam the 14 cases do not pin | outcome |
|---|---|---|
| P1 | full program (+IPL pair) → `reset()` → a DIFFERENT node-heavy graph + different rules, reason again in-process: frames, get_dict, trace, time — and the surviving IPL contaminating run 2 | identical (contamination reproduced identically) |
| P2 | `reset_rules()` BEFORE any reason, facts still loaded; re-add a different rule; reason | identical |
| P3 | `reset_settings()` after flipping persistent + atom_trace + save_graph_attributes_to_trace: knob echo sextet, atom-off trace shape, non-persistent get_dict | identical |
| P4 | resume with new facts (`restart=False`), then a SECOND `again=True` with nothing added — the resume does NOT clear the fact lists at the pin, so the second again RE-CONSUMES the same fact instead of raising | identical (no raise; clock 3→4→5 both engines) |
| P5 | `persistent=True` with a `restart=False` extended timeline: forward stamping across the resumed window, static-fact escape | identical |
| P6 | two sequential full programs, NO reset: `load_graph` replacement, rules + IPL surviving, second fresh run | identical |
| P7 | alias arms beyond the fixtures: `canonical=True` → `reset_settings()` → both read False; `persistent=True` then `canonical=False` → both read False | identical |
| P8 | second fresh `reason()` with no facts re-added (post-run clear observable through emptiness: empty frames, time 1) | identical |

P4 deserves the callout: it is the exact seam an overfitted
`_reason_again` (e.g. one that cleared the fact lists after a resume, or
raised on every repeated again) would fail — the rewrite matches the pin's
re-consume behavior because it reproduces the CLEAR's location, not the
raise as a rule.

## Evidence, independently re-derived

```
# fast tier — 209 passed, 2 deselected
uv run pytest -m "not e2e"

# the new seam tests alone — 14 passed
uv run pytest tests/test_rewrite_state_lifecycle.py -q

# 14-case rerun — ALL PASS (14 case(s))
mkdir -p /tmp/slice3-cases && for c in reset-no-program reset-with-program \
  reset-rules-no-program reset-rules-with-program reset-settings-restore \
  accessors-lifecycle reason-again-no-program reason-again-restart-false \
  reason-again-restart-true reason-bare-again-no-facts persistent-off \
  persistent-on canonical-on canonical-last-write; do \
  cp harness/cases/$c.json /tmp/slice3-cases/; done
PYTHONHASHSEED=0 uv run python -m harness.run --cases /tmp/slice3-cases \
  --engine-a oracle-env/bin/python --engine-b scripts/rewrite-python \
  --results results-phase3-slice3-review
```

Digest cross-check (recomputed, not trusted): for all 14 cases, the
reviewer's fresh `results-phase3-slice3-review/<case>/b1.json` digest map
equals the banked session-15 sweep's `results/<case>/a1.json` digest map —
**14/14** — and the reviewer's fresh oracle `a1` digests equal the banked
sweep's too (**14/14**), so the pass verdicts chain back to the
verdict-of-record artifacts, not merely to today's captures.

## Tests

All 14 new seam tests sit at the module-global facade (a fresh `EngineState`
monkeypatched in — the explicit-state design making the seam testable
without process isolation). Each `proves:` docstring was read against its
assertions; all accurate, including the two subtle ones: the atom-off trace
placeholder test asserts column index 6 (`Occurred Due To`) is `'-'` while
index 8 (`Triggered By`) still names Fact/Rule, and the persistent-on test
asserts the filter frames are IDENTICAL to persistent-off's (change-driven)
with the difference confined to `get_dict`'s forward stamping — both encode
the banked artifacts, not intuition. The surface-inventory gate is green
inside the 209.

## surface.md — row-by-row

Five flips verified: every case in each flipped row's `cases` field passed
oracle-vs-rewrite in a banked slice run AND in a review rerun —

- `fn:reset` (reset-no-program, reset-with-program): slice-3 report + this
  review's rerun, pass.
- `fn:reset_settings` (reset-settings-restore): same, pass.
- `fn:get_logic_program` / `fn:get_interpretation` (accessors-fresh-state,
  accessors-lifecycle): accessors-fresh-state passed in
  `results-phase3-slice1/report.json` and the slice-1 review rerun;
  accessors-lifecycle in slice 3 + this rerun. Pass.
- `setting:canonical` (canonical-on, canonical-last-write): slice 3 + this
  rerun, pass.

Both deliberate non-flips verified correct: `fn:reset_rules` additionally
carries `annotation-fn-reset-clears`/`head-fn-reset-clears` and
`setting:persistent` carries `static-graph-facts-on`/`-off` — none of the
four has run against the rewrite (absent from all three slices' reports).
Count verified mechanically: **44 cased + 8 equivalent = 52 rows** — the
8/52 (15.4%) claim stands.

## Design bars (AC-5) and the no-ADR-0003 claim

The facade still wraps exactly one `EngineState`; the whole slice is three
additions inside ADR 0002's shape — two pure functions over the state
(`_state.reset`, `_state.reset_rules`), one guard in `_reason_again`, one
view method (`get_dict`). No hidden cross-run state (probe P1/P6's
cross-program families run through the same explicit fields the tests can
see), no second core, no dead scaffolding — session 17's `Program.reset_*`
stubs and again-dispatch are now consumed. The no-ADR-0003 argument is
honest: ADR 0002 Decision 2 (numba idioms not transcribed when the
observable is preserved) and Decision 5's exact precedent (the
unregistered-annotation-function NameError "reproduced as an explicit raise
at the same decision point") already license the explicit
`TypeError('List() argument must be iterable')`; nothing about the
state/step/trace description moved.

## Hygiene

- `git -C oracle/pyreason status --porcelain` empty; HEAD at
  `e1a94af33e1f...`, equal to `oracle/PIN`. Oracle byte-clean.
- No dependency changes: `git diff ef2fc01..HEAD -- pyproject.toml uv.lock`
  empty; no installs performed by this review.
- The author's amended-commit wrinkle is resolved in the final history:
  `git ls-files 'results*'` is empty (nothing under any results dir is
  tracked; `results/` itself is wholly gitignored), the three commits'
  trees carry only the files their messages name, and the branch is linear.
- Banked evidence untouched: `results/`, `results-phase3-slice1*/`,
  `results-phase3-slice2*/`, `results-phase3-slice3/` consumed read-only
  (report.json mtimes predate this review's work); the review rerun went to
  the fresh `results-phase3-slice3-review/`, now gitignored like its
  slice-1/2 counterparts.
- No security framing in any reviewed commit, artifact, or this review
  (scanned mechanically).
- `git status` clean at close (after this commit).

## Verdict

**PASS.** Zero findings. The state-lifecycle slice is a faithful
reproduction of the pinned lifecycle semantics — verified by source
read-through, by re-derived evidence (209-test fast tier, 14/14 case rerun,
14/14 + 14/14 digest cross-checks), by empirical reproduction of all five
named oracle quirks against the installed oracle, and by 31
reviewer-constructed probe observations across the seams the committed
cases leave open, all identical cross-engine. Five surface flips and two
non-flips all correct at 8/52. No fixes applied because none were needed;
no DIV records because no committed-case or probe mismatch exists.
