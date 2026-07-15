<!-- doccode: pyreason-rewrite-hivemind-copy-security-model -->
> **Snapshot, not source of truth (operator-requested, 2026-07-15).** Verbatim copy of
> `$HIVEMIND_ROOT/docs/security-model.md`, committed so the GitHub mirror of this repo is readable
> without the hivemind checkout. The canonical file governs and edits land there; refresh
> this copy manually. Its cross-repo links resolve only beside a local hivemind checkout.

# Threat model — the shared single-operator deployment family

Written down per playbook P8: severity ratings are calibrated against *this* deployment, not
against pattern-matched training priors. This is the **shared base model** for every hivemind
repo; each repo's `docs/security.md` adds only its repo-specific trust boundaries and
consequences, and inherits everything here.

## Deployment family

Every hivemind tool is a **single-operator, own-laptop** tool:

- The operator (Colton) runs it by hand on his own machine. The agent (Claude Code) drives
  the CLI with the operator's privileges, in session, under the operator's eyes.
- There is no service surface: nothing listens, nothing is multi-tenant, no other principal's
  data is in scope.
- Local state (registries, DBs, vector stores) is single-writer on the laptop; where it
  reaches the lab it syncs out-of-band (syncthing), read-only.

The base trust table every repo starts from:

| Party | Trust | Capability |
|---|---|---|
| Operator | trusted | everything already (it's their account) |
| Agent-in-session | trusted-in-session | drives the CLI; same authority as the operator's shell |
| *(repo-specific party)* | **semi-trusted** | *defined in the repo's own `docs/security.md`* |

## Standing rules

- A finding must name **attacker, victim, and the privilege boundary crossed *in this
  deployment*** before it gets a severity above Low.
- A scary *mechanism* ("injection!", "path traversal!") that crosses no privilege boundary is
  **Low** — don't let the name set the severity.
- Anything reachable only by the operator attacking themselves on their own machine is **Low**.
- A tool that *advertises* confinement must honor it: a path that escapes a boundary the tool
  itself promises (rather than one the deployment never had) **is** a real finding even here.

## Re-evaluation triggers (consequential fork, P2)

Change the affected repo's `docs/security.md` — and revisit this document — *before* shipping
a change that:
- accepts input that is no longer operator-curated (untrusted third-party content),
- makes any store multi-writer or multi-tenant,
- starts listening on a socket or adds any shared writable surface,
- introduces a second human principal.

## The documented exception

`lab-reasoner-cluster` is the one repo that models a **second human tier**: in a shared
private repo, a committed `labreason.toml` config value can reach *another labmate's* (or
root's) execution via the provisioning scripts — a real cross-user, privilege-escalating
vector, and the reason its config-validation hardening exists. See
[`lab-reasoner-cluster/docs/security.md`][lab-reasoner-cluster-docs-security]. The
family default remains strictly single-human; treat labreason's stance as the template for
any future repo that grows a second principal.

## Per-repo deltas (the semi-trusted party in each)

| Repo | Semi-trusted input | Where it's written down |
|---|---|---|
| lab-reasoner-cluster | committed config / labmate values reaching root provisioning | [`docs/security.md`][lab-reasoner-cluster-docs-security] |
| local-rag | none today — registry is single-writer local, synced read-only to the lab | its `CLAUDE.md` (P8 section) |
| paper-tutor | paper content (external PDFs) flowing into agent context and stored glossary/question rows | [`docs/security.md`][paper-tutor-docs-security] |
| picoharness | the model under test, whose `run`-tool commands execute with operator privileges, confined by convention not containment | [`docs/security.md`][picoharness-docs-security] |

<!-- links:begin -->
[lab-reasoner-cluster-docs-security]: ../../ai-hivemind/lab-reasoner-cluster/docs/security.md
[paper-tutor-docs-security]: ../../ai-hivemind/paper-tutor/docs/security.md
[picoharness-docs-security]: ../../ai-hivemind/picoharness/docs/security.md
<!-- links:end -->
