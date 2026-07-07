<!-- doccode: pyreason-rewrite-docs-reviews-2026-07-07-phase3-slice4-author -->
# Phase 3, slice 4 — the knob-arm semantics (author report)

- session: 19 · 2026-07-07 · author packet
- verdict: **17/17 equivalence PASS** oracle-vs-rewrite (`results-phase3-slice4/report.json`, exit 0, ALL PASS; 4 fresh-process captures per case, same-engine repeats digest-stable, PYTHONHASHSEED=0); fast tier **219 passed** (209 existing + 10 new seam tests)
- code: `60b34ad` (fp schedule + engine-selection plumbing), `9584af9` (10 seam tests + ADR 0003), plus this commit (surface flips + report)
- board: 10 surface rows flip to `equivalent` — **18/52**

## Where the session started

Single-capture screening of the packet's 17 cases against the banked
session-15 oracle artifacts showed **16 of 17 already digest-equal** on the
pre-session core: the sessions 17–18 reference core already carried the
update-mode arms, the inconsistency resolve/override paths, the
allow-ground-rules grounding branches, the static-graph-facts stamping, the
store-off gating with the atom_trace force-flip, and the dead abort knob.
The one gap was `fp-version-on` — the rewrite ran its default schedule
regardless of `fp_version`, and the pinned fp variant's output is genuinely
different. The slice therefore reduced to: land the fp schedule honestly
inside the one-core design, dispatch the two engine-selection knobs the way
the pin does, pin every knob arm with seam tests, and bank the 17-case proof.

Housekeeping note: this session was interrupted mid-flight by a server error
and resumed; at resume the working tree was verified to hold exactly this
packet's three in-progress files (`_interpretation.py`, `_program.py`,
`_state.py`) and nothing else. The coordinator warned a message meant for
this agent was briefly misrouted to another (stopped) agent — nothing
foreign was found in the tree.

## What each knob's pinned semantics turned out to be

- **`abort_on_inconsistency` — a dead knob.** The name exists only inside the
  pinned `_Settings` (pyreason.py:49/:70/:118-123/:284-294; zero consumption
  under scripts/). Both arms resolve the conflict program identically; only
  the readback differs. The rewrite stores and reads the knob and consults it
  nowhere — `test_abort_on_inconsistency_is_dead_at_the_pin` holds the two
  arms' traces equal.
- **`inconsistency_check` — the real governor.** On (default): a conflicting
  update banks a `Consistent=False` trace row with the pinned message
  (IPL-conflict wording vs same-predicate `Update from [a, b] to [c, d] is
  not allowed` wording, three-decimal `float_to_str` formatting) and pins the
  atom AND its IPL complements to static [0,1]
  (interpretation.py:1961-2083). Off: the update is forced through the
  override path (`_update_* override=True`), every row stays consistent, and
  the pin happily produces an INVERTED interval — sick(Alice)
  `[0.8,0.09999999999999998]` via IPL complement arithmetic — which then
  still satisfies the spread rule's `[0.5,1]` clause bound, so derivation
  continues down the chain. Reproduced exactly (banked
  inconsistency-ipl-override).
- **`update_mode` — string-equality against 'override', nothing else.** The
  setter type-checks `str` only; every consumption site is
  `update_mode == 'override'`. Default intersects same-atom bounds
  (`world.update`: [0.2,1] then [0,0.8] → [0.2,0.8], derived(B) fires);
  'override' replaces wholesale (`set_lower_upper`: → [0,0.8], the [0.1,1]
  clause bound fails, nothing derives); a junk string silently behaves as
  intersection and reads back verbatim.
- **`allow_ground_rules`** — consumed inside `_ground_rule`: on, a clause or
  head constant naming a real graph node grounds directly to that node; off,
  the same token is an ordinary variable even when the node exists (two
  influenced() derivations vs one on the twin pair). Already landed in
  session 17; proven here.
- **`store_interpretation_changes` off** — trace appends are gated engine-side
  at every `_update_*`/resolve/static-reapply site; `reason()` force-flips
  the PUBLIC `atom_trace` knob at start (pyreason.py:1584-1585 — the
  get_setting probes read True before reason, False after, store itself
  unchanged); and every trace-backed accessor refuses by AssertionError with
  the pinned per-accessor texts (`...turn on to save rule trace` /
  `...filter and sort nodes` / `...filter and sort edges` — get_rule_trace's
  single assert precedes the node/edge split, so both trace probes bank the
  identical record). `get_time` still answers.
- **`static_graph_facts`** — read at `load_graph` time and stamped onto the
  generated graph-attribute facts as their static flag
  (graphml_parser.py:60/90 via pyreason.py:603). Under `persistent=False`,
  on: the attribute bounds escape the per-timestep reset, the rule regrounds
  every step (derived(B) at t=1 AND t=2) and holds perfect convergence open
  (get_time 3); off: bounds reset to [0,1] at every t>0, one derivation,
  convergence a step earlier (get_time 2).

## The fp/parallel story (AC-1)

**What differs observably at the pin.** The pinned dispatch
(program.py:42-47) selects among three near-copy engine variants: parallel
first, then fp, then default. The banked artifacts split them cleanly:

- `parallel-computing-on` and `parallel-fp-precedence` digest-equal the
  default twin on **every** reasoning probe — the parallel variant's entire
  source diff is the prange decorator flip (interpretation_parallel.py:241),
  invisible on the pinned surface.
- `fp-version-on` does NOT: different fp-counter values (a pass counter, not
  an inner-round counter), different trace event order (all fact rows for
  t=0..2 precede the rule rows their pass produced), **duplicated
  atom-trace groundings** (Justin's t=2 row carries `(Justin,Mary)` twice;
  John's carries `(John,Mary)`×3 + `(John,Justin)`×2), and a different
  last-step frame row order ([Mary, Justin, John] vs [Mary, John, Justin]).
  Same final bounds, same get_time.

**Why the branch is the minimal honest shape.** No post-processing of the
default schedule's output can produce the fp artifact: the duplications come
from the fp variant's per-timestep world dicts feeding globally accumulating
predicate maps — information the default schedule never generates. A
normalized body diff of the pinned variants shows their
grounding/update/resolve/annotate bodies **line-identical**; only the
orchestration (`reason`), the container plumbing, and the init shape differ.
So the rewrite keeps ONE copy of every semantic operation —
`_ground_rule`, `_apply_fact`, `_update_component`,
`resolve_inconsistency_*`, `annotate`, `_add_node/_add_edge(s)` — now
parametrized by the world dicts they operate on, and adds exactly one
alternate orchestration, `reason_fp` (_interpretation.py), transcribing the
pinned fp schedule: whole-run timestep sweeps per pass, conclusions applied
only between passes with the pass counter, per-timestep convergence-counter
resets, the delta-0 update-flag clear, pass-level perfect convergence, and
the `max_t_changes + 1` end time. `parallel_computing` selects **no**
schedule at all — the dispatch is `fp_mode = fp_version and not
parallel_computing`, the exact pinned precedence, with every non-fp
combination running the reference schedule because that is what the pin
observably emits. Knob readbacks are untouched settings state in all arms.
ADR 0003 records the decision; ADR 0002's design otherwise stands unchanged
(same state object, same helpers, same trace discipline — the default
schedule's code path is byte-for-byte the same logic it was, only with
explicit container parameters).

**The stamping defect, reproduced at its seam.** The pinned Program hands
the specific-label maps to ONLY the default Interpretation class
(program.py:34-38 — upstream's own `#TODO: Investigate issues w/ not adding
specific edge and node labels to other interps`), so the fp variant always
reasons with empty specific labels while the closed-world list reaches all
variants. `_program.Program.reason` reproduces exactly that: empty
specific-label maps on the fp path, closed-world predicates on both.

## Per-case verdicts

`results-phase3-slice4/` — 17/17 pass; run wall-clock **3m50.7s** total
(`PYTHONHASHSEED=0`, engine A `oracle-env/bin/python`, engine B
`scripts/rewrite-python`). Per-case reason-time from the a1/b1 artifacts:

| case | verdict | oracle reason | rewrite reason |
|---|---|---|---|
| abort-on-inconsistency-default | pass | 2.42s | <0.01s |
| abort-on-inconsistency-on | pass | 2.40s | <0.01s |
| allow-ground-rules-off | pass | 2.51s | <0.01s |
| allow-ground-rules-on | pass | 2.49s | <0.01s |
| inconsistency-ipl-resolve | pass | 2.49s | <0.01s |
| inconsistency-ipl-override | pass | 2.52s | <0.01s |
| update-mode-default | pass | 2.62s | <0.01s |
| update-mode-override | pass | 2.57s | <0.01s |
| update-mode-junk-string | pass | 2.62s | <0.01s |
| store-off-accessors | pass | 2.98s | <0.01s |
| store-off-atom-trace-flip | pass | 2.99s | <0.01s |
| fp-version-on | pass | 2.92s | <0.01s |
| parallel-computing-default | pass | 2.98s | <0.01s |
| parallel-computing-on | pass | 2.98s | <0.01s |
| parallel-fp-precedence | pass | 3.00s | <0.01s |
| static-graph-facts-on | pass | 2.59s | <0.01s |
| static-graph-facts-off | pass | 2.46s | <0.01s |

No divergences → no DIV records this session.

## Deliberately-reproduced oracle defects (equivalence-PASS; oracle-bug-candidate follow-ups)

1. **Specific-label stamping defect** — program.py:34-38 stamps
   specific node/edge labels onto only the default variant; fp (and
   parallel) reason with empty maps. Upstream's own TODO marks it.
2. **The dead `abort_on_inconsistency` knob** — settable, readable, consulted
   nowhere.
3. **`update_mode` accepts any string silently** — no domain validation; a
   typo means intersection semantics with no signal beyond the readback.
4. **Inverted intervals forced through under `inconsistency_check=False`** —
   IPL complement arithmetic produces `[0.8,0.099...]` (lower > upper) and
   reasoning continues over it.
5. **`reason()` mutates the public `atom_trace` knob** when change storage is
   off (pyreason.py:1584-1585) — a settings write as a side effect of
   reasoning (already on the board from the case authoring; reproduced at
   the `_state._reason` seam).
6. **The fp schedule cannot terminate on `timesteps=-1`** — the fp timestep
   sweep's only exit is `t == tmax` (interpretation_fp.py:272-273), so the
   run-to-convergence arm never returns. Reproduced by construction (the
   transcribed sweep has the same exit), not exercised by any committed case;
   a case pinning it would need a timeout-shaped probe.

## Deviations from a literal transcription (all output-invisible, named)

- The pinned fp `reason` tracks `max_rules_time` that no branch reads —
  dropped (dead scaffolding).
- The pinned fp per-rule "threadsafe" conclusion lists extend in rule order
  after the prange — a sequential per-rule append is order-identical.
- `num_ga` (unobserved by any pinned public probe) is tracked only by the
  default schedule, as at the pin (the fp variant's `reason` takes no
  num_ga); the shared helpers gate on `fp_mode` rather than invent an index
  shape the fp variant never had.
- The pinned default `_update_*` wraps its body in a blanket
  try/except→(False,0); the fp variant has none. The rewrite keeps its
  narrow KeyError guard from session 17 for both (the fp application loops
  pre-create missing worlds, so the guard is unreachable on that path).

## Acceptance criteria

1. **One-core design** — yes: zero duplicated semantics; one forced branch
   (the fp schedule), named above with the observable evidence that forces
   it; parallel introduces no branch. ADR 0003 committed; ADR 0002 holds.
2. **Fast tier** — 219 passed (`uv run pytest -m "not e2e"`), 10 new seam
   tests with accurate one-line `proves:` docstrings (inconsistency
   resolve/override/dead-abort, three update-mode arms, static-graph-facts
   both arms, the fp schedule's pinned shape, parallel masking fp; the
   store-off force-flip + accessor gates were already pinned by
   `test_store_off_flips_atom_trace_and_gates_views`).
3. **17-case run** — 17/17 pass into `results-phase3-slice4/` (untracked,
   gitignored per the slice convention). Truthful table above.
4. **surface.md** — 10 rows flipped to `equivalent`, each only because every
   case in its `cases` field has now passed oracle-vs-rewrite across
   sessions 16–19: `fn:add_inconsistent_predicate`,
   `setting:abort_on_inconsistency`, `setting:persistent`,
   `setting:inconsistency_check`, `setting:static_graph_facts`,
   `setting:store_interpretation_changes`, `setting:parallel_computing`,
   `setting:update_mode`, `setting:allow_ground_rules`,
   `setting:fp_version`. New fraction: **18/52**. Inventory gate green.
   (The big fn:/type:/dsl: rows still wait on the graph-attr/output-file/
   memory-profile case families — future slices.)
5. **Hygiene** — `git status` clean at close; `git -C oracle/pyreason status
   --porcelain` empty; no installs or dependency changes; `results/` and all
   banked `results-phase3-slice*` dirs untouched (screening ran
   single-capture into the session scratchpad; the evidence run wrote only
   the new `results-phase3-slice4/`).

## Repro

```
# fast tier (219)
uv run pytest -m "not e2e"

# the 17-case oracle-vs-rewrite run (stage the committed cases, then run)
mkdir -p /tmp/slice4-cases && for c in abort-on-inconsistency-default \
  abort-on-inconsistency-on inconsistency-ipl-resolve inconsistency-ipl-override \
  allow-ground-rules-off allow-ground-rules-on update-mode-default \
  update-mode-override update-mode-junk-string store-off-accessors \
  store-off-atom-trace-flip fp-version-on parallel-computing-default \
  parallel-computing-on parallel-fp-precedence static-graph-facts-on \
  static-graph-facts-off; do cp harness/cases/$c.json /tmp/slice4-cases/; done
PYTHONHASHSEED=0 uv run python -m harness.run --cases /tmp/slice4-cases \
  --engine-a oracle-env/bin/python --engine-b scripts/rewrite-python \
  --results results-phase3-slice4-repro
```

## Queued-ask recommendations

None new. Nothing in this packet needed pyyaml (the inconsistency cases
carry their IPL inline via `add_inconsistent_predicate`); the existing
queued asks stand as they are.
