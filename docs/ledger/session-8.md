# Session 8 — the settings-only knobs: canonical, abort_on_inconsistency, memory_profile

Date: 2026-07-06 (same sitting as sessions 0–7)

## Verdict

Session 7's NEXT executed as predicted — no capture surgery: three
settings-only pairs (six cases) took the corpus 34 → 40, targeted
oracle-vs-oracle ALL PASS on all six with same-engine repeats (the
post-review-fix rerun is the verdict-of-record), the review gate found
0 High / 1 Medium / 1 Low (both fixed in-session), and the board stands at
30/52 rows `cased` with `setting:canonical`, `setting:abort_on_inconsistency`,
and `setting:memory_profile` flipped. The `abort_on_inconsistency` dead-knob
hypothesis is upgraded to verified: no consumption site outside `_Settings`
in the engine package, and twin digests equal on an inconsistency-triggering
program with only the knob readback differing.

## Evidence

- **Session shape:** the two-agent form from session 7's protocol change, first
  full run — an author worker (cases, runs, board flips, two commits) then an
  independent reviewer-fixer (re-derived every pin citation, re-derived
  non-vacuity from artifacts, applied both fixes itself, reran the targeted
  evidence as the verdict-of-record). No orchestrator re-verification, per the
  protocol.
- **The canonical pair** pins the alias mechanics (`pyreason.py:167` getter
  and `:357` setter both on `__persistent`; the `__canonical` field written at
  init/reset is never read): `canonical-on` sets canonical alone on the
  persistent-on program — both readbacks come back true and all four reasoning
  digests equal `persistent-on`'s; `canonical-last-write` writes
  persistent=true then canonical=false — both readbacks false, digests equal
  `persistent-off`'s. Non-vacuous because the persistent twins differ on
  `interp-dict`/`trace-node`, so the canonical twins landing on opposite sides
  of that split is a real pin. The naming-mismatch class is confirmed
  source-level-only (`pyreason.py:1609` → `program.py:11` → 
  `interpretation.py:64`).
- **The abort pair** twins the inconsistency-ipl-resolve program (the
  machinery demonstrably fires: three `Consistent=False` trace rows) with the
  knob unset vs true: all reasoning digests equal, readback only differing —
  the dead-knob class, grep-verified in the engine package
  (`pyreason.py:49/:70/:118-123/:284-294` are the only sites; upstream's own
  settings tests exercise the getter/setter and nothing else).
- **The memory-profile pair** pins the `reason()` dispatch
  (`pyreason.py:1517-1522`): the on-twin's capture logs all carry the
  run-varying peak-MB stdout line, the default twin's carry none, and all
  reasoning digests are equal — an observational wrapper, interpretation
  unchanged. `memory_profiler` 0.61.0 was already in the oracle env; nothing
  was installed.
- **The runs:** fast tier 61 passed (author and reviewer runs); each of the
  six cases via `uv run python -m harness.run --cases harness/cases/<case>.json
  --engine-a oracle-env/bin/python` → ALL PASS, 4 fresh-process captures each
  (PYTHONHASHSEED=0), same-engine repeats green — author run and post-review
  rerun. Cross-twin equalities (including digest-identity of the default twins
  to `persistent-on`/`persistent-off`/`hello-world`/`inconsistency-ipl-resolve`
  banked artifacts) are authoring-time observations, hedged as such in the
  purposes. **No full-corpus run this session** — the sweep, now 40 cases, is
  owed at the next phase boundary (the standing no-silent-boundary marker).
- **Review gate:**
  [docs/reviews/2026-07-06-settings-only-knob-cases.md](../reviews/2026-07-06-settings-only-knob-cases.md)
  — M1: canonical-on's purpose wrongly claimed no `__canonical` field exists
  (it exists write-only, `pyreason.py:54/:75`); purpose corrected. L1: the
  dead-knob grep claim scoped to the engine package (a full-tree grep also
  hits upstream's settings tests). Both fixed by the reviewer, digests
  unchanged, targeted rerun green.
- **Gates:** preflight 10/10 at session start; links gate and fast tier green
  on every commit; oracle tree clean and pinned at `e1a94af33e1f` throughout.
- **Board:** `docs/surface.md` — 30/52 rows `cased`, 22 `uncovered`;
  `equivalent` still 0/52 — no rewrite exists. Remaining classes per new row
  recorded in the author report: `type-reject` family-wide;
  `naming-mismatch` source-level-only; `memory_profile.interaction-output`
  blocked on the harness's `output_to_file` forbid.

## Committed

- `36f281b` — harness: settings-only pairs for canonical,
  abort_on_inconsistency, memory_profile.
- `e907e87` — docs: board flips for canonical, abort_on_inconsistency,
  memory_profile.
- `c766ff1` — harness: review of settings-only knob cases — one Medium + one
  Low purpose fix; report.
- (this commit) — ledger: session 8 banked; campaign log continued.

## NEXT

The `reverse_digraph` + `fn:load_graphml` packet (session 7's named
follow-on): extend the capture with a committed-fixture graph input (a
`graphml_path` alongside the inline-graph form — the one small capture
extension this packet is allowed), commit a small graphml fixture under
`harness/fixtures/`, then case (a) the `setting:reverse_digraph` pair —
default-false-asis vs nondefault-true-reversed over `load_graphml` with a
direction-sensitive rule (`derived(y) <-1 rel(x,y)`-shaped, so reversal flips
which node derives; the load_graph path ignores the knob per the board note,
which the pair's purposes cite) — and (b) `fn:load_graphml`'s happy classes
(happy-basic, happy-no-attr-parse via the graph-attr knob) over the same
fixture. Run targeted (no corpus sweep), flip `setting:reverse_digraph` and
`fn:load_graphml` to `cased` with remainders (the malformed/bound attribute
cluster) named in notes, bank via review. If wall-clock allows, the
malformed-attr cluster rides the same session; otherwise it is the following
packet. (`setting:parallel_computing` and `output_to_file`/`output_file_name`
still need their own characterization; the settings-knob phase ends when
those and reverse_digraph land — that boundary triggers the owed full-corpus
sweep session.)

## Deviations

None — the two-agent shape ran as the protocol defines it.

## Asks queued

None.

## Divergences

None opened — no rewrite exists.

## Idea seeds

- A first-class file-output probe kind would unblock three surfaces at once:
  the `output_to_file`/`output_file_name` rows and `memory_profile`'s
  `interaction-output` class (the peak-MB line lands in the redirect file) —
  the harness's forbid on `output_to_file` is the single blocker for all
  three.
- Carried: `harness/run.py` accepts one `--cases` path per invocation
  (resurfaced again — the reviewer's rerun loop is six invocations); a
  multi-path or id-list form would make a session's targeted rerun one
  command.
- Carried: the get-family accessors (`get_rules`, `get_logic_program`,
  `get_interpretation`) still have no probe kind that can fingerprint their
  live objects.
- Carried: `REASON_ARGS` is still hand-kept; derive it from the pinned
  signature the way `SETTINGS_KNOBS` is.
