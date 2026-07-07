# Session 5 — the edge accessor and the store knob: the corpus learns to read settings

Date: 2026-07-06 (same sitting as sessions 0–4)

## Verdict

Session 4's NEXT executed in full: the capture grew a `get_setting` probe kind
(the named trace-suppression interaction was unobservable through existing
probes), three cases took the corpus 19 → 22 across the edge-rule accessor and
the store-off pair — oracle-vs-oracle ALL PASS twice (post-authoring and
post-review-fix; repeats green both times), the review gate confirmed
1 Medium + 3 Low (all fixed in-session), and the board stands at 21/52 rows
`cased` with `fn:filter_and_sort_edges` and
`setting:store_interpretation_changes` flipped.

## Evidence

- **The get_setting probe** (`harness/capture.py`): reads one named knob off
  the engine's public module-global settings object — the surface reason()
  itself mutates — so a knob's live value is a compared observation. It refuses
  `allow_raise` (an engine missing a knob is a missing-surface structural
  fault, never a comparable observation), and knob names validate statically
  against `SETTINGS_KNOBS`, the pinned 18-knob surface, in both case forms —
  guard shape shared with `REASON_ARGS`, and AST-gated
  (`tests/test_surface_inventory.py`) so a pin move cannot silently stale it.
- **edge-rule-frames** pins `filter_and_sort_edges`' two frame-reconstruction
  branches in one probe: an edge-head rule
  (`trusted(x,y) <-1 popular(x), Friends(x,y)`) leaves the t=0 frame empty
  (fabricated `[component, *labels]` columns, zero rows) while t≥1 frames carry
  component tuples rebuilt from the two-level index — the branches normalize to
  the same column list, and that normalization is the pinned contract.
- **store-off-accessors** pins the store-off-assert family: with
  `store_interpretation_changes=False`, reason() runs and `get_time` answers,
  but the trace-backed accessors raise `AssertionError` — four `allow_raise`
  probes over three assert sites (`get_rule_trace`'s single assert precedes its
  node/edge split and reuses the "save rule trace" message).
- **store-off-atom-trace-flip** pins reason()'s trace-suppression interaction:
  `atom_trace` reads true before the reason step and false after it while store
  stays off (pyreason.py:1584 at the pin) — the pre-reason readings ride the
  add_fact step, so the flip is attributed to reason(), not settings
  application.
- **The runs:** `uv run python -m harness.run --cases harness/cases --engine-a
  oracle-env/bin/python` → ALL PASS, 22 cases × 4 fresh-process captures,
  `PYTHONHASHSEED=0`, twice; the re-run is the verdict-of-record, banked as
  [session-5-oracle-vs-oracle.json](session-5-oracle-vs-oracle.json).
- **Review gate:** [docs/reviews/2026-07-06-get-setting.md](../reviews/2026-07-06-get-setting.md)
  (one focused Opus reviewer — the scaled-down form again; raw committed
  beside). The Medium: the original knob guard required a `property` descriptor
  on the engine's settings class, hard-coding the oracle's storage mechanism —
  a rewrite storing the same public knob as a plain attribute would have worn
  the `error` label over a real value-divergence. Fixed by the static
  `SETTINGS_KNOBS` validation; the capture now touches knobs with plain
  getattr/setattr. The reviewer verified every pinned observation against the
  banked artifacts and found no false-pass.
- **Gates:** fast tier 61 passed; links gate green on every commit; preflight
  10/10 at session start.
- **Board:** `docs/surface.md` — 21 rows `cased` (fn:filter_and_sort_edges,
  setting:store_interpretation_changes flipped), 31 `uncovered`; `equivalent`
  still 0/52 — no rewrite exists, `cased` marks harness coverage only.

## Committed

- `b7e7374` — harness: get_setting probe reads a live settings knob.
- `3787f3b` — harness: edge-rule + store-off case trio.
- `038a8d9` — docs: board flips + the first banked run.
- `486c881` — harness: review findings fixed; report; the re-banked
  verdict-of-record.
- (this commit) — ledger: session 5 banked.

## NEXT

Case the settings-only reasoning knobs the capture can already express, no
capture surgery expected: an `fp-version-on` case (hello-world inputs with
`settings.fp_version=true` — reason() runs through `interpretation_fp`,
pinning `setting:fp_version`'s nondefault-true-fp class; screen first on this
ARM machine before authoring is final), an `update-mode-override` /
`update-mode-junk-string` pair (`setting:update_mode` nondefault-override plus
the unvalidated-string class — any non-'override' string silently behaves as
intersection, so the junk-string case should compare equal to a default-mode
twin's probes), and an `allow-ground-rules` on/off pair (a ground rule in the
rule DSL with `setting:allow_ground_rules` toggled). Run oracle-vs-oracle,
flip `setting:fp_version`, `setting:update_mode`, and
`setting:allow_ground_rules`, bank the run.

## Deviations

- The review gate again used the umbrella's scaled-down single-focused-reviewer
  form for a contained spine extension (the charter's ≥2-reviewer form names
  complete features); report committed anyway.
- The capture gained the `get_setting` probe kind, which session 4's NEXT did
  not name — the named trace-suppression interaction mutates only the public
  settings object, which no existing probe could read, so the class was
  unpinnable without it.

## Asks queued

None.

## Divergences

None opened — no rewrite exists; the store-off assert family and the
atom_trace force-flip are pinned oracle behaviors recorded on the board,
oracle-bug-candidates / intentional-divergence candidates per AC-3's
both-not-either rule when equivalence runs begin.

## Idea seeds

- reason() mutating the public `atom_trace` knob as a side effect is now a
  pinned contract the rewrite's explicit-state design will want to adjudicate:
  a clean core would suppress tracing internally without writing to the
  user-visible settings surface, and `store-off-atom-trace-flip` will surface
  exactly that divergence the day the rewrite behaves better — a prepared
  intentional-divergence candidate.
- `SETTINGS_KNOBS` is now AST-gated against the pinned source; `REASON_ARGS`
  remains hand-kept — session 4's seed (derive it from the pinned signature the
  way the inventory scan does) still stands, now with a worked example beside
  it.
- The probe-raise exit-taxonomy channel (session 4's deferred M2) is still the
  gating piece before oracle-vs-rewrite runs; the get_setting probe's
  missing-knob AttributeError joins the list of raises that would wear the
  harness-failure label on a candidate engine.
