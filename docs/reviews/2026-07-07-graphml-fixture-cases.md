<!-- doccode: pyreason-rewrite-docs-reviews-2026-07-07-graphml-fixture-cases -->
# Review report — graphml_path fixture input, reverse_digraph pair, load_graphml cases

Scope: the capture-extension commit (`20809a1`, `harness/capture.py` +
three fixtures + four seam tests), the six-case commit (`9125514`), and the
board-flip commit (`a387651`). One focused reviewer-fixer with no shared
session context, verifying against the pinned oracle source
(`e1a94af33e1f`) and fresh run artifacts, then applying fixes in-session.

## Provenance verdict — the adopted `_graph_fault` diff

The author disclosed that the capture extension began life as an
uncommitted, unwired working-tree leftover from an aborted prior attempt,
which it verified, repaired, and adopted. Per the packet, every line was
reviewed here as unreviewed new code, on its own merits. Verdict: **sound
as committed** (after this review's one Low tightening, F2 below).
Specifics checked:

- `REPO = Path(__file__).resolve().parent.parent` resolves the repo root
  from the module's own location, so both validation and `run_case` are
  cwd-independent; the runner already executes captures with `cwd=REPO`,
  and the stub-module seam test pins the resolved-path routing directly.
- `validate_case` calls `_graph_fault` as its final check, so the
  `return _graph_fault(...)` passthrough of `None` is equivalent to
  falling through — no later check is skipped. Non-dict `inputs.graph` is
  now rejected at validation instead of dying inside `build_graph` wearing
  the engine-failure label (exit 1); a graph fault exits 2 as usage.
- `run_case` routes `"graphml_path"` → `pr.load_graphml(str(REPO / path))`
  and leaves the inline `load_graph` path byte-identical. The replaced
  `"graphml"` branch (in the spine since `253f6be`) was indeed dead: no
  case ever carried the key and validation never admitted it — replacing
  rather than adding a parallel form is right.
- The documented limitation is real and correctly reasoned: inputs are
  applied before any probe runs, so a loader raise there fails the capture
  — existence-checking at validation forecloses `malformed-missing-file`
  and `malformed-bad-graphml` through this input form, and both are named
  uncovered on the board. The `PROBE_KINDS` spacing regression the author
  reported fixing is absent from the committed diff.
- The four seam tests test the seam (case JSON → validation verdict /
  `run_case` engine calls), and each `proves:` docstring matches its
  assertions. The fixture-acceptance test doubles as an existence pin for
  the fixture the six cases lean on.
- Fixtures are read-only inputs (the capture only ever passes the path to
  `load_graphml`), committed, and round-trip through the oracle env's
  networkx (`load-graphml-basic` digest-equaling its inline twin is the
  behavioral proof the file parses to the intended graph).

## Pin-site truth

Every file:line citation in the six case purposes, the board notes, and
the author's two contested findings was re-derived at the pin:

- `pyreason.py:569` (`load_graphml`), `:577` (`parse_graph(path,
  settings.reverse_digraph)`), `:581` (`parse_graph_attributes(
  settings.static_graph_facts)` under the `graph_attribute_parsing`
  branch at `:579`, else-branch empty tables `:582-586`), `:589-599`
  (`load_graph` — carries no `reverse_digraph` read; grep confirms the
  knob's only pyreason.py reads are `:577` and `:1609`), `:1609` (Program
  snapshot), setter `:309`/`:319` (TypeError on non-bool). All exact.
- `graphml_parser.py:15-21` (read → `DiGraph` → conditional `reverse()`
  at `:18-19`), `:27-94` (`parse_graph_attributes`), node coercions
  `:35-39` (in-range numeric → bare-key `[v,1]`), `:40-43` (composed
  label `[1,1]`), `:44-55` (comma-pair int parse, label reset, swallowed
  `ValueError/TypeError` at `:54-55`), edge mirror `:65-69`/`:84-85`.
  All exact.
- `interpretation.py:674-680` (perfect-convergence exit) and `:1538` (the
  `save_graph_attributes_to_rule_trace or not
  mode=='graph-attribute-fact'` trace gate). Exact.

**Contested finding (a) — the dead engine-side snapshot: CONFIRMED.** In
all three kernels, `reverse_graph` occurs exactly four times each: the
`__init__` parameter, the store (`interpretation.py:69`,
`interpretation_parallel.py:69`, `interpretation_fp.py:73`), the argument
threaded into the static `reason` call (`:232`/`:232`/`:241`), and the
`reason` signature (`:242`/`:242`/`:251`). Zero occurrences in any
function body — the parameter is passed and dropped. The analysis file's
"re-read at reason time" sentence was wrong, and its same line also
attributed the load-time reversal to `load_graph` (which never reads the
knob). Fixed here (F1). The author's board note stands as written.

**Contested finding (b) — the all-silent coercion cluster: CONFIRMED.**
The only exception handling in `parse_graph_attributes` is the
`except (ValueError, TypeError): pass` pair at `:54-55`/`:84-85`; no
malformed attribute value can raise out of the happy control flow
exercised by the fixture. The fresh artifacts show every claimed
coercion (below). The author's uncased observation that a string like
`"0.5.5"` passes the `replace('.','').isdigit()` guard and would raise
`ValueError` inside `float()` at `:36` also re-derives — a genuine loud
loader path, correctly left to a future raising-loader probe form.

## Non-vacuity (re-derived from the fresh post-fix artifacts)

- The reverse pair discriminates: default derives `derived(B)` `[1,1]` at
  t=1/t=2 with trace grounds `[['A','B']]`; on-twin derives `derived(A)`
  over `[['B','A']]`; readbacks False/True; get_time 3 both (no
  perfect-convergence exit, as the purposes claim). Cross-twin language is
  hedged as authoring-time observation in both purposes.
- Coercions: `nodes-score` → `N1 [0.4,1]`; `nodes-flag` → only `N3 [1,1]`
  (N2's `0` vacuously invisible); `nodes-pair` → empty (`'0,1'` vacuous);
  `nodes-pair2` → `N8 [0,0]`; composed labels `fpair-0.3,0.7` /
  `big-1.5` / `word-abc` each `[1,1]`; `nodes-bare-keys` empty; `edges-w`
  → `(N1,N2) [0.5,1]`. Exactly the purpose's claims.
- `graphml-empty` is a real boundary: steps-form outcome
  `{'raised': false}`, get_time 1, `interpretation_dict` `{'0': {}}`.
- `load-graphml-basic` digest-equals the stored `graph-attr-parsing-on`
  artifact on all seven shared probe ids (checked here against
  `results/graph-attr-parsing-on/a1.json`), pinning graphml-vs-inline
  grounding equality on this graph as the purpose claims (hedged).

## Conventions and board

Case records match the corpus shape (purpose with pin cites,
runtime_class, provenance, surface_items, comparison policy); the default
twin carries the `get_setting` readback; naming follows the knob-pair
convention. Board: both rows flipped to cased; the six ids joined to
exactly the rows their `surface_items` cover and nowhere else (checked
programmatically in both directions across all rows); `fn:load_graphml`
notes name the uncovered classes (interacts-static_graph_facts over this
path, malformed-missing-file, malformed-bad-graphml) and
`setting:reverse_digraph` notes name forwarded-to-engine (dead snapshot)
and type-reject. One judgment call reviewed and accepted:
`graphml-attr-coercions` lists `setting:graph_attribute_parsing` without
setting or reading it back — the default-True parse is that case's entire
observable, so the coverage is genuine. Session totals: the three commits
touch only their listed files; the 14 changed board rows are all
in-packet; `setting:parallel_computing`, `output_to_file`,
`output_file_name` untouched; oracle tree clean at `e1a94af33e1f`; no
dependency files changed.

## Fixed

- **F1 (Medium, analysis correctness)** —
  `docs/analysis/surface/settings.md` `setting:reverse_digraph`: the
  read-at-load-time class attributed the reversal to `load_graph` and
  claimed the engine-side `reverse_graph` copy "is re-read at reason
  time". Both refuted at the pin (kernel grep above; `load_graph` never
  reads the knob). The section now records the dead-snapshot evidence
  under forwarded-to-engine, corrects the reversal site to
  `load_graphml`, and notes the refuted earlier claim. This is the fix
  the author's finding 1 deliberately left to review.
- **F2 (Low, capture validation)** — `_graph_fault` accepted a
  `..`-relative `graphml_path` resolving outside the repo tree,
  contradicting its own committed-fixture contract (absolute paths were
  rejected but `../elsewhere.graphml` was not). Added a resolved
  containment check (`(REPO / path).resolve().is_relative_to(REPO)`)
  before the existence check — available on both interpreters (repo
  ≥3.11, oracle env 3.10) — plus a fault row in the rejection seam test.
  No committed case is affected.

## Deferred with rationale

- The artifact does not echo `inputs` (fixture path included); it names
  the case by id and the committed case JSON is the input record — a
  pre-existing property of the artifact schema for every input form, not
  something this extension changed. Noted, not fixed: echoing inputs is
  an artifact-schema decision beyond this packet's one small extension.
- A raising-loader probe form (missing-file, bad-graphml content,
  settings type-reject) stays future work, as the author asked — the two
  classes are named uncovered on the board.

Blocking findings: none.

## Rerun evidence (post-fix, verdict of record)

- `uv run pytest -m "not e2e"` — 65 passed, 2 deselected.
- `uv run python -m harness.run --cases harness/cases/<case>.json
  --engine-a oracle-env/bin/python` for each of
  `reverse-digraph-default`, `reverse-digraph-on`, `load-graphml-basic`,
  `load-graphml-no-attr-parse`, `graphml-attr-coercions`,
  `graphml-empty` (one case per invocation) — ALL PASS on all six, fresh
  same-engine repeat captures; every non-vacuity item above was
  re-derived from these fresh artifacts.
