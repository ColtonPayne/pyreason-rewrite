<!-- doccode: pyreason-rewrite-docs-reviews-phase4-spike-review -->
# Session-28 independent review — the four-optimization grounding-kernel spike + options memo

- Session: 28 (review pass, 2026-07-12); author report:
  [2026-07-12-phase4-spike-author.md](2026-07-12-phase4-spike-author.md)
- Scope reviewed: commits `c56d238` (K3), `c218f45` (K1), `958523a` (K2),
  `ca600a3` (K4), `b89d318` (baselines section, options memo, author
  report). No shared context with the author; every claim below is
  re-derived from the pinned source, the raw reports, or a fresh run.
- Review stance: adversarial — the failure mode hunted was an
  optimization that changes an observable the sampled cases happen not
  to exercise (grounding order, trace order, memo staleness against
  interim mutation, label identity aliasing).

## Verdict

**Approved with fixes.** All four optimizations are semantically safe
against the pinned source; the equivalence rerun (fast tier, ladder 3,
a 20-case stratified sample with four reviewer-chosen swaps) is ALL
PASS; the memo's numbers re-derive exactly from the raw reports except
one rounding slip (1.46× → 1.47×, fixed in three documents); one
coverage gap is closed with a committed fast-tier seam test pinning
K1's lazy-TypeError shape.

## 1. Semantic review, per optimization

### K3 — memoized node-arm per-head clause re-check (`c56d238`) — SAFE

The claim to falsify: `check_all_clause_satisfaction` is loop-invariant
across a node rule's head-grounding loop. Verified against the pinned
node arm (oracle interpretation.py:955-1063) and the rewrite's
(`_interpretation.py:1176-1275`), line by line:

- The check's arguments (`groundings`, `groundings_edges`, the two
  interpretation maps, `clauses`, `thresholds`, `cwp`) are never
  mutated inside the loop. The loop body only *reads* groundings and
  worlds (trace/annotation collection builds fresh lists).
- The one mutation in the loop — `_add_node` (rewrite line 1271, pin
  line 1059) — is reachable only when `add_head_var_node_to_graph` is
  set, and that arm *always* forces `groundings[head_var_1] =
  [head_var_1]`, a single-element list: the loop runs exactly once, so
  there is no second iteration to observe the mutation. A head-function
  grounding (the multi-element path) sets `groundings[head_var_1]`
  BEFORE the loop, which keeps the add flag False.
- `check_all_clause_satisfaction` itself is pure (read directly:
  `_grounding.py:179-204` builds fresh qualified lists, mutates
  nothing).
- Order: no event is reordered — the memo replaces N identical boolean
  computations with one; trace rows are appended in the same iteration
  order. `satisfaction`'s post-loop value is not consumed (verified:
  `_ground_rule` returns the applicable-rules lists and nothing reads
  `satisfaction` after the head loop).
- Lifetime: `head_check` is a `_ground_rule` local — rebuilt on every
  grounding call, so fixpoint iterations, timesteps, `reason_again`,
  and `reset()` can never see a stale value by construction. Both
  engines (`reason` line 625, `reason_fp` line 908) share this one
  `_ground_rule`, so the fp engine inherits the same analysis
  (exercised by `fp-version-on` in the review sample).
- The edge-rule arm is untouched (its per-pair `temp_groundings`
  genuinely differ per iteration — memoizing there WOULD diverge; the
  author correctly left it alone).

### K1 — lazy-cached `Label.__hash__` (`c218f45`) — SAFE (probe banked as a test)

- Mutability: `_value` is assigned exactly once, in `__init__`
  (repo-wide grep: no setter, no other assignment, no `__slots__`
  conflict, no pickle/deepcopy of Labels anywhere in `src/`), so the
  cached hash can never go stale within a process. Labels are not
  serialized across processes by any engine path (the pinned Label is
  the same shape: plain class, hash-by-`str(self)`).
- The TypeError shape: probed the oracle's plain label class
  (`oracle/pyreason/pyreason/scripts/components/label.py`, exec'd
  read-only) against the rewrite with `Label(3)`: both construct
  silently and raise `TypeError("__str__ returned non-string (type
  int)")` on the FIRST **and** SECOND `hash()` call — the lazy cache
  does not memoize the failure into a different second-call observable
  (the raise happens before `_hash` is assigned, so it stays `None`).
  Banked as fast-tier test
  `test_label_nonstring_value_raises_typeerror_at_every_hash_never_at_construction`
  (tests/test_rewrite_value_types.py) — the one K-shaped observable no
  existing test pinned.
- B27's eq raise (`Label == str` → AttributeError before the isinstance
  guard) is untouched code; probe confirmed byte-identical message both
  sides. Hash-equal-by-value across distinct objects unchanged.
- Residual (named, not a finding): the cache adds a private `_hash`
  attribute to instances; the pin's instances carry only `_value`.
  Attribute-shape introspection (`vars()`) is not on the campaign's
  observable surface (harness compares program outputs), and no engine
  or accessor path reads `__dict__`.

### K2 — hoisted qualified-grounding scans + lazy sets + one-lookup static check (`958523a`) — SAFE

Three sub-changes, each checked separately:

- **Hoisted scans** (`_grounding.py:72-119`): the open-world fast path
  inlines exactly `World.is_satisfied` (`_world.py:26-33`:
  `self._world[label] in bnd`) with `Interval.__contains__`
  (`interval.py:104-105`: `self._lower <= item.lower and self._upper >=
  item.upper`) — the hoisted comparison `bnd_lower <= w._lower and
  bnd_upper >= w._upper` is the identical predicate (the `lower`/`upper`
  properties are bare reads of `_lower`/`_upper`). The `except
  (KeyError, AttributeError)` arm matches `is_satisfied_node/edge`'s
  guard, including the bare-KeyError raise shape of
  `TypedComponentDict.__missing__` (caught to False in both). The
  closed-world arm and the `None`-label/bound arm delegate to the
  original per-candidate path unchanged. The `available`-quantifier
  re-qualification under `interval.closed(0,1)` flows through the same
  hoisted path with the same result (any present label bound is inside
  [0,1]). Order: candidate iteration order and result list order are
  unchanged — grounding order is trace-row order downstream, and the
  scan preserves it.
- **Lazy `nodes_set`/`edges_set`** (`_interpretation.py:1069-1074`):
  every consumer enumerated by grep — lines 1083/1116/1118 (`nodes_set`,
  all guarded by `allow_ground_rules`), 1112 (`edges_set`, guarded by
  `allow_ground_rules`), 1320 (`edges_set`, edge-rule head pairing,
  guarded by `rule_type == 'edge'` structurally). The build conditions
  cover exactly these guards, so the empty-tuple placeholder is
  unreachable as a membership subject. Crucially this is NOT
  deferred-to-first-use laziness: both sets are still built at
  `_ground_rule` entry (just conditionally), so the membership snapshot
  is taken at the same point as the pin — `infer_edges` additions
  between grounding calls land in the next call's snapshot in both
  engines. The silent-failure risk (a missed consumer reading `()` and
  treating membership as False) is what the enumeration rules out, and
  `rule-from-csv-basic` (the infer-edges case that writes inferred
  edges into the edge trace) passes in the review sample.
- **`_apply_fact` one-lookup static check** (`_interpretation.py:358-363`):
  `.get(l)` vs membership-plus-lookup — world values are always
  Intervals (never None; `_world.py:20` and every update path), and
  `recorded` binds the same object the old double lookup returned (no
  mutation between). `interpretations[comp]` still raises the same bare
  KeyError first in both shapes.

### K4 — canonical Label per attribute string in the loader (`ca600a3`) — SAFE

- Label is immutable on every surface (K1 review above), so aliasing
  one object across `specific_node/edge_labels` keys, `_GraphFact`
  labels, world-dict keys, and trace rows cannot leak state. Equality
  and hash are by string value; the pin's per-occurrence objects and
  the rewrite's shared object are indistinguishable to every dict,
  sort, filter, and trace-serialization consumer (trace output renders
  the label's string; repo-wide grep found no identity (`is`/`id()`)
  check on labels anywhere in `src/`, and no public accessor exposes
  object identity).
- Note the pin itself already shares ONE object per distinct string as
  the `specific_labels` dict key (setdefault keeps the first) — K4
  extends the sharing to the graph facts; no new *kind* of aliasing is
  introduced.
- Scope: the cache is per-`parse_graph_attributes` call (per load), so
  no cross-load retention.

## 2. Targeted counter-evidence — the review sample (20 cases)

The author's 16-case stratification covered the touched seams but had
three gaps this review judged sharper cases for; the sample was
extended by four (author's 16 kept intact):

| added case | what it hunts |
|---|---|
| `rule-from-csv-basic` | the ONLY infer-edges case in the corpus: edges added mid-run must land in the next grounding snapshot (K2's conditional `edges_set` build; K3's memo across re-grounding after graph mutation) |
| `persistent-off` | clause satisfaction that CHANGES across timesteps (bounds reset each step; fires at t, not at t+1) — the memo-staleness shape, cross-timestep |
| `fp-version-on` | the fp engine's re-grounding through the SAME memoized `_ground_rule` (fp-counter values, event order, duplicated atom-trace groundings are the case's pinned observables) |
| `save-rule-trace-clause-reorder` | trace/clause-map ordering on a non-identity clause reorder — ordering is contract, and K2/K3 touch the loops that feed the rows |

A confirmation that ordering is actually judged, not assumed: the
harness canonicalization states and implements "ordering within lists
is part of the compared value" (`harness/compare.py`), so every trace
probe in the sample pins event order.

- **Fast tier:** `uv run pytest -m "not e2e"` — **289 passed** (author's
  288 + the K1 seam test added by this review).
- **Ladder 3:** `harness.run` oracle-vs-rewrite on
  perf-ladder-{small,medium,large}, `PYTHONHASHSEED=0` — **ALL PASS (3)**.
- **20-case sample:** oracle-vs-rewrite via `harness.run`,
  `PYTHONHASHSEED=0` — **ALL PASS (20)**, including all four
  reviewer-added cases.

## 3. Perf spot-check (sampled, per the review budget)

One control repeat per claim (`harness.bench`, fresh process,
`PYTHONHASHSEED=0`, idle machine, raw reports in
`results-phase4-baselines/review-spot-{large,medium}-2026-07-12/`):

| rung | review spot (reason()) | author band (n=7) | verdict |
|---|---|---|---|
| large | **1.222 s** | 1.226 (1.224…1.240) | 0.002 s below the band's low edge — reproduces the claim (0.3% off median; the banked band itself spans 1.4%) |
| medium | **0.151 s** | 0.151 (0.151…0.153) | on the median exactly |

The headline post-spike numbers are reproducible, not artifacts of the
author's session.

## 4. Numbers audit (raw reports → memo/report/baselines tables)

Re-derived every headline number from
`results-phase4-baselines/{rewrite-postspike,rewrite-baselines,oracle-baselines}-2026-07-12/bench-report.json`
(medians, min…max over n=7 `reason_s`; RSS from `maxrss_bytes`;
cold-start = `import_s + reason_s` on small):

- large: post 1.2262 (1.2235…1.2403) / pre 18.7916 (18.1239…18.9399) /
  oracle 17.9772 (17.1782…18.5237) → pre/post 15.32×, oracle/post
  14.66× — **matches** "1.226 (1.224…1.240)", "15.3×", "14.7×"; all
  three bands disjoint as claimed.
- medium: 0.1512 (0.1506…0.1526) vs 0.6546 → 4.33× — **matches**.
- small: 0.0028 vs 0.0041 → **1.4668×** — the docs said "1.46×";
  correct rounding is **1.47×**. Fixed in the baselines table, the
  memo, and the author report (the one number that did not re-derive
  as printed; sub-1% and direction-neutral, but precision is the
  banked discipline).
- cold-start small: 0.0667 vs oracle 4.3761 (**matches** 0.067 / 4.376;
  ~65× re-derives at 65.3×); large RSS 67.1 (66.6…68.7) vs oracle 328.6
  (**matches**; 4.9× re-derives).
- Profile: the banked post-spike profile
  (`results-phase4-profile/rewrite-postspike-2026-07-12/perf-ladder-large-profile.txt`)
  shows profiled reason 3.168 s; `reason` loop body 23.6% self;
  `_ground_rule` 25.4% cum; `_update_component` 9.6% self / 23.8% cum;
  `_apply_fact` 8.0% / 15.9%; `Label.__hash__` 4.7% self / 2,757,687
  calls (2.76M); `Label.__eq__` 2.4% / 289,644 (0.29M) — **every
  profile number in the author report and memo matches the artifact**.
  Amdahl check: 1/(1−0.254) = **1.34×** — the memo's C1 ceiling is
  arithmetic, not assertion.

## 5. Memo review (`docs/perf/execution-layer-options.md`)

- Three options, numbers attached to each, exactly one recommendation
  (B). Option A honestly framed as strictly dominated; Option C split
  into C1/C2/C3 with a named dependency ask per sub-option; C2 names
  the AC-5.5 numba interpreter-version ceiling and the re-inherited
  compile floor (≈3.0 s per reason(), ≈1.4 s import — both figures
  match the banked oracle decomposition). The closing operator question
  is a single crisp fork.
- Overclaim check: the 14.7× is presented in a table whose header is
  "rung, reason()" and the prose ties it to the large rung — it is not
  sold as end-to-end. The end-to-end-adjacent claims (cold-start, RSS)
  carry their own measured numbers with the correct tie verdicts. The
  session-27 large-rung tie → win transition is stated with disjoint
  bands, which the raw reports confirm.
- One stale-by-events note, not a fix: the memo and baselines cite
  "fast tier 288 passed" — true at authoring; the count is 289 after
  this review's added test. Left as written (it records the author's
  evidence, and the review's own count is recorded here).

## Fixes applied by this review

1. `1.46×` → `1.47×` in `docs/perf/rewrite-baselines.md`,
   `docs/perf/execution-layer-options.md`,
   `docs/reviews/2026-07-12-phase4-spike-author.md` (rounding of
   1.4668).
2. Added fast-tier seam test pinning K1's lazy-TypeError shape
   (`tests/test_rewrite_value_types.py`): construction never raises;
   every `hash()` call raises the pinned TypeError; the cache cannot
   convert a first-hash failure into a changed second-hash observable.

## Reproduction

```
# fast tier (289):
uv run pytest -m "not e2e"
# ladder 3 (stage perf-ladder-*.json into a dir, then):
PYTHONHASHSEED=0 uv run python -m harness.run --cases <ladder-dir> \
  --engine-a oracle-env/bin/python --engine-b scripts/rewrite-python \
  --results <results-dir>
# 20-case sample: stage the 16 author cases + rule-from-csv-basic,
# persistent-off, fp-version-on, save-rule-trace-clause-reorder; same command.
# perf spot-checks (single control repeat each):
PYTHONHASHSEED=0 uv run python -m harness.bench --engine scripts/rewrite-python \
  --cases harness/cases/perf-ladder-large.json --repeats 1 --tag review-spot-large
PYTHONHASHSEED=0 uv run python -m harness.bench --engine scripts/rewrite-python \
  --cases harness/cases/perf-ladder-medium.json --repeats 1 --tag review-spot-medium
```
