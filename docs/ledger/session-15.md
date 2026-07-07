# Session 15 — the phase-boundary sweep: 94/94 clean, re-derived; the harness phase closes

Date: 2026-07-07 (continuing the 2026-07-06 sitting)

## Verdict

The phase-boundary full-corpus sweep ran and banked clean: **94/94 cases
ALL PASS oracle-vs-oracle** (zero divergent, zero irreproducible, zero
error), `PYTHONHASHSEED=0`, 4 fresh-process captures per case, repeats by
exact digest, total sweep wall-clock 2783 s (46 m 23 s). The spot-fix
loop was empty — no code was touched. The independent audit did not take
the report's word: all 94 verdicts were **recomputed from the preserved
376 artifacts through the real compare layer** and every hygiene claim
re-verified on the current tree. With the board at 52/52 cased and the
corpus verdict-of-record green, the harness-building phase closes;
Phase 3 (the pure-Python reference core) opens, gated on the campaign's
first rewrite dependency ask (`networkx`) — queued below and raised to
the operator at this session's close.

## Evidence

- **Screen-then-confirm honored:** a 4-case representative screen
  (hello-world, save-rule-trace-basic, memory-profile-on,
  annotation-fn-two-arg) passed, with the registrand cache-confinement
  mechanism verified to leave the oracle-env bundled cache clean (zero
  `harness.reference_fns` references) before the 46-minute run was
  committed to.
- **The sweep (verdict-of-record):**
  [docs/reviews/2026-07-07-phase3-boundary-sweep-raw.md](../reviews/2026-07-07-phase3-boundary-sweep-raw.md)
  — the full 94-row verdict table with per-case wall-clock. Slowest:
  `head-fn-grounding` 217 s, `annotation-fn-six-arg` 174 s,
  `annotation-fn-two-arg` 170 s (the three dispatcher-bearing registrand
  cases, cold on every capture, exactly as session 14's review
  predicted). Two one-time ~65 s specialization compiles
  (`conv-delta-bound`, `reason-queries-filter`) grew the cache by the
  two legitimate non-registrand `.nbc` files the audit
  timeline-attributed to the second.
- **The audit** (0 High / 0 Medium / 2 Low):
  [docs/reviews/2026-07-07-phase3-boundary-sweep.md](../reviews/2026-07-07-phase3-boundary-sweep.md)
  — verdict re-derivation via the pure `judge_case` over all 376
  artifacts (94 pass, zero problems); table ids exactly the corpus
  filenames (no dupes/phantoms); a **full** board cross-check (stronger
  than the sampled one asked for): 52/52 cased rows cite exactly the 94
  corpus ids, no orphans in either direction; 14-case artifact sample
  across every probe kind; timing column internally consistent (sum
  2783.3 s) and matching the driver CSV. L1 (fixed): a
  registrand-capture window in the raw report corrected against artifact
  mtimes. L2 (documented): `results/report.json` retains only the final
  invocation's verdict — inherent to the one-case-per-invocation
  protocol; the artifacts fully reconstruct the sweep, so recorded as a
  durability suggestion for future sweep packets, not fixed.
- **Hygiene, re-verified at review close:** oracle tree byte-clean at
  `e1a94af33e1f`; oracle-env cache 233 files with zero registrand
  residue; `git status` clean; fast tier 104 passed / 2 deselected;
  preflight 10/10 post-sweep. The author's filename deviation (the
  packet's suggested report path was already session 11's banked 53/53
  settings report) verified honest — nothing clobbered.
- **Gates:** no installs, no oracle writes, no out-of-repo writes;
  `23b3da3` verified docs-only.

## Committed

- `23b3da3` — docs: the phase-boundary sweep verdict-of-record report
  (94/94; no fixes were needed, so the session's only author commit is
  the report).
- `f474ba0` — docs: audit L1 — registrand-capture window corrected to
  artifact mtimes.
- `7398d79` — docs: audit report.
- (this commit) — ledger: session 15 banked; campaign log continued.

## NEXT

**Open Phase 3 — the pure-Python reference core — starting with the
`networkx` dependency ask (operator gate, raised at this session's
close).** Once adjudicated: set up the rewrite package skeleton (an
explicit-state reasoner core under the module-global API facade, per the
charter's Phase-3 shape: pure functions over explicit state, input-
validating parsers as entry points are written, equivalence from the
first commit), and land the first spine slice — `load_graph`/graph
representation plus the settings facade is the natural first packet,
proven by the existing graphml/settings cases running oracle-vs-rewrite
via `--engine-b`. Every banked oracle contract from sessions 7–14 (the
clause-level threshold gating, the unregistered-name asymmetry, the
Interval prev-seed divergence, the query-filter recursion crash, the IPL
trace-name fallback, state-contamination semantics) is a Phase-3 design
input; divergences the rewrite deliberately proposes go through AC-6
adjudication, never silently.

## Deviations

- The two-agent shape ran with the reviewer as an **evidence auditor**
  rather than a test-rerunner: rerunning a clean 46-minute sweep would
  be the double-verification the session protocol forbids; the audit
  instead recomputed every verdict from the preserved artifacts through
  the compare layer (a stronger check than a rerun, and cheaper). No
  case reruns were performed because no artifact doubt surfaced.

## Asks queued

- **BLOCKING — the Phase-3 `networkx` dependency ask (raised
  interactively at this session's close).** The rewrite's public
  boundary must accept NetworkX graphs (`load_graph(graph: nx.Graph)`
  at the pin) and the graphml loaders traverse NetworkX structures, so
  the rewrite env needs `networkx` as its first runtime dependency.
  Prepared command (on operator approval): `uv add networkx` in the
  campaign repo (the rewrite package's env; the oracle env is untouched
  — it already carries its own pinned copy). Options: (a) approve
  `networkx` unpinned within the resolver's compatible range —
  **recommended**: the rewrite consumes the stable Graph/DiGraph API
  surface only; (b) approve pinned to the oracle env's exact version —
  defensible for maximum comparison fidelity, at the cost of aging the
  rewrite's floor; (c) defer — Phase 3 cannot start its natural first
  packet (graph loading) and would have to open with a graph-free slice
  (settings facade only), a materially worse spine order.
- Carried, non-blocking: the step-outcome message-canonicalization
  option from session 13 (recommendation stands: leave it).

## Divergences

None opened — both engines were the oracle this session.

## Idea seeds

- Sweep durability (audit L2): a future sweep packet could have the
  driver aggregate per-case verdicts into one artifact so
  `results/report.json` isn't last-writer-wins — worth folding into any
  multi-path `--cases` work (carried seed) rather than building alone.
- Phase-3 packet shaping: the three dispatcher-bearing registrand cases
  dominate sweep wall-clock (~9.3 min of 46) — when the rewrite side
  joins the sweep, its captures won't pay numba compiles, so
  oracle-side timing stays the budget driver.
- Carried: rewrite contracts list (session 14 seeds); `probe_s` timing
  field; multi-rule prange characterization; artifact-schema echo of
  `inputs`; `interacts-unknown-predicate`; `raise_errors=False`
  warn-skip arms.
