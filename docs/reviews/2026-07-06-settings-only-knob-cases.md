<!-- doccode: pyreason-rewrite-docs-reviews-2026-07-06-settings-only-knob-cases -->
# Review report — the settings-only knob cases (canonical, abort_on_inconsistency, memory_profile)

Scope: the six-case authoring commit (`36f281b`) and the board-flip commit
(`e907e87`) — three settings-only pairs over existing probe kinds. One focused
reviewer-fixer with no shared session context, verifying against the pinned
oracle source (`e1a94af33e1f`) and the run artifacts, then applying fixes
in-session.

Every mechanism claim was re-derived at the pin. The canonical alias: the
getter returns `self.__persistent` (`pyreason.py:167`) and the setter writes
`self.__persistent` (`:357`), so the two public knobs share one field; the
value rides into `Program` under the parameter name `canonical`
(`pyreason.py:1609` passes `settings.persistent`; `program.py:11` receives it
as `canonical`; `interpretation.py:64` receives it back as `persistent`) —
the naming-mismatch class is real and source-level only. The per-timestep
reset gate is `interpretation.py:260` (`if t>0 and not persistent`). The
capture applies `inputs.settings` in JSON key order (`apply_settings`
iterates the dict), so the last-write-wins mechanics hold as claimed. The
dead-knob claim was re-derived independently with a wider grep than the
author's: in the engine package `abort_on_inconsistency` appears only inside
`_Settings` (`pyreason.py:49` init, `:70` reset default False, `:118-123`
getter, `:284-294` setter) with zero hits under `scripts/`; the only hits
outside the package are upstream's own settings tests, which exercise the
getter/setter and nothing else — no consumption site exists. The
memory-profile dispatch: `reason()` branches on the knob at `pyreason.py:1517`
— `True` wraps `_reason` in `mp.memory_usage(..., max_usage=True,
retval=True)` (`:1518-1519`) and prints the MB line (`:1520`); `False` calls
`_reason` bare (`:1522`); `memory_profiler` 0.61.0 is already importable in
the oracle env (no install performed). Non-vacuity was re-derived from the
artifacts: `persistent-on` vs `persistent-off` differ on `interp-dict` and
`trace-node`, so the canonical twins landing digest-equal to opposite sides
of that split is a real pin; the abort pair's program demonstrably fires the
inconsistency machinery (three `Consistent=False` trace rows — the Alice IPL
conflict both ways plus the Bob bound conflict — with inconsistency
messages); the memory-profile on-twin's capture logs all carry the
run-varying "Program used … MB" stdout line while the default twin's carry
none, so the profiled branch demonstrably ran and the harness digests never
see the print. Twin programs are byte-identical outside `inputs.settings`
(checked programmatically for all three pairs and all three baseline
identities); every cross-twin equality claim reproduces from the artifacts
(canonical-on == persistent-on, canonical-last-write == persistent-off,
abort twins equal, abort-default == inconsistency-ipl-resolve, memory twins
equal, memory-default == hello-world, on 4 shared reasoning probes each) and
the readbacks match ({true,true}, {false,false}, false/true, false/true).
Case records match the corpus shape with authoring-time hedges present in
every purpose; the board's three rows flipped to cased (30/52) with the six
ids joined to exactly the rows their `surface_items` cover and nowhere else
(checked in both directions), including the deliberate joins to
`fn:add_inconsistent_predicate` (abort pair) and `setting:persistent`
(canonical pair) and the deliberate non-join to `fn:filter_and_sort_edges`.
The two commits touch only the six case files and `docs/surface.md`; the
out-of-packet rows (`setting:reverse_digraph`, `setting:parallel_computing`,
`output_to_file`/`output_file_name`) are untouched; the oracle tree is clean
and pinned at `e1a94af33e1f`; no dependency files changed.

## Fixed

- **M1 (Medium)** — the canonical-on purpose asserted "no `__canonical`
  field exists" at the pin. False: `_Settings.__init__` initializes
  `self.__canonical` (`pyreason.py:54`) and `reset()` writes it
  (`:75`); the field is write-only — nothing ever reads it, and the public
  property pair reads/writes `__persistent` — so the alias conclusion and
  the case's behavior are unaffected, but the existence claim a grep
  disproves could mislead a rewrite of the settings object. The purpose now
  says the field is written only at init/reset and never read, leaving no
  independent canonical state. Case inputs, probes, and digests unchanged.
- **L1 (Low)** — the abort-on-inconsistency-on purpose claimed "a full-tree
  grep finds the name only in `_Settings` itself": a literal full-tree grep
  of the oracle clone also hits upstream's own settings tests
  (`tests/api_tests/test_pyreason_settings.py`), which pin only the
  getter/setter. The purpose now scopes the grep to the engine package and
  notes what the upstream tests exercise; the board row's note gained the
  same package scoping. The dead-knob conclusion stands unchanged.

## Deferred with rationale

None — both findings were fixed in-session.

## Rerun evidence (post-fix)

- `uv run pytest -m "not e2e"` — 61 passed, 2 deselected.
- `uv run python -m harness.run --cases harness/cases/<case>.json
  --engine-a oracle-env/bin/python` for each of the six cases (one case per
  invocation) — ALL PASS on all six, fresh same-engine repeat captures;
  cross-twin digest equalities, knob readbacks, the abort pair's three
  inconsistency trace rows, and the memory-profile stdout split were all
  re-derived from the fresh artifacts and match the table above.
