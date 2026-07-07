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
