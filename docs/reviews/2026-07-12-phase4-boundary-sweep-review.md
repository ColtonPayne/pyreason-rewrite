<!-- doccode: pyreason-rewrite-docs-reviews-phase4-boundary-sweep-review -->
# Phase-4 boundary sweep — independent review (the phase-boundary verdict verified)

- session: 32 · 2026-07-12 · reviewer-fixer packet (no shared context with the author)
- scope reviewed: the sweep artifact of record `results-phase4-boundary/`, the author
  report [2026-07-12-phase4-boundary-sweep-author.md](2026-07-12-phase4-boundary-sweep-author.md),
  commit `a2a20e7` (report-only — verified: one file, 216 insertions, no engine/harness/test
  change), graded against the durable-runner design (`harness/run.py`, `harness/capture.py`),
  the ledger context ([session-31](../ledger/session-31.md)), and the packet spec
- verdict: **APPROVED — the boundary claim is CONFIRMED as stated: 116/116 verdicts
  re-derived independently from the on-disk artifacts through the pure judge, the
  artifact is one coherent single invocation (`resumed: false` verified structurally
  AND against every file's mtime and birthtime), and a 7-case stratified live rerun
  reproduced 7/7 PASS with all 28 capture digest maps identical to the artifact of
  record.** Zero fixes needed — the first boundary review in the campaign record with
  an empty fix list. Fast tier **321 passed, 6 deselected** confirmed; oracle
  byte-clean; **no DIV record opened** (next free stays DIV-0004); no full second
  116-case invocation was needed (nothing in the audit raised doubt anywhere).

## 1. The sweep artifact, audited from the captures up

The re-derivation did not trust `report.json` and did not reuse the author's snippet:
this review's own script judged every case through `harness.run.judge_case` under each
committed case's own comparison policy, then cross-checked the runner's report against
the recomputation. It also verified the full marker integrity chain the session-31
durability design promises (`case.done.json` semantics per `harness/run.py`'s
docstring and `completed_marker`). Results:

- **Case universe exact.** `harness/cases/*.json` → 116 files, 116 unique ids, every
  id equal to its filename stem; `results-phase4-boundary/` holds exactly those 116
  case dirs plus `report.json` (no extra dir, no missing dir, no other top-level
  file); the report's verdict list and the resume block's captured list each carry
  116 unique ids.
- **Recomputed verdicts: 116/116 `pass`** — taxonomy tally `{pass: 116}`, zero
  divergent / irreproducible / error — and `report.json`'s statuses match the
  recomputation case-for-case.
- **Marker integrity chain intact in all 116 markers:** schema 1; invocation
  identity **uniform** across all markers — exactly one identity tuple
  `(oracle-env/bin/python, scripts/rewrite-python, hashseed "0")`; every marker's
  `case_digest` equals the sha256 of the committed case file; every one of the 464
  artifact files hashes to its marker's recorded digest (no truncated or
  post-hoc-edited artifact); all 464 recorded returncodes are 0.
- **Artifact self-description right in all 464 captures:** schema 1; every
  `env == {"PYTHONHASHSEED": "0"}`; a1/a2 engine identity uniformly
  (`…/oracle-env/bin/python`, pyreason 3.6.0, python 3.10.20 — the pin), b1/b2
  uniformly the campaign venv (pyreason 0.1.0.dev0, python 3.13.11, never the
  oracle path); every artifact's embedded `case` record **equals the committed case
  file byte-for-parse** (the session-31 self-description contract, held).
- **Resume honesty block coherent:** `resumed: false`, `prior_complete: []`,
  `captured_this_invocation` = all 116 ids exactly once. (List order is the
  runner's filename-sort, where `reason-queries-no-match-edge-heavy.json` sorts
  before `reason-queries-no-match.json` — `-` < `.` — same note as the phase-3
  review; the author's "sorted" pass list is id-sort, both orderings carry the same
  set.)

## 2. Single-clean-invocation claim, attacked

- **Window coherence over ALL files, not just JSON:** every one of the **1097**
  files under `results-phase4-boundary/` (464 artifacts + 464 logs + 116 markers +
  `report.json` + the 52 engine-written `.outdir` csv/txt observation files) carries
  an mtime inside 11:41:58.6Z–12:20:20.2Z; `report.json` is the tree's newest write;
  launch 11:41:52Z → report write = **2308 s**, matching the author's wall-clock
  figure exactly; earliest artifact +6.6 s after launch (author said ~+7 s).
- **The killed-first-launch story leaves no residue, proven on birthtimes too:**
  on this filesystem file *creation* times are recordable, and the earliest
  birthtime anywhere in the tree is 11:41:58.6Z — a case dir carried over from the
  11:28:18Z first attempt would show ~11:28 birthtimes. The wholesale delete was
  real; the banked artifact is entirely the second invocation. The
  environment-not-engine ruling is the correct taxonomy call per the runner's own
  docstring (a killed harness process is never a claim about either engine), with
  the phase-3 boundary incident as recorded precedent.
- **Capture ordering physical:** a1 ≤ a2 ≤ b1 ≤ b2 mtimes in all 116 case dirs;
  every marker written after its last capture; marker `completed_at` order equals
  the runner's filename-sort iteration order — one process walking the corpus once,
  not a stitched or reordered tree.
- **Artifact count arithmetic:** 464 + 116 = 580 case-dir JSON files, the author's
  parenthetical "(580 JSON artifacts)"; with `report.json` the dir holds 581 JSON
  files total. Accuracy note only, no fix: the report lists `report.json` adjacent
  to the 580 figure and the natural reading (case-dir artifacts) is correct.

## 3. Independent rerun — fast tier + stratified live sample

- **Fast tier:** `uv run pytest -m "not e2e"` → **321 passed, 6 deselected**
  (author's count confirmed, 0.33 s; commit `a2a20e7` touches no test, so identity
  with session 31's count is expected and observed).
- **Stratified 7-case live sample**, chosen by this review: `hello-world` (spine),
  `parallel-computing-multirule` (the long/parallel-computing case, session 31's
  newest), `accessors-lifecycle` (accessor-heavy; also the case the killed first
  launch died inside), `save-rule-trace-clause-reorder` (trace-heavy file output),
  `memory-profile-output-on` (canonicalization-bearing: peak-MB + timestamp),
  `rule-json-weights-dtypes` (loader family), `threshold-dict-gate` (threshold
  surface). Run end-to-end oracle-vs-rewrite through the same harness command into
  a scratch results dir (outside the repo) → **ALL PASS (7 case(s))**, exit 0,
  `resumed: false`.
- **Cross-invocation digest identity: 28/28.** Every sample capture's `digests`
  map, `probes` map, engine fingerprint, and env fingerprint is **identical** to
  the banked boundary artifact's — the determinism the harness claims
  (canonicalized timestamps/peak-MB, `PYTHONHASHSEED=0`, fresh processes)
  demonstrated across independent invocations hours apart, not just same-run
  repeats.
- **No full second 116-case invocation was needed:** the artifact audit surfaced
  no id gap, no identity or env anomaly, no digest instability, no coherence
  break — the packet's stated bar for sanctioning one was never approached.

## 4. Report accuracy + context

- **Corpus history checks out:** session 24's ledger banked 96/96; the committed
  corpus is 116 now; the author's family attribution for the +20 matches the
  session 26–31 record (including `parallel-computing-multirule`, corpus 116, in
  session 31's ledger).
- **Sequencing note (context, not a defect):** session-31's NEXT ordered the
  boundary sweep *after* the execution-layer commitment (gate 2 after gate 1);
  session 32 ran it while the commitment is still pending. The author handles this
  correctly and prominently — the verdict is scoped to "the tree as it stands"
  (the Option-B state), with the explicit condition that an engine-changing
  decision (Option A or C) forces a fresh sweep. That contingent framing matches
  the ledger's own description of the sweep as the equivalence half of the
  decision evidence for the current tree. Nothing to fix; the operator should read
  the verdict with that scope.
- **Spot-fix loop empty, verified:** commit `a2a20e7` is the session's only
  commit and adds only the author report; `git status --porcelain` clean;
  `git diff HEAD -- pyproject.toml uv.lock` empty (no installs — last touched
  sessions ago); DIV records still exactly three, all adjudicated, next free
  DIV-0004.

## 5. Hygiene

- Oracle byte-clean: `git -C oracle/pyreason status --porcelain` empty, HEAD
  `e1a94af33e1f9d925c9df8284113dd0e14fe8a73` = `oracle/PIN`.
- `git ls-files 'results*'` → 0 tracked files; `results-phase4-boundary/` covered
  by the committed `results*/` glob and untouched by this review (read-only audit;
  the live sample ran into a scratch directory outside the repo).
- Engine-engineering vocabulary throughout the author report (scanned) and this one.
- Engine executions this review: the fast tier, the 7-case sample run, and the
  artifact re-derivations (pure, no engine). No full corpus sweep, per the packet.

## 6. Verdict

**Approved. The phase-boundary claim stands exactly as the author stated it, and now
stands on two independent derivations of the same artifact plus a cross-invocation
digest identity check: the rewrite — the pure-Python core with the session-28
optimizations, the Option-B state — is equivalent to the pinned oracle (e1a94af3,
v3.6.0) over the entire committed 116-case corpus, in one clean harness invocation,
with claims co-extensive with that artifact, three adjudicated divergences, and the
scope contingency (an engine-changing execution-layer decision re-runs the sweep)
correctly attached.** No fixes were needed: the report's every checkable number —
case count, artifact count, wall-clock, fast-tier count, resume block, engine
identities, incident window — reproduced under independent derivation. The
campaign remains blocked on the operator's execution-layer commitment; this sweep
is the equivalence half of that decision's evidence for the current tree.

## Repro

```
# fast tier
uv run pytest -m "not e2e"                    # 321 passed, 6 deselected

# re-derive all 116 verdicts + the marker integrity chain (no engine needed)
PYTHONHASHSEED=0 PYTHONPATH=. uv run python - <<'EOF'
import hashlib, json
from collections import Counter
from pathlib import Path
from harness.run import judge_case, CAPTURE_NAMES
tally = Counter(); idents = set()
for p in sorted(Path('harness/cases').glob('*.json')):
    b = p.read_bytes(); case = json.loads(b)
    d = Path('results-phase4-boundary')/case['id']
    m = json.loads((d/'case.done.json').read_text())
    assert m['case_digest'] == hashlib.sha256(b).hexdigest(), case['id']
    idents.add((m['engine_a'], m['engine_b'], m['hashseed']))
    arts = {}
    for n in CAPTURE_NAMES:
        raw = (d/f'{n}.json').read_bytes()
        assert hashlib.sha256(raw).hexdigest() == m['artifacts'][n], (case['id'], n)
        assert m['returncodes'][n] == 0, (case['id'], n)
        arts[n] = json.loads(raw)
        assert arts[n]['case'] == case and arts[n]['env'] == {'PYTHONHASHSEED': '0'}
    tally[judge_case(case, arts)['status']] += 1
assert idents == {('oracle-env/bin/python', 'scripts/rewrite-python', '0')}
print(dict(tally))                            # {'pass': 116}
EOF

# the stratified 7-case live rerun (~11 min warm-cache; scratch dir, not the repo)
mkdir -p /tmp/boundary4-review-cases && for c in hello-world \
  parallel-computing-multirule accessors-lifecycle save-rule-trace-clause-reorder \
  memory-profile-output-on rule-json-weights-dtypes threshold-dict-gate; do \
  cp harness/cases/$c.json /tmp/boundary4-review-cases/; done
PYTHONHASHSEED=0 uv run python -m harness.run --cases /tmp/boundary4-review-cases \
  --engine-a oracle-env/bin/python --engine-b scripts/rewrite-python \
  --results /tmp/boundary4-review-results     # ALL PASS (7 case(s))
# then: per case+capture, assert digests/probes/engine/env == the banked
# results-phase4-boundary artifacts' (28/28 identical)

git -C oracle/pyreason status --porcelain && git -C oracle/pyreason rev-parse HEAD
```
