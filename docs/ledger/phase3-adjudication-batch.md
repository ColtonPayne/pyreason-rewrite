<!-- doccode: pyreason-rewrite-docs-ledger-phase3-adjudication-batch -->
# Phase-3 adjudication batch — every queued divergence and carried oracle-bug-candidate, in one document

Assembled session 24 (2026-07-07), the Phase-3 breadth-boundary session, per the
operator instruction banked in [session 22](session-22.md) ("all oracle-bug
candidates and DIV records adjudicated in one batch between Phase 3 and Phase 4").
This is the document the operator adjudicates from. Sources swept: ledger sessions
4–23 (Divergences + Idea-seeds sections), every phase-3 slice author/review report,
[docs/surface.md](../surface.md) row notes, the ADRs, and the two filed DIV records —
plus an independent full-corpus enumeration pass reconciled against the author's own
sweep. Nothing found is omitted; borderline observations are listed in Part C rather
than dropped.

**Review addendum (session 24):** the independent review's own three-way enumeration
sweep (ledgers 4–23, every review report including the pre-phase-3 harness reviews,
board notes + ADRs + DIV records) surfaced five recorded observations the assembly
sweep missed — two carried candidates (B33–B34) and three borderline observations
(C6–C8), added below in this document's own format. Section numbering B1–B32/C1–C5
is unchanged so existing cross-references stay valid.

**The default stance every recommendation starts from (AC-6):** matching the pin is
the default meaning of correct. Every Part-B item is a pinned behavior the rewrite
*deliberately reproduces*, and every covering committed case passes
oracle-vs-rewrite — so "keep matching" costs nothing now. Adjudicating an item as
*improve* means filing a DIV record with a failing test and diverging deliberately;
that machinery exists (DIV-0001/0002 are the worked examples).

---

## Part A — filed DIV records (the two live divergences)

### A1. DIV-0001 — query-filter recursion: the pin dies, the rewrite terminates

- **Record:** [docs/divergences/DIV-0001.md](../divergences/DIV-0001.md)
  (queued-for-operator; opened session 21 by the slice-6 review, executing the
  session-14 seed).
- **What the pin does:** a `reason(queries=...)` query matching a self-recursive
  rule's head drives `filter_ruleset`'s unguarded recursion through the clause
  targets until the process dies — exit 139/SIGSEGV before Python's
  RecursionError (screened sessions 14 and 21). Un-caseable: the pinned process
  leaves no artifact to compare.
- **What the rewrite does:** `src/pyreason/_program.py::filter_ruleset` expands
  each predicate at most once (`seen`), terminates on every cyclic ruleset, and
  returns the identical reachable-rule set on every acyclic one — which is all any
  committed case exercises. Seam test:
  `tests/test_rewrite_output_surface.py::test_filter_ruleset_terminates_on_self_recursive_rule`;
  pin-side reproducer `tests/test_div_0001_reproducer.py` (e2e).
- **Options:** (a) accept the guarded expansion as documented, tested intentional
  behavior; (b) reproduce the pin's crash (reject: deliberately reintroducing a
  process-killing recursion, on an input the harness cannot even bank); (c) replace
  the guard with an explicit diagnostic raise on cyclic inputs (a *third* behavior,
  matching neither engine today).
- **Recommendation: (a)** — exactly the DIV record's proposal. The session-14
  ledger seeded this guard as the natural intentional divergence; the reachable-set
  contract is proven identical on every committed case.

### A2. DIV-0002 — non-string IPL entries: the pin raises an address-derived ValueError, the rewrite accepts

- **Record:** [docs/divergences/DIV-0002.md](../divergences/DIV-0002.md)
  (queued-for-operator; opened session 23 by the slice-8 review probe).
- **What the pin does:** an IPL YAML with non-string pair entries (`ipl: [[1, 2]]`)
  raises `builtins.ValueError` from the numba typed-list unbox
  (label_type.py:86-94) whose *message reads garbage memory as a code point* —
  4 fresh pin processes gave 4 distinct texts. Same-engine unstable, so the
  harness scores the arm irreproducible on the pin itself; un-bankable.
- **What the rewrite does:** the plain-list `parse_ipl` transcription accepts the
  pair (`{"raised": false}`); provisional seam test
  `tests/test_rewrite_state_loaders.py::test_ipl_yaml_nonstring_entries_load_provisionally`;
  pin-side reproducer `tests/test_div_0002_reproducer.py` (e2e, asserts type +
  message *shape*).
- **Options:** (a) guard the loader — raise `builtins.ValueError` on non-string
  entries at the append seam: same type and seam as the pin, stable honest message
  (the pin's own text is unreproducible even pin-vs-pin); (b) keep the acceptance
  and document that non-string labels fail later and differently inside `reason()`.
- **Recommendation: (a)** — the DIV record's proposal, following the established
  typed-container-semantics precedent (slice-6 `TypedRuleList`, slice-7
  `TypedComponentDict` both model pinned container raise shapes).

---

## Part B — carried oracle-bug-candidates (pin behavior deliberately reproduced; adjudicate keep-vs-improve)

Every item below is currently **equivalence-PASS**: the rewrite reproduces the pin
and the covering cases (where they exist) pass oracle-vs-rewrite. "Improve" on any
item = a new DIV record + failing test, post-adjudication. Unless a per-item note
says otherwise, the recommendation is **keep matching the pin** for the reference
core; improvement proposals are Phase-4+ material and none blocks the phase verdict.

### Registry and rule-filter family (slice 2 / session 17)

**B1. Unregistered annotation-function NameError.** Pin: a rule naming an
unregistered annotation function raises `NameError("name 'annotation' is not
defined")` — an accidental unbound-variable raise (annotate's objmode output only
assigned inside the name-match loop, interpretation.py:1918-1931). Rewrite:
explicit raise, same message, same decision point (`_interpretation.annotate`).
Cases: `annotation-fn-unregistered-name`, `annotation-fn-reset-clears` — PASS.
Evidence: docs/reviews/2026-07-07-phase3-slice2-author.md §Deliberately-reproduced;
board `fn:add_annotation_function`. *Keep.*

**B2. Unregistered head-function silence — the asymmetric twin.** Pin:
`_call_head_function`'s objmode loop finds no `__name__` match and returns the
pre-seeded empty grounding (interpretation.py:2330-2338): the rule fires for no
one, `reason()` completes silently — the sharp asymmetry with B1's NameError.
Rewrite: reproduces the silent-empty shape. Cases: `head-fn-unregistered-name`,
`head-fn-reset-clears` — PASS. *Keep; if the operator ever wants a diagnostic
here, it is a behavior change embedders could feel.*

**B3. No-break annotation match loop.** Pin: every same-named registrand runs;
the last result wins (interpretation.py:1919-1930). Rewrite: transcribed as-is.
No committed case registers duplicate names; seam-level only. Evidence: slice-2
author report. *Keep.*

**B4. `filter_ruleset`'s unordered de-dup.** Pin: multi-survivor query filtering
returns `list(set(filtered_rules))` (filter_ruleset.py:34) — survivor *order* is
address-derived by construction (screened stable across 4 runs, but unpinnable).
Rewrite: transcribed as-is; committed cases keep survivor sets ≤ 1 by design.
Evidence: board `type:Query` notes; slice-2 author report. *Keep; keep the
survivor-set-≤1 case discipline.*

**B5. Graph-attribute parse print.** Pin: an unconditional stdout print at graph
load time (not gated by `verbose`). Rewrite: reproduced (observable under the
stdout-redirect knob's cases — `output-to-file` family PASS). Evidence: slice-2
author report §Deliberately-reproduced. *Keep.*

### State-lifecycle family (slice 3 / session 18; the five)

**B6. Half-cleared program after `reset()`.** Pin: `reset()` nulls the interp but
never the program, so `get_time` raises `AttributeError` on `None.time` instead of
answering like the no-program path (pyreason.py:487-516, :549). Rewrite: matched.
Cases: `reset-with-program`, `reset-no-program` — PASS. Evidence: slice-3 author
report; board `fn:reset`, `fn:get_time`. *Keep.*

**B7. `restart=True` resumes under an intact trace — the trace-KeyError family.**
Pin: the clock resets to 0 while prior-run trace rows survive, so
`Interpretation.get_dict` and `filter_and_sort_*` raise `KeyError(1)` on a
*successfully returned* interpretation. First named session 4 (board `fn:reason`
notes: "oracle-bug-candidate once a rewrite exists" — it now does and reproduces
it). Case: `reason-again-restart-true` — PASS. *Keep.*

**B8. The bare-again `TypeError('List() argument must be iterable')`.** Pin: a
numba container-constructor message standing in for a real "no facts to resume
with" signal (reason clears fact globals on exit, pyreason.py:1622-1624). Rewrite:
reproduced message-for-message. Case: `reason-bare-again-no-facts` — PASS. *Keep.*

**B9. `again=True` with no program silently degrades to a fresh run.** Pin:
pinned short-circuit, no assertion. Rewrite: reproduced. Case:
`reason-again-no-program` — PASS. *Keep.*

**B10. Grounding tables and IPL survive `reset()`.** Pin: graph-parse products,
clause maps, and the IPL are never cleared by `reset()` (unlike rules by
`reset_rules`) — the state-contamination family. Rewrite: reproduces by leaving
those `EngineState` fields untouched. Cases: reset family — PASS; slice-3 review
probes P1/P6. Evidence: slice-3 author report; board `fn:reset` notes. *Keep.*

### Knob-arm and schedule family (slice 4 / session 19; six + two review residuals + the session-6 asymmetry)

**B11. Specific-label stamping defect.** Pin: program.py:34-38 stamps specific
node/edge labels onto only the default variant; the fp and parallel classes keep
their empty defaults — upstream's own `#TODO` marks it. Rewrite: reproduces the fp
side exactly (empty maps on the fp path; ADR 0003 §Decision 4). One recorded
nuance: the rewrite's parallel arm runs the one default core and so carries real
maps where the pin's parallel class holds empty ones — verified output-invisible
on the pinned public surface (slice-4 review, probe `probe-parallel-attrs`).
Cases: `fp-version-on`, `parallel-computing-*` — PASS. *Keep (and bless the
recorded parallel-side invisibility argument).*

**B12. The dead `abort_on_inconsistency` knob.** Pin: settable, readable,
consulted nowhere. Rewrite: same. Cases: `abort-on-inconsistency-default/-on` —
PASS. *Keep.*

**B13. `update_mode` accepts any string silently.** Pin: the setter type-checks
`isinstance(value, str)` only (pyreason.py:421-432) — a typo means intersection
semantics with no signal beyond the readback. Rewrite: same. Case:
`update-mode-junk-string` — PASS. *Keep.*

**B14. Inverted intervals forced through under `inconsistency_check=False`.**
Pin: the override arm's IPL complement arithmetic produces `[0.8,0.099…]`
(lower > upper) and reasoning continues over it. Rewrite: reproduced. Case:
`inconsistency-ipl-override` — PASS. (Distinct from B28 — this is the
reasoning-time path, not the constructor.) *Keep.*

**B15. `reason()` mutates the public `atom_trace` knob when change storage is
off.** Pin: pyreason.py:1584-1585 — a settings write as a side effect of
reasoning. First flagged session 5. Rewrite: reproduced at the `_state._reason`
seam. Case: `store-off-atom-trace-flip` — PASS. *Keep.*

**B16. The fp schedule cannot terminate on `timesteps=-1`.** Pin: the fp
timestep sweep's only exit is `t == tmax` (interpretation_fp.py:272-273), so the
run-to-convergence arm never returns — a hang, not a raise. Rewrite: same exit
structure by construction (transcribed sweep); not exercised by any committed
case (a case would need a timeout-shaped probe). Evidence: slice-4 author report;
ADR 0003 §Consequences. *Keep for equivalence, but flag for Phase 4: the
workload ladder must never combine `fp_version=True` with `timesteps=-1`, and
this is the strongest candidate in the batch for an eventual guarded raise (a
one-line diagnostic vs an unbounded hang).*

**B17. fp + `infer_edges`: both engines crash at the same seam with different
KeyError payloads.** Pin: numba typed-dict lookup raises payload-less `KeyError()`
inside fp `reason` for an inferred edge's world lookup. Rewrite: crashes at the
same logical seam (`_add_edge`'s existing-edge branch) but Python's KeyError
carries the key (`KeyError(('A','B'))`). Same type, same outcome (reason()
raises), different message — a steps-form case comparing raise records **would
diverge on the text**, so this is the one Part-B item that converts to a DIV
record the moment the arm is cased. Recorded, not absorbed (slice-4 review F2);
carried in every ledger since session 19. No committed case reaches the arm.
*Adjudicate direction now to unblock any future edge-rule/fp case: recommend
treating it like DIV-0002's shape — same seam, same type, honest stable message —
rather than guessing a bare-raise site to mimic a numba internal.*

**B18. The fp `get_dict` stale-edge-variable defect.** Pin: in fp mode every
edge row of `get_dict` lands on the last edge (a stale loop variable,
interpretation_fp.py:852-854). The session-19 review caught the rewrite silently
*correcting* this and fixed it to reproduce (commit `9c51ee4`; probe
`probe-fp-getdict-edges` verified against the installed oracle; seam test
`test_fp_get_dict_lands_edge_rows_on_the_last_edge`). Evidence: session-19
ledger; ADR 0003 §Consequences. *Keep (the worked example of AC-6's
no-silent-improvement rule).*

**B19. The fp-vs-default trace asymmetry — the single-core question, resolved by
ADR 0003 and awaiting the operator's word.** Pin: on identical inputs the fp
engine's final bounds match the default engine's but its *traces* do not
(fp-counter values, event order, duplicated atom-trace groundings, last-step
frame row order). Session 6 first named it: "one rewrite core cannot natively
reproduce both knob positions' trace shapes … the `fp_version` surface will need
an operator adjudication." The rewrite's answer (ADR 0003): one semantics core
under two pinned iteration *schedules* (`fp_mode`), reproducing each knob
position's pinned trace shape — proven by `fp-version-on`,
`parallel-fp-precedence` PASS. Evidence: session-6 ledger §Idea seeds; board
`setting:fp_version` notes; docs/adr/0003. *Adjudicate: confirm ADR 0003's
resolution as the recorded answer to the session-6 question (recommended — it
reproduces both shapes and passed every covering case), closing that carried
item.*

### Graph-boundary coercion family (slice 5 / session 20 — the graphml silent-coercion cluster, plus O1/O2)

All five below live in the pinned attribute-parsing ladder
(graphml_parser.py:35-55; the swallow at :54-55). No malformed attribute value
raises anywhere in the cluster — session 9's "all silent at the pin" held at
re-verification, and the rewrite reproduces every arm exactly
(`graphml-attr-coercions` + the slice-5 review's probes — all PASS/byte-identical).

**B20. Comma-float pairs never become bounds.** Pin: `'0.3,0.7'` hits `int()`'s
ValueError, silently swallowed, and composes a junk label `fpair-0.3,0.7` at
`[1,1]` instead of the plausible-intent `[0.3,0.7]` bound. *Keep; the sharpest
user-facing surprise in the cluster if the operator ever wants a diagnostic.*

**B21. Malformed attribute values are all-silent.** Pin: out-of-range numerics
(`1.5`) and non-numeric strings (`'abc'`) compose `key-value` labels at `[1,1]`;
no diagnostic anywhere. *Keep.*

**B22. The `0` / `'0,1'` vanishing act.** Pin: both coerce to the vacuous
`[0,1]`, whose no-change update is suppressed at the gate — a stated attribute
leaves **no observable row at all**. *Keep.*

**B23. O1 — the `'1,0'` static-pin variant.** Pin: an inverted in-range comma
pair coerces to `[1,0]`, is inconsistent with `[0,1]` at application, and the
resolve arm silently pins a *static* `[0,1]` with no observable anywhere — one
notch worse than B22, since later facts on that label are frozen out too
(slice-5 review probe `rv-ladder-extra`; reproduced identically by the rewrite).
Not covered by any committed case. Evidence:
docs/reviews/2026-07-07-phase3-slice5-review.md; session-20 ledger. *Keep;
future coercion-cluster case when the graphml row's input classes widen
(session-20 seed).*

**B24. O2 — whitespace tolerance asymmetry.** Pin: the comma-pair arm tolerates
whitespace the numeric-string arm rejects (`int()` strips spaces,
graphml_parser.py:48-49: `'1, 1'` → `[1,1]`, `'0, 1'` vanishes, `'-0,1'` parses
via `int('-0')=0` and vanishes). Reproduced identically by the rewrite (slice-5
review probe). Not covered by any committed case. *Keep; same future-case seed
as B23.*

### Type, DSL, and loader family (slice 1 / session 16, plus phase-2 characterization carried onto Phase-3 contracts)

The slice-1 author report names its block "deliberately reproduced (not repaired)
oracle behaviors … improving any of these is an AC-6 adjudication proposal" —
the same carried-candidate substance under a different label, so they belong in
this batch (each carried by a banked case and a seam test since session 16).

**B25. Interval `intersection` prev-seed mismatch — proxy vs jitted arm.** Pin:
the Python-proxy arm seeds the result's `prev` from *self's current* bounds
(interval.py:69) while the jitted overload seeds from *self's prev*
(interval_type.py:63) — two irreconcilable semantics in one type; the jitted arm
is engine-internal (only reachable by compiling new jitted code). Session 14
named this "likely an adjudication candidate". Rewrite decision taken: the single
core pins the **proxy arm** (`src/pyreason/interval.py:90-91` — prev = self's
current), the arm the public surface exposes; `interval-ops` PASS and every
reasoning case's bounds compare equal cross-engine. *Adjudicate: bless the
proxy-arm choice (recommended — it is the only publicly observable arm), or
require a DIV record documenting the jitted arm as intentionally unreproduced.*

**B26. Query's two silent misparses.** Pin: `Query('popular(Mary')` (no closing
paren) truncates BOTH pred and component via `pred_comp[:-1]`/`[0:-1]` → pred
`'popularMar'`; `Query('~pred(x):[l,u]')` takes the `':'` branch and keeps `'~'`
in the predicate name with bounds `[l,u]` — the unreconciled-branches corner.
Both banked as data by `query-construct` (PASS); the rewrite reproduces both.
Evidence: board `type:Query` notes; slice-1 author report; session 14. *Keep.*

**B27. Label's plain-string equality raise.** Pin: `Label.__eq__` calls
`get_value()` on its argument *before* its isinstance guard (label.py:9-10), so
comparing against a non-Label raises `AttributeError("'str' object has no
attribute 'get_value'")` instead of returning False. Rewrite: reproduced. Case:
`label-ops` — PASS. Evidence: slice-1 author report; board `type:Label`. *Keep.*

**B28. Inverted intervals construct unvalidated (type level).** Pin:
`interval.closed(l, u)` with l > u constructs without complaint; intersection
clamps any empty result to `[0,1]`. Rewrite: reproduced. Case: `interval-ops`
(`inverted-bounds`, `intersection-empty` classes) — PASS. Evidence: slice-1
author report; board `type:Interval`. *Keep.*

**B29. Threshold's unvalidated `thresh` + the IndexError shape fault.** Pin:
`thresh` is stored unvalidated (negative and string values ride through to
`to_tuple`), and a length-1 `quantifier_type` raises `IndexError('tuple index out
of range')` instead of the membership ValueError. Rewrite: reproduced. Case:
`threshold-construct` — PASS. Evidence: slice-1 author report; board
`type:Threshold`. *Keep.*

**B30. `add_rules_from_file` name gaps and raise-after-partial-load.** Pin: the
loader names `rule_{i+offset}` over the filtered line list *even for failed
lines* (skip arm leaves a `rule_1`/`rule_3` gap), and the raise arm fires after
earlier lines already loaded — partial state with no accessor to observe it.
Rewrite: reproduced. Cases: `rules-from-file-basic/-malformed` — PASS. Evidence:
slice-1 author report; board `fn:add_rules_from_file`. *Keep.*

**B31. The loaders' duplicate-name raise after earlier rows loaded.** Pin: the
CSV/JSON loaders' file-local duplicate-name check raises at the offending row
*after* prior rows entered state (and never consults the engine-global name
set). Rewrite: reproduced. Cases: `rule-from-csv-malformed`,
`fact-from-json-malformed` — PASS. Evidence: slice-1 author report; board
`fn:add_rule_from_csv`, `fn:add_fact_from_json`. *Keep.*

**B32. `add_fact_from_json`'s verbose-ungated closing print.** Pin: the loader's
summary print is unconditional (pyreason.py:1290-1292), unlike the CSV loader's
verbose gate — it lands on pre-reason process stdout, which the harness never
compares (named unobserved on the board). Rewrite: reproduced. Evidence: slice-1
author report; board `fn:add_fact_from_json`. *Keep.*

### Added by the session-24 independent review (carried candidates the assembly sweep missed)

**B33. The store-off accessor assert family — with the reused raise message.** Pin:
with `store_interpretation_changes=False`, `reason()` completes and `get_time`
answers, but every trace-backed accessor raises `AssertionError`; `get_rule_trace`'s
single assert (pyreason.py:1666) precedes its node/edge split and reuses
`save_rule_trace`'s own message text verbatim (:1652 — "store interpretation
changes setting is off, turn on to **save rule trace**"), so both trace probes
raise a message naming a different function.
Session 5 tagged this family an oracle-bug-candidate *in the same sentence* as
B15's atom_trace flip ("the store-off assert family and the atom_trace force-flip
are … oracle-bug-candidates", session-5 ledger §Divergences); the batch carried the
flip and dropped the family. Rewrite: reproduces all three assert sites and the
reused message byte-for-byte. Case: `store-off-accessors` (four `allow_raise`
probes over the three assert sites — the banked `trace-node-store-off` and
`trace-edge-store-off` probes both carry the reused text) — PASS. Evidence:
session-5 ledger; board `setting:store_interpretation_changes` notes;
docs/reviews/2026-07-06-get-setting-raw.md. *Keep; the reused message is the
sharpest one-line diagnostic improvement available if the operator ever wants one.*

**B34. `output_to_file` rebinds `sys.stdout` and never restores, flushes, or closes
it — and the re-open leaks the first handle.** Pin: `reason()` executes
`sys.stdout = open(f'./{output_file_name}_{timestamp}.txt', 'a')`
(pyreason.py:1513-1514) and `_reason` re-opens the same name (:1541-1542),
abandoning the first handle; nothing ever restores the process's stdout — every
print an embedder makes after `reason()` returns lands in the engine's file, for
the life of the process. First recorded by the harness review
(docs/reviews/2026-07-06-harness-reviewer-B.md F10); characterized session 10; the
harness's `output_file` probe confines and flushes the file per capture, which is
why the arm is bankable at all. Rewrite: reproduces the rebind-and-never-restore
shape at the same seam. Cases: `output-to-file-default`, `output-to-file-on`,
`output-file-name-custom`, `output-file-name-inert`, `memory-profile-output-on` —
PASS. Evidence: board `setting:output_to_file` notes;
docs/reviews/2026-07-07-parallel-and-file-output-cases.md. *Keep for the reference
core; flag alongside B16 as an embedder-visible behavior an improve-decision could
target post-adjudication (restore-on-exit is a one-line contract change).*

---

## Part C — borderline observations (recorded so nothing is silently dropped; no adjudication strictly required)

- **C1. The unbankable-message family.** Three arms where the pin's raise message
  is environment- or address-derived and therefore un-caseable under exact
  compare, each screened and recorded on the board rather than banked:
  (i) `add_closed_world_predicate` with a non-string — silent at add, raises at
  `reason()` from numba Label conversion with a run-varying character-code
  message (board `fn:add_closed_world_predicate`); (ii) a plain (non-njit)
  callable registered as an annotation function — accepted at registration, fails
  numba argument typing at `reason()` with engine-environment paths in the text
  (board `fn:add_annotation_function`); (iii) same for an unreferenced non-njit
  head function (board `fn:add_head_function`). DIV-0002 (A2) is the same family,
  filed because the rewrite's *outcome* differs, not just the text. If the
  operator adjudicates A2 as (a), the same message-canonicalization stance can be
  reused if any of these three is ever cased.
- **C2. The ungrounded head-function bare KeyError.** Pin: a head-fn argument
  variable riding as itself reaches the unguarded typed-dict lookup
  (interpretation.py:583) and raises a KeyError whose *message is empty* (the
  pinned container erases the key). Cased and equivalent
  (`head-fn-ungrounded-var`, slice 7 — the rewrite models the container shape via
  `TypedComponentDict`), so it needs no decision; listed because it is quirk-class
  behavior an embedder would report as a bug.
- **C3. Zero-survivor queries raise numba's `ValueError('cannot compute
  fingerprint of empty list')` — except on edge-heavy graphs.** Pin: the
  clause-reorder rebuild (pyreason.py:1603) makes the same zero-survivor input
  *reason to completion* when edges outnumber nodes. Both arms cased and
  equivalent (`reason-queries-no-match`, `reason-queries-no-match-edge-heavy`;
  the rewrite's `TypedRuleList` models the raise). Quirk-class; no decision
  needed.
- **C4. `Interval.reset()` ignores the static flag.** Pin: the `is_static` guard
  lives at the engine call site (interpretation.py:265-273), not in the type —
  the type's own `reset()` resets a static interval. Cased and equivalent
  (`interval-ops` `reset-semantics`/`closed-static` classes); noted as
  quirk-class on the board, never flagged as a candidate. No decision needed.
- **C5. Double-count guard.** The self-recursive-query SIGSEGV observation
  (board `type:Query`; session 14) is *subsumed by DIV-0001 (A1)* — it is the
  pin-side half of that record, not a separate carried candidate.
- **C6. First-import side effects land inside the installed package — gated on
  pytest's absence.** (Added session 24 by the review.) Pin: `pyreason/__init__.py`
  points `NUMBA_CACHE_DIR` *inside the package directory*, runs a warmup `reason()`
  on first import, rewrites `.cache_status.yaml` in the package guarded only by
  `'pytest' not in sys.modules` (__init__.py:42), and prints the "Imported PyReason
  for the first time…" banner — so import behavior differs under a test runner, and
  the cache write lands in site-packages. Recorded by the harness review
  (docs/reviews/2026-07-06-harness-reviewer-B.md F9), which is why the harness
  pre-warms the cache and why the oracle env is a non-editable install. Outside the
  compared surface (pre-reason process stdout is never compared; no committed case
  observes import time), and the rewrite has no compile cache to warm — recorded so
  the asymmetry is a documented scope edge, not a silent one.
- **C7. The pin's no-caching belief about the parallel kernel is refuted at three
  sites — plus a compile-time type-safety warning.** (Added session 24 by the
  review.) Pin: the getter docstring (pyreason.py:204-205), the setter docstring
  (:410-411), and the dispatch comment (program.py:41 "We cannot parallelize with
  cache on") all assert the parallel kernel cannot cache, while the decorator is
  `cache=True, parallel=True` and the compiled kernel demonstrably caches across
  fresh processes (~174 s cold → ~3 s warm, session 10; corroborated by the
  slice-7-era review docs/reviews/2026-07-07-parallel-and-file-output-cases.md F2).
  The same kernel's compile emits `NumbaTypeSafetyWarning` (unsafe uint64→int64
  cast, interpretation_parallel.py:572). Source-comment-level upstream defects with
  no rewrite behavior arm to decide (the rewrite has no numba kernel); listed so the
  refuted-belief record reaches the operator with the rest of the batch.
- **C8. Dead and aliased knob observations beyond B12.** (Added session 24 by the
  review.) Pin: (i) `reverse_digraph` is a split read — consulted at load time by
  `load_graphml` only (`load_graph` never reads it, pyreason.py:589-599), while the
  engine-side snapshot threaded into all three kernels is stored and never consumed
  in any kernel body (board `setting:reverse_digraph`, "a dead snapshot, contra the
  analysis note"; docs/reviews/2026-07-07-graphml-fixture-cases.md); (ii)
  `canonical` is a pure alias of `persistent` — getter and setter share persistent's
  field, last write wins, and the `__canonical` field written at init/reset is never
  read (docs/reviews/2026-07-06-settings-only-knob-cases.md M1). Both cased where
  observable (`reverse-digraph-*`, `canonical-*` — PASS) and reproduced; quirk-class
  dead-surface observations in B12's family, no decision needed.

---

## What adjudication unblocks

Phase 4 (execution layer) starts from the reference core these decisions freeze.
The two DIV records decide actual rewrite behavior (A1, A2); B17, B19, and B25
decide recorded direction; every other Part-B item is a bless-the-reproduction
confirmation. Item count: **2 DIV records + 34 carried candidates + 8 recorded
observations = 44 sections** (39 assembled by the author; B33–B34 and C6–C8 added
by the session-24 independent review).
