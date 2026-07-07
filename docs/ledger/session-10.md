# Session 10 — parallel_computing and the output redirect: the last settings knobs

Date: 2026-07-07 (continuing the 2026-07-06 sitting)

## Verdict

Session 9's NEXT executed in full: the capture grew a file-output probe kind
(the `output_to_file` redirect file becomes a compared observation, confined
to a fresh per-capture directory), seven cases took the corpus 46 → 53,
targeted oracle-vs-oracle ALL PASS on all seven with same-engine repeats
(the post-review rerun is the verdict-of-record), the review gate found
0 High / 0 Medium / 3 Low (one board fix, two evidence-precision notes
settled with recorded corroboration), and the board stands at 35/52 rows
`cased` with `setting:parallel_computing`, `setting:output_to_file`, and
`setting:output_file_name` flipped. **The settings-knob phase is complete;
the phase-boundary full-corpus sweep is now due.** Headline
characterization: the parallel kernel is laptop-local, digest-equals the
serial kernel on the pair's program, and its compile *caches across fresh
processes* (~174s cold → ~2.8s warm) — refuting the no-cache belief written
at three pinned sites.

## Evidence

- **Capture extension** (`5b0d8af`): probe kind `output_file` — flush
  stdout, glob `*.txt` in a fresh per-capture confined directory
  (`<artifact>.outdir` under `results/`, cleared each capture), return
  `{name, content}` sorted, basename timestamp canonicalized
  (`_\d{8}-\d{6}\.txt$` → `_<timestamp>.txt`; recorded rationale: the stamp
  at `pyreason.py:1511` is run schedule, not engine behavior). The blanket
  `output_to_file` forbid replaced by a targeted rule: knob-true requires
  ≥1 `output_file` probe; `allow_raise` refused on the kind. The chdir
  happens only for output-surface cases, after absolute artifact-path
  resolution — the cwd-relative redirect (`pyreason.py:1513-1514`, re-opened
  same name at `:1541-1542`, never flushed/closed/restored) cannot land
  outside the per-run results area. Fast tier 65 → 70 seam tests.
- **The output cases** (`e806b60`): default twin (readbacks, confined dir
  empty) / on-twin (one file `pyreason_output_<timestamp>.txt`, contents
  exactly the 8-line verbose reason-time text) / custom-name
  (`campaign_redirect_…`, byte-identical contents) / inert
  (`output_file_name` set, knob off, no file — the pin's two consumption
  sites are both guarded by the knob). All four cases' reasoning digests
  identical cross-case: the redirect moves prints, never reasoning.
- **The parallel cases** (`fa77593`): the dispatch (`program.py:42-46`)
  checks `_parallel_computing` before `_fp_version`; the parallel kernel
  differs from the serial by exactly one line (the `parallel=True`
  decorator flip at `interpretation_parallel.py:241`). Twin pair over
  hello-world (one rule → prange width 1, so trace appends cannot reorder;
  scoped claim only): on-twin digest-equals the default twin on every
  reasoning probe. `parallel-fp-precedence` (both knobs true) ≡ the
  parallel shape and ≠ `fp-version-on` on `trace-node`/`nodes-popular` —
  precedence pinned behaviorally, not by readback alone; the trio jointly
  discriminates the knob.
- **The caching characterization**: first fresh-process parallel reason
  ~174.4s (compile-dominated smoke, screen-then-confirm), every fresh
  process after ~2.7-2.9s; the kernel's single 10.3 MB `.nbc` cache file
  was written once at the cold smoke and never rewritten across nine-plus
  fresh processes (author captures + review rerun). The pinned no-cache
  belief appears at `pyreason.py:204-205`, `:410-411`, and `program.py:41`
  — all three named on the board (review F2). Compile emits a
  uint64→int64 `NumbaTypeSafetyWarning` at `interpretation_parallel.py:572`
  (stderr, not compared) — noted for the rewrite's kernel work.
- **The runs:** fast tier 70 passed; each of the seven cases via
  `uv run python -m harness.run --cases harness/cases/<case>.json --engine-a
  oracle-env/bin/python` → ALL PASS, 4 fresh-process captures each
  (PYTHONHASHSEED=0), repeats green — author run and post-review rerun
  (verdict-of-record). **No full-corpus run** — the sweep, now 53 cases, is
  the next session (the phase boundary is here).
- **Review gate:**
  [docs/reviews/2026-07-07-parallel-and-file-output-cases.md](../reviews/2026-07-07-parallel-and-file-output-cases.md)
  — F1 (Low): the caching claim's banked-timing citation was imprecise
  (warm timings alone don't discriminate; the cache-file mtime evidence
  settles it, recorded). F2 (Low, fixed): the no-cache refutation cited one
  pinned site of three; board note widened. F3 (Low, accepted): the
  precedence case's ≠-fp half rides prior-session `fp-version-on` artifacts
  — pin unmoved, same env fingerprint, digests re-derived at review time.
  Author report:
  [2026-07-07-parallel-and-file-output-cases-raw.md](../reviews/2026-07-07-parallel-and-file-output-cases-raw.md).
- **Gates:** preflight 10/10 at session start; links gate and fast tier
  green on every commit; oracle tree clean at `e1a94af33e1f` throughout.
- **Board:** `docs/surface.md` — 35/52 rows `cased`, 17 `uncovered`;
  `equivalent` still 0/52. Uncovered classes named per row: `type-reject`
  family-wide (needs the raising-probe form), multi-rule prange scheduling
  (deliberately unexercised — if nondeterministic it becomes its own
  characterization case, never absorbed), `memory_profile`/
  `interaction-output` now authorable via the new probe but blocked on a
  recorded text-canonicalization policy for the run-varying peak-MB line.

## Committed

- `5b0d8af` — harness: output_file probe — file-redirect output becomes a
  compared observation.
- `e806b60` — harness: the output_to_file/output_file_name cases — redirect
  pinned as a compared file.
- `fa77593` — harness: parallel_computing twin pair + fp-precedence case.
- `c752584` — docs: board flips for parallel_computing and the
  output_to_file/output_file_name pair.
- `7adb5c2` — harness: author report for the packet (raw, pre-review).
- `dbd9a01` — harness: review — board note widened to all three pinned
  no-cache sites; report.
- (this commit) — ledger: session 10 banked; campaign log continued.

## NEXT

**The owed phase-boundary full-corpus sweep — the settings-knob phase's
verdict-of-record.** Run all 53 committed cases oracle-vs-oracle
(`uv run python -m harness.run` over every `harness/cases/*.json`,
`--engine-a oracle-env/bin/python`, PYTHONHASHSEED=0), fast tier first.
Expect the parallel-branch cases warm (~3s) unless the numba cache was
cleared — a cold first capture (~174s) is schedule, not a finding. Triage
every non-pass by the exit taxonomy: pass / cross-engine divergence
(impossible oracle-vs-oracle — any would be a harness defect) /
same-engine irreproducibility (a harness-or-environment failure to
root-cause, never absorbed). Spot-fix what surfaces, rerun the affected
cases, and bank the sweep verdict — corpus size, pass count, wall-clock,
per-case timing outliers — as the phase's verdict-of-record. Bank via
review only if fixes touched code; a clean sweep banks directly with the
run log as evidence. After the sweep, the queued operator asks (below)
are the natural boundary triage before the next phase opens.

## Deviations

None — the session followed the two-agent shape and the packet spec as
written.

## Asks queued

None blocking. Non-blocking, for operator triage at this boundary (carried
+ new):
- Whether a raising-probe form (apply-inputs-expecting-raise) is worth a
  packet: it unlocks `type-reject` family-wide, `load_graphml`
  missing-file/bad-content, and the `"0.5.5"` float-guard raise — one probe
  shape, four uncovered class families.
- Whether `memory_profile`'s `interaction-output` class should proceed via
  a recorded text-canonicalization policy (canonicalize the run-varying
  peak-MB line in the redirect file, rationale recorded per AC-2's
  per-case normalization contract) — the probe infrastructure is ready.

## Divergences

None opened — no rewrite exists; all seven cases oracle-vs-oracle.

## Idea seeds

- The rewrite's kernel work inherits two pinned facts worth carrying: the
  no-cache belief is wrong at all three sites (parallel + cache coexist),
  and the parallel kernel emits an unsafe uint64→int64 cast warning at
  `interpretation_parallel.py:572`.
- Multi-rule prange scheduling as a deliberate characterization case
  (width >1): would pin whether trace order under real threading is
  deterministic — the harness's `irreproducible` verdict is the honest
  landing spot if not.
- Carried: multi-path `--cases` for one-command targeted reruns (the sweep
  session will feel this friction directly); get-family accessor
  fingerprint probes; `REASON_ARGS` derived from the pinned signature;
  artifact-schema echo of `inputs`.
