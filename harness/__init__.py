"""Oracle-differential harness — the campaign's proof spine (AC-2).

Three seams: `capture` runs one case inside one engine's environment (a bare
subprocess) and emits a self-describing result artifact; `compare` is the
stdlib-only canonicalization/digest/comparison layer, importing nothing from
either engine; `run` orchestrates repeat-paired runs and judges each case as
pass / divergent / irreproducible / error.
"""
