# Session 12 — the accessor/trace-output cluster: four rows, one refuted generalization

Date: 2026-07-07 (continuing the 2026-07-06 sitting)

## Verdict

Session 11's NEXT executed: the capture grew two probe kinds
(`accessor_fingerprint`, `save_rule_trace`), six cases took the corpus
53 → 59, targeted oracle-vs-oracle ALL PASS on all six with same-engine
repeats (the post-review rerun is the verdict-of-record), fast tier
70 → 77, and the board stands at 39/52 rows `cased` with `fn:get_rules`,
`fn:get_logic_program`, `fn:get_interpretation`, and `fn:save_rule_trace`
flipped. The review gate earned its keep: 1 High / 2 Medium / 2 Low — the
High refuted the author's headline characterization ("the trace CSV name
fallback at `output.py:23-25` is dead code") with a live screen: IPL
complement rows bank `IPL: <label>` names unconditionally, so the
fallback fires exactly there with `atom_trace` off. The claim is now
scoped correctly everywhere it was recorded.

## Evidence

- **Probe kinds** (`de547d0`): `accessor_fingerprint` renders a
  get-family accessor's return into canonical digest-comparable JSON,
  with identity flags pinning the return-the-same-object seam
  (`pyreason.py:535`/`:546`) so a copy-returning engine fails;
  `save_rule_trace` runs the saver into the confined per-capture
  directory (`case_wants_output_dir` extended — the pinned default folder
  is the cwd; `TRACE_FOLDER_RE` admits no path escape) and compares the
  written CSVs' canonicalized names and exact contents (`TRACE_TS_RE`
  rationale recorded at the definition site, same run-schedule reasoning
  as session 10's stamp). Validation parity throughout: authoring faults
  exit 2 in both case forms; `allow_raise` legal on both new kinds via
  the shared recorded-probe wrap. +7 seam tests.
- **The cases** (`7921f97`, purposes corrected in `d2c24cd`):
  `accessors-fresh-state` (all three accessors before any load — `None`
  vs empty-list initialization pinned) / `accessors-lifecycle` (across
  load → reason → reset: rules mutate in place under clause reorder,
  `reset_graph` nulls the interpretation) / `save-rule-trace-basic`
  (node+edge CSVs, exact contents) / `save-rule-trace-atom-trace-off`
  (`Occurred Due To` is `'-'` on every row of this IPL-free program) /
  `save-rule-trace-store-off` (the `pyreason.py:1652` assert raise banked;
  write-then-raise unreachable at the pin per review L2) /
  `save-rule-trace-clause-reorder` (the `:1598-1606` reorder mutation
  observed through the saved trace; threshold half named unobserved per
  review L1). All six over the committed hello-world program family — no
  new fixtures.
- **The refuted generalization (review H1, the session's sharpest
  lesson):** the author observed empty trace names with `atom_trace` off
  on the cased programs and generalized to "fallback never fires". The
  reviewer's screen (friends graph + `add_inconsistent_predicate`,
  `atom_trace=False`) shows `'-'` on fact/rule rows and `'IPL: popular'`
  on complement rows — the IPL append sites bank names gated only on
  `store_interpretation_changes` (`interpretation.py:304/:308/:380/:384/
  :1582/:1599` + fp mirrors). Board, case purpose, and
  `docs/analysis/surface/reason-and-state.md:56` all corrected to the
  two-sided scoped claim; the IPL-with-atom-trace-off trace arm is named
  uncovered (no committed case combines them with a trace view). Rewrite
  relevance sharpened: keep the fallback for IPL rows, never invent names
  for fact/rule rows.
- **The runs:** fast tier 77 passed; each of the six cases via
  `PYTHONHASHSEED=0 uv run python -m harness.run --cases
  harness/cases/<case>.json --engine-a oracle-env/bin/python` → ALL PASS,
  4 fresh-process captures each, repeats green — author run and
  post-review rerun (verdict-of-record). No corpus sweep (session 11's
  banked verdict stands; no committed probe changed — the only case edit
  is purpose text).
- **Review gate:**
  [docs/reviews/2026-07-07-accessor-trace-cases.md](../reviews/2026-07-07-accessor-trace-cases.md)
  — H1 (fixed): the dead-code claim rescoped with both append-site cite
  sets and the live screen. M1 (fixed): the atom-trace-off case purpose
  contradicted its own banked CSVs. M2 (fixed): the refuted analysis-doc
  sentence corrected in place, per prior sessions' practice. L1 (fixed):
  the reorder case's unobserved threshold facet named on the board. L2
  (recorded, no fix): the store-off case cannot see a write-then-raise
  engine — unreachable at the pin, recorded as a decision. Author report:
  [2026-07-07-accessor-trace-cases-raw.md](../reviews/2026-07-07-accessor-trace-cases-raw.md).
- **Gates:** preflight 10/10 at session start; links gate and fast tier
  green on every commit; oracle tree clean at `e1a94af33e1f` throughout.
- **Board:** `docs/surface.md` — 39/52 `cased`, 13 `uncovered`
  (`equivalent` still 0/52 — no rewrite exists yet): 9 fn rows
  (`load_inconsistent_predicate_list`, `add_closed_world_predicate`,
  `add_fact_from_json`, `add_fact_from_csv`, `add_rules_from_file`,
  `add_rule_from_csv`, `add_rule_from_json`, `add_annotation_function`,
  `add_head_function`) and the 4 type rows (`Query`, `Threshold`,
  `Interval`, `Label`).

## Committed

- `de547d0` — harness: `accessor_fingerprint` + `save_rule_trace` probe
  kinds (+7 seam tests).
- `7921f97` — harness: six cases over the accessor/trace-output cluster.
- `e532987` — docs: board flips + author report.
- `d2c24cd` — harness: review — dead-code claim rescoped (board, case
  purpose, analysis doc); reorder gap named; report.
- (this commit) — ledger: session 12 banked; campaign log continued.

## NEXT

**Close the un-gated breadth rows, then the Phase-3 fork goes to the
operator.** The next packet: the remaining loader/semantic fn rows that
need no new operator decision — `add_rules_from_file`,
`add_fact_from_json`, `add_fact_from_csv`, `add_rule_from_json`,
`add_rule_from_csv`, `load_inconsistent_predicate_list`,
`add_closed_world_predicate` — read each anchor at the pin, enumerate
input classes, reuse the committed-fixture input pattern (session 9's
`graphml_path` precedent) for the file-taking loaders, case, run
targeted, flip, bank via the two-agent review shape. The 4 type rows and
the two callable-registering functions (`add_annotation_function`,
`add_head_function` — these take Python callables and likely need a
named-function registry in the capture; design it in the same packet if
tractable, else name the blocker precisely) ride the same or a following
packet. **After that, the board's un-gated breadth is exhausted and the
Phase-3 sequencing decision (start the pure-Python reference core; its
likely `networkx` dependency ask rides the same decision) is the
operator's — queued below.**

## Deviations

None — the two-agent shape ran as specified; the loop stopped after this
session on operator instruction (not a deviation: an operator interrupt
is a named stop condition).

## Asks queued

None blocking. For operator triage at this boundary:
- **The Phase-3 fork (new):** open the reference-core rewrite now vs
  after the last breadth packets. Recommendation: one more breadth
  session to close the un-gated fn rows, then open Phase 3; the rewrite's
  first dependency ask (`networkx`, since `load_graph` accepts NetworkX
  graphs at the public boundary) rides the Phase-3 opening.
- The raising-probe form (carried): one probe shape unlocking
  `type-reject` family-wide, `load_graphml` missing-file/bad-content, the
  `"0.5.5"` float-guard raise — and now also the natural home for
  malformed-input arms of the upcoming loader rows.
- The `memory_profile`/`interaction-output` text-canonicalization policy
  (carried).

## Divergences

None opened — no rewrite exists; all six cases oracle-vs-oracle.

## Idea seeds

- The IPL-with-atom-trace-off trace arm as a case once
  `load_inconsistent_predicate_list` is cased — the review's screen is
  the ready-made program shape.
- A named-function registry in the capture for
  `add_annotation_function`/`add_head_function` (callables can't ride
  JSON; a registry of committed reference functions can).
- Carried: `probe_s` capture timing field; multi-path `--cases`;
  multi-rule prange characterization; `REASON_ARGS` from the pinned
  signature; artifact-schema echo of `inputs`.
