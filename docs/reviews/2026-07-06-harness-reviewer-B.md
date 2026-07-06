# Adversarial review — differential-testing harness (Reviewer B)

Target: `harness/{compare.py,capture.py,run.py,cases/hello-world.json}`, `tests/{test_compare_layer,test_harness_runner,test_oracle_vs_oracle_e2e}.py`, cross-checked against the pinned oracle public API `oracle/pyreason/pyreason/pyreason.py` (pin `e1a94af…`) and its `Rule`/`Fact`/`Output`/`Filter`/`Interpretation` internals.

Scope: try to break the harness — false passes, wrong verdicts, capture infidelity, test overstatement, repo-rule violations. No files were modified.

---

## F1 — `interpretation_dict` probe calls a method that does not exist at the pin (HIGH)

**File:** `harness/capture.py:61-62`

```python
if kind == "interpretation_dict":
    return interpretation.get_interpretation_dict()
```

The pinned oracle's `Interpretation` exposes **`get_dict()`**, not `get_interpretation_dict()` (`oracle/pyreason/pyreason/scripts/interpretation/interpretation_parallel.py:707`; `grep -rn get_interpretation_dict oracle/pyreason` returns nothing anywhere in the tree, and `pyreason.py` provides no module-level wrapper either). Any case that uses `"kind": "interpretation_dict"` raises `AttributeError` inside `run_probe`.

Because `run_case` is wrapped by a blanket `except Exception` (`capture.py:123`), that `AttributeError` is written into the artifact as `{"error": "AttributeError(...)"}`. All four runs (a1/a2/b1/b2) hit the identical failure, so `judge_case` returns `status: "error"` — a **broken probe surface is indistinguishable from a genuine engine crash**. The scaffolding is shipped but never exercised by the only committed case, so the defect is latent until the first author reaches for it.

**Failure scenario:** author adds a case probing the interpretation dict; harness reports `error` with an `AttributeError` and the operator burns time chasing a "capture failure" that is actually a wrong API call in the harness.

**Fix:** call `interpretation.get_dict()`; add a fast-tier test that constructs a stub with `get_dict` and asserts `run_probe` routes to it, so the probe surface is pinned to the oracle API. Better still, validate probe `kind` values against a known set at case-load time.

---

## F2 — A truncated/corrupt artifact crashes the whole runner instead of judging `error` (MEDIUM)

**File:** `harness/run.py:72`

```python
artifacts[name] = json.loads(out.read_text()) if out.exists() else None
```

The `out.exists() → None` path is handled by `judge_case` (missing artifact → `error`). But a file that **exists yet is not valid JSON** — a capture process killed mid-`write_text` (OOM / SIGKILL from numba, signal, disk-full) leaving a truncated file — makes `json.loads` raise `JSONDecodeError`. That exception is unhandled: it propagates out of `run_case`, out of the `main` list comprehension (`run.py:96`), and aborts the entire run. All remaining cases get **no verdict**, and the process exits via traceback (Python exit 1) — colliding with the "1 = a case did not pass" convention (`run.py:112`) while actually being an operational crash.

**Failure scenario:** a long corpus run; case 3's a1 capture is OOM-killed mid-write; the runner dies, cases 4..N never run, and the exit code looks like an ordinary "some case failed."

**Fix:** wrap the read in a try/except that maps a parse failure to a synthesized `{"error": "unreadable artifact: …"}` for that run name, so `judge_case` reports `error` for exactly that case and the run continues.

---

## F3 — NaN / ±inf pass through `canonical` unchanged: false digest collision + invalid JSON (MEDIUM)

**File:** `harness/compare.py:18-19`

```python
if isinstance(value, float):
    return value
```

Floats are returned verbatim, so `NaN`, `inf`, `-inf` survive into `canonical_json` → `json.dumps` (default `allow_nan=True`) emits the non-standard tokens `NaN`, `Infinity`, `-Infinity`. Two consequences:

1. **False pass via NaN collision.** `canonical_json(NaN) == "NaN"` regardless of provenance, so a probe leaf that is NaN in engine A (e.g. `0/0` in an annotation) and NaN in engine B (e.g. `inf-inf`) produce identical digests and compare **equal** under the exact path — two genuinely different computations judged the same.
2. **Inconsistent with the tolerance path.** For a probe under a tolerance policy, `approx_equal` computes `abs(NaN-NaN) <= tol` → `False`, so the *same* pair of NaNs is judged **divergent**. Whether a NaN equals a NaN now depends on whether the case names a tolerance — an incoherent verdict rule.
3. Artifacts on disk contain literal `NaN`/`Infinity`, which are invalid per the JSON spec; any non-Python consumer of `results/*.json` will reject them.

**Fix:** in `canonical`, map non-finite floats to a sentinel string (`"NaN"`, `"Infinity"`, `"-Infinity"`) so they are structurally distinct, comparable, and spec-valid — or reject them at capture time as an engine finding.

---

## F4 — int-vs-float distinction produces false *divergences* in exact mode (MEDIUM)

**File:** `harness/compare.py:33-35, 81`

Exact comparison is `canonical_json(a) == canonical_json(b)`, and `json.dumps` renders `1` as `"1"` but `1.0` as `"1.0"`. The oracle's own filter output *mixes* numeric types: an unmatched-but-present label is filled with the **int** literal `[0, 1]` while a matched label is the **float** `[bnd.lower, bnd.upper]` (`oracle/.../scripts/utils/filter.py:47-49`). A rewrite that normalizes all bounds to float (a natural, semantically-identical choice) will digest-differ from the oracle on every default-filled cell and be judged **divergent** despite computing the same interval.

**Failure scenario:** rewrite emits `[0.0, 1.0]` where the oracle emits `[0, 1]`; the judge reports `divergent` on `nodes-popular`; the operator opens an adjudication for a pure representation difference. This directly undermines the campaign's equivalence claim by manufacturing spurious findings.

**Fix:** decide whether numeric type is part of the contract. If not, normalize numbers in `canonical` (e.g. render integral floats and ints identically, or coerce all JSON numbers through a common form) so `1` and `1.0` share a canonical byte string; document the decision next to the ordering-is-contract note.

---

## F5 — Unknown/mistyped settings knobs are silently dropped (MEDIUM)

**File:** `harness/capture.py:72-73`

```python
for knob, value in inputs.get("settings", {}).items():
    setattr(pr.settings, knob, value)
```

`_Settings` is a plain (non-slotted) object. A real knob name routes through its `@property` setter (type-checked), but a **typo** (`"atom_traec"`, `"store_interp_changes"`) just creates a new instance attribute the engine never reads — no error, no warning. The case then runs with the *default* for the intended knob. Both engines are misconfigured identically, so they still agree → a **false pass relative to the case's stated intent**: the case claims to exercise `atom_trace` but silently does not.

**Failure scenario:** a case meant to prove trace-with-atoms equivalence has a knob typo; it passes green while actually testing the atom-trace-off path; a real divergence in the atom-trace path ships undetected.

**Fix:** validate each knob against the known settings names (introspect the `_Settings` properties) before `setattr`; unknown knob → capture exits usage/error rather than no-op.

---

## F6 — Harness/case-definition errors are laundered into engine "error" verdicts (MEDIUM)

**File:** `harness/capture.py:123-128`; `harness/run.py:44-47`

The blanket `except Exception` is intended to record *how the engine failed*, but it also swallows harness/author faults: a case missing `"probes"` or `"id"`, an unknown probe `kind` (`capture.py:63` raises `ValueError`), a malformed graph spec, etc. All become `{"error": repr(exc)}` and are judged with `status: "error"` — the same bucket as a genuine engine crash. The exit taxonomy (`run.py` docstring: pass / divergent / irreproducible / error) has **no "invalid case / usage" state**, so a broken case definition and a real engine failure are indistinguishable.

**Fix:** validate the case schema (id, probes present and non-empty, known kinds, known settings) *before* `run_case`, and exit usage (2) on schema violations so authoring bugs never wear the engine-failure label.

---

## F7 — Dict keys are stringified: silent collision and data loss (MEDIUM)

**File:** `harness/compare.py:21`

```python
if isinstance(value, dict):
    return {str(k): canonical(v) for k, v in value.items()}
```

`str(k)` maps distinct keys onto the same string. `{1: "a", "1": "b"}` canonicalizes to a single `"1"` entry whose value depends on iteration order — **one entry is silently dropped and the digest collides** with a genuinely different map. Edge components in the oracle are tuples (`filter.py:112`), and `get_dict` mixes int time-keys with string node-keys across nesting levels; a node literally named `('a', 'b')` and an edge tuple `('a','b')` both stringify to `"('a', 'b')"`. Two different interpretations can thus share a digest.

**Fix:** reject non-string keys (raise) or encode key type into the canonical key (e.g. prefix by type), so key identity is preserved and collisions become impossible rather than silent.

---

## F8 — Probe-less / vacuous cases are reported as `pass` (MEDIUM)

**File:** `harness/run.py:39-60`; schema has no minimum

A case with `"probes": []` yields empty `probes`/`digests` on all four runs; reproducibility holds trivially, `compare_probes({}, {})` returns `[]`, and the verdict is `pass`. The runner asserts nothing about a case actually observing engine behavior — indeed `tests/test_harness_runner.py:63` drives a `"probes": []` case straight to `pass`. A corpus can be green while proving nothing.

**Failure scenario:** an author scaffolds a case, forgets the probes, sees green, and banks a false equivalence signal.

**Fix:** reject cases with zero probes at load time (usage error); optionally require `inputs` to be non-empty.

---

## F9 — Bare capture process mutates the read-only oracle tree and pollutes the first log (MEDIUM)

**File:** `harness/run.py:29-36`; oracle `pyreason/__init__.py:4-7, 22-46`

The oracle's `__init__` sets `os.environ['NUMBA_CACHE_DIR']` to a path **inside the package** and, on first import, runs a warmup reason() and rewrites `.cache_status.yaml` — but only guards that write with `'pytest' not in sys.modules` (`__init__.py:42`). The harness invokes capture as a **bare `python -m harness.capture`** subprocess (`run.py:31`), so `pytest` is *not* in that process's modules and the guard does not fire: the first capture writes `.cache_status.yaml` and numba cache artifacts into the package directory. If `oracle-env` installs `oracle/pyreason` as an editable/develop install, those writes land **in the read-only oracle tree**, violating the campaign's "never modify `oracle/pyreason`" hard rule — triggered silently by the harness, not by an operator edit. Additionally, the first-run warmup prints "Imported PyReason for the first time…" only into `a1.log`, so `a1.log`/`a2.log` diverge (harmless to the verdict since logs aren't compared, but confusing during diagnosis).

**Fix:** point `NUMBA_CACHE_DIR` (and a cache-status equivalent) at a scratch dir via the subprocess `env` in `capture_subprocess`, and confirm `oracle-env` is a non-editable install so nothing can write into `oracle/pyreason`. Pre-warm the cache once before the differential run so no verdict-bearing capture pays the init cost or emits init stdout.

---

## F10 — `output_to_file` writes uncaptured, timestamped files and redirects stdout (MEDIUM)

**File:** `harness/capture.py` (no handling); oracle `pyreason.py:1513-1514, 1541-1542`

If a case sets `"settings": {"output_to_file": true}`, `reason()` executes `sys.stdout = open(f"./{output_file_name}_{timestamp}.txt", "a")` in the capture's cwd (`REPO`). That file is **never captured as a probe, never compared, and never cleaned up**; its name embeds `%Y%m%d-%H%M%S`, so each of the four runs writes a *different* file. This is a captured-too-little hole (engine output that could distinguish A from B is discarded) and it litters the repo root. The stdout redirect also means anything the engine prints after `reason()` bypasses the `.log` capture in `run.py:35`.

**Fix:** either forbid `output_to_file` in cases (validate and reject) or force it off in capture; if file output must be tested, treat the written file as a first-class probe with a deterministic name and compare its contents.

---

## F11 — Reproducibility check ignores the tolerance policy (LOW)

**File:** `harness/run.py:50-53`

Same-engine reproducibility is `artifacts[r1]["digests"] != artifacts[r2]["digests"]` — an **exact** digest comparison that never consults the case's `comparison.probes` tolerance. A case that legitimately needs a tolerance (an engine with within-epsilon nondeterminism) can therefore *never* clear the reproducibility gate: `a1` vs `a2` will digest-differ and be judged `irreproducible` before divergence is even considered. This may be intended strictness, but it means the tolerance policy is dead for any engine that isn't bit-identical to itself.

**Fix:** decide and document whether reproducibility honors tolerance; if it should, run the same `compare_probes(..., policy)` for the repeat pair instead of raw digest equality.

---

## F12 — Duplicate case `id` clobbers artifacts on disk (LOW)

**File:** `harness/run.py:65`

`case_dir = results_dir / case["id"]`. Two case files sharing an `id` write to the same directory; the second run overwrites the first's `a1..b2.json` and `.log`. Verdicts are computed from in-memory artifacts so the *report* still lists both, but the on-disk artifacts only reflect the last case — diagnosis of the first case is impossible. There is no duplicate-id detection.

**Fix:** detect duplicate ids across the glob and exit usage(2), or namespace the results dir by case file path.

---

## F13 — `.item` / interval duck-typing is fragile and lossy (LOW)

**File:** `harness/compare.py:24-30`

- `getattr(value, "item", None); if callable(item): canonical(item())` — any object with a **callable `.item`** is assumed to be a scalar reducer. A pandas `Series`/`Index` or a multi-element `numpy.ndarray` has `.item()` that *raises* `ValueError` when not size-1; that exception surfaces as a capture `error`. An object whose `.item` means something else entirely is silently misreduced.
- The interval branch reduces **any** object exposing numeric `.lower`/`.upper` to `[lower, upper]`, discarding all other state. A non-interval object that happens to carry those attributes collides with a real interval.
- The final `return str(value)` (`:30`) is a canonicalization collision generator: two distinct objects with equal `str()` produce equal digests (false pass), while an object with a default `<Cls at 0x…>` repr makes the *same-engine* repeat look `irreproducible` (address varies per process).

**Fix:** reduce only known types explicitly (import-free protocols keyed on attribute *and* a type marker); make the `str()` fallback a hard error at capture time so unhandled types are caught, not silently digested.

---

## F14 — Usage-class errors exit via traceback, not code 2 (LOW)

**File:** `harness/run.py:65, 90-91`; `harness/capture.py:120`

- `run.py`: a `--cases` path that is neither a dir nor an existing file yields `[args.cases]`; `run_case` then `case_path.read_text()` raises `FileNotFoundError` → uncaught traceback (Python exit 1), not usage(2).
- `capture.py:120`: `json.loads(args.case.read_text())` is **outside** the try; a missing or malformed case file → uncaught traceback (exit 1), not usage(2).

Both contradict the stated "2 = usage" convention (both module docstrings).

**Fix:** stat/read the case file inside guarded code and return 2 on missing/invalid input.

---

## F15 — Both-engine irreproducibility masks engine B (LOW)

**File:** `harness/run.py:50-53`

The loop returns on the first irreproducible engine, so when *both* A and B are irreproducible only `engine-a` is reported. The operator fixes A, reruns, and only then discovers B is also unstable.

**Fix:** collect both and report the set, or at least note "engine-b also irreproducible."

---

## F16 — Capture subprocess env is stripped of HOME/TMPDIR (LOW)

**File:** `harness/run.py:32`

`env={"PATH": "/usr/bin:/bin", "PYTHONHASHSEED": HASHSEED}` drops everything else, including `HOME` and `TMPDIR`. `PYTHONHASHSEED=0` is correctly pinned (good), but libraries in the engine stack that fall back to `HOME`/`TMPDIR` for scratch or config can behave differently or fail under this minimal env. Determinism of the *reasoning* is not obviously at risk, but robustness is.

**Fix:** start from a copy of the parent env and override only `PYTHONHASHSEED` and the cache dirs, rather than whitelisting two variables.

---

## F17 — Engine identity is captured but never asserted (LOW)

**File:** `harness/capture.py:101-107`; `harness/run.py:39-60`

Each artifact records `engine.pyreason`, `python`, `platform`, `executable`, and `PYTHONHASHSEED`, but `judge_case` looks only at `probes`/`digests`. Nothing verifies that a1/a2 (or b1/b2) actually ran the same interpreter, or that `PYTHONHASHSEED` was really `0` in the captured process, or that A and B are the engines the operator intended. The self-describing metadata is decorative to the verdict.

**Fix:** in `judge_case`, assert the paired runs share `engine.executable` and `env.PYTHONHASHSEED`, and surface a mismatch as a harness/environment error.

---

## Test honesty

### F18 — `test_canonical_json_is_deterministic` overstates what it proves (MEDIUM)

**File:** `tests/test_compare_layer.py:33-37`

```python
def test_canonical_json_is_deterministic():
    """proves: the canonical JSON of a nested value is byte-stable across calls,
    the property digest tripwires rely on."""
    value = {...}
    assert canonical_json(value) == canonical_json(value)
```

It calls `canonical_json` twice on the **same object in the same process** — proving only idempotency. The property the tripwires actually depend on is **cross-process** byte-stability (the four captures are independent interpreters), where the real hazards live: `PYTHONHASHSEED`-dependent `dict`/`set` iteration order and the `str()`/`str(k)` fallbacks (F7, F13). This test cannot observe any of those — notably it never exercises `canonical` on a `set` (whose reduction is `str(set)`, order-unstable across seeds). The docstring's "byte-stable across calls … the property digest tripwires rely on" is stronger than the assertion.

**Fix:** either downgrade the claim to "idempotent within a process," or add a test that reduces a `set`/unordered structure and asserts a stable canonical form, and a cross-process (subprocess) digest-stability test that pins the real guarantee.

### Other tests — accurate

- `test_compare_layer.py` F19-tier claims (interval/tuple reduction, dict-order-vs-list-order, approx tolerance bounds, exact-by-default-tolerance-by-policy, missing-probe) match their assertions.
- `test_harness_runner.py` pass/divergent/irreproducible/error and the seam test are honest; the seam test correctly proves capture ordering `["pyA","pyA","pyB","pyB"]`. (It does not exercise the missing-artifact `None` path or a real capture — not overstated, but that path is untested; combined with F2 the failure-read path has no coverage.)
- `test_oracle_vs_oracle_e2e.py` honestly proves oracle self-reproducibility over the (single-case) "seed corpus"; note that with `--engine-a` only, `rc==0` proves reproducibility (A==A) and cannot prove any cross-engine property, which the docstring correctly limits itself to.

---

## Capture-fidelity spot-checks that are CORRECT (no finding)

- `Rule(rule["text"], rule.get("name"), rule.get("infer_edges", False))` (`capture.py:83`) matches the pin's positional signature `Rule(rule_text, name=None, infer_edges=False, …)`.
- `Fact(text, name, start=0, end=0, static=False)` (`capture.py:87`) matches `Fact(fact_text, name=None, start_time=0, end_time=0, static=False)`.
- Settings are applied **before** `load_graph`/`reason` (`capture.py:72` precedes `:78`,`:91`), which is required because `graph_attribute_parsing`/`static_graph_facts` are read inside `load_graph` and `atom_trace`/`store_interpretation_changes` inside `reason`.
- `get_rule_trace(...)[0]`/`[1]` correctly index the (node_df, edge_df) tuple; the atom-trace clause columns hold **ordered** `list(qn[j])` (numba `ListType`, `interpretation_parallel.py:99`), so list order is deterministic within a fixed seed.
- `dataframe_to_plain` dropping the DataFrame index is benign for these probes specifically, because both `filter_and_sort_*` and `get_rule_trace` return frames on a fresh `reset_index()` RangeIndex.

---

## Verdict

The harness's pure core (`compare`/`judge`) is small and mostly sound, and the separation of reproducibility from divergence is the right shape. But it is not yet trustworthy as an equivalence oracle. One shipped probe calls a method that does not exist at the pin (F1); a truncated artifact takes down the entire run rather than judging one case `error` (F2); and the canonicalization layer has several collision/data-loss vectors — NaN/±inf passthrough (F3), stringified dict keys (F7), and the `str()`/`.item`/interval duck-typing fallbacks (F13) — any of which can make two different behaviors share a digest. Against the campaign's actual goal, the most corrosive issues are the ones that manufacture **spurious verdicts**: int-vs-float exact-mode false divergences (F4) will generate needless adjudications, while silently-dropped settings (F5), vacuous probe-less passes (F8), and case-error laundering (F6) let a case go green while proving less than it claims. The suite is largely honest, but `test_canonical_json_is_deterministic` (F18) asserts in-process idempotency while claiming the cross-process stability the tripwires truly rely on — and that cross-process property, plus the missing-artifact read path, is exactly what is untested. None of these require an engine to reproduce; they are demonstrable from the harness and the pin alone. Recommend addressing F1–F4 and F18 before the harness is used to bank any equivalence claim.
