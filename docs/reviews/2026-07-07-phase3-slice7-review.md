<!-- doccode: pyreason-rewrite-docs-reviews-2026-07-07-phase3-slice7-review -->
# Phase 3, slice 7 — the registrand packet (independent review)

- session: 22 · 2026-07-07 · reviewer-fixer packet (no shared context with the author)
- scope reviewed: the full diff `9f29912..0b670a2` as a coherent whole, graded
  against the pinned source at `e1a94af33e1f` and the slice-7 packet spec
  (session-21 NEXT)
- verdict: **the accommodation and the committed cases are correct as landed —
  every author claim reproduced independently — but a review probe exposed one
  rewrite defect on a caseable registrand input the committed cases could not
  see, fixed by this review; the corrected slice passes.** Author's 7/7 claim
  reproduced pre-fix (7/7 ALL PASS, all 28 capture digests identical to the
  author's run); both digest cross-check claims recomputed and confirmed
  (18/18 identical); the discriminating probes then refuted the head-function
  family's raise-shape fidelity on the ungrounded-argument arm. Post-fix
  evidence: **8/8 pass** (the 7 packet cases + the review's regression case)
  into `results-phase3-slice7-review/`; fast tier **265 passed** (263 + the
  review's 2 seam tests); **5/5 reviewer discriminating probes pass or
  expose-then-pass**; board **50/52 confirmed mechanically** (3 flips, no
  missed or premature flip; the regression case joins fn:add_head_function's
  case list, already equivalent, flip invariant holds). Oracle-env kernel
  cache verified at the 233-file zero-residue baseline after every run.

## Findings, by severity

**F1 (rewrite-defect, fixed) — the ungrounded head-function-argument arm
raised the wrong KeyError shape.** A variable that appears only inside the
head function's argument list is not in `groundings`, and the pin passes it
**as itself** (`interpretation.py:2300-2305` "If variable not grounded, treat
it as itself") — so `first_clause_first_grounding(Z)` returns the literal
`'Z'`, a name that is no graph node, and the pin's unguarded typed-dict
lookup at the rule-application seam (`interpretations_node[n]`,
interpretation.py:583) raises the **bare** `builtins.KeyError` — numba's
nopython typed-dict getitem erases the key, so the message is empty (screened
live on the pinned engine). The committed rewrite's plain-dict lookup at the
same seam (`_interpretation.py` default-schedule apply arm) raised
`KeyError: 'Z'` — same type, key-bearing message, so the raise records
compare unequal on a caseable input (valid DSL rule text
`Processed(first_clause_first_grounding(Z)) <- starter(X)`, a committed
reference function, standard steps). Fix, following slice-6's TypedRuleList
precedent (model the pin's container semantics, not one call site):
`_interpretation.TypedComponentDict`, a dict subclass whose `__missing__`
raises the bare `KeyError`, carried by the default schedule's
`interpretations_node`/`interpretations_edge` maps — the exact containers
that are numba typed.Dicts at the pin. The fp schedule's lookups are
membership-guarded at the pin and in the rewrite (its worlds dicts start
empty by design), so no bare-getitem miss is reachable there and its maps
stay plain. The one message-insensitive `except KeyError` consumer
(`_update_component`'s pinned missing-component guard) is unaffected.
Banked as the committed regression case **`head-fn-ungrounded-var`** (passes
both engines post-fix, byte-equal raise records), the seam test
`test_head_fn_ungrounded_var_raises_the_pinned_bare_keyerror`, and the
fn:add_head_function board note.

No other defects. In particular, three candidate concerns verified sound:
the ModuleNotFoundError-only discriminator (see the probes — a
present-but-broken numba propagates), the plain arm's identity handoff
(resolve() twice returns the same object — harmless, the engine matches by
`__name__`, and the pin's own dispatchers differ per resolve anyway), and
the `_PLAIN_NUMBA` stand-in's deliberate minimality (only `typed.List`; any
other attribute access fails loudly in the plain arm, verified by reading
every committed reference function's numba surface — only
`first_clause_first_grounding` touches the global, only via `typed.List`).

## The accommodation, graded against the pin

**The discriminator is precise and minimal.** resolve() njit-wraps exactly
where `import numba` succeeds and hands the committed function plain only on
`ModuleNotFoundError`. Two properties make this exact rather than merely
reasonable: (1) in the oracle capture the engine itself imports numba before
any step runs (pyreason's own import chain), so an engine process that
reaches resolve() with the pinned engine has already proven numba importable
— the njit arm is selected by construction, never by luck; (2) the plain arm
is reachable only in an engine environment that cannot consume a dispatcher
at all, where "plain" is the only form a callable can take. A
present-but-broken numba (ImportError that is not ModuleNotFoundError)
propagates and fails the capture loudly — probed, not just argued (probe 4).
No engine sniffing, no flags, no new state.

**The oracle path is provably unchanged.** Recomputed both of the author's
digest cross-checks from the artifacts, then reproduced them from live runs:

- all 10 oracle captures (5 registrand cases × a1/a2) in
  `results-phase3-slice7/` byte-identical to the pre-accommodation
  session-15 sweep artifacts in `results/` — **10/10 recomputed identical**;
- all 8 spot-check captures (2 unregistered-name cases × a1/a2/b1/b2)
  byte-identical to the banked slice-2 artifacts — **8/8 recomputed
  identical**;
- my own independent 7-case rerun's 28 captures all digest-identical to the
  author's run — the whole packet is deterministic across operators, not
  just across same-engine repeats.

**Blast radius honestly stated:** resolve() is reached only through
`REGISTRY_OPS` (verified at both apply sites in harness/capture.py), so the
accommodation is dead code for every non-registrand case; the spot-check +
sweep-digest cross-checks cover the change's reach. The module stays
stdlib-only at import (fast-tier test holds it).

**Seam tests read line-by-line:** all four `proves:` docstrings match their
assertions. The numba-arm simulation is honest — the stand-in module is
planted in `sys.modules`, which is precisely the seam `import numba`
consumes, so the arm decision and the wrap both execute for real. The plain
arm test asserts the env invariant (`find_spec("numba") is None`) rather
than assuming it. The integration seam test drives the exact resolve()
output through the rewrite facade to the banked observables.

## fn:reset_rules — the flip is evidence-forced

The pin's `reset_rules` (pyreason.py:517-527) clears `__rules`,
`__annotation_functions`, and `__head_functions` together. The row's four
cases split the surface exactly: reset-rules-no-program/-with-program
(slice 3) pin the rules-clearing arms; `annotation-fn-reset-clears` proves
the annotation-registry clear observably (the re-added rule raises the
never-registered arm's NameError after reset — impossible if the registry
survived); `head-fn-reset-clears` proves the head-registry clear by the
silent-empty twin. All four in the passed set (slices 3 + 7, re-verified in
my rerun). Probe 2 additionally proves the registries **accept and serve
fresh registrands after** reset_rules — clearing without poisoning — which
no committed case covered.

## Discriminating probes (overfitting hunt) — 5 probes

Probes 1–3 ran cross-engine through the harness (PYTHONHASHSEED=0,
oracle-env vs scripts/rewrite-python, 4 fresh-process captures each, session
scratchpad); probe 4 is a fast-tier import-seam test; probe 5 is a
screen-then-confirm pair that became the F1 regression case.

| probe | seam it pins beyond the 7 cases | verdict |
|---|---|---|
| rv-registrand-both-kinds-argswap | both registrand kinds resolve+register+derive in ONE capture (resolve() twice per engine process), and the multi-arg head-fn form with SWAPPED variable order f(Y, X) — the pin parser's documented shape — grounds the head to the FIRST argument's grounding: Processed(B), not A, pinning fn_arg_values assembly order (interpretation.py:2296-2308) | pass |
| rv-registrand-reregister-after-reset | re-registration AFTER reset_rules: both registries cleared then re-fed, both rules re-added, combo(A)=[0.5,1] and Processed(A)=[1,1] derive — the committed reset-clears pair proves only the clearing | pass |
| rv-annotation-fn-six-arg-cap | the 6-arg reference function's cap arm (9 clause-0 edge groundings, 9/8 clamps to 1.0 → crowd(A)=[1.0,1]) at an extended-metadata cardinality the committed case (2/8) never reaches | pass |
| broken-numba import seam (fast tier, committed) | a numba that is PRESENT but BROKEN (meta-path exec raises ImportError, not ModuleNotFoundError) must propagate and fail the capture, never silently select the plain arm — the author's central discriminator claim, exercised by no committed test | pass — committed as `test_resolve_broken_numba_propagates_not_downgrades` |
| ungrounded head-fn argument screens (both engines) | the "variable not grounded, treat it as itself" arm (interpretation.py:2300-2305) drives the head grounding to a non-node name | **exposed F1** — pre-fix raise shapes differed (`KeyError` bare vs `KeyError: 'Z'`); fixed, byte-equal post-fix, committed as case `head-fn-ungrounded-var` |

## Independent rerun

- Fast tier: `uv run pytest -m "not e2e"` → **263 passed** on the author's
  tree (claim confirmed), **265 passed** post-fix (+ the review's 2 tests:
  the F1 seam test and the broken-numba discriminator test). Inventory gate
  6 passed after the board edit.
- 7-case rerun on the author's tree: **ALL PASS (7)**, exit 0, all 28
  capture digests identical to the author's `results-phase3-slice7/` — the
  defect lives outside the committed cases' reach, which is what the probes
  were for.
- Post-fix rerun (the fix touches the default schedule's shared component
  maps, so the full packet set re-ran): fresh `results-phase3-slice7-review/`
  (gitignored by the author's `f94bc90`) → **ALL PASS (8 cases)** = 7 packet
  cases + the regression case, 4 fresh-process captures each, same-engine
  repeats digest-stable.
- Cache confinement: the oracle-env bundled kernel cache at **233 files,
  zero `harness`/`reference_fns` references** after every run (checked after
  the 7-case rerun, the probe run, and the post-fix run; the review's raw
  oracle screen was wrapped in its own snapshot/restore of the bundled
  cache, taken only while no capture was in flight).

## surface.md — 3 flips verified mechanically

Recomputed, not trusted: `git diff f94bc90~1..f94bc90 -- docs/surface.md`
flips exactly 3 rows `cased → equivalent` (fn:add_annotation_function,
fn:add_head_function, fn:reset_rules). The union of `status: pass` verdicts
across the banked `results*/report.json` dirs covers every case in every
`equivalent` row's case list (no unsupported flip) and no `cased` row's full
list is covered (no missed flip); count **50/52 correct**. The 2 remaining
`cased` rows are exactly the predicted gated remainder
(`fn:load_inconsistent_predicate_list`, `fn:save_rule_trace` via
`ipl-atom-trace-off-trace`). The review's regression case was added to
fn:add_head_function's case list (already equivalent; the case passes in the
post-fix run, so the flip invariant holds).

## L3/L4 disposition (AC-5) — deferral upheld

The author's boundary is drawn correctly: both slice-2 loosenesses (L3, the
annotate() return-shape coercion; L4, the quantifier-membership guard) are
unreachable through every committed reference function and case — verified
against the registry (all functions return float 2-tuples; the Threshold
constructor and parser only produce valid quantifier tuples). Changing the
rewrite's shape on those arms with no case able to observe the change would
be an equivalence claim by code-reading. The accommodation is what makes the
future registrand-behavior packet authorable; the deferral is the evidence
discipline working, not a gap. (F1, by contrast, WAS reachable through a
caseable input — which is exactly the line that separates fix-now from
defer.)

## Hygiene

- No installs, no dependency changes: `git diff 9f29912..HEAD --
  pyproject.toml uv.lock` empty (before and after fixes); numba stays out of
  the campaign env (asserted inside the seam tests, not assumed).
- Oracle tree byte-clean: `git -C oracle/pyreason status --porcelain` empty,
  HEAD = `e1a94af33e1f…` = oracle/PIN.
- `git ls-files 'results*'` → 0 tracked files; both slice-7 results dirs
  gitignored by the author's `f94bc90`; banked prior-slice dirs untouched.
- No security framing in the session diff (scanned).
- Full corpus sweep not run (fast tier + the 8 cases + 3 e2e probes + 2
  screens only, per the wall-clock rule).

## Verdict

**The registrand packet's harness work is exact — the discriminator is the
right one, the oracle path is provably byte-unchanged, and the seam tests
are honest — and its five cases bank what they claim. It shipped one
divergence its cases could not see, on the head-function family's
ungrounded-argument arm, caught by a review screen and fixed in-review:**
the default schedule's component maps now carry the pin's container raise
shape (bare KeyError), seam-tested and banked as a committed case. With the
fix, the slice stands at 8/8 oracle-vs-rewrite PASS, fast tier 265, board
50/52 — one row short of the IPL family being the last thing between the
campaign and the Phase-3 boundary sweep.

## Repro

```
# fast tier (265 post-fix)
uv run pytest -m "not e2e"

# the 8-case rerun (7 packet cases + the regression case)
mkdir -p /tmp/slice7-review-cases && for c in annotation-fn-two-arg \
  annotation-fn-six-arg annotation-fn-reset-clears head-fn-grounding \
  head-fn-reset-clears annotation-fn-unregistered-name \
  head-fn-unregistered-name head-fn-ungrounded-var; do \
  cp harness/cases/$c.json /tmp/slice7-review-cases/; done
PYTHONHASHSEED=0 uv run python -m harness.run --cases /tmp/slice7-review-cases \
  --engine-a oracle-env/bin/python --engine-b scripts/rewrite-python \
  --results results-phase3-slice7-review-repro

# digest cross-checks (recompute the author's non-disturbance claims):
# results-phase3-slice7/<case>/{a1,a2}.json digests vs results/<case>/ for the
# 5 registrand cases (10/10 identical) and vs results-phase3-slice2/<case>/
# {a1,a2,b1,b2}.json for the two unregistered-name cases (8/8 identical)

# F1 screen (both engines): reason() on
# "Processed(first_clause_first_grounding(Z)) <- starter(X)" over nodes A,B
# (starter=1) — both raise builtins.KeyError with an EMPTY message
```
