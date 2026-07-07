# Author report — parallel_computing + output_to_file/output_file_name cases (session 10, raw)

Packet: session 9's NEXT — characterize and case `setting:parallel_computing` and the
`output_to_file`/`output_file_name` pair; extend the capture with a file-output probe
kind; flip the three rows. Author: session 10 agent 1. Oracle pin `e1a94af33e1f`,
tree verified clean before and after all runs.

## 1. What I read at the pin (all paths under `oracle/pyreason/pyreason/`)

**output_to_file / output_file_name:**
- Defaults: `pyreason.py:67` (`__output_to_file = False`), `pyreason.py:68`
  (`__output_file_name = 'pyreason_output'`).
- Getters `pyreason.py:94-99` / `:102-107`; setters `:247-258` (bool TypeError) and
  `:260-270` (str TypeError, no path validation).
- The redirect: `reason()` stamps the module-global `__timestamp`
  (`time.strftime('%Y%m%d-%H%M%S')`, `pyreason.py:1511`) then, when the knob is on,
  `sys.stdout = open(f"./{settings.output_file_name}_{__timestamp}.txt", "a")` at
  `pyreason.py:1513-1514`; `_reason` re-opens the **same** name (same `__timestamp`)
  at `:1541-1542`, leaking the first handle. The path is cwd-relative; the handle is
  never flushed, closed, or restored — every later print in the process (including a
  `reason_again`) lands in a file named at first-reason time. `__timestamp` is also
  consumed by the trace savers (`:1654/:1668`), not only the redirect.
- `output_file_name` has exactly two consumption sites — the two guarded opens — so
  with the redirect off it is inert (basis of the `inert-when-output-false` class).

**parallel_computing:**
- Default `pyreason.py:80`; getter `:203-209` (docstring: "This will disable cacheing
  and pyreason will have to be re-compiled at each run"); setter `:408-419` (bool
  TypeError).
- Threaded into `Program` (`pyreason.py:1609` → `scripts/program/program.py:11/:25`).
  Dispatch at `program.py:42-46`: `if self._parallel_computing:` →
  `InterpretationParallel`; `elif self._fp_version:` → `InterpretationFP`; else the
  serial optimized `Interpretation`. Parallel is checked **first** — it masks
  fp_version (the precedence classes).
- `diff scripts/interpretation/interpretation.py scripts/interpretation/interpretation_parallel.py`
  → **one line**: `interpretation_parallel.py:241` flips
  `@numba.njit(cache=True, parallel=False)` to `parallel=True` on the static
  `Interpretation.reason` kernel. Both files import `prange` (line 9) and both run
  the rules loop as `for i in prange(len(rules))` (`:571`, comment at `:564`:
  "Threadsafe flags for in_loop and update within prange; merge after loop") — under
  `parallel=False` prange degrades to range; under `parallel=True` it is a real
  threaded loop.
- Verbose reason-time prints (what the redirect file captures): `pyreason.py`'s
  'Filtering rules based on queries' and (edges>nodes) 'Optimizing rules...' lines;
  the kernel's objmode `'Timestep:'` print (`interpretation.py:257-258`, flush=True);
  convergence lines (`:660/:667/:677`); 'Fixed Point iterations:' (`:238`). All
  deterministic text on fixed inputs.

## 2. What I built

**Capture extension (`harness/capture.py`, commit `5b0d8af`):**
- New probe kind `output_file` (not interpretation-consuming): flushes `sys.stdout`
  (the capture runs the engine in-process, so the engine's never-flushed redirect
  handle *is* the capture's stdout) and returns every `*.txt` in the working
  directory, sorted by name, as `{name, content}` — name canonicalized by
  `OUTPUT_TS_RE` (`_\d{8}-\d{6}\.txt$` → `_<timestamp>.txt`). Recorded rationale: the
  stamp is run schedule (`pyreason.py:1511`), not engine behavior; presence, count,
  the interpolated basename, and full contents compare exactly. An empty list is the
  compared no-file observation. `allow_raise` is refused on this kind (a read fault
  in the harness's own confined directory is a capture failure, never a banked
  observation).
- The `output_to_file` blanket forbid (`FORBIDDEN_SETTINGS`) is replaced by a
  targeted rule: `settings.output_to_file === true` in a case requires ≥1
  `output_file` probe (either case form) — the redirect file must always be
  compared. Explicit `false` validates bare.
- Confinement: when a case sets the knob true or carries the probe
  (`case_wants_output_dir`), `main()` chdirs into a fresh per-capture directory
  `<artifact>.outdir` beside the artifact (`fresh_output_dir`, cleared each capture
  so a stale redirect file can never bank as this run's observation), after
  resolving the artifact path absolute. The cwd-relative redirect therefore cannot
  land in the repo root or outside the per-run results area. Cases not using the
  surface keep their cwd untouched.
- Seam tests (`tests/test_capture_validation.py`): requires-probe rule in both case
  forms; explicit-false needs no probe; allow_raise refusal; read+canonicalize
  behavior incl. empty-dir `[]`, non-txt exclusion, sort order; stale-dir clearing;
  `case_wants_output_dir` truth table; partition test extended with the new kind.
  Fast tier 65 → 70 tests.

**Cases (commits `e806b60`, `fa77593`)** — all seven over the hello-world program
(the existing multi-timestep twin substrate; `timesteps: 2`, `atom_trace: true`):
- `output-to-file-default` — readbacks False/'pyreason_output', confined dir empty
  (`default-false-stdout`, `default-name`).
- `output-to-file-on` — one file `pyreason_output_<timestamp>.txt`, contents exactly
  the 8-line verbose reason-time text (`nondefault-true-redirect`, default-name
  interpolation).
- `output-file-name-custom` — `campaign_redirect_<timestamp>.txt`, same contents
  (`nondefault-name`, `interaction-filename`).
- `output-file-name-inert` — name set, knob off, no file anywhere
  (`inert-when-output-false`).
- `parallel-computing-default` — readback False, serial kernel
  (`default-false-standard`).
- `parallel-computing-on` — parallel kernel selected (`nondefault-true-parallel`).
  Deliberate design: one rule → prange width 1, so thread scheduling cannot reorder
  trace appends; the pair pins kernel-selection equivalence, not multi-rule
  scheduling (named uncovered — see §5).
- `parallel-fp-precedence` — both engine-selection knobs true
  (`interaction-fp-precedence` + fp_version's `interaction-parallel-precedence`).

**Board (commit `c752584`):** the three rows flipped to `cased` (35/52), new case
ids appended to every row their programs exercise, fp_version and memory_profile
notes updated.

## 3. Runs and results

Screens (scratchpad, outside the repo; PYTHONHASHSEED=0, oracle-env python):
- Redirect smoke: one file `pyreason_output_20260707-003744.txt` in the process cwd,
  content = 8 lines ('Filtering rules based on queries' → 'Fixed Point iterations: 3'),
  reason wall ~6s (serial, cached).
- Parallel smoke: completed, correct results; `REASON_S 174.4` cold.
- Parallel cache probe (second fresh process): `REASON_S_2ND_PROCESS 2.7` — see §4.

Harness (each `uv run python -m harness.run --cases harness/cases/<case>.json
--engine-a oracle-env/bin/python`; 4 fresh-process captures per case, self-proof
mode, same-engine repeats compared by exact digest):
- `output-to-file-default` — pass (ALL PASS)
- `output-to-file-on` — pass
- `output-file-name-custom` — pass
- `output-file-name-inert` — pass
- `parallel-computing-default` — pass
- `parallel-computing-on` — pass
- `parallel-fp-precedence` — pass (rerun after a purpose-text precision edit; the
  verdict-of-record is on the committed case text — probes/inputs unchanged between
  runs)

Fast tier: `uv run pytest -m "not e2e"` → **70 passed** (after the capture commit and
again before the docs commit). No full-corpus sweep run (phase-boundary property).

Authoring-time cross-case digest checks (from banked `results/<case>/a1.json`):
- All four output cases' reasoning digests (`nodes-popular`, `trace-node`,
  `trace-edge`, `time`) identical cross-case — the redirect moves prints, never
  reasoning.
- `output-to-file-on` vs `output-file-name-custom` file contents byte-identical;
  only the canonicalized basename differs.
- `parallel-computing-on` ≡ `parallel-computing-default` on all reasoning probes.
- `parallel-fp-precedence` ≡ `parallel-computing-on` on all reasoning probes, and
  ≠ `fp-version-on` (banked artifacts) on `trace-node` and `nodes-popular`
  (`trace-edge`/`time` match vacuously: empty edge trace, get_time 3) — precedence
  pinned behaviorally, not by readback alone.

## 4. Findings / characterizations

1. **The parallel kernel compile caches across fresh processes, contra the pinned
   docstring.** `pyreason.py:204-205` claims parallel "will disable cacheing and
   pyreason will have to be re-compiled at each run". Measured on this machine
   (numba 0.59.1, darwin/arm64, default threading layer): first fresh process
   ~174.4s reason wall (compile-dominated); second fresh process 2.7s; harness
   captures thereafter ~2.8s. The parallel path is fully laptop-local — no extra
   threading layer needed. Evidence: the two smoke runs in §3 and the banked
   `timing.reason_s` in `results/parallel-computing-on/*.json`.
2. **Kernel equivalence on the pair's program.** With prange width 1 the parallel
   kernel's digests equal the serial optimized kernel's on every reasoning probe —
   no divergence to record for this input class. (No claim is made for multi-rule
   programs; that class is named uncovered, §5.)
3. **Dispatch precedence is behavioral fact.** Both knobs true produces the
   parallel/optimized digest shape, not the fp shape — `program.py:42-46` order
   confirmed by comparison against fp-version-on's banked artifacts.
4. **The redirect is exactly what the pin reads as.** Cwd-relative, append-mode,
   timestamp-named, never restored/flushed; content is precisely the verbose
   reason-time prints; a set `output_file_name` with the knob off writes nothing.
   The `_reason` double-open (`:1541`) lands on the same file, so a one-step case
   yields exactly one file.
5. Compile emits `NumbaTypeSafetyWarning: unsafe cast from uint64 to int64` at
   `interpretation_parallel.py:572` (stderr only, not compared) — noting for the
   rewrite's kernel work.

## 5. Uncovered classes (named on the board)

- `type-reject` on all three rows — family-wide gap; a settings raise during input
  application fails the capture, so it needs the raising-probe form already queued
  as an idea seed.
- `setting:parallel_computing` — multi-rule prange scheduling: trace order under a
  prange of width >1 is deliberately unexercised here; if it is nondeterministic it
  must surface as its own characterization case (likely `irreproducible` in the
  harness), never absorbed into this pair.
- `setting:memory_profile` / `interaction-output` — now *authorable* (the probe
  exists) but still uncovered: the redirect file would carry the run-varying
  peak-MB line (`pyreason.py:1520`), and the per-case comparison policy supports
  only numeric tolerance on canonical values, not text canonicalization. That
  recorded-canonicalization decision is the remaining blocker.

## 6. What the reviewer should scrutinize

- The chdir in `capture.py main()`: it happens after validation, only for
  output-surface cases, with the artifact path resolved absolute first. Check I
  have not broken any assumption in the non-output cases' capture path (they never
  chdir) and that `.outdir` cleanup cannot delete anything outside `results/`
  (`fresh_output_dir` derives strictly from the artifact path).
- The `*.txt` glob: it observes every txt in the confined dir, not just the
  engine's basename. A fresh directory makes that safe; confirm no other engine
  writer could drop a `.txt` there (trace savers write only on explicit
  `save_rule_trace`, not probed here).
- The width-1 prange argument in `parallel-computing-on`'s purpose — verify the
  claim that thread scheduling cannot reorder trace appends when `len(rules) == 1`
  reads correctly from `interpretation_parallel.py:571`.
- The precedence case leans on fp-version-on's **banked** artifacts (from a prior
  session's run) for the ≠-fp half of the argument; the case's own harness verdict
  only self-proves parallel-vs-parallel. If that reliance is too stale, the
  alternative is rerunning fp-version-on — a cheap targeted run, but outside this
  packet's e2e budget by the letter of the wall-clock rule.
- Timestamp regex `_\d{8}-\d{6}\.txt$`: a user-chosen `output_file_name` ending in
  a digits-dash-digits pattern would also be canonicalized. Harmless for equality
  (both engines canonicalize identically) but worth a note if a future case picks
  a pathological name.

## 7. Reproduction

```
uv run pytest -m "not e2e"
for c in output-to-file-default output-to-file-on output-file-name-custom \
         output-file-name-inert parallel-computing-default parallel-computing-on \
         parallel-fp-precedence; do
  uv run python -m harness.run --cases harness/cases/$c.json --engine-a oracle-env/bin/python
done
```
(First parallel-on-branch capture on a cold numba cache pays ~174s; warm ~3s.)

Commits: `5b0d8af` (capture extension + seam tests), `e806b60` (output cases),
`fa77593` (parallel cases), `c752584` (board flips).
