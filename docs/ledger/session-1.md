# Session 1 — oracle environment, the ARM gate, and the AC-1 inventory

Date: 2026-07-06 (same sitting as session 0)

## Verdict

The pinned oracle runs on the campaign machine (ARM gate PASSED, on Python 3.10 — it reds
on 3.12), and the equivalence target set is enumerated and mechanized: `docs/surface.md`
holds all 52 rows with ~420 first-pass input classes, gated by an AST-scan test that reds
on any omitted or phantom row.

## Evidence

- **Oracle env** (the operator-approved Phase-1 dependency ask, executed): wheel built
  from a scratch copy of the clone (`SETUPTOOLS_SCM_PRETEND_VERSION=3.6.0`,
  `uv build --wheel`), installed **non-editable** into git-ignored `oracle-env/` —
  the clone verified clean before and after (`git status --porcelain` empty).
  Fingerprint: [session-1-oracle-env.txt](session-1-oracle-env.txt) (python 3.10.20,
  numba 0.59.1, numpy 1.26.4, pandas 2.3.3). Two undeclared runtime needs surfaced and
  were satisfied inside the approved env ask: `setuptools<81` (the pinned oracle imports
  `pkg_resources` at import time; setuptools 81+ no longer ships it), and the Python
  ceiling below.
- **Python ceiling (measured, not assumed):** on Python 3.12 the oracle's import-time
  warm-up `reason()` fails to JIT — numba 0.59.1 cannot unify the comprehension variable
  in `interpretation.py:473` under 3.12's inline-comprehension scoping. Upstream CI at the
  pin tests only 3.9/3.10. The oracle env runs 3.10; this is direct evidence for the
  AC-5 version-headroom bar on any numba-retention decision.
- **ARM gate** (`tools/oracle_smoke.py`, run in bare subprocesses of the oracle env):
  - run 1 (first-ever import, numba cache build — context, never a comparison bar):
    import 185.67s, then `reason(timesteps=2)` 0.30s in-process, output `[1, 2, 3]`.
  - runs 2–3 (warm cache, fresh process each): import 1.36s / 1.34s, first `reason()`
    3.03s / 2.96s, same output. Warm cold-start ≈ 4.4s total — the AC-4 cold-start
    context number on this machine.
- **AC-1 inventory:** `docs/surface.md` — 52 rows (26 fn / 6 type / 2 dsl / 18 setting),
  each with oracle anchor and first-pass input classes; all `uncovered`. Enumeration
  banked per group in `docs/analysis/surface/` (four Opus analyst reports, source-read
  only; corpus bug reports carried as labelled hypotheses, per the charter). Gate:
  `tests/test_surface_inventory.py` (5 tests, fast tier, stdlib `ast` only — never
  imports the oracle). Full fast tier 12 passed.
- **Analysis highlights the case corpus must exercise** (hypotheses until reproduced):
  `abort_on_inconsistency` has no consumption site (dead knob); `canonical` is a pure
  alias sharing `persistent`'s field; `update_mode` accepts any string, only
  `== 'override'` matters; `parallel_computing` masks `fp_version` in the engine
  dispatch; `reason()` force-mutates `settings.atom_trace` when
  `store_interpretation_changes` is off; `load_graph` ignores `reverse_digraph` while
  `load_graphml` honors it; the two `Interval.intersection` implementations seed `prev`
  bounds differently.

## Committed

- `93bfdcb` — tools: the ARM-gate oracle smoke script; `oracle-env/` git-ignored.
- `51568f5` — docs: the AC-1 surface inventory + its AST gate + the four analyst reports.
- (this commit) — ledger: session 1 banked.

## NEXT

Build the AC-2 harness spine (Phase 2): the subprocess capture runner (each case run in a
bare oracle-env process emitting a self-describing result artifact), the stdlib-only
compare layer (normalize + digest + compare, importing nothing from either engine), and
the committed case-record format — seed it with the hello-world case, then run
oracle-vs-oracle with a same-engine repeat (`PYTHONHASHSEED` pinned) and bank the PASS.

## Deviations

- The oracle env pins Python 3.10 (the charter's env sketch named only the package set) —
  forced by the measured 3.12 JIT failure; upstream CI's newest tested version chosen.
  The rewrite package itself keeps `requires-python >= 3.11`; the two envs are separate.

## Asks queued

None new. Executed under the session-0 approvals: the oracle env build (plus
`setuptools<81` as an undeclared-but-required runtime dependency of the pinned oracle,
judged inside the approved env ask and recorded here).

## Idea seeds

- Version-headroom evidence for the execution-layer ADR: numba 0.59.1 caps the oracle at
  Python ≤ 3.11 (3.12 measured red); any numba retention in the rewrite re-inherits a
  ceiling of this kind — the cost lands written in that ADR when the fork is decided.
