# Session 18 — the state lifecycle lands: reset/resume/persistence, 14/14 equivalent

Date: 2026-07-07 (continuing the 2026-07-06 sitting)

## Verdict

The cross-run state semantics landed inside the existing explicit-state
design: the reset family (`reset`, `reset_rules`, `reset_settings` —
exactly what each clears and what survives at the pin),
`reason(again=…, restart=…)` including the pinned bare-again
`TypeError('List() argument must be iterable')` arm and the
restart-true `KeyError(1)`, the `persistent`/`canonical` knob arms with
forward-stamping, and `Interpretation.get_dict()` for the
`interpretation_dict` probe. Proof: **14/14 oracle-vs-rewrite PASS**
over the lifecycle case set, rewrite digests equal to the banked
session-15 sweep. The independent review returned **zero findings at
any severity, zero fixes** — its overfitting hunt ran 8 probe families
/ 31 observations through both engines, all byte-identical, including
the sharpest unpinned seam (a resume does not clear the fact lists, so
a second `again=True` re-consumes the same fact — both engines agree).
Board: five rows flip to equivalent, **8/52**.

## Evidence

- **Author report:**
  [docs/reviews/2026-07-07-phase3-slice3-author.md](../reviews/2026-07-07-phase3-slice3-author.md)
  — no ADR 0003 (0002 still describes the design; the session-17
  scaffolding — `Program.reset_*`, the again-dispatch — proved out
  unchanged). Five deliberately-reproduced **oracle-bug-candidates**
  named: half-cleared program → `get_time` AttributeError;
  restart-true clock-reset KeyErrors; the numba-message bare-again
  TypeError; the silent again-no-program degrade; grounding tables/IPL
  surviving `reset()`.
- **Review (verdict of record):**
  [docs/reviews/2026-07-07-phase3-slice3-review.md](../reviews/2026-07-07-phase3-slice3-review.md)
  (probe materials in […-raw.md](../reviews/2026-07-07-phase3-slice3-review-raw.md))
  — independent rerun **14/14** into `results-phase3-slice3-review/`;
  fast tier **209 passed**; digest cross-checks 14/14 both directions;
  all five quirk-reproductions verified against the pinned source *and*
  the installed oracle; surface flips verified row-by-row, both
  deliberate non-flips (`fn:reset_rules`, `setting:persistent`)
  correct.
- **Hygiene:** oracle byte-clean at `e1a94af33e1f`; no installs; banked
  results dirs untouched; the author's self-reported evidence-commit
  wrinkle (briefly tracked results dir, amended before anything
  stacked) verified resolved — nothing under `results*` tracked beyond
  the long-standing `results/report.json`; `git status` clean.

## Committed

- `a85886a` — engine: the cross-run state lifecycle — reset family,
  resume arms, dict view.
- `f2f9b29` — docs: slice-3 evidence — 14/14; five rows equivalent.
- `2466f2a` — docs: author report.
- `69c4cd5` — docs: independent review — packet passes, zero fixes.
- (this commit) — ledger: session 18 banked; campaign log continued.

## NEXT

**Land the knob-arm semantics slice: the remaining settings families
that need no new harness ops — proven oracle-vs-rewrite over 17
cases:** `abort-on-inconsistency-default`, `abort-on-inconsistency-on`,
`inconsistency-ipl-resolve`, `inconsistency-ipl-override` (inline `ipl`
input; no pyyaml involved), `allow-ground-rules-off/-on`,
`update-mode-default/-override/-junk-string`, `store-off-accessors`,
`store-off-atom-trace-flip` (the pinned force-flip of `atom_trace` when
storage is off is a compared knob readback), `fp-version-on`,
`parallel-computing-default/-on`, `parallel-fp-precedence` (the
variant-selecting knobs run the same single reference core — AC-5's
one-engine mandate; equivalence is output-level), and
`static-graph-facts-on/-off`. After this slice the un-run remainder is
the I/O/graph surface (graphml family, output-to-file family,
save_rule_trace family, memory-profile, loader happy paths,
closed-world-on, reason-queries), the registrand family (gated on the
review-L1 harness accommodation), and the IPL file family (gated on the
pyyaml ask).

## Deviations

None — the two-agent shape ran as specified.

## Asks queued

- **pyyaml** — carried (session 16 options + recommendation stand);
  gates only the IPL file-loading case family.

## Divergences

None opened — 14/14 equivalent; the five reproduced oracle quirks are
named as oracle-bug-candidate follow-ups in the author report (board
notes carry them; formal DIV filing remains available if the operator
wants records ahead of any rewrite-side improvement proposal).

## Idea seeds

- Carried: harness registrand accommodation (conditional njit-wrap —
  gate on the two registrand rows); registrand-behavior packet cases
  (L3/L4 arms); ragged-CSV / interval-nonnumeric / weights-dtype /
  delta_t cases; sweep durability; `probe_s` timing; multi-rule prange
  characterization; artifact-schema `inputs` echo;
  `interacts-unknown-predicate`; `raise_errors=False` warn-skip arms.
