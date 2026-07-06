<!-- doccode: pyreason-rewrite-docs-ledger-README -->
# Campaign ledger — the session-banking seam

Each campaign session banks its state here as `session-<N>.md`, following the
shared-brain-optimization pattern: what ran, what it proved (with the numbers), what was
committed, and the single **NEXT** step. The newest session file is the resume point — a
fresh agent (or a weaker one picking up after the Fable window) starts by reading the
newest session, not by reconstructing history.

**Session 0 is the fresh-environment preflight**: on the machine that runs the campaign,
run `uv run python tools/hive_preflight.py --json`, fix anything red using its hints, and
bank the passing JSON report plus a one-line verdict as `session-0.md`. No campaign work
starts on a machine whose preflight is red.

A fresh machine has one expected red: the lrag registry is **machine-local**, so session 0
bootstraps it — the single registry write this repo ever performs:

```
uv run --directory $HIVEMIND_ROOT/local-rag lrag collection new pyreason-analysis --path ~/Projects/dyuman-pryeason
uv run --directory $HIVEMIND_ROOT/local-rag lrag sync -c pyreason-analysis
```

Every retrieval thereafter passes `--no-sync`. (`$HIVEMIND_ROOT` defaults to
`~/Projects/ai-hivemind`; the manifest's `~`-rooted entries resolve per-machine, so the
same committed `repos.toml` works on any home path.)

A session file states, in order:

1. **Verdict** — one line: what this session established.
2. **Evidence** — the runs/tests/measurements that force the verdict (paths to committed
   artifacts, not inlined dumps).
3. **Committed** — the commits this session landed (SHA + one-line why).
4. **NEXT** — the single next step, concrete enough for a cold agent to execute.
