---
description: Run a pyreason-reimagining campaign session as an orchestrator of Fable-level subagents, then bank the plain-English wrap-up in the campaign log
---

Continue the pyreason reimagining campaign, acting as an **orchestrator**: you do the reading, decomposition, verification, and banking yourself; you delegate the substantive work to Fable-level subagents.

## Setup (do this inline, never via subagents)

1. Read this repo's CLAUDE.md, the charter it points to, and the newest `docs/ledger/session-<N>.md`.
2. Run the preflight doctor (`uv run python tools/hive_preflight.py`). If it is red, stop and report — no campaign work on a red preflight.
3. Take the session file's **NEXT** and decompose it into work packets. Prefer a few meaty, independent packets over many tiny ones.

## Orchestration rules

- Dispatch each packet with the Agent tool using `subagent_type: "campaign-worker"` (pinned to Fable at **effort: high** in `.claude/agents/campaign-worker.md` — do not override its model or effort downward). Operator note, 2026-07-06: the operator authorized Fable-tier subagents for `/campaign` sessions, superseding the charter's Opus cap; the charter's **12-concurrent cap still holds** — a larger fan-out is an ask, every time.
- Subagents share none of your context, so every prompt must be self-contained: the absolute repo path, the relevant charter/ledger excerpts pasted in (not referenced), the exact acceptance criteria, where to write the full report, and precisely what to return (verdict + report path + reproduction commands).
- Restate the repo's hard rules in **every** subagent prompt: `oracle/pyreason/` is read-only and never modified or rebuilt; the oracle pin never moves without operator adjudication; no installs or dependency changes; fast-tier tests must stay green.
- Run independent packets in parallel (one message, multiple Agent calls); sequence dependent ones. Use SendMessage to continue an existing subagent rather than respawning when iterating on its packet.
- **Verify before you bank.** Do not accept a subagent's claims on trust: rerun the tests it cites, diff the files it says it changed, re-execute the measurement that forces its verdict. Only verified results go in the ledger.
- **Test-tier discipline (wall-clock rule, operator-set 2026-07-06):** the full `e2e` suite runs **at most once per session, after review fixes are in** — never as a pre-work baseline and never as pre-review evidence. For a review, the fast tier green plus the packet's **new/changed tests passing** is sufficient evidence. Restate this in every subagent prompt: workers run the gate's fast tier and the specific tests their packet adds or touches, nothing broader. When the session's verdict needs the full-e2e run, dispatch it as its own dedicated `campaign-worker` packet after review fixes land — **you never run it yourself**; the worker banks the run's report to a file and returns verdict + path, which you verify by reading the report before banking.

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
3. Final chat message: exactly three lines — the session's one-line verdict, the campaign-log path, and the one-line resume prompt (per the context discipline above, the wrap-up prose lives only in the file).
