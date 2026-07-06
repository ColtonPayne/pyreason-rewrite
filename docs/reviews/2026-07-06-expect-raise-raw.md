# Review — commit 3a1d32b: expect_raise probe, optional reason, ipl input

Scope: `harness/capture.py` and `tests/test_capture_validation.py` at HEAD, as consumed
by `harness/cases/rule-text-malformed.json`, `harness/cases/fact-text-malformed.json`,
`harness/run.py`, `harness/compare.py`. Hunt: correctness defects only — wrong-verdict
paths (false pass / false divergence / authoring fault mislabeled as engine failure),
ordering/side-effect hazards, exception-message nondeterminism, validation gaps.

## What I verified as *safe* (so it isn't re-litigated)

- **Constructor isolation holds for the oracle.** `oracle/.../rules/rule.py` and
  `.../facts/fact.py` show `Rule.__init__` / `Fact.__init__` only call a parser and store
  the result — no module-global mutation. So `probe_expect_raise` running *after* `reason()`
  in a mixed case cannot perturb the already-computed interpretation, and probe order among
  `expect_raise` constructions is side-effect-free. The comment at capture.py:28-30 is
  accurate for the oracle. (This safety is itself part of the equivalence being tested, so
  it is not guaranteed for the rewrite — but that is a divergence the harness would surface,
  not a harness defect.)
- **Positional signatures match.** `pr.Rule(text, name, infer_edges)` and
  `pr.Fact(text, name, start, end, static)` line up with the oracle's constructor params.
- **`get_time` without `reason()` does not crash the oracle** — `get_time()` swallows the
  `get_interpretation()` failure and returns `0` (oracle pyreason.py:554-558).
- **Oracle parser messages are deterministic** — no addresses, set/dict reprs, or
  hash-ordered content; `PYTHONHASHSEED` is pinned. Same-engine repeats (a1/a2) are stable.
- **ipl validation + consumption is shape-safe.** The `[str,str]`-pair guard makes the
  `for pred_a, pred_b in ...` unpack in run_case:179 total; `add_inconsistent_predicate`
  is called before `reason()` (correct order). A `null` ipl value is rejected (exit 2).

---

## Findings

### H1 — Acceptance is recorded as a bare `{"raised": false}`, discarding the parsed object → false pass on accepted-boundary inputs
**Severity: High (wrong verdict — false pass)**
**capture.py:124; harness/cases/fact-text-malformed.json:33-34**

`probe_expect_raise` reduces a successful construction to `{"raised": False}` with *zero*
information about the resulting `Rule`/`Fact`. The `fact-text-malformed` case deliberately
carries an **accepted** shape — `bound-predicate-charset` = `si-ck.v2(Alice)` — and that
case **never runs the reasoner** (`inputs` has no `reason` block). So if the oracle and the
rewrite both *accept* `si-ck.v2(Alice)` but parse it into different predicate/component
values (e.g. the rewrite's `_PREDICATE_RE` treats `.`/`-` differently, or splits the
component differently), both probes emit the identical `{"raised": false}` and the case is
declared **`pass`** — two engines with divergent parse behavior on this input are certified
equivalent. Nothing else in this tranche compares the parse, because the tranche's whole
point is that it does not reason. Concrete failure: rewrite accepts `si-ck.v2` as predicate
`si-ck.v2`, oracle accepts it as predicate `si` (or errors on the component) — if both merely
"don't raise", the divergence is invisible. The probe's docstring claims acceptance "is as
much a captured behavior as the raise," but it captures nothing distinguishing about it.

Fix direction: for the acceptance branch, record a canonical fingerprint of the constructed
object (e.g. `str(fact)`/parsed pred+component+bound, or the rule's normalized form) so two
different accepted parses cannot collide.

---

### M1 — `INTERP_PROBE_KINDS` is a second hand-maintained list with no drift guard → a future interp probe crashes as exit 1 (engine failure) instead of exit 2 (authoring fault)
**Severity: Medium (wrong exit label)**
**capture.py:31-33, 68-71; run_probe dispatch capture.py:127-145**

The "must carry a `reason` block" gate is driven by `INTERP_PROBE_KINDS`, a set maintained
*separately* from `PROBE_KINDS` and the `run_probe` dispatch. `test_probe_kinds_cover_the_capture_dispatch`
guards `PROBE_KINDS` ↔ dispatch, but **nothing guards `INTERP_PROBE_KINDS` completeness.**
Add a new interpretation-consuming probe kind to `PROBE_KINDS` + `run_probe` and forget to
list it in `INTERP_PROBE_KINDS`: a case using only that probe with no `reason` block passes
`validate_case`, then `run_probe(pr, None, probe)` dereferences `interpretation=None`
(`interpretation.get_dict()`-style) → `AttributeError` inside `run_case` → `main` returns
**exit 1**, stamping an authoring/harness gap with the engine-failure label the taxonomy
exists to prevent. The exact failure the module docstring (lines 11-13) promises cannot
happen, can happen. Fix: derive `INTERP_PROBE_KINDS` completeness from a single source, or
add a test asserting every non-`{get_time, expect_raise}` kind is in the interp set.

---

### M2 — `except Exception` conflates a DSL rejection with a harness/binding fault; both are recorded as an engine "raise" observation
**Severity: Medium (authoring/binding fault mislabeled as engine behavior; can force false divergence or false pass)**
**capture.py:115-124**

The `try/except Exception` cannot tell "the constructor rejected the DSL text" (the intended
observation) from "calling the constructor failed for harness reasons." If an engine lacks
`pr.Rule`/`pr.Fact` (`AttributeError`), or the rewrite's constructor has a different
positional arity so `pr.Rule(text, name, infer_edges)` mis-binds (`TypeError`), that failure
is silently captured as `{"raised": True, "type": "AttributeError"/"TypeError", "message": ...}`
and compared **as if it were the parser's rejection behavior**. Two outcomes, both wrong:
(a) oracle raises a real `ValueError` from parsing while the rewrite raises a binding
`TypeError` → recorded as a `divergent` verdict that is actually a harness wiring bug, not an
engine finding; (b) a genuine constructor mismatch is normalized into the same
`{"raised": True}` shape as a legitimate rejection and never surfaces as a *capture* failure
(exit 1/2), only as probe data. The taxonomy's promise that binding/authoring faults never
wear an engine-behavior label is violated at the probe boundary. Fix: only treat the
engine's declared parse/validation exception types as "raised"; let unexpected exception
classes (AttributeError, TypeError from arity) propagate to `run_case`'s handler as a
capture failure.

---

### M3 — Exception identity reduced to short `type(exc).__name__` + verbatim `str(exc)`: message text couples the verdict to embedded CPython builtin wording (false divergence), and short-name collisions can false-pass
**Severity: Medium (false divergence across differing engine Pythons; low-probability false pass)**
**capture.py:123**

Two coupled fragilities in the recorded `{type, message}`:

1. **Verbatim message compared across engines that may run different Python versions.**
   The harness compares `a1` (engine-a) against `b1` (engine-b) with **no requirement that
   their `engine.python` match** (judge_case:77-83 only checks Python equality *within* a
   same-engine pair). The oracle's `fact_parser` re-raises CPython's own `float()` message:
   `raise ValueError(f"Invalid interval values: {e}")` for `sick(Alice):[low,high]`
   (exercised by `malformed-interval-nonnumeric`, and `malformed-bound-nonnumeric` in the
   rule case). That embedded builtin wording is CPython-version-dependent; if engine-a and
   engine-b run different CPython versions, the two engines can reject the *same* input for
   the *same* reason yet record different `message` strings → **`divergent`** for a
   non-divergence. (Same-engine self-proof pairs share a Python, so they are safe; the risk
   is cross-engine oracle-vs-rewrite with mismatched interpreters.)
2. **Short-name only.** `type(exc).__name__` drops the module/identity, so an engine that
   raises a custom exception class sharing a builtin's short name (e.g. its own `ValueError`
   or a `ParseError` that also exists in the other engine) compares equal on `type`; if the
   messages also coincide, a semantically different rejection reads as a `pass`.

Fix direction: compare against a normalized, engine-neutral rejection tag rather than raw
`str(exc)`; if full-message parity is truly the contract, document that engine-a/engine-b
must share a CPython version and enforce it in judge_case.

---

### L1 — Making `reason` optional silently changes `get_time`-only cases from "time after reasoning" to "no-interpretation fallback"
**Severity: Low (behavior change; latent exit-1 mislabel for a non-guarding engine)**
**capture.py:182-187; INTERP_PROBE_KINDS excludes `get_time` at capture.py:31-33**

Before this commit `reason()` always ran, so a `get_time` probe always read post-reasoning
state. Now a case with a `get_time` probe and no `reason` block (the `VALID` fixture's exact
shape) skips `reason()` and `get_time()` returns its no-interpretation fallback (`0` in the
oracle) instead of a reasoned time — a quiet semantic change for any such authored case.
Safe for the oracle because `get_time` swallows the missing-interpretation error; but the
harness now permits `get_time` to run against uninitialized module state, and an engine
whose `get_time` does *not* guard that path would raise → `run_case` → **exit 1**, an
engine-failure label for what is really "the case forgot to reason." Low because no shipped
case exercises it and the oracle is safe, but the invariant "get_time runs without a reason
block" (comment, capture.py:29) rests on an engine-specific swallow, not on the harness.

---

## Severity summary
- High: 1 (H1)
- Medium: 3 (M1, M2, M3)
- Low: 1 (L1)
