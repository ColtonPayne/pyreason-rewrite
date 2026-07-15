<!-- doccode: pyreason-rewrite-hivemind-copy-charter -->
> **Snapshot, not source of truth (operator-requested, 2026-07-15).** This is a verbatim
> copy of the governing charter, taken 2026-07-15 from
> `$HIVEMIND_ROOT/idea-synthesis/plans/hivemind-portability.md`, committed so the charter
> is readable from the GitHub mirror of this repo. The charter's own Charter-discovery
> clause names the planning-repo file as the single source of truth precisely because a
> copy drifts silently — that clause still governs: campaign sessions read the canonical
> file, never this snapshot, and edits land there. Refresh this copy manually when it
> matters; the source's livedoc status region and doc-code stay behind in the planning
> repo and are omitted here.

# Plan: the pyreason reimagining campaign — a ground-up rewrite proven by oracle differential
Stakes: foundational — the campaign is both halves of one boundary-drawing act: it closes the
portability MVP's acceptance (the federated substrate carrying real foreign-repo work on a second
machine), and it rebuilds a load-bearing dependency (MINDSET sits on pyreason) behind an
equivalence boundary that is expensive to redraw once consumers depend on it.
Idea: [writeups/hivemind-portability.md][idea-synthesis-writeups-hivemind-portability]
Target repo: **pyreason-rewrite** — the campaign repo; every campaign artifact (code, harness,
cases, ledger, ADRs) lands there under its committed rules
([CLAUDE.md][pyreason-rewrite-CLAUDE]).

## Goal
Reimagine pyreason from the ground up in the campaign repo — understand what it is good at and
where it breaks, redesign it for performance and maintainability, and prove by an e2e
oracle-differential harness that every pyreason public-API feature gives the same results as the
pinned oracle, minus operator-adjudicated correctness bugs. The campaign's ordinary workflow is
itself the portability MVP's acceptance run on the fresh second machine, and every stopping point
is a valid end state an Opus-class agent can resume cold.

## How to read this document
This is a **charter, not a step script**: it governs by acceptance criteria, standing
disciplines, and a permission charter. The methodology sections are *suggestions with rationale*
— the executing session may deviate, recording each deviation and its reason in the campaign
ledger. Two properties hold regardless of path: every claim of equivalence, performance, or
"done" is proven by the named mechanism (the harness, a test tier, a measured number, an operator
sign-off) — never by assertion — and every action stays inside the permission charter and the
campaign repo's committed rules ([CLAUDE.md][pyreason-rewrite-CLAUDE], which this charter
operates inside and never relaxes).

A fresh executing session starts in the campaign repo and reads, in order:
1. the campaign repo's `CLAUDE.md` (the enforced rules, and the breadcrumb to this charter);
2. this charter;
3. the newest `docs/ledger/session-<N>.md` — the resume point
   ([the ledger seam][pyreason-rewrite-docs-ledger-README]); if no session exists yet, execute
   the committed session-0 contract first (Substrate, below);
4. `docs/surface.md` — the equivalence progress board (AC-1), once it exists.

Then pick up the ledger's NEXT, or — if NEXT is done or blocked — the highest-value open
criterion the board and ledger show unfinished.

## Hard constraint — this campaign is never security work (operator-set, 2026-07-06)

The campaign is correctness, performance, and maintainability engineering on an inference
engine — nothing else. **No security framing, anywhere, ever**: no vulnerability-analysis or
exploit-adjacent content, and no security-assessment framing of the work in session prompts,
subagent tasks, harness cases, retrieval queries, docs, or commit messages. The rationale is
operational, not stylistic: the executing engine's safety classifier flags dual-use security
content, and a flagged session is hard to unwind back to an ordinary engineering state — one
careless framing can cost the session, and sessions are the campaign's scarcest resource.
Concretely:
- The analysis corpus's BUG entries are read as **software-defect reports** — crashes, wrong
  bounds, state contamination, which is what they are — never re-framed in vulnerability or
  exploit terms.
- Downstream consumers are named without security characterization: MINDSET is a downstream
  consumer whose pain points include cold-start latency, full stop.
- Subagent prompts and lrag queries stay in engine-engineering vocabulary (parser, grounding,
  convergence, interval semantics, throughput).
- If an input surfaces security-framed material, the campaign does not engage it — note the
  path neutrally in the ledger if load-bearing, and move on.
(The hivemind's standing review-severity calibration against its deployment model is process
discipline, not campaign content, and is unaffected.)

## The committed substrate (verified standing state — the contracts this charter builds on)

All verified against the committed sources on 2026-07-06; the campaign re-verifies anything it
makes load-bearing beyond this list.

- **The preflight doctor** — `uv run python tools/hive_preflight.py`, ten checks by name:
  `python-version`, `uv-present`, `umbrella-manifest`, `manifest-entry`, `hstate-invokable`,
  `links-gate`, `lrag-probe`, `oracle-pin`, `ledger-writable`, `git-wiring`. Exit 0 all-pass /
  1 any-fail / 2 usage; `--json` emits the report the ledger banks. Every failure prints an
  actionable hint.
- **The session-0 contract** ([ledger README][pyreason-rewrite-docs-ledger-README]): on the
  campaign machine, run the doctor, fix reds by its hints, bank the passing JSON report plus a
  one-line verdict as `session-0.md`. The one documented expected red on a fresh machine is the
  machine-local lrag registry, bootstrapped by exactly two commands (the single registry write
  this repo ever performs):
  `uv run --directory $HIVEMIND_ROOT/local-rag lrag collection new pyreason-analysis --path ~/Projects/dyuman-pryeason`
  then `uv run --directory $HIVEMIND_ROOT/local-rag lrag sync -c pyreason-analysis`. Every
  retrieval thereafter passes `--no-sync`. A truly fresh clone may surface others the hints
  cover (the one-time `git config core.hooksPath scripts/hooks` included). No campaign work
  while the preflight is red.
- **The campaign machine** — the operator's second laptop: **macOS / Apple Silicon**, with
  `~/Projects` mirrored from the primary Linux laptop by syncthing (operator-stated,
  2026-07-06 — the one substrate fact this list carries on the operator's word rather than a
  file read; the preflight verifies the mirrored tree's mechanics on it, and Phase 1's gate
  tests the oracle on it).
- **The ledger session format** — each `session-<N>.md` states, in order: **Verdict** /
  **Evidence** / **Committed** / **NEXT**. The newest session is the resume point. This charter
  extends the format additively (Session protocol, below); the four committed fields stay
  exactly as the ledger README has them.
- **The gate** — the committed pre-commit hook runs the corpus-wide `hstate links check` when
  any `.md` is staged and `uv run pytest -m "not e2e"` when any `.py`/`.toml` is staged; the
  `e2e` marker means "needs the live federated substrate" and is deselected by the gate.
- **The oracle** — `oracle/pyreason/`, a read-only clone of upstream lab-v2/pyreason detached at
  `e1a94af33e1f9d925c9df8284113dd0e14fe8a73` (release v3.6.0), verified clean by the `oracle-pin`
  check. Never modified; the pin moves only by operator decision recorded in the ledger.
- **Retrieval** — the operator's clean-room analysis corpus (29 registered docs — the lrag
  collection's count; the tree holds a few more `.md` than the collection registers — over
  `~/Projects/dyuman-pryeason` (the directory name is literally `dyuman-pryeason`; copy it
  verbatim, never "correct" the spelling): `BUG_LOG.md` + `BUG_LOG_2.md`, IDs
  BUG-001…BUG-208, ~191 entries,
  beside `GLOSSARY.md` and the layer/interpretation/grounding analyses) is the lrag collection
  `pyreason-analysis`:
  `uv run --directory $HIVEMIND_ROOT/local-rag lrag retrieve "<query>" -c pyreason-analysis --no-sync`.
  The workspace is read-only input. A near-duplicate corpus lives on the `ai-documentation`
  branch of the nested clone `~/Projects/dyuman-pryeason/pyreason` (its `ai_docs/` adds a
  `PUBLIC_API.md`); prefer the top-level files where they disagree. **Bug reports are seeds for
  understanding, never acceptance criteria, and never taken at face value: a logged bug is a
  hypothesis until reproduced against the pinned oracle.** The corpus's MASTER_TODO is discarded.
- **The campaign package starts empty** — the committed `pyproject.toml` declares
  `requires-python = ">=3.11"`, **zero runtime dependencies**, and a dev group of `pytest`
  only. Under the committed never-install-unprompted rule, *every* dependency the campaign
  needs — the oracle's own runtime set included — is an operator ask (Permission charter).
- **The editable-install trap (verified in the pinned source):** `pyreason/__init__.py` sets
  `NUMBA_CACHE_DIR` *inside the package directory*, rewrites `.cache_status.yaml`, and runs a
  warm-up `reason()` on first import. `.cache_status.yaml` is a **git-tracked** file committed
  as `initialized: false` — the clone's `.gitignore` lists it, but ignore rules don't apply to
  tracked files, so the first-import rewrite shows in `git status --porcelain` and reds the
  `oracle-pin` check. (The numba `cache/` directory is untracked-and-ignored — git-invisible,
  but still a write into a tree the campaign never writes. The yaml write is skipped when
  pytest is in the importing process; harness capture runs the oracle in bare subprocesses,
  where it fires.) The oracle is always installed **non-editable** (built and copied into its
  own environment), so its first-import writes land in site-packages, never in the clone.

## The oracle, in brief (verified profile vs carried priors)

Verified against the pinned source, 2026-07-06 — the campaign's own deep analysis re-verifies
anything it builds on further:
- An explainable inference engine for annotated, real-valued, graph-based temporal logic
  programs: a NetworkX graph whose nodes/edges carry predicate → truth-interval `[l,u]` atoms;
  rules, facts, and thresholds over time windows; a fixed-point temporal forward-chaining loop
  with an optional rule trace as the explainability surface.
- **The public API surface is finite**: 26 public module-level functions defined in the API
  module `oracle/pyreason/pyreason/pyreason.py` — 31 top-level `def`s minus the 5
  `_`-prefixed private ones (load/add/reset families, `reason(...)`, `get_rule_trace`,
  filter/sort accessors), 6 public types (`Rule`, `Fact`, `Query`, `Threshold`, `Interval`,
  `Label` — the `Rule`/`Fact` text DSLs included; only the first four are name-level imports
  in the API module, `Interval`/`Label` are reached through its aliased submodule imports),
  and an 18-knob module-global `settings` singleton (`verbose` … `fp_version`). Two further
  names (`LogicIntegratedClassifier`, `ModelInterfaceOptions`) appear only when the optional
  `torch` extra is installed; **the model-integration surface is out of scope for the
  campaign (operator-set, 2026-07-06)** — torch is never installed, no equivalence claim
  covers those two names, and the inventory names the exclusion in a header note rather than
  dropping the names silently (re-scoping it in later is a clean follow-on: one dependency
  ask for both envs, the inventory rows, the cases — the integration sits on top of the
  public API and touches no engine architecture). The whole program
  state lives in module globals — there is no reasoner object.
- **The engine is triplicated**: `interpretation.py` (2338 lines), `interpretation_parallel.py`
  (2338), `interpretation_fp.py` (2456) — three near-copies a fix must land in three times
  (plus a small 58-line `interpretation_dict.py` helper: not a fourth core, but part of any
  complete enumeration of the engine files).
  numba is architectural bedrock (structref/jitclass mirrors of every domain type; `@njit`
  reasoner core); pins `numba==0.59.1` / `numpy==1.26.4`.
- Carried as **priors, not verified facts** — each is re-verified before anything load-bearing
  rests on it: the dominant bug families read from the analysis corpus (parser input-validation
  gaps, JIT-vs-python parity divergence, module-global state contamination across `reason()`
  calls, float-equality fragility in convergence detection); the upstream issue/PR numbers the
  corpus cites; and **that the pinned oracle runs at all on macOS/Apple Silicon** — a
  first-session gate, not an assumption.

## Acceptance criteria (the proof targets)

Every criterion names its proof mechanism, its baseline, and its noise discipline, and states
what significant, measured progress means where full completion is out of reach. A bar cleared
by assertion, by noise, or by construction-trivial cases is not cleared.

### AC-0 — Substrate integrity and the portability acceptance (standing; gates every criterion)
**Bar:**
1. **Session 0 banked per the committed contract** — the passing `--json` preflight report as
   `docs/ledger/session-0.md`, on the campaign machine.
2. **Non-disruption proven, not presumed** — the same session banks the evidence that
   registration changed nothing it shouldn't: the `links-gate` check green (the corpus link
   graph is intact), `git status --porcelain` clean of campaign-caused modification in the
   umbrella tree *and* in the nested repos the bootstrap reaches (local-rag, hive-state — the
   machine-local lrag registry is git-ignored rebuildable state, so a clean tree there is the
   expected result, and a dirtied one is a finding), and the lrag registration being the
   campaign's only write outside its own repo.
3. **The substrate stays load-bearing** — sessions bank in the ledger, analysis retrievals go
   through `lrag retrieve … --no-sync`, the gates run on every commit, the campaign's docs
   participate in the link graph. A campaign that quietly routes around the substrate fails
   this criterion even with a green preflight.
4. **Friction is evidence** — every point of substrate friction lands one Friction record
   (Session protocol) instead of a silent workaround; that record stream is the portability
   idea's raw material for its deferred general model.
**Proof mechanism:** the banked session-0 artifacts; audit by construction thereafter — any
reader can walk ledger entries, retrieval commands in Evidence, and gate runs back from commits.
**Baseline:** the Linux-laptop preflight PASS already committed and e2e-wrapped.

### AC-1 — The equivalence target set is enumerated and committed
**Bar:** a committed `docs/surface.md` inventory that makes "all pyreason-API features"
countable. One row per surface item across three kinds: the 26 public module-level functions,
the 6 public types (their text DSLs as their own rows), and the 18 `settings` knobs. Each row
carries (the seam contract, defined here once): `item` (stable id, e.g. `fn:add_rule`,
`type:Interval`, `setting:persistent`) · `oracle anchor` (file:line at the pin) · `input
classes` (the enumerated equivalence classes this item must be proven over — happy path,
boundary, malformed, and named interactions; enumerating them *is* the analysis work) ·
`cases` (ids of covering harness cases) · `status` ∈ {`uncovered`, `cased`, `equivalent`,
`divergent-queued`, `adjudicated`} · `notes`. Coverage is thereafter a measured fraction —
items at `equivalent`-or-`adjudicated` over total, and input classes likewise — and nothing
off-inventory counts toward any equivalence claim.
**Proof mechanism:** the committed file, plus a fast-tier test that AST-scans the pinned API
module `oracle/pyreason/pyreason/pyreason.py` (stdlib `ast` only — the test parses source and
never imports the oracle, so it runs offline on a machine with no oracle env) and asserts the
inventory rows match the scan **per row kind**, since the three kinds live in three shapes:
*functions* = top-level `FunctionDef`s minus `_`-prefixed names (26 at the pin); *knobs* =
`@property` defs on the `_Settings` class in the same file (18 at the pin); *types* = the four
classes imported by name (`Rule`, `Fact`, `Query`, `Threshold`) plus the two reached through
the aliased submodule imports (`interval.Interval`, `label.Label`) — the module has no
`__all__`, so the six type rows are asserted against those import statements, not against a
name list a single-shape scan could derive. An omitted or phantom item is a red gate, not a
review finding.
**Baseline:** the pinned oracle source. **Progress form:** the inventory existing and mechanized
is itself the bar; it is a prerequisite for AC-3's numbers meaning anything.

### AC-2 — The oracle-differential harness (the proof spine)
**Bar:** a committed harness with these mechanized properties (the *design* — module layout,
runner ergonomics — is the campaign's):
1. **Isolated capture** — each case runs through each engine in its own environment via
   subprocess (the engines never share a process, and their dependency sets never mix: the
   oracle env carries the pinned upstream deps; the rewrite env carries the rewrite's). Each
   run emits a self-describing result artifact (inputs, engine identity + env fingerprint,
   probe outputs as canonical JSON, digests) with raw artifacts preserved for diagnosis —
   digests are tripwires, not the diagnosis.
2. **A stdlib compare layer** — normalization + digest + comparison import nothing from either
   engine.
3. **Comparison at the public API boundary** — each case declares its **probe set** (the
   public-API calls whose outputs are compared) and its **comparison policy**: exact equality
   by default; a numeric tolerance only per-case, with its rationale recorded in the case
   record. No global epsilon, ever — a silent tolerance is a silently absorbed divergence.
   Ordering is part of the compared value: event order within a rule trace and row order in
   returned frames are contract by default, normalized only where a case records the oracle's
   own ordering as nondeterministic (with the characterization that proves it).
4. **Reproducibility before verdicts** — every verdict-bearing run pairs with a same-engine
   repeat (`PYTHONHASHSEED` pinned; any engine nondeterminism explicitly characterized and
   canonicalized or exempted per-case with rationale). The exit taxonomy separates the three
   signals: pass / cross-engine divergence / same-engine irreproducibility — and the third is a
   harness-or-environment failure, never a finding about the rewrite.
5. **Divergences recorded, never absorbed** — every cross-engine mismatch lands an AC-6 record.
6. **The harness proves itself first** — oracle-vs-oracle PASS on the seed corpus (repeats
   green, digests stable) before any rewrite claim counts.
**The case corpus:** committed, each case one self-describing record (the seam contract):
`id` · `purpose` (one line) · `inputs` (graph, rules, facts, settings — inline or by committed
fixture path) · `probe set` · `comparison policy` (+ tolerance rationale if any) · `surface
items covered` (AC-1 ids) · `provenance` (oracle example / oracle test / corpus seed BUG-id /
property-generated / perf ladder) · `runtime class` (smoke / standard / long — long cases obey
screen-then-confirm). Seed sources: the oracle's own examples and tests, spine cases written
against the inventory, corpus-seeded reproducers (hypotheses until they reproduce).
**Proof mechanism:** the harness's own committed tests plus the banked oracle-vs-oracle run.
**Baseline:** the pinned oracle. **Progress form:** this criterion is mechanism, not coverage —
it clears when the spine exists, self-proves, and is consumed by AC-3.

### AC-3 — API equivalence coverage (the north-star bar)
**Full bar:** every `docs/surface.md` item at `equivalent` or `adjudicated`: proven by AC-2
runs at ≥1 case per enumerated input class — with the reasoner spine (graph loading, `add_rule`
+ the Rule DSL, `add_fact` + Fact semantics, `reason` including its `again`/`restart` semantics,
`get_rule_trace`, the filter/sort accessors, the reset family, and the semantically heavy
settings: `persistent`, `canonical`, `atom_trace`, `inconsistency_check`, `update_mode`,
`allow_ground_rules`, `fp_version`, `parallel_computing`) covered by a *deep* corpus
(multi-timestep programs, convergence-threshold variants, inconsistency paths, static vs
windowed facts), not only single happy-path cases.
**Divergence semantics (binding both ways):** matching the pinned oracle is the default
meaning of correct. A behavior the analysis corpus or the campaign's own analysis flags as an
oracle bug that the rewrite *reproduces* is equivalence-PASS **and** still files an AC-6
oracle-bug-candidate — both, not either; matching the oracle never silently blesses a bug. A
deliberate fix diverging from the oracle is `divergent-queued` until the operator adjudicates
it into documented, tested intentional behavior.
**Proof mechanism:** AC-2 harness artifacts + the inventory statuses; no claim by assertion or
code-reading counts. **Baseline:** the pinned oracle. **Noise:** exact-by-default comparison;
per-case tolerances carry recorded rationale.
**Progress form (the honest in-window shape):** the measured fraction, spine-first. Significant
progress = the spine items at `equivalent`/`adjudicated` with the deep corpus green, plus the
breadth fraction reported as a number. An uncovered breadth item is a number on the board, not
a hidden gap — and the breadth grind is deliberately shaped so a weaker agent can execute it
item-by-item from the inventory (read the anchor → write the cases → run the harness → update
the status).

### AC-4 — Performance is first-class, measured, and the execution layer clears its floor
**Bar:**
1. **A committed workload ladder** — small/medium/large cases (the campaign designs and commits
   the sizes with rationale; large stresses reasoning at scale while staying laptop-local and
   intentionally lightweight). Ladder cases are harness cases too, so performance and
   equivalence share inputs. The committed ladder precedes any floor verdict — the floor is
   falsifiable only against a committed rung.
2. **Oracle baselines banked first, on the campaign machine** — cold-start (fresh-process
   import + first `reason()`, with the oracle's numba cache already warm: the one-time
   first-ever import that *builds* the cache is banked separately as context, never as the
   comparison bar — a rewrite with no cache-build phase would flatter itself against it),
   steady reasoning throughput per ladder rung, peak memory. Every
   measurement obeys **screen-then-confirm**: a short smoke screen plus a control-repeat noise
   band before any long measurement; no claim from a single run; medians with spread, and the
   noise band banked beside the numbers.
3. **The execution-layer floor (operator-signed, 2026-07-06):** the JIT layer is load-bearing
   because it makes pyreason efficient at large-workload reasoning, so whatever the rewrite
   ships — retained JIT, C-level compilation, vectorized kernels, anything — must be
   **measurably performant at that job**: the accepted configuration's large-rung throughput is
   not worse than the oracle baseline beyond the banked noise band. A slow "clean" core is not
   an acceptable end state; regressions are reported as plainly as wins.
4. **Cold-start is a named target** — the oracle's first-import warm-up (a full `reason()` at
   import time) is a known consumer pain; the rewrite's cold-start is banked as a first-class
   number beside the oracle's.
Thresholds beyond the parity floor (how much faster is "good") are **proposed to the operator
only after the baselines exist** — a threshold invented before its baseline is a vibe, and this
charter refuses to fabricate one.
**Proof mechanism:** the committed benchmark runner + banked ledger numbers. **Baseline:** the
pinned oracle on the same machine and interpreter. **Noise:** the control-repeat band;
sub-band deltas are ties.
**Progress form:** baselines + screens banked in-window is real progress; the floor verdict
lands when the execution-layer choice lands (Methodology, phase 4).

### AC-5 — The redesign clears its maintainability bars (mechanized, not vibes)
Each property names its mechanized check; repo inspection alone grades nothing:
1. **One engine.** A single reasoning-core implementation; any acceleration sits behind a
   narrow kernel seam; if an interpreted fallback path exists at all, its parity with the
   accelerated path is a standing harness case family (guard parity — the oracle's
   JIT-vs-python divergence family is the cautionary tale), never a maintained near-copy. The
   oracle's triplicated ~2400-line engine is the named anti-goal. Check: the parity case
   family green (vacuously satisfied while the single core is the only path — the family
   becomes a live obligation with the first acceleration seam, never before; building it
   speculatively would be the dead scaffolding this charter forbids); no second core
   implementation in the tree.
2. **No hidden cross-run state.** The module-global API facade (required for equivalence) wraps
   a core with explicit, resettable state. Check: a harness case family proving two sequential
   programs in one process are independent — the oracle's state-contamination family becomes a
   passing case set, adjudicated per AC-6 wherever the *oracle* fails it.
3. **Parsers validate.** Malformed graph/rule/fact/settings input fails loudly with actionable
   errors; the corpus's parser-crash reports seed the case set (as reproduced hypotheses).
   Check: fast-tier malformed-input tests across every parser entry point — guard parity means
   every entry point that reaches the protected operation, or one shared choke point.
4. **The suite is tiered and evidence-bearing.** Fast tier offline and gate-run; differential
   and perf tiers `e2e`-marked; every test carries a one-line `proves:` docstring matched to
   what it actually asserts (the committed repo rule — an overstated claim is worse than a
   missing one). Check: the gate itself, plus the `proves:` discipline auditable per test.
5. **Version headroom is honest.** The rewrite's `requires-python` matches the campaign floor
   (>=3.11), and its ceiling is stated with evidence given the chosen execution layer — a numba
   retention re-inherits a version ceiling, and that cost lands written in the execution-layer
   ADR, not discovered later.
**Baseline:** the oracle's shape (the anti-goals). **Progress form:** these are properties of
whatever code exists — they hold from the first spine commit or they're red; there is no
"clean it up later" phase.

### AC-6 — Divergence adjudication: nothing is silently absorbed
**Bar:** every cross-engine divergence the harness surfaces lands one committed record in
`docs/divergences/` (the seam contract, one file per record, `DIV-<seq>.md`): `id` · `case
ids` · `surface items` · `observed` (each engine's value or artifact path) · `first-seen
session` · `classification` ∈ {`harness-defect`, `rewrite-defect`, `oracle-bug-candidate`,
`intentional-divergence-proposed`, `unclassified`} — classifying is itself a judgment call
(telling a rewrite defect from an oracle bug takes engine understanding a post-window filer
may not have), so a filer unsure between classes records `unclassified` and lets the
operator's batch adjudication decide rather than steering it wrong · `reproducer` (for bug candidates and intentional
divergences: the path to a failing test against the pinned oracle) · `status` ∈ {`open`,
`queued-for-operator`, `adjudicated`} · `provisional behavior` (what the rewrite does
meanwhile, if a dependent surface forced a choice) · `verdict` + adjudicating session ref.
Harness-defects and rewrite-defects are the campaign's to fix; oracle-bug-candidates and
intentional divergences are **operator-adjudicated, each with its failing-test reproducer**;
an adjudicated-accepted divergence becomes documented, tested intentional behavior on the
inventory. **Queue-and-continue:** adjudication never blocks the campaign — where a dependent
surface needs a behavior now, the rewrite provisionally matches the oracle and the record says
so; the operator batch-adjudicates at session boundaries.
**Proof mechanism:** auditability by reconciliation — harness divergence events and divergence
records match 1:1; a mismatch is a red finding against the campaign itself. **Baseline:** the
pin, which moves only by operator decision recorded in the ledger.

### AC-7 — Every stopping point is a valid end state; the pickup contract is mechanized
**Bar:**
1. **Committed is the default state** — every green checkpoint commits (small, focused, why in
   the message, `Co-Authored-By` trailer, gates never bypassed); the working tree is never the
   only home of anything.
2. **Every session banks a ledger entry** in the committed four-field format plus this
   charter's trailing sections (Session protocol); **NEXT names one concrete action a cold
   agent can execute**, not a theme.
3. **The progress board is real** — `docs/surface.md` statuses and the divergence records are
   current as of every commit that changes them; architecture decisions land as ADRs in
   `docs/adr/` *when made*, with the options and the deciding rationale.
4. **The pickup drill (the mechanized weaker-agent contract):** at least once mid-campaign, and
   again at the window's close if reachable, a cold Opus subagent (explicit `model: 'opus'`)
   is given only the committed repo and asked to state the campaign's state and execute the
   ledger's NEXT far enough to prove it's executable. Any gap between its reading and the
   intended state is a defect in the *committed state* — fixed and re-drilled before the
   campaign proceeds. The drill and its result bank in the ledger.
**Proof mechanism:** the drill, plus audit by construction on the rest. **Baseline:** none —
this criterion is absolute. Missing AC-3's full bar in-window is acceptable **only while this
criterion holds**; it is the one bar the window's close cannot be allowed to break.

## Suggested methodology (non-binding; deviate with recorded reason)

**Phase 0 — session 0 (the committed contract).** Preflight → fix reds by hints (the lrag
bootstrap's two commands; hooksPath wiring; whatever else a fresh clone surfaces) → bank the
passing JSON report + the AC-0 non-disruption evidence as `session-0.md`. The charter
breadcrumb in the campaign repo's `CLAUDE.md` is a banking-time precondition (Permission
charter → Charter discovery); finding it missing is a substrate finding — restore it in the
session's first docs commit and record the friction.

**Phase 1 — environment + understanding, before any rewrite code.**
- **The batched dependency ask, once:** one operator ask listing (a) the oracle environment —
  a dedicated env installing the pinned oracle **non-editable** (the editable-install trap,
  Substrate) with its declared runtime set (`networkx`, `pyyaml`, `pandas`, `numba==0.59.1`,
  `numpy==1.26.4`, `memory_profiler`, `pytest` — small; `torch` stays out: the
  model-integration surface it gates is out of scope, operator-set 2026-07-06, which also
  keeps the heaviest, most platform-sensitive wheel out of the ARM gate's surface),
  and (b) the rewrite/harness dev set (test and
  benchmark tooling; runtime deps as the design firms). Rationale: the committed
  never-install-unprompted rule plus a zero-dependency `pyproject.toml` make this the
  campaign's first hard operator dependency — batching it avoids a drip of blocking asks.
- **The ARM gate:** verify the pinned oracle actually runs on the campaign machine —
  macOS/Apple Silicon (hello-world `reason()` in the oracle env; bank the result; with torch
  excluded, the platform-sensitive surface is the `numba==0.59.1`/`numpy==1.26.4` wheels and
  their JIT behavior on ARM). This is a carried prior, not a fact; if it
  fails, the comparison boundary and much of this methodology re-plan — stop and escalate with
  options rather than improvising around a broken oracle.
- **Build the inventory (AC-1)** from the AST scan + reading; profile-read the architecture
  (grounding, rule firing, interval updates, the interpretation loop); seed understanding and
  case ideas with targeted lrag retrievals over the analysis corpus (BUG entries as hypotheses
  to reproduce, never as facts). Opus subagents fan out per-module (explicit `model:`, ≤12
  concurrent without an ask; outputs to files; verdict + path back — full reports never
  round-trip through context).

**Phase 2 — harness before rewrite.** Capture scripts, the stdlib compare layer, the case
record format, the seed corpus (oracle examples/tests + spine cases), oracle-vs-oracle
reproducibility including hash-seed characterization. The harness contract is fully stated in
AC-2 — it requires no external repo read: its design prior art lives on the operator's Linux
laptop only (not mirrored to the campaign machine), so do not depend on or go looking for it;
if reading that source ever seems worth it, that is an operator ask, not a workaround. Rationale: until the harness exists,
every rewrite claim is assertion — the false-done guard here is mechanical, not aspirational;
building the proof spine first also front-loads the campaign's highest-value banked artifact.

**Phase 3 — the reference core.** Ground-up clean design: an explicit-state reasoner core
under the module-global API facade; a pure-Python reference implementation of the spine;
equivalence from the first commit (spine cases green oracle-vs-rewrite as they land);
input-validating parsers as the entry points are written, not retrofitted. The reference core
is the correctness spine — it is *expected* to be slow; its job is meaning, not speed. Write
the hot loop as pure functions over explicit state (good design regardless, and it keeps the
later acceleration choice cheap to try and cheap to reverse).

**Phase 4 — the execution-layer evidence path.** Profile the oracle *and* the reference core
on the ladder to find where time actually goes — measured, not assumed. Spike candidate
accelerations on the hottest kernel only (vectorized numpy; numba re-added behind the seam as
one candidate; C-level compilation as another), each screened cheap before any long
confirmation. The commitment — which acceleration ships as the core — is the campaign's
hardest-to-reverse fork and its single biggest schedule risk: it goes to the operator as
options + measured numbers + a recommendation, and stays reversible (behind the seam) until
signed. New dependencies any candidate needs ride the ask that proposes it.

**Phase 5 — breadth + confirmation.** The inventory-driven coverage grind (deliberately
weaker-agent-shaped); performance confirmation on the chosen layer against AC-4's floor;
the AC-5 bars closed; the AC-7 window-close drill and verdict-of-record ledger entry.

**Wall-clock discipline (standing):** the campaign never schedules development work by its own
duration guesses — dev throughput is discovered by doing. Experiments and measurements are the
opposite: each is planned around its expected wall-clock cost, cheap discriminating probes
before expensive confirmations, no long run a short one could have decided, no measurement
answering a question nothing depends on.

**Stop conditions.** Stop a thread when its remaining unknowns need an operator decision —
queue the ask (ledger, Asks queued), commit, move to the next unblocked item. Stop an
acceleration lever when two consecutive candidates fail to beat the banked best beyond the
noise band (diminishing returns — a ruled-out candidate is a result). At the window's close:
write the verdict-of-record ledger entry — the state of every criterion, what remains, the
recommended next session — AC-7's interruption form.

## Permission charter

**Autonomous (no ask):**
- All work inside the campaign repo: code, tests, docs, the harness and its runs, benchmark
  runs (local, intentionally lightweight, screen-then-confirm).
- Read-only reads of the oracle clone, the analysis workspace (and its `ai-documentation`
  branch), and the umbrella's docs; lrag retrievals with `--no-sync`.
- Web research to calibrate and verify (verified-vs-prior discipline in writing).
- Subagents with an explicit `model:` capped at Opus (`'opus'` substantive, `'sonnet'`/`'haiku'`
  narrow), **up to 12 concurrent** (operator-set, 2026-07-06 — carried verbatim; a larger
  fan-out is an ask, every time). Subagents write full reports to files and return verdict +
  path.
- Committing at every green checkpoint (never pushing); queueing divergences and asks and
  continuing.

**Ask first (options + recommendation, then wait):**
- **Any dependency change** — `uv add`, a new environment, any install anywhere (the Phase-1
  batched ask is the expected first; candidate-specific deps ride their proposing ask). Batch
  asks at session boundaries where they aren't blocking.
- **Moving the oracle pin** (recorded in the ledger with the operator's decision).
- **Any write outside the campaign repo** beyond session 0's documented machine-local lrag
  bootstrap.
- **The execution-layer commitment** — adopting an acceleration approach as the shipped core.
- **A fan-out beyond 12 concurrent subagents**; any paid-API spend of any kind.
- **Upstream-contribution work** (a post-window consumer, not in-window scope).
- **Wiring the hive-state ideas pipeline** — the extension point exists (`hstate ideas ingest`
  takes `--path`/`--repo`) and is an operator ask if the campaign's idea-seed volume warrants
  it; never pre-built (idea seeds live in ledger trailing sections meanwhile).
- **Anything ambiguous — the ambiguous case defaults to asking**, and a blocked thread never
  silently stalls the campaign: write the ask into the ledger, commit, move to the next
  unblocked item.

**Adjudication semantics (so an absent operator never stalls the window):** divergence
adjudication is **queue-and-continue** (AC-6). The campaign blocks on an adjudication only when
a dependent surface cannot proceed without the behavior decision — and even then it
provisionally matches the oracle, marks the record, and proceeds. Asks and queued divergences
are batched for the operator at session boundaries.

**Never:**
- Security framing of any kind (the Hard constraint above) — no vulnerability- or
  exploit-adjacent content or vocabulary in any campaign artifact, prompt, or query.
- Lab compute, at all — no inference endpoints, no broker, nothing (the committed campaign
  rule, stricter than the umbrella's tiers).
- Installs without an ask; writes to `~/Projects/dyuman-pryeason`, any operator tree, or
  `oracle/pyreason` — editable installs from the clone included (the cache-write trap).
- Bypassing hooks; hand-editing any machine-rendered region anywhere; pushing without an ask.
- A "done"/"equivalent"/"faster" claim by assertion — the harness, the gates, a banked
  measurement, or an operator sign-off says so, or it is not so.

**Charter discovery (the breadcrumb).** This charter lives in the planning repo
(idea-synthesis `plans/hivemind-portability.md`), mirrored to every campaign machine by
syncthing — a single source of truth, never copied into the campaign repo (a copy drifts
silently). The campaign repo carries a committed pointer: one line in its `CLAUDE.md` —
*"Governing charter: `$HIVEMIND_ROOT/idea-synthesis/plans/hivemind-portability.md` — read it
before campaign work."* **The pointer is committed as part of banking this plan, before the
first campaign session** — a cold agent can only find this charter through it, so a missing
pointer is a defect in the banking step, never a condition the campaign self-heals from
(Phase 0 restores it and records the friction if it ever goes missing). A fresh session
starting cold from the campaign repo reaches the charter through it.

**Session protocol + the handoff seam.** Sessions are operator-launched on the campaign
machine. Every session ends by banking one ledger entry — the committed four fields **in the
committed order** (Verdict / Evidence / Committed / NEXT), extended additively after NEXT by
these charter-defined trailing sections, each present when non-empty (the seam contract,
defined here once):
- **Deviations** — from the suggested methodology, each with its reason.
- **Asks queued** — every operator ask, each with its prepared command or options +
  recommendation.
- **Divergences** — records opened/updated/adjudicated this session (ids).
- **Friction** — substrate-friction records: `surface` (which substrate piece) · `expected vs
  actual` · `workaround` · `cost` (one line) · `recommendation`. Consumed by the portability
  idea's deferred general-model work as federation evidence.
- **Idea seeds** — follow-on ideas and substrate gaps for post-window triage into the idea
  pipeline.

## Standing engineering discipline

The campaign writes a whole codebase, largely by agent hands; the recurring AI-authoring
failure modes are guarded, not hoped away (the catalogue:
[ai-coding-pitfalls][ai-hivemind-docs-ai-coding-pitfalls]; the campaign repo's committed rules
bind throughout). The vital subset, restated as standing rules:
- **Reuse or extract, never duplicate** — the oracle's triplicated engine is what unchecked
  duplication grows into. Grep before writing; third occurrence ⇒ extract and migrate the
  existing sites in the same change.
- **Test the seam, not just the helper** — every behavioral change lands with a test at the
  boundary that composes it; the differential harness is the outermost seam, never the only
  one.
- **Guard parity** — a validation covers every entry point that reaches the protected
  operation, or lives at their single shared choke point.
- **No dead scaffolding** — no config field, parameter, or fallback until its consumer lands in
  the same change; the kernel seam itself is introduced with its first second consumer (the
  first acceleration spike), not speculatively.
- **Narrow excepts; exit codes 0 ok / 1 operational / 2 usage** routed through entrypoint
  handlers — the harness's own exit taxonomy included.
- **No backward-looking comments; docs present-tense** — change rationale lives in commit
  messages and ADRs.
- **Root cause by evidence** — a causal claim about a failure (a divergence, a perf cliff) is a
  hypothesis until a reproducer or trace forces it; exonerate what you rule out; say "unproven"
  when it is.

## Review gate
Foundational plan: independent verification and a plan-logic review per the planning repo's
rules before this plan is marked ready. Downstream, campaign code rides the campaign repo's
committed gates on every commit; a complete feature (the harness, the reference core, each
accepted acceleration) gets an independent adversarial review — ≥2 Opus reviewers with no
shared context (explicit `model:`), findings fixed or down-rated against the deployment's
threat model ([security model][ai-hivemind-docs-security-model]: single operator, own
machines, no new privilege boundary) — with the report committed under the campaign repo's
`docs/reviews/`.

<!-- links:begin -->
[ai-hivemind-docs-ai-coding-pitfalls]: ../../../ai-hivemind/docs/ai-coding-pitfalls.md
[ai-hivemind-docs-security-model]: ../../../ai-hivemind/docs/security-model.md
[idea-synthesis-writeups-hivemind-portability]: ../../../ai-hivemind/idea-synthesis/writeups/hivemind-portability.md
[pyreason-rewrite-CLAUDE]: ../../CLAUDE.md
[pyreason-rewrite-docs-ledger-README]: ../ledger/README.md
<!-- links:end -->
