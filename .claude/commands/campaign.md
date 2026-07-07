---
description: Run a pyreason-reimagining campaign session as an orchestrator of Fable-level subagents, then bank the plain-English wrap-up in the campaign log
---

Continue the pyreason reimagining campaign, acting as an **orchestrator**: you do the reading, decomposition, and banking yourself; you delegate the substantive work — including verification — to Fable-level subagents. One `/campaign` invocation runs **sessions in a loop** (Session loop, below), not a single session.

## Setup (do this inline, never via subagents)

1. Read this repo's CLAUDE.md, the charter it points to, and the newest `docs/ledger/session-<N>.md`.
2. Run the preflight doctor (`uv run python tools/hive_preflight.py`). If it is red, stop and report — no campaign work on a red preflight.
3. Take the session file's **NEXT** and decompose it into work packets. Prefer a few meaty, independent packets over many tiny ones.

## Session loop (operator-set, 2026-07-06)

A `/campaign` invocation does not stop after banking one session. After each session's wrap-up is banked and committed, **immediately begin the next session** from the just-banked NEXT: rerun the preflight (step 2), decompose the new NEXT (step 3), dispatch the two agents, bank. Repeat until one of these stops the loop:

- **An ask gate blocks the campaign** (Ask gates, below) — raise it interactively and wait; the loop ends with that session's wrap-up banked and the ask queued in its ledger.
- **The operator interrupts** — bank the in-flight session's wrap-up (even if it stalls mid-packet) before stopping.
- **Nothing unblocked remains** — every NEXT candidate is gated; bank the wrap-up naming the gates and stop.

Do not stop merely because a session completed cleanly, because the conversation is long (context is summarized and work continues), or because a phase boundary arrived — the phase-boundary sweep is itself the next session, not a stopping point. Between chained sessions, emit the three-line end-of-session message (Session wrap-up, below), then continue without waiting for a reply.

## Session shape — two agents (operator-set, 2026-07-06)

The ordinary session runs exactly two sequential `campaign-worker` agents:

1. **Agent 1 — author.** Does the packet's substantive work: authors the cases/code, writes the tests, runs the fast tier plus **only the e2e runs its own packet just added or changed**, commits at green, returns verdict + report path.
2. **Agent 2 — reviewer-fixer.** Independent (no shared context with agent 1): reviews agent 1's commits against the pinned source and the packet spec, **applies the fixes itself**, reruns the fast tier plus the same new/changed e2e runs, commits the fixes and the review report under `docs/reviews/`, returns verdict + report path.

**Do not verify twice.** The independent review *is* the verification — the orchestrator does not rerun tests, re-diff files, or re-execute measurements that agent 2 already verified. The orchestrator reads the two returned reports, checks they answer the packet spec, and banks.

**Full e2e corpus wall-clock rule (operator-set, 2026-07-06, supersedes the once-per-session form):** the full corpus/e2e sweep does **not** run every session. It runs only at a **phase boundary** — when the ledger's NEXT moves to a new phase of work — as a dedicated session of its own: run everything, spot-fix what surfaces, bank the verdict-of-record. Between boundaries, each session's evidence is the fast tier plus its own new/changed e2e runs, and the deferred sweep is named in the ledger so no boundary passes silently.

## Orchestration rules

- Dispatch each packet with the Agent tool using `subagent_type: "campaign-worker"` (pinned to Fable at **effort: high** in `.claude/agents/campaign-worker.md` — do not override its model or effort downward). Operator note, 2026-07-06: the operator authorized Fable-tier subagents for `/campaign` sessions, superseding the charter's Opus cap; the charter's **12-concurrent cap still holds** — a larger fan-out is an ask, every time.
- Subagents share none of your context, so every prompt must be self-contained: the absolute repo path, the relevant charter/ledger excerpts pasted in (not referenced), the exact acceptance criteria, where to write the full report, and precisely what to return (verdict + report path + reproduction commands).
- Restate the repo's hard rules in **every** subagent prompt: `oracle/pyreason/` is read-only and never modified or rebuilt; the oracle pin never moves without operator adjudication; no installs or dependency changes; fast-tier tests must stay green.
- Run independent packets in parallel (one message, multiple Agent calls); sequence dependent ones. Use SendMessage to continue an existing subagent rather than respawning when iterating on its packet.
- **Verification is agent 2's job, once.** Do not re-verify what the reviewer-fixer verified (Session shape, above) — the orchestrator banks from the two reports. What the orchestrator still owns: reading both reports, confirming the packet spec's acceptance criteria are each answered, and refusing to bank a report that crossed a gate or skipped a criterion (that packet is failed and redone, not patched by you).
- **Test-tier discipline:** every subagent prompt restates the wall-clock rule from Session shape — workers run the gate's fast tier and only the e2e runs their packet adds or touches; the full corpus sweep is a phase-boundary session, never a per-session step.

## Context discipline — files, not chat

The point of this skill is that the orchestrator's session survives long campaigns without its context ballooning. Therefore:

- **Never emit substantive prose as chat output tokens.** Every artifact — ledger session file, wrap-up, packet syntheses, review notes, queued asks — is written to a file (Write tool, or a worker writing its own report). Your chat messages are one-line status pointers to file paths, nothing more.
- Don't paste file contents or subagent reports back into chat; reference them by path.
- The end-of-session final message is exactly three lines: the session's one-line verdict, the path to the wrap-up in `docs/ledger/campaign-log.md`, and the one-line resume prompt. The wrap-up itself lives in the file, not in chat.
- You — not a subagent — write `docs/ledger/session-<N+1>.md`, following `docs/ledger/README.md` (verdict, evidence, commits, single NEXT), and make whatever commits the session protocol calls for.

## Ask gates — interrupt the operator, never decide alone

The charter's Permission charter section is binding and orchestration does not dilute it. At any of these gates, **stop and ask the operator interactively** (AskUserQuestion, with options and a recommendation) before proceeding:

- **Any dependency change or install, anywhere** — `uv add`, pip, a new environment, the oracle's runtime set included.
- **Moving the oracle pin.**
- **Any write outside the campaign repo** (beyond session 0's documented lrag bootstrap).
- **The execution-layer commitment** — adopting an acceleration approach as the shipped core.
- **Fan-out beyond 12 concurrent subagents; any paid-API spend.**
- **Anything ambiguous — the ambiguous case defaults to asking.**

Gate discipline under orchestration:

- Gate decisions are **yours to surface and the operator's to make** — never delegate one to a subagent, and never accept a subagent's output that quietly crossed a gate (treat that packet as failed and redo it inside the rules).
- If a gate blocks the current thread, follow the charter's queue-and-continue semantics: write the ask into the ledger, commit, and move to the next unblocked packet — but still raise the ask interactively rather than only batching it silently. Batch non-blocking asks and queued divergences for the operator at the session boundary, alongside the wrap-up.

## Session wrap-up (always, even if the session stalls or fails)

1. Write the plain-English wrap-up with exactly these parts:
   - **What we knew going in** — the state of the campaign before this session, in plain English.
   - **What we learned this session** — the new information or capability this session produced, in plain English.
   - **What we expect to learn next session** — what NEXT should reveal.
   - **Resume prompt** — a one-line copy-paste prompt for a fresh session (normally `/campaign`, or a plain-prose line if the command isn't available).
2. Append that wrap-up verbatim to `docs/ledger/campaign-log.md` under a `## Session <N+1> — YYYY-MM-DD` heading. If the file doesn't exist, create it with a one-paragraph header explaining it's the running plain-English narrative of the campaign, one entry per session, newest last. Commit it alongside the session's ledger file.
3. End-of-session chat message: exactly three lines — the session's one-line verdict, the campaign-log path, and the one-line resume prompt (per the context discipline above, the wrap-up prose lives only in the file). Then, per the Session loop, continue straight into the next session unless a stop condition holds; the resume prompt line matters most on the loop's final message, where it is what a fresh instance copy-pastes.
