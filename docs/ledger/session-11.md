# Session 11 — the phase-boundary full-corpus sweep: clean, banked directly

Date: 2026-07-07 (continuing the 2026-07-06 sitting)

## Verdict

The settings-knob phase's verdict-of-record: **CLEAN SWEEP — 53/53 cases
pass oracle-vs-oracle, zero divergent, zero irreproducible, zero error,
1331 s (22 m 11 s) total wall-clock**, fast tier 70 passed before and
after, preflight 10/10, oracle clean at `e1a94af33e1f` throughout. No code
was touched anywhere in the session, so per session 10's NEXT the sweep
banked directly on its run log with no reviewer session. The standing
no-silent-boundary marker is discharged; the phase closes with every
committed case green in one sitting.

## Evidence

- **The sweep:** one runner invocation per case over all 53
  `harness/cases/*.json` (census 53 files, 53 distinct ids), sorted order,
  `PYTHONHASHSEED=0 uv run python -m harness.run --cases <case> --engine-a
  oracle-env/bin/python`, self-proof mode, 4 fresh-process captures per
  case, same-engine repeats by exact digest. Every invocation exited 0
  with `ALL PASS`; runner output uniform across all 53 (no stderr leakage,
  no stray lines — grep-verified).
- **Schedule discipline:** screen-then-confirm honored — three
  representative cases timed first (~26 s each → ~23 min estimate,
  confirmed 22 m 11 s); the parallel branch ran warm as predicted (the
  session-10 `.nbc` cache untouched; no cold-compile capture occurred).
- **Timing:** mean 25.1 s, median 27 s, band 24-28 s, no slow outliers.
  Seven fast outliers: five explained by banked `timing` blocks
  (expect-raise cases never reason; reset cases do no reasoning;
  graphml-empty reasons in 1.47 s); two (the attr-parse-off pair, ~1.5
  s/capture below their attrs-on siblings) sit in uninstrumented capture
  time and are **recorded cause-unproven** — an observation, not a
  finding; no verdict rides on wall-clock. First hypothesis ("lighter
  probe set") was checked and refuted before recording.
- **Taxonomy note for the record:** in self-proof mode `divergent` is
  unreachable (`harness/run.py` judges any cross-pair mismatch with
  engine_a == engine_b as `irreproducible`); no branch of the taxonomy
  beyond `pass` was exercised.
- **Artifacts:** run log (per-case verdict + wall-clock table, totals,
  outlier analysis):
  [docs/reviews/2026-07-07-phase-boundary-sweep-log.md](../reviews/2026-07-07-phase-boundary-sweep-log.md);
  report:
  [docs/reviews/2026-07-07-phase-boundary-sweep-raw.md](../reviews/2026-07-07-phase-boundary-sweep-raw.md).
  Engine fingerprint in every banked artifact: pyreason 3.6.0, python
  3.10.20, darwin, PYTHONHASHSEED=0.

## Committed

- `02d392e` — harness: phase-boundary sweep — 53/53 clean; run log +
  report.
- (this commit) — ledger: session 11 banked; campaign log continued.

## NEXT

**Open the breadth phase on the accessor/trace-output cluster** — four
uncovered fn rows in one coherent packet: `fn:get_rules`,
`fn:get_logic_program`, `fn:get_interpretation`, `fn:save_rule_trace`.
Read each anchor at the pin first and enumerate the input classes per row
(that enumeration is the analysis work). Expected shape: (a) the
get-family accessors need fingerprint probes (the carried idea seed) —
what each returns, how it canonicalizes, whether it is stable across
same-engine repeats; (b) `save_rule_trace` writes trace files the
session-10 `output_file` probe can now compare — read the pin for what it
writes where (likely CSV, not `.txt`; extend the probe's glob/confinement
as needed, validation parity maintained, faults exit 2); (c) twin/probe
cases per enumerated class over existing programs (hello-world and one
multi-timestep trace-bearing program), run targeted (fast tier + only the
new cases), flip the four rows, bank via review with the two-agent shape.
Uncovered classes that need the raising-probe form stay named, not
absorbed.

## Deviations

- Single-agent session: session 10's NEXT pre-authorized banking a clean
  sweep directly without the reviewer-fixer; the sweep was clean and
  touched no code, so the two-agent shape did not apply.
- The sweep agent's first run was cut off by a transient server error
  mid-loop and resumed with context intact; no work was lost and no
  campaign artifact was affected (recorded for completeness, not as
  friction — the substrate was not involved).

## Asks queued

None blocking. Carried for operator triage at this boundary, unchanged
from session 10:
- The raising-probe form (apply-inputs-expecting-raise) — one probe shape
  unlocking `type-reject` family-wide, `load_graphml`
  missing-file/bad-content, and the `"0.5.5"` float-guard raise.
- The `memory_profile`/`interaction-output` text-canonicalization policy
  (canonicalize the run-varying peak-MB line, rationale recorded per
  AC-2's per-case normalization contract).

## Divergences

None opened — clean sweep, oracle-vs-oracle.

## Idea seeds

- A `probe_s` timing field in the capture would make the uninstrumented
  capture-time residual attributable for free (born of the sweep's one
  unproven outlier pair).
- Multi-path `--cases` (carried; the sweep ran 53 invocations where one
  could do — felt directly this session).
- Carried: multi-rule prange characterization case; `REASON_ARGS` from
  the pinned signature; artifact-schema echo of `inputs`.
