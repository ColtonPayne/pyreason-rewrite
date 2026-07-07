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
