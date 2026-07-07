<!-- doccode: pyreason-rewrite-docs-reviews-phase3-boundary-sweep -->
# Review — session 15: Phase-3-boundary full-corpus sweep (evidence audit)

Reviewer: Agent 2 (independent of the author; judged only commit `23b3da3`,
the on-disk run artifacts, and the committed corpus/board). Author report
reviewed: [2026-07-07-phase3-boundary-sweep-raw.md](2026-07-07-phase3-boundary-sweep-raw.md).

Per the wall-clock rule the 46-minute sweep was **not rerun**; this is an
evidence audit of the clean-sweep claim against what is actually on disk. No
targeted case reruns were needed either — no artifact contradiction or digest
doubt surfaced anywhere in the audit.

## Verdict

**The clean-sweep claim stands as the phase-boundary verdict-of-record: 94/94
pass, zero divergent, zero irreproducible, zero error.** The decisive check:
the runner's judge (`harness.run.judge_case`) is pure, and the sweep's four
capture artifacts per case are all preserved under `results/<id>/` — so I
re-derived every one of the 94 verdicts from the artifacts through the real
compare layer (`self_proof=True`, per-case comparison policy from the
committed case files). All 94 judged `pass`; zero schema, engine-identity,
env-fingerprint, or digest problems. The verdict is recomputed from evidence,
not taken from the report.

Findings: zero High, zero Medium, two Low (one fixed by this review, one
documented below). Every sharp claim in the author report that I tested —
counts, sums, timestamps, cache deltas, the filename rationale — verified,
several to the second.

## 1. Completeness — the table is the corpus

- `harness/cases/*.json` counts **94** files. The report table's 94 ids,
  extracted and sorted, are **identical** to the corpus filename set — no
  case skipped, no phantom rows, no duplicates
  (`diff` of the two sorted id lists is empty).
- Board consistency (`docs/surface.md`): 52 rows, all `status: cased`, zero
  uncased/pending. I ran the full cross-check, not just the requested sample:
  the union of all 52 `cases:` lines cites exactly **94 distinct ids**, every
  one present in the corpus, and **every corpus case is cited by at least one
  row** — no orphans in either direction. Rows read closely while sampling
  across kinds: graph loading (reverse-digraph/graphml), the reasoning-loop
  settings row, ipl loading, inconsistency handling, closed-world, the
  fact-from-json/csv loaders, rules-from-file.

## 2. Artifact reality — the sweep is auditable from disk

`results/<id>/{a1,a2,b1,b2}.json` + `.log` exist for all 94 cases (the report
says where; confirmed). Checked programmatically across **all 376 capture
artifacts** (94 × 4):

- `env.PYTHONHASHSEED == "0"` in every capture's fingerprint;
- engine executable is `oracle-env/bin/python` (pyreason 3.6.0, python
  3.10.20, darwin) in every capture;
- same-engine repeat digests match and cross-pair probes compare clean —
  that is what the judge re-derivation in the Verdict section proves;
- capture file mtimes span **06:01:27–06:50:06**, consistent with the
  reported sweep window and the 06:55:10 commit.

Fresh-process/ordering sample (14 cases spanning the mandated kinds:
`hello-world`, `save-rule-trace-basic`, `memory-profile-output-on`,
`output-file-name-custom`, `fact-from-csv-malformed`, `rule-text-malformed`
(apply_input raising, banked as `raised`/`type`/`message`),
`annotation-fn-two-arg`, `head-fn-grounding` (registrand annotation/head),
`query-construct`, `threshold-dict-gate`, `interval-ops`, `label-ops`,
`abort-on-inconsistency-default`, `persistent-on` (ordinary reasoning)): in
every one, the four captures' mtimes are strictly increasing (sequential
fresh processes) and the four digest sets are identical. Registrand spans
(127–163 s across four captures) show the all-captures-cold pattern the
report claims; ~5 s spans on construction-only cases match their ~6 s rows.

Run-order claims verified from mtimes: every non-registrand case's last
capture (06:37:56) precedes `parallel-computing-on`'s first (06:38:03), which
precedes the first registrand capture (06:38:43); the seven registrands ran
last, ending 06:50:06.

**Low (documented, no fix needed):** `results/report.json` holds only the
*final* runner invocation's verdict (`head-fn-unregistered-name`) — the
one-case-per-invocation protocol overwrites it 94 times, so there is no
single machine-readable whole-sweep report on disk. The per-case record is
the artifact set plus the author's driver CSV (session scratchpad,
ephemeral). This is inherent to the committed runner's design, the report
does not claim otherwise, and the artifacts alone fully reconstruct the
verdict (proven above) — but a future sweep packet could point the driver at
a persistent per-sweep CSV path to make the record durable in one file.

## 3. Report quality — numbers and attributions

- The 94 wall-clock rows sum to **2783.3 s**, mean 29.61 s, median 26.6 s —
  exactly the report's totals line; 2783 + 251 s screen ≈ the ~50.6 min
  session engine total.
- Row-by-row cross-check of all 94 (verdict, wall-clock) against the author's
  driver CSV (`sweep_results.csv`, final write 06:50:06): **zero
  mismatches**.
- The two "+65 s one-time specialization" attributions verified to the
  second: `interpretation.Interpretation.reason-240.py310.2.nbc` written
  **06:06:07** = `conv-delta-bound`'s a1 finish (repeats then 7 s apart —
  warm); `....3.nbc` written **06:23:52** = `reason-queries-filter`'s a1.
  Only these two `.nbc` files were written in the entire sweep window
  (231 → 233), both plain non-registrand specializations — consistent with
  the session-14 review's mechanism, and no registrand overload survived.
- The §1 "+12 since session 14 (219 → 231)" attribution — hedged by the
  author as inferred from the count — is **confirmed by per-file
  archaeology**: the six repaired kernels' `.1.nbc` files carry mtimes
  05:37:59–05:38:37, inside the session-14 review's post-fix verification
  batch (its `rerun-final` log closes 05:49:04, immediately before the
  session-14 review commits at 05:49:57–05:52:42); the matching six `.nbi`
  complete the 12. Exactly the "review's own post-repair verification runs
  re-populating the six repaired kernels' normal specializations".
- Filename deviation: honest and correct. The packet's target path
  `2026-07-07-phase-boundary-sweep-raw.md` is session 11's committed 53/53
  settings-knob verdict-of-record (commit `02d392e`); taking the `phase3-`
  name avoided clobbering a banked artifact.

**Low (fixed):** the §5 parenthetical dated the registrand captures
"06:34–06:49"; the artifacts say **06:38–06:50** (first registrand capture
artifact 06:38:43, last 06:50:06). Wrong on both ends by a few minutes;
decorative — the surrounding claim (zero surviving registrand additions;
index restores at 06:44:51/06:49:08 writing prior bytes back) verified
exactly. Corrected in the raw report by this review.

## 4. Hygiene, re-verified on the current tree

- Oracle: `git -C oracle/pyreason status --porcelain` empty; HEAD
  `e1a94af33e1f9d925c9df8284113dd0e14fe8a73` — byte-clean at the pin.
- Bundled kernel cache: 233 files; `grep` over every `.nbi`/`.nbc` finds
  **zero** `harness.reference_fns` references.
- Repo: `git status` clean.
- Fast tier (rerun by this review): `uv run pytest -m "not e2e"` →
  **104 passed, 2 deselected**.

## 5. Gates

- `23b3da3` is docs-only: one new `.md`, 249 insertions, nothing else — no
  dependency changes, no oracle writes, no out-of-repo writes.
- No security framing in the report.
- The wall-clock rule was respected by both agents: the author ran the one
  sanctioned full sweep; this review ran no case at all.

## Reproduction of this audit

```
ls harness/cases/*.json | wc -l                                # 94
uv run python - <<'EOF'                                        # re-derive all verdicts
import json
from pathlib import Path
from harness.run import judge_case
for cp in sorted(Path('harness/cases').glob('*.json')):
    case = json.loads(cp.read_text())
    arts = {n: json.loads((Path('results')/case['id']/f'{n}.json').read_text())
            for n in ('a1','a2','b1','b2')}
    assert judge_case(case, arts, self_proof=True)['status'] == 'pass', case['id']
print('94/94 re-derived pass')
EOF
git -C oracle/pyreason status --porcelain && git -C oracle/pyreason rev-parse HEAD
uv run pytest -m "not e2e"
```
