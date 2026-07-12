"""Phase-4 profiling driver: run one ladder case in-process on the
reference core with cProfile around the `reason()` call, and emit a pstats
dump plus readable top-N tables by cumulative and by self time.

Run under the engine interpreter, from the repo root (stdlib only):

  PYTHONHASHSEED=0 scripts/rewrite-python -m harness.profile \\
    --case harness/cases/perf-ladder-medium.json \\
    --out-dir results-phase4-profile/<tag> [--top 25]

This driver is only meaningful for the pure-Python reference core. The
pinned oracle's hot loop is numba-jitted: cProfile sees one opaque
dispatcher call, so per-function attribution there is meaningless — the
oracle's decomposition is per-stage wall-clock from harness/bench.py
(banked in docs/perf/profile-phase4.md).

Measured window: import and input setup run unprofiled (they are bench.py
territory); a single `reason()` runs under cProfile. The profiled reason()
wall-clock is recorded in the outputs so the cProfile overhead can be
stated against the *unprofiled* banked baseline
(docs/perf/rewrite-baselines.md) — profiled and unprofiled numbers are
never mixed.

Outputs, in --out-dir:
- `<case-id>.pstats`       — binary dump, `pstats.Stats`-loadable.
- `<case-id>-profile.txt`  — wall-clocks + top-N by cumulative + top-N by
  self time, percentages of total profiled reason time.
- `<case-id>-profile.json` — the same rows, machine-readable.

Percentages use the profiler's own accounting: total profiled time =
sum of every entry's self time (tt), the denominator cProfile itself
reports as the profile's total — cumulative percentages can exceed rows'
sums since callers subsume callees.
"""

import argparse
import cProfile
import json
import pstats
import sys
import time
from pathlib import Path

# pstats entry shape: stats[(file, line, name)] = (cc, nc, tt, ct, callers)
#   cc = primitive (non-recursive) calls, nc = total calls,
#   tt = self time, ct = cumulative time.
SORT_KEYS = {"cumulative": 3, "self": 2}


# ---------------------------------------------------------------- pure layer

def func_label(func: tuple) -> str:
    """Human-readable label for a pstats function triple.

    Built-ins/primitives carry file '~' (pstats' convention) — label them
    by name alone; real functions get a short `parent/file:line(name)` so
    two same-named helpers in different modules stay distinguishable."""
    filename, line, name = func
    if filename == "~":
        return name
    path = Path(filename)
    short = "/".join(path.parts[-2:]) if len(path.parts) >= 2 else str(path)
    return f"{short}:{line}({name})"


def total_profiled_s(stats: dict) -> float:
    """Total profiled time: the sum of every entry's self time — the same
    total cProfile prints as the profile's overall seconds."""
    return sum(entry[2] for entry in stats.values())


def top_rows(stats: dict, sort_by: str, n: int) -> list[dict]:
    """The top-`n` entries of a pstats stats mapping by 'cumulative' or
    'self' time, as rows with self/cum seconds and percentages of the
    total profiled time. Raises on an unknown sort key rather than
    silently sorting by something else."""
    if sort_by not in SORT_KEYS:
        raise ValueError(f"unknown sort key {sort_by!r} "
                         f"(expected one of {sorted(SORT_KEYS)})")
    idx = SORT_KEYS[sort_by]
    total = total_profiled_s(stats)
    ranked = sorted(stats.items(), key=lambda item: item[1][idx],
                    reverse=True)[:n]
    rows = []
    for func, (cc, nc, tt, ct, _callers) in ranked:
        rows.append({
            "func": func_label(func),
            "calls": nc, "primitive_calls": cc,
            "self_s": tt, "cum_s": ct,
            "self_pct": (100.0 * tt / total) if total else 0.0,
            "cum_pct": (100.0 * ct / total) if total else 0.0,
        })
    return rows


def format_rows(rows: list[dict], title: str) -> str:
    """One readable table for a top-N row list: header + fixed-width
    columns, seconds to 3 decimals, percentages to 1."""
    lines = [title,
             f"{'self_s':>9} {'self%':>6} {'cum_s':>9} {'cum%':>6} "
             f"{'calls':>10}  function"]
    for r in rows:
        calls = (str(r["calls"]) if r["calls"] == r["primitive_calls"]
                 else f"{r['calls']}/{r['primitive_calls']}")
        lines.append(f"{r['self_s']:>9.3f} {r['self_pct']:>6.1f} "
                     f"{r['cum_s']:>9.3f} {r['cum_pct']:>6.1f} "
                     f"{calls:>10}  {r['func']}")
    return "\n".join(lines)


# ------------------------------------------------------------------- driver

def profile_case(case_path: Path, out_dir: Path, top_n: int) -> int:
    """Set up one ladder case unprofiled, run reason() once under cProfile,
    write the dump + reports. Mirrors bench.child_main's input application
    (capture's validated helpers — reuse, never duplication)."""
    from harness.capture import (validate_case, apply_settings, build_graph,
                                 build_rule, add_fact_from_args,
                                 build_reason_args)
    repo = Path(__file__).resolve().parent.parent
    try:
        case = json.loads(case_path.read_text())
    except (OSError, ValueError) as exc:
        print(f"unreadable case file: {exc!r}", file=sys.stderr)
        return 2
    fault = validate_case(case)
    if fault is None and ("steps" in case or "reason" not in case["inputs"]):
        fault = ("profile drives one-step-form cases with an inputs.reason "
                 "block (the ladder's form)")
    if fault:
        print(f"invalid profile case: {fault}", file=sys.stderr)
        return 2

    t0 = time.perf_counter()
    import pyreason as pr
    import_s = time.perf_counter() - t0

    inputs = case["inputs"]
    t1 = time.perf_counter()
    apply_settings(pr, inputs.get("settings", {}))
    graph_spec = inputs.get("graph")
    if graph_spec is not None:
        if "graphml_path" in graph_spec:
            pr.load_graphml(str(repo / graph_spec["graphml_path"]))
        else:
            pr.load_graph(build_graph(graph_spec))
    for rule in inputs.get("rules", []):
        pr.add_rule(build_rule(pr, rule))
    for fact in inputs.get("facts", []):
        add_fact_from_args(pr, fact)
    for pred_a, pred_b in inputs.get("ipl", []):
        pr.add_inconsistent_predicate(pred_a, pred_b)
    setup_s = time.perf_counter() - t1

    reason_args = build_reason_args(pr, inputs["reason"])
    profiler = cProfile.Profile()
    t2 = time.perf_counter()
    profiler.enable()
    pr.reason(**reason_args)
    profiler.disable()
    profiled_reason_s = time.perf_counter() - t2

    stats = pstats.Stats(profiler).stats
    case_id = case["id"]
    out_dir.mkdir(parents=True, exist_ok=True)
    profiler.dump_stats(out_dir / f"{case_id}.pstats")

    header = {
        "schema": 1, "mode": "profile-rewrite", "case_id": case_id,
        "python": sys.version.split()[0], "executable": sys.executable,
        "import_s": import_s, "setup_s": setup_s,
        "profiled_reason_s": profiled_reason_s,
        "total_profiled_s": total_profiled_s(stats),
        "top_n": top_n,
    }
    tables = {sort_by: top_rows(stats, sort_by, top_n)
              for sort_by in SORT_KEYS}
    (out_dir / f"{case_id}-profile.json").write_text(json.dumps(
        {**header, "top": tables}, indent=2, sort_keys=True))

    text = [
        f"case {case_id}  python {header['python']}",
        f"import {import_s:.3f}s  setup {setup_s:.3f}s  "
        f"reason (PROFILED — carries cProfile overhead; compare against "
        f"docs/perf/rewrite-baselines.md for the unprofiled number) "
        f"{profiled_reason_s:.3f}s",
        "",
        format_rows(tables["cumulative"],
                    f"top {top_n} by cumulative time"),
        "",
        format_rows(tables["self"], f"top {top_n} by self time (tottime)"),
        "",
    ]
    report_path = out_dir / f"{case_id}-profile.txt"
    report_path.write_text("\n".join(text))
    print(f"profiled reason(): {profiled_reason_s:.3f}s  "
          f"report: {report_path}")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--case", type=Path, required=True,
                        help="one ladder case JSON (one-step form)")
    parser.add_argument("--out-dir", type=Path, required=True,
                        help="artifact directory (gitignored results dir)")
    parser.add_argument("--top", type=int, default=25,
                        help="rows per table (default 25)")
    args = parser.parse_args(argv)
    if args.top < 1:
        parser.error("--top must be >= 1")
    return profile_case(args.case.resolve(), args.out_dir.resolve(),
                        args.top)


if __name__ == "__main__":
    sys.exit(main())
