# Campaign log — the pyreason reimagining, in plain English

The running plain-English narrative of the campaign: one entry per session,
newest last, written at each session's close by the orchestrator. Each entry
says what we knew going in, what the session taught us, what the next session
should reveal, and the one-line prompt that resumes the campaign cold. The
mechanized record (verdicts, evidence, commits, NEXT) lives in the
per-session `session-<N>.md` files beside this one; this file is the story.

## Session 7 — 2026-07-06

**What we knew going in.** The differential harness was self-proven and
growing: 28 cases, all passing oracle-vs-oracle with repeats green, and 24 of
the 52 public-surface rows cased — including the three settings-only
reasoning knobs from session 6 (the fp engine, update semantics, ground
rules). No rewrite code exists yet; every session so far builds the proof
spine that will judge it. Session 6 predicted the three load-time graph
knobs would case cleanly with no harness surgery, using an attribute-bearing
graph.

**What we learned this session.** The prediction held exactly: six new cases
(three on/off pairs sharing one attribute-bearing graph whose attributes are
the only source of truth bounds) pinned how the oracle turns graph attributes
into facts at load time, how the "static" stamp lets those facts survive the
per-timestep reset when persistence is off, and how the trace-inclusion knob
changes only what the explanation trace records — never the derived bounds.
A subtlety the prediction missed: turning parsing off (or letting fluent
bounds reset) also changes *when the run converges*, so the timestep count
and frame counts shift too — traced to the pinned convergence exit and now
part of the pinned contract. All six cases pass oracle-vs-oracle with
repeats; an independent reviewer re-derived every claim from the pinned
source and artifacts, found one Low (source-line citations in two case
purposes), and fixed it itself. The corpus is 34 cases; the board is 27/52
cased. The session protocol also changed by operator steer: each session now
runs exactly two agents (an author, then a reviewer-fixer whose review *is*
the verification), and the full-corpus sweep now runs only at phase
boundaries as its own spot-fix session — so a 34-case sweep is explicitly
owed at the next boundary.

**What we expect to learn next session.** Whether the three remaining
no-surgery settings knobs behave as the board hypothesizes: `canonical` as a
pure alias of `persistent` (last write wins), `abort_on_inconsistency` as a
dead knob the engine never reads (its twin cases should be digest-identical
on every reasoning probe), and `memory_profile` as a pure observational
wrapper. A dead knob confirmed differentially is a real finding — it tells
the rewrite what it need not implement behaviorally.

**Resume prompt.** `/campaign`

## Session 8 — 2026-07-06

**What we knew going in.** The harness stood at 34 cases with 27 of 52
public-surface rows cased, all passing oracle-vs-oracle with repeats green.
Session 7 had just reshaped the session protocol — two agents per session (an
author, then an independent reviewer-fixer who applies its own fixes), no
orchestrator re-verification, and the full-corpus sweep deferred to phase
boundaries. Three settings knobs looked caseable with no capture surgery:
canonical (believed a pure alias of persistent), abort_on_inconsistency
(hypothesized dead — no consumption site in the engine), and memory_profile
(believed an observational wrapper).

**What we learned this session.** All three beliefs held, and are now
evidence instead of hypotheses. Canonical is exactly persistent under a
second name — setting one flips the other's readback, last write wins
through either name, and the twins land digest-identical to the persistent
pair's two sides. Abort_on_inconsistency is confirmed dead at the pin: the
name never escapes the settings object, and an inconsistency-firing program
reasons identically with the knob on or off. Memory_profile only wraps the
reasoner in a peak-memory measurement and prints a line — every reasoning
digest is unchanged. Six new cases (corpus now 40), three rows flipped
(board now 30/52), review gate found one Medium and one Low wording defect
in case purposes, both fixed in-session. The two-agent session shape ran
end-to-end for the first time and worked as designed.

**What we expect to learn next session.** Whether the capture extension for
committed graphml fixtures is as small as believed, and whether
reverse_digraph actually reverses derivations under a direction-sensitive
rule while load_graph ignores it — plus load_graphml's happy-path behavior,
the first step into its malformed-attribute hazard cluster.

**Resume prompt.** `/campaign`

## Session 9 — 2026-07-07

**What we knew going in.** The corpus stood at 40 cases, 30 of 52 rows
cased, and every case's graph was inline — nothing exercised pyreason's
graphml file loader directly, and the reverse_digraph knob (believed a
load-time-only reversal that load_graph ignores) needed a committed fixture
to case. The board called load_graphml's attribute coercions a hazard
cluster of unknown loudness.

**What we learned this session.** The harness now takes committed graphml
fixtures as first-class case inputs, and the loader behaved as the pin
promised: reverse_digraph flips which node derives under a
direction-sensitive rule, the graphml path grounds byte-identically to the
inline path on the same graph, and an empty graph reasons cleanly. Two
sharper facts landed: the reverse-graph flag the engine kernels receive is
dead — passed into all three, read by none — and the whole
malformed-attribute cluster is silent coercion, never a raise; the nastiest
edge is that an attribute value of 0 (or a "0,1" pair) becomes a vacuous
fact that leaves no observable trace at all. Six new cases (corpus 46),
two rows flipped (board 32/52), review fixed one wrong analysis-doc claim
and one path-containment gap. The settings-knob phase is one packet from
its boundary.

**What we expect to learn next session.** Whether the parallel-computing
kernel runs laptop-local and reasons digest-identically to the serial one,
and what the output-to-file pair looks like once the harness grows a
file-output probe — the last two knob surfaces before the owed full-corpus
sweep at the phase boundary.

**Resume prompt.** `/campaign`

## Session 10 — 2026-07-07

**What we knew going in.** Two settings knobs stood between the campaign
and the settings-knob phase boundary: parallel_computing (unknown whether
the parallel kernel even runs laptop-local — the pin's own docstrings
promise a recompile every run) and the output_to_file/output_file_name
pair, which the harness flatly forbade because it had no way to compare a
file the oracle writes.

**What we learned this session.** Both knobs are now cased and the phase
is complete. The harness grew a file-output probe: the redirect file the
oracle writes is captured in a confined per-run directory, its timestamp
canonicalized, its contents compared exactly — and the redirect turned out
to be precisely what the pin reads as: cwd-relative, append-mode, never
closed, moving prints but never reasoning. The parallel kernel surprised
us in the good direction: it runs fine on this laptop, reasons
digest-identically to the serial kernel on the pair's program, and its
compile *caches across processes* (~174s once, ~3s ever after) — the
pin's "recompiles every run" belief is written in three places and wrong
in all three. Dispatch precedence (parallel beats fp_version) is pinned
behaviorally. Seven new cases (corpus 53), three rows flipped (board
35/52), review 0 High / 0 Medium / 3 Low, all settled.

**What we expect to learn next session.** Whether all 53 cases pass
together — the owed full-corpus sweep is the phase's verdict-of-record,
and any same-engine irreproducibility it surfaces is a harness defect to
root-cause, not a finding to absorb.

**Resume prompt.** `/campaign`

## Session 11 — 2026-07-07

**What we knew going in.** The settings-knob phase was complete on paper —
every knob row cased, corpus at 53 — but the phase's verdict-of-record was
owed: the full-corpus sweep had been deliberately deferred session after
session under the wall-clock rule, and until everything ran green in one
sitting, "the corpus passes" was a stitched-together claim, not a banked
one.

**What we learned this session.** Everything passes together: 53/53 cases
oracle-vs-oracle, zero divergences, zero irreproducibility, 22 minutes
wall-clock, with the parallel branch running warm exactly as session 10's
caching characterization predicted. The sweep also stress-tested the
harness's honesty disciplines in miniature: a first guess about two fast
timing outliers was checked against the banked artifacts and refuted, and
the residual is recorded as cause-unproven rather than dressed up as
explained. Nothing needed fixing, so the sweep banked directly — the first
session since the harness landed with no review gate, by the rule made for
exactly this case.

**What we expect to learn next session.** The breadth phase opens on the
accessor cluster: what the get-family accessors actually return at the pin
(fingerprint probes), and whether save_rule_trace's written traces can
ride the new file-output probe — the first test of that probe beyond the
knob that bore it.

**Resume prompt.** `/campaign`

## Session 12 — 2026-07-07

**What we knew going in.** The settings-knob phase had closed with a clean
53-case sweep, and the breadth phase opened on the accessor cluster: four
uncovered rows covering what the get-family accessors return and what
save_rule_trace writes — the first real test of the file-output machinery
beyond the knob that bore it.

**What we learned this session.** All four rows are cased (board 39/52,
corpus 59): the accessors return live objects — the same objects the
engine holds, pinned by identity so a copy-returning rewrite would fail —
and reset_graph nulls the interpretation; the trace saver writes exact,
comparable CSVs into the confined directory. The session's best lesson
was a caught mistake: the author observed empty trace names with
atom_trace off and generalized to "the CSV name fallback is dead code."
The independent reviewer refuted that live — inconsistent-predicate
complement rows bank names unconditionally, so the fallback fires exactly
there — and rescoped the claim on the board, in the case purpose, and in
the analysis doc. A rewrite that trusted the original claim would have
diverged on any IPL-bearing program. That is the two-agent shape doing
precisely what it exists for.

**What we expect to learn next session.** The last un-gated breadth rows:
the file-taking loaders (rules/facts from JSON, CSV, text file) and the
inconsistent-predicate/closed-world semantic loaders — after which the
board's remaining gaps all wait on operator decisions, and the Phase-3
fork (start writing the rewrite's reference core) is on the table.

**Resume prompt.** `/campaign`

## Session 13 — 2026-07-07

**What we knew going in.** The board stood at 39/52 rows cased after the
accessor/trace cluster, and the operator had adjudicated the three boundary
asks: one more breadth session (the un-gated loader/semantic rows) before
opening Phase 3, the raising-probe form approved as a packet, and the
peak-MB text canonicalization approved with per-case rationale. The
remaining un-gated rows were the five file loaders, the inconsistent-
predicate-list loader, and the closed-world registration.

**What we learned this session.** Both approved mechanisms landed and
immediately paid for themselves: the `apply_input` raising form banked
every loader's malformed-input arm (exception type + exact message, no
canonicalization on that path), and the peak-MB canonicalization unlocked
the memory-profile/output-file interaction case. Seventeen new cases (corpus
59 → 76) flipped all seven rows — the board is at 46/52, with only the four
type rows and the two callable-registering functions left. The review gate
caught the same failure class as last session, on the other side of the
same coin: the author generalized "a single-clause rule never shows the
closed-world assumption" from a screen where the predicate happened to be
stated; the reviewer's live screen showed that a wholly-unstated predicate
grounds *all* nodes and the single-clause rule fires everywhere. Two
sessions running, the sharpest finding is a scoped observation promoted to
"never" — the two-agent shape is earning its cost. One arm stays
deliberately un-cased and recorded: the closed-world non-string raise
carries a run-varying pointer-like token in its message, un-bankable
without a policy the operator hasn't approved (recommendation: leave it).

**What we expect to learn next session.** Whether the last six breadth rows
close — the four public types (constructor/DSL input classes) and the two
callable-registering functions, which need a named-function registry design
because Python callables can't ride the JSON case format. If they close,
the breadth grind is done, the next session is the phase-boundary
full-corpus sweep, and Phase 3 (the pure-Python reference core) opens with
the networkx dependency ask.

**Resume prompt.** `/campaign`

## Session 14 — 2026-07-07

**What we knew going in.** The board stood at 46/52 after the loader
packet, with six rows left: the four public types (Query, Threshold,
Interval, Label) and the two functions that register Python callables —
the awkward tail of the breadth grind, because callables can't ride the
JSON case format and two of the types aren't reachable through any other
public call.

**What we learned this session.** The breadth grind is done: **52 of 52
public-surface rows are cased.** The named-function registry solved the
callable problem (committed reference functions selected by name, compiled
at resolve time), queries now ride `reason(queries=…)`, and the two
unreachable types got direct-construction probes. Eighteen new cases
(corpus 94) banked some of the campaign's most rewrite-relevant contracts
yet: number thresholds gate at the clause level, not per head; the
unregistered-name asymmetry (annotation functions fail loudly, head
functions silently ground nothing); the Interval proxy and its jitted twin
disagree about where `intersection` seeds prev-bounds from; and two
behaviors the harness correctly refuses to bank — a query matching a
self-recursive rule crashes the pinned process outright, and non-compiled
registrands poison `reason()` with machine-path-bearing errors. The review
gate caught the third evidence-discrimination finding in three sessions
(a true clause-level claim whose cases couldn't discriminate it — fixed
with a discriminating case) and re-scoped a runtime hazard the author had
underestimated: every registrand capture was silently re-poisoning and
growing the oracle environment's compiled-kernel cache; the capture now
confines it with a snapshot/restore.

**What we expect to learn next session.** The phase boundary is here.
Next session is the dedicated full-corpus sweep — all 94 cases
oracle-vs-oracle in one run — which either banks the green
verdict-of-record that closes the harness-building phase, or surfaces
interaction defects the per-packet targeted runs couldn't see. After it
banks, Phase 3 (the pure-Python reference core) opens, starting with the
campaign's first rewrite dependency ask: networkx.

**Resume prompt.** `/campaign`

## Session 15 — 2026-07-07

**What we knew going in.** The breadth grind had just closed — all 52
public-surface rows cased by a 94-case corpus — but every session since the
last sweep had run only its own packet's targeted cases, per the wall-clock
rule. The phase boundary had arrived, and the rule's bill came due: one
dedicated session running everything, before Phase 3 opens.

**What we learned this session.** The harness phase closes clean. All 94
cases passed oracle-vs-oracle in one 46-minute sweep — zero divergences,
zero irreproducibility, and the spot-fix loop came up empty: not one line
of code needed touching. The independent audit earned its keep by trusting
nothing: it recomputed all 94 verdicts from the preserved artifacts through
the real compare layer, cross-checked the full board against the corpus
(every cased row cites exactly the cases that exist, no orphans either
way), and re-verified the oracle-env kernel cache carries no residue from
the registrand mechanism. Two low findings (a timestamp precision fix and a
noted last-writer-wins quirk in the summary artifact). The sweep also
confirmed session 14's cost prediction: the three callable-registering
cases dominate wall-clock because their dispatcher-bearing signatures can
never warm numba's cache.

**What we expect to learn next session.** Phase 3 — the pure-Python
reference core — opens, and its first action is a decision only the
operator can make: approving networkx as the rewrite's first runtime
dependency (the public boundary accepts NetworkX graphs, so graph loading
— the natural first spine slice — needs it). Once adjudicated, the next
sessions start proving rewrite-vs-oracle equivalence case by case, and the
board's `equivalent` column finally starts moving off 0/52.

**Resume prompt.** `/campaign`

## Session 16 — 2026-07-07

**What we knew going in.** The harness phase was closed (94/94
verdict-of-record), the operator had approved networkx as the rewrite's
first runtime dependency, and Phase 3 — the pure-Python reference core —
stood unblocked with nothing of the rewrite yet written. The board's
`equivalent` column sat at 0/52.

**What we learned this session.** The rewrite exists, and it starts life
equivalent. Its opening slice — an explicit-state core under the
module-global pyreason facade, with the settings facade, the Interval and
Label value types, the four public constructors and their validating
text-DSL parsers, the loader-family malformed arms, and the fresh-state
accessors — passed all twelve of the corpus's no-reason cases against the
oracle on the first banked run, and matched all 85 probe digests from the
banked sweep artifacts. Two design facts earned their keep: the src-tree +
wrapper layout keeps the rewrite off the oracle subprocess's import path
with zero install surface (ADR 0001), and the banked sweep artifacts work
as probe-level ground truth an author can hit before ever running the live
harness. The independent review fixed two real CSV-seam defects the twelve
fixtures alone would never have caught (record-ordinal line numbering on
quoted multi-line records; non-UTF8 faults dodging the pinned error wrap)
— vindication for the overfitting-probe lens. First two rows flip to
equivalent: Interval and Label, 2/52.

**What we expect to learn next session.** Whether the reasoning spine
itself — load_graph, rule and fact parsing on the happy path, the
fixed-point reason loop, the trace and the filter/sort accessors — can be
built to the same standard: hello-world green oracle-vs-rewrite, then the
smoke-class reason-bearing cases. That slice is where the engine's real
semantics (interval updates, rule grounding, convergence) start being
meaning-for-meaning reproductions rather than parser equivalence.

**Resume prompt.** `/campaign`

## Session 17 — 2026-07-07

**What we knew going in.** The rewrite existed but could not yet reason:
session 16 had landed the package skeleton, the value types, the four
constructors' parsers, and the loader malformed arms — everything around
the engine, none of the engine. The reasoning core itself, the campaign's
hardest piece, was untouched.

**What we learned this session.** The rewrite reasons, and it reasons
equivalently. The default-path spine — grounding, clause evaluation with
the full threshold-gating matrix, interval updates, the fixed-point
temporal loop with all four convergence modes, and the atom trace — landed
as pure functions over explicit state and passed all 13 of its cases
against the oracle, every probe digest byte-equal to the banked sweep. The
strongest signal came from the review: ten adversarially chosen probe
programs — threshold boundary arithmetic, delta-0 re-entry, inconsistency
arms, expiring facts, trace-ordering ties, even registered annotation and
head functions driven outside the harness — matched the oracle ten for
ten, with zero code fixes needed. Two structural facts surfaced: registrand
cases can't cross the harness into the numba-less rewrite env until
reference_fns gets a conditional-njit accommodation (queued), and the
board's Threshold row is the third to flip equivalent (3/52).

**What we expect to learn next session.** Whether the module-global
facade's cross-run state semantics — the reset family, reason(again),
persistence and canonicalization — reproduce the oracle's characterized
state-contamination behavior. That is where the explicit-state design
either pays off cleanly or meets the oracle's global-state quirks head-on:
fourteen lifecycle cases will say.

**Resume prompt.** `/campaign`

## Session 18 — 2026-07-07

**What we knew going in.** The rewrite could reason equivalently on the
default path, but only within a single run: the reset family, the resume
(`again`/`restart`) arms, and the persistence knobs — the oracle's
characterized state-contamination territory — were wired but unproven.

**What we learned this session.** The lifecycle is equivalent, quirks and
all. The reset family, the resume arms, and the persistent/canonical knobs
landed inside the existing explicit-state design with no architectural
change, and passed all fourteen lifecycle cases against the oracle. The
striking part is what "equivalent" required: the rewrite now deliberately
reproduces five characterized oracle defects at the public boundary — a
half-cleared program that AttributeErrors on get_time, the restart-true
clock-reset KeyError, a bare-again TypeError whose message is numba
implementation text, the silent no-op when again=True finds no program,
and grounding tables that outlive reset() — each named in the report as an
oracle-bug-candidate for eventual adjudication rather than silently
blessed. The review found nothing to fix at any severity: eight probe
families it invented (31 observations, including resume re-consuming the
same fact list twice) came back byte-identical across engines. Board:
8/52 equivalent.

**What we expect to learn next session.** Whether the remaining
settings-knob arms — inconsistency handling, update modes,
storage-off, the variant-selecting fp/parallel knobs that must all run the
same single reference core, static graph facts — hold to the same
standard over seventeen cases, which would leave only the I/O-and-graph
surface, the registrand family, and the pyyaml-gated IPL files between the
board and full-corpus territory.

**Resume prompt.** `/campaign`

## Session 19 — 2026-07-07

**What we knew going in.** The rewrite reasoned equivalently through the
default path and the full state lifecycle, but a third of the settings
surface — inconsistency handling, update modes, storage-off, and the two
knobs that in the oracle select among its three near-copy engines — was
still unproven, and those variant knobs were where the one-engine design
principle would face its first real test.

**What we learned this session.** All seventeen knob-arm cases pass, and
the one-engine principle survived contact: fp_version turned out to force
only a different iteration *schedule*, not different semantics — ADR 0003
records one semantics core under two pinned schedules, and the review
confirmed structurally that the oracle's parallel variant is byte-identical
to its default at the pin, so the rewrite's single core honestly serves all
knob combinations. The session also produced the campaign's best
demonstration yet of why the reviewer exists: among sixteen adversarial
probes, one caught the rewrite being *better* than the oracle — the
fp-mode dict view was silently correcting a pinned stale-edge defect — and
equivalence discipline required fixing the rewrite to reproduce the defect,
seam-tested. Six more oracle defects are named as bug-candidates. The
author agent was interrupted by a server error mid-packet and resumed from
its transcript without loss. Board: ten rows flip, 18/52.

**What we expect to learn next session.** Whether the graph-boundary
surface — graphml loading with its silent attribute-coercion hazard
cluster, reverse-digraph, attribute-fact stamping, closed-world
predicates, and the loader happy paths — reproduces cleanly; after that
only the output-file surface, the registrand family, and two gated
families stand between the board and Phase-3 breadth territory.

**Resume prompt.** `/campaign`

## Session 20 — 2026-07-07

**What we knew going in.** The rewrite was equivalent across 56 cases —
the engine, its lifecycle, and every settings knob — but the graph
boundary itself (graphml files, attribute coercion, edge reversal,
closed-world predicates) and the loaders' happy paths were unproven, and
the graphml attribute cluster was the campaign's characterized nest of
silent oracle coercions.

**What we learned this session.** The graph boundary is equivalent,
silence and all. All sixteen cases passed on the first banked run, with
the pin's all-silent coercion cluster deliberately reproduced rather than
cleaned up — three named oracle-bug-candidates — and the review's five
adversarial probes (inverted comma pairs, whitespace variants, bounds
riding reversed edges, closed-world collisions, expired static CSV facts)
came back byte-identical across engines while surfacing two further
oracle quirks for the candidate list. Zero defects to fix. The board
crossed half: eleven rows flip, 29/52 equivalent, with the un-run
remainder now enumerable on one hand — the output-file surface, the
registrand family behind a small harness accommodation, and the
pyyaml-gated IPL files.

**What we expect to learn next session.** Whether the output surface —
stdout redirection, the memory-profile line, saved trace CSVs, and the
query-filtering arms with their known recursion-crash contract —
reproduces cleanly; after that, Phase 3's breadth boundary sweep comes
into view.

**Resume prompt.** `/campaign`

## Session 21 — 2026-07-07

**What we knew going in.** The graph boundary had landed in session 20 and the
board had just crossed half (29/52). The next slice was the output surface —
about thirteen cases covering writing results to files, the memory-profile
line, the rule-trace CSVs, and the `queries` argument's rule filtering — with
the pyyaml ask already approved so the IPL file family sat unblocked behind it.

**What we learned this session.** The output surface is now equivalent, and the
review shape earned its keep: the author landed all thirteen cases green, but
the independent reviewer's own probes caught two real defects the cases had
missed — the rewrite raised an error on an empty filtered ruleset where the
pinned oracle quietly completes with zero rules on edge-heavy graphs, and it
raised the wrong exception type when saving a trace into a missing folder. Both
were fixed in-review and the packet now stands at fourteen-of-fourteen passing,
with a new regression case banked. The memory-profile line needed no new
dependency — the standard library's `resource` module reproduces the observable
shape. One open question went to the operator as DIV-0001: the rewrite
deliberately refuses (with a clean error) a pathological query input that
crashes the pinned oracle's process outright, and that intentional divergence
needs an operator signature the ledger trail doesn't yet carry. The board sits
at 47/52.

**What we expect to learn next session.** Whether the harness can be taught to
conditionally njit-wrap registered functions — the accommodation the registrand
family's five cases have been gated on — without disturbing any banked verdict,
and whether those five cases then prove equivalent end-to-end.

**Resume prompt.** `/campaign`

## Session 22 — 2026-07-07

**What we knew going in.** The output surface had landed in session 21 (board
47/52) and the last two gates were the registrand family — five cases blocked
on a harness accommodation, because the harness njit-wrapped registered
functions and the rewrite environment has no numba — and the IPL file family,
already unblocked by the approved pyyaml.

**What we learned this session.** The harness can be taught the difference: the
resolve seam now njit-wraps registered annotation and head functions only where
numba imports, so the oracle consumes them exactly as the pinned engine does
while the rewrite consumes them plain. The change provably disturbed nothing —
the reviewer recomputed every banked digest it could touch and found all
byte-identical. The five registrand cases then proved equivalent end-to-end,
and the review's probing caught one more real defect (the rewrite dressed up an
exception the pinned engine raises bare on an ungrounded head-function
argument), fixed in-review with a regression case banked. Eight of eight pass;
the board sits at 50/52 with only the IPL pair un-run. Mid-session the operator
set a binding boundary: the session loop stops when Phase 3 ends, and all
queued oracle-bug candidates and divergences get adjudicated in one batch
before Phase 4.

**What we expect to learn next session.** Whether the YAML
inconsistent-predicate-list path proves equivalent over its four cases — the
last un-run gate — leaving only the Phase-3 breadth boundary sweep, after which
the loop halts for the operator's adjudication batch.

**Resume prompt.** `/campaign`

## Session 23 — 2026-07-07

**What we knew going in.** After the registrand gate fell in session 22 the
board stood at 50/52 with exactly one gate left: the four IPL file cases,
unblocked since the operator approved pyyaml. The operator had set the
boundary: the loop stops when Phase 3 ends, with all oracle-bug candidates
adjudicated in one batch before Phase 4.

**What we learned this session.** The YAML inconsistent-predicate-list path is
equivalent — four of four cases pass, and the loader transcribes the pinned
parser faithfully down to raise order and null-overwrite semantics. The board
now reads 52/52 with every row run, and the reviewer re-derived that number
mechanically from the banked artifacts rather than trusting the reports. The
review's probing also found one divergence no exact-compare case can bank:
feeding the pin a non-string IPL entry raises an error whose message text
changes from process to process (it embeds an address), so the harness itself
scores the pin irreproducible on that input; the rewrite currently accepts the
entry. That went in as DIV-0002 with a proposed guarded raise, joining DIV-0001
in the operator's adjudication batch.

**What we expect to learn next session.** Whether the whole committed corpus
passes oracle-vs-rewrite in a single invocation — the Phase-3 boundary sweep
and verdict-of-record, after which the loop halts and the operator adjudicates
DIV-0001, DIV-0002, and the carried oracle-bug-candidate observations.

**Resume prompt.** `/campaign`

## Session 24 — 2026-07-07

**What we knew going in.** Every board row was run (52/52) after the IPL family
landed in session 23, but every banked verdict was slice-scoped — the phase
claim still needed the whole corpus through the harness in a single
invocation. The operator had set the boundary: stop after Phase 3, adjudicate
everything at once.

**What we learned this session.** Phase 3 is closed and the claim held: all 96
committed cases pass oracle-vs-rewrite in one twenty-five-minute run, with no
spot-fixes needed. The independent review re-derived every verdict from the raw
on-disk captures rather than trusting the summary, confirmed the run was one
coherent invocation, and reran a fifteen-case sample spanning every family with
byte-identical digests — the reference core is equivalent to the pinned oracle
over the full committed corpus. The review also audited the operator's
adjudication document for completeness and recovered five recorded
observations the author's sweep of the ledgers had dropped; the batch now
stands at forty-four sections — two divergence records with recommendations,
thirty-four oracle-bug-candidates, and eight observations needing no decision.
The loop stops here, as instructed.

**What we expect to learn next session.** The operator's adjudication verdicts
on the batch — chiefly the two divergence records and the three
direction-decisions — and then Phase 4 opens: the workload ladder, the oracle
baselines on this machine, and the profile that says where the time actually
goes.

**Resume prompt.** `/campaign` (after adjudicating docs/ledger/phase3-adjudication-batch.md)

## Session 25 — 2026-07-11

**What we knew going in.** Phase 3 was closed (96/96 oracle-vs-rewrite in one
invocation, independently re-derived) and the campaign was stopped on the
operator's between-phases gate: the forty-four-section adjudication batch —
two divergence records, thirty-four carried oracle-bug-candidates, eight
recorded observations.

**What we learned this session.** The operator adjudicated the entire batch,
accepting every recommendation as written. Both divergence records are now
adjudicated intentional behavior: the query-filter recursion guard stands
(the pin dies on that input; the rewrite terminates with the identical
reachable set on every input a case can bank), and the IPL loader now raises
a stable, honest ValueError on non-string entries at the exact seam where
the pin's typed container fails with an unreproducible garbage-memory
message — implemented at a single choke point both loader entry points pass
through, verified against the pin with live probes, with no committed case
changing verdict. The three direction decisions are on the record (the
fp+infer_edges payload gets the same honest-message treatment if ever cased;
the one-core-two-schedules answer to the fp trace asymmetry is confirmed;
the Interval proxy-arm choice is blessed), and the fp hang on
run-to-convergence is carried forward as the one hazard the Phase-4 workload
ladder must design around. Phase 4 is unblocked.

**What we expect to learn next session.** The shape of the workload ladder —
what small, medium, and large actually are, with rationale — and then the
first real performance numbers of the campaign: the oracle's cold-start,
per-rung throughput, and peak memory on this machine, each with a banked
noise band, which is the baseline every later execution-layer claim will be
measured against.

**Resume prompt.** `/campaign`
