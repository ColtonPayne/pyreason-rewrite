# Session 17 — the reasoning spine lands: the rewrite reasons, 13/13 equivalent

Date: 2026-07-07 (continuing the 2026-07-06 sitting)

## Verdict

The reference core's default-path reasoning spine landed: `load_graph`
(inline DiGraph path), fact/rule application and grounding, clause
evaluation with threshold gating (default + custom `Threshold` lists,
number/percent × total/available, clause-level), interval update
semantics, the fixed-point temporal `reason(timesteps, …)` loop with
all four convergence modes, the `atom_trace` rule trace, `get_time`,
`filter_and_sort_nodes`/`edges`, and `get_rule_trace` — pure functions
over the explicit state object under the session-16 facade (ADR 0002).
Proof: **13/13 oracle-vs-rewrite PASS** over the slice's mechanically
computed case set, with all 39 rewrite probe digests byte-equal to the
banked session-15 sweep artifacts. The independent review found **0
High / 0 Medium / 4 Low — zero code fixes needed** — and its
overfitting hunt ran **10 reviewer-constructed discriminating probes
through both engines, 10/10 matching** (threshold boundary arithmetic,
delta-0 fixed-point re-entry, inconsistency-message arms, fact windows
under perfect convergence, edge-chain grounding, and — via a direct
two-engine script — registered annotation/head functions). Board:
`type:Threshold` flips to equivalent, **3/52**.

## Evidence

- **Author report:**
  [docs/reviews/2026-07-07-phase3-slice2-author.md](../reviews/2026-07-07-phase3-slice2-author.md)
  — design + per-case verdicts; ADR
  [docs/adr/0002-reference-core-state-step-trace.md](../adr/0002-reference-core-state-step-trace.md)
  (the core's state/step/trace shape; a meaning-for-meaning
  reproduction of the pinned `interpretation.py` default path, not a
  numba-idiom transliteration).
- **Review (verdict of record):**
  [docs/reviews/2026-07-07-phase3-slice2-review.md](../reviews/2026-07-07-phase3-slice2-review.md)
  (probe reproducers verbatim in
  […-review-raw.md](../reviews/2026-07-07-phase3-slice2-review-raw.md))
  — independent rerun 13/13 into `results-phase3-slice2-review/`; fast
  tier **195 passed** (175 + 20 new seam tests); both digest
  cross-checks recomputed 39/39; the narrowed-except and
  omitted-empty-container design deviations traced arm-by-arm against
  the pin and verified behavior-preserving.
- **The four Lows (all noted/accepted, none a defect in this packet's
  claims):** L1 — registrand cases are structurally uncoverable
  cross-engine through the committed harness (`reference_fns.resolve()`
  njit-wraps; the campaign env has no numba): a harness accommodation
  (njit-wrap only where numba imports) is queued follow-up work before
  the `fn:add_annotation_function`/`fn:add_head_function` rows can ever
  flip. L2 — the pinned-verbatim `Program.reset_*` stubs and the
  wired-but-unproven `again` dispatch are accepted scaffolding: the
  reset/again packet is next and claims nothing yet. L3/L4 —
  unreachable-arm shape loosenesses recorded for the future
  registrand-behavior packet.
- **Hygiene:** oracle tree byte-clean at `e1a94af33e1f`; no installs;
  banked results dirs untouched; `git status` clean; surface flip
  verified honest against both banked report.json files.

## Committed

- `56b0559` — engine: the default-path reasoning spine as pure
  functions over explicit state.
- `0ad3fa4` — tests: seam-test the reasoning core at the module-global
  facade.
- `1b55fe7` — docs: slice-2 evidence — 13/13; `type:Threshold`
  equivalent.
- `bd856fa` — docs: independent review — packet passes, zero fixes.
- (this commit) — ledger: session 17 banked; campaign log continued.

## NEXT

**Land the state-lifecycle slice: the reset family (`reset`,
`reset_rules`, `reset_settings`), `reason(again=…, restart=…)`
semantics, and the `persistent`/`canonical` knob arms with
`interpretation_dict` probe support — proven oracle-vs-rewrite over the
14 lifecycle/persistence cases:** `reset-no-program`,
`reset-with-program`, `reset-rules-no-program`,
`reset-rules-with-program`, `reset-settings-restore`,
`accessors-lifecycle`, `reason-again-no-program`,
`reason-again-restart-false`, `reason-again-restart-true`,
`reason-bare-again-no-facts`, `persistent-off`, `persistent-on`,
`canonical-on`, `canonical-last-write`. The banked state-contamination
contracts and the L2-accepted `again` dispatch are the design inputs;
the session-16/17 pattern holds (banked sweep artifacts as probe-level
ground truth; reviewer runs a discriminating-probe hunt).

## Deviations

None — the two-agent shape ran as specified; the reviewer's
out-of-harness registrand probe was the packet-appropriate form of the
overfitting hunt given L1.

## Asks queued

- **pyyaml** — carried from session 16, still non-blocking, still open
  with the operator (options + recommendation in
  [session-16.md](session-16.md)). It gates the IPL case family
  (`ipl-load-basic`, `ipl-load-null-overwrite`,
  `ipl-atom-trace-off-trace`, `ipl-load-malformed`) joining the
  rewrite's proof set.

## Divergences

None opened — 13/13 equivalent; the review's probe hunt surfaced no
cross-engine mismatch.

## Idea seeds

- **Harness registrand accommodation (review L1):** make
  `harness/reference_fns.resolve()` njit-wrap only when numba imports,
  so registrand cases can capture in the numba-less rewrite env — the
  gate on ever flipping the two registrand function rows.
- Future cases from L3/L4's unreachable arms (registrand return-shape
  coercion; quantifier-membership guard) for the registrand-behavior
  packet.
- Carried: ragged-CSV / interval-nonnumeric / weights-dtype / delta_t
  overflow cases (session 16); sweep durability; rewrite contracts
  list; `probe_s` timing field; multi-rule prange characterization;
  artifact-schema echo of `inputs`; `interacts-unknown-predicate`;
  `raise_errors=False` warn-skip arms.
