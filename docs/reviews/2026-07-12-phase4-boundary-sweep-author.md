<!-- doccode: pyreason-rewrite-docs-reviews-phase4-boundary-sweep-author -->
# Phase-4 boundary sweep — the verdict-of-record for the current tree (author report)

- session: 32 · 2026-07-12 · the phase-boundary verdict-of-record packet
- verdict: **116/116 committed cases equivalence PASS, oracle-vs-rewrite, in ONE
  `harness.run` invocation** (`results-phase4-boundary/report.json`, exit 0,
  `ALL PASS (116 case(s))`, resume block `resumed: false`) — zero divergent,
  zero irreproducible, zero error, **zero spot-fixes needed**; fast tier
  **321 passed, 6 deselected** before launch and after the sweep, unchanged
- scope of the claim: this is the verdict-of-record **for the tree as it
  stands** — the pure-Python core with the session-28 optimizations, i.e. the
  Option-B state of [docs/perf/execution-layer-options.md](../perf/execution-layer-options.md).
  The operator's execution-layer commitment is still pending; if a different
  option is chosen and engine code changes, this sweep re-runs over that tree.
- DIV records opened this session: **none** (next free stays DIV-0004; the
  three existing records are all adjudicated and unchanged)

## The invocation

**Case count, enumerated, not assumed:** `ls harness/cases/*.json | wc -l` →
**116**; the runner's duplicate-id gate saw the same 116 (session 24's corpus
was 96 — since then the phase-4 ladder rungs, the registrand-behavior,
warn-skip, coercion, delta/weights-dtype families, and
`parallel-computing-multirule` were committed by sessions 26–31).

```
PYTHONHASHSEED=0 uv run python -m harness.run --cases harness/cases \
  --engine-a oracle-env/bin/python --engine-b scripts/rewrite-python \
  --results results-phase4-boundary
```

- **Launched:** 2026-07-12T11:41:52Z, detached (`nohup`), one process.
- **Wall-clock:** **2308 s (38.5 min)** launch-to-report (epoch marker at
  launch vs `report.json` mtime).
- **Results dir:** `results-phase4-boundary/` — git-ignored by the `results*/`
  glob; 116 case dirs × (4 capture artifacts + 4 logs + `case.done.json`
  completion marker) + the one whole-sweep `report.json` (580 JSON artifacts).
- **Verdicts:** 116/116 `pass`; console tail `ALL PASS (116 case(s))`.
  Same-engine repeats (a1/a2, b1/b2 per case, fresh processes,
  `PYTHONHASHSEED=0`) were digest-stable in all 116 cases — zero
  irreproducible, so no harness-or-environment failure needed running down
  in the banked run.

**Honesty block (the report's own resume accounting):** `resumed: false`,
`prior_complete: []`, `captured_this_invocation: 116` — every capture in the
banked artifact was made by this single invocation; the durable runner's
resume machinery was **not** exercised in the run of record. Single clean
invocation over the final tree: **yes**.

**Run incident, named honestly (environment, not engine):** the *first*
launch of this exact command (11:28:18Z, backgrounded through the session
harness) was killed ~34 s in — runner process gone mid-capture on
`accessors-lifecycle` a2, no `report.json`, no exit line, output file empty —
a session-host background-task interruption, the same class as the phase-3
sweep's incident (see the 2026-07-07 phase-3 boundary author report). Per the
taxonomy rule this is a harness/environment failure, never an engine finding:
the partial dir (3 completed cases) was **deleted wholesale** and the sweep
relaunched clean, detached with `nohup`, same command, fresh
`results-phase4-boundary/`. The banked artifact is entirely the second,
uninterrupted invocation — no verdict rests on the first attempt, and the
preferred verdict-of-record form (clean single invocation, session-31 idea
seed) is preserved rather than resumed into.

**Screen-then-confirm:** before the full run, a 3-case screen
(`query-construct`, `label-ops`, `ipl-load-malformed`) ran into a throwaway
scratchpad results dir — ALL PASS in under a minute; staging and results dirs
were deleted.

## Independent re-derivation (self-audit)

Because `report.json` is written once by the runner, all 116 verdicts were
also re-derived from the on-disk artifacts through the pure judge
(`harness.run.judge_case`, per-case comparison policy from the committed case
files): **116/116 `pass` over all 464 capture artifacts**, and every artifact
carries `env == {"PYTHONHASHSEED": "0"}`, engine A =
`oracle-env/bin/python` (pyreason **3.6.0**, python **3.10.20** — the pin),
engine B = the campaign venv python via `scripts/rewrite-python` (pyreason
**0.1.0.dev0**, python **3.13.11**). Snippet in §Repro.

**Mtime analysis (single-invocation coherence, per the runner's docstring):**
all 580 JSON files in the results dir have mtimes inside the invocation
window — earliest +7 s after launch, latest at the report write; nothing in
the dir predates the launch (the first attempt's partial dir was deleted, so
no artifact from it exists to leak in).

## Spot-fix loop

**Empty.** No FAIL of any taxonomy surfaced: 116/116 passed on the single
invocation, so no harness or rewrite fixes, no seam tests added, no targeted
reruns, no full-sweep re-invocation, and no new DIV record. Nothing was
absorbed and no comparison was loosened: `git status --porcelain` was empty
after the sweep — no `harness/`, `src/`, or `tests/` change this session.

## Fast tier

`uv run pytest -m "not e2e"` → **321 passed, 6 deselected**, unchanged from
session 31, green both before the sweep launch and after it. This packet adds
no tests (nothing needed proving that the 116 cases don't already prove) and
removes none. The 6 deselected are the e2e-marked pin-side DIV reproducers,
the substrate-gated tests, and the mini-sweep resume exercise, per the gate's
design.

## The verdict-of-record statement

The rewrite — the pure-Python core with the session-28 optimizations, exactly
the Option-B tree awaiting the operator's execution-layer word — is
**equivalent to the pinned oracle (e1a94af3, v3.6.0) over the entire
committed 116-case corpus, in a single clean harness invocation**
(`results-phase4-boundary/report.json`, `resumed: false`). Every case
compared under its committed per-case policy — exact compare everywhere
except the long-standing canonicalizations (trace/txt timestamps, peak-MB) —
with fresh-process same-engine repeats digest-stable on both engines. Known
divergences stand at exactly three (DIV-0001, DIV-0002, DIV-0003), all
operator-adjudicated, all confined to inputs no committed case can bank.
Equivalence claims are co-extensive with this artifact: uncovered input
classes and named-unobserved facets recorded in `docs/surface.md` notes
remain outside any claim. **Contingency:** this verdict is the record for the
current tree; the pending execution-layer decision does not alter it, but a
decision that changes engine code (Option A or C) requires a fresh boundary
sweep over the changed tree.

## Full pass list (116/116, sorted)

abort-on-inconsistency-default, abort-on-inconsistency-on,
accessors-fresh-state, accessors-lifecycle, allow-ground-rules-off,
allow-ground-rules-on, annotation-fn-duplicate-name,
annotation-fn-reset-clears, annotation-fn-return-interval,
annotation-fn-return-triple, annotation-fn-six-arg, annotation-fn-two-arg,
annotation-fn-unregistered-name, canonical-last-write, canonical-on,
closed-world-off, closed-world-on, closed-world-unknown-predicate,
conv-delta-bound, conv-delta-interp, conv-perfect, delta-zero-rule,
edge-rule-frames, fact-csv-ragged, fact-from-csv-basic,
fact-from-csv-malformed, fact-from-csv-warn-skip, fact-from-json-basic,
fact-from-json-malformed, fact-from-json-warn-skip, fact-text-malformed,
fp-version-on, graph-attr-parsing-off, graph-attr-parsing-on,
graphml-attr-coercions, graphml-empty, graphml-static-pin,
head-fn-duplicate-name, head-fn-edge-rule-positions, head-fn-grounding,
head-fn-reset-clears, head-fn-return-bare-string, head-fn-ungrounded-var,
head-fn-unregistered-name, hello-world, inconsistency-ipl-override,
inconsistency-ipl-resolve, interval-ops, ipl-atom-trace-off-trace,
ipl-load-basic, ipl-load-malformed, ipl-load-null-overwrite, label-ops,
load-graphml-basic, load-graphml-no-attr-parse, memory-profile-default,
memory-profile-on, memory-profile-output-on, output-file-name-custom,
output-file-name-inert, output-to-file-default, output-to-file-on,
parallel-computing-default, parallel-computing-multirule,
parallel-computing-on, parallel-fp-precedence, perf-ladder-large,
perf-ladder-medium, perf-ladder-small, persistent-off, persistent-on,
query-construct, reason-again-no-program, reason-again-restart-false,
reason-again-restart-true, reason-bare-again-no-facts, reason-queries-filter,
reason-queries-no-match, reason-queries-no-match-edge-heavy,
reset-no-program, reset-rules-no-program, reset-rules-with-program,
reset-settings-restore, reset-with-program, reverse-digraph-default,
reverse-digraph-on, rule-delta-variants, rule-from-csv-basic,
rule-from-csv-malformed, rule-from-csv-warn-skip, rule-from-json-basic,
rule-from-json-malformed, rule-from-json-warn-skip, rule-json-weights-dtypes,
rule-text-malformed, rules-from-file-basic, rules-from-file-malformed,
save-graph-attrs-to-trace-off, save-graph-attrs-to-trace-on,
save-rule-trace-atom-trace-off, save-rule-trace-basic,
save-rule-trace-clause-reorder, save-rule-trace-store-off,
static-graph-facts-off, static-graph-facts-on, store-off-accessors,
store-off-atom-trace-flip, threshold-construct, threshold-dict-gate,
threshold-number-gate-clause-level, threshold-number-gate-default,
threshold-number-gate-two, threshold-percent-total, update-mode-default,
update-mode-junk-string, update-mode-override.

## Hygiene

- Preflight doctor 10/10 at session start.
- Oracle byte-clean post-run: `git -C oracle/pyreason status --porcelain`
  empty; HEAD `e1a94af33e1f9d925c9df8284113dd0e14fe8a73` = `oracle/PIN`.
- No installs, no dependency changes: `git diff -- pyproject.toml uv.lock`
  empty; both engines' environments exactly as found.
- Nothing under `results*` newly tracked; `results-phase4-boundary/` covered
  by the committed `results*/` glob.
- The full-corpus run was this packet's explicit job (the sanctioned
  phase-boundary run); the fast tier and the 3-case screen were the only
  other engine executions.

## Open follow-ups (carried, unchanged by this session)

- **The execution-layer commitment** (blocking, operator gate):
  [docs/perf/execution-layer-options.md](../perf/execution-layer-options.md),
  recommendation Option B — this sweep is the equivalence half of that
  decision's evidence for the current tree.
- After the word: the AC-5 closure audit and the execution-layer ADR
  (AC-5.5 version-headroom statement per the chosen option).
- Non-blocking: the oracle-env numba-cache re-baseline (session-29 review
  F2). Context only, no claim: this sweep's 2308 s wall-clock is not
  comparable to the phase-3 sweep's 1524 s — different corpus (116 vs 96,
  including the ladder rungs) and unmeasured oracle cache state; the
  re-baseline packet owns any timing claim.

## Repro

```
uv run pytest -m "not e2e"                    # 321 passed, 6 deselected
ls harness/cases/*.json | wc -l               # 116
PYTHONHASHSEED=0 uv run python -m harness.run --cases harness/cases \
  --engine-a oracle-env/bin/python --engine-b scripts/rewrite-python \
  --results results-phase4-boundary-repro     # fresh dir for a re-run; ~40 min

# re-derive every verdict from the banked artifacts (no engine needed)
uv run python - <<'EOF'
import json
from pathlib import Path
from harness.run import judge_case
for cp in sorted(Path('harness/cases').glob('*.json')):
    case = json.loads(cp.read_text())
    arts = {n: json.loads((Path('results-phase4-boundary')/case['id']/f'{n}.json').read_text())
            for n in ('a1','a2','b1','b2')}
    assert judge_case(case, arts)['status'] == 'pass', case['id']
print('116/116 re-derived pass')
EOF

git -C oracle/pyreason status --porcelain && git -C oracle/pyreason rev-parse HEAD
```
