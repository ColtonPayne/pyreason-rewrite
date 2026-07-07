# Session 6 — the settings-only knobs: fp engine, update semantics, ground rules

Date: 2026-07-06 (same sitting as sessions 0–5)

## Verdict

Session 5's NEXT executed in full, with no capture surgery — exactly as
predicted: six cases took the corpus 22 → 28 across the three settings-only
reasoning knobs (the fp-engine case ARM-screened before authoring was final),
oracle-vs-oracle ALL PASS twice (post-authoring and post-review-fix; repeats
green both times), the review gate confirmed 0 High / 0 Medium / 1 Low (fixed
in-session), and the board stands at 24/52 rows `cased` with
`setting:fp_version`, `setting:update_mode`, and `setting:allow_ground_rules`
flipped.

## Evidence

- **The ARM screen** (session 5's named precondition): `fp_version=true` on
  hello-world inputs through `harness.capture` in the oracle env — first
  capture ~62s (the fp path's one-time numba compile), repeat ~7s with the
  cache warm, digests identical across runs. The fp case is `runtime_class:
  standard` for that fresh-env compile cost.
- **fp-version-on** pins the fp engine's own contract (`program.py` selects
  `InterpretationFP` only when parallel_computing is off): node frames,
  node/edge traces, `get_time`, and the knob's live value. Authoring-time
  comparison against the banked hello-world artifacts (hedged as such in the
  case record — the harness judges the case fp-vs-fp only): same final bounds,
  but different fp-counter values, event order, duplicated atom-trace
  groundings, and last-frame row order — a pinned engine-variant asymmetry.
- **The update-mode trio** pins both bound-update semantics and the
  unvalidated-string class: two same-atom facts (`wide(A):[0.2,1]` then
  `[0,0.8]`) intersect to `[0.2,0.8]` under the default — satisfying a rule's
  `[0.1,1]` clause bound so `derived(B)` appears — while `override` replaces
  wholesale to `[0,0.8]` (`set_lower_upper` vs `world.update` at the pin),
  fails the clause, and converges a step earlier. `update_mode='junk'`
  digest-equals the default twin on all four reasoning probes (verified at
  authoring; every consumption site in all three engines is a string-equality
  against `'override'`) and differs only in the knob readback.
- **The allow-ground-rules pair** pins `_ground_rule`'s constant-in-node-set
  short-circuit: with `popular(Mary)` and `popular(Justin)` both true, the
  clause `popular(Mary)` binds Mary alone when the knob is on
  (`influenced(John)` only) but is an ordinary variable when off
  (`influenced(John)` and `influenced(Cat)`) — one vs two derivations on
  identical inputs.
- **The runs:** `uv run python -m harness.run --cases harness/cases --engine-a
  oracle-env/bin/python` → ALL PASS, 28 cases × 4 fresh-process captures,
  `PYTHONHASHSEED=0`, twice; the post-review-fix re-run is the
  verdict-of-record, banked as
  [session-6-oracle-vs-oracle.json](session-6-oracle-vs-oracle.json).
- **Review gate:**
  [docs/reviews/2026-07-06-settings-knob-cases.md](../reviews/2026-07-06-settings-knob-cases.md)
  (one focused Opus reviewer — the scaled-down form again; raw committed
  beside). The reviewer re-derived the junk-twin digest equality from the
  banked artifacts, confirmed override non-vacuous by absolute pinned values,
  traced the ground-rule mechanism to the pinned source, and verified the
  board flips exact. The Low — the fp purpose stating the fp-vs-optimized
  observation without the verified-at-authoring hedge — fixed in-session.
- **Gates:** fast tier 61 passed; links gate green on every commit; preflight
  10/10 at session start.
- **Board:** `docs/surface.md` — 24 rows `cased` (setting:fp_version,
  setting:update_mode, setting:allow_ground_rules flipped), 28 `uncovered`;
  `equivalent` still 0/52 — no rewrite exists, `cased` marks harness coverage
  only.

## Committed

- `d685af2` — harness: settings-only knob cases — fp engine, update-mode
  trio, ground-rule pair.
- `2b8948a` — docs: board flips for the three settings-only knobs; bank the
  28-case run.
- `b24ac33` — harness: review finding fixed; report; the re-banked
  verdict-of-record.
- (this commit) — ledger: session 6 banked.

## NEXT

Case the load-time graph knobs — settings-only again, no capture surgery
expected, all observable through existing frame/trace probes over an
attribute-bearing graph: a `graph-attr-parsing-off` / on pair
(`setting:graph_attribute_parsing` — off skips attribute-to-fact conversion,
so the graph-attribute facts and their trace rows vanish), a
`static-graph-facts-off` / on pair (`setting:static_graph_facts` — the
staticness stamped onto generated graph-attribute facts, observable with
persistent left false as bounds that do vs don't survive the per-timestep
reset), and a `save-graph-attrs-to-trace-on` / off pair
(`setting:save_graph_attributes_to_trace` — trace contents only, never derived
bounds). Run oracle-vs-oracle, flip `setting:graph_attribute_parsing`,
`setting:static_graph_facts`, and `setting:save_graph_attributes_to_trace`,
bank the run.

## Deviations

- Session 5's NEXT named an update-mode *pair*; a third case
  (`update-mode-default`, same inputs, knob untouched) was authored so the
  junk-string twin-equality claim is a mechanized digest comparison against a
  committed baseline rather than an eyeballed one — it also covers the row's
  `default-intersection` class.
- The review gate again used the umbrella's scaled-down single-focused-reviewer
  form for a contained case-only extension (the charter's ≥2-reviewer form
  names complete features); report committed anyway.

## Asks queued

None.

## Divergences

None opened — no rewrite exists. The fp engine's trace asymmetry against the
optimized engine on identical inputs is a pinned oracle behavior recorded on
the board, an adjudication candidate per AC-3's both-not-either rule when
equivalence runs begin.

## Idea seeds

- The fp-vs-optimized trace asymmetry sharpens the single-core question AC-5
  poses: one rewrite core cannot natively reproduce *both* knob positions'
  trace shapes (fp-counter semantics, event order, duplicated groundings), so
  the `fp_version` surface will need an operator adjudication — emulate each
  engine's trace quirks per knob position, or declare one canonical trace
  shape an intentional divergence. `fp-version-on` and `hello-world` are the
  prepared reproducer pair.
- The probe-raise exit-taxonomy channel (session 4's deferred M2) remains the
  gating piece before oracle-vs-rewrite runs.
- `REASON_ARGS` is still hand-kept (sessions 4–5's seed: derive it from the
  pinned signature the way `SETTINGS_KNOBS` now is).
- After the load-time knob family, the biggest capture gap is the get-family
  accessors (`get_rules`, `get_logic_program`, `get_interpretation`) — each
  returns a live object no existing probe kind can fingerprint; a
  `parse_fingerprint`-style reduction per accessor is the likely shape.
