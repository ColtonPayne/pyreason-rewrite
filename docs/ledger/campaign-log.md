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
