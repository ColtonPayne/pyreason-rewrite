# Session 22 — the registrand gate falls: accommodation + 8/8; board 50/52

Date: 2026-07-07 (continuing the 2026-07-06 sitting)

## Verdict

The registrand packet landed: the `harness/reference_fns.resolve()`
conditional-njit accommodation (njit-wrap where numba imports — the
oracle env consumes registrands as the pin does, the rewrite env
consumes them plain), then the registrand family run end-to-end
through it. The oracle path is **provably unchanged**: the review
recomputed both non-disturbance cross-checks (18/18 digests
byte-identical to the banked slice-2 and session-15 artifacts). The
author's 5/5 + 2/2 spot-check survived review with **one probe-caught
rewrite defect fixed in-review** (the ungrounded head-fn-argument arm
raised a decorated `KeyError` where the pin's typed-dict getitem
raises the bare one — fixed to pinned behavior, regression case
banked). Final: **8/8 oracle-vs-rewrite PASS**, fast tier **265**,
board **50/52** — the un-run remainder is exactly the IPL pair.

**Operator instruction (2026-07-07, binding):** the campaign session
loop **stops when Phase 3 ends** — the operator adjudicates all
queued oracle-bug candidates and divergence records between Phase 3
and Phase 4. The boundary-sweep session is Phase 3's last; after it
banks, the loop halts with the adjudication batch prepared.

## Evidence

- **Author report:**
  [docs/reviews/2026-07-07-phase3-slice7-author.md](../reviews/2026-07-07-phase3-slice7-author.md)
  — the accommodation + 5/5 registrand cases into
  `results-phase3-slice7/`; spot-check pair unchanged; oracle captures
  byte-identical to the pre-accommodation session-15 sweep; slice-2
  L3/L4 deferred with rationale (arms unreachable through every
  committed reference function/case).
- **Review (verdict of record):**
  [docs/reviews/2026-07-07-phase3-slice7-review.md](../reviews/2026-07-07-phase3-slice7-review.md)
  — independent 7/7 rerun (28/28 digests identical), both
  cross-checks recomputed, cache at the 233-file zero-residue
  baseline after every run; 5/5 discriminating probes (swapped
  fn-arg-order both-kinds capture, post-reset re-registration, 6-arg
  cap arm, broken-numba ImportError propagation — never a silent
  plain-arm downgrade, and the ungrounded-var screen that caught
  **F1**); F1 fixed via `TypedComponentDict` container semantics,
  raise records byte-equal post-fix; board 50/52 verified
  mechanically (3 flips: fn:add_annotation_function,
  fn:add_head_function, fn:reset_rules).

## Committed

- `f5f3680` — harness: the conditional-njit accommodation + resolve-arm
  seam tests.
- `3339446` — tests: resolve-to-rewrite-engine integration seam test.
- `f94bc90` — docs: board — three rows flip (50/52); slice-7 gitignore.
- `0b670a2` — docs: slice-7 author report.
- `bab41d8` — engine: review fix — the ungrounded head-fn arm raises
  the pin's bare KeyError; regression case banked.
- `143a53f` — tests: broken-numba discriminator seam test.
- `f3b1418` — docs: independent review — packet passes after one fix.
- (this commit) — ledger: session 22 banked; campaign log continued.

## NEXT

**Land the IPL file family — proven oracle-vs-rewrite over its 4
cases** (`ipl-load-basic`, `ipl-load-malformed`,
`ipl-load-null-overwrite`, `ipl-atom-trace-off-trace` — the
`load_inconsistent_predicate_list` YAML path, unblocked by the
operator-approved pyyaml 6.0.3 in the campaign env; the oracle env's
own pinned pyyaml untouched). That closes the last un-run gate:
after it every board row is landed or adjudication-pending, and the
next session is **Phase 3's close — the breadth boundary sweep**
(run everything, spot-fix what surfaces, bank the verdict-of-record).
Per the operator instruction recorded above, the loop **stops after
that sweep banks**, with all oracle-bug candidates and DIV records
batched for adjudication.

## Deviations

None — the two-agent shape ran as specified.

## Asks queued

- Carried, non-blocking: **DIV-0001** adjudication (the query-filter
  recursion guard) — part of the operator's announced
  end-of-Phase-3 adjudication batch.

## Divergences

None opened — F1 was fixed to pinned behavior, not absorbed; DIV-0001
carries unchanged.

## Idea seeds

- Registrand-behavior packet (slice-2 L3/L4 arms — now reachable
  through the accommodation; needs new cases).
- Edge-rule head-function forms still named-unobserved on the board.
- Carried: fp+`infer_edges` exception-payload asymmetry; ragged-CSV /
  interval-nonnumeric / weights-dtype / delta_t cases; sweep
  durability; `probe_s` timing; multi-rule prange characterization;
  artifact-schema `inputs` echo; `interacts-unknown-predicate`;
  `raise_errors=False` warn-skip arms; O1/O2 graphml coercion quirks.
