<!-- doccode: pyreason-rewrite-docs-reviews-phase3-boundary-review -->
# Phase-3 breadth boundary sweep — independent review (the phase verdict verified)

- session: 24 · 2026-07-07 · reviewer-fixer packet (no shared context with the author)
- scope reviewed: the sweep artifact of record `results-phase3-boundary/`, the author
  report [2026-07-07-phase3-boundary-author.md](2026-07-07-phase3-boundary-author.md),
  the adjudication batch
  [docs/ledger/phase3-adjudication-batch.md](../ledger/phase3-adjudication-batch.md),
  and the session diff `06d72e9..b9d3251`, graded against the pinned source at
  `e1a94af33e1f` and the boundary packet spec (session-23 NEXT)
- verdict: **the phase claim is CONFIRMED — 96/96 verdicts re-derived independently
  from the on-disk captures through the committed compare layer, the artifact is one
  coherent single invocation, and a 15-case stratified rerun reproduced 15/15 PASS
  with all 60 capture digest maps identical to the artifact of record. The
  adjudication batch is CORRECTED: the review's independent enumeration found five
  recorded observations the assembly sweep dropped, added as B33–B34 + C6–C8
  (commit `44331b9`) — final count 2 DIV + 34 carried candidates + 8 observations
  = 44 sections.** Fast tier **270 passed, 4 deselected** confirmed; board **52/52
  re-verified mechanically**; zero engine defects; **no full second 96-case
  invocation was needed** (stated explicitly in §3).

## 1. The sweep artifact, audited from the captures up

The re-derivation did not trust `report.json`: every verdict was recomputed from
the 384 on-disk capture artifacts through the pure judge (`harness.run.judge_case`)
under each committed case's own comparison policy, with the summary cross-checked
against the recomputation afterwards. Results:

- **Case universe exact.** `harness/cases/*.json` → 96 files, 96 unique ids, every
  id equal to its filename stem; `results-phase3-boundary/` holds exactly those 96
  case dirs plus `report.json` — no extra dir, no missing dir, no duplicate id in
  the report's verdict list (so nothing silently skipped or double-counted).
- **Recomputed verdicts: 96/96 `pass`** — and the report.json statuses match the
  recomputation case-for-case. Verdict order in report.json is the runner's
  filename-sort (where `reason-queries-no-match-edge-heavy.json` sorts before
  `reason-queries-no-match.json`, `-` < `.`), exactly the order the case dirs were
  written in.
- **Engine identities and env fingerprints right in all 384 captures:** a1/a2 =
  `oracle-env/bin/python` (pyreason 3.6.0, python 3.10.20), b1/b2 = the campaign
  engine (pyreason `0.1.0.dev0`, never the oracle path), every capture's
  `env == {'PYTHONHASHSEED': '0'}`, every schema = 1, every artifact's `case_id`
  matching its directory.
- **Same-engine repeats digest-stable in all 96 cases**, checked directly on the
  digest maps (not only through the judge's taxonomy).
- **One coherent invocation, not stitched:** all 821 files in the tree (768
  capture artifacts + logs, the 40 `.outdir` output-file trees the capture layer
  preserves for the ten file-output cases, and report.json) carry mtimes inside
  19:10:52–19:35:48 (span 1496 s — matching the author's first-artifact-to-report
  figure exactly); report.json is the tree's newest write (12 ms after the last
  capture); per-case capture order is a1 ≤ a2 ≤ b1 ≤ b2 in all 96 dirs; case-dir
  write order equals the runner's iteration order; the largest inter-artifact gap
  is 55 s (a registrand-family oracle capture — compile time, not a seam).

## 2. The run incident — ruling verified

The author's killed-first-launch story leaves no residue: the earliest mtime
anywhere under `results-phase3-boundary/` is 19:10:52, well after the 17:58 launch
plus ~49 min would place any first-attempt write — the wholesale delete was real,
and the banked artifact is entirely the second invocation. The
environment-not-engine ruling is evidenced in the report (runner process gone
mid-capture with no exit line, coincident session-host interruption, the partial
artifacts judge-shape-normal) and is the correct taxonomy call: a killed harness
process is never a claim about either engine, per the runner's own docstring. The
warm-numba-cache explanation for the 25.4-min wall-clock is consistent with the
digest evidence — my rerun (also warm-cache) reproduced identical digests, which
is the cache-independence claim demonstrated rather than asserted.

## 3. Independent rerun — fast tier + stratified sample

- **Fast tier:** `uv run pytest -m "not e2e"` → **270 passed, 4 deselected**
  (author's count confirmed; no test change rode the session — the diff
  `06d72e9..b9d3251` touches only the two docs and one gitignore line).
- **Stratified 15-case sample**, chosen by this review to span every family and
  include every packet-required case: spine (`hello-world`, `conv-delta-interp`,
  `reason-again-restart-true`), settings knobs (`fp-version-on`,
  `update-mode-junk-string`, `inconsistency-ipl-override`), loaders
  (`rule-from-csv-malformed`, `ipl-load-basic` — the required ipl case), graph
  boundary (`load-graphml-basic`, `graphml-attr-coercions`), output surface
  (`save-rule-trace-clause-reorder` — the required save-rule-trace case,
  `memory-profile-on`), registrand (`annotation-fn-six-arg` — dispatcher-bearing,
  `head-fn-ungrounded-var`), plus `reason-queries-no-match-edge-heavy` (the two
  named in-review-fix cases both included). Run through the same harness command
  into fresh gitignored `results-phase3-boundary-review/` → **ALL PASS (15)**,
  exit 0.
- **Digest cross-check:** all 15×4 capture digest maps **identical** to the
  boundary artifact's, engine fingerprints equal — deterministic across
  independent invocations, not just same-run repeats.
- **A full second 96-case invocation was NOT needed:** the artifact audit
  surfaced no doubt anywhere (no id gap, no identity/env anomaly, no repeat
  instability, no coherence break), which is the packet's stated bar for
  sanctioning one.

## 4. The adjudication batch — completeness audited, five gaps fixed

Method: an independent three-way enumeration (ledger sessions 4–23 + campaign
log; every `docs/reviews/*.md` including the 2026-07-06 harness and pre-slice
reviews and the `-raw` files; `docs/surface.md` row notes + the three ADRs + both
DIV records), swept for candidate/quirk/observation/adjudication tagging with a
broader vocabulary than the author's grep set, then reconciled item-by-item
against the batch's 39 sections.

**Reconciliation result: all 39 authored sections are real, correctly attributed,
and none misstates evidence** — every Part-B oracle anchor was spot-verified
against the pinned source (filter_ruleset.py:34; pyreason.py:421-432, :1584-1585,
:1622-1624, :1290-1292, :1603; interpretation.py:1918-1931, :2330-2338, :583;
interpretation_fp.py:272-273, :852-854; interval.py:69 vs interval_type.py:63;
label.py:9-10; graphml_parser.py:35-55) and each matches the described behavior.
Part A matches both DIV records' options and proposals exactly. C5's double-count
guard is correct.

**Five recorded observations were missing** — each tagged in the record, none
carried into the batch — fixed by this review in the batch's own format
(commit `44331b9`), numbering B1–B32/C1–C5 untouched:

- **B33 — the store-off accessor assert family** (the sharpest drop: session 5
  tagged it "oracle-bug-candidate" *in the same ledger sentence* as B15's
  atom_trace flip; the batch carried the flip and dropped the family). Covering
  case `store-off-accessors` — its banked probes carry the reused
  "…to save rule trace" message on both trace accessors.
- **B34 — `output_to_file`'s stdout rebind, never restored + handle leak**
  (harness-review F10; board-noted; five covering cases PASS).
- **C6 — pytest-gated first-import package-dir writes + banner** (harness-review
  F9; outside the compared surface; recorded as a documented scope edge).
- **C7 — the thrice-stated no-cache belief refuted + the NumbaTypeSafetyWarning**
  (session 10 + parallel-and-file-output review F2; source-comment-level, no
  rewrite arm).
- **C8 — the dead/aliased knob cluster beyond B12** (reverse_digraph's dead
  engine snapshot and load-path-split read; canonical/persistent alias with the
  write-only `__canonical` field).

**Considered and deliberately not added**, so the line is visible rather than
silent: the slice-6 F2 pandas `OSError` on a missing trace folder (ordinary
third-party raise shape, faithfully reproduced and seam-tested — not a pin
defect); `interval.closed('a',1)`'s TypingError and the `'0.5.5'` float-guard
raise (both explicitly scoped as future-case seeds in sessions 16 and 9, and
carried as such in the author report's follow-ups); the registrar
arity-validation asymmetry (registration-time laxity already in front of the
operator via B2 + C1-ii/iii); `reason(queries=…)`'s permanent narrowing of
`get_rules`, the resume/reset lifecycle details (second-again re-consumption,
reset_rules clearing registries, the get_interpretation guard asymmetry), and the
loader message-shape details (first-char-only comments, unquoted-comma wholesale
tokenizer failure, doubled item prefixes) — all board-carried characterization
banked as compared case data, where any drift fails loudly; and the
harness-representation quirks (int-fill vs float bounds, empty-frame
normalization, CPython-version float() message), which are compare-layer
contracts, not pin behaviors. None of these is tagged as a carried candidate
anywhere in the record.

**Author-report accuracy notes (no fix needed):** the corpus arithmetic sentence
("session 15's corpus was 94 … and the four `ipl-*` cases replaced nothing")
reads ambiguously as if the ipl cases were new; they were committed in phase 2
(commit `0527526`) and were inside the 94 — the arithmetic is 94 + 2 = 96 and is
correct. The report's "sorted" pass-list claim means filename-sort (see §1).
The batch-count references in the author report (39 sections) were accurate at
its commit and are superseded by the corrected count here.

## 5. Board + hygiene

- **Board 52/52 recomputed mechanically, not trusted:** 52 rows, all
  `equivalent`; every row's full case list ⊆ this review's *recomputed* pass set
  (not report.json's); every listed case id backed by a committed case file; all
  96 committed cases appear on some row; the inventory gate is green inside the
  fast tier.
- Oracle byte-clean: `git -C oracle/pyreason status --porcelain` empty, HEAD
  `e1a94af33e1f9d925c9df8284113dd0e14fe8a73` = `oracle/PIN`.
- No installs, no dependency changes: `git diff HEAD -- pyproject.toml uv.lock`
  empty across the session and this review.
- `git ls-files 'results*'` → 0 tracked files; `results-phase3-boundary/`
  untouched by this review (the rerun landed in its own gitignored dir, added to
  `.gitignore` with this report).
- No security framing in any session artifact (scanned).
- Engine executions this review: the fast tier, the 15-case sample run, and the
  artifact re-derivations (pure, no engine). No full e2e sweep, per the packet.

## 6. Verdict

**Phase 3's claim stands exactly as the author stated it, and now stands on two
independent derivations of the same artifact plus a cross-invocation digest
identity check: the rewrite's reference core is equivalent to the pinned oracle
(e1a94af3, v3.6.0) over the entire committed 96-case corpus in one harness
invocation, with claims co-extensive with that artifact and two queued
divergences.** The one defect found this session was in the decision document,
not the engine: the adjudication batch had silently absorbed five recorded
observations, the exact failure mode a completeness audit exists to catch; they
are restored with provenance and the operator now adjudicates from a 44-section
batch (2 DIV records with proposals, 34 carried candidates, 8 recorded
observations). The loop stops after this session banks, per the session-22
operator instruction.

## Repro

```
# fast tier
uv run pytest -m "not e2e"                    # 270 passed, 4 deselected

# re-derive all 96 verdicts + identity/env/coherence audit (no engine needed)
uv run python - <<'EOF'
import json, sys; sys.path.insert(0, ".")
from pathlib import Path
from harness.run import judge_case
cases = {p.stem: json.loads(p.read_text()) for p in Path('harness/cases').glob('*.json')}
assert len(cases) == 96
for cid, case in sorted(cases.items()):
    arts = {n: json.loads((Path('results-phase3-boundary')/cid/f'{n}.json').read_text())
            for n in ('a1','a2','b1','b2')}
    assert all(a['env'] == {'PYTHONHASHSEED': '0'} for a in arts.values()), cid
    assert judge_case(case, arts)['status'] == 'pass', cid
print('96/96 re-derived pass')
EOF

# the stratified 15-case rerun (cases listed in §3; ~12 min warm-cache)
mkdir -p /tmp/boundary-review-cases && for c in hello-world conv-delta-interp \
  reason-again-restart-true fp-version-on update-mode-junk-string \
  inconsistency-ipl-override rule-from-csv-malformed ipl-load-basic \
  load-graphml-basic graphml-attr-coercions save-rule-trace-clause-reorder \
  memory-profile-on annotation-fn-six-arg head-fn-ungrounded-var \
  reason-queries-no-match-edge-heavy; do \
  cp harness/cases/$c.json /tmp/boundary-review-cases/; done
PYTHONHASHSEED=0 uv run python -m harness.run --cases /tmp/boundary-review-cases \
  --engine-a oracle-env/bin/python --engine-b scripts/rewrite-python \
  --results results-phase3-boundary-review
# then: per case+capture, assert digests == results-phase3-boundary's (all 60 equal)

git -C oracle/pyreason status --porcelain && git -C oracle/pyreason rev-parse HEAD
```
