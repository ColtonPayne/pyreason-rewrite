<!-- doccode: pyreason-rewrite-docs-reviews-2026-07-12-ac5-closure-review -->
# Session 33 — independent review: AC-5 closure, ADR 0004, the cache re-baseline

- session: 33 · date: 2026-07-12 · independent reviewer (no shared context with the author)
- scope: commits `370875b` (ADR 0004), `af8a8cf` (memo decision section),
  `be800fb` (the two audit mechanizations), `4f6b957` (author report + cache
  manifest), reviewed against the charter's AC-5 bars, ADR 0001–0003
  conventions, and the banked evidence.
- verdict: **approved with fixes** — one numeric transcription error found
  and corrected (`03862f4`); every other claim re-derived independently and
  confirmed. All five AC-5 bars re-audited GREEN from my own runs; the cache
  re-baseline verified end to end including the "before" side.

## 1. What was re-derived, not taken on the report's word

Every number below is from my own run in this review session, from the repo
root unless noted.

### The cache re-baseline (author report §2) — fully confirmed

- **Manifest recount:** 232 files (101 `.nbi` indexes + 131 `.nbc` data
  files), aggregate sha256
  `e573ad7504efdeb7f65c0fd4ac59d618374573dc4b2aa2bd762e0a4b05b5136a` — exact
  match to [the committed manifest](../ledger/session-33-oracle-env-cache-baseline.md),
  and a row-by-row diff of all 232 per-file (sha256, size, path) entries
  against a fresh recompute: **0 mismatches, 0 banked-only, 0 fresh-only**.
- **Bare unpickle:** my own script (cwd outside the repo,
  `importlib.util.find_spec("harness") is None` asserted, oracle-env
  python), full pickle-load of every index: **101 LOADED CLEAN, 0 FAILED**.
- **Byte-scan:** all 232 files scanned for `harness` and `reference_fns`:
  **0 hits**.
- **The "before" side, independently reproduced** (the author's set-aside
  copy survives in the shared session scratchpad): the old cache recounts to
  **237 files, aggregate `8d4e1a0f…a52020`** — exact match to the manifest's
  prose record; a byte-scan finds **exactly 8** harness-embedding files (the
  four `.2.nbc` specializations + their four rewritten indexes — precisely
  the session-29 review §F2 inventory); and bare unpickle of the four old
  indexes **REPRODUCES `No module named 'harness'` 4/4**.
- **Name-level diff old → new:** exactly five old-only entries — the four
  leaked `.2.nbc` specializations and
  `interpretation.Interpretation.reason-240.py310.3.nbc` — and **zero
  new-only entries**. The author's account is complete.
- **Oracle clone:** `git -C oracle/pyreason status --porcelain` → 0 lines;
  HEAD = `e1a94af3` = `oracle/PIN`, before and after my sample runs. The pin
  never moved; only oracle-env's site-packages cache was touched, under the
  operator's §F2 approval.

### My own serving sample — disjoint from the author's

The author's 15-case sample (report in the session scratchpad: 15/15 pass,
`resumed: false`) left its case list on disk, so I chose **4 of my 5 cases
outside it**: `closed-world-on`, `canonical-last-write`,
`graphml-attr-coercions`, `ipl-load-malformed`, plus `hello-world` as the
banked-digest anchor. One invocation, `PYTHONHASHSEED=0`, oracle-env vs
`scripts/rewrite-python`: **5/5 PASS**. The fresh oracle `hello-world`
capture's digests and probes are **byte-identical to the banked session-15
artifact** (`results/hello-world/a1.json`). The cache after the sample
recounts to the same 232 files and the same aggregate — **byte-stable**, so
four input classes the author never sampled also served entirely from the
regenerated cache with zero new compilation.

### The missing `reason-240.py310.3.nbc` — the argument holds

Assessed honestly: the entry's generating input class is unknown; the
author's 15 strata plus my 4 additional classes all served cache-hitting, so
no known input class needs it. If an unsampled class ever does, numba's
first service compiles a clean bare-signature entry — a latency event (tens
of seconds, once) that moves the banked file count, which the committed
per-file manifest makes immediately detectable. The failure mode class
genuinely changed: a stale count is discoverable and self-healing; the old
quirk was an import fault wherever `harness` wasn't importable. Accepting
the gap is the right call; regenerating blind to chase a count would have
been cargo cult.

## 2. The five AC-5 bars — re-audited from my own runs

Charter wording checked against the source
(`$HIVEMIND_ROOT/idea-synthesis/plans/hivemind-portability.md`, AC-5 §1–5);
the author's framing matches it, including the vacuous-parity clause, which
is the charter's own text, not an invention.

1. **One engine — GREEN.** `grep -rn "def _ground_rule"` across
   src/harness/tests/tools/scripts → exactly one hit
   (`src/pyreason/_interpretation.py:1036`); one interpretation module
   (1897 + 356 helper lines vs the oracle's three ~2400-line near-copies);
   acceleration imports (`numba|numpy|cython|cffi|ctypes`) in
   `src/pyreason/` → **0**. No parity scaffolding exists, matching the
   charter's "never before the first acceleration seam".
2. **No hidden cross-run state — GREEN.** The sweep of record
   (`results-phase4-boundary/report.json`): 116/116 pass, `resume.resumed:
   false`, and the 13 lifecycle/sequential-independence cases all `pass` —
   re-read from the banked artifact, list identical to the author's.
3. **Parsers validate — GREEN.** The new
   `test_load_graphml_malformed_file_fails_loudly_and_leaves_state` passes;
   its claims check out: the pinned oracle's graphml seam is the same
   `nx.read_graphml` call (`graphml_parser.py:16`), and the two networkx
   versions are as stated (oracle-env 3.4.2, rewrite 3.6.1). I checked the
   inventory's omissions rather than its rows: the facade functions absent
   from the table (`add_annotation_function`, `add_head_function`,
   `add_closed_world_predicate`, the output helpers) all take live Python
   objects with no text-parse malformed class; notably
   `add_closed_world_predicate` mirrors the pinned oracle's bare `set.add`
   (oracle `pyreason.py:1122`) — no guard exists there to mirror, so the
   omission is guard-parity-correct, not a gap.
4. **Tiered, evidence-bearing suite — GREEN.** My own AST count over
   `tests/test_*.py`: **294 test functions, 0 missing `proves:`** —
   independently reproducing the gate check, which also passes. `-m e2e
   --collect-only` → exactly 6 of 336; the fast tier runs offline in ~0.4 s.
5. **Version headroom honest — GREEN.** Read `pyproject.toml` myself:
   `requires-python = ">=3.11"`, dependencies exactly
   `networkx>=3.6.1` + `pyyaml>=6.0.3`, **no `[build-system]` table**. The
   ADR's correction of the memo's "zero dependencies" shorthand to the
   actual two-library surface is accurate and the honest direction. The
   contrast evidence checks: `numba==0.59.1` at
   `oracle/pyreason/requirements.txt:4`; `version_info|sys.version` in
   `src/pyreason/` → 0.

**Fast tier at review head: 330 passed, 6 deselected (0.37 s)** — matching
the author's count.

## 3. The decision record (ADR 0004 + memo) — numbers verified

- Every ladder figure in the ADR's table (post-spike 0.0028 / 0.151 /
  1.226 s; pre-spike 0.0041 / 0.655 / 18.792 s; oracle 2.992 / 3.611 /
  17.977 s with bands), cold-start 0.067 vs 4.376 s, RSS 67.1 vs 328.6 MiB,
  and the 14.7× / 4.3× / 1.47× multipliers trace exactly to
  [rewrite-baselines.md](../perf/rewrite-baselines.md) and
  [oracle-baselines.md](../perf/oracle-baselines.md).
- The four session-28 optimization commits named in the decision
  (`c56d238`, `c218f45`, `958523a`, `ca600a3`) all exist with matching
  subjects.
- The verdict-of-record citation is exact: 116/116, one invocation,
  `resumed: false`, zero divergences.
- ADR conventions: MADR-lite Context/Decision/Consequences, doccode marker,
  `NNNN-slug` name, status/date/session header — matches ADR 0001–0003.
- The decision framing is faithful to the memo's standing question: Option B
  signed, C-track closed unopened, no dependency ask granted, and the
  deferred grounding-scope seed carries its equivalence-proof burden
  explicitly rather than landing as a leftover obligation.

### The one fix — F1 (corrected, `03862f4`)

**ADR 0004 and the memo addendum both cited the Pokec 10k oracle band as
"2,589–2,701 s"; the raw banked captures say 2,619.6 s and 2,701.1 s**
(`results-pokec-sanders/smoke/perf-pokec-10k/a1.json` → `reason_s:
2701.074`; `a2.json` → `2619.623`), and "2,589" appears nowhere in any
version of the Pokec report or anywhere else in the tree. The error
originated in the memo addendum (`8f8c097`, a prior session) and the ADR
inherited it. Corrected to **2,620–2,701 s** in both files; the ~101×
multiplier is unaffected (2701.074 / 26.762 = 100.9, and the Pokec report
itself was always right). Class: transcription slip in a decision-bearing
document — exactly what "verify the ADR's numbers against the banked
sources" exists to catch; no measured claim changes.

### Observation, no fix (out of this packet's scope)

The Pokec report's 10k row prints the rewrite runs as "26.7 / 26.7" where
the raw captures say 26.88 / 26.76 s — a rounding wobble of ≤ 0.7% in a
prior-session document that currently carries an uncommitted operator-side
edit (left untouched per the packet). It does not move the ~101× claim
(100.5–100.9 computed either way). Flagged here so the record notes it;
worth folding into that report's next touch, not worth colliding with the
concurrent workstream now.

## 4. Repro commands

```
# cache manifest recount + row-by-row diff vs the committed manifest
python3 - <<'EOF'
import hashlib, re
from pathlib import Path
cache = Path("oracle-env/lib/python3.10/site-packages/pyreason/cache")
fresh = {str(p.relative_to(cache)): (hashlib.sha256(p.read_bytes()).hexdigest(), p.stat().st_size)
         for p in sorted(cache.rglob("*")) if p.is_file()}
block = Path("docs/ledger/session-33-oracle-env-cache-baseline.md").read_text().split("## Per-file manifest")[1]
banked = {p: (h, int(s)) for h, s, p in re.findall(r"^([0-9a-f]{64})\s+(\d+)\s+(\S+)$", block, re.M)}
lines = [f"{h}  {s:>9}  {p}" for p, (h, s) in sorted(fresh.items())]
print(len(fresh), hashlib.sha256("\n".join(lines).encode()).hexdigest())
print("mismatches:", [p for p in fresh if banked.get(p) != fresh[p]], "delta:", set(banked) ^ set(fresh))
EOF

# bare unpickle (run from OUTSIDE the repo with oracle-env python;
# asserts harness unimportable, pickle-loads all *.nbi) → 101 clean, 0 fail
# byte-scan → 0 files contain b"harness" or b"reference_fns"

# oracle pin
git -C oracle/pyreason status --porcelain; git -C oracle/pyreason rev-parse HEAD

# AC-5 bar checks
grep -rn "def _ground_rule" --include="*.py" src harness tests tools scripts
grep -rniE "import (numba|numpy|cython|cffi)|from (numba|numpy|cython|cffi)" src/pyreason/
uv run pytest tests/test_suite_discipline.py -q
uv run pytest -m e2e --collect-only -q
uv run pytest -m "not e2e"

# the F1 fix's source of truth
python3 -c "import json; print([json.load(open(f'results-pokec-sanders/smoke/perf-pokec-10k/{f}.json'))['timing']['reason_s'] for f in ('a1','a2','b1','b2')])"

# the reviewer's disjoint 5-case serving sample
PYTHONHASHSEED=0 uv run python -m harness.run --cases <dir with hello-world,
  closed-world-on, canonical-last-write, graphml-attr-coercions,
  ipl-load-malformed> --engine-a oracle-env/bin/python \
  --engine-b scripts/rewrite-python --results <disposable>
```

## 5. Hygiene

- No installs, no dependency changes, no lab compute; uv only; no push.
- `oracle/pyreason` read at the pin only; oracle-env cache byte-identical to
  the banked baseline after all review runs.
- The pre-existing uncommitted `docs/perf/pokec-scaling-report.md` edit was
  left untouched and unstaged; all staging was by explicit path.
- Review scripts and sample results live in the session scratchpad only.
