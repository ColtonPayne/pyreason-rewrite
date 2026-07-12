# Session 25 — the Phase-3 adjudication lands: all 44 sections decided per recommendation; DIV-0002's guard is in

Date: 2026-07-11

## Verdict

**The operator adjudicated the full 44-section Phase-3 batch (2026-07-11):
every recommendation accepted as written.** DIV-0001 and DIV-0002 are
`adjudicated` (A1: the recursion guard is documented, tested intentional
behavior; A2: the IPL loader now raises a stable honest
`builtins.ValueError` at the pin-equivalent append seam — implemented,
seam-tested, guard-parity verified at the shared `ipl_pair` choke point).
The three direction decisions are recorded (B17 → DIV-0002-shaped
direction for any future cased arm; B19 → ADR 0003 confirmed as the
answer to the session-6 fp-trace question; B25 → the proxy-arm choice
blessed); B16 carries as the flagged Phase-4 hazard; Part C stays
recorded-no-decision. Fast tier **271**; the packet's one touched e2e
(DIV-0002 pin-side reproducer) green; board inventory gate green.
**Phase 4 is unblocked.**

## Evidence

- **Author report:**
  [docs/reviews/2026-07-11-session25-adjudication-author.md](../reviews/2026-07-11-session25-adjudication-author.md)
  — adjudication recorded across both DIV records, the batch's
  `## Adjudication record`, and the board; the guard (`ipl_pair`,
  `src/pyreason/_state.py`) used by both `load_inconsistent_predicate_list`
  and `add_inconsistent_predicate`; message
  `IPL entries must be strings; got int: 1` (only the offending entry
  named); provisional acceptance test flipped to assert the adjudicated
  raise.
- **Independent review (approved-with-fixes):**
  [docs/reviews/2026-07-11-session25-adjudication-review.md](../reviews/2026-07-11-session25-adjudication-review.md)
  — seam confirmed against the pin (yaml_parser.py:187-196,
  label_type.py:86-94, pyreason.py:620-629) with live pin probes
  (`["a", 1]` raises at `_append` in both engines; a str subclass is
  accepted by both — no over-rejection); guard parity exact (two append
  sites, both through the choke point); pin-side reproducer assertions
  byte-identical; no committed case changes verdict (all five IPL
  fixtures string-entried; harness validates `inputs.ipl` at
  capture.py:594-598) — verified by inspection, no corpus run. Three
  staleness defects fixed (stale reproducer field, classification tense,
  the `fn:add_inconsistent_predicate` board note).
- **Tests:** `uv run pytest -m "not e2e"` → 271 passed, 4 deselected;
  `uv run pytest tests/test_div_0002_reproducer.py -m e2e` → 1 passed;
  `uv run pytest tests/test_surface_inventory.py -q` → 6 passed.
- **Pre-session substrate repair:** preflight was red on arrival
  (links-gate): CLAUDE.md's rendered links block had been re-rendered
  against a different tree's context (`~/Campaigns/hivemind-wt-maturation`
  paths) plus one stray character in the batch doc; repaired via
  `hstate links render --repo pyreason-rewrite` + a one-character revert;
  preflight 10/10 before any campaign work. See Friction.

## Committed

- `ec92405` — docs: the adjudication recorded (DIV records →
  adjudicated, batch adjudication record, board notes A1/B17/B19/B25/B16).
- `8310954` — loaders: the DIV-0002 option-(a) guard at the `ipl_pair`
  choke point + flipped/new seam tests + present-tense record text.
- `41f4397` — docs: session-25 author report.
- `b8b4774` — docs: review fixes (reproducer field, classification
  tense, guard-parity board note).
- `38c3d6a` — docs: session-25 review report.
- (this commit) — ledger: session 25 banked; campaign log continued.

## NEXT

**Open Phase 4 — the execution-layer evidence path (charter, phase 4):**
design and commit the **AC-4 workload ladder** (small/medium/large with
rationale; ladder cases are harness cases too, so performance and
equivalence share inputs; large stays laptop-local and intentionally
lightweight), then bank **oracle baselines on this machine** —
cold-start (fresh-process import + first `reason()`, numba cache warm;
the cache-*build* first import banked separately as context), steady
throughput per rung, peak memory — every measurement screen-then-confirm
(smoke screen + control-repeat noise band; medians with spread; the band
banked beside the numbers). **Read B16 first: no ladder rung ever
combines `fp_version=True` with `timesteps=-1`** (the fp schedule cannot
terminate on it). Rewrite-side baselines and profiling follow once the
oracle numbers are banked. The mid-campaign **AC-7 pickup drill** is
still owed and fits at this seam — run it as its own session right after
the ladder lands.

## Deviations

- None from the session shape. Note: the operator armed a session-side
  30-minute `/campaign` re-invoke loop (harness scheduling, not a
  campaign artifact) so the session loop survives turn boundaries while
  he sleeps.

## Asks queued

- None. The Phase-3 adjudication batch is fully resolved; no new asks
  arose this session. (Standing: Phase 4's acceleration spikes will
  raise dependency asks when candidates are proposed — none yet.)

## Divergences

- **DIV-0001 — adjudicated** (2026-07-11, option (a)): the guarded
  query-filter expansion is documented, tested intentional behavior.
- **DIV-0002 — adjudicated** (2026-07-11, option (a)): the loader
  guard is implemented at the shared choke point; stable honest message
  recorded in the record.

## Friction

- **surface:** syncthing-mirrored CLAUDE.md rendered-links block ·
  **expected vs actual:** committed block should render identically on
  every machine; arrived re-rendered against `~/Campaigns/…` worktree
  paths (uncommitted), redding links-gate + preflight ·
  **workaround:** `hstate links render --manifest … --repo
  pyreason-rewrite` restored the committed content; one stray `◊`
  reverted by hand · **cost:** ~5 minutes pre-session ·
  **recommendation:** the umbrella's render tooling could resolve
  targets through the manifest rather than the invoking tree's own
  location, so a render run from a worktree can't rewrite a federated
  consumer's links to worktree-relative paths.

## Idea seeds

- Carried into Phase 4 (unchanged from session 24): B16 hazard;
  registrand-behavior packet (L3/L4 arms); edge-rule head-function
  forms; sweep durability; `probe_s` timing; multi-rule prange
  characterization; pyyaml-version parity tripwire; artifact-schema
  `inputs` echo; `raise_errors=False` warn-skip arms.
