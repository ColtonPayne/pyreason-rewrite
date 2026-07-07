<!-- doccode: pyreason-rewrite-docs-reviews-2026-07-06-get-setting -->
# Review report — get_setting probe and the edge-rule / store-off case trio

Scope: the get_setting capture extension (`b7e7374`), the edge-rule + store-off
case trio (`3787f3b`), and the board/run commit (`038a8d9`). One focused Opus
reviewer with no shared session context — the umbrella's scaled-down form for a
contained spine extension (same deviation as the session-3/4 gates; recorded in
the ledger). Raw reviewer output:
[2026-07-06-get-setting-raw.md](2026-07-06-get-setting-raw.md).

The reviewer found no false-pass: every probe's banked observation was verified
against the actual run artifacts and the pinned source, and each would
genuinely diverge under a differently-behaving engine. The atom-trace-flip pin
was confirmed correctly isolated (the pre-reason readings ride the add_fact
step, so the flip is attributed to reason(), not settings application), and the
edge-rule case confirmed to execute both frame-reconstruction branches.
Findings and their resolutions:

## Fixed

- **M1 (Medium)** — `settings_knob_guard` required each knob to be a `property`
  descriptor on `type(pr.settings)`, hard-coding the oracle's storage mechanism
  into the harness: a rewrite exposing the identical public knob as a plain
  attribute would make every `get_setting` probe (and `apply_settings`) fail
  the capture, hiding a real value-divergence behind the `error` label. The
  guard is gone; knob names are now validated statically against
  `SETTINGS_KNOBS` — the pinned 18-knob surface, the same shape as
  `REASON_ARGS` — in `validate_case`, covering both `inputs.settings` keys and
  `get_setting` probes in both case forms. A typo is now exit 2 (authoring
  fault) instead of exit 1, and the capture reads/writes knobs with plain
  getattr/setattr, indifferent to engine internals. A new fast-tier gate
  asserts `SETTINGS_KNOBS` against the AST scan of the pinned `_Settings`
  class, so a pin move cannot silently stale the list.
- **L2 (Low)** — the `fn:filter_and_sort_edges` board note said empty and
  non-empty frames "have divergent column shapes"; the observed columns are
  identical — the source's two reconstruction branches *normalize* to the same
  `[component, *labels]` list, and that normalization is what the case pins.
  Reworded to say so.
- **L3 (Low)** — "all four accessors pinned" overstated the store-off case:
  `get_rule_trace`'s single assert precedes its node/edge split, so the two
  trace probes bank byte-identical records — four probes over three assert
  sites. The case purpose and board note now say exactly that; both probes are
  kept (harmless redundancy, and the node/edge pair stays load-bearing for a
  rewrite whose accessor split behaves differently).
- **L4 (Low)** — the `get_setting` validation tests exercised only a missing
  `knob` key and only the top-level form. Now: missing, empty, non-string, and
  off-surface knob names are each asserted rejected, in the steps form too,
  and the `run_probe` test proves the probe reads a plain-attribute settings
  object (the M1 property requirement is pinned absent).

All fixes regression-tested (fast tier 61 passed); the corpus re-ran green
after the fixes and the re-banked run is the session's verdict-of-record.

## Deferred with rationale

None — every finding was fixed in-session.
