<!-- doccode: pyreason-rewrite-docs-reviews-2026-07-06-expect-raise -->
# Review — the expect_raise capture extension (commit 3a1d32b)

Scope: the harness capture change adding the `expect_raise` probe kind, the optional
`inputs.reason` block, and the `inputs.ipl` input. One focused Opus reviewer (the change is
a contained two-file spine extension; the full two-reviewer gate ran on the harness itself
in [2026-07-06-harness.md](2026-07-06-harness.md)). Raw reviewer file:
[2026-07-06-expect-raise-raw.md](2026-07-06-expect-raise-raw.md). Findings: 1 High,
3 Medium, 1 Low.

Severity is calibrated to the deployment: a single-operator local harness on the
operator's own machines — every rating here is about wrong-verdict paths, not privilege.

## Dispositions

- **H1 (High — acceptance recorded as a bare `{"raised": false}` → false pass on
  accepted-boundary inputs): FIXED.** The acceptance branch now records a parse
  fingerprint (rule: name/type/target/head-variables/delta/bnd/clause-count; fact:
  pred/component/bound/type), so two engines accepting the same text into different
  parses cannot compare equal. The fingerprint also pins the pin's silent multi-digit
  delta consumption (`<-10` → `delta_t=10`) as a compared value
  (`rule-text-malformed:multichar-delta-consumed`). Regression-tested in
  `tests/test_capture_validation.py`.
- **M1 (Medium — `INTERP_PROBE_KINDS` had no drift guard; a future
  interpretation-consuming kind left out of it would crash as exit 1): FIXED.**
  `test_interp_probe_kinds_partition_the_probe_surface` asserts the probe surface
  partitions exactly into the interp set plus `{get_time, expect_raise}`.
- **M2 (Medium — `except Exception` conflates binding faults with parser rejections):
  PARTIALLY FIXED, remainder down-rated.** A missing `Rule`/`Fact` constructor now
  propagates as a capture failure (exit 1 with the artifact naming it) instead of being
  recorded as engine behavior. The residual case — a constructor arity mismatch whose
  `TypeError` is recorded as a rejection — is not distinguishable from a parser's
  legitimate `TypeError` without knowing the second engine's exception contract, and no
  second engine exists yet. Raw artifacts preserve the full message for diagnosis, and a
  mis-binding would present as a uniform all-probe divergence, not a quiet false pass.
  Revisit when the rewrite env lands.
- **M3 (Medium — exception identity was a short type name + verbatim message; cross-engine
  CPython-version wording differences would read as divergence): PARTIALLY FIXED,
  remainder deferred by design.** The recorded type is now module-qualified
  (`builtins.ValueError`), closing the short-name collision. The verbatim-message
  comparison across engines is a named future fork, not an absorbed one: the rewrite's
  error-message contract is itself an open design decision, and the per-probe comparison
  policy seam in each case record is where oracle-vs-rewrite message handling gets
  decided (per-case, with rationale — never a global normalization). Oracle-vs-oracle
  pairs share one interpreter and are unaffected.
- **L1 (Low — a `get_time` probe with no `reason` block now reads the no-interpretation
  fallback instead of post-reasoning state): DOWN-RATED, no change.** No committed case
  has that shape; the oracle's `get_time` guards the path by contract (returns 0), and
  the no-interpretation behavior is itself an enumerated input class on the board that a
  future case will exercise deliberately.

## Verified-safe notes carried from the reviewer

Constructor isolation at the pin (Rule/Fact constructors parse and store, mutating no
module global, so post-`reason()` constructions cannot perturb a mixed case), positional
signature agreement, `get_time`'s guarded no-interpretation path, deterministic parser
messages under the pinned hash seed, and the `[str, str]` ipl shape guard.
