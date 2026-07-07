<!-- doccode: pyreason-rewrite-docs-reviews-phase3-boundary-sweep-raw -->
# Author report — Phase-3-boundary full-corpus sweep (session 15, raw)

Packet: session 14's NEXT — the breadth grind closed at 52/52 cased, so per the
wall-clock rule (operator-set 2026-07-06) this dedicated session runs the full
94-case corpus oracle-vs-oracle, spot-fixes what surfaces, and banks the
verdict-of-record before Phase 3 opens.

Author: session 15 agent 1, 2026-07-07. Oracle pin `e1a94af33e1f` (v3.6.0), tree
verified byte-clean before and after all runs.

Filename note: the packet named `2026-07-07-phase-boundary-sweep-raw.md` as the
target, but that path is session 11's committed verdict-of-record for the
*settings-knob* phase boundary (commit `02d392e`, 53/53). This report takes the
`phase3-` name rather than clobber a banked artifact.

## Verdict

**CLEAN SWEEP — 94/94 pass, zero divergent, zero irreproducible, zero error, in
2783 s (46 m 23 s) sweep wall-clock (screen adds 251 s; session engine total
~50.6 min). No harness, case, fixture, or test code was touched — the spot-fix
loop is empty. The registrand cache-confinement mechanism's promise held exactly:
zero `harness.reference_fns` references and zero surviving registrand overloads
in the oracle-env bundled kernel cache after the sweep.**

## 1. Session-start state

- `git status` clean at `7323327`; oracle tree clean at the pin.
- Fast tier `uv run pytest -m "not e2e"` → **104 passed / 2 deselected** (run
  again after the sweep: 104/2 — no fix happened, run as a free tripwire).
- Preflight 10/10 (verified by the orchestrator at session start; re-run by the
  author after the sweep: 10/10).
- Corpus census: 94 case files, 94 distinct ids; the swept id set was diffed
  against `harness/cases/*.json` — identical.
- Oracle-env bundled kernel cache baseline: 231 files, **zero**
  `harness.reference_fns` references (the session-14 review left it repaired at
  219; the +12 since are consistent with the review's own post-repair
  verification runs re-populating the six repaired kernels' normal
  specializations — 6 kernels x index + code — though that decomposition is
  inferred from the count, not from per-file archaeology).

## 2. Screen (screen-then-confirm)

Four representative cases, one per mandated category, each the committed
single-case runner form:

| case | category | result | wall-clock |
| --- | --- | --- | --- |
| hello-world | baseline | pass | 26.8 s |
| save-rule-trace-basic | rule-trace output | pass | 27.4 s |
| memory-profile-on | memory profile | pass | 28.5 s |
| annotation-fn-two-arg | registrand | pass | 168.1 s |

After the registrand screen case: bundled cache still 231 files, zero registrand
references — the confinement mechanism confirmed live before committing to the
full run. The 168 s registrand time matched the session-14 budget note
(~40–60 s compile x 4 captures), fixing the schedule estimate.

## 3. The sweep

One runner invocation per case, serial, run order = sorted filename order except
`parallel-computing-on` (deferred to the last non-registrand slot) and the seven
registrand cases (run last, isolated two-per-driver-call so no registrand capture
could be killed mid-run — a kill skips the cache restore, the mechanism's one
documented residual exposure). Each invocation:

```
PYTHONHASHSEED=0 uv run python -m harness.run --cases harness/cases/<id>.json --engine-a oracle-env/bin/python
```

Self-proof mode (engine B defaults to engine A): 4 fresh-process captures per
case, same-engine repeats compared by exact digest, cross-pair probes by per-case
policy. In this mode a cross-pair mismatch judges `irreproducible`, never
`divergent` — a cross-engine divergence is impossible oracle-vs-oracle, and none
of the taxonomy's non-pass branches was exercised.

Engine fingerprint in every banked artifact: pyreason 3.6.0, python 3.10,
darwin, `PYTHONHASHSEED=0`. Screen cases were re-run inside the sweep loop; every
case's verdict-of-record is its in-loop run.

### Per-case verdicts (run order)

| # | case | verdict | wall-clock (s) | notes |
| --- | --- | --- | --- | --- |
| 1 | abort-on-inconsistency-default | pass | 24.5 |  |
| 2 | abort-on-inconsistency-on | pass | 24.8 |  |
| 3 | accessors-fresh-state | pass | 5.9 | no reasoning work (authoring-fault exit-2 arms or construction-only probes) |
| 4 | accessors-lifecycle | pass | 26.0 |  |
| 5 | allow-ground-rules-off | pass | 26.4 |  |
| 6 | allow-ground-rules-on | pass | 26.5 |  |
| 7 | canonical-last-write | pass | 28.2 |  |
| 8 | canonical-on | pass | 28.3 |  |
| 9 | closed-world-off | pass | 25.4 |  |
| 10 | closed-world-on | pass | 26.8 |  |
| 11 | conv-delta-bound | pass | 65.2 | cold compile of a new `reason` specialization; wrote overload `.2.nbc` 06:06; its 3 repeat captures ran warm |
| 12 | conv-delta-interp | pass | 28.3 |  |
| 13 | conv-perfect | pass | 28.3 |  |
| 14 | edge-rule-frames | pass | 28.9 |  |
| 15 | fact-from-csv-basic | pass | 29.3 |  |
| 16 | fact-from-csv-malformed | pass | 6.0 | no reasoning work (authoring-fault exit-2 arms or construction-only probes) |
| 17 | fact-from-json-basic | pass | 28.4 |  |
| 18 | fact-from-json-malformed | pass | 6.6 | no reasoning work (authoring-fault exit-2 arms or construction-only probes) |
| 19 | fact-text-malformed | pass | 6.1 | no reasoning work (authoring-fault exit-2 arms or construction-only probes) |
| 20 | fp-version-on | pass | 28.5 |  |
| 21 | graph-attr-parsing-off | pass | 19.8 |  |
| 22 | graph-attr-parsing-on | pass | 26.7 |  |
| 23 | graphml-attr-coercions | pass | 26.5 |  |
| 24 | graphml-empty | pass | 15.7 |  |
| 25 | hello-world | pass | 28.3 |  |
| 26 | inconsistency-ipl-override | pass | 26.9 |  |
| 27 | inconsistency-ipl-resolve | pass | 25.5 |  |
| 28 | interval-ops | pass | 6.9 | no reasoning work (authoring-fault exit-2 arms or construction-only probes) |
| 29 | ipl-atom-trace-off-trace | pass | 26.9 |  |
| 30 | ipl-load-basic | pass | 28.6 |  |
| 31 | ipl-load-malformed | pass | 6.2 | no reasoning work (authoring-fault exit-2 arms or construction-only probes) |
| 32 | ipl-load-null-overwrite | pass | 28.6 |  |
| 33 | label-ops | pass | 6.0 | no reasoning work (authoring-fault exit-2 arms or construction-only probes) |
| 34 | load-graphml-basic | pass | 26.8 |  |
| 35 | load-graphml-no-attr-parse | pass | 19.8 |  |
| 36 | memory-profile-default | pass | 28.6 |  |
| 37 | memory-profile-on | pass | 29.2 |  |
| 38 | memory-profile-output-on | pass | 29.3 |  |
| 39 | output-file-name-custom | pass | 28.6 |  |
| 40 | output-file-name-inert | pass | 28.6 |  |
| 41 | output-to-file-default | pass | 28.6 |  |
| 42 | output-to-file-on | pass | 28.5 |  |
| 43 | parallel-computing-default | pass | 28.4 |  |
| 44 | parallel-fp-precedence | pass | 28.5 |  |
| 45 | persistent-off | pass | 28.5 |  |
| 46 | persistent-on | pass | 28.6 |  |
| 47 | query-construct | pass | 6.2 | no reasoning work (authoring-fault exit-2 arms or construction-only probes) |
| 48 | reason-again-no-program | pass | 28.4 |  |
| 49 | reason-again-restart-false | pass | 28.5 |  |
| 50 | reason-again-restart-true | pass | 28.6 |  |
| 51 | reason-bare-again-no-facts | pass | 25.7 |  |
| 52 | reason-queries-filter | pass | 63.5 | cold compile, queries-bearing `reason` signature; wrote overload `.3.nbc` 06:23; repeats warm |
| 53 | reason-queries-no-match | pass | 22.7 |  |
| 54 | reset-no-program | pass | 13.6 |  |
| 55 | reset-rules-no-program | pass | 13.5 |  |
| 56 | reset-rules-with-program | pass | 28.4 |  |
| 57 | reset-settings-restore | pass | 28.8 |  |
| 58 | reset-with-program | pass | 28.6 |  |
| 59 | reverse-digraph-default | pass | 26.5 |  |
| 60 | reverse-digraph-on | pass | 26.4 |  |
| 61 | rule-from-csv-basic | pass | 29.1 |  |
| 62 | rule-from-csv-malformed | pass | 10.5 |  |
| 63 | rule-from-json-basic | pass | 28.7 |  |
| 64 | rule-from-json-malformed | pass | 5.9 | no reasoning work (authoring-fault exit-2 arms or construction-only probes) |
| 65 | rule-text-malformed | pass | 8.5 | no reasoning work (authoring-fault exit-2 arms or construction-only probes) |
| 66 | rules-from-file-basic | pass | 28.6 |  |
| 67 | rules-from-file-malformed | pass | 10.5 |  |
| 68 | save-graph-attrs-to-trace-off | pass | 26.7 |  |
| 69 | save-graph-attrs-to-trace-on | pass | 27.4 |  |
| 70 | save-rule-trace-atom-trace-off | pass | 26.9 |  |
| 71 | save-rule-trace-basic | pass | 28.7 |  |
| 72 | save-rule-trace-clause-reorder | pass | 28.4 |  |
| 73 | save-rule-trace-store-off | pass | 25.4 |  |
| 74 | static-graph-facts-off | pass | 26.5 |  |
| 75 | static-graph-facts-on | pass | 26.5 |  |
| 76 | store-off-accessors | pass | 25.4 |  |
| 77 | store-off-atom-trace-flip | pass | 25.4 |  |
| 78 | threshold-construct | pass | 5.9 | no reasoning work (authoring-fault exit-2 arms or construction-only probes) |
| 79 | threshold-dict-gate | pass | 25.4 |  |
| 80 | threshold-number-gate-clause-level | pass | 26.5 |  |
| 81 | threshold-number-gate-default | pass | 26.4 |  |
| 82 | threshold-number-gate-two | pass | 25.2 |  |
| 83 | threshold-percent-total | pass | 26.5 |  |
| 84 | update-mode-default | pass | 26.0 |  |
| 85 | update-mode-junk-string | pass | 25.8 |  |
| 86 | update-mode-override | pass | 24.5 |  |
| 87 | parallel-computing-on | pass | 28.3 | ran last of the non-registrands; parallel kernel warm from prior sessions |
| 88 | annotation-fn-reset-clears | pass | 19.9 | registrand case; reset clears registration before reason, so the reason signature stays warm |
| 89 | annotation-fn-six-arg | pass | 174.2 | dispatcher-bearing registrand case: all 4 captures compile cold (~44 s each); cache restore verified |
| 90 | annotation-fn-two-arg | pass | 170.1 | dispatcher-bearing registrand case: all 4 captures compile cold (~43 s each); cache restore verified |
| 91 | annotation-fn-unregistered-name | pass | 19.9 | registrand case; warm reason signature (NameError banked as behavior) |
| 92 | head-fn-grounding | pass | 217.4 | dispatcher-bearing registrand case, slowest in corpus: all 4 captures compile cold (~54 s each); cache restore verified |
| 93 | head-fn-reset-clears | pass | 24.9 | registrand case; warm reason signature |
| 94 | head-fn-unregistered-name | pass | 24.9 | registrand case; warm reason signature |

Totals: 94 cases, 2783.3 s; mean 29.6 s, median 26.6 s. Band structure: ~24–29 s
for reasoning cases; ~6–11 s for cases that never reason (authoring-fault exit-2
arms, construction-only probes, malformed-input loaders); 13–20 s for
reduced-work cases (no-program resets, attr-parsing-off, graphml-empty).

## 4. Triage / spot-fix loop

Empty — no non-pass occurred. Nothing was fixed, weakened, or canonicalized;
no per-case comparison policy changed.

## 5. Post-sweep hygiene

- **Oracle tree:** `git -C oracle/pyreason status --porcelain` empty; HEAD
  `e1a94af33e1f`. Byte-clean before and after.
- **Bundled kernel cache:** zero `harness.reference_fns` references in any
  index. File count 231 → 233; both new files diagnosed from the run timeline,
  neither registrand-related:
  - `interpretation.Interpretation.reason-240.py310.2.nbc` (9.8 MB, 06:06) —
    written while `conv-delta-bound` was in flight (65.2 s, ~2x band: cold
    compile of a new `reason` signature specialization, repeats warm).
  - `...reason-240.py310.3.nbc` (9.9 MB, 06:23) — written while
    `reason-queries-filter` was in flight (63.5 s, same pattern: the
    queries-bearing `reason` call is a distinct signature).
  Both are legitimate non-registrand specializations — exactly what the on-disk
  cache is for (the session-14 repair deleted the six poisoned kernels' full
  cache sets, so this sweep was the first to re-pay those two compiles; they are
  now cached for future sweeps). The registrand captures (06:34–06:49) left zero
  surviving `.nbc` additions; the rewritten indexes' 06:44/06:49 mtimes are the
  restore writing prior bytes back.
- **Repo:** `git status` clean (run artifacts confined to the gitignored
  `results/`; driver + CSV in the session scratchpad).
- **Fast tier:** 104 passed / 2 deselected after the sweep. Preflight 10/10.

## 6. What Phase 3 should know

- **Schedule:** a full warm-cache sweep costs ~46 min on this machine; the three
  dispatcher-bearing registrand cases (`head-fn-grounding` 217 s,
  `annotation-fn-six-arg` 174 s, `annotation-fn-two-arg` 170 s) are 20% of it
  and irreducible in-process — every fresh-process capture re-pays the compile
  because dispatcher-bearing signatures never hit numba's on-disk cache
  (session-14 review, re-confirmed here: all four captures of each ran
  ~equal-cold). The other four registrand cases stay in the normal band; only
  cases whose `reason()` call carries a dispatcher pay.
- **Cache dynamics:** first-run-after-repair specializations (`conv-delta-bound`,
  `reason-queries-filter`) each cost one ~35 s cold compile and ~10 MB of
  site-packages, once; they are warm now. Future sweeps should sit at ~44 min
  with no cache growth.
- **Reproducibility:** every one of 376 captures (94 x 4) was exactly
  reproducible by digest under `PYTHONHASHSEED=0` — the corpus is a stable
  differential baseline for the rewrite. No tolerance policies, no
  canonicalizations were needed anywhere oracle-vs-oracle.
- **The corpus is Phase-3-ready:** 94 banked oracle behaviors including the
  deliberate warts (Query silent misparses, the Interval prev-seed divergence,
  the unregistered-name asymmetry, the clause-level threshold gating) — each now
  re-proven stable in a single sweep, so any rewrite mismatch against them is a
  real divergence, not environment noise.
- Per session 14's NEXT: Phase 3 opens with the `networkx` dependency ask to the
  operator — an operator gate, not decided here.

## 7. Reproduction

```
uv run pytest -m "not e2e"
for f in harness/cases/*.json; do
  PYTHONHASHSEED=0 uv run python -m harness.run --cases "$f" --engine-a oracle-env/bin/python
done
```

Expect ~46 min warm (~44 min now that the two new specializations are cached);
the three dispatcher-bearing registrand cases pay their compiles on every run.
