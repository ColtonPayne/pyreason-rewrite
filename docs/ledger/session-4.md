# Session 4 — resume, restart, and the reset family: the corpus learns to sequence

Date: 2026-07-06 (same sitting as sessions 0–3)

## Verdict

Session 3's NEXT executed in full: the capture grew a multi-step step list
(`reason` / `add_fact` / `reset` / `reset_rules` / `reset_settings`, probes after each
step, step outcomes banked as compared data), nine cases took the corpus 10 → 19 across
the resume/restart pair, the reset family, and reset_settings — oracle-vs-oracle ALL
PASS twice (before and after the review fixes; repeats green both times), the review
gate confirmed 1 High + 3 Medium + 3 Low (all fixed except one deferred with rationale),
and the board stands at 19/52 rows `cased` with two pin hypotheses now confirmed.

## Evidence

- **The step list** (`harness/capture.py`): a case may declare ordered steps; each banks
  an outcome record ({"raised": false} or module-qualified exception + message) under its
  id in the artifact's probe map, so a raising op is a compared observation, never a
  capture failure. `allow_raise: true` on a probe records its raise the same way (wrapped,
  so a raise record and a bare value can never be confused). The one-step form is intact.
- **add_fact joined the op set beyond NEXT's literal list because the pin forced it:**
  `_reason` nulls the fact globals on exit, so a bare `reason(again=True)` raises
  `TypeError: List() argument must be iterable` (screened, then pinned by
  `reason-bare-again-no-facts`) — a resume that actually reasons needs a fact added
  between steps.
- **Screened discoveries, all pinned as case data:** `reason(again=True, restart=True)`
  resets `interp.time` beneath the rule trace's earlier events, so the trace-reconstructing
  accessors (`filter_and_sort_nodes`, `get_dict`) raise `KeyError` after it — an
  oracle-bug-candidate once a rewrite exists to diverge (noted on the board's fn:reason
  row). `get_time` after `reset()` with a live program raises AttributeError on
  `None.time` — session 3's board hypothesis, now confirmed; after `reset_rules()` it
  still answers (the interpretation survives) — the observable contrast between the two
  resetters. The restart pair isolates its knob on identical inputs: get_time 3 → 2
  (restart) vs 3 → 4 (continue).
- **The runs:** `uv run python -m harness.run --cases harness/cases --engine-a
  oracle-env/bin/python` → ALL PASS, 19 cases × 4 fresh-process captures,
  `PYTHONHASHSEED=0`, twice (post-authoring and post-review-fix); the re-run is the
  verdict-of-record, banked as
  [session-4-oracle-vs-oracle.json](session-4-oracle-vs-oracle.json).
- **Review gate:** [docs/reviews/2026-07-06-steps.md](../reviews/2026-07-06-steps.md)
  (one focused Opus reviewer — the session-3 scaled-down form again; raw committed
  beside). The High (a probe-less successful reason step banks a vacuous
  {"raised": false} that could mask a divergence — latent, none of the nine triggered
  it) is closed by validation: probes or an explicit `outcome_only: true`. Reason kwargs
  now validate against the pin's surface in both forms. The probe-raise-as-`error`
  taxonomy gap is deferred with rationale (self-proof mode cannot exhibit a cross-engine
  raise asymmetry) to when oracle-vs-rewrite runs begin.
- **Gates:** fast tier 55 passed; links gate green on every commit; preflight 10/10 at
  session start.
- **Board:** `docs/surface.md` — 19 rows `cased` (fn:reset, fn:reset_rules,
  fn:reset_settings flipped), 33 `uncovered`; `equivalent` still 0/52 — no rewrite
  exists yet, `cased` marks harness coverage only.

## Committed

- `50dcaad` — harness: multi-step step list + allow_raise probes.
- `bc368fb` — harness: the nine resume/restart/reset cases.
- `5dfeef8` — docs: board flips + the first banked run.
- `eb48e1d` — harness: review findings fixed; report; the re-banked verdict-of-record.
- (this commit) — ledger: session 4 banked.

## NEXT

Case the accessor family the corpus can already probe: author an edge-rule case
(an edge-head rule over the friends graph) covering `fn:filter_and_sort_edges`'s
happy path and its `edge-component-shape` class (empty vs non-empty frames differ
in column shape — the probe kind `filter_sort_edges` already exists in the capture),
and a `setting:store_interpretation_changes=False` pair pinning the accessor
store-off-assert classes (`get_rule_trace`, `filter_and_sort_*` — via `allow_raise`
probes) plus `fn:reason`'s trace-suppression-interaction (the knob force-flips
`atom_trace` at reason start). Run oracle-vs-oracle, flip `fn:filter_and_sort_edges`
and `setting:store_interpretation_changes`, bank the run.

## Deviations

- The review gate again used the umbrella's scaled-down single-focused-reviewer form
  for a contained spine extension (the charter's ≥2-reviewer form names complete
  features); report committed anyway.
- The step-op set gained `add_fact`, which session 3's NEXT did not name — the pin's
  fact-clearing behavior (Evidence) makes a fact-less resume unable to reason, so the
  named resume classes were uncoverable without it.

## Asks queued

None.

## Divergences

None opened — no rewrite exists; the restart-true KeyError family and the bare-resume
TypeError are pinned oracle behaviors recorded on the board and in case purposes,
oracle-bug-candidates to file per AC-3's both-not-either rule when equivalence runs
begin.

## Idea seeds

- The restart=True clock-vs-trace mismatch (interp.time reset beneath surviving trace
  events → KeyError in every trace-derived accessor) joins session 3's get_dict seed as
  evidence for the same rewrite contract decision: derived views must read world state,
  not replay the trace — or the trace must carry run epochs.
- The runner's exit taxonomy needs a probe-raise channel before oracle-vs-rewrite runs:
  a candidate engine that newly raises on an undeclared probe currently wears the
  harness-failure label (review M2, deferred with rationale in the report).
- `REASON_ARGS` in the capture duplicates `reason()`'s keyword surface by hand; the
  AC-1 AST gate could derive it from the pinned signature the way the inventory scan
  does, making a pin move impossible to miss.
