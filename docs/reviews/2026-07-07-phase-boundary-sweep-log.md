# Phase-boundary full-corpus sweep — run log (2026-07-07)

The settings-knob phase's verdict-of-record: every committed case, oracle-vs-oracle
(self-proof mode — `--engine-a` only, so engine B is the same executable and any
cross-pair mismatch judges `irreproducible`, never `divergent`). This log is the
sweep's evidence artifact: per-case verdict + wall-clock, totals, outliers.

## Run conditions

- Corpus: all `harness/cases/*.json` — **53 case files, 53 distinct case ids** (counted,
  matching the expected 53).
- Invocation, one case per runner call, looped over the sorted corpus:
  `PYTHONHASHSEED=0 uv run python -m harness.run --cases harness/cases/<case>.json
  --engine-a oracle-env/bin/python`
- Engine fingerprint (recorded in every banked artifact): pyreason 3.6.0,
  python 3.10.20, darwin, `PYTHONHASHSEED=0`.
- Oracle pin `e1a94af33e1f`, tree verified clean before and after the sweep.
- 4 fresh-process captures per case (a1/a2/b1/b2); same-engine repeats compared by
  exact digest, cross-pair probes by per-case policy.
- Fast tier green immediately before (70 passed) and immediately after (70 passed)
  the sweep. Preflight 10/10 at session start.
- Numba cache state going in: warm — the parallel kernel's 10.3 MB `.nbc` present
  from session 10 (mtime Jul 7 00:41), so no cold-compile capture occurred
  (session 10's ~174 s cold-cache schedule note did not apply).

## Per-case results (runner order = sorted case filename)

| # | case | verdict | wall (s) |
|---|------|---------|----------|
| 1 | abort-on-inconsistency-default | pass | 24 |
| 2 | abort-on-inconsistency-on | pass | 24 |
| 3 | allow-ground-rules-off | pass | 26 |
| 4 | allow-ground-rules-on | pass | 25 |
| 5 | canonical-last-write | pass | 28 |
| 6 | canonical-on | pass | 27 |
| 7 | conv-delta-bound | pass | 28 |
| 8 | conv-delta-interp | pass | 28 |
| 9 | conv-perfect | pass | 28 |
| 10 | edge-rule-frames | pass | 28 |
| 11 | fact-text-malformed | pass | 6 |
| 12 | fp-version-on | pass | 28 |
| 13 | graph-attr-parsing-off | pass | 20 |
| 14 | graph-attr-parsing-on | pass | 26 |
| 15 | graphml-attr-coercions | pass | 26 |
| 16 | graphml-empty | pass | 16 |
| 17 | hello-world | pass | 27 |
| 18 | inconsistency-ipl-override | pass | 27 |
| 19 | inconsistency-ipl-resolve | pass | 25 |
| 20 | load-graphml-basic | pass | 26 |
| 21 | load-graphml-no-attr-parse | pass | 19 |
| 22 | memory-profile-default | pass | 28 |
| 23 | memory-profile-on | pass | 28 |
| 24 | output-file-name-custom | pass | 28 |
| 25 | output-file-name-inert | pass | 28 |
| 26 | output-to-file-default | pass | 28 |
| 27 | output-to-file-on | pass | 28 |
| 28 | parallel-computing-default | pass | 28 |
| 29 | parallel-computing-on | pass | 28 |
| 30 | parallel-fp-precedence | pass | 28 |
| 31 | persistent-off | pass | 28 |
| 32 | persistent-on | pass | 28 |
| 33 | reason-again-no-program | pass | 28 |
| 34 | reason-again-restart-false | pass | 28 |
| 35 | reason-again-restart-true | pass | 28 |
| 36 | reason-bare-again-no-facts | pass | 25 |
| 37 | reset-no-program | pass | 13 |
| 38 | reset-rules-no-program | pass | 13 |
| 39 | reset-rules-with-program | pass | 28 |
| 40 | reset-settings-restore | pass | 28 |
| 41 | reset-with-program | pass | 28 |
| 42 | reverse-digraph-default | pass | 26 |
| 43 | reverse-digraph-on | pass | 26 |
| 44 | rule-text-malformed | pass | 8 |
| 45 | save-graph-attrs-to-trace-off | pass | 27 |
| 46 | save-graph-attrs-to-trace-on | pass | 27 |
| 47 | static-graph-facts-off | pass | 26 |
| 48 | static-graph-facts-on | pass | 26 |
| 49 | store-off-accessors | pass | 25 |
| 50 | store-off-atom-trace-flip | pass | 25 |
| 51 | update-mode-default | pass | 26 |
| 52 | update-mode-junk-string | pass | 26 |
| 53 | update-mode-override | pass | 26 |

## Totals

- **53 / 53 pass. Zero divergent, zero irreproducible, zero error.** Every runner
  invocation printed `ALL PASS (1 case(s))` and exited 0; the captured runner output
  contains no line beyond the per-case pass line and the ALL PASS footer for all
  53 cases (no stderr leakage, no warnings surfaced at the runner level).
- Total wall-clock: **1331 s (22 m 11 s)**; per-case sum equals the loop total
  (loop overhead < 1 s aggregate). Mean 25.1 s/case; median 27 s; min 6 s; max 28 s.

## Timing outliers

The corpus sits in a tight 24-28 s band (46 of 53 cases) — ~6.5 s per fresh-process
capture × 4 captures (uv + interpreter start, `import_s` ≈ 1.35 s, `reason_s` ≈
2.6-2.9 s per the banked artifacts). Seven cases run faster, each for a reason
visible in its banked `timing` block — all expected case shapes, none a finding:

| case | wall (s) | banked per-capture timing | why it is fast |
|------|----------|---------------------------|----------------|
| fact-text-malformed | 6 | `reason_s: null` | expect-raise case; no reason call |
| rule-text-malformed | 8 | `reason_s: null` | expect-raise case; no reason call |
| reset-no-program | 13 | steps 0.0 / 0.0 | reset + no-op reason, no reasoning work |
| reset-rules-no-program | 13 | steps 0.0 / 0.0 | reset_rules + no-op reason |
| graphml-empty | 16 | reason 1.47 s | empty graph, cheap reason |
| load-graphml-no-attr-parse | 19 | reason 2.57 s | see note below — cause unproven |
| graph-attr-parsing-off | 20 | reason 2.58 s | see note below — cause unproven |

Note on the two attr-parse-off cases (19-20 s vs their attrs-on siblings' 26 s):
the instrumented segments are equal across each pair (`import_s` ≈ 1.35 s,
`reason_s` 2.57-2.58 s off vs 2.40-2.46 s on) and the probe sets are identical in
kind and count (7 probes, verified from the case files and banked artifacts), so
the ~1.5 s/capture residual sits in uninstrumented capture time (loader + probe
execution + artifact write; the attrs-on artifacts are larger, 3.6 KB vs 2.0 KB).
One run per case cannot separate a systematic cost from machine-schedule noise —
**cause unproven, recorded as an observation only**; no verdict rides on wall-clock
(all judgments are digest/probe comparisons, and every same-engine repeat was
exactly reproducible).

The parallel-branch cases (parallel-computing-on, parallel-fp-precedence) ran warm
at 28 s — in-band, confirming the compile cache held across this sweep's eight
fresh parallel-kernel processes (consistent with session 10's caching
characterization; no new timing claim made here).

No slow outliers: nothing exceeded 28 s.

## Triage

Nothing to triage — no non-pass occurred, so no branch of the exit taxonomy
(cross-engine divergence / same-engine irreproducibility / error) was exercised
on this run. No code, case, or fixture was modified this session.

## Reproduction

```
uv run pytest -m "not e2e"
for f in harness/cases/*.json; do
  PYTHONHASHSEED=0 uv run python -m harness.run --cases "$f" --engine-a oracle-env/bin/python
done
```

(On a cold numba cache the first parallel-branch capture pays ~174 s compile —
schedule, not a finding.)
