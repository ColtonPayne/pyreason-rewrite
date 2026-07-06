# Session 0 — fresh-machine preflight (campaign machine, macOS/Apple Silicon)

Date: 2026-07-06

## Verdict

Preflight 10/10 green on the campaign machine; the federated substrate (manifest, hstate,
links gate, lrag `pyreason-analysis`, oracle pin, ledger, git wiring) is verified live and
non-disrupted — campaign work is cleared to start.

## Evidence

- **Passing preflight report:** [session-0-preflight.json](session-0-preflight.json)
  (`uv run python tools/hive_preflight.py --json`, exit 0, all ten checks PASS; run from a
  fresh shell with no inline env, proving `~/.zshenv` carries `LRAG_STORE` to
  non-interactive agent shells).
- **Initial state:** 4/10 under system python (3.9.6) — uv absent on this machine, and
  every other red cascaded from it. `oracle-pin` (clean at `e1a94af33e1f`),
  `umbrella-manifest`, `ledger-writable`, `git-wiring` passed from the first run.
- **lrag bootstrap:** `lrag --allow-empty collection new pyreason-analysis --path
  ~/Projects/dyuman-pryeason` then `lrag sync -c pyreason-analysis` → **29 added, 0
  removed** — matching the charter's committed 29-doc count. The `--allow-empty` guard was
  overridden knowingly: the store is genuinely new on this machine.
- **AC-0 non-disruption:** `git status --porcelain` after bootstrap — clean in
  `local-rag`, `hive-state`, `idea-synthesis`, `oracle/pyreason`, and
  `~/Projects/dyuman-pryeason`. The umbrella tree shows two untracked files predating this
  session (`.DS_Store`; `docs/fable-window-plan-banking/2026-07-04-mistake-registry-run-4-output.md`)
  — not campaign-caused. The campaign repo's only change is this session's ledger artifacts.
  `links-gate` green in the banked report (corpus link graph intact).
- **Writes outside the campaign repo this session** (each operator-approved in-session,
  2026-07-06): `brew install uv` (uv 0.11.26); `~/.lrag/store` created +
  `export LRAG_STORE="$HOME/.lrag/store"` appended to `~/.zshenv` (the local-rag README's
  documented setup); the machine-local lrag registry bootstrap (the documented session-0
  write). Nothing else outside the repo was touched.

## Committed

- (this commit) — session 0 banked: passing preflight JSON + this entry.

## NEXT

Build the operator-approved oracle environment (approved 2026-07-06): a dedicated,
git-ignored uv env inside the campaign repo with the pinned oracle installed
**non-editable** plus its declared runtime set (`networkx`, `pyyaml`, `pandas`,
`numba==0.59.1`, `numpy==1.26.4`, `memory_profiler`, `pytest`; no torch) — then run the
ARM gate: hello-world `reason()` in that env on this machine, result banked in session 1.

## Asks queued

None outstanding — three were raised and resolved in-session (2026-07-06):
1. **Install uv** → approved, `brew install uv` executed (uv 0.11.26).
2. **Oracle env + pinned runtime deps, non-editable, no torch** → approved; execution is
   NEXT. (The Phase-1 batched dependency ask, raised early because the uv ask was already
   blocking — batching per the permission charter.)
3. **lrag store setup writing `~/.zshenv`** → approved, README-documented form.

## Friction

1. `surface`: preflight doctor / session-0 contract · `expected vs actual`: contract
   expects "run the doctor, fix reds by hints" — actual fresh machine had no `uv`, so the
   doctor could not run at all (system python 3.9.6 also lacks `tomllib`) · `workaround`:
   ran the doctor under system python3 for a partial red enumeration, then an
   operator-approved `brew install uv` · `cost`: one blocking operator round-trip ·
   `recommendation`: the ledger README / session-0 contract should name "uv installed" as
   an explicit fresh-machine operator prerequisite, beside the lrag bootstrap.
2. `surface`: lrag bootstrap commands · `expected vs actual`: the two documented commands
   assume a configured `LRAG_STORE`; a fresh machine has no store, and lrag (correctly)
   refuses to invent one — additionally `--allow-empty` is a *global* flag
   (`lrag --allow-empty collection new …`), not a subcommand option, which one retry
   discovered · `workaround`: operator-approved README setup (`~/.lrag/store` +
   `~/.zshenv` export), then the documented commands with `--allow-empty` · `cost`: one
   operator round-trip + two usage-error retries · `recommendation`: the session-0
   contract should carry the store prerequisite and the exact `--allow-empty` form.
