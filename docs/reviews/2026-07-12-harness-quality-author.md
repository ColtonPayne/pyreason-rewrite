<!-- doccode: pyreason-rewrite-docs-reviews-2026-07-12-harness-quality-author -->
# Session 31 — harness-quality seed batch (author report)

- session: 31 · 2026-07-12 · author packet (the last unblocked thread: the five
  carried harness-quality seeds, all local, no dependency changes)
- scope: (1) sweep durability — the full-corpus runner made resumable/idempotent
  per case; (2) pyyaml-version parity tripwire; (3) artifact `case` echo;
  (4) per-probe `probe_s` timing; (5) multi-rule prange characterization of the
  pinned PARALLEL kernel, screened at the pin
- verdict: **all five seeds landed.** Fast tier **320 passed, 6 deselected**
  (was 310 + the 10 new tests, +1 new deselected e2e); the packet's small e2e
  (the resume mini-sweep) **1 passed in ~30 s**; the prange screens ran 4
  self-proof arms **ALL PASS** (16 fresh oracle processes) and the promoted
  case `parallel-computing-multirule` banked **oracle-vs-rewrite PASS**. Corpus
  at 116. No installs, no oracle-tree writes, no rewrite-engine changes.

## 1. Sweep durability (`harness/run.py`)

Motivating incidents: session 24's boundary sweep lost ~49 min to a host
interruption and restarted from zero; a session-30 worker was killed mid-run
(state-recovery note in that session's author report).

### Completion/resume semantics (the design decisions)

- **Completion marker.** After a case's four captures land, the runner writes
  `case.done.json` in the case's results dir — atomically (tmp + `os.replace`)
  and only after all four captures return. A marker on disk always means a
  completed case; an interruption at any earlier moment leaves no marker and
  the whole case re-runs. The marker records the **invocation identity**
  (engine-a/engine-b executables, the pinned hash seed, the case file's
  sha256-of-bytes) plus each capture's **exit code** and each artifact file's
  **sha256** and a `completed_at` timestamp.
- **Completion is decidable from the results dir alone.** A re-invocation
  skips a case iff its marker parses, matches the current invocation identity
  (an edited case file, a different engine path, or a different hash seed all
  force a re-run), and every artifact still hashes to the recorded digest — so
  a truncated or half-written artifact invalidates the case rather than being
  judged as if it were the completed capture's output. Anything less than that
  is "incomplete": the stale marker is deleted *before* the first re-capture
  (so an interruption mid-recapture can never pair an old marker with a
  partially refreshed dir), and the case re-runs whole. Loss on interruption
  is therefore at most the in-flight case.
- **Verdicts are always derived from the artifacts.** The marker never carries
  authority over the verdict: on skip, the runner re-loads the four artifacts
  (using the marker's recorded exit codes, since `load_artifact`'s taxonomy
  needs them) and re-judges through the same pure `judge_case`. A resumed
  sweep's verdict list therefore **equals** a single-invocation sweep's by
  construction — same artifacts, same judge — differing only in per-case
  `completed_at` timestamps inside the markers.
- **An `error` verdict is still a completed case.** A capture that exits
  nonzero (with or without an artifact) completed its run; the marker records
  the absence (`artifacts.<name>: null`) and the exit code, and a re-invocation
  resumes to the identical error verdict instead of silently retrying —
  resume must never flip a verdict the single-invocation report would carry.
  Forcing a retry is the explicit act of deleting the case dir (or marker).
- **Honesty: resumed-vs-single stays distinguishable.** `report.json` gains a
  `resume` block: `{"resumed": <bool>, "prior_complete": [...],
  "captured_this_invocation": [...]}` — `resumed` is true iff any case was
  prior-complete, so a future verdict-of-record can claim single-invocation
  from the report itself (`resumed: false`) and still corroborate with the
  session-24 full-tree mtime analysis (a resumed sweep's artifact mtimes
  straddle invocations; the markers' `completed_at` stamps say when each case
  landed). The console mirrors it: `[prior-complete]` per resumed case and a
  `RESUMED — N prior-complete, M captured this invocation` tally. A
  single-invocation run's console and report are byte-identical to the
  pre-change format except for the added `resume` block (`resumed: false`).
- **Byte-compatibility.** Artifact schema unchanged (additive only — §3/§4);
  report keys `engine_a`/`engine_b`/`hashseed`/`verdicts` unchanged in content
  and order; verdict entries carry no new keys. Existing consumers (the
  compare layer, banked reports) read what they always read.

Fast-tier coverage (`tests/test_harness_runner.py`, 7 new tests, each with a
`proves:` docstring): marker written + resume without recapture; identity
mismatch (case edit / engine change) invalidates; deleted marker and truncated
artifact each re-run the case; stale marker removed before recapture begins;
error verdicts resume identically; and a main()-level proof that a resumed
report's verdicts equal the uninterrupted report's while the resume block and
console say RESUMED.

### Mini-sweep resume demonstration (live oracle, 3 reason-free cases)

Also automated as `tests/test_resume_e2e.py` (e2e-marked; 1 passed, ~30 s),
which additionally holds the untouched case's artifact mtimes unchanged across
the resume. CLI transcript (interval-ops / label-ops / query-construct,
self-proof mode; the interruption is one deleted marker + one truncated
artifact):

```
$ uv run python -m harness.run --cases <mini-corpus> \
    --engine-a oracle-env/bin/python --results <results>
pass            interval-ops
pass            label-ops
pass            query-construct

ALL PASS (3 case(s))
exit: 0

# artificial interruption:
#   rm <results>/interval-ops/case.done.json        (killed before completion)
#   truncate <results>/label-ops/b1.json to 100 B   (killed mid-write)

$ uv run python -m harness.run --cases <mini-corpus> \
    --engine-a oracle-env/bin/python --results <results>
pass            interval-ops
pass            label-ops
pass            query-construct  [prior-complete]

ALL PASS (3 case(s); RESUMED — 1 prior-complete, 2 captured this invocation)
exit: 0

verdicts equal: True
clean resume block:   {'resumed': False, 'prior_complete': [],
                       'captured_this_invocation': ['interval-ops', 'label-ops', 'query-construct']}
resumed resume block: {'resumed': True, 'prior_complete': ['query-construct'],
                       'captured_this_invocation': ['interval-ops', 'label-ops']}
```

## 2. pyyaml-version parity tripwire (`tests/test_env_pins.py`)

pyyaml entered the campaign env operator-approved at **6.0.3** in ledger
session 22 (to unblock the `load_inconsistent_predicate_list` YAML path; the
oracle env's own pinned pyyaml untouched) and is pinned in `uv.lock`
(`pyyaml >= 6.0.3`, locked at 6.0.3). The lockfile pins resolution; the new
fast-tier test pins what the running interpreter actually **imports**
(`yaml.__version__ == "6.0.3"`), so a rebuilt venv or a lock update that
slipped past the ledger trips every commit. The failure message states the
legitimate-move protocol: re-screen the YAML-consuming case family
(`ipl-load-basic`, `ipl-load-malformed`, `ipl-load-null-overwrite`,
`ipl-atom-trace-off-trace`) oracle-vs-rewrite against the pin, confirm ALL
PASS, then update the expectation citing the new screen.

## 3. Artifact `case` echo (`harness/capture.py`)

The artifact previously echoed only `case_id`; it now carries the parsed case
verbatim under `"case"` — every artifact written after the case parsed,
error artifacts included — so an artifact can be read, re-judged (it contains
the comparison policy), or audited without the case file beside it. The echo
sits outside the probe map, so digests are untouched; the schema stays 1
(additive keys; the judge's checks read exactly the fields they always read,
and previously banked schema-1 artifacts remain judgeable).

## 4. Per-probe `probe_s` timing (`harness/capture.py`)

`timing.probes_s` maps probe id → wall-clock seconds (probe execution +
canonical reduction), in both case forms (top-level probes and step probes;
step *outcomes* keep their existing `steps_s`). Like `import_s`/`reason_s`,
it rides outside the digested probe map: diagnostic only, never compared —
probe timing is run schedule, not engine behavior.

## 5. Multi-rule prange characterization (the pinned PARALLEL kernel)

**Question carried on the board:** the oracle's `parallel_computing=True`
path runs the rules loop as a `prange` (interpretation_parallel.py:571 at the
pin); the committed family only ever exercised prange width 1. How do
multi-rule programs behave — determinism, rule-order effects, trace shape vs
the default engine?

**Method (screen at the pin).** Discriminating program: 3 rules with
interacting heads over the hello-world graph — `popular_rule` and `echo_rule`
both *write* `popular`, `trendy_rule` consumes it (`trendy(x) <- popular(x)`),
cyclically (`popular(x) <- trendy(x)`); `popular(Mary)` fact, timesteps 3,
`atom_trace` on. Four arms: {parallel, serial} × {base rule order, permuted
rule order (trendy, echo, popular)}. Each arm ran as a `harness.run`
self-proof — 4 fresh oracle processes per arm, `PYTHONHASHSEED=0` pinned by
the runner — 16 fresh-process captures total; cross-arm probe comparison via
the stdlib compare layer. Kernel-cache state checked before screening: the
parallel `Interpretation.reason` `.nbc`/`.nbi` pair present in the oracle
env's bundled cache (banked 2026-07-07), and a single warm screen capture ran
the full case in **6.6 s** (reason_s ≈ 2.8 s) — no ~174 s cold compile,
budget as C7 predicted.

**Findings.**

1. **Deterministic at width 3.** All four arms self-proof PASS — every arm's
   4 fresh processes digest-identical on every probe.
2. **Serial parity.** The parallel arms digest-equal their serial twins on
   *every* reasoning probe (trace shape included), on both rule orders —
   width-3 prange scheduling did not reorder trace appends or updates
   relative to the default engine on this machine (numba 0.59.1/darwin).
   Whether numba serializes this loop or the threads happen to commit in
   order is deliberately **not** claimed; only the observed digest parity is.
3. **Rule-list order is behavior — identically in both engines.** Permuting
   the rule list changed exactly two probes (`nodes-popular`, `trace-node`),
   the same way in parallel and serial: (a) a same-timestep duplicate
   derivation's trace row is attributed to whichever writing rule comes first
   in list order (base order credits `popular_rule` with its 4-clause
   groundings; permuted order credits `echo_rule` with its 1-clause
   grounding — same node, same label, same bounds), and (b) equal-bound rows
   in the filtered frames come back in a different order. 14 of 15 trace rows
   identical across orders; values everywhere identical.
4. **Timing (diagnostic).** reason_s ≈ 2.8 s in all four arms — no parallel
   speedup on this toy program; recorded only as run schedule.

**Disposition.** The base-order parallel arm is deterministic, stable, and
covers the board row's one deliberately unexercised class, so it was promoted
to committed case `parallel-computing-multirule` (oracle-vs-rewrite **PASS**
at authoring — consistent with serial parity, since the rewrite's parallel
knob runs the single default core per ADR 0003 / batch B11; nothing
rewrite-side changed). The permuted-order arms stay screen-only: they add
rule-order attribution coverage, but that behavior is engine-independent and
already pinned indirectly by the trace-bearing corpus; committing both orders
of the same program would double runtime for one attribution row. Board row
`setting:parallel_computing` updated with the characterization and the new
case; the "multi-rule prange scheduling unexercised" caveat is retired,
leaving type-reject as the family's only uncovered class.

## Evidence & reproduction

- Fast tier: `uv run pytest -m "not e2e"` → **320 passed, 6 deselected**.
- Resume e2e (the one e2e this packet touches):
  `uv run pytest tests/test_resume_e2e.py -m e2e` → **1 passed** (~30 s).
- New-case differential run:
  `uv run python -m harness.run --cases harness/cases/parallel-computing-multirule.json
  --engine-a oracle-env/bin/python --engine-b scripts/rewrite-python
  --results <fresh-dir>` → **ALL PASS (1 case(s))**.
- Prange screens: the four arm case files and all 16 capture artifacts +
  per-arm reports are in the session scratchpad (screen artifacts, not
  banked); their content is fully described above and in the board row, and
  the promoted case reproduces the base-order parallel arm from committed
  content.

## Commits

- `bc1fab7` — harness: capture artifacts echo their full case record and time
  each probe.
- `00c2e61` — harness: per-case durability — the runner resumes over its own
  results dir.
- `95b65eb` — tests: pyyaml-version parity tripwire in the fast tier.
- `0f6e637` — tests: e2e mini-sweep resume exercise.
- `f21b296` — cases: parallel-computing-multirule — the width-3 prange arm.
- (next) — docs: board row + this report.

## Hygiene

- Oracle tree untouched (read-only throughout; screens ran the installed
  oracle env against scratchpad results dirs). No installs, no dependency
  changes. No writes outside the campaign repo other than the session
  scratchpad. Rewrite engine source untouched.
