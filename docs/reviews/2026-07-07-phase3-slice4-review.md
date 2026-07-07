<!-- doccode: pyreason-rewrite-docs-reviews-2026-07-07-phase3-slice4-review -->
# Phase 3, slice 4 — the knob-arm semantics (independent review)

- session: 19 · 2026-07-07 · reviewer-fixer packet (no shared context with the author)
- scope reviewed: the full diff `8774b1d..edbb3a6` as a coherent whole, graded
  against the pinned source at `e1a94af33e1f` and the slice-4 packet spec
- verdict: **packet PASSES with one rewrite-defect found and fixed by review**
  (fp-mode `get_dict` failed to reproduce a pinned fp-variant defect), one
  low-severity residual recorded (fp+infer_edges crash-payload difference),
  and two documentation corrections (ADR 0003 scope sentence, .gitignore
  placement). Independent rerun: **17/17 pass** into
  `results-phase3-slice4-review/`; fast tier **220 passed** (author's 219 + 1
  review seam test); digest cross-check: rewrite b1 digests equal the banked
  session-15 sweep's oracle a1 digests on **17/17** cases, probe for probe.

## Findings, by severity

### F1 (medium, FIXED): fp-mode `get_dict` did not reproduce the pinned fp variant's stale-edge defect

The pinned fp variant's `get_dict` unpacks each edge trace row's component
into a variable it never reads and indexes with the stale `edge` left over
from the init loop (`interpretation_fp.py:852-854`), so **every edge trace
row lands on the LAST edge in `self.edges`**, whatever its true component.
The default variant's `get_dict` is correct — this is an fp-only oracle
defect. The rewrite shipped one correct `get_dict` for both schedules, i.e.
it silently FIXED the oracle on the fp arm — under AC-6, a rewrite-defect
(matching the pin including its quirks is the meaning of correct).

- Found by review probe `probe-fp-getdict-edges` (fp_version=true, an edge
  fact `rel(A,B)`, graph edges [(A,B),(B,C)]): the installed oracle banks
  `rel` on `('B','C')` at t=0/t=1 with `('A','B')` empty; the pre-fix
  rewrite banked the inverse. Harness verdict: `divergent — probes: dict`.
- Not a committed-case mismatch (no committed fp case probes
  `interpretation_dict`), so per AC-6 no DIV record; fixed instead.
- Fix: `src/pyreason/_interpretation.py::Interpretation.get_dict` — in
  `fp_mode`, edge trace rows stamp `self.edges[-1]`; node rows keep their
  true component. Docstring names the pinned lines and why an edge row with
  no edges cannot arise.
- Pinned by new seam test
  `test_fp_get_dict_lands_edge_rows_on_the_last_edge` (accurate `proves:`),
  and the probe rerun after the fix: `probe-fp-getdict-edges` → **pass**.
- ADR 0003 amended: its "only reason/container-plumbing/init differ"
  sentence understated the pinned variant diff — `get_dict` (on the
  compared surface via the harness dict probe) and the gym-facing
  `query`/`delete_*`/`add_edge` methods also differ. `query` takes the
  t-keyed shape and different miss-returns at the pin but is unreachable
  through the pinned public `pyreason.py` surface — named, not transcribed.

### F2 (low, recorded): fp + infer_edges — both engines crash at the same seam, with different KeyError payloads

Review probe `probe-fp-infer-edges` (fp_version=true, an `infer_edges` edge
rule): the **pinned oracle itself crashes** — numba typed-dict lookup raises
`KeyError()` (payload-less) inside fp `reason`, from the per-timestep edge
world lookup for an inferred edge. The rewrite crashes at the same logical
seam (`_add_edge`'s existing-edge branch,
`interpretations_edge[t_e][('A','B')]`) but Python's KeyError carries the
key: `KeyError(('A', 'B'))`. Same exception type, same reasoning outcome
(reason() raises; nothing banks), different message text — a steps-form
committed case comparing raise records would diverge on the message.

- This is oracle-bug-candidate territory (fp + infer_edges is broken at the
  pin — the author's defect list gains a seventh entry) and sits outside
  this slice's 17 cases and all ten flipped rows.
- Recorded, not absorbed and not patched around: matching a numba-internal
  empty payload byte-for-byte would mean raising a bare KeyError at a
  guessed site; whether that arm is ever cased (and with what message
  canonicalization, cf. the run-varying-message precedent in
  harness/capture.py) belongs to the edge-rule slice and, if cased, to
  operator adjudication.

### F3 (low, FIXED): documentation accuracy

- ADR 0003's variant-diff sentence corrected (see F1).
- `.gitignore`: the author appended `results-phase3-slice4/` under the
  caches section; moved to the harness-artifacts block and
  `results-phase3-slice4-review/` added per the slice convention.

No other findings. No security framing anywhere in the diff. Commit
messages match what the commits contain. The author's interrupted-session
note checks out: every hunk in `8774b1d..edbb3a6` is accounted for by the
packet (8 files: engine, program, state plumbing, tests, ADR, report,
surface, gitignore) — nothing foreign.

## ADR 0003 one-engine assessment (AC-5)

**The one-engine claim stands.** Verified independently, not from the ADR's
own evidence:

- **Parallel variant**: `interpretation_parallel.py` at the pin is
  byte-identical to `interpretation.py` after normalizing the single
  decorator flag (`diff <(sed 's/parallel=True/parallel=False/' …)` — empty;
  the one hit is `interpretation_parallel.py:241`). A knob whose entire
  source diff is a numba parallelization flag selects no schedule; the
  rewrite's `fp_mode = fp_version and not parallel_computing` is the exact
  pinned precedence (program.py:42-47).
- **fp variant**: my own AST-normalized function-by-function diff of the
  pinned default vs fp modules: 33 units line-identical (every
  grounding/threshold/satisfaction helper, `annotate`,
  `check_consistent_*`, `resolve_inconsistency_*`, `float_to_str`, …); the
  differing units are exactly `reason` (orchestration), `__init__`/init
  shape, `_start_fp` (no num_ga extension), `_add_*`/`_update_*` (num_ga
  plumbing dropped, one blanket try/except dropped, two presence guards
  added), `_ground_rule` (num_ga pass-through only), plus the
  `get_dict`/`query`/gym-method diffs now named in the ADR. So the pinned
  observable fp differences force exactly one alternate orchestration and a
  state-shape parameter — which is what was built: the rewrite's semantic
  operations exist once, take their world dicts as parameters, and
  `reason_fp` is the only new loop. **Not a second engine in disguise**: no
  semantic body is duplicated (checked the new `reason_fp`,
  `_fp_copy_forward`, `_fp_apply_rule_conclusion` against `reason` — they
  drive the same `_ground_rule`/`_apply_fact`/`_update_*`/`resolve_*`/
  `annotate`/`_add_*` functions the default schedule drives).
- **Transcription fidelity**: `reason_fp` line-checked against
  `interpretation_fp.py:251-807`: per-pass timestep sweeps with the
  `t == tmax` post-iteration exit (hence the pinned tmax=-1 non-termination),
  copy-forward semantics (`fp_cnt == 0` recreate + fill-missing-labels rule,
  persistent=all vs static-only), per-timestep convergence-counter resets
  (so only the last swept timestep's fact changes join the pass's
  convergence data — quirk reproduced and named), the delta-0 enqueue
  clearing the accumulated update flag, the sticky-update
  `max_t_changes` bump semantics in the application phase (bumps ride the
  accumulated flag, never the resolve branch), unconditional
  `changes_cnt += changes` from `_add_edges` even in delta_bound mode (pin
  quirk, reproduced), full queue drains between passes, pass-level perfect
  convergence, `max_t_changes + 1` return. The four named deviations
  (dropped `max_rules_time`, sequential per-rule conclusion appends, num_ga
  gating, the KeyError guard) all verified output-invisible; I confirmed
  `max_t` and `max_rules_time` are write-only at the pin (grep: writes at
  fp:253/256/569/611/639, zero reads).
- **Stamping defect**: program.py:34-38 assigns the specific-label maps
  onto the default `Interpretation` class object only; `InterpretationFP`
  and `InterpretationParallel` keep their empty class defaults
  (interpretation.py:59-61 pattern in each module). The rewrite reproduces
  the fp side exactly. One deliberate deviation on the parallel side: the
  rewrite's parallel arm passes the REAL maps where the pin's parallel class
  holds empty ones. Verified invisible on the pinned public surface:
  (a) `num_ga` (the only state the seeding writes beyond worlds/maps) is
  consumed nowhere in `pyreason.py`; (b) the graphml parser builds each
  specific-label list and its graph-attribute facts in the same loop, and
  graph-attribute facts precede user facts in the queue, so the fact-built
  predicate maps carry identical content AND order; (c) change/`updated`
  accounting in `_update_*` is identical for a seeded [0,1] entry vs a
  just-created one. Probe `probe-parallel-attrs` (attribute-bearing nodes
  and edges + IPL under parallel_computing=true) — pass. ADR names this
  deviation; assessment: honest.

## The six claimed oracle-defect reproductions — verified

1. **Specific-label stamping defect** — CONFIRMED (program.py:34-38 class
   assignment reaches only the default class; upstream `#TODO` on :34).
2. **Dead `abort_on_inconsistency`** — CONFIRMED: `grep -rn abort
   oracle/pyreason/pyreason/scripts/` → 0 hits; the name lives only in
   `_Settings`. The rewrite's dead-knob test holds both arms' traces equal.
3. **`update_mode` accepts any string** — CONFIRMED: setter type-checks
   `isinstance(value, str)` only (pyreason.py:421-432); every consumption
   is `update_mode == 'override'` (interpretation.py:316/391/446/493/520 +
   3 more).
4. **Inverted intervals under `inconsistency_check=False`** — CONFIRMED at
   source: the override arm `set_lower_upper(bnd.lower, bnd.upper)` plus the
   IPL complement `lower = max(l, 1-u'); upper = min(u, 1-l')` with no
   ordering check (interpretation.py `_update_node` IPL block) yields
   sick=[0.8, 0.09999999999999998] from the case's inputs; banked
   inconsistency-ipl-override reproduces it, as do my
   probe-fp-incons-override and probe-multi-ipl-override (both pass — the
   inversion carries identically through the fp path and multi-pair IPL).
5. **`reason()` mutates public `atom_trace`** — CONFIRMED
   (pyreason.py:1584-1585: `if not settings.store_interpretation_changes:
   settings.atom_trace = False`), pinned by the store-off cases' live knob
   readback.
6. **fp non-termination on `timesteps=-1`** — CONFIRMED by construction:
   the fp sweep's only exit is `if t == tmax` (interpretation_fp.py:272-273),
   never true for tmax=-1; the transcription shares the shape. Correctly
   labeled by-construction (not exercised — a run would hang).

Review adds a seventh: **the fp `get_dict` stale-edge defect** (F1) and an
eighth observation, **fp + infer_edges crashes at the pin** (F2).

## Discriminating probes (overfitting hunt) — 16 probes, both engines

Ad-hoc cases (scratchpad, not committed) through the same harness,
PYTHONHASHSEED=0, oracle-env vs scripts/rewrite-python:

| probe | seam it pins beyond the 17 cases | verdict |
|---|---|---|
| probe-fp-getdict-edges | fp dict view over edge trace rows | **divergent → FIXED → pass** |
| probe-fp-incons-resolve | IPL + same-pred conflicts through the fp fact loop | pass |
| probe-fp-incons-override | inconsistency_check=false on the fp path (inverted interval rides) | pass |
| probe-fp-update-override | update_mode=override inside fp fact/application arms | pass |
| probe-fp-static-attrs | static_graph_facts + persistent=false under fp copy-forward | pass |
| probe-fp-store-off | store-off gating + atom_trace flip + accessor refusal on fp | pass |
| probe-fp-conv-delta | delta_interpretation convergence on the fp pass loop | pass |
| probe-fp-delta0 | delta-0 rule chain (the update-flag clear quirk) | pass |
| probe-fp-infer-edges | edge-adding rule on fp | **error in BOTH engines** (F2: pin crashes KeyError(), rewrite KeyError(('A','B')) at the same seam) |
| probe-edge-incons-resolve | inconsistency arising on an EDGE, resolve arm | pass |
| probe-edge-incons-override | edge inconsistency forced through | pass |
| probe-multi-ipl-resolve | one predicate in TWO IPL pairs, resolve fan-out | pass |
| probe-multi-ipl-override | two IPL pairs under override | pass |
| probe-parallel-attrs | parallel + attribute-bearing nodes/edges + IPL (the seeding deviation) | pass |
| probe-ground-mixed-on | rule mixing ground-constant and variable clauses, knob on | pass |
| probe-ground-mixed-off | same rule, knob off | pass |

Two packet-suggested probes could not ride the harness and were verified by
code read instead: (a) *junk update_mode set after a first reason* — the
knob is baked into the Interpretation at construction in BOTH engines (the
pin builds the interpretation per plain reason() and reuses it on
again=True; the rewrite's session-18 lifecycle plumbing mirrors this), so a
between-reason knob write is equally inert in both; (b) *store-off then
atom_trace re-enable* — same argument; the flip is a settings write at
reason() entry, and the next plain reason() re-reads whatever the settings
hold, identically on both sides. One residual seam named for the
output-file slice: under verbose=true with delta convergence, the pinned fp
convergence print interpolates a `t` that the application loops REBIND to
the last conclusion's timestep; the rewrite prints its sweep-exit `t`.
Verbose output is not compared by any committed case yet (output_file cases
are a named future family); flagged so the output-file slice authors probe
it.

## Independent rerun + digest cross-check

- Fast tier: `uv run pytest -m "not e2e"` → **220 passed** (author's 219 +
  the review's fp-get_dict seam test), surface-inventory gate green.
- 17-case rerun (post-fix): `PYTHONHASHSEED=0 uv run python -m harness.run
  --cases <staged-17> --engine-a oracle-env/bin/python --engine-b
  scripts/rewrite-python --results results-phase3-slice4-review` →
  **ALL PASS (17 cases)**, fresh untracked results dir.
- Digest cross-check: my rerun's rewrite (b1) per-probe digests vs the
  banked session-15 sweep's ORACLE artifacts (`results/<case>/a1.json`) —
  **17/17 cases match on every probe digest**, tying the rewrite to the
  sweep of record, not just to today's oracle run.

## surface.md — ten flips verified row-by-row

Every case in every flipped row's `cases` field traced to a banked passing
oracle-vs-rewrite run: `persistent-off/on` and `canonical-on/last-write` in
`results-phase3-slice3` AND `results-phase3-slice3-review` (session 18,
both runs pass); the seventeen slice-4 cases in `results-phase3-slice4`
(author) and re-confirmed by my `results-phase3-slice4-review`. Rows:
fn:add_inconsistent_predicate, setting:abort_on_inconsistency,
setting:persistent, setting:inconsistency_check, setting:static_graph_facts,
setting:store_interpretation_changes, setting:parallel_computing,
setting:update_mode, setting:allow_ground_rules, setting:fp_version. No
other row's status changed in the diff (verified against the full diff, not
the report). Count: 52 rows, 18 equivalent — **18/52 correct**. One honesty
note, not a flip-blocker: the fp_version row's equivalence is judged on its
two cases per the stated convention; the fp get_dict arm (now fixed) and the
fp+infer_edges crash arm (F2) sat outside them — the former is now also
pinned by a fast-tier seam test, the latter is recorded here.

## Tests

The ten author seam tests: read line-by-line; each `proves:` docstring
matches what the test asserts, all assert at the module-global facade (the
harness seam), the dead-knob test isolates its second EngineState, and the
fp-schedule test pins the four pinned fp signatures (pass counters, event
order, duplicated groundings, frame row order) rather than incidental
values. The review adds one (F1). Fast tier fully green.

## Hygiene

- No installs, no dependency changes: diff touches neither `uv.lock` nor
  `pyproject.toml`; no new env anywhere.
- Oracle tree byte-clean: `git -C oracle/pyreason status --porcelain` empty,
  HEAD = `e1a94af33e1f…` = oracle/PIN.
- Banked results dirs unmodified: the digest cross-check reads
  `results/<case>/a1.json` and matches — the banked sweep is intact;
  `git ls-files 'results*'` → 0 tracked files; review artifacts went to the
  new gitignored `results-phase3-slice4-review/` and the session scratchpad.
- Preflight doctor: 10/10 at review start.
- `git status` clean at close; hooks not bypassed.

## Verdict

**Packet passes.** The knob-arm slice is semantically faithful to the pin
on every arm the cases and my probes reached, the fp schedule is an honest
single-core transcription (AC-5 upheld), the evidence reproduces
independently, and the one real gap review found (fp get_dict) is fixed,
tested, and re-proven against the installed oracle. F2 rides to the
edge-rule slice as a named residual.

## Repro

```
# fast tier (220)
uv run pytest -m "not e2e"

# the 17-case rerun (stage the committed cases, then run)
mkdir -p /tmp/slice4-review-cases && for c in abort-on-inconsistency-default \
  abort-on-inconsistency-on inconsistency-ipl-resolve inconsistency-ipl-override \
  allow-ground-rules-off allow-ground-rules-on update-mode-default \
  update-mode-override update-mode-junk-string store-off-accessors \
  store-off-atom-trace-flip fp-version-on parallel-computing-default \
  parallel-computing-on parallel-fp-precedence static-graph-facts-on \
  static-graph-facts-off; do cp harness/cases/$c.json /tmp/slice4-review-cases/; done
PYTHONHASHSEED=0 uv run python -m harness.run --cases /tmp/slice4-review-cases \
  --engine-a oracle-env/bin/python --engine-b scripts/rewrite-python \
  --results results-phase3-slice4-review-repro

# digest cross-check (rewrite b1 vs the banked sweep's oracle a1), per case:
# python3 -c 'import json; a=json.load(open("results/<case>/a1.json"))["digests"]; \
#   b=json.load(open("results-phase3-slice4-review-repro/<case>/b1.json"))["digests"]; \
#   assert a==b'
```
