<!-- doccode: pyreason-rewrite-docs-reviews-2026-07-07-phase3-slice5-review -->
# Phase 3, slice 5 — the graph surface + loader happy paths (independent review)

- session: 20 · 2026-07-07 · reviewer-fixer packet (no shared context with the author)
- scope reviewed: the full diff `ef471fd..ccc11d6` as a coherent whole, graded
  against the pinned source at `e1a94af33e1f` and the slice-5 packet spec
- verdict: **packet PASSES with zero defect findings.** Independent rerun:
  **16/16 pass** into `results-phase3-slice5-review/`; fast tier **242
  passed** (surface-inventory gate green); digest cross-check: rewrite b1
  digests equal the banked session-15 sweep's oracle a1 digests on **16/16**
  cases, probe for probe; **5/5 reviewer discriminating probes pass** both
  engines; all eleven surface flips verified row-by-row; all three claimed
  coercion-cluster reproductions verified against the pinned source and
  empirically against the installed oracle. Two reviewer observations
  recorded (below) — oracle quirks the rewrite reproduces correctly, no fix
  warranted, no committed-case mismatch, so no DIV record.

## Findings, by severity

**None.** No rewrite defect, no evidence gap, no dishonest claim survived
verification. Review found nothing to fix; the only review commit is this
report.

### Reviewer observations (oracle quirks, correctly reproduced — recorded, not absorbed)

**O1 — the inverted integer pair `'1,0'` is a fourth silent vanishing
variant, and it routes through the inconsistency machinery.** The pinned
ladder accepts any in-range integer comma pair with no ordering check
(graphml_parser.py:44-55), so `'1,0'` coerces to the out-of-order bound
[1,0]. Applied at t=0 it is inconsistent with the initial [0,1], and the
resolve arm pins the world entry to **static [0,1]** — verified in the
rewrite's world state directly (`inv: [0.0,1.0] static`, the
resolve-inconsistency signature) — while leaving **no observable anywhere**:
no filter row, no interp-dict entry, and no trace row even with
`atom_trace` and `save_graph_attributes_to_trace` both on. Probed on a node
and an edge attribute (`rv-ladder-extra`, X3 + the X1→X2 edge); both
engines byte-identical on every probe. The static pin means later facts on
that label are also frozen out — one notch beyond the author's follow-up #3
(`0`/`'0,1'` leave no row but at least stay fluent). Belongs on the
oracle-bug-candidate list beside the author's three.

**O2 — the comma-pair arm tolerates whitespace the numeric-string arm
rejects.** `'0, 1'` and `'1, 1'` fail the `isdigit` branch but `int()`
strips the spaces (graphml_parser.py:48-49), so `'1, 1'` becomes the [1,1]
bound under the bare key and `'0, 1'` silently vanishes like `'0,1'`.
Likewise `'-0,1'` parses (`int('-0')` = 0) and vanishes, while `-0.5` /
`'-0.5'` / `'2'` compose `key-value` labels at [1,1]. All probed; both
engines identical (the rewrite carries the ladder verbatim, so this follows
by construction — the probe makes it evidence). Documentation-grade only.

## Semantic fidelity to the pinned graph boundary

Read side-by-side, not trusted from the report:

- **`_graph.parse_graphml`** is the pinned `GraphmlParser.parse_graph`
  (graphml_parser.py:15-20) line for line: `read_graphml` → `DiGraph`
  coercion → conditional `.reverse()`. Both engines take typed values from
  `read_graphml` itself, so the ladder sees identical inputs.
- **`_graph._attribute_to_label_bound`** is the pinned coercion ladder
  (graphml_parser.py:35-55) exactly, including the comma-pair check running
  last so it overrides, the swallowed `(ValueError, TypeError)`, and the
  int-typed upper bound 1 on the numeric arm. The node and edge arms of the
  pin (:35-55 vs :65-85) are duplicates; the rewrite's single helper is
  faithful to both.
- **`load_graphml`** (pyreason.py:569-586): reads `reverse_digraph` at load
  time on this path only; `load_graph` (pyreason.py:589-608) still never
  consults it — the pinned knob asymmetry, held by
  `test_load_graph_never_reads_reverse_digraph` and the reverse-digraph
  case pair. Both load paths run the same attribute-parsing branch,
  including the reset-to-empty else arm; the extraction into
  `_parse_attributes_under_settings` is reuse of the pin's duplicated
  branch, not a semantic change.
- **`add_closed_world_predicate`** (pyreason.py:1122-1130 → set,
  :1613-1617 → labels at reason time): the rewrite registers into
  `state.closed_world_predicates` (set — the duplicate add is a no-op) and
  converts to `Label`s at reason time (`_state.py:274`). The satisfaction
  branch in `_grounding.is_satisfied_node/is_satisfied_edge` matches the
  pinned kernel (interpretation.py:1757-1778): absent label → `[0,0] in
  clause_bnd`; present at exactly [0,1] → same; otherwise the ordinary
  `world.is_satisfied`. The **edge** branch — which the committed
  closed-world-on case never reaches — is pinned by my `rv-cwa-edge` probe.
- **`save_graph_attributes_to_trace`** gates
  (interpretation.py:297/:373/:1538/:1657) and the loader happy paths were
  pre-session code; their equivalence evidence is the 16-case run plus the
  probes below.

## The three claimed coercion reproductions — verified

Against the pinned source (lines above) AND empirically against the
installed oracle (my rerun's `a1` captures,
`results-phase3-slice5-review/graphml-attr-coercions/`):

1. **Comma-float pairs never become bounds** — CONFIRMED: oracle banks
   `fpair-0.3,0.7` at [1,1] on N5 and the bare-key probe
   (`fpair`/`big`/`word`) is empty.
2. **All-silent malformed values** — CONFIRMED: `big-1.5` and `word-abc`
   compose at [1,1]; every capture completed, nothing raised anywhere in
   the cluster (and O1/O2 extend the same silence to four more input
   classes).
3. **The `0` / `'0,1'` vanishing act** — CONFIRMED: `flag` shows only N3
   (the value-1 node; N2's `flag=0` leaves no row) and `pair` is empty;
   `pair2='0,0'` lands [0,0] under the bare key.

The rewrite's `b1` matches the oracle probe-for-probe on all of it —
equivalence-PASS under AC-6, defects deliberately reproduced.

## Discriminating probes (overfitting hunt) — 5 probes, both engines

Ad-hoc cases (temporary untracked `probe-tmp/` during the run, since
`graphml_path` must resolve inside the repo; removed after; artifacts in
the session scratchpad) through the same harness, PYTHONHASHSEED=0,
oracle-env vs scripts/rewrite-python — **ALL PASS (5 cases)**:

| probe | seam it pins beyond the 16 cases | verdict |
|---|---|---|
| rv-ladder-extra | graphml values no fixture carries: `-0.5` (double + string), `'1,0'` inverted pair on node AND edge, `'0, 1'`/`'1, 1'` whitespace pairs, boolean attr.type true/false, `'2'`, `'0.50'`, `'-0,1'` — 11 filter probes + interp dict + both traces | pass (O1/O2 observed, identical both engines) |
| rv-reverse-edge-attr | reverse_digraph × attribute-bound edges: `w=0.6` rides the reversed edge — w row on (B,A), `hi(x) <-1 w(x,y):[0.5,1]` derives hi(B) not hi(A) | pass |
| rv-cwa-collide | closed-world pred colliding with facts and a rule head on the same predicate: busy(A) [1,1] fails the [0,0] clause; busy(B) stated explicitly at the vacuous [0,1] reads as [0,0] (the explicit-vacuous arm); busy(C) absent; `busy(x) <-2 avail(x)` flips B and C to [1,1] at t=3 mid-run | pass |
| rv-cwa-edge | the closed-world branch on the EDGE satisfaction path (unreached by any committed case): strangers derives on (A,C) only, knows(A,B) [1,1] blocks (A,B) | pass |
| rv-csv-static-multistep | the committed facts.csv reasoned PAST its windows (timesteps=4 vs end 2): the static `'yes'` fact keeps reapplying, the windowed facts stop, the popular cascade agrees at the horizon | pass |

No divergence on any probe — the graph boundary is not overfit to the 16
committed cases on any seam I could reach.

## Independent rerun + digest cross-check

- Fast tier: `uv run pytest -m "not e2e"` → **242 passed, 2 deselected**
  (author's claim confirmed; includes the 22 new seam tests and the
  6 surface-inventory gate tests).
- 16-case rerun: fresh dir `results-phase3-slice5-review/` (untracked,
  gitignored by the author's `ccc11d6` alongside `results-phase3-slice5/`,
  consistent with the slice convention) → **ALL PASS (16 cases)**, exit 0.
- Digest cross-check: my rerun's rewrite `b1` per-probe digests vs the
  banked session-15 sweep's oracle artifacts (`results/<case>/a1.json`) —
  **16/16 cases match on every digest** (6+5+5+7+7+12+3+7+7+6+6+6+5+5+7+7
  probe digests), tying the rewrite to the sweep of record, not just to
  today's oracle run.

## surface.md — eleven flips verified row-by-row

Mechanically recomputed, not trusted: the union of `status: pass` verdicts
across all banked `results-phase3-slice[1-5]*/report.json` files (72
distinct cases, zero non-pass verdicts) covers **every case in every
flipped row's `cases` field** — fn:load_graphml (6 cases),
fn:add_closed_world_predicate (2; closed-world-off passed in a prior
slice), the five loaders (2 each), fn:filter_and_sort_edges (13),
setting:graph_attribute_parsing (5), setting:reverse_digraph (2),
setting:save_graph_attributes_to_trace (3). All 29 `equivalent` rows hold
the same invariant; **no cased row's full case list is covered** (so no
missed or premature flip anywhere); count **29/52 correct**. The slice-5
dependencies are additionally re-proven by my own rerun.

## Tests

The 22 author seam tests read line-by-line: every `proves:` docstring
matches what the test asserts; the graphml tests assert through the facade
(the harness seam) over the same committed fixtures the equivalence cases
load; the 9-arm ladder parametrization pins the pure helper AND
`test_graphml_coercion_cluster_observable_rows` re-pins the cluster at the
observable seam (rows/trace/get_time), so the I/O seam is tested, not just
the helper. Pin line citations in docstrings spot-checked against the
oracle source — accurate. Fast tier fully green.

## Design bars (AC-5) and the no-new-ADR claim

The `ef471fd..ccc11d6` diff touches exactly `src/pyreason/__init__.py` (a
one-line facade delegation), `src/pyreason/_graph.py` (two pure functions +
the extracted shared branch), the two test files, `docs/surface.md`, the
author report, and `.gitignore`. No new state fields (`_state.py`
untouched), no engine or schedule change, no dead scaffolding (every new
function is reached: facade → `load_graphml` → `parse_graphml` +
`_parse_attributes_under_settings` → the pre-existing
`parse_graph_attributes`), no hidden cross-run state (pure functions over
`EngineState`). **The no-new-ADR claim is honest** — ADRs 0002/0003 are
undisturbed by this shape. Commit messages match their contents.

## Hygiene

- No installs, no dependency changes: `git diff ef471fd..HEAD --
  pyproject.toml uv.lock` empty; no new env.
- Oracle tree byte-clean: `git -C oracle/pyreason status --short` empty,
  HEAD = `e1a94af33e1f…` = oracle/PIN.
- Banked results dirs unmodified: `results/` mtime 05:21 (session-15 sweep),
  slice1–4 dirs' mtimes all predate the author's session-20 commits; the
  digest cross-check reads the banked artifacts and matches. `git ls-files
  'results*'` → 0 tracked files.
- No security framing anywhere in the session-20 diff (scanned).
- Preflight doctor 10/10 at review; `git status` clean at close; hooks not
  bypassed; full e2e sweep not run (fast tier + the 16 packet cases + 5
  probes only).

## Verdict

**Packet passes as landed.** The graph boundary is semantically faithful to
the pin on every arm the 16 cases and my 5 probes reached — including the
all-silent coercion cluster, the load-path knob asymmetry, the edge-side
closed-world branch, and attribute bounds riding reversed edges. The
evidence reproduces independently and ties back to the banked sweep of
record. Zero fixes needed; O1 (the `'1,0'` static-pin vanishing variant)
and O2 (whitespace-tolerant comma pairs) ride to the oracle-bug-candidate
follow-up list.

## Repro

```
# fast tier (242)
uv run pytest -m "not e2e"

# the 16-case rerun (stage the committed cases, then run)
mkdir -p /tmp/slice5-review-cases && for c in load-graphml-basic \
  load-graphml-no-attr-parse graphml-attr-coercions graphml-empty \
  reverse-digraph-default reverse-digraph-on graph-attr-parsing-on \
  graph-attr-parsing-off save-graph-attrs-to-trace-on \
  save-graph-attrs-to-trace-off closed-world-on fact-from-csv-basic \
  fact-from-json-basic rule-from-csv-basic rule-from-json-basic \
  rules-from-file-basic; do cp harness/cases/$c.json /tmp/slice5-review-cases/; done
PYTHONHASHSEED=0 uv run python -m harness.run --cases /tmp/slice5-review-cases \
  --engine-a oracle-env/bin/python --engine-b scripts/rewrite-python \
  --results results-phase3-slice5-review-repro

# digest cross-check (rewrite b1 vs the banked sweep's oracle a1), per case:
# python3 -c 'import json; a=json.load(open("results/<case>/a1.json"))["digests"]; \
#   b=json.load(open("results-phase3-slice5-review-repro/<case>/b1.json"))["digests"]; \
#   assert a==b'

# O1 world-state check (rewrite; the oracle side is the matching harness probe):
# load a one-node graph with inv='1,0', reason 1 timestep, then inspect
# interp.interpretations_node['X3'].world — 'inv' sits at [0,1] static with
# no trace row despite atom_trace + save_graph_attributes_to_trace on.
```
