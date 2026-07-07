<!-- doccode: pyreason-rewrite-docs-adr-0001 -->
# ADR 0001 — Rewrite package layout: src/ tree, wrapper interpreter, facade over explicit state

- status: accepted
- date: 2026-07-07
- session: 16 (Phase 3, opening slice)

ADR format note: this directory uses MADR-lite (Context / Decision /
Consequences), numbered `NNNN-slug.md`; this file sets the convention.

## Context

The rewrite must be importable **as `pyreason`** by the engine-B interpreter,
because the capture protocol is `<engine-python> -m harness.capture …` run
from the repo root with `import pyreason as pr` inside. That same protocol
puts the repo root first on `sys.path` in **both** engines' subprocesses — so
a top-level `pyreason/` directory in this repo would shadow the oracle
environment's installed pyreason in the engine-A capture and silently turn
every differential run into a rewrite-vs-rewrite self-comparison. The
equivalence evidence would look green and mean nothing.

Two further forces: the campaign permits no dependency or packaging changes
without an operator ask (so no `[build-system]`/editable install to put the
package on a venv's site-packages), and the charter requires a module-global
API facade (the pinned surface shape) over a core with **no hidden state**.

## Decision

1. **The package lives at `src/pyreason/`.** The repo root's `sys.path`
   entry cannot see it, so the oracle's import in engine A is unshadowable
   by construction. Verified empirically both directions at adoption
   (engine-A capture artifact reports the oracle-env executable and
   pyreason 3.6.0; `scripts/rewrite-python -c "import pyreason"` resolves to
   `src/pyreason/__init__.py`).
2. **Engine B reaches it through `scripts/rewrite-python`**: a committed
   wrapper that execs `.venv/bin/python` with `<repo>/src` prepended to
   `PYTHONPATH`. That wrapper path is what `--engine-b` receives; no
   environment gains a permanent install.
3. **The fast tier reaches it through pytest `pythonpath = [..., "src"]`**
   (a test-runner path entry, not an install).
4. **Inside the package**: `__init__.py` is the module-global facade holding
   exactly one `EngineState` (`_state.py`) and delegating; parsers, loaders,
   and add-functions are pure functions over that explicit state; the public
   value types (`interval`, `label`, `threshold`, `rule`, `fact`, `query`)
   are their own modules, with `pyreason.interval` / `pyreason.label`
   mirroring the pinned aliased-submodule access paths the harness probes.
5. **Deliberate scope exception, per the packet**: `_settings.Settings`
   carries all 18 pinned knobs (not just the ones today's cases read),
   because the capture applies arbitrary `inputs.settings` dicts through
   `setattr` and the knob surface is one leaf value object — implementing a
   subset would make valid future cases fail on a missing-attribute
   structural fault instead of a compared observation. One descriptor class
   (`_Knob`) carries the pinned validate-and-store shape for all knobs.

## Consequences

- The layout hazard is closed structurally, not procedurally: no future
  packet can shadow the oracle by adding files, only by moving the package —
  which this ADR marks as a decision, not a refactor.
- If real packaging (a `[build-system]` table, editable install into a
  dedicated rewrite venv) ever becomes the better long-term layout, that is
  an operator ask; the wrapper keeps working either way, so there is no
  pressure to decide early. For now the src/ tree with no build backend is
  sufficient: nothing consumes the package except the harness (via the
  wrapper) and the fast tier (via pytest pythonpath).
- Every reasoning-capable future slice inherits the explicit-state seam:
  new engine capability lands as pure functions over `EngineState`, and the
  facade only ever grows one-line delegations.
