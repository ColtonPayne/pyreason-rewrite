<!-- doccode: pyreason-rewrite-docs-reviews-2026-07-12-case-seed-batch-review -->
# Session 30 — case-seed batch, independent review

- session: 30 · 2026-07-12 · reviewer-fixer (no shared context with the author)
- scope reviewed: commits `92eed57` (two rewrite parser changes + 8 seam tests),
  `4b87f2e` (10 cases + 13 fixtures), `7cc5678` (board widening), `99b1351`
  (author report), with the interruption-recovery claims held to independent
  verification throughout
- verdict: **approved with fixes** — the packet's claims all reproduce, but
  fresh pin screens past the author's sampled points found **three class
  mismatches in the two engine-change models**, fixed in commit `1dd1bf9`;
  after the fixes: fast tier **310 passed / 5 deselected**, the 10-case batch
  **ALL PASS 10/10** oracle-vs-rewrite on a fresh run

## 1. The two engine changes, re-derived at the pin (findings + fixes)

Both models were re-derived from the pinned source (delta digit-consumption at
oracle `rule_parser.py:51-64`, the `numba.types.uint16` cast at `:243`; the
weights `np.array(..., dtype=float64)` conversion + checks at `:203-230`;
`rule_internal.Rule` is a plain class, so no construction-time typing narrows
either seam) and re-screened live at the pin — 2 fresh oracle-env processes
per arm, all stable, including values the author did not sample. The author's
banked points all reproduce exactly (65535 verbatim; 65536→0; 70000→4464;
`[[1,2]]` ACCEPTED with len = row count; `[None]` takes the finiteness raise;
ragged and mixed-depth take the conversion TypeError; `[]`, `[[]]`, numeric
strings including `'1_000'`, booleans, `'1e3'`, and bytes leaves all match).
Three classes beyond the sampled points did not:

| # | class | pin (screened 2026-07-12) | rewrite before fix |
|---|---|---|---|
| F1 | delta past the C-long max | `<-9223372036854775808` (2^63) and 2^64-1 **raise** `OverflowError: Python int too large to convert to C long`; 2^63-1 still wraps to 65535 | `% 65536` wrapped everything (2^64 → 0) |
| F2 | tuple weights | `weights=(1,2)` and `[(1,2)]` **accepted** — np.array treats tuples as array dimensions | list-only model raised the conversion TypeError |
| F3 | scalar weights | `weights=5` / `'12'` raise `TypeError: len() of unsized object` (np.array(5) is a 0-d ndarray; the length check's len() raises, un-wrapped) | `TypeError: object of type 'float' has no len()` — wrong message text |

Fixes (commit `1dd1bf9`, all screened back to class-for-class match):

- **F1** — `_delta_uint16` applies the pinned cast **at RuleIR construction
  time**, after every other validation, because the pin's cast sits at the
  end of parse_rule: screened that a huge delta plus a bad clause raises the
  clause ValueError and plus bad weights raises the weights TypeError, at
  both engines, before any overflow.
- **F2** — `_weights_to_floats` recurses over list and tuple alike,
  normalizing to lists; rectangularity and the ragged/mixed-depth raise arms
  unchanged.
- **F3** — a non-list conversion result raises the pinned
  `len() of unsized object` outside the conversion re-wrap (so it is never
  converted into the `weights must be a numpy array...` TypeError).

5 new seam tests pin the three classes (`test_rule_delta_wraps_up_to_c_long_max`
x2, `test_rule_delta_past_c_long_max_takes_pinned_overflow`,
`test_rule_weights_tuples_accepted_like_lists`,
`test_rule_weights_scalar_takes_pinned_unsized_len_raise`), each with a
`proves:` docstring citing the screen.

Out-of-scope by construction, recorded here as the model's boundary: ndarray
weights input (the pin skips conversion for it) cannot arise on the compared
surface — the rewrite engine carries no numpy, so no case program shared by
both engines can construct one; exotic sequence types beyond list/tuple
(e.g. `range`) remain unmodeled and are noted in `_weights_to_floats`'s
docstring. Session 29's tuple-only-coercion precedent repeated here almost
verbatim (F2): sequence-type acceptance is now a standing screen item for any
model of a pinned np/numba coercion.

## 2. Triage table — complete and honest

Every arm the packet named is in the table: the four warn-skip loaders (rows
2–5, with `add_rules_from_file` correctly noted as banked since session 16,
row 1), both ragged-CSV directions (6–7), **interval-nonnumeric** (row 8 —
present, carried inside the two fact warn-skip fixtures: CSV
`"beta(A):[abc,1]"` and JSON `delta(A):[nope,1]`, both verified in the
committed fixtures), the weights family (9–12), the delta family including 0
end-to-end (13–15), `interacts-unknown-predicate` (16), and O1/O2 (17–18).
The 18→10 tally is honest: rows 6+7 share one case, row 8 rides two others,
rows 10–12 share the weights case, 13–14 share the delta-variants case. The
all-nodes-fallback provenance for row 16 checks against the pinned
`get_rule_node_clause_grounding` (interpretation.py:1396-1402, the
`else: grounding = nodes` branch).

## 3. The 10 cases

- **Corpus seam contract**: all 10 parse, every `harness/fixtures/` reference
  resolves to a tracked file (the only unresolved paths in the corpus are the
  pre-existing intentional missing-path arms), fixtures carry exactly the
  arms the purposes claim.
- **graphml-static-pin**: the banked observations genuinely show every
  claimed discriminator — t=0 rows empty for inv/pw/nz/einv with only `ow`
  `[1,1]` present (O2's space-tolerant bare-key arm); the node filter frozen
  at the inverted `[1,0]` on X1 with the later `[1,1]`/`[0.5,1]`/`[0.7,1]`
  facts never landing; the edge side resolving `[1,0]→[0,1]` with
  graph-attribute-fact resolve rows in the edge trace vs no-change rows in
  the node trace — the node/edge asymmetry is in the compared surface, not
  just the prose.
- **Warn-skip cases**: the compared-surface statement is accurate — verified
  in `harness/run.py:46` that loader warnings ride stdout+stderr into the
  diagnostic `.log` beside the artifact and are never part of the compared
  capture; the cases bank post-load state (rules fingerprints or reasoning
  frames), which is the skip semantics itself, and their purposes say so.
- **rule-json-weights-dtypes**: the purpose's honesty note is correct —
  `parse_fingerprint`/rules fingerprints carry no weights contents, so the
  nested acceptance is banked as load-plus-fingerprint presence; the
  conversion values themselves are pinned by the fast-tier seam tests.
- **rule-delta-variants**: `expect_raise` acceptance branches bank the parse
  fingerprint including `delta` (capture.py:656-662), so the wrap values are
  genuinely compared, not just non-raising.
- `proves:` docstrings present on all 8 author seam tests (and my 5).

## 4. Equivalence rerun (post-fix)

- Fast tier: **310 passed, 5 deselected** (author's 305 + 5 review seam
  tests); inventory gate green (tests/test_surface_inventory.py in-tier).
- The 10-case batch, fresh results dir: **ALL PASS (10 case(s))**, exit 0,
  same-engine repeat stability enforced by the runner (a1/a2 + b1/b2 per
  case). Repro:

```
uv run pytest -m "not e2e"

mkdir -p /tmp/seed-batch-cases && for c in rule-from-csv-warn-skip \
  rule-from-json-warn-skip fact-from-csv-warn-skip fact-from-json-warn-skip \
  fact-csv-ragged rule-json-weights-dtypes rule-delta-variants \
  delta-zero-rule closed-world-unknown-predicate graphml-static-pin; do \
  cp harness/cases/$c.json /tmp/seed-batch-cases/; done
PYTHONHASHSEED=0 uv run python -m harness.run --cases /tmp/seed-batch-cases \
  --engine-a oracle-env/bin/python --engine-b scripts/rewrite-python \
  --results results-session30-review
```

(`results-session30-review` is covered by the gitignore the author added.)

## 5. Recovery-note audit

The interruption-recovery claims check out against the tree: the four commits
are coherent and complete — `4b87f2e` carries all 10 cases + 13 fixtures +
the gitignore line in one commit (no half-written fixture; every case's
fixture references resolve inside the commit), the parser change and its
seam tests travel together in `92eed57`, and the board/report commits touch
only docs. Post-commit tree state verified: oracle byte-clean at
`e1a94af33e1f` (= oracle/PIN), `pyproject.toml`/`uv.lock` untouched since
`9181767`, no stray uncommitted work. The author's decision to re-run the
harness against committed content after resuming was the right discipline;
nothing in the banked evidence rests on pre-interruption output.

## 6. What the fixes mean for the author's claims

No case content changed; the three corrected classes sit outside the 10
cases' probe sets, so the author's 10/10 PASS was real before the fixes and
remains real after them (re-run fresh, above). The corrections are to the
**models** in the rewrite parser — the same defect family session 29's
review caught — not to any banked observation. Zero divergences filed stands;
"0 un-bankable" stands; the triage table stands as written.
