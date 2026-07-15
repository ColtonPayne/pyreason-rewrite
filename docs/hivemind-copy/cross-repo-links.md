<!-- doccode: pyreason-rewrite-hivemind-copy-cross-repo-links -->
> **Snapshot, not source of truth (operator-requested, 2026-07-15).** Verbatim copy of
> `$HIVEMIND_ROOT/docs/cross-repo-links.md`, committed so the GitHub mirror of this repo is readable
> without the hivemind checkout. The canonical file governs and edits land there; refresh
> this copy manually. Its cross-repo links resolve only beside a local hivemind checkout.

# Cross-repo links — the authoring convention and the move-as-registry-operation

How docs across the hivemind address one another, and how a move propagates. The mechanism is
the `links` table-set in hive-state; the decisions are [umbrella ADR 0002][ai-hivemind-docs-adr-0002-cross-repo-link-registry]
(the registry), [ADR 0003][ai-hivemind-docs-adr-0003-livedoc-marker-taxonomy] (the marker
taxonomy), and [ADR 0004][ai-hivemind-docs-adr-0004-repo-outer-key-and-manifest] (repo is the
outer key + the manifest). The committed graph over the whole corpus is
[hive-state's links registry][hive-state-docs-build-log-03-cross-repo-link-registry].

## Why

A relative path is the most drift-prone construct in the corpus: one `git mv` breaks every
inbound link at once, and the links are scattered across seven repos. So a doc is addressed by a
**stable doc-code** that travels with the file, not by its current location. A move re-points one
mapping; every inbound link follows mechanically on the next ingest.

## The authoring convention

1. **Every managed doc carries a doc-code marker** — `<!-- doccode: <code> -->` near the top
   (immediately after the top livedoc region if one is present, else at byte 0). The code is the
   doc's rename-surviving identity, conventionally `<repo>-<repo-relative-path>` with `.md`
   stripped and slashes turned to dashes (e.g. `ai-hivemind-docs-cross-repo-links`). It is
   authored once and never changes when the file moves.

2. **Anchorless doc→doc links are reference-style** — write `[text][doc-code]`, never a raw
   relative path. The clickable `[doc-code]: <relative-path>` definition lives in the doc's
   machine-managed block at EOF, delimited by `<!-- links:begin -->` / `<!-- links:end -->`. You
   author only the `[text][doc-code]` usage in prose; `hstate links render` writes the block.

3. **These stay inline as raw paths** — a **doc→code** link (a doc pointing at a source file, or
   at an excluded `.md` like a skill or a generated render — a path-keyed leaf, never a coded
   node) and an **anchored doc→doc** link (`[text](path.md#L55)`), because a single reference
   definition can't carry a per-use fragment.

4. **Never hand-edit the `links:` block.** `hstate links render` is its only writer, exactly like
   the livedoc regions `hstate ideas render` owns — a hand-edit reds the gate.

External links (`http(s)://`, `mailto:`) and gitignored targets (the out-of-band papers corpus)
are left alone — neither becomes a coded edge.

## New docs — `git add` before you render

The tooling enumerates git-tracked files, so a never-staged new doc is invisible: `render` won't
stamp its `links:` block and `check` passes green by simply not seeing it. `git add` the new doc
first, then render.

Then **`git add` again before you commit.** `render` writes the block into the working tree, and the
pre-commit `check` validates the *working tree*, not the index — so a commit staged *before* render
captures a stale/empty block yet still passes green. Order: `git add` → render → `git add` → commit.

## The gate

Every repo's `scripts/hooks/pre-commit` runs, whenever **any** `.md` is staged, the corpus gate:

```
uv run --directory <abs hive-state> hstate links check --manifest <abs umbrella>/repos.toml
```

`links check` ingests every manifest repo's git-tracked files (`git ls-files`, not the raw
filesystem) into an in-memory DB and verifies, over
the union: every doc's `links:` block is current (`ingest → render == tree`), every `[text][code]`
usage resolves to a known doc-code, every leaf/anchored target is a tracked file in its owning
repo, and codes are unique. It writes nothing and takes no `--db`. The guard runs **parallel to**
each hook's docs/code classifier — never nested in a branch — so a commit that mixes a doc move
with code can't skip it. It **soft-skips** only when `uv`, the hive-state sibling, or the umbrella
manifest is unreachable (a lone or partial clone still commits).

When this gate reds, the repair is the `/hive-state-links` skill — it runs the `ingest → render →
check` choreography below against the manifest and surfaces each finding (stale block, unresolved
link, unknown/duplicate code) with its fix. A red gate committed nothing; repair, then re-commit.

## The move-as-registry-operation

A referencing doc's definition depends on **another** doc's location, so a move fans out across
repos and resolution is **atomic** — render every affected repo and commit them together:

1. **`git mv`** the doc. Its doc-code travels in the marker; its new location is observed, not
   authored, so there is no path to hand-edit.
2. **Re-ingest the union** — rebuild the store from the new locations:
   `hstate links ingest --manifest <umbrella>/repos.toml` (run via
   `uv run --directory <hive-state>`).
3. **Re-render each affected repo** — recompute the `[code]: path` definitions against the moved
   target: `hstate links render --manifest <umbrella>/repos.toml --repo <r>` for every repo whose
   docs reference the moved file. (Render reads the shared store, so step 2 must precede it for a
   cross-repo code to resolve.)
4. **Commit every affected repo together.** `links check` reds any repo committed with a now-stale
   inbound definition, so a half-finished move blocks commits corpus-wide until repaired —
   propagation is mandatory, not best-effort. One agent does this today; the
   [multi-repo-commit-sweep][idea-synthesis-writeups-multi-repo-commit-sweep] sibling is the
   benchmarked fan-out that will perform the N-repo commit later, and this registry is its first
   customer.

<!-- links:begin -->
[ai-hivemind-docs-adr-0002-cross-repo-link-registry]: ../../../ai-hivemind/docs/adr/0002-cross-repo-link-registry.md
[ai-hivemind-docs-adr-0003-livedoc-marker-taxonomy]: ../../../ai-hivemind/docs/adr/0003-livedoc-marker-taxonomy.md
[ai-hivemind-docs-adr-0004-repo-outer-key-and-manifest]: ../../../ai-hivemind/docs/adr/0004-repo-outer-key-and-manifest.md
[hive-state-docs-build-log-03-cross-repo-link-registry]: ../../../ai-hivemind/hive-state/docs/build-log/03-cross-repo-link-registry.md
[idea-synthesis-writeups-multi-repo-commit-sweep]: ../../../ai-hivemind/idea-synthesis/writeups/multi-repo-commit-sweep.md
<!-- links:end -->
