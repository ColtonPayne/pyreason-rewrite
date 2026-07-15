<!-- doccode: pyreason-rewrite-hivemind-copy-ai-coding-pitfalls -->
> **Snapshot, not source of truth (operator-requested, 2026-07-15).** Verbatim copy of
> `$HIVEMIND_ROOT/docs/ai-coding-pitfalls.md`, committed so the GitHub mirror of this repo is readable
> without the hivemind checkout. The canonical file governs and edits land there; refresh
> this copy manually. Its cross-repo links resolve only beside a local hivemind checkout.

# AI-coding pitfalls — recurring patterns to watch

The hivemind codebases are built largely by AI coding agents, and the same mistakes recur
across all of them. The 2026-05-30 Santa-Method review of `lab-reasoner-cluster`
(see [code-review-playbook.md][ai-hivemind-docs-code-review-playbook]) surfaced ~43 findings, and most
cluster into a handful of **recurring agent behaviors** — not one-off mistakes, but tendencies
that will keep producing the same class of issue unless guarded against; later reviews in
local-rag, paper-tutor, and picoharness confirmed the same classes. Each below names the
trend, the concrete instances found, *why* an AI agent gravitates to it, and the guardrail.
This doc is the "what to stop doing"; each repo's CLAUDE.md carries its distilled rules.

> **Note:** the specific instances cited below are from `lab-reasoner-cluster` (the first
> review) and were **fixed** in the review follow-up (Tier 1–4 commits — correctness bugs,
> guard parity, error handling, dedup, and the I/O-seam tests). They're retained here as
> illustrations of the *pattern* to avoid, not as an open bug list.

---

## 1. Orchestration accretes in the CLI handler instead of a service layer
**Instances:** `cli.py` grew to 541 LOC; `cmd_models` is 117 lines doing the full
pull/cap/evict workflow; the 1 TB cap invariant lives in `cmd_models`, not `models.py`
(A1-1, A1-12, A2-5). Each new feature was added *into the command handler* rather than into a
module behind a thin handler.
**Why the agent does it:** adding code where the entry point already is, is the path of least
resistance — it works immediately and the diff is local. The cost (no reuse, no testable seam,
duplication) is invisible at write time and only shows up at review/roadmap time.
**Guardrail:** command handlers stay thin — parse args → call a function in the domain module
→ render. Business rules and invariants (e.g. "refuse a pull over cap") live in the module
that owns the data, so they can't be bypassed and can be unit-tested without the CLI.

## 2. Tests cover the pure helpers; the I/O seam ships untested
**Instances:** the suite was 82 green, yet the **headline** prospective-cap refusal,
`fetch_models` host-fallback, `Tunnel` lifecycle, `fetch_manifest_gib`, `run_repl`, and *every*
`cmd_*` success path had zero coverage (A3-1..A3-8). Pure functions (`parse_*`, `select_best`,
cap math) were tested well.
**Why the agent does it:** pure functions are trivial to test (no mocking), so the agent
writes those and feels "done" — the green count looks healthy. The wired-up behavior needs
monkeypatching `ssh.run`/`Popen`/the OpenAI client, which is more effort, so it's skipped.
**Guardrail:** "tested" means the *behavioral seam* is tested, not just the leaf helpers. For
every feature, add at least one test that drives the function that composes I/O (monkeypatch
the boundary: `ssh.run`, `subprocess`, the client). A green suite that skips the seams
overstates coverage — treat handler/seam tests as part of the feature, not optional.

## 3. Duplication instead of reuse — even when the helper already exists
**Instances:** the probe→select→"No GPU box available" block is copy-pasted across
`status`/`launch`/`endpoint` with byte-identical strings (A1-4); the scp+`sudo bash` pattern
is implemented twice — and the agent even *created* `_run_root_script` but never refactored
`cmd_setup` to use it (A1-2/A2-18).
**Why the agent does it:** when implementing command N it pattern-matches command N-1 and
copies, rather than extracting a shared helper — and when it does extract one, it doesn't go
back to retro-fit the earlier call site.
**Guardrail:** third occurrence ⇒ extract. When you add a helper, immediately migrate existing
call sites to it (or don't add it). Grep for the string/pattern you're about to write before
writing it.

## 4. Severity stated without anchoring to the threat model
**Instances:** four findings (ssh.options ProxyCommand, history path traversal, env-int crash,
REPL "double-save") were initially rated **High**; both independent verifiers down-rated all
four to Low/Medium because none crosses a privilege boundary for a single operator on their
own laptop (the documented threat model). One finding was a pure false positive (A2-5).
**Why the agent does it:** it recognizes a *mechanism* ("path traversal!", "injection!") and
reaches for the matching severity from training, without asking "who is the attacker, who is
the victim, and is there a boundary between them *here*?" Security checklists reward
pattern-spotting, not impact reasoning.
**Guardrail:** every security/severity claim must state the threat model and the boundary it
crosses. "Real mechanism, no privilege boundary in this deployment" = Low. Keep the calibration
explicit — this is why [security-model.md][ai-hivemind-docs-security-model] and each repo's `docs/security.md`
exist. Don't let a scary name set the severity.

## 5. Hardcoded literals that shadow an existing config field
**Instances:** the provision script hardcodes `:11434` in two places while `cfg.ollama.port`
exists and is threaded everywhere else (A2-6) — overriding the port silently breaks the
readiness check.
**Why the agent does it:** it inlines the "obvious" current value because that's what's true
right now, forgetting the same value is already a parameter elsewhere.
**Guardrail:** before hardcoding any value, grep for it — if it's already a config field or
constant, use that. Especially in generated scripts where the literal looks like "just text."

## 6. Forward-looking scaffolding left dead
**Instances:** `coder_model` is defined, merged, and documented but never read by any code
path (A2-19) — added in anticipation of a feature that wasn't wired.
**Why the agent does it:** it scaffolds for a planned future ("there'll be a coder mode") and
the field outlives the intent, becoming dead config that also escapes validation.
**Guardrail:** don't add config/fields/params until the code that consumes them lands in the
same change. If you must stage ahead, mark it clearly and track it; don't let it look live.

## 7. Guards applied to the obvious case, not consistently across entry points
**Instances:** `validate_config` covers `hosts`/`user`/`models_dir`/`keep_alive` but not
`ssh.options` (A2-1) or `args.host` from `--host` (verifier M1); `validate_model_name` is
enforced at the CLI boundary but not in the `models.*` functions themselves (A1-12, M4). The
hardening was real but *asymmetric*.
**Why the agent does it:** it fixes the instance in front of it (the reported sink) and stops,
without enumerating *all* paths that reach the same dangerous operation.
**Guardrail:** when adding a guard/validation, enumerate every entry point to the protected
operation and cover them all — or push the guard down to the single choke point they all pass
through. Parity, not point-fixes.

## 8. New features quietly add latency / change behavior of unrelated paths
**Instances:** adding the store-usage line to `cmd_status` introduced a **serial**
`fetch_models` SSH round-trip on top of the parallel probe (verifier M3) — a small UX
regression in an unrelated-feeling command.
**Why the agent does it:** it focuses on the feature's happy path and doesn't model the cost it
adds to the command's existing critical path (here, an extra per-host ConnectTimeout on a
down fleet).
**Guardrail:** when adding work to an existing command, ask "what does this add to the path
that already runs?" Make additive work best-effort/parallel/lazy if it can fail or block.

## 9. Dead fallbacks from not tracing the full call path
**Instances:** `repl.run_repl` has `model = model or conv.model`, but the only caller
pre-resolves `model = args.model or default` to a non-empty string — so the `conv.model`
fallback is dead and `--resume` silently uses the wrong model (A2-12).
**Why the agent does it:** it writes a locally-sensible fallback ("use the saved model if none
given") without tracing how the caller actually supplies the argument.
**Guardrail:** when writing a `x or fallback`, check what the caller passes — if it's always
truthy, the fallback is dead and signals a real bug upstream. Trace one level up.

## 10. Broad excepts and ad-hoc error/exit-code handling
**Instances:** `except Exception: pass` in `_unload`, a broad stream `except Exception` that
treats auth/404 the same as transient errors (A2-14/A2-15); exit codes decided per-handler
with a dead `return 2` and `persistence status` always returning 0 (A1-6); an env int-parse
that raises `ValueError` instead of the caught `ConfigError` (A2-3).
**Why the agent does it:** broad catches make the happy path "just work" and defer error
taxonomy; exit codes are assigned reactively per handler.
**Guardrail:** catch the narrowest exception that fits; if you swallow, log at debug. Keep exit
codes to a documented convention (0 ok / 1 operational / 2 usage-config) and route config
errors through the one exception the entrypoint catches.

## 11. Backward-looking comments that only parse with refactor context
**Instances:** (from the MINDSET project, 2026-06-04, the original surfacing of this rule)
module-level "X is a separate concern and lives in module Y" justifications written during an
extraction — true only as a contrast with the pre-refactor tangle a fresh reader has no reason
to expect; "reverting the previous design decision…", "now lives in…", "moved out of…",
"this used to…" framings that narrate the diff instead of explaining the code.
**Why the agent does it:** the comment is written from inside the change — the author explains
the edit to the reviewer instead of the result to the next reader. The framing is an artifact
of the author's head, not a property of the code, and it ages into noise the moment the prior
design is forgotten.
**Guardrail:** a comment must land for a reader who has only ever seen the current code — no
commit history, no prior chats. Before keeping one, ask "does this only make sense if you know
what changed?" If yes, cut it; change-rationale belongs in the commit message or an ADR.
Document dependencies present-tense at the point of use ("subjects are normalized via
`normalize_label`"), not as "these are separate concerns" justifications. Soft tells: "single
home for…", "now lives in…", "moved out of…", "this used to…", "reverted…".

## 12. Scoped `git add`, unscoped `git commit`
**Instances:** (umbrella, 2026-06-12, dev-log review finding #1) the hivemind-dev-log skill
ran `git add docs/dev-log/ && git commit -m "docs: dev log …"` — the `add` is scoped but the
`commit` takes the **entire index**, so anything the operator had staged when the 5 am timer
fired would be silently folded into the dev-log commit; staged non-docs content would also
flip which pre-commit gate fires.
**Why the agent does it:** add-then-commit is modeled as one atomic "save these files"
operation; the index as *shared mutable state* — co-owned by the operator and every
concurrent process — isn't in the mental model.
**Guardrail:** any commit made on a working tree the agent doesn't exclusively own
(automation, timers, parallel agents) pathspecs the commit itself:
`git commit -m … -- <paths>`. And concurrency around the index needs a real lock
(`flock`), not an idempotency argument.

---

### The meta-pattern
Most of these share one root: **the agent optimizes for "works now, locally" and under-weights
the costs that only surface later** — reuse, testable seams, consistency across paths, and
impact-calibrated judgment. The two structural antidotes that prevent the most issues:
**(a) keep handlers thin / put logic and invariants in modules**, and **(b) test the I/O seam,
not just the pure helper.** The two judgment antidotes: **state the threat model before rating
severity**, and **trace one level up before trusting a fallback.**

<!-- links:begin -->
[ai-hivemind-docs-code-review-playbook]: ../../../ai-hivemind/docs/code-review-playbook.md
[ai-hivemind-docs-security-model]: ../../../ai-hivemind/docs/security-model.md
<!-- links:end -->
