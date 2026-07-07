<!-- doccode: pyreason-rewrite-docs-reviews-2026-07-06-settings-knob-cases -->
# Review report — the settings-only knob cases (fp engine, update-mode trio, ground-rule pair)

Scope: the six-case authoring commit (`d685af2`) and the board/run commit
(`2b8948a`). One focused Opus reviewer with no shared session context — the
umbrella's scaled-down form for a contained case-only extension (same deviation
as the session-3/4/5 gates; recorded in the ledger). Raw reviewer output:
[2026-07-06-settings-knob-cases-raw.md](2026-07-06-settings-knob-cases-raw.md).

The reviewer found no false-pass and no material overstatement: every purpose,
board note, and source-mechanism claim was verified against the banked run
artifacts and the pinned oracle source. The junk-string twin equality was
re-derived from the banked digests (equal to the default twin on all four
reasoning probes, differing only in the knob readback), the override case
confirmed observably different by absolute pinned values (not by cross-case
comparison, so it stays non-vacuous under the harness's per-case judging), the
ground-rule pair's one-vs-two derivations traced to the `_ground_rule`
constant-in-node-set short-circuit, and the fp engine-selection precedence
confirmed at the pin. Board flips (24/52 cased) and per-row case-id placement
verified exact.

## Fixed

- **L1 (Low)** — the fp-version-on `purpose` stated the fp-vs-optimized
  difference (same final bounds, different traces and last-frame row order) as
  bare fact, without the "verified at authoring" hedge the junk-string case
  carries — the harness judges each case fp-vs-fp and never enforces that
  cross-knob comparison. The purpose now says the comparison was verified
  against the banked hello-world artifacts at authoring and that the harness
  judges the case fp-vs-fp only, making the six records uniform.

## Deferred with rationale

None — the single finding was fixed in-session.
