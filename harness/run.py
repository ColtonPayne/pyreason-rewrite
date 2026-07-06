"""Differential runner: capture each case per engine with a same-engine repeat,
then judge — pass / divergent / irreproducible / error.

Every verdict-bearing run pairs with a same-engine repeat in a fresh process
(`PYTHONHASHSEED` pinned), so the exit taxonomy can separate the three signals:
a cross-engine divergence is a finding, a same-engine mismatch is a harness or
environment failure and never a claim about either engine. With a single
`--engine-a`, the runner is the oracle-vs-oracle self-proof (two independent
pairs of the same engine).

Exit codes: 0 every case passes, 1 any case does not, 2 usage.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

from harness.compare import compare_probes

REPO = Path(__file__).resolve().parent.parent
HASHSEED = "0"


def capture_subprocess(python_exe: str, case_path: Path, out_path: Path) -> int:
    """Run one capture in a bare engine process; stdout/stderr land beside the
    artifact for diagnosis (raw artifacts are preserved, digests are tripwires)."""
    proc = subprocess.run(
        [python_exe, "-m", "harness.capture", str(case_path), str(out_path)],
        capture_output=True, text=True, cwd=REPO,
        env={"PATH": "/usr/bin:/bin", "PYTHONHASHSEED": HASHSEED},
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.with_suffix(".log").write_text(proc.stdout + proc.stderr)
    return proc.returncode


def judge_case(case: dict, artifacts: dict) -> dict:
    """Judge one case from its four artifacts {a1, a2, b1, b2} (parsed JSON).

    Pure — no I/O — so the taxonomy is testable without an engine.
    """
    for name in ("a1", "a2", "b1", "b2"):
        if artifacts[name] is None or "error" in artifacts[name]:
            detail = (artifacts[name] or {}).get("error", "capture did not run")
            return {"status": "error", "detail": f"{name}: {detail}"}

    policy = case.get("comparison", {}).get("probes", {})
    for engine, r1, r2 in (("engine-a", "a1", "a2"), ("engine-b", "b1", "b2")):
        if artifacts[r1]["digests"] != artifacts[r2]["digests"]:
            probes = compare_probes(artifacts[r1]["probes"], artifacts[r2]["probes"])
            return {"status": "irreproducible", "detail": engine, "probes": probes}

    mismatched = compare_probes(
        artifacts["a1"]["probes"], artifacts["b1"]["probes"], policy
    )
    if mismatched:
        return {"status": "divergent", "probes": mismatched}
    return {"status": "pass"}


def run_case(case_path: Path, engine_a: str, engine_b: str, results_dir: Path,
             capture=capture_subprocess) -> dict:
    case = json.loads(case_path.read_text())
    case_dir = results_dir / case["id"]
    artifacts = {}
    for name, exe in (("a1", engine_a), ("a2", engine_a),
                      ("b1", engine_b), ("b2", engine_b)):
        out = case_dir / f"{name}.json"
        capture(exe, case_path, out)
        artifacts[name] = json.loads(out.read_text()) if out.exists() else None
    verdict = judge_case(case, artifacts)
    verdict["case_id"] = case["id"]
    return verdict


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cases", type=Path, required=True,
                        help="a case file or a directory of *.json cases")
    parser.add_argument("--engine-a", required=True,
                        help="python executable of engine A's environment")
    parser.add_argument("--engine-b", default=None,
                        help="python executable of engine B (default: engine A — the self-proof)")
    parser.add_argument("--results", type=Path, default=REPO / "results")
    args = parser.parse_args(argv)

    engine_b = args.engine_b or args.engine_a
    case_paths = (sorted(args.cases.glob("*.json"))
                  if args.cases.is_dir() else [args.cases])
    if not case_paths:
        print(f"no cases found under {args.cases}", file=sys.stderr)
        return 2

    verdicts = [run_case(p, args.engine_a, engine_b, args.results)
                for p in case_paths]
    report = {"engine_a": args.engine_a, "engine_b": engine_b,
              "hashseed": HASHSEED, "verdicts": verdicts}
    args.results.mkdir(parents=True, exist_ok=True)
    (args.results / "report.json").write_text(json.dumps(report, indent=2))

    for v in verdicts:
        line = f"{v['status']:<15} {v['case_id']}"
        if v.get("probes"):
            line += f"  probes: {', '.join(v['probes'])}"
        if v.get("detail"):
            line += f"  ({v['detail']})"
        print(line)
    ok = all(v["status"] == "pass" for v in verdicts)
    print(f"\n{'ALL PASS' if ok else 'NOT PASSING'} ({len(verdicts)} case(s))")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
