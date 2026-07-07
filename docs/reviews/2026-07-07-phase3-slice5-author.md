<!-- doccode: pyreason-rewrite-docs-reviews-2026-07-07-phase3-slice5-author -->
# Phase 3, slice 5 — the graph surface + loader happy paths (author report)

- session: 20 · 2026-07-07 · author packet
- verdict: **16/16 equivalence PASS** oracle-vs-rewrite (`results-phase3-slice5/report.json`, exit 0, ALL PASS; 4 fresh-process captures per case, same-engine repeats digest-stable, PYTHONHASHSEED=0); fast tier **242 passed** (220 existing + 22 new seam tests)
- code: `1006766` (load_graphml + 22 seam tests), `859b8ad` (surface flips), plus this commit (report)
- board: 11 surface rows flip to `equivalent` — **29/52**
- DIV records: none — no cross-engine mismatch surfaced
- ADR: none — ADRs 0002/0003 still hold unchanged (rationale below)

## Where the session started

Single-capture pre-check of the packet's 16 cases against the banked
session-15 oracle artifacts split the slice cleanly in two:

- **10 of 16 already digest-equal on the pre-session core.** The
  graph-attr-parsing pair, save-graph-attrs-to-trace pair, closed-world-on,
  and the five loader-basic cases exercise code sessions 16–19 had already
  landed: `_graph.parse_graph_attributes` (the coercion ladder, built for the
  inline `load_graph` path), the closed-world satisfaction branch in
  `_grounding.is_satisfied_node/edge` (threaded since the session-17 spine —
  its off twin passed then), and the five `_loaders` functions (whose
  malformed arms landed in session 16; their happy paths were already written,
  just never proven).
- **The 6 graphml cases had no engine surface to hit at all** —
  `load_graphml` did not exist on the facade, so every `graphml_path` case
  (`load-graphml-basic`, `load-graphml-no-attr-parse`,
  `graphml-attr-coercions`, `graphml-empty`, and the reverse-digraph pair)
  would have failed capture on a missing binding.

The slice therefore reduced to: land `load_graphml` inside the existing
one-core design, pin the graphml arms and the already-written-but-unproven
knob/loader arms with seam tests, and bank the 16-case proof.

## The graph boundary's pinned semantics, and how the rewrite reproduces them

**Parse (pyreason.py:569-586 → graphml_parser.py:15-20).** The pin reads the
file with `nx.read_graphml`, coerces to `nx.DiGraph`, and — only on this
path — reverses every edge when `settings.reverse_digraph` is on, read at
load time. The rewrite's `_graph.parse_graphml` is those three lines
verbatim; `_graph.load_graphml` assigns the parsed graph and runs the same
attribute-parsing branch `load_graph` runs (extracted into
`_parse_attributes_under_settings` rather than duplicated). `load_graph`
deliberately still never reads `reverse_digraph` — the pinned load-path knob
asymmetry, pinned by `test_load_graph_never_reads_reverse_digraph` and
differentially by the reverse-digraph pair riding `load_graphml`. Typed
attribute values (int/float/str per the file's `attr.type` keys) come from
`read_graphml` itself in both engines, so the coercion ladder downstream
sees identical inputs.

**The silent-coercion cluster (graphml_parser.py:27-94), reproduced
deliberately.** The rewrite's `_attribute_to_label_bound` is the pinned
ladder line for line, and the slice's coercion case + 9-arm parametrized
seam test hold every class to it:

| input | pinned outcome | observable |
|---|---|---|
| numeric (or numeric-string) v ∈ [0,1], e.g. `score=0.4`, edge `w=0.5` | bound `[v, 1]` under the bare key | row `[0.4,1]` / `[0.5,1]` |
| `flag=1` | `[1,1]` | row `[1,1]` |
| `flag=0` | coerces to the **vacuous `[0,1]`** | **no row** — the no-change update is suppressed at the gate |
| `pair='0,1'` (int comma pair in range) | both bounds set → vacuous `[0,1]` | **no row** |
| `pair2='0,0'` | both bounds set, label reset to the bare key | row `[0,0]` |
| `fpair='0.3,0.7'` (comma **float** pair) | `int()` ValueError **silently swallowed** (graphml_parser.py:54-55), falls through | composed label `fpair-0.3,0.7` at `[1,1]`; nothing under `fpair` |
| `big=1.5` (out of range), `word='abc'` (non-numeric) | composed label `key-value` at `[1,1]` | `big-1.5` / `word-abc` rows; nothing under bare keys |

No malformed value raises anywhere in the cluster — the session-9
characterization ("all silent at the pin") held at re-verification and the
rewrite reproduces it exactly. **These are deliberately-reproduced oracle
defects and are named as oracle-bug-candidate follow-ups** (see below);
matching the pin is AC-6's default meaning of correct, so
`graphml-attr-coercions` is an equivalence PASS.

**Empty graph (bound-empty-graph).** The zero-node fixture parses into an
empty DiGraph, attribute parsing walks nothing, and `reason(timesteps=1)`
completes without raising — `get_time` 1, `get_dict() == {0: {}}` — same in
both engines.

**`save_graph_attributes_to_trace` (interpretation.py:297/:373/:1538/:1657).**
On: `graph-attribute-fact` rows enter both traces — the t=0 gate
applications plus one static-reapplication row per later timestep. Off
(default): every such row is suppressed; derivation itself is untouched
(the on/off twins' derived bounds are digest-equal). The rewrite's gates
were already in `_interpretation`; the pair is now proven and seam-tested.

**`add_closed_world_predicate` (pyreason.py:1122-1130,
interpretation.py:1757-1775).** A bare `set.add` at registration (the
duplicate add in the case is a set-level no-op), consumed at reason time:
a registered predicate whose bound is absent or the vacuous `[0,1]` reads
as `[0,0]` in satisfaction checks, so the `busy(x):[0,0]` clause fires for
the never-stated nodes while the known-`[1,1]` node still fails it. Already
implemented in `_grounding.is_satisfied_node/edge` (verified side-by-side
against the pinned kernel this session); the on arm is now proven.

**Loader happy paths (pyreason.py:652-1412).** The five loaders' parsed
content demonstrably reaches the engine and reasoning: CSV facts (header
skip, quoted comma-bearing edge fact with an interval bound, auto-named
`fact_2` with truthy `'yes'` static, short-row padding), JSON facts (given +
auto-counter names, windows, bounds, static), CSV rules (explicit clause
bound `[0.5,1]`, auto-named `rule_1`, quoted row with `infer_edges` coerced
true — the inferred `team` edges land in the edge trace), JSON rules (all
four accepted forms: plain, custom_thresholds list, custom_thresholds dict
with the `'1'` key int-parsed and clause 0 defaulted, weights), and the
rules text file (comment/blank skipping, `rule_{i+offset}` naming over one
preloaded rule, the file-loaded `trendy` rule firing at t=2). All were
already implemented; the accessor fingerprints and traces now compare equal
to the oracle's.

## Design: no ADR needed

The boundary lands as two pure functions in `_graph.py` (`parse_graphml` +
the shared `_parse_attributes_under_settings`) writing the same four
explicit-state fields `load_graph` writes, plus a one-line facade
delegation. Nothing about ADR 0002's explicit-state spine (pure functions
over `EngineState`, program built at reason time) or ADR 0003's one-semantics
-core/two-schedules shape moves; no new state fields, no new engine
concepts, no schedule changes. The only structural change is extracting the
previously-inline attribute-parsing branch so the two load paths share it —
reuse, not redesign.

## Per-case verdicts (all PASS, `results-phase3-slice5/`)

Wall-clock from the run's artifacts (capture-internal timing; `import_s` +
total reason/steps seconds, engine A = pinned oracle, engine B = rewrite;
rewrite step times round to 0.000 at the artifact's 3-decimal resolution):

| case | verdict | oracle import/reason (s) | rewrite import/reason (s) |
|---|---|---|---|
| closed-world-on | pass | 1.83 / 2.807 | 0.101 / 0.000 |
| fact-from-csv-basic | pass | 1.61 / 3.468 | 0.096 / 0.000 |
| fact-from-json-basic | pass | 1.54 / 3.339 | 0.098 / 0.000 |
| graph-attr-parsing-off | pass | 1.58 / 2.905 | 0.063 / 0.000 |
| graph-attr-parsing-on | pass | 1.47 / 2.706 | 0.064 / 0.000 |
| graphml-attr-coercions | pass | 1.47 / 2.724 | 0.065 / 0.000 |
| graphml-empty | pass | 1.51 / 1.704 | 0.066 / 0.000 |
| load-graphml-basic | pass | 1.50 / 2.736 | 0.067 / 0.000 |
| load-graphml-no-attr-parse | pass | 1.57 / 2.914 | 0.065 / 0.000 |
| reverse-digraph-default | pass | 1.48 / 2.726 | 0.067 / 0.000 |
| reverse-digraph-on | pass | 1.50 / 2.744 | 0.061 / 0.000 |
| rule-from-csv-basic | pass | 1.52 / 3.590 | 0.064 / 0.000 |
| rule-from-json-basic | pass | 1.52 / 3.663 | 0.066 / 0.000 |
| rules-from-file-basic | pass | 1.53 / 2.905 | 0.076 / 0.000 |
| save-graph-attrs-to-trace-off | pass | 1.52 / 2.725 | 0.068 / 0.000 |
| save-graph-attrs-to-trace-on | pass | 1.50 / 2.737 | 0.064 / 0.000 |

Pass criterion per case: 4 fresh-process captures (a1/a2/b1/b2), same-engine
repeats digest-stable, A-vs-B probe digests equal. The results directory is
untracked per the slice convention; `results/` and the slice-1..4 dirs were
not written to.

## Board

11 rows flip to `equivalent` — every case in each row's `cases` field has
now passed oracle-vs-rewrite across `results-phase3-slice1..5`:

`fn:load_graphml`, `fn:add_closed_world_predicate`, `fn:add_fact_from_json`,
`fn:add_fact_from_csv`, `fn:add_rules_from_file`, `fn:add_rule_from_csv`,
`fn:add_rule_from_json`, `fn:filter_and_sort_edges` (its last three cases —
the graphml trio — rode this slice), `setting:graph_attribute_parsing`,
`setting:reverse_digraph`, `setting:save_graph_attributes_to_trace`.

New fraction: **29/52** rows equivalent (was 18/52). The flip set was
computed mechanically (every `cased` row whose full case list ⊆ the passed
set); notably `fn:load_graph`, `fn:reason`, `fn:add_rule`, `fn:add_fact`,
`setting:verbose`, `setting:atom_trace` and the dsl rows stay `cased` —
each still carries the memory-profile/output-file cases no slice has run
yet. Inventory gate green (`tests/test_surface_inventory.py`, 6 passed).

## Oracle-bug-candidate follow-ups (deliberately reproduced, equivalence-PASS)

1. **Comma-float pairs never become bounds** — `'0.3,0.7'` hits `int()`'s
   ValueError, silently swallowed (graphml_parser.py:54-55), and composes a
   junk label `fpair-0.3,0.7` at `[1,1]` instead of the plausible-intent
   `[0.3,0.7]` bound.
2. **Malformed attribute values are all-silent** — out-of-range numerics
   (`1.5`) and non-numeric strings (`'abc'`) compose `key-value` labels at
   `[1,1]`; no diagnostic anywhere in the cluster.
3. **The `0` / `'0,1'` vanishing act** — both coerce to the vacuous `[0,1]`,
   whose no-change update is suppressed, so a stated attribute leaves no
   observable row at all.

## Deviations from the packet

None. No installs, no oracle-tree writes, no dependency changes; the full
e2e sweep was not run (fast tier + the 16 packet cases only, per the
test-tier rule). No queued-ask recommendations from this slice — nothing
here needed pyyaml or any other blocked input.

## Repro

```
uv run pytest -m "not e2e"                       # fast tier: 242 passed
mkdir -p /tmp/slice5-cases && for c in load-graphml-basic load-graphml-no-attr-parse \
  graphml-attr-coercions graphml-empty reverse-digraph-default reverse-digraph-on \
  graph-attr-parsing-on graph-attr-parsing-off save-graph-attrs-to-trace-on \
  save-graph-attrs-to-trace-off closed-world-on fact-from-csv-basic fact-from-json-basic \
  rule-from-csv-basic rule-from-json-basic rules-from-file-basic; do \
  cp harness/cases/$c.json /tmp/slice5-cases/; done
PYTHONHASHSEED=0 uv run python -m harness.run --cases /tmp/slice5-cases \
  --engine-a oracle-env/bin/python --engine-b scripts/rewrite-python \
  --results results-phase3-slice5    # 16/16 ALL PASS (use a fresh --results dir to re-run)
```
