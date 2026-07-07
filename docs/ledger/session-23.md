# Session 23 — the IPL family lands 4/4: every board row is run (52/52); DIV-0002 opens

Date: 2026-07-07 (continuing the 2026-07-06 sitting)

## Verdict

The IPL file family landed: `load_inconsistent_predicate_list` as a
faithful transcription of the pinned `parse_ipl` (raise order,
null-overwrite, parse-first rebind — all reproduced at the public-API
boundary, safe-load only, pyyaml as already approved and installed).
**4/4 oracle-vs-rewrite PASS**; fast tier **270**; board **52/52** —
zero rows un-run, with the review confirming both flips honest by
mechanical recomputation over every banked `report.json` (the
`fn:save_rule_trace` flip's last covering case was this slice's
`ipl-atom-trace-off-trace`). The review's probes surfaced one
un-caseable divergence, queued as **DIV-0002**: non-string IPL
entries — the pin raises a `ValueError` whose message is
address-derived and same-engine-unstable (harness-irreproducible on
the pin itself), while the rewrite's plain-list append accepts;
proposed resolution is a guarded raise per the established typed-list
precedent. Phase 3's slices are done; the breadth boundary sweep is
the phase's last session, after which the loop **stops** per the
operator instruction banked in session 22.

## Evidence

- **Author report:**
  [docs/reviews/2026-07-07-phase3-slice8-author.md](../reviews/2026-07-07-phase3-slice8-author.md)
  — 4/4 into `results-phase3-slice8/`; 4 new seam tests (fast tier
  269); safe-load only; the pyyaml-version parity observation (a
  future oracle-env rebuild on a different pyyaml fails the exact
  compare loudly, not silently).
- **Review (verdict of record):**
  [docs/reviews/2026-07-07-phase3-slice8-review.md](../reviews/2026-07-07-phase3-slice8-review.md)
  — independent rerun 4/4, 16/16 capture digests identical; board
  52/52 recomputed mechanically; the save_rule_trace flip verified
  (full-case-list ⊆ passed-union, no case-list edit rode along);
  probes: empty-list overwrite, four YAML shape arms,
  `inconsistency_check=False`, duplicate pairs — all cross-engine
  equal; the non-string-entry probe forced **DIV-0002**
  ([docs/divergences/DIV-0002.md](../divergences/DIV-0002.md),
  queued-for-operator, pin-side e2e reproducer
  `tests/test_div_0002_reproducer.py` + provisional seam test).

## Committed

- `409298e` — engine: `load_inconsistent_predicate_list` + facade +
  4 seam tests.
- `5de8c72` — docs: board — the last two rows flip (52/52); slice-8
  gitignore.
- `fc01d63` — docs: slice-8 author report.
- `5173aa2` — docs+tests: DIV-0002 filed with pin-side reproducer and
  provisional seam test.
- `dcd284f` — docs: independent review — packet passes; DIV-0002
  queued.
- (this commit) — ledger: session 23 banked; campaign log continued.

## NEXT

**Run the Phase-3 breadth boundary sweep — the phase's
verdict-of-record session:** the **whole committed case corpus in one
invocation** through the harness, oracle-vs-rewrite, into a dedicated
gitignored results dir (every banked verdict so far is slice-scoped;
`report.json` is last-writer-wins, so the phase claim needs the
single-run artifact). Expect the registrand compile wall-clocks
(~6 min class for that family alone). Spot-fix what surfaces (fixes
to pinned behavior; un-fixable mismatches become DIV records), rerun
the touched cases, and bank the sweep as the phase verdict: N/N cases,
the full pass list, fast-tier count, board state, and the
adjudication batch assembled for the operator (DIV-0001, DIV-0002,
plus every carried oracle-bug-candidate observation — the graphml
coercion cluster and O1/O2 included). **After this session banks, the
loop stops** (operator instruction, session 22): the operator
adjudicates the batch between Phase 3 and Phase 4.

## Deviations

None — the two-agent shape ran as specified.

## Asks queued

- **End-of-Phase-3 adjudication batch (operator-announced, assembled
  next session):** DIV-0001 (query-filter recursion guard), DIV-0002
  (non-string IPL entries — proposed guarded raise), and the carried
  oracle-bug-candidate observations.

## Divergences

- **DIV-0002** opened (queued-for-operator) — non-string IPL entries;
  see Evidence.

## Idea seeds

- pyyaml-version parity tripwire (the slice-8 observation) — consider
  a preflight-style env fingerprint check if the oracle env is ever
  rebuilt.
- Carried: registrand-behavior packet (L3/L4 arms now reachable);
  edge-rule head-function forms; fp+`infer_edges` exception-payload
  asymmetry; ragged-CSV / interval-nonnumeric / weights-dtype /
  delta_t cases; sweep durability; `probe_s` timing; multi-rule
  prange characterization; artifact-schema `inputs` echo;
  `interacts-unknown-predicate`; `raise_errors=False` warn-skip arms;
  O1/O2 graphml coercion quirks.
