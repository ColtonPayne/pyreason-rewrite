# Author report — phase-boundary full-corpus sweep (session 11, raw)

Packet: session 10's NEXT — the settings-knob phase's verdict-of-record. Run all
committed cases oracle-vs-oracle, fast tier first, triage every non-pass by the
exit taxonomy, bank the sweep verdict (corpus size, pass count, wall-clock,
per-case timing outliers). This session is the phase-boundary exception to the
per-session e2e budget: the full corpus run is exactly the job.

Author: session 11 agent 1. Oracle pin `e1a94af33e1f`, tree verified clean before
and after all runs.

## Verdict

**CLEAN SWEEP — 53/53 pass, zero divergent, zero irreproducible, zero error, in
1331 s (22 m 11 s) total wall-clock. No code was touched anywhere in the session
(harness, cases, fixtures, tests all untouched), so per the packet the sweep banks
directly on this log with no reviewer session required.**

## 1. What ran

- Gates first: preflight 10/10; fast tier `uv run pytest -m "not e2e"` → **70
  passed** (run again after the sweep: 70 passed — required only after a fix, run
  anyway as a free tripwire since no fix happened).
- Corpus census: `harness/cases/*.json` → **53 files** (the expected 53), 53
  distinct case ids (the runner's duplicate-id guard also enforces this per
  invocation).
- Schedule screen (screen-then-confirm): three representative cases timed first —
  hello-world 26.1 s, parallel-computing-on 26.5 s, reason-again-restart-true
  26.9 s → estimate 53 × ~26 s ≈ 23 min, confirmed the parallel branch warm
  (the kernel's 10.3 MB `.nbc` from session 10 present, mtime Jul 7 00:41 —
  no cold-compile capture would occur; none did).
- The sweep: one runner invocation per case, sorted filename order,
  `PYTHONHASHSEED=0 uv run python -m harness.run --cases harness/cases/<case>.json
  --engine-a oracle-env/bin/python` — self-proof mode (engine B defaults to
  engine A), 4 fresh-process captures per case, same-engine repeats compared by
  exact digest, cross-pair probes by per-case policy. Per-case wall-clock and
  verdict captured per invocation.
- Engine fingerprint in every banked artifact: pyreason 3.6.0, python 3.10.20,
  darwin, `PYTHONHASHSEED=0`.

Note: the three screen cases were also run inside the sweep loop afterward — every
case's verdict-of-record is its in-loop run; the screen runs were schedule
estimation only (and agreed: pass there too).

## 2. Results

Full per-case table (verdict + wall-clock), totals, and outlier analysis:
[2026-07-07-phase-boundary-sweep-log.md](2026-07-07-phase-boundary-sweep-log.md)
— the committed run log is the sweep's evidence artifact.

Headline numbers:
- 53/53 `pass`; every invocation printed `ALL PASS (1 case(s))` and exited 0.
- Runner output was uniform: across all 53 invocations the captured output
  contains exactly the per-case pass line and the ALL PASS footer — no stderr
  leakage, no warnings, no stray lines (verified by grepping the full captured
  log for anything else: zero hits).
- Total 1331 s; per-case sum equals the loop total (aggregate loop overhead
  < 1 s). Mean 25.1 s, median 27 s, min 6 s (fact-text-malformed), max 28 s
  (many; nothing above 28 s — no slow outliers, i.e. no cold compile and no
  straggler).

## 3. Triage

None required: no non-pass occurred, so no branch of the exit taxonomy was
exercised. For the record, in self-proof mode the taxonomy collapses to
pass / irreproducible / error — a `divergent` verdict is unreachable
oracle-vs-oracle (`harness/run.py` judges any cross-pair mismatch with
`engine_a == engine_b` as `irreproducible`), so "cross-engine divergence" could
only have appeared via a runner defect; it did not appear.

## 4. Timing outliers — and one honesty note

Seven cases run below the 24-28 s band; five are fully explained by their banked
`timing` blocks (expect-raise cases never call reason; the no-program reset cases
do no reasoning work; graphml-empty reasons an empty graph in 1.47 s).

The remaining two (load-graphml-no-attr-parse 19 s, graph-attr-parsing-off 20 s,
vs 26 s for their attrs-on siblings) are **not** explained by the instrumented
segments: `import_s` and `reason_s` are equal across each pair, and the probe
sets are identical in kind and count (7 probes — verified against both the case
files and the banked artifacts after my first hypothesis, "lighter probe set",
was refuted by that check). The ~1.5 s/capture residual sits in uninstrumented
capture time; the attrs-on artifacts are larger (3.6 KB vs 2.0 KB), which is
directionally consistent with more observed data but nowhere near proving the
magnitude. One run per case cannot separate a systematic cost from
machine-schedule noise. **Cause unproven — recorded as an observation, not a
finding.** No verdict rides on wall-clock; all judgments are digest/probe
comparisons and every same-engine repeat was exactly reproducible.

(Idea seed if anyone cares later: a `probe_s` timing field in the capture would
make this class of residual attributable for free.)

## 5. What was and was not touched

- Code touched: **none.** No harness, case, fixture, or test change; `git status`
  clean throughout except the two docs files this report comprises.
- Repo state: oracle tree clean at the pin before and after; `results/` artifacts
  refreshed by the sweep (unversioned, as always).
- Consequence per the packet: **clean sweep banks directly** — no reviewer
  session is triggered by this packet.

## 6. Reproduction

```
uv run pytest -m "not e2e"
for f in harness/cases/*.json; do
  PYTHONHASHSEED=0 uv run python -m harness.run --cases "$f" --engine-a oracle-env/bin/python
done
```

Expect ~22 min warm; on a cold numba cache the first parallel-branch capture pays
~174 s compile (schedule, not a finding — session 10's characterization).
