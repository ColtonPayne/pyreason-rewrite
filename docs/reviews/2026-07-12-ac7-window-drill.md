<!-- doccode: pyreason-rewrite-docs-reviews-ac7-window-drill -->
# AC-7 window-close pickup drill — session 34 (2026-07-12)

The charter's AC-7.4 drill, window-close edition: a cold Opus subagent
(explicit `model: 'opus'`, no shared context) was given only the committed
repo and asked to (1) state the campaign's condition from committed state
alone, (2) execute the ledger's NEXT far enough to prove the resume path,
and (3) report every point where the committed state misled or blocked it.

## Drill outcome — resume path PROVEN

The cold agent's reading matched the intended state on every substantive
point: the campaign's proof mechanisms (oracle-differential harness, the
surface board, the divergence discipline), the decided/closed/open split
(Option B signed in ADR 0004; AC-3 at 52/52 `equivalent` with the
session-32 116/116 sweep as verdict-of-record; AC-5 5/5; DIV-0001..3 all
adjudicated; the lab-box and publication threads gated), and the resume
prompt. What it executed, all green from committed state alone:

| step | result |
|---|---|
| preflight doctor | PASS 10/10 |
| oracle pin | clean at `e1a94af3` |
| fast tier | 330 passed / 6 deselected |
| e2e collection | 6 tests correctly deselected from the fast gate |
| oracle live gate (`tools/oracle_smoke.py`) | GATE PASSED (import 1.45 s, reason 3.24 s) |
| harness spine (`tests/test_resume_e2e.py`) | 1 passed (34.6 s) — two-engine capture, compare, resume-determinism |

## Gaps found (defects in the committed state) and their disposition

1. **README `Status` flatly stale** — still said "campaign not yet
   started" after 33 sessions and a signed execution layer. The front door
   contradicted the ledger. **Fixed** (this session's commit): the Status
   section now defers to the newest ledger session as the authoritative
   state and carries a dated snapshot.
2. **`tools/oracle_smoke.py` rebuild recipe contradicted the env of
   record** — docstring said `--python 3.12`; the actual oracle-env (and
   every banked baseline) is Python 3.10.20. A cold rebuild from the
   docstring would produce a different interpreter than the banked
   numbers'. **Fixed**: docstring now states 3.10 with the ADR-0004
   pointer.
3. **`uv run pytest -m e2e` had a hidden 20+ minute runtime** — the
   README's acceptance one-liner gave no warning that the oracle-vs-oracle
   corpus test reruns the full corpus through the oracle twice; the drill
   agent initially had to rule out a stall. **Fixed**: the README
   quick-start now states the runtime and that a long quiet stretch is
   normal.
4. **`docs/perf/pokec-scaling-report.md` carries a concurrent uncommitted
   operator-side edit** (known; session-33 Friction). **Not fixed here** —
   the file belongs to the operator's in-flight lab workstream; the ≤0.7%
   print-precision nit folds into its next touch.

## Re-drill

Per AC-7.4, gaps are fixed and re-drilled before the campaign proceeds.

## Re-drill result (same day, after commit 652863b)

**RE-DRILL PASSED — "no substantive gaps."** A second cold Opus agent,
starting from the front door, reported: the README's account now matches
the ledger exactly (52/52 rows, the 116/116 sweep, ADR 0004, AC-5 5/5);
the oracle-env rebuild recipe matches the environment actually present
(Python 3.10.20); the e2e runtime warning was seen in advance and the
agent chose the fast oracle gate deliberately. Its own runs: preflight
10/10, fast tier 330 passed / 6 deselected, oracle live gate PASSED
(import 1.40 s, reason 3.06 s). It independently recognized the one dirty
working-tree file as the ledger-documented operator-side edit and left it
alone. Its two observations for the record (the prior drill's self-repair
being visible at HEAD; a stale harness-side git snapshot) are properties
of the drill mechanism and the session harness, not of the committed
state.
