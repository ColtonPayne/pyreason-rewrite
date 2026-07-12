<!-- doccode: pyreason-rewrite-docs-reviews-2026-07-12-breadth-registrand-edgerule-author -->
# Session 29 — author report: the registrand-behavior packet, the edge-rule head-function forms, and B17's pre-authorized DIV-0003

- session: 29 · date: 2026-07-12 · author packet (the unblocked breadth
  thread carried since session 22; the execution-layer decision stays
  queued and untouched)
- verdict: **6/6 new cases oracle-vs-rewrite PASS**
  (`results-session29-breadth/report.json`, exit 0, ALL PASS — one
  invocation, 4 fresh-process captures per case, same-engine repeats
  digest-stable, PYTHONHASHSEED=0); fast tier **296 passed** (289
  preexisting + 7 new seam tests); the DIV-0003 pin-side e2e reproducer
  passes; **1 pre-authorized intentional divergence implemented and filed
  (DIV-0003)**, zero unadjudicated divergences
- code commits: `4914cff` (engine guards + reference fns + 7 seam tests),
  `60350c6` (DIV-0003 + pin reproducer), `0efb82b` (cases + board),
  plus this commit (report)

## What the deferred arms were, and what they are now

**L3 (slice-2 review, deferred by slice 7 as unreachable):** the rewrite's
`annotate()` accepted anything indexable at [0]/[1] where the pinned
objmode block coerces the registrand return to `Tuple((float64, float64))`
at its exit (interpretation.py:1918); the head-side twin — the pinned
`_call_head_function` unboxes its objmode result to
`types.ListType(types.unicode_type)` (interpretation.py:2332) — was the
board's "returning something other than a numba typed list of strings"
named-unobserved. Both were unreachable through every committed reference
function (all return well-shaped values); the slice-7 conditional-njit
accommodation is what made new reject-arm registrands authorable. This
session authored them and made the rewrite reproduce the pinned coercion
observables at the same seams:

| arm | pin behavior (screened 2/2 fresh processes, 2026-07-12) | rewrite now |
|---|---|---|
| annotation fn returns 3-tuple | `builtins.ValueError: size mismatch for tuple, expected 2 element(s) but got 3` | same, at `annotate`'s return coercion (`_coerce_annotation_pair`) |
| annotation fn returns an Interval | `builtins.TypeError: bad argument type for built-in operation` | same (the no-length arm of the same coercion) |
| head fn returns a bare string | `builtins.TypeError: can't unbox a <class 'str'> as a <class 'numba.typed.typedlist.List'>` | same, at `call_head_function`'s return guard |

Boundary honesty: the coercions reproduce exactly the screened arms plus
the pass-through for well-shaped returns; element-level conversion faults
(a size-2 sequence of non-numbers; a list of non-strings) are named
unobserved on the board — no committed reference function returns one, and
banking those arms would need their own pin screens first.

**L4 (slice-2 review, deferred):** `_grounding._satisfies_threshold`
returns falsy `None` for a quantifier-type outside number/percent where
the pinned jitted twin would fail compilation-side. Re-verified this
session as **unreachable through every public input**: the pinned
`Threshold` constructor validates quantifier and quantifier_type
membership (oracle threshold/threshold.py), the rewrite's mirrors it
(banked `threshold-construct` reject arms), the rule-text parser only
synthesizes valid tuples (slice-2 review), and the harness constructs
thresholds only through `pr.Threshold`. No case can discriminate the arm;
changing the rewrite's internal shape with no observable would be an
equivalence claim by code-reading, so it stays as-is, recorded here. Not
a code deliverable — the deferral rationale's "L3/L4" packet reduces to
L3 plus this unreachability re-verification.

**B3 (duplicate-name registrands, "seam-level only" since slice 2):** now
cased cross-engine through a new registry mechanism — *shadow entries*
(`harness/reference_fns.py` `SHADOWS`): registry KEYS that deliberately
differ from their functions' `__name__`s, the only way one JSON case can
register two distinct callables under one engine-visible name. The
fast-tier registry gate now asserts the split invariant (non-shadow keys
== `__name__`; shadow `__name__` == declared target). The two resolution
asymmetries banked: annotate's no-break loop runs every same-named
registrand and the LAST registration wins; `_call_head_function` BREAKS on
the first match so the FIRST registration wins.

## Case list and results (`results-session29-breadth/`, one invocation, 4 fresh captures per case)

Wall-clock is the artifact-recorded per-capture engine time (import s /
step-and-reason s); verdicts of record are
`results-session29-breadth/report.json`.

| case | what it banks | verdict | oracle a1 | rewrite b1 |
|---|---|---|---|---|
| annotation-fn-return-triple | ValueError('size mismatch for tuple, expected 2 element(s) but got 3') as the reason step's outcome record | pass | 1.35/38.9s | 0.07/~0s |
| annotation-fn-return-interval | TypeError('bad argument type for built-in operation') ditto | pass | 1.33/38.7s | 0.07/~0s |
| head-fn-return-bare-string | TypeError("can't unbox a <class 'str'> as a <class 'numba.typed.typedlist.List'>") ditto | pass | 1.36/49.7s | 0.07/~0s |
| annotation-fn-duplicate-name | both same-named registrands run, LAST registration's bound banks (combo(·)=[0.5,0.75], the shadow's constant, not clause_lower_mean's [0.25,1]) | pass | 1.31/37.0s | 0.07/~0s |
| head-fn-duplicate-name | FIRST registration wins (break): the shadow's last-grounding pick banks Processed(B) over the real picker's A | pass | 1.36/49.8s | 0.07/~0s |
| head-fn-edge-rule-positions | LinkedOne(f(X), Y) and LinkedBoth(f(X), f(Y)) each derive (A,B):[1,1] on the existing edge; edge trace + frames + get_time | pass | 1.37/50.2s | 0.07/~0s |

(The oracle numbers are the dispatcher-bearing numba compile cost per
fresh capture, the class sessions 15/22 banked; no performance claim is
made or licensed by this table.)

## B17 — the pre-authorized fp+infer_edges direction, implemented (DIV-0003)

- **Pin-side banked:** `tests/test_div_0003_reproducer.py` (e2e, passes
  against the live oracle env) — fp_version + an infer_edges rule whose
  inferred edge re-derives at a later timestep dies inside fp `reason()`
  with the PAYLOAD-LESS `builtins.KeyError()` from numba's typed-dict
  getitem (dictobject.py:778; traceback's final line is bare `KeyError`).
  Screened 2/2 fresh pin processes before the test was written.
- **Rewrite-side implemented:** at the same logical seam — `_add_edge`'s
  existing-edge branch, gated to the fp path where alone the state is
  reachable — the rewrite raises `builtins.KeyError` with the honest,
  stable message `edge ('A', 'B') already exists but has no world at
  timestep 1: the fp schedule's per-timestep world maps do not carry
  existing edges forward, so an inferred edge cannot be re-derived at a
  later timestep`. Exactly the operator's recorded direction (2026-07-11
  batch adjudication, item B17: DIV-0002's shape — same seam, same type,
  honest stable message; docs/ledger/phase3-adjudication-batch.md §B17 and
  §Adjudication record). Seam test:
  `test_fp_infer_edges_rederivation_raises_the_adjudicated_stable_keyerror`.
- **Record filed:** [DIV-0003](../divergences/DIV-0003.md) —
  classification intentional-divergence, status **adjudicated** on filing
  (the verdict pre-authorized; the record cites the session-25 batch).
- **Covering-case disposition (packet 3d):** NO committed case — the
  corpus's only per-probe comparison-policy form is a numeric `tolerance`
  (harness/compare.py `compare_probes`), which cannot cover a raise-record
  message difference, and inventing a raise-type-only policy is exactly
  the new-mechanism move the packet forbids. The precedent followed is
  DIV-0002's own: its arm is likewise case-less ("case ids: none"), with
  the DIV record + the pin-side e2e reproducer + the fast-tier seam twin
  carrying the evidence. The nearest committed case (`rule-from-csv-basic`,
  default-schedule infer_edges) covers the branch's unreachability on the
  default path.

## Board deltas (docs/surface.md; inventory gate green)

- `fn:add_annotation_function` — cases +3 (return-triple, return-interval,
  duplicate-name); input classes +`malformed-return-shape`,
  +`interacts-duplicate-name`; the Interval-return named-unobserved
  resolved into pinned text; element-level coercion faults stay named
  unobserved. Status stays `equivalent` (every listed case passed —
  the three new ones in this session's run).
- `fn:add_head_function` — cases +3 (return-bare-string, duplicate-name,
  edge-rule-positions); input classes +`happy-edge-rule-heads`,
  +`malformed-return-shape`, +`interacts-duplicate-name`; both
  named-unobserved items this packet targeted (edge-rule forms, return
  contract) resolved into pinned text; the non-njit poisoning and
  element-dtype arms stay named unobserved. Status stays `equivalent`.
- `setting:fp_version` — the B17 sentence now records the implemented
  DIV-0003 with the case-less rationale. Status unchanged (`equivalent`);
  the B16 Phase-4 hazard note untouched.

## Wall-clocks (screen-then-confirm)

The first oracle screen (`ann-triple`) ran end-to-end in **39.1 s** — the
dispatcher-bearing compile cost the ledger predicted — before the family
was run; every subsequent registrand screen landed in the same class.
Screens: 7 arms + 2 stability repeats + 2 fp screens ≈ 8 min of oracle
time total. The committed family run's per-capture timings are in the
table above (annotation-family oracle captures ~37–39 s, head-family
~50 s, rewrite captures ~0.07 s import-bound); whole 6-case invocation
≈ 9 min.

## Evidence commands (from the repo root)

```
# fast tier
uv run pytest -m "not e2e"          # 296 passed, 5 deselected

# the packet's e2e: the 6-case family, oracle-vs-rewrite, one invocation
mkdir -p /tmp/session29-cases && for c in annotation-fn-return-triple \
  annotation-fn-return-interval head-fn-return-bare-string \
  annotation-fn-duplicate-name head-fn-duplicate-name \
  head-fn-edge-rule-positions; do cp harness/cases/$c.json /tmp/session29-cases/; done
PYTHONHASHSEED=0 uv run python -m harness.run --cases /tmp/session29-cases \
  --engine-a oracle-env/bin/python --engine-b scripts/rewrite-python \
  --results results-session29-breadth-rerun

# the DIV-0003 pin-side reproducer
uv run pytest tests/test_div_0003_reproducer.py -m e2e
```

## Hygiene

- No installs, no dependency changes; `oracle/pyreason` byte-clean at
  `e1a94af33e1f` (checked post-run); oracle-env bundled kernel cache
  restored by the capture's snapshot/restore on every registrand capture
  and by the screens' own snapshot/restore.
- **Cache-leak found and remediated (disclosure):** a post-run audit
  found FOUR dispatcher-embedding kernel specializations
  (`interpretation._call_head_function/-ground_rule/-determine_*_head_vars`
  `*.3.nbc`, ~3.7 MB, written 01:51 during this session's screen phase —
  one screen process's saves survived; the committed capture machinery
  itself leaked nothing: no `.nbc` writes during the runner window
  remain). The entries carried ZERO module-path references (grepped for
  `harness`/scratchpad/`__main__` — clean, so nothing load-breaking, only
  the never-hittable dead-weight class) and were removed surgically: the
  four data files deleted and each index rewritten with its leaked entry
  dropped, restoring the pre-session 237-file state. Post-cleanup proof:
  a fresh oracle `hello-world` capture is cache-hitting (6.9 s) and its
  probe digests are byte-identical to the banked session-15 sweep
  (`results/hello-world/a1.json`).
- No full-corpus sweep: fast tier + the 6 packet cases + the packet's
  reproducer e2e only.
- Screens and scratch scripts confined to the session scratchpad;
  `results-session29-breadth/` gitignored per the convention.
- The execution-layer thread untouched: no acceleration work, no
  dependency asks.
