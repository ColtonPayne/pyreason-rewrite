# Session 13 — the loader/semantic breadth packet: seven rows, two approved mechanisms landed

Date: 2026-07-07 (continuing the 2026-07-06 sitting)

## Verdict

Session 12's NEXT executed in full: the operator-approved raising-probe
form (`apply_input`, both probe-kind and step-op spellings) and the
approved peak-MB canonicalization landed with seam tests (fast tier
77 → 90), 17 cases took the corpus 59 → 76, targeted oracle-vs-oracle
ALL PASS on all 17 with same-engine repeats (the reviewer's rerun is the
verdict-of-record), and all seven un-gated loader/semantic fn rows
flipped — the board stands at **46/52 cased**, with the 6 uncovered
being exactly the 4 type rows plus the two callable-registering
functions. The review gate again caught a session-12-class
overgeneralization: the author's "a single-clause rule never shows the
CWA" was refuted live (the predicate-map *else* branch grounds ALL
nodes when the predicate is wholly unstated) and the board note
re-scoped two-sidedly.

## Evidence

- **Mechanisms** (`300bf3f`): `apply_input` probe form — a case declares
  an input application expected to raise; the banked observation is the
  module-qualified exception type + exact message, with no
  canonicalization on the apply path (nothing canonicalized without
  recorded rationale). Validation parity via a shared `_apply_fault`
  (authoring faults exit 2 in both case forms); path handling refuses
  absolute/empty/escaping paths in both spellings. Peak-MB
  canonicalization: `PEAK_MB_RE` anchors the full pinned line
  (`pyreason.py:1520`), per-case opt-in, refused unless
  `settings.memory_profile` is true; narrowness proven by a seam test.
  +13 seam tests.
- **Fixtures and cases** (`dc172f4`, `0527526`): 26 committed
  loader-input fixtures (session 9's `graphml_path` pattern); 17 cases —
  happy/malformed pairs across the five file loaders, the IPL triple
  (basic / null-overwrite / malformed), the session-12 seed
  `ipl-atom-trace-off-trace` (closing fn:save_rule_trace's named gap:
  `('popular','-')` ×6 and `('unpopular','IPL: popular')` ×6 in the
  re-parsed CSV), the closed-world twins (`busy`/`available`;
  on-twin derives `available` for John/Justin, never Mary; off-twin
  none), and `memory-profile-output-on` (the interaction-output case
  the canonicalization unlocks). Semantic rows observed through
  `reason()` output, not stored values.
- **Review gate** (2 Medium / 4 Low fixed, 1 Low recorded):
  [docs/reviews/2026-07-07-loader-rows.md](../reviews/2026-07-07-loader-rows.md)
  — M1: the CWA "never" claim refuted with a live screen
  (`interpretation.py:1400-1401` grounds ALL nodes for a map-absent
  predicate; single-clause `[0,0]` rule fires everywhere); board note now
  two-sided, `interacts-unknown-predicate` named with its ready-made
  case shape. M2: detection-flavored predicate names renamed to
  engine-neutral vocabulary, semantics re-proven. L1–L4: exception-quote
  precision, missing-file scoping, branch-imprecision, stale note.
  L5 (recorded): kwarg whitelist entries validated but not yet consumed —
  warn-skip arms named uncovered. Author report:
  [2026-07-07-loader-rows-raw.md](../reviews/2026-07-07-loader-rows-raw.md).
- **The deliberately un-cased arm, confirmed live by the reviewer:**
  `add_closed_world_predicate(3)` is silent and `reason()` raises with a
  run-varying pointer-like token (`U+ffe710` vs `U+1962710` across
  identical runs) — un-bankable under exact compare, and casing it would
  need a step-outcome message-canonicalization policy the operator has
  not approved. Left recorded on the board; reviewer recommends leaving
  it (it would pin nothing of value).
- **The runs:** fast tier 90 passed / 2 deselected at every commit; each
  of the 17 cases via `PYTHONHASHSEED=0 uv run python -m harness.run
  --cases harness/cases/<case>.json --engine-a oracle-env/bin/python` →
  ALL PASS, 4 fresh-process captures, repeats by exact digest — author
  run and post-fix rerun (verdict-of-record); the 3 fix-touched cases
  reran post-fix. No corpus sweep (wall-clock rule; capture changes
  additive, no pre-existing case's probes changed — verified in the
  diff by the reviewer).
- **Gates:** preflight 10/10 at session start; links gate and fast tier
  green on every commit; oracle tree clean at `e1a94af33e1f` throughout;
  no installs, no out-of-repo writes.
- **Board:** `docs/surface.md` — **46/52 cased**, 6 uncovered
  (`equivalent` still 0/52 — no rewrite exists yet): `type:Query`,
  `type:Threshold`, `type:Interval`, `type:Label`,
  `fn:add_annotation_function`, `fn:add_head_function`.

## Committed

- `300bf3f` — harness: `apply_input` probe form + loader step ops +
  peak-MB canonicalization (+13 seam tests).
- `dc172f4` — harness: 26 committed loader-input fixtures.
- `0527526` — harness: 17 cases (corpus 59 → 76).
- `840451a` — docs: seven board flips + author report.
- `87fa18e` — harness: review M2 — engine-neutral predicate rename,
  semantics re-proven.
- `5df0f7e` — harness/docs: review M1 + L1–L4 — CWA scope corrected,
  precision fixes.
- `4d5f376` — docs: review report.
- (this commit) — ledger: session 13 banked; campaign log continued.

## NEXT

**Close the last six breadth rows, then the phase boundary.** The next
packet: the 4 type rows (`type:Query`, `type:Threshold`,
`type:Interval`, `type:Label` — read each anchor at the pin, enumerate
the constructor/DSL input classes, malformed arms via the `apply_input`
raising form where the type is reachable through a loader or setter,
direct-construction probes where not) and the two callable-registering
functions (`fn:add_annotation_function`, `fn:add_head_function` — these
take Python callables that can't ride JSON: design the named-function
registry of committed reference functions in the capture in the same
packet if tractable, else name the blocker precisely). Two-agent review
shape as always. **After this breadth session, the ledger's NEXT moves
to the Phase-3 opening — that is a phase boundary, so the following
session is the dedicated full-corpus/e2e sweep (run everything,
spot-fix, bank the verdict-of-record), and Phase 3's first action after
it is the `networkx` dependency ask to the operator.**

## Deviations

None — the two-agent shape ran as specified; fast tier plus
packet-touched e2e only, per the wall-clock rule.

## Asks queued

- **Non-blocking, operator's option:** a step-outcome
  message-canonicalization policy would be needed to bank the CWA
  non-string reason-time raise (run-varying pointer-like token in the
  message). Reviewer and orchestrator recommendation: **leave it
  un-cased** — it would pin nothing of value; the arm is recorded on the
  board with rationale. No action needed unless the operator wants it.

## Divergences

None opened — no rewrite exists; all 17 cases oracle-vs-oracle.

## Idea seeds

- `interacts-unknown-predicate` for `add_closed_world_predicate` — the
  M1 refuting screen is the ready-made case shape (map-absent predicate,
  single-clause `[0,0]` rule, CWA fires on every node).
- The `apply_input` form's ready-made unlocks: `type-reject` family-wide,
  `load_graphml` missing-file/bad-content arms.
- `raise_errors=False` warn-skip arms across the CSV/JSON loaders (the
  L5-validated plumbing is already in place).
- Carried: named-function registry for the callable-registering rows
  (session 14's packet); `probe_s` capture timing field; multi-path
  `--cases`; multi-rule prange characterization; `REASON_ARGS` from the
  pinned signature; artifact-schema echo of `inputs`.
