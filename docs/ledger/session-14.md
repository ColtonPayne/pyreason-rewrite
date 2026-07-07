# Session 14 — breadth closed: the four type rows and the callable registrars; the board reads 52/52 cased

Date: 2026-07-07 (continuing the 2026-07-06 sitting)

## Verdict

Session 13's NEXT executed: the last six breadth rows flipped — the board
stands at **52/52 cased** (`equivalent` still 0/52 — no rewrite exists
yet). The capture grew query construction (`queries` in `REASON_ARGS`),
threshold/weights rule specs, `interval_probe`/`label_probe`
direct-construction probes (the two types the public API offers no other
reach for), an `add_rule` step op, and the **named-function registry**
(`harness/reference_fns.py`, stdlib-only import, njit at resolve time)
that lets JSON cases select committed reference callables by name —
unlocking `add_annotation_function`/`add_head_function`. 18 cases took
the corpus 76 → 94; fast tier 90 → 104; targeted oracle-vs-oracle ALL
PASS on everything with same-engine repeats (the reviewer's reruns are
the verdict-of-record). The review gate caught the third
evidence-discrimination finding in three sessions (a true claim whose
committed cases could not discriminate it) and materially re-scoped a
runtime-cache hazard, fixing both.

## Evidence

- **Mechanisms** (`0aa8d6e`, +13 seam tests): validation parity and
  raise-attribution discipline held across all new surfaces (authoring
  faults exit 2 in both case forms before the engine imports;
  construction raises are capture failures, never banked behavior).
  Additivity verified in the review diff — no pre-existing case's
  capture call shape changes, so no sweep was owed this session.
- **The cases** (`79363e4`, +`f34dbf0`'s discriminator): Query
  (construction fingerprints banking both silent misparses at
  `query_parser.py:24-26`/`:8-11`; `reason(queries=…)` filtering; the
  query-emptied-ruleset numba `ValueError` banked), Threshold
  (construction + accepted gating semantics: number default/two,
  dict-form, percent-total, and the clause-level discriminator),
  Interval (`interval-ops` — the proxy-vs-jitted `intersection` prev-seed
  divergence banked as data), Label (`label-ops` — `__eq__`'s
  AttributeError-before-isinstance banked as the probe's recorded raising
  relation), and the registrar rows (annotation effect observed through
  derived bounds two-arg and six-arg; reset clears registration;
  unregistered-name asymmetry: `NameError` for annotation vs silent empty
  grounding for head, `interpretation.py:1918-1930` vs `:2316-2338`).
- **Recorded un-caseable behaviors (board-noted, screens confirmed by
  the reviewer):** a query matching a self-recursive rule's head
  crashes the pinned process in `filter_ruleset` (unbounded Python
  recursion at `filter_ruleset.py:22-24`; exit 139, no artifact — the
  runner's taxonomy correctly refuses to bank it); plain (non-njit)
  registrands pass both registrars then fail `reason()` with
  environment-path-bearing TypingErrors (unbankable under exact
  compare; the head arm poisons even unreferenced).
- **Review gate** (2 Medium / 1 Low fixed, 2 recorded):
  [docs/reviews/2026-07-07-type-rows.md](../reviews/2026-07-07-type-rows.md)
  — M1: the clause-level threshold claim was true but its cases could
  not discriminate it (both gating semantics predicted the same outcome
  on the twins' graph); the discriminating shape banked as
  `threshold-number-gate-clause-level` (two disconnected pairs, each
  head's neighborhood holds one qualifier, the clause's whole-graph
  count 2 — both heads derive). M2: the registrand numba-cache
  poisoning recurs on **every** registrand capture, the author's
  "repo-rooted runs are safe" scoping refuted live (sys.path, not cwd,
  decides), and dispatcher-bearing signatures never hit the on-disk
  cache (each registrand capture paid a full compile and appended a
  ~10 MB `.nbc` overload, forever); fixed with a condition-gated
  snapshot/restore of the bundled kernel cache around registrand
  captures (an env-var re-pointing alternative screened and refuted —
  the engine's `__init__` re-points `NUMBA_CACHE_DIR` before decoration;
  rationale in the mechanism's docstring), and the oracle-env cache
  repaired (325 → 219 files, zero poisoned indexes; the disposable env,
  never the pinned tree). L1: fn:reason cases-line consistency.
  Recorded: type:Rule cross-link hygiene; registrand compile cost
  (~40–60 s × 4 captures × 3 dispatcher-reasoning cases) dominating the
  upcoming boundary sweep's added wall-clock. Author report:
  [2026-07-07-type-rows-raw.md](../reviews/2026-07-07-type-rows-raw.md).
- **The runs:** fast tier 104 passed / 2 deselected at every commit;
  reviewer reruns — pre-fix 17/17 ALL PASS on the author's tree,
  mid-review 19/19 (all 17 + discriminator + hello-world), final 6/6
  (the 5 registrand cases + hello-world) on the committed tree with the
  bundled cache verified clean after; all
  `PYTHONHASHSEED=0 uv run python -m harness.run --cases
  harness/cases/<id>.json --engine-a oracle-env/bin/python`, 4
  fresh-process captures, repeats by exact digest.
- **Gates:** preflight 10/10 at session start and at review end; links
  gate and fast tier green on every commit; oracle tree byte-clean at
  `e1a94af33e1f` throughout; no installs, no out-of-repo writes (screens
  in the session scratchpad; cache maintenance confined to the
  disposable oracle-env).
- **Board:** `docs/surface.md` — **52/52 cased**, 0 uncovered;
  `equivalent` 0/52. Corpus 94 cases.

## Committed

- `0aa8d6e` — harness: query/threshold/interval/label mechanisms +
  named-function registry (+13 seam tests).
- `79363e4` — harness: 17 cases (corpus 76 → 93).
- `a88bb3b` — docs: six board flips + three adjacent-row updates +
  author report.
- `6c337e1` — harness: review M2 — registrand cache confinement
  (snapshot/restore) + seam test.
- `f34dbf0` — harness/docs: review M1 — the clause-level discriminator
  case (corpus 94) + board fixes.
- `cef5b1a` — docs: review report.
- (this commit) — ledger: session 14 banked; campaign log continued.

## NEXT

**The phase boundary has arrived: run the dedicated full-corpus sweep
session, then open Phase 3.** The breadth grind is done (52/52 cased),
so the ledger's NEXT moves to a new phase of work — which per the
wall-clock rule means the next session is the **full corpus/e2e sweep as
a session of its own**: run all 94 cases oracle-vs-oracle
(`PYTHONHASHSEED=0`, repeats green), spot-fix whatever surfaces, and
bank the verdict-of-record. Budget note from review: the three
dispatcher-reasoning registrand cases dominate added wall-clock
(~40–60 s compile × 4 captures each — dispatcher-bearing signatures can
never hit numba's on-disk cache in a fresh process); screen-then-confirm
still applies (a short subset screen before the full run). **Immediately
after the sweep banks green, Phase 3 (the pure-Python reference core)
opens; its first action is the `networkx` dependency ask to the
operator** (the rewrite env's first runtime dependency, since
`load_graph` accepts NetworkX graphs at the public boundary) — an ask
gate, raised interactively.

## Deviations

None — the two-agent shape ran as specified (the author needed two
resume nudges to run its case batches to completion rather than idling
on background-run notifications; work and evidence unaffected).

## Asks queued

None new. Carried, non-blocking: the step-outcome
message-canonicalization option from session 13 (recommendation stands:
leave it).

## Divergences

None opened — no rewrite exists; all cases oracle-vs-oracle. (The
proxy-vs-jitted Interval `intersection` prev-seed difference and the
Query silent misparses are banked oracle behaviors on the board, not
cross-engine divergences; they become rewrite-relevant contracts in
Phase 3.)

## Idea seeds

- Phase-3 rewrite contracts already banked by this packet: keep the
  clause-level number-threshold gating; the unregistered-name asymmetry;
  the Interval prev-seed divergence (decide deliberately which semantics
  the rewrite's single core has — likely an adjudication candidate);
  bound or guard the query-filter recursion (the pinned crash-on-input
  is a natural intentional-divergence candidate).
- `interacts-unknown-predicate` for `add_closed_world_predicate`
  (carried from session 13; ready-made shape).
- `raise_errors=False` warn-skip arms (carried; plumbing validated).
- Carried: `probe_s` capture timing field; multi-path `--cases`;
  multi-rule prange characterization; artifact-schema echo of `inputs`.
