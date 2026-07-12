<!-- doccode: pyreason-rewrite-docs-ledger-lab-compute-waiver -->
# Operator adjudication — lab-compute waiver for the scaling experiments

Date: 2026-07-12 · Status: **active** · Granted by: the operator, in session, verbatim
("waiver approved" / "permission granted")

## What is waived

This repo's hard rule **"No lab compute, at all"** and, for this campaign only, the
umbrella's Tier-2 rule ("an agent never runs a command on lab compute",
[ADR 0006][ai-hivemind-docs-adr-0006-tiered-lab-execution]) are waived **for the
following scope and nothing wider**:

- **Host:** `sanders.syr.edu` (lcs-pashakar-02, 512-core CPU box, 1.5 TB RAM) only.
  Never the GH200 fleet (`gottfried0{1..4}`), never `godel`/`redmond`.
- **Account:** `crpayne`, via the operator's existing keyless SSH. No sudo, ever.
- **Purpose:** this campaign's scaling experiments on larger graphs (first: the
  PyReason-paper §4 replications, Pokec oracle-vs-rewrite). Nothing else runs there.
- **Installs:** user-home only, each one **logged** in
  [docs/lab/sanders-install-log.md](../lab/sanders-install-log.md) (operator condition:
  "Log here everything you install to lab compute that wasn't there before").
- **Etiquette:** never interrupt running jobs (operator condition); check load before
  long runs and leave headroom; stay out of `/data` and other users' trees.
- **Long runs** execute inside `tmux` on the box so VPN drops don't kill them.

## What is not waived

Everything else stands: the oracle pin discipline, no pushes without ask, the
screen-then-confirm measurement rule, consequential forks to the operator. The umbrella's
rule is untouched for every other repo and host.

## Revocation

The operator revokes by saying so; the waiver dies immediately, remaining remote jobs are
torn down on next contact, and this record's status flips to revoked. The waiver also does
not outlive the campaign.

<!-- links:begin -->
[ai-hivemind-docs-adr-0006-tiered-lab-execution]: ../../../ai-hivemind/docs/adr/0006-tiered-lab-execution.md
<!-- links:end -->
