# Session 21 — the output surface lands after two probe-caught fixes: 14/14; board 47/52

Date: 2026-07-07 (continuing the 2026-07-06 sitting)

## Verdict

The output-surface slice landed: the output-to-file family (stdout
redirection into the confined working directory), the memory-profile
family (a **stdlib-only** peak-MB line via `resource` — no
memory_profiler dependency), the save_rule_trace family (trace CSVs,
atom-trace/store interactions, clause reordering), and the
reason-queries pair (the `queries` argument's rule-filtering
semantics). The author's 13/13 did **not** survive independent review
unamended: the reviewer's discriminating probes caught **two rewrite
defects**, fixed them in-review, and the packet passes as
**14/14 oracle-vs-rewrite PASS** (13 packet cases + 1 new regression
case). The review also found the query-filter recursion guard's
adjudication trail incomplete and filed **DIV-0001**
(intentional-divergence-proposed, queued-for-operator). Board:
eighteen rows flip, **47/52 equivalent**.

## Evidence

- **Author report:**
  [docs/reviews/2026-07-07-phase3-slice6-author.md](../reviews/2026-07-07-phase3-slice6-author.md)
  — 13/13 into `results-phase3-slice6/`; 15 new seam tests (fast tier
  257); 18 board flips claimed.
- **Review (verdict of record):**
  [docs/reviews/2026-07-07-phase3-slice6-review.md](../reviews/2026-07-07-phase3-slice6-review.md)
  — independent rerun into `results-phase3-slice6-review/`; **F1**:
  the query-emptied-ruleset `ValueError` over-fired — on an edge-heavy
  graph the pin's reorder arm rebuilds even an empty filtered ruleset
  and completes with zero rules (probed live: oracle `time=3`, pre-fix
  rewrite raised); fixed, banked as committed case
  `reason-queries-no-match-edge-heavy`. **F2**: `save_rule_trace` into
  a nonexistent folder raised bare `FileNotFoundError` where the pin
  raises pandas' `OSError: Cannot save file into a non-existent
  directory`; reproduced exactly, seam-tested. Post-fix: 14/14 PASS,
  fast tier **259**, board math re-verified mechanically (47/52, 18
  flips exact), preflight-grade hygiene confirmed (oracle byte-clean
  at `e1a94af33e1f`, no installs, tree clean).
- **DIV-0001:**
  [docs/divergences/DIV-0001.md](../divergences/DIV-0001.md) — the
  query-filter recursion guard; the ledger trail (session-14 screen +
  idea seed, session-20 design input) supports the design but carries
  no operator adjudication, which AC-6 requires for intentional
  divergences; pin-side reproducer
  `tests/test_div_0001_reproducer.py` (e2e-marked, screened green:
  the pinned process dies on the self-recursive-match input).

## Committed

- `8a7d961` — engine+tests: the output surface — stdout redirect,
  stdlib peak-MB line, trace CSVs, query filtering.
- `9dfcbbd` — chore: gitignore the slice-6 results dirs per convention.
- `b69f7b5` — docs: board — eighteen rows flip (47/52).
- `dae7345` — docs: slice-6 author report.
- `7d235a7` — engine: review fixes — the empty-ruleset raise fires on
  the pin's trigger only; missing-folder saves raise the pinned OSError.
- `737690a` — docs+tests: DIV-0001 filed with pin-side reproducer.
- `4c75b8f` — docs: independent review — two defects fixed in-review,
  14/14 post-fix.
- (this commit) — ledger: session 21 banked; campaign log continued.

## NEXT

**Land the registrand packet — the harness conditional-njit
accommodation plus the registrand family, proven oracle-vs-rewrite
over its 5 cases:** the harness change to `reference_fns.resolve()`
(conditionally njit-wrapping registered annotation/head functions so
the oracle env consumes them as the pin does while the rewrite env
consumes them plain — the accommodation session 20 named as needing
its own careful packet), then the 5 registrand-family cases run
end-to-end through it. The harness change must not disturb any
already-banked verdict: the reviewer re-runs a small spot-check of
previously-passing registrand-adjacent cases (the annotation-fn and
head-fn families) alongside the 5 new runs — still not the full
sweep. After it the un-run remainder is exactly the IPL file family
(4 cases, pyyaml approved and installed), then any
`hello-world-parallel`-class leftovers, then the Phase-3 breadth
boundary sweep as its own session.

## Deviations

None — the two-agent shape ran as specified; the review's in-review
fixes and DIV filing are the shape working, not a deviation.

## Asks queued

- **DIV-0001 adjudication (non-blocking, batched per AC-6
  queue-and-continue):** the query-filter recursion guard as
  intentional divergence — the pinned process dies (recursion) on a
  self-recursive-match `queries` input; the rewrite raises a clean,
  tested error instead. Options: (a) adjudicate the guard as
  documented intentional behavior (recommended — the failing-test
  reproducer is banked and the guarded behavior is seam-tested);
  (b) require the rewrite to reproduce the pin's process death;
  (c) defer. The surface is landed either way; only the record's
  status waits.

## Divergences

- **DIV-0001** opened (intentional-divergence-proposed,
  queued-for-operator) — see Asks queued.

## Idea seeds

- Carried: fp+`infer_edges` exception-payload asymmetry (edge-rule
  slice); registrand-behavior cases (slice-2 L3/L4); ragged-CSV /
  interval-nonnumeric / weights-dtype / delta_t cases; sweep
  durability; `probe_s` timing; multi-rule prange characterization;
  artifact-schema `inputs` echo; `interacts-unknown-predicate`;
  `raise_errors=False` warn-skip arms; O1/O2 graphml coercion quirks.
