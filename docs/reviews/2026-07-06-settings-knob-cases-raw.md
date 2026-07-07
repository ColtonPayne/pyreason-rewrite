# Adversarial review — settings-knob cases (fp-version, update-mode trio, ground-rule pair)

Reviewer: independent adversarial reviewer (no prior session context).
Scope: commits `d685af2` (six new harness cases) and `2b8948a` (docs/surface.md
board flips + `docs/ledger/session-6-oracle-vs-oracle.json`).
Deployment: single operator, own machines, no new privilege boundary — severity
calibrated accordingly.

## Verdict

No false-passes and no material overstatements found. **0 High, 0 Medium, 1 Low**
(the single Low is an observational transparency note, not a defect). The six cases
pin observable, non-vacuous contracts; every purpose, board note, and source-mechanism
claim I checked matched the banked artifacts and the pinned oracle source.

---

## What I verified clean

### 1. update-mode trio — the junk==intersection claim (fully verified)

Banked `a1` digests (`results/update-mode-*/a1.json`):

| probe | default | junk | override |
|---|---|---|---|
| `nodes-wide-derived` | `effad7fa…` | `effad7fa…` (=default) | `52a168d2…` (differs) |
| `trace-node` | `059c853d…` | `059c853d…` (=default) | `21422bfb…` (differs) |
| `time` | `d4735e3a…` (=2) | `d4735e3a…` (=default) | `6b86b273…` (=1) |
| `trace-edge` | `1f75c248…` | `1f75c248…` | `1f75c248…` (empty, shared) |
| `mode-knob` | `intersection` | `junk` | `override` |

- junk digest-equals the default twin on **all four reasoning probes**; only
  `mode-knob` differs, reading back `"junk"` verbatim. Matches the junk-string
  purpose exactly.
- Override is observably different reasoning, not vacuous: default yields
  `wide(A)=[0.2,0.8]` and `derived(B)=[1,1]` at t=1 (`time=2`); override yields
  `wide(A)=[0,0.8]`, **no** `derived(B)`, and converges early at `time=1`. A rewrite
  that mishandled `override` (or that treated `junk` as override) would diverge on
  `nodes-wide-derived`/`time`. The contract is pinned by absolute observed values,
  not by cross-case comparison — so it is non-vacuous even though the harness judges
  each case in isolation.
- Arithmetic in the default purpose checks out: intersection of `[0.2,1.0]` and
  `[0.0,0.8]` = `[0.2,0.8]`, which satisfies the clause bound `[0.1,1.0]`; override's
  `[0,0.8]` has lower `0 < 0.1` and fails it.

Source basis (pinned, read-only): every `update_mode` consumption site is a string
equality against `'override'`:
- `oracle/pyreason/pyreason/scripts/interpretation/interpretation.py` lines
  316, 391, 446, 493, 520 — all `override = True if update_mode == 'override' else False`
  (this is the default `Interpretation` engine the trio actually runs).
- The parallel and fp engines carry the identical idiom
  (`interpretation_parallel.py` 316/391/446/493/520, `interpretation_fp.py`
  396/477/654/704/738), so the board note's generalized "every consumption site"
  is honest.
- Setter `pyreason.py:421-432` type-checks only (`isinstance(value, str)`), so
  `'junk'` is accepted — matching "the setter type-checks only".
- The override branch mechanism (`set_lower_upper` vs `world.update`) is confirmed:
  `_update_node` `interpretation.py:1528-1531` — `if override: set_lower_upper(...)`
  else `world.update(l, bnd)`. The purpose's "set_lower_upper vs world.update at the
  pin" is exact.

### 2. allow-ground-rules pair — one vs two derivations (verified)

Banked `a1` probes:
- ON (`ground-knob=True`): frame1 = `influenced(John)` only.
- OFF (`ground-knob=False`): frame1 = `influenced(John)` **and** `influenced(Cat)`.

This is exactly "one influenced() derivation vs two on identical inputs". Trace the
logic on the graph (`John→Mary`, `Cat→Justin` Friends; `popular(Mary)`,
`popular(Justin)`): ON grounds `Mary` to itself so `Friends(x,Mary)` yields only
John; OFF treats `Mary` as a variable so `popular(VAR)∈{Mary,Justin}` and
`Friends(x,VAR)` yields John (via Mary) and Cat (via Justin). Non-vacuous —
`nodes-popular-influenced` and `trace-node` both diverge under a wrong engine.

Mechanism claim matches the pinned source: the constant-in-node-set short-circuit is
`interpretation.py:861` — `if allow_ground_rules and clause_var_1 in nodes_set:
grounding = numba.typed.List([clause_var_1])`, else the variable-grounding path
`get_rule_node_clause_grounding(...)` (line 864). Matches "_ground_rule short-circuits
when the clause 'variable' is in the node set."

### 3. fp-version-on — pins the fp engine's own behavior; board note consistent

- The case pins the knob (`fp-knob` get_setting = `True`) plus the fp engine's own
  `nodes-popular` frames and `trace-node`. A rewrite producing optimized-style traces
  would diverge on both. Non-vacuous.
- Board note claims, checked against `results/fp-version-on/a1.json` vs
  `results/hello-world/a1.json` (same graph/rule/fact; only `fp_version` flipped):
  - **same final bounds**: both final frames are `{Mary,Justin,John}` all
    `popular=[1,1]`. ✓
  - **frame row order differs at the last step**: fp = `Mary,Justin,John`;
    optimized = `Mary,John,Justin`. ✓ (earlier frames identical.)
  - **different fp-counter values**: `Fixed-Point-Operation` column is `0,0,0,0,0,1`
    (fp) vs `0,1,1,2,2,2` (optimized). ✓
  - **different event order**: fp groups Mary(t0,t1,t2) then Justin then John;
    optimized interleaves per timestep. ✓
  - **duplicated atom-trace groundings**: fp `Clause-2` shows repeated pairs
    (e.g. John: `[["John","Mary"]×3, ["John","Justin"]×2]`); optimized shows
    `[["John","Mary"],["John","Justin"]]`. ✓
  - `time` digest is identical in both (`4e074085…`), and the note does not claim it
    differs. ✓
- Engine-selection precedence confirmed at `program.py:42-47`:
  `if parallel_computing … elif fp_version → InterpretationFP … else Interpretation`.
  Matches "selects interpretation_fp; only reachable when parallel_computing is off."

### 4. Board flips (surface.md) — accurate, not overstated

- Three rows flip `uncovered → cased` with correct case ids: `setting:update_mode`
  → `update-mode-{default,override,junk-string}`; `setting:allow_ground_rules` →
  `allow-ground-rules-{on,off}`; `setting:fp_version` → `fp-version-on`.
- Cased count is now **24/52** (`grep -c "^- status: cased"` = 24; 52 `##` rows),
  matching the commit message's "24/52 rows" (session 5 was 21, +3).
- All six case ids were appended to exactly the spine rows their `surface_items`
  name and that they actually exercise (load_graph, add_rule, add_fact, reason,
  filter_and_sort_nodes, get_rule_trace, get_time, type:Rule, type:Fact, dsl:rule-text,
  dsl:fact-text, setting:atom_trace, setting:verbose). Spot-checks:
  - `filter_and_sort_edges` was **not** given the new cases — correct, none of the
    six probe edges.
  - `get_rule_trace` got all six — correct; each has a `rule_trace_node` probe
    (fp + update-mode trio additionally have `rule_trace_edge`).
- No case claims a `surface_item` it does not exercise (verified per-case probe/knob
  lists against each case's `surface_items`).

### 5. Case-record quality

- Purposes are present-tense and match the artifacts (arithmetic, derivations, knob
  readbacks all reconcile).
- `runtime_class`: `fp-version-on` = `standard` (one-time ~60s numba compile),
  others = `smoke`. Sensible.
- Provenance honest ("spine case against docs/surface.md setting:X <class>";
  fp reuses hello-world inputs with the knob flipped).
- Probe ids unique within each case; all `get_setting` probes name a pinned knob and
  carry no `allow_raise` (validation enforces this).
- Comparison policy is `{"probes": {}}` on all six → exact-by-default
  (`compare.py:83-103`: unnamed probes compare by canonical JSON equality). Correct.
- Ledger `session-6-oracle-vs-oracle.json`: 28 verdicts, all `pass`, self-proof
  (`engine_a == engine_b`), matching the 28 case files and the "ALL PASS" claim.

---

## Findings

### L1 (Low, observational — not a defect): fp cross-engine claim is an authoring-time observation, not harness-enforced

`harness/cases/fp-version-on.json:3` and the `setting:fp_version` board note assert
the fp engine "differ[s] from the optimized engine's on identical inputs … same final
bounds". This comparison is true and consistent with `results/fp-version-on` vs
`results/hello-world`, but the harness never runs it: each case is judged fp-vs-fp
(self-proof today; fp-oracle-vs-fp-rewrite later), so nothing in the case's pass/fail
enforces "fp ≠ optimized." What the case *does* pin is the fp engine's own absolute
trace/frame shape, which is the correct and sufficient contract for a rewrite to
reproduce.

Failure scenario: a reader treats the board row as evidence the *harness proves*
fp≠optimized and skips writing a dedicated cross-knob differential when the rewrite
lands. Mitigating context: the junk-string purpose uses the explicit hedge "verified
digest-equal at authoring," and the fp board note already frames the asymmetry as
something "a single-core rewrite must adjudicate" — so the framing is honest; the only
gap is that the fp *purpose* line states the cross-engine claim as bare fact without
the parallel "verified at authoring" hedge the junk case carries. A one-clause hedge
would make the six records uniform. No correctness impact; safe to leave or tidy at
next touch.

---

## Coverage of the review mandate

All six mandate items exercised: (1) per-probe non-vacuity — clean; (2) update-mode
junk==default digests + source string-equality — clean; (3) ground-rule 1-vs-2 +
`_ground_rule` short-circuit — clean; (4) fp knob+traces + board note vs hello-world —
clean; (5) board flips honesty/count — clean; (6) case-record quality — clean.
