# Review — get_setting probe + edge-rule / store-off case trio

## Scope

The working session's three commits, `f2d17a5..038a8d9`:

- `b7e7374` — a `get_setting` probe kind in `harness/capture.py` (reads one
  named knob off the engine's module-global `settings` object; refuses
  `allow_raise`; shares `settings_knob_guard` with `apply_settings`) plus fast
  tests in `tests/test_capture_validation.py`.
- `3787f3b` — three case files: `harness/cases/edge-rule-frames.json`,
  `store-off-accessors.json`, `store-off-atom-trace-flip.json`.
- `038a8d9` — `docs/surface.md` board edits (two rows flipped to `cased`, case
  ids appended) and `docs/ledger/session-5-oracle-vs-oracle.json` (the banked
  22-case ALL PASS self-proof).

## Method

Read in full: `harness/capture.py`, `harness/run.py`, `harness/compare.py`, the
three new case JSONs, the changed test file, and every touched `surface.md`
row. Cross-checked every pinned claim against the oracle source at the pin —
`oracle/pyreason/pyreason/pyreason.py` (`reason`/`_reason` 1497-1642, the
atom_trace flip at 1584-1585, the four accessor asserts at 1652/1666/1682/1698,
the `_Settings` class 60-484 and the `atom_trace`/`store_interpretation_changes`
properties + setters) and `oracle/pyreason/pyreason/scripts/utils/filter.py`
(the edge-frame component-tuple reconstruction, 62-117).

Critically, I did **not** rely on the self-proof "ALL PASS" alone (it proves
only reproducibility, not that a probe observed anything meaningful). I read the
**actual banked artifacts** under `results/` for all three new cases and
confirmed each pinned observation is the real oracle output:

- `results/edge-rule-frames/a1.json` — `edges-trusted` is a 3-frame list: t=0
  `{"columns":["component","trusted"],"rows":[]}` (empty branch), t=1 and t=2
  each carry `[["John","Mary"],[1,1]]` and `[["John","Justin"],[1,1]]` (tuple
  branch). Both `filter.py` branches genuinely execute; the rule fires.
- `results/store-off-accessors/a1.json` — all four accessor probes bank
  `AssertionError`; `trace-node-store-off` and `trace-edge-store-off` carry the
  identical `...to save rule trace` message, `nodes-store-off` /
  `edges-store-off` their own messages.
- `results/store-off-atom-trace-flip/a1.json` — `atom-trace-before` true,
  `atom-trace-after` false, `store-before`/`store-after` both false.

The engine was not run by me (no engine env, oracle is read-only); the banked
artifacts are the evidence.

## Verdict

The trio is substantially sound. Every case pins a real, non-vacuous oracle
behavior, and I found **no false-pass** (the worst defect class) — every probe's
banked observation would genuinely diverge if a rewrite behaved differently.
Findings below are one **Medium** harness-robustness issue and three **Low**
claim-precision / test-gap notes.

---

## Medium

### M1 — `settings_knob_guard` requires each knob to be a `property` descriptor on `type(pr.settings)`; a rewrite exposing the same public knob as a plain attribute converts a value-divergence into a harness `error`

`harness/capture.py:272-278`:

```python
def settings_knob_guard(pr, knob: str) -> None:
    if not isinstance(getattr(type(pr.settings), knob, None), property):
        raise ValueError(f"unknown settings knob: {knob!r}")
```

`run_probe` (`capture.py:284-286`) calls this guard *before* reading the knob,
so the read only happens when the knob is a Python `property` on the settings
**class**. Verified against the oracle: `settings = _Settings()` (pyreason.py:484)
and `atom_trace`/`store_interpretation_changes` are `@property` with setters, so
the guard passes and the three new cases work.

The defect is cross-engine: the harness's job is oracle-vs-rewrite. If a rewrite
exposes the identical public surface (`pr.settings.atom_trace` reads/writes the
knob) but implements it as a dataclass field, a plain instance attribute,
`__slots__`, or `__getattr__` — none of which is a `property` on the type — the
guard raises `ValueError`. Because a `get_setting` probe is forbidden from
carrying `allow_raise` (correctly), that `ValueError` propagates as a capture
failure (exit 1), so `judge_case` reports the case as **`error`**, not `pass`
and not `divergent`.

Failure scenario: rewrite force-flips `atom_trace` to a *different* value than
the oracle (a genuine cross-engine divergence the `store-off-atom-trace-flip`
case exists to catch), but also stores `atom_trace` as a plain attribute. Every
`get_setting` probe errors on the guard, the case comes back `error`, and the
real value-divergence is hidden behind the structural error label instead of
being reported as `divergent`. All three new cases (and every future
`get_setting`/settings case) are exposed to this.

This is **not a false pass** — it surfaces as `error`, which an operator
investigates — so it is Medium, not High. But it makes the harness depend on the
oracle's *descriptor mechanism* rather than the *public knob value*, which is the
only thing equivalence should compare. It predates this diff (the guard lived in
`apply_settings`), but `b7e7374` factored it into a shared helper and put it on
the read path, and the three new cases now depend on it.

Fix: decouple the guard from `property`. Prefer an explicit allowlist of known
knob names derived from the `setting:` rows in `docs/surface.md` (which already
enumerate the 18 knobs) and check membership; or, at minimum, accept any knob the
*instance* actually exposes (`hasattr(pr.settings, knob)` plus the allowlist to
still catch typos). Either keeps the typo-catch while comparing values across
engines with different internals.

---

## Low

### L2 — `surface.md` note "empty vs non-empty frames have divergent column shapes" is imprecise: the observed column shapes are identical

`docs/surface.md`, `fn:filter_and_sort_edges` note. The banked probe output
(`results/edge-rule-frames/a1.json`) shows the empty t=0 frame and the non-empty
t≥1 frames have the **same** columns `["component","trusted"]` — which is the
whole point of `filter.py`'s `else` branch (line 115) fabricating
`['component', *labels]` to match the reconstructed tuple branch (line 113). What
actually differs between the two frames is the *row content*, not the column
shape; the "divergent column shapes" phrasing (pre-existing text) describes the
source's *would-be* divergence before normalization, not the observed output. A
reader could take it to mean the probe compares differing column shapes, when in
fact it pins that the empty frame's columns are *normalized to match*. The added
clause ("both branches pinned in one probe … t=0 empty, t≥1 tuple components") is
accurate. Fix: reword to "empty and non-empty frames take different
reconstruction branches (`filter.py:109-115`) but are normalized to the same
`[component, *labels]` columns; the empty-frame normalization is what
`edge-rule-frames` pins."

### L3 — "all four [accessors] pinned" reflects four probes but only three distinct engine assert sites

`store-off-accessors.json` purpose and the `setting:store_interpretation_changes`
note say all four accessors are pinned. Verified in the artifact:
`trace-node-store-off` and `trace-edge-store-off` both invoke
`pr.get_rule_trace(interpretation)` (`capture.py:293-296`), which asserts at
pyreason.py:1666 *before* returning the `(node, edge)` tuple, so both probes bank
the byte-identical `AssertionError(...to save rule trace)`. Three distinct assert
sites are actually pinned (get_rule_trace, filter_and_sort_nodes,
filter_and_sort_edges), not four; the node/edge pair is redundant (with store off
there is no node-vs-edge behavior to distinguish — the assert precedes any
tuple). The purpose does acknowledge "get_rule_trace (node and edge frames)", so
this is not false, only slightly overstated. Harmless redundancy, no masking.
Fix: say "three assert sites across four probes" or drop one of the two
get_rule_trace probes.

### L4 — test coverage gap: `get_setting` validation is unit-tested only in the one-step form, and the knob-string guard is tested only for the missing-key case

`tests/test_capture_validation.py`. `test_get_setting_probe_requires_a_knob_string`
exercises only a *missing* `knob` key; the guard also rejects `knob: ""` and
`knob: 123` (`capture.py:87`) but neither is asserted. And no test drives a
`get_setting` probe *inside a step* — the live shape used by
`store-off-atom-trace-flip` — though it is covered transitively because
`_probe_list_fault` is form-agnostic and shared. The `proves:` docstrings all
match what their tests assert (I checked each new one against its body). Low
because the transitive coverage is real; still, a direct steps-form
`get_setting` validation test and an empty/non-string-knob assertion would close
the gap the docstring ("without a named knob") already implies.

---

## What I checked and found sound

- **No false pass anywhere in the trio.** Each probe's banked value would diverge
  under a differently-behaving rewrite: the store-off accessors bank
  type+message (a rewrite that returns frames, raises a different type, or
  reworks the message diverges); the atom_trace flip banks true→false (a rewrite
  that doesn't flip, or flips store too, diverges); the edge frames bank the
  empty-frame columns and the reconstructed tuples (a rewrite with a different
  empty-frame shape or a non-tuple component diverges).
- **The atom_trace-flip pin is source-accurate and correctly isolated.**
  pyreason.py:1584-1585 flips `settings.atom_trace = False` only when store is
  off, inside `_reason`, and the `atom_trace` setter (321-332) does not couple to
  store — so `apply_settings` accepts `atom_trace: true` while store is off, and
  the flip happens strictly inside `reason()`. Placing `atom-trace-before` on the
  `add_fact` step correctly proves the value is still true after settings
  application *and* after add_fact, isolating the flip to `reason()`. Confirmed
  by the artifact (before=true, after=false; store unchanged false→false).
- **The store-off asserts are source-accurate.** All four accessors assert
  `settings.store_interpretation_changes` (1666/1682/1698, and get_rule_trace
  reused by both trace probes); the "save rule trace" message reuse noted in
  `surface.md` is real (1666 vs 1652).
- **The edge rule genuinely fires** (no `infer_edges` needed — `Friends(x,y)`
  binds existing edges that `trusted` annotates), verified in the artifact's
  `trace-edge` and `edges-trusted` frames; both `filter.py` branches execute.
- **`get_setting` schema/dispatch/guard wiring is correct.** It is added to
  `PROBE_KINDS` and to the `INTERP_PROBE_KINDS` partition assertion
  (test line 137); it is a standalone (non-interp) kind, so it is validly placed
  before any reason step (which `store-off-atom-trace-flip` relies on);
  `_probe_list_fault`'s allow_raise-boolean check (line 80) runs before the
  get_setting block, so ordering is safe; the `allow_raise` refusal is correct
  (the blanket catch would otherwise bank the guard's own `ValueError` as engine
  behavior). `test_probe_kinds_cover_the_capture_dispatch` guards the
  whitelist/dispatch agreement.
- **`get_setting` reads the same module-global object `reason()` mutates.** `pr`
  is the pyreason module; `pr.settings` is the module-global `_Settings()` that
  `_reason` mutates via the property setter — so the probe observes the live,
  post-flip value, not a stale copy.
- **The board flips are honest.** Rows are marked `cased` (a case touches the
  item), never `equivalent`; the self-proof ledger is labeled oracle-vs-oracle
  and proves reproducibility only, so nothing overclaims cross-engine
  equivalence. Counts reconcile: 21 `cased` + 31 `uncovered` = 52; two rows
  flipped this session (filter_and_sort_edges, store_interpretation_changes). No
  header fraction needed updating (coverage is measured over
  equivalent-or-adjudicated rows, still 0).
- **No wrapped-vs-bare collision on `get_setting`.** It cannot carry
  `allow_raise`, so its output is always the bare canonical value in both
  engines — never wrapped `{"raised": false, "value": ...}` in one and bare in
  the other.
