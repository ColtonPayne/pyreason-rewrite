<!-- doccode: pyreason-rewrite-docs-reviews-2026-07-07-phase3-slice8-review -->
# Phase 3, slice 8 — the IPL file family (independent review)

- session: 23 · 2026-07-07 · reviewer-fixer packet (no shared context with the author)
- scope reviewed: the full diff `b8b020b..fc01d63` as a coherent whole, graded
  against the pinned source at `e1a94af33e1f` and the slice-8 packet spec
  (session-22 NEXT)
- verdict: **the committed loader, cases, and seam tests are correct as landed
  — every author claim reproduced independently — but a review probe exposed
  one arm of the pinned loader the plain-list transcription cannot carry
  (non-string pair entries), filed by this review as DIV-0002; the slice
  passes with the divergence queued, not absorbed.** Author's 4/4 reproduced
  (4/4 ALL PASS into `results-phase3-slice8-review/`, all 16 capture digests
  identical to the author's run); fast tier **269 confirmed** on the author's
  tree, **270** after the review's provisional seam test; **5/5 reviewer
  discriminating probes ran cross-engine — 4 pass, 1 exposed the DIV-0002
  divergence**; board **52/52 confirmed mechanically** (both flips honest —
  the `fn:save_rule_trace` flip verified case-by-case against the slice-6
  reports; no missed or premature flip under the board's operating
  convention, with the DIV-0001/DIV-0002 status treatment argued explicitly
  below).

## Findings, by severity

**F1 (divergence, queued as DIV-0002 — not fixable to pinned behavior) — the
pin raises on non-string IPL entries; the rewrite accepts them.** The pinned
`parse_ipl` constructs plain `Label(labels[0])` without complaint (the
pure-Python constructor checks nothing), but its append lands in a numba
`typed.List(Tuple((label_type, label_type)))`, and `unbox_label`
(label_type.py:86-94) unboxes each Label's `_value` through `types.string` —
an int read as a unicode struct raises `builtins.ValueError` whose message is
**address-derived garbage**: probe `rv-ipl-nonstring-pair`
(`ipl:\n  - [1, 2]\n`) run twice through the harness gave 4 fresh pin
processes and 4 distinct messages (`character U+1552710 / U+51c2710 /
U+341e710 / U+5c6e710 is not in range [U+0000; U+10ffff]`), so the harness
scores the input **`irreproducible (engine-a)`** — the pin cannot reproduce
its own observable, and no exact-compare case can ever bank the arm. The
rewrite's plain-list append accepts the same file (`{"raised": false}`).
This is a real behavioral difference on a reachable input, but "fix to
pinned behavior" is impossible by construction (any deterministic message
differs from the pin's unstable one), and the choice between a guarded raise
with an invented message and a documented acceptance is a consequential
fork — so per AC-6 it lands as **`docs/divergences/DIV-0002.md`**
(queued-for-operator, proposed resolution: the guarded raise, following the
TypedRuleList/TypedComponentDict container-semantics precedent), with the
pin-side e2e reproducer `tests/test_div_0002_reproducer.py` (run once here:
1 passed) and the fast-tier provisional seam test
`test_ipl_yaml_nonstring_entries_load_provisionally` documenting the
rewrite's current arm. Nothing in the committed slice is touched: every
committed fixture and case carries string entries, and all 4 committed
cases pass unchanged.

No other defects. The committed loader is a faithful transcription: safe_load
is the single YAML entry point (no other loader class reachable in
`_loaders.py`); the raise order matches the pin exactly (open → safe_load →
`['ipl']` subscript → per-pair `[1]`); the null-'ipl:' arm reduces to an
empty list (not None) so a null file still overwrites; and the rebind is
parse-first (any raise leaves the prior IPL untouched), which the pin gets
from the `parse_ipl`-then-assign split and the rewrite gets from building
the list before `state.ipl = ipl`. The rewrite's plain `Label` matches the
pin's pure-Python class byte-for-byte on the consumed surface. The compare
layer is untouched by the slice (the diff reaches only `src/pyreason/`,
`tests/`, `docs/`, `.gitignore`) — no loosened policy, no canonicalization.

## Seam tests read line-by-line

All four `proves:` docstrings match their assertions. The replace-not-merge
test seeds a different pair (`sick/healthy`) before loading, so the
assertion genuinely discriminates overwrite from merge; the null test
asserts `== []` (not falsy), pinning empty-list-not-None; the malformed test
asserts all four exception types with exact messages where deterministic
(KeyError `"'ipl'"`, IndexError `'list index out of range'`) and re-asserts
the prior IPL after every raise — the parse-before-rebind property, tested
rather than claimed; the facade test monkeypatches a fresh EngineState into
the module global and drives the public `pyreason.
load_inconsistent_predicate_list`, which is the exact seam
`harness/capture.py` applies (`APPLY_FILE_OPS`). All four read real
committed fixtures — the same files the equivalence cases load.

## The two board flips — both honest, verified mechanically

**`fn:load_inconsistent_predicate_list`**: forced by this slice — all 4
covering cases pass in `results-phase3-slice8/` (author) and in my
independent `results-phase3-slice8-review/` rerun.

**`fn:save_rule_trace`**: the mechanical rule is *full case list ⊆ the
oracle-vs-rewrite passed set across banked results dirs*. The row's list is
save-rule-trace-basic/-atom-trace-off/-store-off/-clause-reorder +
ipl-atom-trace-off-trace. The first four passed in slice 6 (re-verified in
both `results-phase3-slice6/report.json` and the slice-6 review's rerun
dir); the fifth — the row's last un-run covering case, exactly what the
slice-7 review predicted as the gated remainder — landed this slice. The
`5de8c72` diff changes only the two status lines, no case-list edit rode
along, so the flip is the rule firing on new evidence, not a redefinition.
Honest.

**Whole-board arithmetic recomputed, not trusted**: a script over
`docs/surface.md` × the union of `status: pass` verdicts in every banked
`results*/report.json` — 52 rows, all `equivalent`, every row's full case
list inside the passed union, every case id backed by a real
`harness/cases/<id>.json`, zero non-pass verdicts anywhere. **52/52
confirmed.**

**The DIV-0001 (and now DIV-0002) status question, argued explicitly**: both
divergences sit on rows counted `equivalent`. That follows the board's
operating convention, set when the slice-6 review filed DIV-0001 and upheld
by the slice-7 review's mechanical check: `equivalent` tracks the committed
case list (all cases pass), while divergences on inputs **no case can bank**
(DIV-0001: the pinned process dies before an artifact exists; DIV-0002: the
pinned message is same-engine unstable) live in the row notes + the DIV
record + the adjudication batch — `divergent-queued` is the status for a
*committed case* diverging, which none does. Flipping type:Query or this
row now would retroactively contradict two banked ledger fractions (48/52,
50/52) counted under the same convention. Both DIVs are visible: row notes
name them in bold, and the operator's end-of-Phase-3 batch carries them.

## Discriminating probes (overfitting hunt) — 5 probe cases, 8 new inputs

All ran cross-engine through the harness (PYTHONHASHSEED=0, oracle-env vs
scripts/rewrite-python, 4 fresh-process captures each; probe cases in the
session scratchpad, probe fixtures review-local under `harness/fixtures/`
and removed after — contents inlined in Repro below).

| probe | seam it pins beyond the 4 cases | verdict |
|---|---|---|
| rv-ipl-shape-arms (4 arms) | four YAML shapes the committed malformed case never reaches, each a distinct plain-Python raise before any append: empty file → TypeError `'NoneType' object is not subscriptable`; top-level list document → TypeError list-indices; scalar `ipl: 5` → TypeError `'int' object is not iterable`; string `ipl: ab` → IndexError `'string index out of range'` (the string twin of the committed short-pair arm's *list* message) | pass |
| rv-ipl-empty-list-overwrite | the board's named-unobserved bound-ipl-empty-list class: explicit `ipl: []` passes the `is not None` guard (different branch from null), iterates zero times, and still overwrites a prior add — zero complement rows | pass |
| rv-ipl-inconsistency-check-off | the loaded IPL × `settings.inconsistency_check=False` interaction: complement-row emission is NOT gated by the setting — trace identical to ipl-load-basic in both engines | pass |
| rv-ipl-dup-pairs | a duplicated [popular, unpopular] pair: parse_ipl appends both without dedup and both engines double the complement rows (12 vs basic's 6) — row multiplicity pinned | pass |
| rv-ipl-nonstring-pair | non-string pair entries (`[[1, 2]]`) — the typed-list unbox arm, the one place the pinned container enforces what parse_ipl doesn't | **exposed F1 → DIV-0002** (pin: ValueError, address-derived message, same-engine unstable; rewrite: accepts) |

## Independent rerun

- Fast tier: `uv run pytest -m "not e2e"` → **269 passed** on the author's
  tree (claim confirmed), **270 passed** after the review's provisional seam
  test (4 deselected: 3 prior e2e + the DIV-0002 reproducer). Inventory gate
  green after the board-note edit.
- 4-case rerun: fresh `results-phase3-slice8-review/` (gitignored by the
  author's `5de8c72`) → **ALL PASS (4)**, exit 0, all 16 capture digests
  identical to the author's `results-phase3-slice8/` — deterministic across
  operators, not just across same-engine repeats.
- DIV-0002 reproducer: `uv run pytest tests/test_div_0002_reproducer.py -m
  e2e` → 1 passed (the only e2e run; no full e2e sweep, per the wall-clock
  rule).
- The author's pyyaml observation confirmed as stated: both envs at 6.0.3,
  neither touched (`git diff b8b020b..HEAD -- pyproject.toml uv.lock` empty),
  and the ParserError message parity does rest on that version identity —
  the fixture-level exact compare is the loud tripwire if an env rebuild
  ever moves it.

## Hygiene

- No installs, no dependency changes anywhere; `pyproject.toml`/`uv.lock`
  untouched across the slice and the review.
- Oracle tree byte-clean: `git -C oracle/pyreason status --porcelain` empty,
  HEAD = `e1a94af33e1f…` = oracle/PIN.
- `git ls-files 'results*'` → 0 tracked files; both slice-8 results dirs
  gitignored by the author's `5de8c72`; probe results and probe cases stayed
  in the session scratchpad; the review-local probe fixtures removed from
  `harness/fixtures/` before finish (tree clean).
- No security framing in the session diff (scanned) — malformed YAML is
  input validation, full stop.
- Full corpus sweep not run (fast tier + the 4 packet cases + 6 probe-case
  harness runs + 1 e2e reproducer only) — the one-invocation sweep is the
  boundary-sweep session's job.

## Verdict

**The IPL loader is a faithful transcription of the pinned parse_ipl —
raise order, null semantics, and the parse-first wholesale rebind all
reproduce at the public-API boundary — its four cases bank exactly what
they claim, and both board flips are the mechanical rule firing on real
evidence: 52/52 stands.** The review's probes found the one arm the
transcription cannot carry — the pinned typed-container's non-string
enforcement, whose raise message the pin itself cannot reproduce — and
filed it as DIV-0002 (queued, reproducer-backed, provisionally documented
in a fast-tier seam test) rather than absorbing or paper-fixing it. Post
review: fast tier 270, board 52/52, adjudication batch = DIV-0001 +
DIV-0002 + the carried oracle-bug-candidate observations, all prepared for
the operator at the Phase-3 boundary. The boundary sweep is unblocked.

## Repro

```
# fast tier (270 post-review)
uv run pytest -m "not e2e"

# the 4-case rerun
mkdir -p /tmp/slice8-review-cases && for c in ipl-load-basic \
  ipl-load-malformed ipl-load-null-overwrite ipl-atom-trace-off-trace; do \
  cp harness/cases/$c.json /tmp/slice8-review-cases/; done
PYTHONHASHSEED=0 uv run python -m harness.run --cases /tmp/slice8-review-cases \
  --engine-a oracle-env/bin/python --engine-b scripts/rewrite-python \
  --results results-phase3-slice8-review-repro

# DIV-0002, both halves
uv run pytest tests/test_div_0002_reproducer.py -m e2e     # pin raises, unstable message
uv run pytest tests/test_rewrite_state_loaders.py -k nonstring   # rewrite accepts (provisional)

# probe fixtures (review-local; recreate to rerun the probes)
#   rv-ipl-nonstring.yaml:     "ipl:\n  - [1, 2]\n"
#   rv-ipl-empty.yaml:         ""            (zero bytes)
#   rv-ipl-toplevel-list.yaml: "- [popular, unpopular]\n"
#   rv-ipl-scalar-value.yaml:  "ipl: 5\n"
#   rv-ipl-string-value.yaml:  "ipl: ab\n"
#   rv-ipl-empty-list.yaml:    "ipl: []\n"
#   rv-ipl-dup.yaml:           "ipl:\n  - [popular, unpopular]\n  - [popular, unpopular]\n"
# probe cases: apply_input probes over the malformed fixtures (shape of
# ipl-load-malformed); reason-carrying clones of ipl-load-basic /
# ipl-load-null-overwrite for dup / inconsistency-check-off / empty-list
```
