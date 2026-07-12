"""AC-4 benchmark runner: measure one engine over the committed workload
ladder, one fresh process per measurement.

Two modes, one file (mirroring capture.py's subprocess seam so the engines
never share a process):

- **Parent** (the default, run from the campaign venv):
  `uv run python -m harness.bench --engine <python> --cases <file-or-dir>
  --repeats N --results <dir> --tag <label>` — for each case and repeat,
  spawns `/usr/bin/time -l <engine-python> -m harness.bench --child ...`
  (fresh interpreter per run, `PYTHONHASHSEED` pinned like harness.run),
  parses the child's timing payload plus the OS-reported peak RSS, and
  writes one aggregate report with medians and the control-repeat noise
  band. Any failed child run fails the invocation — a partial series is
  never silently aggregated.

- **Child** (`<engine-python> -m harness.bench --child <case.json>
  <out.json>`): runs INSIDE the engine environment. Reuses the capture
  module's validated input-application helpers (validate_case,
  apply_settings, build_graph, build_rule, add_fact_from_args,
  build_reason_args — reuse, never duplication) but runs **no probes**:
  probe rendering is comparison work, not engine work, so the measured
  window is exactly import -> setup -> reason. One-step-form cases only
  (the ladder's form); `timesteps` is always an explicit bound there
  (docs/perf/ladder.md, the B16 constraint).

Metrics per run (seconds via time.perf_counter unless noted):
- `import_s`  — `import pyreason` in a fresh process. For the pinned
  oracle this includes loading (not building) the numba kernel cache; the
  one-time cache *build* is banked separately as context, never as a
  comparison bar.
- `setup_s`   — settings + graph load + rules + facts + ipl.
- `reason_s`  — the `reason()` call: steady reasoning throughput per rung.
- `cold_start_s` — `import_s + reason_s`, computed by the parent: the
  fresh-process import + first-`reason()` metric (the small rung is the
  designated cold-start workload).
- `maxrss_bytes` — peak resident set size of the whole child process, as
  reported by `/usr/bin/time -l` (macOS reports bytes; it takes the value
  from wait4()'s per-child rusage, so repeats never contaminate each other
  the way an in-parent RUSAGE_CHILDREN aggregate would — that counter is
  monotonic across children, which is why it is NOT used here). The window
  covers import + setup + reason (no probes) and is documented as
  peak-of-process, not reasoning-only.
- `wall_s`    — parent-observed wall-clock of the whole child, context for
  the timer values.

The noise band: for every metric the aggregate carries median, min, max,
and spread (max - min) over the same-config repeats — the control-repeat
band the charter requires; cross-engine deltas smaller than this band are
ties. Exit codes: 0 all runs measured and aggregated, 1 any child run
failed, 2 usage.
"""

import argparse
import json
import os
import platform
import re
import statistics
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
HASHSEED = "0"  # pinned like harness.run: measurement runs under the same
                # env fingerprint as equivalence runs — shared inputs, shared env
TIME_TOOL = "/usr/bin/time"  # -l: per-child rusage on macOS (bytes)

MAXRSS_RE = re.compile(r"(\d+)\s+maximum resident set size")
CHILD_METRICS = ("import_s", "setup_s", "reason_s")


# ---------------------------------------------------------------- pure layer

def parse_maxrss(time_l_output: str):
    """Peak RSS in bytes from `/usr/bin/time -l` stderr text, or None.

    Searches the whole text (the child's own stderr precedes the rusage
    block); the last match wins so a child that happened to echo a
    similar-looking line cannot shadow the real trailing block."""
    matches = MAXRSS_RE.findall(time_l_output)
    return int(matches[-1]) if matches else None


def summarize(values):
    """Median-with-spread for one metric's same-config repeats.

    spread = max - min is the control-repeat noise band; median is the
    banked number. Raw values ride along so the report is re-derivable."""
    vals = list(values)
    if not vals:
        return None
    return {"n": len(vals), "median": statistics.median(vals),
            "min": min(vals), "max": max(vals),
            "spread": max(vals) - min(vals), "values": vals}


def child_payload_fault(payload) -> str | None:
    """One child run's payload validated before it may aggregate — a child
    that died after writing a partial file must fail the run, never bank."""
    if not isinstance(payload, dict):
        return "child payload is not an object"
    if payload.get("schema") != 1 or payload.get("mode") != "bench-child":
        return "unexpected child payload schema"
    for key in CHILD_METRICS:
        value = payload.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) \
                or value < 0:
            return f"child payload missing/invalid {key!r}"
    return None


def aggregate_case(runs):
    """Per-metric summaries over one case's repeats. `cold_start_s` is
    derived per run (import + first reason — every child's reason() is its
    process's first) before summarizing; maxrss_bytes/wall_s summarize only
    over runs that carry them."""
    metrics = {}
    for key in CHILD_METRICS:
        metrics[key] = summarize(r[key] for r in runs)
    metrics["cold_start_s"] = summarize(
        r["import_s"] + r["reason_s"] for r in runs)
    for key in ("maxrss_bytes", "wall_s"):
        present = [r[key] for r in runs if r.get(key) is not None]
        metrics[key] = summarize(present)
    return metrics


# ------------------------------------------------------------------- child

def child_main(case_path: Path, out_path: Path) -> int:
    """Measure this engine environment over one ladder case: import ->
    setup -> reason, no probes, one timing payload. Runs with the repo root
    on sys.path exactly like harness.capture (`-m harness.bench`)."""
    from harness.capture import (validate_case, apply_settings, build_graph,
                                 build_rule, add_fact_from_args,
                                 build_reason_args)
    try:
        case = json.loads(case_path.read_text())
    except (OSError, ValueError) as exc:
        print(f"unreadable case file: {exc!r}", file=sys.stderr)
        return 2
    fault = validate_case(case)
    if fault is None and ("steps" in case or "reason" not in case["inputs"]):
        fault = ("bench measures one-step-form cases with an inputs.reason "
                 "block (the ladder's form)")
    if fault:
        print(f"invalid bench case: {fault}", file=sys.stderr)
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
            pr.load_graphml(str(REPO / graph_spec["graphml_path"]))
        else:
            pr.load_graph(build_graph(graph_spec))
    for rule in inputs.get("rules", []):
        pr.add_rule(build_rule(pr, rule))
    for fact in inputs.get("facts", []):
        add_fact_from_args(pr, fact)
    for pred_a, pred_b in inputs.get("ipl", []):
        pr.add_inconsistent_predicate(pred_a, pred_b)
    setup_s = time.perf_counter() - t1

    t2 = time.perf_counter()
    pr.reason(**build_reason_args(pr, inputs["reason"]))
    reason_s = time.perf_counter() - t2

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps({
        "schema": 1, "mode": "bench-child", "case_id": case["id"],
        "import_s": import_s, "setup_s": setup_s, "reason_s": reason_s,
        "python": sys.version.split()[0], "executable": sys.executable,
    }, indent=2, sort_keys=True))
    return 0


# ------------------------------------------------------------------ parent

def measure_once(engine: str, case_path: Path, out_path: Path) -> dict:
    """One fresh-process measurement: child under /usr/bin/time -l; returns
    the run record or an {'error': ...} record. Raw stderr is preserved
    beside the payload for auditability."""
    out_path.unlink(missing_ok=True)
    t0 = time.perf_counter()
    proc = subprocess.run(
        [TIME_TOOL, "-l", engine, "-m", "harness.bench",
         "--child", str(case_path), str(out_path)],
        capture_output=True, text=True, cwd=REPO,
        env={**os.environ, "PYTHONHASHSEED": HASHSEED},
    )
    wall_s = time.perf_counter() - t0
    out_path.with_suffix(".time.txt").write_text(proc.stderr)
    if proc.returncode != 0:
        return {"error": f"child exited {proc.returncode}: "
                         f"{proc.stderr.strip().splitlines()[:3]}"}
    try:
        payload = json.loads(out_path.read_text())
    except (OSError, ValueError) as exc:
        return {"error": f"unreadable child payload: {exc!r}"}
    fault = child_payload_fault(payload)
    if fault:
        return {"error": fault}
    return {**payload, "maxrss_bytes": parse_maxrss(proc.stderr),
            "wall_s": wall_s}


def machine_identity() -> dict:
    """The banked machine fingerprint. Chip via sysctl (best-effort — the
    identity block must never fail a measurement run)."""
    try:
        chip = subprocess.run(
            ["sysctl", "-n", "machdep.cpu.brand_string"],
            capture_output=True, text=True, timeout=10).stdout.strip() or None
    except OSError:
        chip = None
    return {"platform": platform.platform(), "machine": platform.machine(),
            "mac_ver": platform.mac_ver()[0], "chip": chip,
            "parent_python": sys.version.split()[0]}


def parent_main(args) -> int:
    case_paths = (sorted(args.cases.glob("*.json"))
                  if args.cases.is_dir() else [args.cases])
    if not case_paths or not all(p.is_file() for p in case_paths):
        print(f"no case file(s) at {args.cases}", file=sys.stderr)
        return 2
    run_dir = args.results / args.tag
    run_dir.mkdir(parents=True, exist_ok=True)

    report = {"schema": 1, "mode": "bench-report", "engine": args.engine,
              "hashseed": HASHSEED, "repeats": args.repeats,
              "machine": machine_identity(),
              "started_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
              "cases": {}}
    failed = False
    for case_path in case_paths:
        case_id = json.loads(case_path.read_text()).get("id", case_path.stem)
        runs = []
        for i in range(args.repeats):
            record = measure_once(args.engine, case_path,
                                  run_dir / f"{case_id}-run{i}.json")
            if "error" in record:
                print(f"FAIL {case_id} run {i}: {record['error']}",
                      file=sys.stderr)
                failed = True
                runs = []
                break
            runs.append(record)
            print(f"{case_id} run {i}: import {record['import_s']:.3f}s "
                  f"setup {record['setup_s']:.3f}s "
                  f"reason {record['reason_s']:.3f}s "
                  f"maxrss {record['maxrss_bytes']} wall {record['wall_s']:.2f}s")
        if runs:
            report["cases"][case_id] = {
                "engine_python": runs[0]["python"],
                "engine_executable": runs[0]["executable"],
                "runs": runs, "summary": aggregate_case(runs)}
    report_path = run_dir / "bench-report.json"
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True))
    print(f"report: {report_path}")
    return 1 if failed else 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--child", nargs=2, metavar=("CASE", "OUT"),
                        help="internal: measure one case inside this engine env")
    parser.add_argument("--engine", help="python executable of the engine env")
    parser.add_argument("--cases", type=Path,
                        help="a case file or a directory of *.json cases")
    parser.add_argument("--repeats", type=int, default=5)
    parser.add_argument("--results", type=Path,
                        default=REPO / "results-phase4-baselines")
    parser.add_argument("--tag", default=time.strftime("%Y%m%d-%H%M%S"),
                        help="subdirectory label for this invocation's artifacts")
    args = parser.parse_args(argv)
    if args.child:
        return child_main(Path(args.child[0]), Path(args.child[1]).resolve())
    if not args.engine or not args.cases:
        parser.error("--engine and --cases are required in parent mode")
    if args.repeats < 1:
        parser.error("--repeats must be >= 1")
    return parent_main(args)


if __name__ == "__main__":
    sys.exit(main())
