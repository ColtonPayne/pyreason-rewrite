# Session 33 — the execution layer is signed (Option B); AC-5 closes 5/5; the cache re-baseline lands; the upstream regression gets its commit

Date: 2026-07-12

## Verdict

**The campaign's biggest gate is closed: the operator signed the
execution-layer commitment as Option B** — the pure-Python core with
the session-28 optimizations ships as the engine; the C track closed
unopened. The decision is recorded in the memo and in **ADR 0004**,
which carries the AC-5.5 version-headroom statement (dependency
surface exactly `networkx>=3.6.1` + `pyyaml>=6.0.3`, both pure
Python; no JIT pin, no build step, no interpreter ceiling). The
**AC-5 closure audit reports 5/5 bars GREEN** (two closed in-packet:
a `load_graphml` malformed-input seam test, and a standing AST gate
asserting every test carries a `proves:` docstring — 294/294). The
**operator-approved oracle-env cache re-baseline** is banked: 232
files with a committed per-file sha256 manifest, regenerated from
bare runs, the session-29 F2 import-fragility proven gone (0 harness
byte-references; 101/101 indexes unpickle clean bare). A
mid-session operator ask was also answered: **the upstream
grounding regression is attributed to a single commit** (`b01a803`,
2024-06-15; release bracket v2.3.0 → v3.0.0; shipped via upstream
PR #43) — source-reading evidence, with the discriminating
two-release run queued for the lab box. Independent review:
**approved-with-fixes** (one numeric transcription corrected in
ADR/memo against the raw captures; ~101× unaffected). Fast tier
**330**. With B signed, the session-32 boundary sweep (116/116, one
clean invocation) stands as the verdict-of-record of the shipped
layer.

## Evidence

- **Author report (packet + AC-5 audit):**
  [docs/reviews/2026-07-12-ac5-closure-author.md](../reviews/2026-07-12-ac5-closure-author.md)
- **Independent review (approved-with-fixes):**
  [docs/reviews/2026-07-12-ac5-closure-review.md](../reviews/2026-07-12-ac5-closure-review.md)
  — every claim re-derived: manifest 232/232 exact, old cache 237 /
  F2 reproduces 4/4, own disjoint 5-case e2e sample 5/5 PASS with
  banked-digest identity, AC-5 bars from own runs, dependency surface
  read from pyproject.toml.
- **ADR:** [docs/adr/0004-execution-layer-pure-python-core.md](../adr/0004-execution-layer-pure-python-core.md)
- **Cache baseline of record:**
  [docs/ledger/session-33-oracle-env-cache-baseline.md](session-33-oracle-env-cache-baseline.md)
- **Regression attribution:**
  [docs/perf/upstream-grounding-rework.md](../perf/upstream-grounding-rework.md)
- **Tests:** `uv run pytest -m "not e2e"` → 330 passed, 6 deselected
  (author and reviewer independently); oracle clone byte-clean at the
  pin throughout; no installs.

## Committed

- `370875b` — ADR 0004: execution layer = pure-Python core,
  operator-signed; AC-5.5 headroom statement.
- `af8a8cf` — memo gains the decision section; C track closed.
- `be800fb` — audit mechanizations: load_graphml seam test; `proves:`
  AST gate.
- `4f6b957` — audit report + the cache-baseline manifest.
- `c07f35c` — the upstream grounding-rework attribution report.
- `03862f4` — review fix: ADR/memo Pokec band corrected to the raw
  captures (2,620–2,701 s).
- `436a8b1` — the review document.
- (this commit) — ledger: session 33 banked; campaign log continued.

## NEXT

**Session 34: the AC-7 window-close pickup drill** — a cold Opus
subagent, given only the committed repo, states the campaign's
condition and proves the resume path executable; any gap between its
reading and the intended state is a committed-state defect, fixed and
re-drilled. Post-drill threads, for the record: (1) fold the sanders
overnight batch (200k band, 25k equivalence anchor, parallel-mode
validation) into Pokec report v3 when it lands, plus the queued
v2.3.0-vs-v3.0.0 discriminating run under the waiver; (2) the
repo-publication decision — awaiting the operator's answers
(host/visibility/name; raw results dirs in or out).

## Deviations

- **A third packet ran without a same-session independent review**:
  the grounding-regression attribution (operator-asked mid-session).
  It is a docs-only, source-reading claim explicitly labeled as
  commit-granularity evidence; its verification is the queued
  discriminating run on the lab box, named in the report itself.
- The two reviewed packets ran concurrently with the attribution
  packet (disjoint paths, explicit staging) — a departure from the
  strictly-sequential two-agent shape, without incident.

## Asks queued

- **Repo publication** (operator-initiated, awaiting parameters):
  host/visibility (recommendation: private first — the tree names the
  lab host and account, carries dangling hivemind links, and makes a
  public claim about upstream), repo name (default
  `pyreason-rewrite`), and whether gitignored `results-*` dirs ship
  (recommendation: no — reports carry the evidence).
- **Lab-box queue (under the standing waiver, when convenient):** the
  v2.3.0-vs-v3.0.0 Pokec-10k discriminating run; the overnight batch
  is already in flight.

## Divergences

- None opened or updated.

## Friction

- None new. Carried note: `docs/perf/pokec-scaling-report.md` holds a
  concurrent uncommitted operator-side edit; both agents left it
  unstaged. The review flagged (not fixed) a ≤0.7% print-precision nit
  in that file's 10k rewrite pair (26.88 / 26.76 s in the raw
  captures) — fold into its next touch.

## Idea seeds

- With B signed, the neighborhood-scoped grounding class (Pokec
  report; ADR 0004's deferred-headroom note) is the campaign's
  clearest post-window follow-on, now with its upstream pivot commit
  identified as design reference.
