# Oracle-differential harness — adversarial QA review (Reviewer A)

Scope: `harness/compare.py`, `harness/capture.py`, `harness/run.py`, `harness/__init__.py`,
`harness/cases/hello-world.json`, and the three test modules. Contract reference: campaign
charter AC-2 (1)–(6). Framing is engine/testing QA only; single-operator laptop deployment,
so nothing here crosses a trust boundary and severities reflect impact on verdict correctness
and harness robustness, not exposure.

---

## F1 — Capture return code is ignored; a stale artifact can be judged as a fresh PASS (High)

**Where:** `harness/run.py:71-72` (and `harness/run.py:26-36`).

```python
capture(exe, case_path, out)                                   # return code discarded
artifacts[name] = json.loads(out.read_text()) if out.exists() else None
```

`run_case` never inspects the value returned by `capture` (`capture_subprocess` returns
`proc.returncode`, but the caller drops it). The verdict is derived *only* from whatever bytes
happen to sit at `out`. This is safe when the file is absent (→ `None` → `error`) or when the
capture wrote an error artifact for a Python-level exception (`capture.py:123-128`). It is
**not** safe when the capture process dies at the native level (numba/llvmlite segfault, OOM
kill, SIGKILL) *after* a previous invocation already left a valid artifact at that path.

**Failure scenario (concrete):**
1. Operator runs `python -m harness.run --cases ... --engine-a oracle-env/bin/python` with the
   default results dir (`REPO/results`, reused across invocations, not a tmp dir). Case
   `hello-world` passes; `results/hello-world/a1.json` … `b2.json` are valid artifacts.
2. Engine or a dependency is changed and a later run crashes natively inside `pr.reason()` for
   the `a1` capture — the subprocess exits non-zero **without** rewriting `a1.json`.
3. `capture_subprocess` swallows the non-zero return code; `run_case` sees `a1.json` still
   exists, loads the **stale** artifact from step 1, and judges the case from it.

The crash is invisible; the run reports `pass` (or a stale divergence) from data that no
current process produced. A hard harness/engine failure is thus laundered into a **false PASS**
— the worst failure mode named in the charter, and one the whole taxonomy exists to prevent.
The e2e test masks this because it passes a fresh `tmp_path` results dir (`test_oracle_vs_oracle_e2e.py:28`),
so the reused-directory hazard is never exercised.

**Suggested fix:** honor the return code — treat `capture(...) != 0` as a forced `error`
artifact for that run name regardless of file state; and/or delete `out` (and its `.log`)
before each capture so a crash can never leave a stale predecessor; and/or write every
invocation into a run-scoped fresh subdirectory. Recording the return code in the artifact/log
would also make native crashes diagnosable.

---

## F2 — In self-proof mode, same-engine non-determinism can be labeled `divergent` (Medium)

**Where:** `harness/run.py:50-59`, reached whenever `engine_b == engine_a` (the default,
`run.py:89`; the documented oracle-vs-oracle self-proof).

`judge_case` treats `a*` and `b*` as two *different* engines: it checks each pair for
reproducibility (`a1==a2`, `b1==b2`) and then compares `a1` vs `b1`; a cross-pair mismatch is
reported as `{"status": "divergent"}`. When `engine_a is engine_b` this is the *same* engine
run four times, so a cross-pair mismatch is by definition **same-engine irreproducibility**,
not a cross-engine finding.

**Failure scenario:** the oracle has a run-to-run non-determinism that settles to one of two
stable outputs per process (e.g. a numba parallel-reduction ordering that is consistent within
a process but varies between processes). By chance both `a`-runs land on ordering-1 and both
`b`-runs on ordering-2. Reproducibility passes for each pair; `a1 != b1` → verdict
`divergent`. The charter (4) is explicit that the third bucket "is never an engine finding,"
yet here a harness/environment non-determinism is announced with divergence vocabulary — the
exact misattribution the taxonomy forbids. The e2e test's own docstring ("reproducible against
itself") shows `divergent` is not even a meaningful label in this mode. Likelihood is low
(most non-determinism trips the `a1==a2` check first), but the taxonomy is structurally unable
to tell self-proof from cross-engine, so the label is wrong by construction when it does fire.

**Suggested fix:** when `engine_a == engine_b`, either fold the a/b comparison into the
reproducibility bucket (any mismatch among the four → `irreproducible`), or have `run.py` pass
a `self_proof` flag into `judge_case` so a cross-pair mismatch in that mode is reported as
irreproducibility, never divergence.

---

## F3 — Process exit code conflates an engine finding with a harness failure (Medium)

**Where:** `harness/run.py:110-112`.

```python
ok = all(v["status"] == "pass" for v in verdicts)
return 0 if ok else 1
```

The exit code is only `0` (all pass) / `1` (anything else); `2` is reserved for "no cases"
(`run.py:94`). So `divergent` (a genuine cross-engine finding), `irreproducible` (a harness
failure that is "never an engine finding"), and `error` (capture failed) all collapse to exit
`1`. Any operator or CI that keys off the exit code — the scriptable boundary — cannot tell
"the engines disagree" from "the harness broke," which is precisely the distinction charter (4)
demands and the whole repeat-pairing machinery is built to preserve. The status is present in
`report.json`, but the exit code is the contract most callers read first, and the repo rule
explicitly allows the `0/1/2` space.

**Suggested fix:** map the buckets onto the three exit codes so a harness failure never
masquerades as an engine finding — e.g. `0` all pass; `1` real divergence(s) with no
harness failures; `2` any `irreproducible`/`error` present (harness failure dominates). Keep
usage errors on `2` (or a distinct code) as today.

---

## F4 — Minimal subprocess env risks breaking / mis-representing the engine (Medium)

**Where:** `harness/run.py:32`.

```python
env={"PATH": "/usr/bin:/bin", "PYTHONHASHSEED": HASHSEED},
```

The capture subprocess inherits *nothing* else — no `HOME`, `TMPDIR`, `VIRTUAL_ENV`, or the
platform loader vars. pyreason pulls in numba/llvmlite, which write a compilation cache and
select a threading layer; those paths and thread backends are commonly driven by
`HOME`/`TMPDIR`/`NUMBA_CACHE_DIR`/`OMP_*`. Two hazards:

- **Breakage:** the engine may fail to start or to JIT under this stripped env, turning every
  case into `error`. Because the env is identical across all four runs it will not manufacture
  a *false divergence* (a saving grace), but it can block the self-proof entirely — and F3
  means that block reads as a plain non-pass rather than a harness failure.
- **Non-representativeness:** even when it works, the self-proof then proves reproducibility of
  the engine *in an environment no operator uses*, weakening the AC-2 (6) precondition it is
  meant to establish.

**Suggested fix:** pass through a curated set the engine actually needs (`HOME`, `TMPDIR`, and
a pinned `NUMBA_CACHE_DIR`/threading vars) on top of `PATH`/`PYTHONHASHSEED`, or derive the env
from a documented allowlist rather than a two-entry minimum. Whatever is chosen must stay
byte-identical across the four runs (it currently is) so reproducibility is not perturbed.

---

## F5 — `canonical`'s `str()` fallback can embed process-specific ids → false irreproducibility (Medium)

**Where:** `harness/compare.py:30` (`return str(value)`).

Any probe value that is not a str/number/bool/None/dict/list, is not interval-like
(numeric `.lower`/`.upper`), and has no callable `.item()` falls through to `str(value)`. For
an ordinary engine object that inherits the default `__repr__`, `str()` yields
`<Foo object at 0x104d04560>` — the hex is the object's memory address, which **varies per
process**.

**Failure scenario:** a supported probe returns such an object (e.g. `interpretation_dict`
nesting an internal engine type, or a DataFrame cell holding one — `run_probe` kinds
`interpretation_dict`, `filter_sort_*`). The canonical form differs between `a1` and `a2` (and
their digests differ) purely because of the address → `judge_case` reports
`irreproducible` for engine-a. That is a **false harness-failure verdict**: the engine is
deterministic; only the canonicalizer is leaking a process id. This misattributes
irreproducibility exactly as the charter warns against, and would block a self-proof for a
non-reason. The current `hello-world` probes happen to reduce to numbers/strings/lists, so it
is latent, not live — but the fallback is reachable through the declared probe surface.

**Suggested fix:** make the fallback deterministic and loud — e.g. reduce via a stable field
(class-qualified name + sorted `vars()`), or raise on an un-reducible type at *capture* time so
it surfaces as a schema/coverage gap rather than a phantom irreproducibility. At minimum, never
let a default `__repr__` (with its id) reach the digest.

---

## F6 — NaN/inf pass through unchecked: non-standard JSON and an exact-vs-tolerance split (Medium)

**Where:** `harness/compare.py:18` (float returned as-is) → `compare.py:33-35`
(`json.dumps(...)` with default `allow_nan=True`).

`canonical` returns floats verbatim, and `canonical_json` serializes with stdlib defaults, so
`NaN`/`inf` emit the tokens `NaN`, `Infinity`, `-Infinity` (verified) — which are **not valid
JSON**. Consequences:

- **Exact vs tolerance disagree on NaN.** The exact path compares `canonical_json` strings, so
  two NaNs both render `"NaN"` and are judged **equal**; the tolerance path
  (`approx_equal`, `compare.py:50-51`) computes `abs(NaN - NaN) <= tol` → `False` → **unequal**.
  The same pair of artifacts thus passes under an exact probe and diverges under a
  tolerance-policied probe — an internal inconsistency in the comparison seam.
- **NaN can be laundered into agreement.** If both engines emit `NaN` for a probe, the exact
  default reports `pass` (and same-engine repeats digest identically → reproducible), so a
  genuinely undefined result reads as engine agreement rather than being surfaced.
- Any downstream tool that strict-parses the preserved raw artifacts (`allow_nan=False`) will
  reject them.

**Suggested fix:** decide NaN/inf policy explicitly in `canonical` — map them to a sentinel
string (e.g. `"NaN"`/`"Infinity"`) or reject them at capture — so both comparison paths agree
and artifacts stay strict-JSON. If NaN must ever count as equal-to-itself, make `approx_equal`
honor the same rule the exact path implies.

---

## F7 — Dict keys collide after `str()` (Low)

**Where:** `harness/compare.py:21` — `{str(k): canonical(v) for k, v in value.items()}`.

If a probe returns a dict with keys that are distinct in Python but share a `str()` form
(e.g. `{1: "a", "1": "b"}` → `{"1": "b"}`, verified), one value silently overwrites the other.
Two structurally different engine outputs could then canonicalize to the same bytes (risking a
false "same"), or a single artifact could silently lose a key. pyreason's public-boundary
dicts are string-keyed today, so this is latent, but the reduction is lossy by construction.

**Suggested fix:** detect key collisions (raise, or key on a lossless encoding of `k`), or
restrict/validate that probe dicts are string-keyed at capture time.

---

## F8 — Duplicate case `id` across case files clobbers artifacts and verdicts (Low)

**Where:** `harness/run.py:64` (`case_dir = results_dir / case["id"]`), `run.py:74`,
`run.py:90` (directory glob).

The runner globs `*.json` and derives both the artifact directory and the report verdict from
the in-file `id`, not the filename. Two case files carrying the same `"id"` write into the same
`results/<id>/` tree (later run overwrites the earlier's `a1.json` …) and emit two report
verdicts with an identical `case_id`, silently masking one case behind the other.

**Suggested fix:** assert unique `id`s across the glob before running (fail fast on collision),
or namespace `case_dir` by the source filename.

---

## F9 — `comparison.default` is dead; a schema gap between case, capture, and judge (Low)

**Where:** `harness/cases/hello-world.json:40` (`"comparison": {"default": "exact"}`) vs
`harness/run.py:49` (`case.get("comparison", {}).get("probes", {})`).

`judge_case` reads only `comparison.probes`; the `comparison.default` key is never consulted.
It is harmless as written (default is already exact), but a future case setting
`"default": "tolerance"` would be **silently ignored** and compared exactly — a quiet policy
mismatch. Relatedly, capture stamps `"schema": 1` (`capture.py:99`) but no consumer validates
it, so a schema drift between capture and judge would pass unnoticed.

**Suggested fix:** either honor `comparison.default` in the judge or reject unknown
`comparison` keys so a mis-set policy fails loudly; and have `judge_case`/`run_case` assert the
artifact `schema` it expects.

---

## F10 — Error-path robustness: a corrupt artifact crashes the whole run; case-read errors misclassed (Low)

**Where:** `harness/run.py:65,72` and `harness/capture.py:120`.

- `run_case` calls `json.loads(out.read_text())` unguarded (`run.py:72`). A partially written
  artifact (capture killed mid-`write_text`) raises `JSONDecodeError`, which propagates out of
  `run_case`/`main` as an unhandled traceback instead of being judged `error` for that run —
  one bad file aborts the entire batch rather than failing a single case cleanly.
- In `capture.py`, `json.loads(args.case.read_text())` is *outside* the `try` (`capture.py:120`),
  so a malformed **case** file exits with an uncaught-exception code `1` — indistinguishable
  from the "engine failed inside" code `1` the module's own docstring reserves. A case-loading
  problem is a usage error (`2`), not an engine finding.

**Suggested fix:** wrap the per-artifact load in a narrow `except (OSError, ValueError)` → mark
that run `error`; move the case-file parse in `capture.py` under a guard that exits `2` on a
malformed/missing case.

---

## F11 — `numpy.float64` bypasses the documented `.item()` reduction (Low / nit)

**Where:** `harness/compare.py:16-18` vs the module docstring ("numpy scalars via `.item()`").

`numpy.float64` is a subclass of Python `float`, so it is caught by the `isinstance(value,
float)` branch (`compare.py:18`) and returned as-is rather than reduced through the `.item()`
path the docstring advertises (that path only catches non-float numpy scalars like `int64`,
`float32`). It still serializes identically for comparison, so this is a documentation/behavior
mismatch rather than a verdict bug — but the stated invariant ("engine objects are reduced")
is not literally true for `float64`, which is worth either fixing (call `.item()` first) or
correcting in the comment.

---

## Test-claim audit

The `proves:` docstrings were checked against what each test asserts. All are **accurate and
not overstated**:

- `test_compare_layer.py` — the six claims (interval/tuple reduction, dict-order-agnostic /
  list-order-sensitive digest, deterministic canonical JSON, tolerance forgives numeric-only
  drift, exact-by-default-tolerance-by-policy, missing-probe-is-a-mismatch) each match their
  assertions.
- `test_harness_runner.py` — pass / divergent-names-probes / irreproducible-is-not-divergence /
  error-carries-detail / four-captures-through-the-seam all assert exactly what they claim. The
  claims are honestly scoped: they cover the *injected* capture callable, so the real
  `capture_subprocess` (subprocess spawn + the F4 env construction) has **no fast-tier test** —
  a genuine coverage gap, though not a false claim.
- `test_oracle_vs_oracle_e2e.py` — `rc == 0` does entail reproducible repeats and stable
  digests over the seed corpus, so the claim holds. Note it necessarily runs in
  `engine_a == engine_b` self-proof mode, which is where F2 lives.

---

## Verdict

The comparison seam is clean, thin, and stdlib-only as the contract requires, and the judge's
bucket *ordering* (error → irreproducible → divergent → pass) is correct in the common
cross-engine case. The serious problems are at the edges the taxonomy is supposed to police:
**F1** can turn a native crash into a false PASS by trusting a stale artifact and ignoring the
capture return code — the single most important fix, because a false pass defeats the whole
harness. Around it, three Medium taxonomy/robustness gaps blunt the charter's core promise that
a harness failure is "never an engine finding": the self-proof can mislabel same-engine
non-determinism as `divergent` (F2), the process exit code cannot distinguish a finding from a
harness failure (F3), and the stripped subprocess env risks breaking or mis-representing the
very engine the self-proof certifies (F4). Two canonicalization Mediums (F5 process-id leakage,
F6 NaN handling) can each fabricate a wrong verdict on probe shapes already within the declared
surface. The Lows are latent lossiness and error-path sharp edges. None of this crosses a trust
boundary — it is a single operator on their own laptop — so every item is rated purely on its
effect on verdict correctness and harness reliability. Recommend addressing F1 before any
rewrite claim is allowed to lean on this harness, and F2–F6 before the self-proof is treated as
load-bearing.
