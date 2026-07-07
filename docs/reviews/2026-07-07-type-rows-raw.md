<!-- doccode: pyreason-rewrite-docs-reviews-type-rows-raw -->
# Author report — session 14: the last six breadth rows (4 types + 2 callable registrars)

Author: campaign worker (Agent 1), 2026-07-07. Packet: session 13's NEXT —
`type:Query`, `type:Threshold`, `type:Interval`, `type:Label`,
`fn:add_annotation_function`, `fn:add_head_function`. Board before: 46/52
cased. Board after: **52/52 cased** (`equivalent` still 0/52 — no rewrite
exists).

## Anchors read at the pin (e1a94af33e1f)

- `scripts/query/query.py:4-37` + `scripts/utils/query_parser.py:5-34` —
  Query construction; four parsed fields; the `~`/`:` branches never
  reconcile; `find('(')` == -1 silently truncates.
- `scripts/threshold/threshold.py:1-41` — quantifier/quantifier_type
  membership checks; `thresh` stored unvalidated; `to_tuple()` verbatim.
- `scripts/numba_wrapper/numba_types/interval_type.py:13-145` +
  `scripts/interval/interval.py:6-90` — the two parallel implementations;
  `closed()` at :143-145; the intersection prev-seed divergence
  (interval_type.py:63 vs interval.py:69).
- `scripts/numba_wrapper/numba_types/label_type.py:16-105` +
  `scripts/components/label.py:1-21` — string-valued equality/hash; the
  numba typer's string-only constructor; unbox reads `_value`.
- `pyreason.py:1415-1494` — the two registrars (arity gate 2/6 vs no
  validation); `pyreason.py:1497-1626` — reason()'s queries plumbing;
  `scripts/utils/filter_ruleset.py:1-34` — predicate-match + recursion +
  `list(set(...))`; `interpretation.py:1869-1931` (annotate), `:2231-2338`
  (head-var determination and `_call_head_function`), `:1364-1377` +
  `:1475-1503` (threshold satisfaction), `:227-231` (extended-arity flags).
- Oracle test exemplars: `tests/functional/test_advanced_features.py`
  (annotation/head-function shapes the pin's own suite exercises).

## Input classes enumerated

Taken row-by-row from `docs/analysis/surface/{reason-and-state,rules}.md`
(already enumerated there); every class is either covered by a committed case
or named on the board with the precise reason it is not. No class was
silently dropped.

## Mechanisms landed (commit 0aa8d6e)

1. **`queries` joins `REASON_ARGS`** — case JSON carries query-text strings;
   the capture builds pinned `Query` objects at the call site, outside the
   steps form's recording try (a construction raise is a capture failure;
   malformed query text belongs to the expect_raise form).
2. **`expect_raise` constructs `query` and `threshold`** — acceptance banks
   the parse/stored fingerprint (misparses become data); threshold args are
   exactly the pinned constructor's three parameters, list quantifier_type
   handed over as the documented tuple, strings ridden verbatim for the
   shape-fault arms.
3. **`interval_probe` / `label_probe`** — direct-construction probes for the
   aliased public value types (`pyreason.interval.closed`,
   `pyreason.label.Label`), fixed observation pipelines (construction state,
   equality/hash/containment RELATIONS — never raw hash numbers —
   intersections, the reset transition, and the post-reset intersection that
   pins the proxy prev-seeding). allow_raise forbidden on both (self-recording
   or fixed-pipeline; a raise is a binding fault).
4. **Rule specs carry `custom_thresholds` (both pinned forms) and `weights`**
   — shared builder for `inputs.rules` and the new **`add_rule` step op**
   (needed because reset_rules clears rules and registrations together, so
   the reset arm re-adds the rule after).
5. **Named-function registry** (`harness/reference_fns.py`) — committed
   reference functions selected by name via the new
   `add_annotation_function`/`add_head_function` apply ops; unknown name =
   exit 2 validated against `REGISTRY` before the engine imports. The module
   is stdlib-only at import (the fast tier, which has no numba, imports it to
   validate names); `resolve()` applies `numba.njit` inside the engine env
   because the pin accepts plain callables at registration but requires
   njit-compilable registrands at reason dispatch (screened: a plain 2-arg
   function registers fine and reason() then dies in numba argument typing).
   Registry keys are held to `fn.__name__` by a fast-tier test — the engine
   matches registrands by `__name__` (interpretation.py:1920, :2334).

+13 seam tests; fast tier 90 → 103, green at every commit.

## Design rationale for the registry

The packet's carried seed. Constraints that shaped it: (a) callables cannot
ride JSON, so the case declares a NAME and the capture must resolve it; (b)
an unknown name must be an authoring fault (exit 2) — validation therefore
needs the registry importable in the fast-tier env, which has no engine, no
numba, no networkx → stdlib-only module import, njit at resolve time; (c) the
engine matches by `__name__` → registry keys are the functions' `__name__`s,
test-enforced; (d) reference outputs land in exact-compared observations →
closed-form arithmetic on exact binary fractions only; (e) the reject arms
need deliberately wrong shapes → the two stubs are registry members like any
other (resolution is uniform njit; njit is lazy so never compiles for a
registrand the engine rejects at registration).

## Cases (17 new; corpus 76 → 93)

Every case: exact comparison policy (`"comparison": {"probes": {}}`), no
canonicalization anywhere in this packet — nothing run-varying survived into
any banked observation. Targeted runs:
`PYTHONHASHSEED=0 uv run python -m harness.run --cases harness/cases/<id>.json --engine-a oracle-env/bin/python`
— ALL PASS, 4 fresh-process captures each, same-engine repeats by exact
digest.

| case | pins |
| --- | --- |
| query-construct | all 8 Query construction classes; both silent misparses banked as parse data; bad-float ValueError |
| reason-queries-filter | predicate-only ruleset filtering; permanent `__rules` narrowing (post-reason get_rules = survivor only); no busy row despite its satisfied body |
| reason-queries-no-match | zero survivors → numba `ValueError: cannot compute fingerprint of empty list` at reason; `__rules` left a plain `[]` (accessor fingerprint) |
| threshold-construct | 5 quantifiers accepted; both ValueErrors; string/short quantifier_type shape faults (IndexError 'tuple index out of range'); thresh unvalidated (−5, 'many' banked verbatim) |
| threshold-number-gate-default / -two | the accepted-threshold semantics gap: number thresholds gate at clause level; ≥2 with one whole-graph qualifier kills the rule everywhere vs the default twin's derivation |
| threshold-dict-gate | dict form + parser-defaulted clause 0 reach the same consumed thresholds (blocked outcome vs the default twin) |
| threshold-percent-total | percent/total = qualified/grounding ratio vs thresh*0.01 — 2/2 fires, 1/2 does not, both arms in one program |
| interval-ops | closed/static/inverted/disjoint construction; equality+hash ignore static; empty-intersection clamp to [0,1]; reset transition (reset() ignores the static flag); has_changed; the PROXY intersection prev-seed pin |
| label-ops | value/str/repr; equality+hash by string value (relations only); empty-string label; the ==-non-Label AttributeError |
| annotation-fn-two-arg | both arity rejects (3-arg, *args→0) with the pinned message; 2-arg semantics THROUGH reason() (combo(A)=[0.5,1]); weights consumption differential (combo2=[0.625,1]) |
| annotation-fn-six-arg | extended signature routed by the per-rule arity flag; crowd(A)=[0.25,1] from clause-0 grounding count, atom_trace off |
| annotation-fn-unregistered-name | reason-time `NameError: name 'annotation' is not defined` (objmode output assigned only in the name-match loop) |
| annotation-fn-reset-clears | reset_rules clears the registration → same NameError with the rule re-added (add_rule step) |
| head-fn-grounding | no-validation asymmetry (the SAME stub that TypeErrors at the annotation registrar registers silently); unreferenced registration inert; referenced fn grounds the head → Processed(A)=[1,1] |
| head-fn-unregistered-name | the silent arm: no `__name__` match → empty grounding, zero rule rows, reason completes |
| head-fn-reset-clears | reset_rules clears head registrations → silent-empty vs head-fn-grounding's derivation |

## Screens that shaped scope (not banked, each named on the board)

- **Self-recursive rule + matching query**: filter_ruleset recurses without
  bound through clause targets; the process dies with SIGSEGV (exit 139)
  before Python's RecursionError — no artifact, so un-caseable. Board:
  type:Query notes.
- **Multi-survivor filter order**: `list(set(rules))` (filter_ruleset.py:34)
  is address-derived; screened stable across 4 fresh runs, but committed
  cases keep survivor sets ≤ 1 rather than bank an incidental ordering.
- **Plain (non-njit) registrands**: accepted at registration (both
  registrars), then reason() fails numba argument typing — the TypingError
  message embeds engine-environment site-packages paths, so banking it would
  hard-code this environment's text; named unobserved instead. For head
  functions this poisoning fires even when the registrand is UNREFERENCED.

## A hazard hit and repaired mid-session (for the reviewer's attention)

Screen runs njit-compiled functions from a *scratchpad* module inside the
oracle env; numba's on-disk cache (cache=True kernels under the engine
package's cache dir) pickled dispatcher-bearing signatures whose
deserialization imports the registrand's module — every later cache-index
load then failed with `ModuleNotFoundError: No module named
'proto_reference_fns'`, breaking even cases that register nothing. Repair:
deleted the six affected kernels' cache sets (index + code files) from
`oracle-env/.../pyreason/cache/`; hello-world re-verified ALL PASS after the
recompile. The pinned oracle TREE was never touched. Standing consequence,
worth a board/ledger eye: captures that register reference functions write
cache entries referencing `harness.reference_fns` — importable in every
repo-rooted run (the runner always runs `cwd=REPO` with `-m`), but an
oracle-env process started OUTSIDE the repo after such a capture would hit
the same index fault until the cache heals. Screens must only njit functions
from committed, repo-importable modules (or clean up after themselves).

## Compile-cost note (wall-clock rule compliance)

Each distinct registrand tuple is a fresh numba specialization of the big
reason kernel (compiled once, then disk-cached across processes). This
packet added three such signatures; their first captures paid the compile,
repeats ran warm. No corpus sweep was run; the fast tier plus the 17
targeted case runs (plus a hello-world rerun after the cache repair) are the
only engine executions.

## Verdicts

- Fast tier: 103 passed / 2 deselected at every commit.
- 17/17 targeted case runs ALL PASS (oracle-vs-oracle self-proof, 4 fresh
  captures each, `PYTHONHASHSEED=0`), plus hello-world re-verified after the
  cache repair.
- Board: 52/52 cased; six rows flipped with the unobserved facets named
  above; fn:get_rules' post-reason-filtered class and fn:reason's
  queries-filter class closed by the same cases; fn:reset_rules'
  registration-clearing half moved from assertion to pinned.

## Idea seeds (carried forward)

- The multi-survivor `list(set(...))` ordering is a ready-made divergence
  probe once a rewrite exists (a rewrite will almost certainly order
  deterministically; the oracle's order is address-derived).
- `interacts-reorder_clauses` for the 6-arg annotation contract: an
  edges>nodes graph with a 6-arg fn that banks clause_labels order would pin
  the post-reorder metadata contract.
- Edge-rule head-function forms (Route/Path/Link shapes from the oracle
  suite) are a cheap second head-fn case.
- The zero-survivor reason raise + the SIGSEGV recursion make reason(queries=)
  a strong adjudication cluster for Phase 3's rewrite design.

## Blockers

None. No installs, no oracle-tree writes, no out-of-repo writes; no operator
gate was crossed (the cache repair is runtime-cache maintenance inside the
disposable oracle-env virtualenv, not the pinned tree — flagged above for
review anyway).
