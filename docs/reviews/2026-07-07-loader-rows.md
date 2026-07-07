# Review — loader/semantic fn rows + the two approved canonicalization arms (session 13, agent 2)

Reviewer: session 13 agent 2 (independent of the author; judged only the
committed range `300bf3f..840451a` against the pinned oracle source and the
packet spec). Oracle pin `e1a94af33e1f` (v3.6.0), oracle tree verified clean
before and after review; campaign tree clean at review start. Author report:
[2026-07-07-loader-rows-raw.md](2026-07-07-loader-rows-raw.md). This review's
reruns are the session's verdict-of-record.

## Verdict

**All three packet parts met.** The `apply_input` probe form held up under
adversarial reading and seam-test scrutiny with no correctness defect; the
peak-MB canonicalization is exactly as narrow as its recorded rationale; the
seven rows' anchors, input-class enumerations, and partial-load claims all
verified against the pinned source and the banked artifacts. Findings:
**2 Medium / 4 Low fixed, 1 Low recorded** — the sharpest is a session-12-class
overgeneralization in the author's report ("a single-clause rule never shows
the CWA"), refuted with a live screen and re-scoped on the board. Fast tier
90 passed / 2 deselected at every fix commit; all 17 cases (plus the 3 the
fixes touched, rerun) targeted oracle-vs-oracle ALL PASS with same-engine
repeats, `PYTHONHASHSEED=0`.

## Findings

### M1 (fixed, `5df0f7e`) — "a single-clause rule never shows the CWA" is an overgeneralization, refuted live

The author's report (raw, lines 188-192) generalizes from their first CWA
screen: "when the clause predicate is in the predicate map,
`get_rule_node_clause_grounding` (interpretation.py:1396-1402) draws
candidates from the map (only nodes that *have* the predicate), so a
single-clause rule never shows the CWA." The premise is right; the "never"
is not. `get_rule_node_clause_grounding` has an *else* branch: when the
predicate is absent from the predicate map entirely (no fact ever states
it), the grounding falls back to **all nodes** (interpretation.py:1400-1401
at the pin) — and every one of them reaches `is_satisfied_node`'s CWA
branch. Refuting screen (scratch, oracle env at the pin, 2026-07-07):
two-node graph, `available(x) <-1 busy(x) : [0,0]` as the *only* clause,
`busy` closed-world and stated by **no** fact — `available [1.0,1.0]`
derives for **both** nodes at t1 and t2. The author's own screen had the
predicate stated (`busy(Mary)`), which is why they saw no single-clause
effect. Same failure class as session 12's H1: a scoped observation
promoted to "never".

Fix: the board note (`docs/surface.md` fn:add_closed_world_predicate)
now carries the two-sided scope — map-known predicates hide never-stated
nodes from a single-clause rule; wholly-unstated predicates ground ALL
nodes and the single-clause rule fires everywhere — and names the screen
as `interacts-unknown-predicate`'s ready-made case shape (that facet stays
uncovered; casing it is a one-case follow-up). The committed cases
themselves are unaffected (their purposes were correctly scoped to the
two-clause program). Rewrite relevance: the grounding fallback, not just
the CWA branch, is load-bearing for closed-world semantics.

### M2 (fixed, `87fa18e`) — detection-flavored vocabulary in the closed-world twins

The CWA cases modeled "nodes not known `suspicious` are `safe`" — the one
spot in the four commits at odds with the campaign's engine-engineering
vocabulary rule (cases, seam-test example names, board note, author-report
descriptions). Pure rename to `busy`/`available` everywhere: identical
program shape (fact `busy(Mary)` [1,1], rule
`available(x) <-1 Friends(x,y), busy(x):[0,0]`, same graph, same probes).
Re-proven after the rename: both twins ALL PASS; on-twin derives
`available` for John/Justin only, Mary's known [1,1] still fails the
clause; off-twin derives zero available rows.

### L1 (fixed, `5df0f7e`) — threshold-arm exception quotes omitted the outer wrap

`rule-from-json-malformed`'s purpose and the fn:add_rule_from_json board
note quoted the two threshold faults as "Item 0, threshold 0: Invalid
threshold - 'thresh'" and "custom_thresholds dict key 'one' must be an
integer clause index" while attributing the doubled prefix only to the
string-item arm. The banked artifacts (verified in this review's rerun,
`results/rule-from-json-malformed/a1.json`) show both threshold faults
wear the same outer wrap as every loader-level ValueError:
`Item 0: Failed to parse rule - Item 0, threshold 0: Invalid threshold - 'thresh'`
and `Item 0: Failed to parse rule - Item 0: custom_thresholds dict key 'one'
must be an integer clause index` (the raises at pyreason.py:987/:1004 are
ValueErrors inside the item try, re-wrapped at :1065). Purpose and board
now quote the full banked messages.

### L2 (fixed, `5df0f7e`) — fact-CSV board note swept missing-file into "all doubled-row-prefix ValueErrors"

fn:add_fact_from_csv's note read "missing file ('CSV file not found'),
invalid static cell, missing fact_text — all doubled-row-prefix
ValueErrors". The missing-file arm is the loader's own
`FileNotFoundError: CSV file not found: <path>` (pyreason.py:1334-1335),
no row prefix — confirmed in the banked artifact. Reworded: only the
latter two are doubled-row-prefix ValueErrors.

### L3 (fixed, `5df0f7e`) — "`ipl: []` — same code path as null" is branch-imprecise

fn:load_inconsistent_predicate_list's uncovered note claimed the explicit
empty list takes the *same code path* as null. Same empty-list outcome,
different branch: null fails the `is not None` guard at
yaml_parser.py:192 and skips the loop; `[]` passes the guard and iterates
zero times. The distinction matters precisely because the facet is being
left uncased on a by-inspection argument. Note reworded.

### L4 (fixed, `5df0f7e`) — stale "raising-loader probe form is future work" on fn:load_graphml

The form now exists (this packet). The row note now says so and records
why `load_graphml` is deliberately not yet an apply op (no committed case
consumes it; adding the op without one would be dead scaffolding — the
author's stated and correct rationale).

### L5 (recorded, no fix) — kwarg whitelist entries with no consuming case

`APPLY_FILE_OPS` whitelists `raise_errors` on the four CSV/JSON loaders
and `infer_edges` on `add_rules_from_file`, but the only committed case
passing any of them is `rules-from-file-malformed` (`raise_errors: true`).
The entries are signature-mirroring validation data (they *reject* typo'd
kwargs; they add no execution path — `call_apply_input` passes whatever
validation admitted), so they are not dead scaffolding in the packet's
sense, and the warn-and-skip arms they would serve are named uncovered on
every affected row and in the author's idea seeds. Recorded so the next
packet's raise_errors=False cases know the plumbing is already validated.

## The deliberately un-cased arm — author's claim checked

The packet asked whether the CWA non-string arm could be cased within the
already-approved canonicalization policy. Verified live (two identical
fresh oracle processes, `PYTHONHASHSEED=0`): `add_closed_world_predicate(3)`
is silent, and `reason()` raises `ValueError: character U+ffe710 is not in
range [U+0000; U+10ffff]` in run 1 vs `U+1962710` in run 2 — a
pointer-like, run-varying token. **Confirmed un-bankable under exact
compare.** It cannot be cased within approved policy: the raise surfaces
in a *reason step's outcome record*, not in an `apply_input` probe's
exception observation, so banking it would need a step-outcome message
canonicalization — a mechanism and policy the operator has not approved.
Left recorded on the board (validation refuses the non-string spelling
outright, with the rationale in the error text). Agreeing with the author.

## Probe-form review (Part A) — what was checked, verdict MET

- **Exception scope:** `raise_record` banks module-qualified type + exact
  message; no canonicalization exists on the apply path — nothing is
  canonicalized without recorded rationale (the only canonicalization in
  the packet is the flagged peak-MB line). Messages embedding
  repo-resolved absolute paths compare exactly because both captures pass
  the identical `str(REPO / rel)` — the property banked artifacts already
  rely on.
- **Validation parity:** one shared `_apply_fault` behind both the probe
  kind and the step op; authoring faults exit 2 in both forms
  (`test_apply_input_validates_as_a_step_op_too`); `allow_raise` banned on
  the self-recording kind exactly as on `expect_raise`.
- **Exit taxonomy:** `getattr` outside the try on both surfaces — a
  missing loader binding fails the capture (exit 1), never banks as
  engine behavior (`test_probe_apply_input_missing_loader_is_a_capture_failure`
  covers both forms).
- **Path handling:** both spellings refuse absolute, empty, non-string,
  and repo-escaping paths; `path` must exist (typo'd happy arm cannot bank
  FileNotFoundError and pass self-proof), `missing_path` must not (a case
  cannot claim a missing-file observation while banking a load). No
  escape found.
- **Kwargs:** whitelisted per op against the pinned signatures — verified
  against pyreason.py:652/:753/:868/:1168/:1294/:611 (all boolean at the
  pin); `add_closed_world_predicate` takes exactly a string name.
- **No dead scaffolding at op level:** all six file ops consumed on the
  probe surface (six malformed cases), all seven ops on the step surface
  (eight happy/semantic cases). L5 records the kwarg-level nuance.
- **Additivity:** `rule_fingerprint` and every pre-existing probe kind
  untouched (read in the diff); no committed case's digests could move —
  consistent with the wall-clock rule's no-sweep decision.

## Peak-MB canonicalization review (Part B) — verdict MET

`PEAK_MB_RE` anchors the full pinned line (`^Program used <num> MB of
memory$`, multiline; number admits sign/decimal/exponent) and the
substitution replaces only the number's line with the placeholder text,
leaving every other character intact —
`test_output_file_probe_canonicalizes_only_the_peak_mb_line` proves both
the narrowness and that the unflagged path is byte-identical, so no
existing case's comparison changed. The flag is per-case opt-in, refused
unless `settings.memory_profile` is true (nothing else at the pin writes
the line — verified: pyreason.py:1520/:1526 are the only sites), and the
rationale is recorded at the definition site and in the case record
(AC-2). The consuming case's banked redirect file (rerun, spot-checked)
carries the verbose print shape plus exactly
`Program used <peak-mb> MB of memory`.

## Row-by-row anchor check (Part C) — verdict MET

Each flipped row's anchor, enumeration, and notes read against the pinned
source; each case's banked artifacts spot-checked beyond the PASS verdict:

| row | anchor verified | artifact spot-check |
|---|---|---|
| add_rules_from_file | :652-690 — filter, `rule_{i+offset}` over the filtered list, raise wrap, bare open() | fp `[popular_rule, rule_1, rule_2]`; raise-arm partial load `[rule_0]`; skip-arm gap `[rule_0, rule_1, rule_3]`; bare errno FileNotFoundError |
| add_rule_from_csv | :753-866 — three except arms, exact header, `_parse_bool_param`, file-local dedup, doubled row wrap | fp `[csv_full, rule_1, csv_quoted]`; dup raise at row 2 after `[same_name]` loaded; unquoted-comma fails wholesale (tokenizer message); inferred `team` edges in edge trace |
| add_rule_from_json | :868-1080 — threshold list/dict loops, weights, doubled item wrap | all six raises banked; closing fp `null`; threshold messages carry the outer wrap (L1) |
| add_fact_from_json | :1168-1292 — shared param helper, unconditional summary print | trace names `{json-popular, fact_1, json-static}`; single- vs doubled-prefix pair banked |
| add_fact_from_csv | :1294-1412 — verbose-gated print, header exact-match, short-row padding | trace names `{csv-popular, csv-short, fact_2}`; edge fact `[0.9,1.0]` on the edge trace; empty file banks `{"raised": false}` |
| load_inconsistent_predicate_list | :611-618, yaml_parser.py:187-196 — wholesale rebind, no validation | 6 complement rows `('IPL: popular','IPL')`; null-overwrite: 0 complement rows; four distinct exception types banked |
| add_closed_world_predicate | :1122-1130, :1613-1617, interpretation.py:1757-1775, :1396-1402 | on-twin: available = {John, Justin}, never Mary; off-twin: none; non-string arm confirmed un-bankable (above); M1 scope correction |

The session-12 seed `ipl-atom-trace-off-trace`: the saved node CSV
re-parsed with a real CSV reader in this review —
`('popular', '-')` ×6 and `('unpopular', 'IPL: popular')` ×6, exactly the
scoped fallback claim; the fn:save_rule_trace row's uncovered gap is
correctly closed. Out-of-scope rows verified untouched: the diff touches
only the seven fn rows plus fn:save_rule_trace and
setting:memory_profile; board stands 46/52 cased with the 6 uncovered
being exactly the 4 type rows + `add_annotation_function` /
`add_head_function`.

## Rerun results (verdict-of-record)

`PYTHONHASHSEED=0 uv run python -m harness.run --cases
harness/cases/<case>.json --engine-a oracle-env/bin/python` — self-proof
mode, 4 fresh-process captures per case, same-engine repeats by exact
digest:

| case | pre-fix rerun | post-fix rerun |
|---|---|---|
| rules-from-file-basic | ALL PASS | — |
| rules-from-file-malformed | ALL PASS | — |
| rule-from-csv-basic | ALL PASS | — |
| rule-from-csv-malformed | ALL PASS | — |
| rule-from-json-basic | ALL PASS | — |
| rule-from-json-malformed | ALL PASS | ALL PASS (purpose-only edit) |
| fact-from-json-basic | ALL PASS | — |
| fact-from-json-malformed | ALL PASS | — |
| fact-from-csv-basic | ALL PASS | — |
| fact-from-csv-malformed | ALL PASS | — |
| ipl-load-basic | ALL PASS | — |
| ipl-load-null-overwrite | ALL PASS | — |
| ipl-load-malformed | ALL PASS | — |
| ipl-atom-trace-off-trace | ALL PASS | — |
| closed-world-on | ALL PASS | ALL PASS (renamed) |
| closed-world-off | ALL PASS | ALL PASS (renamed) |
| memory-profile-output-on | ALL PASS | — |

Fast tier: `uv run pytest -m "not e2e"` → **90 passed, 2 deselected** —
before fixes, and at both fix commits (pre-commit hook run visible in each
commit). No corpus sweep (wall-clock rule; the capture changes are
additive and no pre-existing case's probes changed — verified in the
diff, not taken from the author).

## Gates

No installs or dependency changes; no writes outside the repo (screens ran
in the session scratchpad); oracle tree clean at `e1a94af33e1f` before and
after; `git status` clean at review end; no security framing remains in
the committed artifacts (M2). Fixed: M1, M2, L1-L4 (`87fa18e`,
`5df0f7e`). Recorded, not decided: L5; the CWA non-string arm stays
un-cased pending any operator appetite for a step-outcome canonicalization
policy (none requested).
