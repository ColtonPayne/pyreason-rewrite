# Session 7 — the load-time graph knobs: attr parsing, static stamp, trace inclusion

Date: 2026-07-06 (same sitting as sessions 0–6)

## Verdict

Session 6's NEXT executed as predicted — no capture surgery: six cases (three
load-time graph-knob on/off pairs over one shared attribute-bearing inline
graph) took the corpus 28 → 34, targeted oracle-vs-oracle ALL PASS on all six
with same-engine repeats (author run, then the post-review-fix rerun as the
verdict-of-record), the review gate confirmed 0 High / 0 Medium / 1 Low (fixed
in-session), and the board stands at 27/52 rows `cased` with
`setting:graph_attribute_parsing`, `setting:static_graph_facts`, and
`setting:save_graph_attributes_to_trace` flipped. Mid-session the operator
reshaped the session protocol (Deviations): two agents per session
(author + independent reviewer-fixer), no orchestrator re-verification, and
the full-corpus e2e sweep moved out of the per-session loop to phase
boundaries — so this session deliberately banks no full-corpus run JSON.

## Evidence

- **Case design:** one shared inline graph across all six — node
  `A(special=1)`, edge `A->B(rel=1)`, rule `derived(y) <-1 special(x),
  rel(x,y)`, **no user facts** — the attribute-to-fact conversion
  (`graphml_parser.py:27-94` at the pin) is the sole bound source, so each
  knob's effect is unmasked. Pairs differ only in the target knob; default
  twins leave the knob unset with a `get_setting` readback probe.
- **The parsing pair** pins the load-time gate (`pyreason.py:602-608`, and
  :580 for load_graphml): off leaves the graph-fact lists empty, nothing
  grounds, and perfect convergence exits at t=0 — trace-node empty, get_time
  1 vs 3, one frame per filter probe vs three.
- **The static pair** (persistent=false in both, the interaction-persistent
  class) pins the staticness stamp (`graphml_parser.py:60/:90`) against the
  per-timestep reset (`interpretation.py:260-273`): fluent attribute bounds
  reset at t=1 so the rule grounds only at t=0 and derived(B) loses its t=2
  re-derivation (get_time 2 vs 3) — exactly the bounds-survive-the-reset
  contrast session 6's NEXT named.
- **The trace pair** pins the trace gates (`interpretation.py:1538/:1657`
  and the static-reapplication branches :297/:373 node-side, edge analogues):
  on adds `graph-attribute-fact` rows per timestep while `nodes-derived` and
  `get_time` stay digest-equal across the twins — trace contents only, never
  derived bounds.
- **The runs:** fast tier 61 passed; each of the six cases via
  `uv run python -m harness.run --cases harness/cases/<case>.json --engine-a
  oracle-env/bin/python` → ALL PASS, 4 fresh-process captures each
  (PYTHONHASHSEED=0), same-engine repeats green — author run and post-review
  rerun. Cross-twin comparisons are authoring-time observations (hedged as
  such in every purpose that carries one); the harness judges each case
  within one knob position. **No full-corpus run this session** — the 34-case
  sweep is owed at the next phase boundary (Deviations).
- **Review gate:**
  [docs/reviews/2026-07-06-load-time-graph-knob-cases.md](../reviews/2026-07-06-load-time-graph-knob-cases.md)
  — the new reviewer-fixer form: an independent worker re-derived every cited
  pin site, re-derived pair non-vacuity from the run artifacts, checked
  conventions and scope, applied its one Low fix itself (edge-side source
  citations in the trace-pair purposes; purpose-text only), and reran the
  targeted evidence green.
- **Gates:** preflight 10/10 at session start; links gate green on every
  commit; fast tier green at every commit.
- **Board:** `docs/surface.md` — 27/52 rows `cased`, 25 `uncovered`;
  `equivalent` still 0/52 — no rewrite exists, `cased` marks harness coverage
  only.

## Committed

- `9473457` — harness: load-time graph-knob cases — attr parsing, static
  stamp, trace inclusion.
- `93692d6` — harness: review fix (trace-pair purpose citations); review
  report.
- `519fabf` — docs: board flips for the three load-time graph knobs.
- `fa77377` — skill: two-agent session shape; full-corpus sweep only at
  phase boundaries.
- (this commit) — ledger: session 7 banked; campaign log started.

## NEXT

Case the remaining no-surgery settings knobs — three settings-only pairs over
existing probe kinds: a `canonical` pair (`setting:canonical` — pure alias of
persistent at the pin, getter and setter share persistent's field; pin
last-write-wins via readbacks of both knobs plus persistent-driven reset
behavior), an `abort-on-inconsistency` pair (`setting:abort_on_inconsistency`
— no consumption site anywhere in the engine per the board's hypothesis; twin
an inconsistency-triggering program and predict digest-equality on all
reasoning probes, knob readback only differing), and a `memory-profile` pair
(`setting:memory_profile` — observational wrapper, reasoning digests
predicted equal). Run each pair oracle-vs-oracle targeted (no corpus sweep),
flip `setting:canonical`, `setting:abort_on_inconsistency`, and
`setting:memory_profile`, bank via review. (`setting:reverse_digraph` is
deliberately not in this packet: the load_graph path ignores it, so its pair
rides a `fn:load_graphml` graphml-fixture packet — likely a small capture
extension — as its own follow-on; `setting:parallel_computing` and the
`output_to_file`/`output_file_name` pair need their own characterization.)

## Deviations

- **Operator steer, mid-session (2026-07-06, in-chat):** (1) each session
  runs exactly two agents — an author and an independent reviewer-fixer who
  applies fixes itself and reruns the targeted evidence; (2) the review *is*
  the verification — the orchestrator no longer re-runs what the review
  verified; (3) the full e2e corpus sweep leaves the per-session loop: it
  runs only at phase boundaries as a dedicated run-everything-and-spot-fix
  session. `.claude/commands/campaign.md` updated in `fa77377`; supersedes
  session 6's once-per-session full-run form. Consequence: no
  `session-7-oracle-vs-oracle.json` — the targeted six-case runs plus the
  review rerun are this session's differential evidence, and **a 34-case
  full-corpus sweep is owed at the next phase boundary** (this line is the
  no-silent-boundary marker).
- Session 6's NEXT sketched the off-twins as vanishing facts/rows only; the
  pinned perfect-convergence exit (`interpretation.py:674-680`) additionally
  shifts `get_time` and filter frame counts in pairs 1–2 (3 vs 1, 3 vs 2).
  Mechanism traced at the pin and recorded in the case purposes — it
  strengthens non-vacuity.

## Asks queued

None.

## Divergences

None opened — no rewrite exists.

## Idea seeds

- `harness/run.py` accepts one `--cases` path per invocation; a multi-path or
  id-list form would make a session's targeted rerun one command (surfaced by
  the review's rerun loop).
- `setting:reverse_digraph` + `fn:load_graphml` as one packet: a committed
  graphml fixture and probably a small capture extension (fixture-path
  input), pinning the reversal against a direction-sensitive rule.
- Carried: the get-family accessors (`get_rules`, `get_logic_program`,
  `get_interpretation`) still have no probe kind that can fingerprint their
  live objects — a `parse_fingerprint`-style reduction per accessor.
- Carried: `REASON_ARGS` is still hand-kept; derive it from the pinned
  signature the way `SETTINGS_KNOBS` is.
