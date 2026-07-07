# Session 9 — graphml fixtures: the reverse_digraph pair and load_graphml's classes

Date: 2026-07-07 (continuing the 2026-07-06 sitting)

## Verdict

Session 8's NEXT executed, and the optional cluster rode: the one allowed
capture extension (`graphml_path` committed-fixture input) landed with three
fixtures and four seam tests, six cases took the corpus 40 → 46, targeted
oracle-vs-oracle ALL PASS on all six with same-engine repeats (the
post-review-fix rerun is the verdict-of-record), the review gate found
0 High / 1 Medium / 1 Low (both fixed in-session), and the board stands at
32/52 rows `cased` with `setting:reverse_digraph` and `fn:load_graphml`
flipped. Two characterization findings landed: the engine-side
`reverse_graph` snapshot is dead at the pin (threaded into all three kernels,
never consumed in any body), and the attribute-coercion cluster is entirely
silent — no malformed attribute value raises.

## Evidence

- **Capture extension** (`20809a1`): `inputs.graph.graphml_path` — a
  repo-relative committed-fixture path, validated (non-empty string, no
  mixing with inline keys, containment inside the repo after the review's
  F2 fix, existence) with faults exiting 2, routed to `pr.load_graphml` with
  a repo-root-resolved path; the dead `"graphml"` spine branch replaced
  rather than duplicated; the inline path byte-untouched. Documented
  limitation: inputs apply before probes, so loader raises
  (missing-file/bad-graphml) are foreclosed through this form — named
  uncovered on the board; a raising-loader probe form is future work.
  Provenance disclosure: the extension began as an uncommitted working-tree
  leftover from the aborted first launch of this packet; the author verified
  and adopted it, and the reviewer re-reviewed every line as new code —
  verdict sound as committed.
- **The reverse-digraph pair** pins the load-time reversal
  (`pyreason.py:577` → `graphml_parser.py:18-19`) with a direction-sensitive
  rule over the `chain-ab` fixture: default twin derives derived(B) over
  grounds `[['A','B']]` (readback False); on-twin derives derived(A) over
  `[['B','A']]`. `load_graph` (`pyreason.py:589-599`) carries no
  `reverse_digraph` read — cited in both purposes. The `forwarded-to-engine`
  class has **no behavioral observable**: the Program snapshot
  (`pyreason.py:1609`) is stored and threaded (`interpretation.py:69/:232/:242`
  + fp/parallel mirrors) but never consumed in any kernel body.
- **The load_graphml cases**: `load-graphml-basic` digest-equals its inline
  twin `graph-attr-parsing-on` on all seven shared probes (graphml and inline
  ground identically on this graph — authoring-time observation, reviewer
  re-derived); `load-graphml-no-attr-parse` takes the empty-tables branch
  (`pyreason.py:582-586`) — nothing derives, get_time 1.
- **The coercion cluster** (`graphml-attr-coercions` over the
  `attr-coercions` fixture, observed through
  `save_graph_attributes_to_trace=true`): in-range numeric → `[v,1]`;
  `1` → `[1,1]`; `0` and `"0,1"` → vacuous `[0,1]` with **no observable row**;
  `"0,0"` → `[0.0,0.0]`; comma-float pair → swallowed ValueError
  (`graphml_parser.py:54-55/:84-85`), composed label at `[1,1]`;
  out-of-range/nonnumeric → composed labels at `[1,1]`. All silent — the
  board's hazard cluster is characterization material, not expect-raise.
  `graphml-empty` pins the zero-node boundary: reasons clean, get_time 1.
- **The runs:** fast tier 65 passed; each of the six cases via
  `uv run python -m harness.run --cases harness/cases/<case>.json --engine-a
  oracle-env/bin/python` → ALL PASS, 4 fresh-process captures each
  (PYTHONHASHSEED=0), repeats green — author run and post-review rerun.
  **No full-corpus run** — the sweep, now 46 cases, is owed at the phase
  boundary (the standing no-silent-boundary marker).
- **Review gate:**
  [docs/reviews/2026-07-07-graphml-fixture-cases.md](../reviews/2026-07-07-graphml-fixture-cases.md)
  — F1 (Medium): `docs/analysis/surface/settings.md` claimed the engine-side
  copy is "re-read at reason time" and attributed the reversal to
  `load_graph`; both refuted at the pin and fixed. F2 (Low): `_graph_fault`
  accepted a `..`-relative path escaping the repo; containment check + test
  row added. Both fixed by the reviewer; rerun green.
- **Gates:** preflight 10/10 at session start; links gate and fast tier green
  on every commit; oracle tree clean at `e1a94af33e1f` throughout.
- **Board:** `docs/surface.md` — 32/52 rows `cased`, 20 `uncovered`;
  `equivalent` still 0/52. Uncovered classes named per row:
  `malformed-missing-file`/`malformed-bad-graphml` (foreclosed by the input
  form), `forwarded-to-engine` (dead snapshot), `type-reject` family-wide.

## Committed

- `20809a1` — harness: graphml_path fixture input — capture extension +
  3 fixtures + 4 seam tests.
- `9125514` — harness: reverse_digraph pair + load_graphml cases over
  committed fixtures (6 cases).
- `a387651` — docs: board flips for reverse_digraph and load_graphml.
- `08c29e7` — harness: review — analysis-doc refutation fixed, path
  containment tightened; report.
- (this commit) — ledger: session 9 banked; campaign log continued.

## NEXT

The last settings knobs before the phase boundary: characterize and case
`setting:parallel_computing` and the `output_to_file`/`output_file_name`
pair. (a) `parallel_computing` — read the pin first (`pyreason.py` knob site
and the `interpretation_parallel.py` dispatch): if the parallel kernel is
selectable and runs laptop-local, a twin pair over an existing
multi-timestep program (default-off readback twin; on-twin predicting
digest-equal reasoning if the kernels are equivalent — any divergence is a
finding to record precisely, not to absorb); if the parallel path cannot run
in the oracle env (compile cost, thread requirements), that characterization
— with evidence — is itself the banked result and the row's notes say so.
(b) `output_to_file`/`output_file_name` — currently forbidden by the
harness; extend the capture with a file-output probe kind (read the redirect
file the oracle writes, digest its canonicalized contents — this also
unblocks `memory_profile`'s `interaction-output` class), then a pair pinning
default-stdout vs file-redirect. Run targeted, flip the three rows, bank via
review. **When these land, the settings-knob phase is complete: the next
session after that is the owed phase-boundary full-corpus sweep**
(46+ cases, run everything, spot-fix, verdict-of-record).

## Deviations

- The session's first launch was interrupted mid-authoring, leaving an
  uncommitted capture diff; the relaunched author adopted it with line-by-line
  verification and disclosure, and the reviewer treated it as unreviewed new
  code (provenance verdict: sound). Recorded here so the adoption is on the
  ledger, not only in the reports.

## Asks queued

None blocking. Non-blocking, for operator triage at a boundary: whether a
raising-loader probe form (missing-file, bad-graphml, settings type-reject,
and the `"0.5.5"` float-guard raise at `graphml_parser.py:36`) is worth a
packet after the sweep.

## Divergences

None opened — no rewrite exists.

## Idea seeds

- A raising-loader probe form: apply-inputs-expecting-raise, covering
  `load_graphml` missing-file/bad-content, settings setter type-rejects, and
  the `"0.5.5"` in-range-guard ValueError — one probe shape unlocks four
  uncovered classes.
- The artifact schema does not echo `inputs` (the committed case JSON is the
  input record); echoing them (fixture path included) is an artifact-schema
  decision deferred by the review — worth deciding before the rewrite's
  first divergent run makes artifacts load-bearing for diagnosis.
- Carried: multi-path `--cases` for one-command targeted reruns; get-family
  accessor fingerprint probes; `REASON_ARGS` derived from the pinned
  signature.
