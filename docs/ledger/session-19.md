# Session 19 — the knob arms land: 17/17 equivalent; the board crosses one-third (18/52)

Date: 2026-07-07 (continuing the 2026-07-06 sitting)

## Verdict

The remaining no-new-ops settings semantics landed: inconsistency
detection/resolution against inline IPLs (`inconsistency_check`
resolve-vs-override, `abort_on_inconsistency`), `allow_ground_rules`,
`update_mode` including the junk-string arm, `store_interpretation_changes`
off with the pinned `atom_trace` force-flip, `static_graph_facts`, and
the variant-selecting knobs `fp_version`/`parallel_computing` — the
last as **one semantics core under two pinned iteration schedules**
(ADR 0003; the parallel variant is byte-identical to the default at the
pin modulo one decorator flag, so it runs the same path). Proof:
**17/17 oracle-vs-rewrite PASS**, rewrite digests equal to the banked
sweep on every probe. The independent review confirmed the one-engine
claim structurally, verified all six author-named oracle-defect
reproductions, ran 16 discriminating probes, and **caught one real
Medium: the fp-mode `get_dict` view was silently *correcting* the
pinned fp variant's stale-edge defect — fixed to reproduce it, with a
seam test.** Board: ten rows flip, **18/52 equivalent**. The author
agent was interrupted mid-packet by a server error and resumed from its
transcript cleanly (process note below).

## Evidence

- **Author report:**
  [docs/reviews/2026-07-07-phase3-slice4-author.md](../reviews/2026-07-07-phase3-slice4-author.md)
  — per-knob pinned semantics and the one-core story; ADR
  [docs/adr/0003](../adr/) (fp as a schedule, not a second engine); six
  oracle-bug-candidates named.
- **Review (verdict of record):**
  [docs/reviews/2026-07-07-phase3-slice4-review.md](../reviews/2026-07-07-phase3-slice4-review.md)
  — independent rerun **17/17** into `results-phase3-slice4-review/`;
  fast tier **220 passed** (author 219 + 1 review seam test); digest
  cross-check 17/17 every probe; ADR 0003 independently confirmed (33
  semantic units line-identical between default/fp at the pin) and
  amended where it understated the variant diff; 16 both-engine probes:
  14 pass, 1 Medium found-and-fixed (the fp stale-edge view), 1
  residual recorded (fp+`infer_edges` crashes **both** engines at the
  same seam; the pin's numba `KeyError()` is payload-less vs the
  rewrite's `KeyError(('A','B'))` — rides to the edge-rule slice).
- **Hygiene:** oracle byte-clean at `e1a94af33e1f`; no installs; banked
  results dirs untouched; nothing under `results*` newly tracked; tree
  clean.
- **Process note:** the author hit a mid-packet server error and was
  resumed from its transcript; a resume message was briefly misrouted
  to session 17's completed author agent, which was stopped seconds
  later — the reviewer read the full `8774b1d..edbb3a6` diff as a
  coherent whole and found nothing foreign.

## Committed

- `60b34ad` — core: the fp schedule — one semantics core, two pinned
  schedules.
- `9584af9` — tests+adr: knob-arm seam tests; ADR 0003.
- `edbb3a6` — docs: slice-4 verdict — 17/17; ten rows flip (18/52).
- `9c51ee4` — engine: review fix — fp-mode `get_dict` reproduces the
  pinned stale-edge defect.
- `c86526a` — docs: independent review — packet passes.
- (this commit) — ledger: session 19 banked; campaign log continued.

## NEXT

**Land the graph-surface + loader happy-path slice — proven
oracle-vs-rewrite over 16 cases:** the graphml family
(`load-graphml-basic`, `load-graphml-no-attr-parse`,
`graphml-attr-coercions`, `graphml-empty`, `reverse-digraph-default`,
`reverse-digraph-on`), `graph-attr-parsing-on/-off`,
`save-graph-attrs-to-trace-on/-off`, `closed-world-on`
(`add_closed_world_predicate`), and the loader happy paths
(`fact-from-csv-basic`, `fact-from-json-basic`, `rule-from-csv-basic`,
`rule-from-json-basic`, `rules-from-file-basic`). After it, the un-run
remainder is the output/trace-file surface (output-to-file family,
memory-profile, save_rule_trace family, reason-queries — ~13 cases),
the registrand family (gated on the harness conditional-njit
accommodation), and the IPL file family (gated on the pyyaml ask); then
the Phase-3 breadth boundary comes into view.

## Deviations

- The author's single-session run was split across an API interruption
  and a transcript resume — no protocol deviation in substance; the
  reviewer's whole-diff read covered the seam.

## Asks queued

- **pyyaml** — carried (session 16 options + recommendation stand);
  gates only the IPL file-loading case family.

## Divergences

None opened — 17/17 equivalent; the fp stale-edge finding was a
rewrite-defect (over-correction of a pinned defect), fixed in-session;
the fp+`infer_edges` both-engine crash asymmetry is recorded in the
review as a residual for the edge-rule slice.

## Idea seeds

- **fp+`infer_edges` exception-payload asymmetry** (review residual):
  when the edge-rule slice lands, case the arm and decide
  reproduce-vs-DIV there.
- Carried: harness registrand accommodation (conditional njit-wrap);
  registrand-behavior cases (slice-2 L3/L4); ragged-CSV /
  interval-nonnumeric / weights-dtype / delta_t cases; sweep
  durability; `probe_s` timing; multi-rule prange characterization;
  artifact-schema `inputs` echo; `interacts-unknown-predicate`;
  `raise_errors=False` warn-skip arms.
