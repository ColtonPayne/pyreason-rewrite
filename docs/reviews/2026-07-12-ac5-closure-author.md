<!-- doccode: pyreason-rewrite-docs-reviews-2026-07-12-ac5-closure-author -->
# Session 33 — author report: the decision lands, the AC-5 closure audit, and the oracle-env cache re-baseline

- session: 33 · date: 2026-07-12 · author agent
- packet: (1) record the operator's execution-layer decision; (2) ADR 0004;
  (3) the AC-5 closure audit, all five bars, mechanized evidence; (4) the
  operator-approved oracle-env numba-cache re-baseline (session-29 review §F2)
- verdict: **all five AC-5 bars GREEN** (two closed by small fast-tier
  additions inside this packet; the rest verified as already standing);
  **the cache re-baseline is banked and the F2 quirk is gone**
  (0 harness references, 101/101 indexes unpickle in a bare context,
  15-case stratified sample ALL PASS with banked-artifact digest identity).
- fast tier: **330 passed, 6 deselected** at every commit (321 at session 32,
  +7 from the post-session-32 Pokec-rig commits `bae3a5f`/`1d72d23`, +2 this
  packet). Oracle pin byte-clean at `e1a94af3` before and after everything
  below.

## 0. The decision of record (packet items 1–2)

The operator signed **Option B** on 2026-07-12: the campaign ships the
pure-Python core with the session-28 optimizations; the C-track closes
unopened. Recorded in two commits:

- `370875b` — [ADR 0004](../adr/0004-execution-layer-pure-python-core.md):
  the options with their measured numbers (cited from the banked
  session-27/28 baselines, not re-measured), the decision, the evidence of
  record (the session-32 boundary sweep 116/116 as the verdict-of-record of
  the chosen layer; the Pokec addendum's ~101× real-scale point), the
  **AC-5.5 version-headroom statement**, and the neighborhood-scoped-grounding
  headroom seed explicitly deferred with its equivalence-proof burden named.
- `af8a8cf` — the memo
  ([docs/perf/execution-layer-options.md](../perf/execution-layer-options.md))
  gains its "Decision (operator, 2026-07-12)" section pointing at the ADR.

One honesty note carried into the ADR: the packet's shorthand "zero runtime
dependencies" is stated exactly there — the shipped package's runtime surface
is **two pure-Python libraries** (`networkx>=3.6.1`, the pinned public API's
graph input type; `pyyaml>=6.0.3`, the pinned YAML loader parity) and nothing
else; zero JIT/compiled/version-sensitive dependencies. Claiming literal zero
would not have survived `grep "^import\|^from" src/pyreason/*.py`.

## 1. The AC-5 closure audit — five bars, mechanized

Charter reference: AC-5 ("the redesign clears its maintainability bars —
mechanized, not vibes"), bars 1–5. For each: the check, the evidence, the
verdict. Two bars needed work inside this packet (3 and 4 — one coverage gap
closed, one convention mechanized); commit `be800fb` carries both.

### Bar 1 — one engine: GREEN

**Check:** a single reasoning-core implementation; no second core in the
tree; acceleration seam status stated honestly.

- Exactly one grounding/semantics core exists:
  `grep -rn "def _ground_rule" --include="*.py" src harness tests tools scripts`
  → one hit, `src/pyreason/_interpretation.py:1036`. The shipped package has
  exactly one interpretation module (`ls src/pyreason/ | grep -ci interpretation`
  → 1; semantics core `_interpretation.py` 1897 lines + `_grounding.py`
  356 lines of pure helper functions), against the pinned oracle's three
  near-copy ~2400-line variants (the named anti-goal). The one pinned-forced
  branch is the two *schedule* functions (`reason` / `reason_fp`) over the
  same semantics helpers — ADR 0003's adjudicated shape, output-forced, with
  no semantic body duplicated.
- **Acceleration seam status: none exists.** Mechanized:
  `grep -rniE "import (numba|numpy|cython|cffi)|from (numba|numpy|cython|cffi)" src/pyreason/`
  → 0 matches; `ctypes` likewise 0. With Option B signed, the single core is
  the only execution path, so the charter's accelerated-vs-fallback **parity
  case family stays vacuously satisfied** — per the charter's own wording it
  becomes a live obligation only with the first acceleration seam, and
  building it speculatively is the dead scaffolding the charter forbids. No
  parity scaffolding exists in the tree, which is the honest state.

### Bar 2 — no hidden cross-run state: GREEN

**Check:** the module-global facade wraps explicit, resettable state; a
harness case family proves sequential programs in one process are
independent.

- The facade holds exactly one `EngineState`
  (`src/pyreason/__init__.py:35`, ADR 0001) and every public function
  delegates to it; fast tier: `test_engine_states_are_independent`,
  `test_facade_delegates_to_its_one_state`,
  `test_facade_fresh_state_accessors`
  (tests/test_rewrite_state_loaders.py) plus the 14 lifecycle seam tests
  (tests/test_rewrite_state_lifecycle.py).
- **The case family: the 13 lifecycle/sequential-independence cases** —
  `accessors-fresh-state`, `accessors-lifecycle`,
  `annotation-fn-reset-clears`, `head-fn-reset-clears`,
  `reason-again-no-program`, `reason-again-restart-false`,
  `reason-again-restart-true`, `reason-bare-again-no-facts`,
  `reset-no-program`, `reset-rules-no-program`, `reset-rules-with-program`,
  `reset-settings-restore`, `reset-with-program`. `reset-with-program` runs
  reason → reset → reason → reason in ONE capture process — two sequential
  programs in the same interpreter, banked cross-engine. **Current status:
  all 13 `pass` in the sweep of record**
  (`results-phase4-boundary/report.json`, session 32, 116/116).

### Bar 3 — parsers validate: GREEN (one gap closed this packet)

**Check:** fast-tier malformed-input coverage per parser entry point; guard
parity — every entry point that reaches the protected operation, or one
shared choke point.

The facade's complete external-input entry-point inventory
(`src/pyreason/__init__.py`), each with its fast-tier malformed coverage:

| entry point | fast-tier malformed coverage | file |
|---|---|---|
| `add_rule` / `Rule(text)` | `test_rule_text_rejections_carry_banked_messages` (parametrized) + the weights/delta reject arms | test_rewrite_dsl_parsers.py |
| `add_fact` / `Fact(text)` | `test_fact_text_rejections_carry_banked_messages` (parametrized) | test_rewrite_dsl_parsers.py |
| `Query(text)` | `test_query_nonnumeric_bound_raises_float_message` + `test_query_silent_misparses_are_reproduced` | test_rewrite_dsl_parsers.py |
| `add_rules_from_file` | missing-file / wrap-line / warn-skip arms (3 tests) | test_rewrite_state_loaders.py |
| `add_rule_from_csv` | 9 malformed arms (missing/empty/wide/short/non-UTF-8/duplicate/tokenizer-line…) | test_rewrite_state_loaders.py |
| `add_rule_from_json` | document-level + item/threshold arms (2 tests) | test_rewrite_state_loaders.py |
| `add_fact_from_csv` | `test_fact_csv_malformed_arms` | test_rewrite_state_loaders.py |
| `add_fact_from_json` | `test_fact_json_malformed_arms` | test_rewrite_state_loaders.py |
| `load_inconsistent_predicate_list` | YAML malformed + nonstring arms (3 tests) | test_rewrite_state_loaders.py |
| `add_inconsistent_predicate` | `test_add_inconsistent_predicate_nonstring_raises_the_same_guard` | test_rewrite_state_loaders.py |
| `load_graphml` | **NEW this packet**: `test_load_graphml_malformed_file_fails_loudly_and_leaves_state` — the shared `nx.read_graphml` choke point (identical call at pinned graphml_parser.py:16; raise shapes screened identically in both engines' networkx), plus the missing-file arm, plus prior-state survival | test_rewrite_graph_boundary.py |
| `load_graph` | takes a live `nx.DiGraph` (no text parse — no malformed-input class); the attribute-coercion ladder is pinned by `test_attribute_coercion_ladder_matches_pin` | test_rewrite_graph_boundary.py |
| settings knobs (`setattr`) | `test_settings_setters_validate_types_with_pinned_messages` (the `_Knob` choke point, all 18 knobs) | test_rewrite_state_loaders.py |
| `Threshold(...)` | `test_threshold_rejects_bad_quantifier_and_type` + short-tuple arm | test_rewrite_value_types.py |

**The gap this audit found and closed:** `load_graphml` was the one entry
point with no fast-tier malformed-input test (every other row predated this
packet). The new seam test pins both loud-failure arms
(`xml.etree.ElementTree.ParseError` on unparseable content —
screened live in oracle-env networkx 3.4.2 and the rewrite's 3.6.1,
byte-same shapes — and `FileNotFoundError` on a missing path) and that a
previously loaded graph survives untouched. Beyond the fast tier, the e2e
corpus carries 14 malformed/warn-skip cases banked cross-engine
(`ls harness/cases/ | grep -E "malformed|warn-skip|ragged|junk"`).

### Bar 4 — tiered, evidence-bearing suite: GREEN (discipline mechanized this packet)

**Check:** fast tier offline and gate-run; differential/perf tiers
e2e-marked; every test carries a `proves:` docstring — audited mechanically,
not sampled.

- **The gate:** `scripts/hooks/pre-commit` runs `uv run pytest -m "not e2e"`
  on any staged `.py`/`.toml` (and the corpus link check on any `.md`) —
  every commit in this packet passed through it. Current fast tier: **330
  passed, 6 deselected in ~0.4 s** (offline: no substrate reached).
- **e2e marking:** the `e2e` marker is declared in `pyproject.toml`;
  `uv run pytest -m e2e --collect-only -q` → exactly 6 tests (oracle-vs-oracle,
  preflight, resume, DIV reproducers) — the tier split is total.
- **`proves:` discipline, mechanized:** an AST audit over every
  `tests/test_*.py` — **294/294 test functions carry a `proves:`
  docstring, 0 missing** (this includes the 6 e2e tests the gate
  deselects, since the audit parses rather than collects). Until this packet
  that rule was enforced by review habit; it is now a standing fast-tier
  check, `tests/test_suite_discipline.py::test_every_test_function_carries_a_proves_docstring`,
  so an uncredentialed test fails the gate itself. (What a mechanized check
  cannot grade is whether each claim *matches* what the test asserts — that
  stays the review bar it has always been, exercised as recently as
  session 29's F1.)

### Bar 5 — version headroom honest: GREEN

**Check:** `requires-python` matches the campaign floor and the ceiling is
stated with evidence in the execution-layer ADR.

Carried by [ADR 0004 §AC-5.5](../adr/0004-execution-layer-pure-python-core.md):
`requires-python = ">=3.11"` with **no stated ceiling** (`pyproject.toml`);
no JIT pin, no compiled wheel, no build step; the two-library pure-Python
dependency surface named exactly; and the evidence that the headroom is real
rather than asserted — the pinned oracle's `numba==0.59.1`
(`oracle/pyreason/requirements.txt:4`) is why it lives in a dedicated Python
3.10.20 env, while the rewrite ran the whole 116-case corpus and fast tier
on Python 3.13.11 with zero version-conditional code
(`grep -rn "version_info\|sys.version" src/pyreason/` → 0).

**Audit summary: 5/5 GREEN, no red bar left standing.**

## 2. The oracle-env kernel-cache re-baseline (packet item 4, operator-approved)

Session-29 review §F2
([the record](2026-07-12-breadth-registrand-edgerule-review.md)): the banked
237-file cache baseline itself contained four pre-session-29 `.2.nbc`
dispatcher-embedding specializations (written 2026-07-07) whose indexes embed
`harness.reference_fns` and hard-fail unpickle wherever `harness` is not
importable. The operator approved regenerating the baseline. The cache lives
in **oracle-env's site-packages** (the campaign's own engine environment) —
the oracle *clone* was byte-clean at the pin before and after every step here
(`git -C oracle/pyreason status --porcelain` → empty).

### Where the old baseline lived

The 237-file count was banked in prose, not in a manifest: session-29 review
§5 ("exactly 237 files") and the session-29 author report / ledger; the
index-count flavor ("101 kernel indexes / 110 MB") in
[docs/perf/oracle-baselines.md](../perf/oracle-baselines.md). No committed
per-file digest list existed. The new baseline gets a committed manifest —
[docs/ledger/session-33-oracle-env-cache-baseline.md](../ledger/session-33-oracle-env-cache-baseline.md)
— so every future restore-check has bytes to compare against instead of a
sentence.

### Before (the quirk, reproduced one last time)

Old cache recorded: **237 files, aggregate sha256
`8d4e1a0f…a52020`** (full per-file manifest preserved with the set-aside
copy). From a bare context (cwd and script dir outside the repo;
`importlib.util.find_spec("harness") is None` asserted), `pickle.load` on
each of the four F2 indexes:

```
interpretation._ground_rule-809            REPRODUCES: No module named 'harness'
interpretation._call_head_function-2315    REPRODUCES: No module named 'harness'
interpretation._determine_node_head_vars-2230  REPRODUCES: No module named 'harness'
interpretation._determine_edge_head_vars-2271  REPRODUCES: No module named 'harness'
```

A byte-scan found exactly 8 files embedding `harness`: the four `.2.nbc`
data files and their four rewritten indexes — precisely F2's inventory.

### Regeneration (bare, three warmup phases)

The old cache was set aside whole; the new one was built exclusively by
**bare runs**: oracle-env python, cwd and script outside the repo root, each
script asserting `harness` is unimportable before importing the engine.
Because numba compiles an njit function's whole transitive call graph at the
top-level compile, one `reason()` per engine variant rebuilds that variant's
entire kernel set:

1. **default** engine (rules + facts + graph attributes, `reason(timesteps=2)`) — 166.7 s compile;
2. **fp_version** — 62.2 s;
3. **parallel_computing** — 180.9 s;
4. default again with `again=True`/`restart` arms — 6.5 s, all cache hits
   (no new signatures: `again` is a value, not a type);
5. default with `convergence_bound_threshold=0.001` (the `conv-delta-bound`
   input class — a float64 in the signature) — 43.6 s, regenerating the
   `Interpretation.reason` and `_init_convergence` second specializations.

### After — the new baseline and the quirk-gone proof

- **232 files (101 indexes + 131 data files), aggregate sha256
  `e573ad75…b5136a`**, banked file-by-file in
  [the manifest](../ledger/session-33-oracle-env-cache-baseline.md).
- **Name-level diff old → new:** the only entries that did not regenerate
  are the four leaked `.2.nbc` specializations (never hittable — their
  pickled signatures reference per-process registrand dispatchers) and one
  historical `Interpretation.reason-240.py310.3.nbc` third specialization
  whose generating input class is unknown; the 15-case stratified sample
  below (which exercises the default/fp/parallel engines, the float
  convergence bound, again/restart, registrands, and the ladder rung)
  compiled nothing, so no sampled input class needs it. If some unsampled
  corpus case does, first service would compile it as a clean bare-signature
  entry and move the banked count — which the committed manifest makes
  immediately detectable, the failure mode being a stale count, never an
  import fault.
- **Quirk gone, three ways:** (1) byte-scan of all 232 files for
  `harness`/`reference_fns` → **0 hits**; (2) **all 101 indexes unpickle
  cleanly in a bare context** (the exact F2 failure mode, now 101/101 LOADED
  CLEAN, 0 fail); (3) the four named kernels' indexes load among them.

### The regenerated cache serves captures identically

Stratified 15-case sample (the packet asked for a small sample incl.
hello-world and one ladder rung; the strata here: hello-world,
`perf-ladder-small`, fp, parallel ×2, convergence-bound, inconsistency+ipl,
rule-trace ×2, reason-again, accessors-lifecycle, memory-profile-output,
weights-dtypes, threshold-dict, and one registrand case to prove
snapshot/restore keeps the new baseline intact), one invocation,
`PYTHONHASHSEED=0`, oracle-env vs `scripts/rewrite-python`:

- **15/15 PASS** (report:
  `<scratchpad>/results-session33-cache-sample/report.json`).
- **hello-world probe digests byte-identical to the banked session-15
  artifact** (`results/hello-world/a1.json`) — the same identity check the
  session-29 review used; ditto `annotation-fn-two-arg` against its banked
  artifact.
- **Cache byte-stable across the whole sample:** the post-sample manifest
  equals the post-warmup manifest (232 files, same aggregate) — the
  non-registrand captures were fully cache-hitting and the registrand case's
  snapshot/restore returned the cache to baseline.

### Old → new, one line

**237 files / aggregate `8d4e1a0f…` (banked in prose, 4 entries
import-fragile outside the repo root) → 232 files / aggregate `e573ad75…`
(banked as a committed manifest, 0 harness references, 101/101 indexes load
bare).**

## 3. Commits

- `370875b` — docs: ADR 0004 (execution layer, AC-5.5 statement).
- `af8a8cf` — docs: the memo's Decision section.
- `be800fb` — tests: the two audit mechanizations (graph-file malformed
  coverage; the standing `proves:` gate check).
- (see ledger) — docs: the new cache-baseline manifest + this report.

## 4. Evidence commands (from the repo root)

```
# fast tier (330 = 328 + this packet's 2)
uv run pytest -m "not e2e"

# bar-1 mechanized checks
grep -rn "def _ground_rule" --include="*.py" src harness tests tools scripts
grep -rniE "import (numba|numpy|cython|cffi)|from (numba|numpy|cython|cffi)" src/pyreason/

# bar-2 family status in the sweep of record
python3 -c "import json; r=json.load(open('results-phase4-boundary/report.json')); \
  print([ (e['case_id'],e['status']) for e in r['verdicts'] \
  if any(s in e['case_id'] for s in ('reset','again','fresh-state','lifecycle'))])"

# bar-4 audits
uv run pytest tests/test_suite_discipline.py -q
uv run pytest -m e2e --collect-only -q

# the cache re-baseline verification (count + digests vs the banked manifest)
python3 - <<'EOF'
import hashlib
from pathlib import Path
cache = Path("oracle-env/lib/python3.10/site-packages/pyreason/cache")
lines = [f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.stat().st_size:>9}  {p.relative_to(cache)}"
         for p in sorted(cache.rglob("*")) if p.is_file()]
print("files:", len(lines), "aggregate:", hashlib.sha256("\n".join(lines).encode()).hexdigest())
EOF

# the quirk-gone check (bare unpickle of every index; run from OUTSIDE the repo)
#   oracle-env/bin/python <bare-script>  — asserts harness unimportable, then
#   pickle-loads all *.nbi; expected: 101 load clean, 0 fail

# the 15-case sample (cases copied out of harness/cases; results dir disposable)
PYTHONHASHSEED=0 uv run python -m harness.run --cases <sample-dir> \
  --engine-a oracle-env/bin/python --engine-b scripts/rewrite-python \
  --results <results-dir>
```

## 5. Hygiene

- No installs, no dependency changes, no lab compute; `oracle/pyreason`
  byte-clean at the pin before and after (0 porcelain lines at every check).
- The set-aside 237-file cache and all warmup/verification scripts live in
  the session scratchpad only; nothing outside the repo was written except
  scratchpad temporaries.
- One pre-existing uncommitted working-tree change
  (`docs/perf/pokec-scaling-report.md`, an n=2 timing refinement) predates
  this packet and was left untouched and unstaged throughout.
- No full-corpus sweep: fast tier + the 15-case sample + the bare warmups
  only, per the packet's test-tier rule.
