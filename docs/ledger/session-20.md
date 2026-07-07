# Session 20 — the graph boundary lands: 16/16 equivalent; the board crosses half (29/52)

Date: 2026-07-07 (continuing the 2026-07-06 sitting)

## Verdict

The graph surface and the loader happy paths landed: `load_graphml`
(networkx `read_graphml` + the pin's post-processing, empty-graph arm
included), `graph_attribute_parsing` both arms with the pin's
**all-silent coercion cluster deliberately reproduced**,
`reverse_digraph`, `save_graph_attributes_to_trace`,
`add_closed_world_predicate`, and the five loaders' happy paths now
reasoning end-to-end. Proof: **16/16 oracle-vs-rewrite PASS**, rewrite
digests equal to the banked sweep on every probe. The independent
review found **zero defects** (its 5 discriminating probes — inverted
`'1,0'` pairs, whitespace pairs, bounds riding reversed edges, the
edge-side closed-world branch, closed-world colliding with a rule head,
static CSV facts past their windows — all byte-identical cross-engine)
and recorded two new oracle-quirk observations for the bug-candidate
list. Board: eleven rows flip, **29/52 equivalent** — past half. The
loop stops here by operator instruction ("stop at the end of the
stage"); the queued pyyaml ask is raised at this boundary.

## Evidence

- **Author report:**
  [docs/reviews/2026-07-07-phase3-slice5-author.md](../reviews/2026-07-07-phase3-slice5-author.md)
  — no new ADR (the boundary is two pure functions writing the existing
  four explicit-state graph fields + a facade delegation; 0002/0003
  hold); the silent-coercion cluster named as three
  oracle-bug-candidate follow-ups; fast tier 242 (220 + 22 new seam
  tests).
- **Review (verdict of record):**
  [docs/reviews/2026-07-07-phase3-slice5-review.md](../reviews/2026-07-07-phase3-slice5-review.md)
  — independent rerun **16/16** into `results-phase3-slice5-review/`;
  fast tier 242; digest cross-check 16/16 every probe; all 11 surface
  flips re-verified mechanically (29/52 exact); all 3 coercion
  reproductions confirmed against pinned source + installed oracle;
  preflight 10/10. New quirk observations: **O1** — `'1,0'` silently
  routes through the inconsistency resolve arm and pins a static
  `[0,1]` with no observable row; **O2** — the comma-pair arm tolerates
  whitespace the numeric-string arm rejects. Both reproduced
  identically by the rewrite; neither touches a committed case, so no
  DIV record per AC-6.
- **Hygiene:** oracle byte-clean at `e1a94af33e1f`; no installs; banked
  results dirs untouched; nothing under `results*` tracked beyond the
  long-standing `results/report.json`; tree clean.

## Committed

- `1006766` — engine+tests: the graph boundary and loader happy paths.
- `859b8ad` — docs: board — eleven rows flip (29/52).
- `3539661` — docs: author report.
- `ccc11d6` — chore: gitignore the slice results dirs per convention.
- `0599428` — docs: independent review — packet passes, zero defects.
- (this commit) — ledger: session 20 banked; campaign log continued.

## NEXT

**Land the output-surface slice — proven oracle-vs-rewrite over ~13
cases:** the output-to-file family (`output-to-file-default`,
`output-to-file-on`, `output-file-name-custom`,
`output-file-name-inert` — stdout redirection into the confined
working directory, compared via the `output_file` probe), the
memory-profile family (`memory-profile-default`, `memory-profile-on`,
`memory-profile-output-on` — peak-MB line canonicalized by the
harness; the rewrite needs a stdlib-only equivalent of the observable
output shape), the save_rule_trace family (`save-rule-trace-basic`,
`save-rule-trace-atom-trace-off`, `save-rule-trace-clause-reorder`,
`save-rule-trace-store-off` — CSV trace files written into the
confined directory), and the reason-queries pair
(`reason-queries-filter`, `reason-queries-no-match` — the `queries`
argument's rule-filtering semantics, with the banked query-filter
recursion-crash contract as a design input). After it the un-run
remainder is exactly: the registrand family (5 cases, gated on the
harness conditional-njit accommodation — a harness change to
`reference_fns.resolve()` that needs its own careful packet), the IPL
file family (4 cases, gated on the pyyaml ask), and `hello-world-parallel`-class
leftovers if any; then the Phase-3 breadth boundary sweep.

## Deviations

None — the two-agent shape ran as specified.

## Asks queued

- **pyyaml — raised interactively at this session boundary and
  adjudicated by the operator (2026-07-07): approved, option (a),
  unpinned within the resolver's range** (the recommended option; the
  rewrite consumes only safe-load of small IPL files). Executed on
  approval: `uv add pyyaml` → pyyaml 6.0.3 in the campaign env; the
  oracle env untouched (it carries its own pinned copy). Original
  options for the record: (a) unpinned — approved; (b) pinned to the
  oracle env's exact version; (c) defer. The IPL file family (4 cases)
  is now unblocked for a future slice.

## Divergences

None opened — 16/16 equivalent; O1/O2 are oracle-quirk observations
outside any committed case, carried on the bug-candidate list.

## Idea seeds

- O1/O2 (above) as future coercion-cluster cases when the graphml row's
  input classes next widen.
- Carried: harness registrand accommodation (conditional njit-wrap);
  fp+`infer_edges` exception-payload asymmetry (edge-rule slice);
  registrand-behavior cases (slice-2 L3/L4); ragged-CSV /
  interval-nonnumeric / weights-dtype / delta_t cases; sweep
  durability; `probe_s` timing; multi-rule prange characterization;
  artifact-schema `inputs` echo; `interacts-unknown-predicate`;
  `raise_errors=False` warn-skip arms.
