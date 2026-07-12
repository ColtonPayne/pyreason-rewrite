<!-- doccode: pyreason-rewrite-docs-lab-sanders-install-log -->
# sanders install log

Everything installed on `sanders.syr.edu` (as `crpayne`, user-home only, no sudo) that
was not there before — an operator condition of the
[lab-compute waiver](../ledger/lab-compute-waiver.md). One line per install, newest last.
Removals are logged too, so the box can be returned to its prior state.

| Date | What | Where | Why |
|------|------|-------|-----|
| 2026-07-12 | uv 0.11.28 (astral.sh standalone installer) | `~crpayne/.local/bin/uv` (+ `~/.local/share/uv`) | toolchain for the oracle/campaign envs |
| 2026-07-12 | uv-managed CPython 3.10.20 (linux-x86_64-gnu) | `~crpayne/.local/share/uv/python/` | the oracle env's pinned interpreter |
| 2026-07-12 | oracle env: pyreason-3.6.0 wheel (built from the pinned source), numba 0.59.1, llvmlite 0.42.0, numpy 1.26.4, networkx 3.4.2, pyyaml 6.0.3, pandas 2.3.3, memory_profiler 0.61.0, pytest 9.1.1, setuptools 80.10.2 (+ transitive deps) | `~crpayne/pyreason-campaign/oracle-env/` | the pinned oracle, mirroring the laptop oracle-env exactly |
| 2026-07-12 | campaign repo working tree (rsync, no .git) + `~/pyreason-campaign/oracle-build/` wheel scratch | `~crpayne/pyreason-campaign/pyreason-rewrite/` | the rewrite engine + harness |
| 2026-07-12 | Pokec dataset (SNAP soc-pokec relationships + profiles + readme) | `~crpayne/pyreason-campaign/data/pokec/` | the §4.2 replication's input data |
| 2026-07-12 | paper-era env: uv venv (CPython 3.10.20) + pyreason==1.2.4 from PyPI (+ its pinned deps) | `~crpayne/pyreason-campaign/paper-era-env/` | the paper-publication-era engine, for the regression finding |
| 2026-07-12 | `paper_era_driver.py` (campaign-authored driver for the 1.2.4 YAML API) | `~crpayne/pyreason-campaign/` | runs the Pokec rungs on the paper-era engine |
