#!/usr/bin/env python3
"""oracle_smoke — the ARM gate: prove the pinned oracle runs on this machine.

Runs the oracle's own hello-world program (the pinned functional test's form) inside the
dedicated oracle environment and reports import time and reasoning wall time separately —
the first-ever import also builds the numba cache, so a first run is banked as context,
never as a comparison bar.

Run it in a bare subprocess of the oracle env (never the campaign .venv):

    oracle-env/bin/python tools/oracle_smoke.py

The oracle env is rebuilt from scratch as: copy oracle/pyreason (minus .git) to a scratch
dir, `SETUPTOOLS_SCM_PRETEND_VERSION=3.6.0 uv build --wheel`, then
`uv venv oracle-env --python 3.12` and `uv pip install <wheel> numba==0.59.1
numpy==1.26.4 networkx pyyaml pandas memory_profiler pytest`. The clone itself is never
built in place or installed editable (its first import writes inside the package dir).

Exit codes: 0 gate passed, 1 wrong reasoning output or import/run failure.
"""

import sys
import time


def main() -> int:
    t0 = time.perf_counter()
    import pyreason as pr  # first import may build the numba cache and warm up reason()
    import_s = time.perf_counter() - t0

    from importlib.resources import files

    graph_path = str(files("pyreason") / "examples" / "hello-world" / "friends_graph.graphml")

    pr.reset()
    pr.reset_rules()
    pr.reset_settings()
    pr.settings.atom_trace = True

    pr.load_graphml(graph_path)
    pr.add_rule(pr.Rule("popular(x) <-1 popular(y), Friends(x,y), owns(y,z), owns(x,z)", "popular_rule"))
    pr.add_fact(pr.Fact("popular(Mary)", "popular_fact", 0, 2))

    t1 = time.perf_counter()
    interpretation = pr.reason(timesteps=2)
    reason_s = time.perf_counter() - t1

    dataframes = pr.filter_and_sort_nodes(interpretation, ["popular"])
    counts = [len(df) for df in dataframes]
    expected = [1, 2, 3]

    print(f"python        {sys.version.split()[0]} ({sys.platform})")
    print(f"import        {import_s:.2f}s")
    print(f"reason(2)     {reason_s:.2f}s")
    print(f"popular/t     {counts} (expected {expected})")

    if counts != expected:
        print("GATE FAILED: reasoning output does not match the pinned expectation")
        return 1
    print("GATE PASSED")
    return 0


if __name__ == "__main__":
    sys.exit(main())
