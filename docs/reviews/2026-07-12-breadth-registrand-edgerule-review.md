<!-- doccode: pyreason-rewrite-docs-reviews-2026-07-12-breadth-registrand-edgerule-review -->
# Session 29 — independent review: the registrand-behavior packet, the edge-rule forms, and DIV-0003

- session: 29 · date: 2026-07-12 · independent reviewer-fixer (no shared
  context with the author)
- scope: commits `4914cff` (engine + reference fns + seam tests), `60350c6`
  (DIV-0003 + pin reproducer), `0efb82b` (cases + board), `6c38c56` (author
  report)
- verdict: **approved with fixes** — one genuine engine-behavior finding
  (the annotate return coercion modeled the pinned unbox as len()-based
  where the pin is tuple-only; fixed to pinned behavior, screened 2/2 fresh
  pin processes per arm), one factual correction to the author report's
  cache-audit characterization (recorded here, not a code defect), and one
  line-citation off-by-one (fixed). Everything else verified as claimed.
- fix commit: `2654a1e`; review evidence:
  fast tier **297 passed / 5 deselected** post-fix; review rerun of the 6
  packet cases + `hello-world` + `annotation-fn-two-arg` oracle-vs-rewrite
  in one invocation: **8/8 PASS** with `hello-world` and
  `annotation-fn-two-arg` probe digests byte-identical to their banked
  artifacts; DIV-0003 pin-side reproducer **1 passed**.

## 1. Engine raise shapes vs the pinned source — verified, one fixed

Each claimed pin shape was re-derived from the pinned source and then
independently screened by fresh oracle-env processes (2 per arm,
njit-wrapped registrands as `resolve()` produces oracle-side, kernel-cache
snapshot/restore around every batch — the cache came back to its 237-file
state each time).

| arm | pinned source derivation | review pin screen (2 fresh processes) | rewrite |
|---|---|---|---|
| annotation fn returns 3-tuple | objmode exit unboxes to `Tuple((float64, float64))` (interpretation.py:1918); numba `unbox_tuple` (core/boxing.py:571) emits `size mismatch for tuple, expected %d element(s) but got %%zd` | `builtins.ValueError: size mismatch for tuple, expected 2 element(s) but got 3` — byte-stable | same — CONFIRMED |
| annotation fn returns an Interval | `unbox_tuple` sizes/walks with `PyTuple_Size`/`PyTuple_GetItem` (tuple-only); the failed element fetch surfaces CPython's bad-argument TypeError | `builtins.TypeError: bad argument type for built-in operation` — byte-stable | same — CONFIRMED |
| head fn returns bare str | `_call_head_function` objmode output `types.ListType(types.unicode_type)` (interpretation.py:2332); typedlist unbox (numba typed/typedlist.py:530) emits `can't unbox a %S as a %S` | `builtins.TypeError: can't unbox a <class 'str'> as a <class 'numba.typed.typedlist.List'>` — byte-stable | same — CONFIRMED (the f-string generalizes the same format numba uses) |

**Finding F1 (fixed): the coercion's non-tuple-sequence arm was wrong.**
The author's `_coerce_annotation_pair` modeled the pinned unbox with
`len()`: anything with a length got the size check, so a **size-2 list**
passed through (the rewrite completed and banked `combo(A)=[0.25,0.75]`)
and a **size-3 list** raised the size-mismatch ValueError. The pinned
unbox is tuple-only — `PyTuple_GetItem` never sizes a non-tuple — so the
pin raises `TypeError('bad argument type for built-in operation')` for
list returns of BOTH sizes. Review screens, 2 fresh oracle-env processes
per size, byte-stable:

```
annotate-list2: builtins.TypeError | 'bad argument type for built-in operation'
annotate-list3: builtins.TypeError | 'bad argument type for built-in operation'
```

The arm is unreachable through every committed reference function (none
returns a list), so no banked case was wrong — but the engine claimed a
pin shape it did not have, exactly the screened-not-cased hiding spot this
review targets. Fixed to the pinned behavior (`isinstance(value, tuple)`
gate before the size check; tuple subclasses pass `PyTuple_Check` and the
isinstance alike), with the boundary re-documented in the coercion
docstring and the board, and a fast-tier seam test pinning both list sizes
(`test_annotation_fn_list_return_raises_pinned_bad_argument_any_size`).
All four previously-screened arms retain their exact behavior under the
fix (3-tuple → size-mismatch ValueError; Interval → bad-argument
TypeError; 2-tuple → pass-through), and the three packet cases re-passed
oracle-vs-rewrite after the fix. The still-unmodeled boundary is now
stated precisely: element-level conversion faults of a real 2-TUPLE
(non-numeric elements) remain named-unobserved.

Also verified at this seam: the coercion sits AFTER the no-break match
loop (pin: unbox happens once at objmode exit on the last assignment —
same observable), and the no-match NameError outranks it (pin: the
unassigned objmode output raises before any unbox). The head-side guard
raises only on a matched registrand's non-list return; the no-match arm
still returns the pre-seeded empty list (the pinned silent arm).

## 2. B17 / DIV-0003 — verified as pre-authorized

- The session-25 batch §B17 and §Adjudication record read verbatim:
  "recorded direction for the fp+`infer_edges` KeyError payload:
  DIV-0002's shape (same seam, same type, honest stable message) whenever
  that arm is ever cased." The implemented raise is `builtins.KeyError`,
  at `_add_edge`'s existing-edge branch, gated `interp.fp_mode`, message
  built only from the edge pair and timestep — the recorded direction,
  implemented at the recorded seam.
- Pin seam re-derived: interpretation_fp.py's per-timestep world dicts
  initialize t=0 only and empty (lines 144-184 as cited); the
  existing-edge branch getitem sits at **line 2244** (the record and the
  engine comment cited 2245 — off-by-one, fixed); numba's payload-less
  `raise KeyError()` is at dictobject.py:778 in the oracle env as cited.
- The pin-side e2e reproducer passes (review run below), asserting the
  payload-less shape (bare final traceback line + the typed-dict raise
  site). The fast-tier twin asserts the adjudicated message exactly.
- Default engine untouched: the guard is `fp_mode`-gated; the default
  path's existing-edge branch is byte-for-byte the pre-session logic, and
  on that schedule every existing edge holds a world entry by construction
  (`rule-from-csv-basic` remains the covering case — still sound).
- Case-less disposition verified: `compare_probes`' only per-probe policy
  form is a numeric tolerance (harness/compare.py), which cannot cover a
  raise-message difference; DIV-0002's record is likewise "case ids:
  none". The precedent citation is accurate.

## 3. SHADOWS + reject arms — non-disturbance verified

The reference_fns diff is add-only: `resolve()` and every pre-existing
registrand are untouched, and registration only happens when a case's
apply op selects a name — so no previously-committed case can observe the
new entries. The registry gate's new invariant (non-shadow key ==
`__name__`; shadow `__name__` == declared non-shadow target, distinct
object) holds in the fast tier. Empirical seal: this review re-ran
`annotation-fn-two-arg` (the slice-7-family registrand case) and
`hello-world` through the harness alongside the packet cases — **both
PASS, all probe digests byte-identical to their banked artifacts**
(`results/annotation-fn-two-arg`, `results/hello-world`), so the
mechanism disturbed nothing the oracle path previously banked, consistent
with the session-22 banked result.

## 4. The 6 cases — re-run PASS, contracts sound

Review rerun (one invocation, fresh results dir, PYTHONHASHSEED=0,
post-fix rewrite): **all 6 PASS** — see
`results-session29-review/report.json` under the review scratch dir; the
verdicts and the raise-record outcomes match the author's committed run
(`results-session29-breadth/report.json`, whose banked a1/b1 artifacts
this review inspected directly — the oracle's own outcome records carry
the exact claimed messages, so the PASS verdicts genuinely pin message
text cross-engine). Probe sets are sound: the three reject-arm cases bank
the raise as the reason step's outcome record plus `get_time` with
`allow_raise` (post-raise state); the duplicate-name pair banks the
resolution asymmetry through trace/frames; the edge-rule case banks both
head positions on the existing edge. `proves:` docstrings match what the
tests assert. Board widening consistent — inventory gate green
(tests/test_surface_inventory.py, 6 passed).

## 5. The cache-audit disclosure — restore faithful, characterization corrected

Independently verified: `git -C oracle/pyreason status --porcelain` clean
at `e1a94af33e1f`; the oracle-env kernel cache holds exactly **237 files**
with no file newer than the author's cleanup window; a review-run
`hello-world` oracle capture was cache-hitting with probe digests
byte-identical to the banked session-15 artifact. Every index entry's
data file exists (no orphaned references) — the hand-rewrite left the
indexes structurally consistent. The root-cause naming (one screen
process without the capture's snapshot/restore; no writes in the runner
window) is consistent with the evidence and with capture.py's documented
mechanism.

**Finding F2 (correction of record, no code change): the report's "ZERO
module-path references … nothing load-breaking" claim is a grep
artifact.** BSD grep without `-a` classifies these `.nbc`/`.nbi` files as
binary under a UTF-8 locale and reports NO match even where the bytes are
present (reproduced live: `grep -c harness <index>` → 0/exit 1;
`grep -a -c` → 1; a Python byte-scan → 2 occurrences). A byte-level scan
finds `harness`/`reference_fns` references in FOUR pre-existing `.2.nbc`
dispatcher-embedding specializations (written 2026-07-07 18:47 — part of
the banked 237-file baseline, NOT a session-29 leak) and in their four
rewritten indexes (`interpretation._ground_rule-809`,
`._call_head_function-2315`, `._determine_node_head_vars-2230`,
`._determine_edge_head_vars-2271`). The session-29 `.3.nbc` twins of these
same kernels almost certainly carried the same references (they embed the
same dispatcher types by construction); the author's grep could not have
seen them. Consequences, stated precisely:

- The author's **restore is faithful** — the 237-file baseline was
  restored exactly, and this review's captures/probes kept it there.
- The **baseline itself carries a latent hazard that predates session
  29**: those four indexes unpickle only where `harness` is importable
  (reproduced: `pickle.load` on the index → `ModuleNotFoundError: No
  module named 'harness'`; numba's `_load_index` does not guard that
  unpickle, and capture.py's own docstring documents the 2026-07-07 live
  reproduction of the hard error). Harness captures and repo-root `-c`
  runs are unaffected (repo root on sys.path); a plain-script default-
  schedule oracle run outside the repo root would fail at those four
  kernels' index loads. The fp kernels' indexes are clean, so the
  DIV-0003 reproducer is unaffected.
- **No unilateral cleanup**: excising the four `.2.nbc` entries would
  change the banked baseline every restore-check and byte-identity claim
  compares against — that is an operator decision. Recommendation:
  adjudicate a one-time cache re-baseline (drop the four 2026-07-07
  leaked entries, re-bank the file count and a fresh hello-world sweep)
  in a dedicated session; until then the hazard is documented here and
  bounded (harness paths unaffected).

## 6. L4 unreachability — confirmed

Re-derived: the pinned `Threshold.__init__` validates quantifier and
quantifier_type membership (oracle threshold/threshold.py — `("number",
"percent")` × `("total", "available")`), the rewrite's mirrors it; both
rule parsers consume `custom_thresholds` only through `.to_tuple()` on
Threshold instances (a raw tuple dies at the attribute lookup before any
reasoning) and synthesize only valid defaults (`("greater_equal",
("percent", "total"), 100)`); the case format cannot express a duck-typed
object. No public-surface input reaches `_satisfies_threshold` with a
quantifier-type outside number/percent. Leaving the rewrite arm as-is,
recorded without a code change, is the right AC-6-shaped call — changing
it would be an equivalence claim with no observable.

## 7. Review fixes

1. `_coerce_annotation_pair`: len()-model → tuple-check (F1), with the
   corrected docstring, the new seam test, and the board's tuple-only
   sentence + named-unobserved tightening (a 2-TUPLE of non-numbers).
2. Line citation interpretation_fp.py:2245 → 2244 in DIV-0003.md and the
   `_add_edge` guard comment.
3. F2 recorded above as a correction of the author report's cache-audit
   characterization — the report itself stays as filed (historical
   record); this section is the correction of record.

## Evidence commands (from the repo root)

```
# fast tier (297 = 296 + the review's list-return seam test)
uv run pytest -m "not e2e"

# the packet's e2e: 6 cases + hello-world + annotation-fn-two-arg,
# oracle-vs-rewrite, one invocation
mkdir -p /tmp/review-cases && for c in annotation-fn-return-triple \
  annotation-fn-return-interval head-fn-return-bare-string \
  annotation-fn-duplicate-name head-fn-duplicate-name \
  head-fn-edge-rule-positions hello-world annotation-fn-two-arg; do \
  cp harness/cases/$c.json /tmp/review-cases/; done
PYTHONHASHSEED=0 uv run python -m harness.run --cases /tmp/review-cases \
  --engine-a oracle-env/bin/python --engine-b scripts/rewrite-python \
  --results /tmp/results-session29-review

# the DIV-0003 pin-side reproducer
uv run pytest tests/test_div_0003_reproducer.py -m e2e

# the cache-audit reproduction (byte-scan vs grep false-clean)
python3 - <<'EOF'
from pathlib import Path
cache = Path("oracle-env/lib/python3.10/site-packages/pyreason/cache")
hits = [p.name for p in cache.rglob("*") if p.is_file()
        and b"reference_fns" in p.read_bytes()]
print(len(hits), sorted(hits))
EOF
```

## Hygiene

- No installs, no dependency changes; `oracle/pyreason` untouched
  (byte-clean at the pin before and after review).
- Every review probe batch ran under the capture's own
  snapshot/restore helpers; the kernel cache was verified back at 237
  files after each batch.
- No full-corpus sweep: fast tier + the packet's cases (+ the two
  digest-comparison reruns) + the packet's reproducer only.
