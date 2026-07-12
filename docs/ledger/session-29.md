# Session 29 — the carried breadth thread lands: registrand L3 arms, edge-rule head functions, and B17 becomes DIV-0003

Date: 2026-07-12

## Verdict

**The breadth seeds carried since session 22 are landed.** The slice-2
L3 registrand arms (return-shape and duplicate-name behaviors) and the
edge-rule head-function forms are cased and green — **6 new cases, all
PASS oracle-vs-rewrite** (8/8 in the review's rerun including
non-disturbance controls); L4 re-verified unreachable through every
public input and recorded. **B17 is implemented as the operator
pre-authorized** (session 25): the fp `_add_edge` existing-edge branch
now raises a stable, honest `KeyError` where the pin dies payload-less
at the same seam — filed as **DIV-0003, adjudicated on filing**, with a
passing pin-side reproducer. The review caught and fixed one real
modeling defect (the pin's annotate return coercion is **tuple-only**;
the author's len-based model accepted size-2 lists the pin rejects —
fixed to pinned behavior, seam-tested, no banked case was wrong). Fast
tier **297**; board input classes widened on both registrand rows.

## Evidence

- **Author report:**
  [docs/reviews/2026-07-12-breadth-registrand-edgerule-author.md](../reviews/2026-07-12-breadth-registrand-edgerule-author.md)
  — the L3 arms, the SHADOWS reject-arm mechanism in
  harness/reference_fns.py (add-only; resolve() untouched), the 6
  cases, the B17 implementation, the cache-audit disclosure.
- **Independent review (approved-with-fixes):**
  [docs/reviews/2026-07-12-breadth-registrand-edgerule-review.md](../reviews/2026-07-12-breadth-registrand-edgerule-review.md)
  — every claimed pin raise shape re-derived from the pinned source
  AND re-screened in fresh oracle-env processes (2 per arm,
  byte-identical); F1 the tuple-only fix; SHADOWS non-disturbance
  proven by rerunning two previously-banked cases with all 8 digest
  sets byte-identical; B17/DIV-0003 verified verbatim against the
  session-25 adjudication record; L4 unreachability re-derived.
- **DIV-0003:** [docs/divergences/DIV-0003.md](../divergences/DIV-0003.md)
  — intentional divergence, status adjudicated (pre-authorized, batch
  §B17); reproducer `tests/test_div_0003_reproducer.py` (e2e, passes).
  The arm stays case-less per DIV-0002's precedent (raise messages
  differ by adjudicated design; the record + reproducers carry the
  evidence).
- **Cache correction of record (review F2):** the oracle-env numba
  cache's banked 237-file baseline itself contains four pre-session-29
  `.2.nbc` entries (dated 2026-07-07) whose indexes embed
  `harness.reference_fns` and hard-fail unpickle where `harness` isn't
  importable — a latent portability quirk of the baseline, not a
  session-29 leak (the session's own leak was 4 further files, cleanly
  removed and verified digest-identical to session 15).
  **Re-baselining recommended; queued as a non-blocking operator ask.**
- **Tests:** `uv run pytest -m "not e2e"` → 297 passed, 5 deselected;
  cases 6/6 PASS (author) and 8/8 PASS incl. controls (review);
  DIV-0003 reproducer 1 passed; inventory gate 6 passed; oracle pin
  byte-clean.

## Committed

- `4914cff` — engine+harness: L3 raise-shape reproductions; fp
  `_add_edge` adjudicated KeyError; reference-fn reject arms; 7 seam
  tests.
- `60350c6` — docs: DIV-0003 filed adjudicated + pin-side reproducer.
- `0efb82b` — cases+board: 6 cases; both registrand rows widened.
- `6c38c56` — docs: session-29 author report.
- `2654a1e` — review fix: annotate coercion tuple-only, per fresh pin
  screens; seam test; citation fixes.
- `2d22328` — docs: session-29 review report.
- (this commit) — ledger: session 29 banked; campaign log continued.

## NEXT

**The remaining carried case seeds, as one batch session:** the
`raise_errors=False` warn-skip arms; the loader-input widenings
(ragged-CSV, interval-nonnumeric, weights-dtype, `delta_t` variants);
`interacts-unknown-predicate`; and — where the screen shows them
bankable — the O1/O2 graphml coercion arms (session-20 seed: the
`'1,0'` static-pin variant and the whitespace asymmetry, batch
§B23/§B24). Same discipline: pin screens first, cases only for
deterministic arms, divergences filed never absorbed, fast tier +
own-case e2e only. After that batch the unblocked queue is
harness-quality seeds (sweep durability, `probe_s` timing, prange
characterization, artifact-schema `inputs` echo, pyyaml parity
tripwire) — take them next if the execution-layer word still hasn't
come; the full-corpus sweep remains reserved for the Phase-4 boundary
after the operator signs.

**Blocked asks standing:** (1) the execution-layer commitment
([docs/perf/execution-layer-options.md](../perf/execution-layer-options.md),
recommendation B); (2) new, non-blocking: oracle-env numba-cache
re-baseline (review F2).

## Deviations

- None from the session shape.

## Asks queued

- **Execution-layer commitment** (carried, blocking Phase-4 closure):
  the memo with recommendation B.
- **Oracle-env cache re-baseline** (new, non-blocking): four
  pre-existing baseline cache entries embed `harness.reference_fns`
  and are import-fragile outside the repo root (review F2, evidence in
  the session-29 review report §F2). Recommendation: regenerate the
  cache baseline once from a bare capture sweep and re-bank the file
  count + digests; until then the quirk is recorded and harmless in
  situ.

## Divergences

- **DIV-0003 — opened and adjudicated in one motion** (pre-authorized
  by the session-25 batch adjudication of B17); implemented, seam-
  tested, reproducer banked.

## Idea seeds

- A `numba _load_index` unpickle-fragility note for any future
  cache-portability work (from review F2).
- Carried: sweep durability; `probe_s` timing; multi-rule prange
  characterization; pyyaml-version parity tripwire; artifact-schema
  `inputs` echo; `raise_errors=False` warn-skip arms; ragged-CSV /
  interval-nonnumeric / weights-dtype / delta_t;
  `interacts-unknown-predicate`; O1/O2 coercion cases.
