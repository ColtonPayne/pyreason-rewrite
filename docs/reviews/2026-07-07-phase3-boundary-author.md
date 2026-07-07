<!-- doccode: pyreason-rewrite-docs-reviews-phase3-boundary-author -->
# Phase-3 breadth boundary sweep — the phase verdict-of-record (author report)

- session: 24 · 2026-07-07 · the phase's verdict-of-record packet
- verdict: **96/96 committed cases equivalence PASS, oracle-vs-rewrite, in ONE
  `harness.run` invocation** (`results-phase3-boundary/report.json`, exit 0,
  `ALL PASS (96 case(s))`) — zero divergent, zero irreproducible, zero error,
  **zero spot-fixes needed**; fast tier **270 passed, 4 deselected**; board
  **52/52 equivalent** (recomputed mechanically:
  `grep -c "^- status: equivalent" docs/surface.md` → 52)
- adjudication batch: [docs/ledger/phase3-adjudication-batch.md](../ledger/phase3-adjudication-batch.md)
  (commit `4e13676`) — **2 DIV records + 32 carried oracle-bug-candidates + 5
  borderline observations = 39 sections**, the document the operator adjudicates
  from between Phase 3 and Phase 4
- DIV records opened this session: **none** (next free stays DIV-0003 — no
  committed case mismatched)

## AC-1 — the single-invocation sweep

**Case count, enumerated, not assumed:** `ls harness/cases/*.json | wc -l` → **96**
(the runner's own duplicate-id gate saw the same 96; session 15's corpus was 94 —
since then `reason-queries-no-match-edge-heavy` and `head-fn-ungrounded-var`
were committed by the slice-6/7 reviews, and the four `ipl-*` cases replaced
nothing).

**The invocation** (one process, one report.json carrying all 96 verdicts —
exactly the artifact the carried sweep-durability seed asked for; the committed
runner accepts a case *directory*, so the session-15 one-case-per-invocation
last-writer-wins caveat does not apply here):

```
PYTHONHASHSEED=0 uv run python -m harness.run --cases harness/cases \
  --engine-a oracle-env/bin/python --engine-b scripts/rewrite-python \
  --results results-phase3-boundary
```

- **Results dir:** `results-phase3-boundary/` — gitignored this session per the
  slice convention (commit `4e13676`); 96 case dirs × 4 capture artifacts + logs
  + the one whole-sweep `report.json` (`engine_a`/`engine_b`/`hashseed`/96
  verdicts).
- **Wall-clock:** **1524 s (25.4 min)** launch-to-report (epoch markers around
  the invocation); first-artifact-to-report window 1496 s. Under the projected
  registrand-heavy budget because this run's oracle captures reused the numba
  cache the first attempt's captures had already warmed (below).
- **Verdicts:** 96/96 `pass` — the console tail reads `ALL PASS (96 case(s))`,
  and the per-case list in `report.json` is the full committed corpus, sorted:
  every id in §Full pass list below. Same-engine repeats (a1/a2, b1/b2 per
  case, fresh processes, `PYTHONHASHSEED=0`) were digest-stable in all 96 cases
  — zero irreproducible, so nothing needed running down on that axis.
- **Independent re-derivation (self-audit):** because `report.json` is written
  once by the runner, I also re-derived all 96 verdicts from the on-disk
  artifacts through the pure judge (`harness.run.judge_case`, per-case
  comparison policy from the committed case files): 96/96 `pass`, and every one
  of the 384 captures carries `env == {'PYTHONHASHSEED': '0'}`, engine A =
  `oracle-env/bin/python` (pyreason 3.6.0, python 3.10.20), engine B = the
  campaign venv python via `scripts/rewrite-python` (pyreason `0.1.0.dev0`).
  Snippet in §Repro.

**Run incident, named honestly (environment, not engine):** the *first* launch
of this exact invocation (17:58, backgrounded through the session harness) was
killed ~49 min in, mid-capture on `head-fn-grounding` a2 — runner process gone,
no `report.json`, no exit line, coincident with a session-host interruption
(the artifacts it did write were normal; the annotation-fn registrand family had
completed and passed judge-shape inspection). Per the packet's rule this was
run down as a harness/environment failure, never an engine finding: the partial
dir was **deleted wholesale** and the sweep relaunched clean, detached
(`nohup`), same command, same results path. The banked artifact is entirely the
second, uninterrupted invocation — no case's verdict rests on the first
attempt. One side effect: the first attempt's oracle captures warmed the numba
cache, which is why the run of record's wall-clock (25.4 min) beats the ~46-min
class of the session-15 sweep; capture *outputs* are cache-independent (the
same digests bank either way — every slice rerun has demonstrated this).

**Screen-then-confirm:** before the full run, a 6-case screen (the 3 intended
cheap cases `query-construct`, `label-ops`, `ipl-load-malformed` plus 3
leftovers in the scratchpad staging dir) ran into a throwaway scratchpad
results dir — ALL PASS in ~51 s; the staging and results dirs were deleted.

## AC-2 — spot-fix loop

**Empty.** No FAIL of any taxonomy surfaced: 96/96 passed on the single
invocation, so no fixes to pinned behavior, no seam tests added, no targeted
reruns, and no new DIV record. Nothing was absorbed and no comparison was
loosened (the compare layer and every committed case file are untouched this
session — `git diff` shows no `harness/` or `tests/` change). Had a fix been
needed, the documented convention was: land fix + seam test, rerun the touched
cases into the same `results-phase3-boundary/` dir (the runner re-captures a
case's four artifacts atomically per case), and name those cases as
rerun-after-fix in this report. The convention went unused.

## AC-3 — fast tier

`uv run pytest -m "not e2e"` → **270 passed, 4 deselected** (0.71 s), unchanged
from session 23 — this packet adds no tests (nothing needed proving that the 96
cases don't already prove) and removes none. The 4 deselected are the e2e-marked
pin-side DIV reproducers and substrate-gated tests, per the gate's design.

## AC-4 — the adjudication batch

[docs/ledger/phase3-adjudication-batch.md](../ledger/phase3-adjudication-batch.md),
committed `4e13676` before the sweep verdict landed (its content is
sweep-independent; the clean sweep added no items). Assembly method: grep sweep
over `oracle-bug`, `quirk`, `O1`/`O2`, `adjudicat` across `docs/` (ledgers 4–23,
all slice author+review reports, the board, the ADRs, both DIV records), plus an
independent enumeration pass over the same corpus, reconciled item-by-item —
the two lists agreed after the reconciliation pass pulled in the slice-1
"deliberately reproduced (not repaired)" block and the session-6 fp-trace-shape
question that ADR 0003 answered. Structure: **Part A** the two DIV records with
options + recommendations (DIV-0001 recursion guard → accept; DIV-0002
non-string IPL → guarded raise); **Part B** 32 carried candidates, each with
what-the-pin-does (evidence path + oracle anchor), what-the-rewrite-does,
covering cases, and a recommendation — including the graphml silent-coercion
cluster (B20–B22) and O1/O2 (B23–B24) named by the packet, the state-lifecycle
five, the knob/schedule family with the fp residuals (B16 flagged as a Phase-4
hazard: fp + `timesteps=-1` hangs), and the three direction-decisions (B17
exception-payload asymmetry, B19 fp-trace-shape/ADR-0003 confirmation, B25
Interval prev-seed); **Part C** 5 borderline observations listed rather than
dropped, with a double-count guard note (the self-recursive-query SIGSEGV is
DIV-0001's pin-side half, not a separate item).

## AC-5 — the phase verdict-of-record

**Phase 3's claim, and the evidence that forces it:** the rewrite's reference
core is **equivalent to the pinned oracle (e1a94af3, v3.6.0) over the entire
committed case corpus — 96/96 in a single harness invocation**
(`results-phase3-boundary/report.json`), covering all 52 surface-inventory rows
(26 public functions, 6 types + 2 text DSLs, 18 settings knobs; the torch-gated
pair excluded by the operator-set scope note), with every banked verdict now
carried by one internally-consistent artifact rather than eight slice-scoped
ones. Every case compared under the committed per-case policies — exact
compare everywhere except the three long-standing canonicalizations (trace/txt
timestamps, peak-MB) — with fresh-process same-engine repeats digest-stable on
both engines. Known divergences stand at exactly two (DIV-0001, DIV-0002), both
confined to inputs no committed case can bank (a pin-side process death and a
pin-side address-derived message), both queued with proposals in the
adjudication batch. Equivalence claims here are exactly co-extensive with this
artifact: the uncovered input classes and named-unobserved facets recorded
per-row in `docs/surface.md` notes remain outside any claim.

**Board state:** 52/52 rows `equivalent`; inventory gate green
(`tests/test_surface_inventory.py`, 6 passed inside the fast tier).

**What Phase 4 opens with (charter AC-4 — the execution layer):** the evidence
path is *profile first, then build*: (1) **commit the workload ladder** —
small/medium/large harness cases with size rationale; **the ladder does not
exist yet and is Phase-4 work by design** (no committed case today is a
performance rung; none was started this session per the packet). The committed
ladder precedes any floor verdict. (2) **Bank oracle baselines on the campaign
machine** — cold-start (fresh-process import + first reason, warm numba cache;
the cache-*build* first-import banked separately as context, never as the bar),
steady throughput per rung, peak memory — screen-then-confirm with a
control-repeat noise band, medians with spread. (3) Then the execution-layer
work against the operator-signed floor: whatever the rewrite ships must not be
worse than the oracle baseline on the large rung beyond the banked noise band;
cold-start is a named first-class target. Phase-4 case design should respect
B16 (never fp + `timesteps=-1` on a ladder rung) and keeps the equivalence
harness as the shared input format (ladder cases are harness cases too).
**Before any of that: the operator adjudicates the batch** — the loop stops
after this session banks, per the session-22 instruction.

## Full pass list (96/96, `results-phase3-boundary/report.json` order)

abort-on-inconsistency-default, abort-on-inconsistency-on,
accessors-fresh-state, accessors-lifecycle, allow-ground-rules-off,
allow-ground-rules-on, annotation-fn-reset-clears, annotation-fn-six-arg,
annotation-fn-two-arg, annotation-fn-unregistered-name, canonical-last-write,
canonical-on, closed-world-off, closed-world-on, conv-delta-bound,
conv-delta-interp, conv-perfect, edge-rule-frames, fact-from-csv-basic,
fact-from-csv-malformed, fact-from-json-basic, fact-from-json-malformed,
fact-text-malformed, fp-version-on, graph-attr-parsing-off,
graph-attr-parsing-on, graphml-attr-coercions, graphml-empty,
head-fn-grounding, head-fn-reset-clears, head-fn-ungrounded-var,
head-fn-unregistered-name, hello-world, inconsistency-ipl-override,
inconsistency-ipl-resolve, interval-ops, ipl-atom-trace-off-trace,
ipl-load-basic, ipl-load-malformed, ipl-load-null-overwrite, label-ops,
load-graphml-basic, load-graphml-no-attr-parse, memory-profile-default,
memory-profile-on, memory-profile-output-on, output-file-name-custom,
output-file-name-inert, output-to-file-default, output-to-file-on,
parallel-computing-default, parallel-computing-on, parallel-fp-precedence,
persistent-off, persistent-on, query-construct, reason-again-no-program,
reason-again-restart-false, reason-again-restart-true,
reason-bare-again-no-facts, reason-queries-filter,
reason-queries-no-match-edge-heavy, reason-queries-no-match, reset-no-program,
reset-rules-no-program, reset-rules-with-program, reset-settings-restore,
reset-with-program, reverse-digraph-default, reverse-digraph-on,
rule-from-csv-basic, rule-from-csv-malformed, rule-from-json-basic,
rule-from-json-malformed, rule-text-malformed, rules-from-file-basic,
rules-from-file-malformed, save-graph-attrs-to-trace-off,
save-graph-attrs-to-trace-on, save-rule-trace-atom-trace-off,
save-rule-trace-basic, save-rule-trace-clause-reorder,
save-rule-trace-store-off, static-graph-facts-off, static-graph-facts-on,
store-off-accessors, store-off-atom-trace-flip, threshold-construct,
threshold-dict-gate, threshold-number-gate-clause-level,
threshold-number-gate-default, threshold-number-gate-two,
threshold-percent-total, update-mode-default, update-mode-junk-string,
update-mode-override.

## Hygiene

- Oracle byte-clean post-run: `git -C oracle/pyreason status --porcelain` empty;
  HEAD `e1a94af33e1f9d925c9df8284113dd0e14fe8a73` = `oracle/PIN`.
- No installs, no dependency changes anywhere: `git diff -- pyproject.toml
  uv.lock` empty; both engines' environments exactly as found.
- Preflight doctor 10/10 at session start.
- Nothing under `results*` newly tracked; `results-phase3-boundary/` gitignored.
- No security framing anywhere in this session's artifacts.
- The full-corpus run was this packet's explicit job (the one sanctioned
  long run); the fast tier and the 6-case screen were the only other engine
  executions.

## Open follow-ups (carried, post-adjudication material)

- **The adjudication batch itself** — the operator's decision gate between
  Phase 3 and Phase 4; nothing in it blocks the phase verdict.
- Phase-4 openers per AC-5 above: the workload ladder (does not exist yet),
  oracle baselines, then the execution layer against the signed floor.
- Carried case seeds (from the ledger chain, unchanged by this session):
  registrand-behavior packet (L3/L4 arms), edge-rule head-function forms,
  ragged-CSV / interval-nonnumeric / weights-dtype / delta_t cases, `probe_s`
  timing, multi-rule prange characterization, artifact-schema `inputs` echo,
  `interacts-unknown-predicate`, `raise_errors=False` warn-skip arms, O1/O2 as
  future coercion-cluster cases, the pyyaml-version parity tripwire.

## Repro

```
uv run pytest -m "not e2e"                    # 270 passed, 4 deselected
ls harness/cases/*.json | wc -l               # 96
PYTHONHASHSEED=0 uv run python -m harness.run --cases harness/cases \
  --engine-a oracle-env/bin/python --engine-b scripts/rewrite-python \
  --results results-phase3-boundary-repro     # fresh dir for a re-run; ~25-45 min

# re-derive every verdict from the banked artifacts (no engine needed)
uv run python - <<'EOF'
import json
from pathlib import Path
from harness.run import judge_case
for cp in sorted(Path('harness/cases').glob('*.json')):
    case = json.loads(cp.read_text())
    arts = {n: json.loads((Path('results-phase3-boundary')/case['id']/f'{n}.json').read_text())
            for n in ('a1','a2','b1','b2')}
    assert judge_case(case, arts)['status'] == 'pass', case['id']
print('96/96 re-derived pass')
EOF

git -C oracle/pyreason status --porcelain && git -C oracle/pyreason rev-parse HEAD
```
