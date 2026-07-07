<!-- doccode: pyreason-rewrite-docs-reviews-2026-07-07-phase3-slice7-author -->
# Phase 3, slice 7 — the registrand packet (author report)

- session: 22 · 2026-07-07 · author packet
- verdict: **5/5 registrand cases + 2/2 spot-check cases equivalence PASS**
  oracle-vs-rewrite (`results-phase3-slice7/report.json`, exit 0, ALL PASS —
  7 cases; 4 fresh-process captures per case, same-engine repeats
  digest-stable, PYTHONHASHSEED=0); fast tier **263 passed** (259 existing +
  4 new seam tests)
- code: `f5f3680` (the conditional-njit accommodation + 3 resolve-arm seam
  tests), `3339446` (the resolve-to-rewrite-engine integration seam test),
  `f94bc90` (board flips + results-dir gitignore), plus this commit (report)
- board: 3 surface rows flip to `equivalent` — **50/52**
- DIV records: none — no cross-engine mismatch on any committed case
- ADR: none — rationale below

## Where the session started

The registrand family was the board's structural gap, named by slice-2
review finding **L1**: `harness/reference_fns.resolve()` unconditionally
njit-wrapped the committed reference function inside the engine
environment, and the campaign (rewrite) env carries no numba — so every
case that *registers* a function failed the rewrite capture at resolve
time, before the engine saw anything. Five cases were stuck `cased`
because of it (`annotation-fn-two-arg`, `annotation-fn-six-arg`,
`annotation-fn-reset-clears`, `head-fn-grounding`, `head-fn-reset-clears`),
gating three rows (`fn:add_annotation_function`, `fn:add_head_function`,
`fn:reset_rules`). The two unregistered-name cases never call resolve()
and had already passed oracle-vs-rewrite in slice 2 — they are this
packet's mandated spot-check, not new work.

## The accommodation (AC-1)

**The change** (harness/reference_fns.py, ~10 lines of logic): resolve()
now decides its arm at its own `import numba` seam —

- **numba imports** (the oracle env — the pinned engine's kernels require
  njit-dispatcher registrands): njit-wrap exactly as before, module-global
  `numba` bound to the imported module. Not one token of this arm's
  behavior changed.
- **numba absent** (the rewrite env): return the committed function
  **plain** — identity-preserved, `__name__` intact (the engine matches
  registrands by `__name__`) — and bind the module-global `numba` to
  `_PLAIN_NUMBA`, a stand-in whose only surface is `typed.List = list`, so
  the head registrand's pinned return contract (`numba.typed.List` of
  grounding strings, interpretation.py:2316-2338) reduces to the builtin
  list a plain-python engine's head-function caller consumes. Nothing else
  is provided on purpose: a reference function reaching for any other
  numba surface fails loudly in the plain arm.

**The discriminator, justified:** numba *importability*, caught as
`ModuleNotFoundError` only. Importability is exactly the property the two
arms differ on — an env that can run the pinned engine has numba by
construction, and an env without numba cannot consume a dispatcher at all,
so no finer discriminator (engine identity sniffing, env vars, flags)
would add precision, only new state to get wrong. Catching
`ModuleNotFoundError` and not the broader `ImportError` keeps a
present-but-broken numba what it is: an engine-environment fault that
fails the capture loudly rather than silently downgrading the oracle side
to plain registrands.

**Why no ADR:** the accommodation is a harness-seam execution of a
recorded review finding, not an architecture decision. The property that
makes it *automatically correct per engine* — resolve() runs inside each
engine's own subprocess interpreter — is ADR 0001's two-interpreter shape,
unchanged. The design rationale lives in the module docstring and this
report; no existing ADR is contradicted or extended.

**Cache confinement, untouched and verified:** the snapshot/restore
machinery around registrand captures (session-14 M2) is not modified. In
the rewrite env its `find_spec("pyreason")` resolves to `src/pyreason`,
whose `cache/` does not exist, so snapshot/restore no-op harmlessly
(verified post-run: no cache directory appeared under `src/pyreason/`).
In the oracle env it did its job on all 12 registrand-case oracle
captures: the bundled kernel cache holds **233 files with zero
`harness` references** after the full run — byte-count identical to the
session-15 baseline.

## Non-disturbance evidence (AC-3), two independent angles

1. **The packet-scoped spot-check rerun:** both previously-banked
   registrand-adjacent cases (`annotation-fn-unregistered-name`,
   `head-fn-unregistered-name` — slice 2's passes) reran through the
   committed harness: **pass**, and every probe digest of every capture
   (a1/a2/b1/b2 × both cases) is **byte-identical to the banked slice-2
   artifacts**.
2. **The oracle arm cross-checked against pre-accommodation ground
   truth:** all 10 oracle captures of the 5 registrand cases (a1/a2 each)
   have probe digests **byte-identical to the banked session-15 sweep
   artifacts in `results/`** — captured before the accommodation existed,
   through the unconditional-njit resolve(). The oracle path's behavior is
   provably unchanged, not just argued unchanged.

No other banked verdict consumes resolve(): the accommodation is dead code
for every non-registrand case (resolve() is only reached through
`REGISTRY_OPS`), so the packet-scoped spot-check plus the sweep-digest
cross-check covers the change's entire blast radius. The full corpus
sweep remains the phase-boundary session's job.

## Per-case verdicts (all PASS, `results-phase3-slice7/`, one invocation)

Wall-clock from the artifacts' capture-internal timing (`import_s` / total
step-and-reason seconds; engine A = pinned oracle, engine B = rewrite):

| case | verdict | oracle a1 (s) | oracle a2 (s) | rewrite b1/b2 (s) |
|---|---|---|---|---|
| annotation-fn-two-arg | pass | 1.39 / 38.79 | 1.43 / 38.74 | 0.11 / ~0.000 |
| annotation-fn-six-arg | pass | 1.30 / 37.15 | 1.51 / 37.74 | 0.11 / ~0.000 |
| annotation-fn-reset-clears | pass | 1.32 / 3.04 | 1.28 / 3.17 | 0.07 / ~0.000 |
| head-fn-grounding | pass | 1.36 / 49.37 | 1.45 / 50.40 | 0.11 / ~0.000 |
| head-fn-reset-clears | pass | 1.50 / 3.06 | 1.39 / 3.06 | 0.06 / ~0.000 |
| annotation-fn-unregistered-name (spot) | pass | 1.47 / 2.63 | 1.36 / 2.60 | 0.06 / ~0.000 |
| head-fn-unregistered-name (spot) | pass | 1.36 / 2.55 | 1.40 / 2.59 | 0.06 / ~0.000 |

The wall-clock budget behaved as the ledger predicted: the three
dispatcher-bearing cases pay the numba compile on **every oracle capture**
(~37–50 s each; dispatcher-embedding signatures can never hit the disk
cache), while the reset-clears pair reasons over *cleared* registrations
(empty function tuples — cache-hitting signatures, ~3 s). The
screen-then-confirm doctrine ran on exactly that structure: the cheapest
registrand case (`annotation-fn-reset-clears`) screened first as a
standalone run (PASS, 10.4 s wall), the full 7 committed to only after.
Session-15's "~170–217 s per registrand case" was a 4-oracle-capture
figure; at 2 oracle captures per case this run's oracle side totals
~275 s, ~5.5 min for the whole invocation.

**What the 5 passes prove, semantically:** the 2-arg weight-scaled-mean
bound with differential weights consumption (combo [0.5,1] vs combo2
[0.625,1] in one trace), the 6-arg extended-metadata bound (crowd(A) =
[0.25,1] from 2 clause-0 groundings / 8, atom_trace off), the registration
arity gate's two reject arms (both TypeErrors byte-equal cross-engine),
the head registrar's silent no-validation acceptance plus DSL-form head
grounding (Processed(A):[1,1] via `first_clause_first_grounding`), and
reset_rules clearing both registries (the annotation side re-raising the
unregistered NameError, the head side grounding to silent-empty) — each
now banked cross-engine, not just seam-asserted.

## Seam tests (fast tier 263 = 259 + 4)

Every test carries a `proves:` docstring; the numba-present arm is
simulated exactly as AC-1 allows, and here is precisely how: a stand-in
module object is planted in `sys.modules["numba"]` (monkeypatch, restored
after), which is the very seam resolve()'s `import numba` consumes — so
the arm decision and the wrap both execute for real, only the numba
library itself is substituted.

- `test_resolve_plain_arm_hands_over_the_committed_function_unwrapped` —
  the plain arm **for real, no mocks**: numba's absence from this env is
  *asserted* (`find_spec("numba") is None`), resolve() returns the
  identical registry function object with `__name__` intact and binds the
  stand-in.
- `test_resolve_numba_arm_njit_wraps_via_the_import_seam` — the simulated
  arm: resolve() returns exactly `njit(committed_fn)` and binds the
  module global to the imported module.
- `test_head_registrand_plain_arm_returns_a_builtin_list` — the one
  registrand that touches the `numba` module global returns a builtin
  list of grounding strings under the stand-in.
- `test_harness_resolved_registrands_drive_this_engine`
  (tests/test_rewrite_reasoning_core.py) — the consumption seam end to
  end: the exact objects a rewrite-env registrand capture hands to the
  registrars register on the rewrite facade and reason to the banked
  observables (combo [0.5,1]; Processed(A) via the head registrand).

The pre-existing resolve-path seam tests (name validation before the
engine imports; run_step handing the resolved callable to the registrar
outside the recording try; the registry-key/`__name__` pairing;
stdlib-only import) all still pass unmodified.

## Board

3 rows flip to `equivalent`, each by the mechanical rule (full case list ⊆
the oracle-vs-rewrite passed set across `results-phase3-slice1..7`):

- `fn:add_annotation_function` — two-arg, six-arg, reset-clears (slice 7)
  + unregistered-name (slice 2, re-verified slice 7).
- `fn:add_head_function` — grounding, reset-clears (slice 7) +
  unregistered-name (slice 2, re-verified slice 7).
- `fn:reset_rules` — reset-rules-no-program/-with-program (slice 3) + the
  two reset-clears cases (slice 7).

New fraction: **50/52** (was 47/52). The remaining `cased` pair is exactly
the IPL-file family's gate: `fn:load_inconsistent_predicate_list` and
`fn:save_rule_trace` (whose case list includes `ipl-atom-trace-off-trace`)
— pyyaml approved, cases not yet run oracle-vs-rewrite. Inventory gate
green (`tests/test_surface_inventory.py`, 6 passed).

## Slice-2 L3/L4 disposition (AC-5)

Both stay follow-ups, deliberately, and here is the boundary they sit on:

- **L3** (the rewrite's `annotate()` accepts anything indexable at
  [0]/[1] where the pin's objmode coerces to `(float64, float64)`) and
  **L4** (`_satisfies_threshold` returns falsy `None` on a quantifier-type
  outside number/percent where the pin fails compilation-side) are both
  **unreachable through every committed reference function and every
  committed case** — the registry's functions return float 2-tuples, and
  the `Threshold` constructor plus the parser only produce valid
  quantifier tuples. This packet's scope was the harness accommodation
  plus the five *committed* cases; making L3/L4 reachable requires
  authoring new reference functions (an Interval-returning annotation
  function, an exotic-return head function) and new cases to discriminate
  the arms — the "registrand-behavior packet" session 17 named. Changing
  the rewrite's shape on those arms *now*, with no case able to observe
  the change, would be an equivalence claim by code-reading — exactly what
  the evidence discipline forbids. The accommodation this packet landed is
  what *unblocks* that future packet: plain-arm registrands can now
  capture in the rewrite env, so those cases become authorable.

## Divergences and observations

- **DIV records: none.** All 7 cases compare equal; nothing was absorbed
  or loosened — the compare layer is untouched.
- **No new oracle-bug candidates.** The pinned behaviors this packet
  banked cross-engine (the unregistered-name NameError/silent-empty
  asymmetry, the no-validation head registrar) were already recorded on
  the board as pin behavior.
- **Observation, not a defect:** the accommodation makes the *committed
  source* the shared contract across engines — the oracle consumes it
  compiled, the rewrite consumes it plain. Float arithmetic agreed
  bit-exactly on every banked observable, as the reference-function
  contract (exact binary fractions, closed-form arithmetic) was designed
  to guarantee.

## Deviations from the packet

None. No installs anywhere (numba stays out of the campaign env — the
accommodation exists precisely so it can); no oracle-tree writes (byte-
clean at `e1a94af33e1f`, checked post-run); no full corpus sweep (fast
tier + the 7 packet-scoped e2e cases + the 1-case screen only); the
oracle-env bundled cache left exactly as found (233 files, zero registrand
residue).

## Open follow-ups

- The IPL file family (4 cases, pyyaml approved) — the last un-run gate
  before the Phase-3 breadth boundary sweep; after it the board's
  remaining pair can flip.
- The registrand-behavior packet (slice-2 L3/L4, now unblocked by this
  accommodation): new reference functions + cases for the return-shape
  coercion arms and the quantifier-membership guard.
- Carried unchanged: `type-reject` probe form for the settings family;
  `raise_errors=False` warn-skip arms; `interacts-unknown-predicate`;
  multi-rule prange characterization; sweep durability (report.json
  last-writer-wins — this run sidestepped it by running all 7 cases in
  one invocation).

## Repro

```
uv run pytest -m "not e2e"          # fast tier: 263 passed, 3 deselected
mkdir -p /tmp/slice7-cases && for c in annotation-fn-two-arg \
  annotation-fn-six-arg annotation-fn-reset-clears head-fn-grounding \
  head-fn-reset-clears annotation-fn-unregistered-name \
  head-fn-unregistered-name; do cp harness/cases/$c.json /tmp/slice7-cases/; done
PYTHONHASHSEED=0 uv run python -m harness.run --cases /tmp/slice7-cases \
  --engine-a oracle-env/bin/python --engine-b scripts/rewrite-python \
  --results results-phase3-slice7-review   # 7/7 ALL PASS (fresh dir for a re-run)
```

Digest cross-checks (the non-disturbance evidence), from the repo root:
compare `results-phase3-slice7/<case>/<cap>.json`'s `digests` against
`results-phase3-slice2/` for the two spot-check cases (all 8 captures
identical) and against `results/<case>/a1.json` (the session-15 sweep)
for the 5 registrand cases' oracle captures (all 10 identical).
