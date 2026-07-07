# Session 16 — Phase 3 opens: the rewrite exists and its first 12 cases are equivalent

Date: 2026-07-07 (continuing the 2026-07-06 sitting)

## Verdict

Phase 3's opening slice landed: the rewrite package now exists
(`src/pyreason/` — an explicit-state core under the module-global
`pyreason` facade, reached by engine B through the committed
`scripts/rewrite-python` wrapper so the oracle side can never be
shadowed), carrying the settings facade, the Interval and Label value
types, the four public constructors with validating text-DSL parsers,
the loader-family malformed arms, and the fresh-state accessors. Proof:
**12/12 oracle-vs-rewrite PASS** over the corpus's twelve no-`reason()`
cases (4 fresh-process captures per case, `PYTHONHASHSEED=0`, repeats
digest-stable), plus an 85/85 probe-digest cross-check against the
banked phase-boundary sweep artifacts. The independent review found
0 High / 2 Medium / 2 Low, fixed both Mediums itself (CSV tokenizer
line-numbering on quoted multi-line records; non-UTF8 CSV faults dodging
the pinned wrap), reran everything, and passed the packet. The first
two inventory rows are honestly `equivalent` (2/52): `type:Interval`
and `type:Label`.

## Evidence

- **Author report:**
  [docs/reviews/2026-07-07-phase3-slice1-author.md](../reviews/2026-07-07-phase3-slice1-author.md)
  — design + ADR pointer
  ([docs/adr/0001-rewrite-package-layout.md](../adr/0001-rewrite-package-layout.md):
  src-tree + PYTHONPATH wrapper, no build backend — zero install
  surface; shadowing verified empirically both directions), per-case
  verdict table, every hand-matched third-party-origin exception
  string, and an honest-gap list of pin deviations in unexercised arms
  (ragged-CSV padding, weights-as-list, `delta_t` overflow wrap,
  narrowed read-wrap excepts) — each a future-case candidate, none
  observable by any committed case.
- **Review (verdict of record):**
  [docs/reviews/2026-07-07-phase3-slice1-review.md](../reviews/2026-07-07-phase3-slice1-review.md)
  — independent 12-case rerun **12/12 ALL PASS**
  (`results-phase3-slice1-review/`), fast tier **175 passed**
  (171 author + 4 review regression tests), overfitting probe 78/79
  same-class-variant matches post-fix (the 1: `interval.closed('a',1)`
  raises a numba TypingError in the oracle, unexercised by any case —
  recorded, not absorbed), and the author's ragged-row "NaN padding"
  gap claim corrected against the pin (pandas pads `''` there — the
  code was already equivalent).
- **Equivalence targets were the banked artifacts:** ground truth for
  every probe was `results/<case>/a1.json` from the session-15 sweep
  (read-only; rewrite runs landed in fresh `results-phase3-slice1*/`
  dirs).
- **Hygiene:** oracle tree byte-clean at `e1a94af33e1f`; no installs
  (pyproject gained only the pytest `pythonpath` src entry); `git
  status` clean; banked `results/` untouched; surface-inventory gate
  green; no writes outside the repo.
- **Scope exclusion, by gate:** `ipl-load-malformed` (the corpus's 13th
  no-reason case) needs pyyaml — its oracle raise is
  `yaml.parser.ParserError`, irreproducible without the library — so it
  stayed out and the dependency ask is queued below.

## Committed

- `bc252b3` — rewrite: opening slice — explicit-state core under the
  module-global pyreason facade.
- `b619a49` — docs: Phase-3 slice 1 evidence — 12/12 pass; Interval and
  Label rows go equivalent.
- `fde0c62` — rewrite: review fixes — CSV tokenizer line is the record
  ordinal; decode faults take the pinned wrap.
- `10b96db` — docs: independent review — packet passes after two fixed
  CSV-seam findings.
- (this commit) — ledger: session 16 banked; campaign log continued.

## NEXT

**Land the reasoning spine's first slice: `load_graph` (inline-graph
path) + `add_rule`/`add_fact` happy-path DSL parsing + the fixed-point
`reason(timesteps)` loop + `get_time` + `filter_and_sort_nodes`/`edges`
+ `get_rule_trace` — proven oracle-vs-rewrite via `--engine-b` starting
with `hello-world` and extending to the smoke-class reason-bearing
cases the slice's surface rows cover.** Every banked oracle contract
from sessions 7–14 (clause-level threshold gating, the Interval
prev-seed divergence, IPL trace-name fallback, state-contamination
semantics, canonical/persistent knob behavior) is a design input;
deliberate divergences go through AC-6, never silently. The pattern
that worked this session repeats: banked sweep artifacts as the
probe-level ground truth before any live run.

## Deviations

- The ledger-15 NEXT suggested "graphml/settings cases" as the first
  proof set, but every such case invokes `reason()`; the actually
  runnable first slice is the twelve no-reason cases (value types,
  constructors, loaders, fresh-state accessors). Recorded as the
  packet-shaping decision; the graphml/settings cases join at the
  reasoning-spine slice.

## Asks queued

- **pyyaml (non-blocking, batched for the operator):** the rewrite needs
  a YAML parser to cover `load_inconsistent_predicate_list` — the
  oracle's malformed-IPL raise is `yaml.parser.ParserError`, whose
  module-qualified type and parser-internal message cannot be
  reproduced without pyyaml. Options: (a) **`uv add pyyaml`, unpinned
  within the resolver's range (recommended** — same shape as the
  approved networkx ask; the oracle env already carries its own pinned
  copy); (b) pin to the oracle env's exact version; (c) defer until the
  IPL surface row is otherwise reached. Until adjudicated,
  `ipl-load-malformed` stays oracle-only and the row stays `cased`.
- **Packaging (`[build-system]`/editable install): recommendation is
  *no ask needed now*** — ADR 0001's src-tree + wrapper layout covers
  every current consumer with zero install surface; revisit only if an
  external consumer appears.

## Divergences

None opened — 12/12 equivalent; the two review findings were
rewrite-defects, fixed in-session.

## Idea seeds

- Future cases for the honest-gap arms: ragged-short CSV rows,
  `interval.closed` non-numeric construction (oracle raises numba
  TypingError), rule-weights dtype arm, `delta_t` > 65535.
- Carried: sweep durability (report.json last-writer-wins); rewrite
  contracts list (session 14); `probe_s` timing field; multi-rule
  prange characterization; artifact-schema echo of `inputs`;
  `interacts-unknown-predicate`; `raise_errors=False` warn-skip arms.
