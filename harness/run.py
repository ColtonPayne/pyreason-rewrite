"""Differential runner: capture each case per engine with a same-engine repeat,
then judge — pass / divergent / irreproducible / error.

Every verdict-bearing run pairs with a same-engine repeat in a fresh process
(`PYTHONHASHSEED` pinned on top of the operator's environment), so the exit
taxonomy can separate the three signals: a cross-engine divergence is a
finding, a same-engine mismatch is a harness or environment failure and never
a claim about either engine. With a single `--engine-a`, the runner is the
oracle-vs-oracle self-proof (two independent pairs of the same engine) — in
that mode a cross-pair mismatch is also irreproducibility, never a divergence.

Same-engine repeats compare by exact digest even for tolerance-policied probes:
per the charter, engine nondeterminism is explicitly characterized and
canonicalized or exempted per-case, never absorbed by a tolerance.

Per-case durability: after a case's four captures land, the runner writes an
atomic completion marker (`case.done.json`, tmp + rename) beside them,
recording the invocation identity (engine executables, hash seed, the case
file's byte digest) plus each capture's exit code and each artifact file's
digest. Completion is thereafter decidable from the results dir alone: a
re-invocation over the same dir re-judges a completed case from its on-disk
artifacts (never re-capturing) and re-runs an incomplete one from scratch, so
a host interruption loses at most the in-flight case. Because every verdict —
first run or resumed — is derived from the artifacts by the same pure judge,
a resumed sweep's verdict list equals a single-invocation sweep's; the report
additionally carries a `resume` block naming which cases were prior-complete,
so a resumed sweep always SAYS it was resumed (a verdict-of-record claiming
single-invocation coherence needs `resumed: false` plus the usual mtime
analysis). A completed case with an `error` verdict is still completed — its
captures ran to their recorded exit — and is skipped like any other; deleting
its case directory (or just its marker) is the deliberate way to force a
re-capture.

Exit codes: 0 every case passes, 1 any case does not (the per-case status in
report.json and on the console carries the taxonomy), 2 usage.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from harness.compare import compare_probes

REPO = Path(__file__).resolve().parent.parent
HASHSEED = "0"
CAPTURE_NAMES = ("a1", "a2", "b1", "b2")
MARKER_NAME = "case.done.json"
MARKER_SCHEMA = 1


def capture_subprocess(python_exe: str, case_path: Path, out_path: Path) -> int:
    """Run one capture in a bare engine process; stdout/stderr land beside the
    artifact for diagnosis (raw artifacts are preserved, digests are tripwires).
    Any prior artifact/log at the target is removed first, so a capture that
    dies natively can never leave a stale predecessor to be judged."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.unlink(missing_ok=True)
    out_path.with_suffix(".log").unlink(missing_ok=True)
    proc = subprocess.run(
        [python_exe, "-m", "harness.capture", str(case_path), str(out_path)],
        capture_output=True, text=True, cwd=REPO,
        env={**os.environ, "PYTHONHASHSEED": HASHSEED},
    )
    out_path.with_suffix(".log").write_text(proc.stdout + proc.stderr)
    return proc.returncode


def load_artifact(out_path: Path, returncode: int):
    """One capture's artifact, or a synthesized error artifact — a non-zero exit
    or an unreadable file is that run's failure, never a batch crash."""
    if not out_path.exists():
        return {"error": f"capture exited {returncode} with no artifact"}
    try:
        artifact = json.loads(out_path.read_text())
    except (OSError, ValueError) as exc:
        return {"error": f"unreadable artifact: {exc!r}"}
    if returncode != 0 and "error" not in artifact:
        return {"error": f"capture exited {returncode} despite writing an artifact"}
    return artifact


def judge_case(case: dict, artifacts: dict, self_proof: bool = False) -> dict:
    """Judge one case from its four artifacts {a1, a2, b1, b2} (parsed JSON).

    Pure — no I/O — so the taxonomy is testable without an engine.
    """
    for name in ("a1", "a2", "b1", "b2"):
        if artifacts[name] is None or "error" in artifacts[name]:
            detail = (artifacts[name] or {}).get("error", "capture did not run")
            return {"status": "error", "detail": f"{name}: {detail}"}
        if artifacts[name].get("schema") != 1:
            return {"status": "error",
                    "detail": f"{name}: unexpected artifact schema"}

    for r1, r2 in (("a1", "a2"), ("b1", "b2")):
        same_engine = (artifacts[r1]["engine"]["executable"]
                       == artifacts[r2]["engine"]["executable"])
        same_env = artifacts[r1]["env"] == artifacts[r2]["env"]
        if not (same_engine and same_env):
            return {"status": "error",
                    "detail": f"{r1}/{r2}: engine identity or env fingerprint mismatch"}

    unstable = [engine for engine, r1, r2 in
                (("engine-a", "a1", "a2"), ("engine-b", "b1", "b2"))
                if artifacts[r1]["digests"] != artifacts[r2]["digests"]]
    if unstable:
        return {"status": "irreproducible", "detail": ", ".join(unstable)}

    policy = case.get("comparison", {}).get("probes", {})
    mismatched = compare_probes(
        artifacts["a1"]["probes"], artifacts["b1"]["probes"], policy
    )
    if mismatched:
        if self_proof:
            return {"status": "irreproducible", "probes": mismatched,
                    "detail": "cross-pair mismatch in self-proof mode"}
        return {"status": "divergent", "probes": mismatched}
    return {"status": "pass"}


def file_digest(path: Path):
    """sha256 of a file's bytes, or None when the file is absent/unreadable —
    None is itself a recordable state (a capture that exited nonzero without
    writing an artifact has no artifact to hash, and that absence must resume
    to the same error verdict, not a silent retry)."""
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def read_marker(case_dir: Path):
    """The case's completion marker, parsed — or None when absent, unreadable,
    or not an object. An unreadable marker means exactly what a missing one
    means (the case re-runs); it can never fail a sweep."""
    try:
        marker = json.loads((case_dir / MARKER_NAME).read_text())
    except (OSError, ValueError):
        return None
    return marker if isinstance(marker, dict) else None


def completed_marker(case_dir: Path, case_digest: str,
                     engine_a: str, engine_b: str):
    """The marker vouching this case's four captures completed under exactly
    this invocation's inputs — or None, meaning the case must (re)run.

    Decided from the on-disk results dir alone: the marker's identity fields
    must match the current invocation (both engine executables, the pinned
    hash seed, the case file's byte digest — an edited case always re-runs),
    and every artifact it lists must still hash to the recorded digest, so a
    truncated or half-written artifact invalidates the case instead of being
    judged as if it were the completed capture's output.
    """
    marker = read_marker(case_dir)
    if marker is None or marker.get("schema") != MARKER_SCHEMA:
        return None
    identity = {"case_digest": case_digest, "engine_a": engine_a,
                "engine_b": engine_b, "hashseed": HASHSEED}
    if any(marker.get(key) != value for key, value in identity.items()):
        return None
    returncodes, artifacts = marker.get("returncodes"), marker.get("artifacts")
    if not (isinstance(returncodes, dict)
            and set(returncodes) == set(CAPTURE_NAMES)
            and all(isinstance(rc, int) for rc in returncodes.values())):
        return None
    if not (isinstance(artifacts, dict)
            and set(artifacts) == set(CAPTURE_NAMES)):
        return None
    for name in CAPTURE_NAMES:
        if file_digest(case_dir / f"{name}.json") != artifacts[name]:
            return None
    return marker


def write_marker(case_dir: Path, marker: dict) -> None:
    """Written atomically (tmp + rename) and only AFTER all four captures: a
    marker on disk always means a completed case; an interruption at any
    earlier moment leaves no marker and the whole case re-runs."""
    tmp = case_dir / (MARKER_NAME + ".tmp")
    tmp.write_text(json.dumps(marker, indent=2, sort_keys=True))
    os.replace(tmp, case_dir / MARKER_NAME)


def run_case(case_path: Path, engine_a: str, engine_b: str, results_dir: Path,
             capture=None):
    """Capture-or-resume one case, then judge it from its on-disk artifacts.

    Returns (verdict, prior) — prior True when the four artifacts were
    complete from an earlier invocation and were re-judged, not re-captured.
    The judge always reads the artifacts, so the verdict is identical either
    way; `prior` only feeds the report's resume honesty block.
    """
    capture = capture or capture_subprocess
    case_bytes = case_path.read_bytes()
    case = json.loads(case_bytes)
    case_digest = hashlib.sha256(case_bytes).hexdigest()
    case_dir = results_dir / case["id"]
    marker = completed_marker(case_dir, case_digest, engine_a, engine_b)
    if marker is None:
        case_dir.mkdir(parents=True, exist_ok=True)
        # A stale marker goes before any capture starts — never after some:
        # were it left in place, an interruption mid-recapture would pair the
        # old marker with a partially refreshed case dir. (The per-artifact
        # digest check would still catch that; removing first keeps "marker
        # present == case complete" a single-cause invariant.)
        (case_dir / MARKER_NAME).unlink(missing_ok=True)
        returncodes = {}
        for name, exe in zip(CAPTURE_NAMES,
                             (engine_a, engine_a, engine_b, engine_b)):
            returncodes[name] = capture(exe, case_path,
                                        case_dir / f"{name}.json")
        write_marker(case_dir, {
            "schema": MARKER_SCHEMA, "case_id": case["id"],
            "case_digest": case_digest,
            "engine_a": engine_a, "engine_b": engine_b, "hashseed": HASHSEED,
            "returncodes": returncodes,
            "artifacts": {name: file_digest(case_dir / f"{name}.json")
                          for name in CAPTURE_NAMES},
            "completed_at": datetime.now(timezone.utc).isoformat()})
    else:
        returncodes = {name: marker["returncodes"][name]
                       for name in CAPTURE_NAMES}
    artifacts = {name: load_artifact(case_dir / f"{name}.json",
                                     returncodes[name])
                 for name in CAPTURE_NAMES}
    verdict = judge_case(case, artifacts, self_proof=engine_a == engine_b)
    verdict["case_id"] = case["id"]
    return verdict, marker is not None


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
    if not case_paths or not all(p.is_file() for p in case_paths):
        print(f"no case file(s) at {args.cases}", file=sys.stderr)
        return 2
    ids = {}
    for p in case_paths:
        try:
            case_id = json.loads(p.read_text()).get("id")
        except ValueError as exc:
            print(f"unreadable case {p}: {exc!r}", file=sys.stderr)
            return 2
        if case_id in ids:
            print(f"duplicate case id {case_id!r} in {p} and {ids[case_id]} — "
                  f"artifacts would clobber", file=sys.stderr)
            return 2
        ids[case_id] = p

    verdicts, prior_ids, captured_ids = [], [], []
    for p in case_paths:
        verdict, prior = run_case(p, args.engine_a, engine_b, args.results)
        verdicts.append(verdict)
        (prior_ids if prior else captured_ids).append(verdict["case_id"])
    # The verdict list is derived from the artifacts either way, so it equals
    # a single-invocation sweep's; the resume block is the deliberate honesty
    # extension — `resumed` is true iff any case was prior-complete, so a
    # single-invocation claim can be checked from the report itself.
    report = {"engine_a": args.engine_a, "engine_b": engine_b,
              "hashseed": HASHSEED, "verdicts": verdicts,
              "resume": {"resumed": bool(prior_ids),
                         "prior_complete": prior_ids,
                         "captured_this_invocation": captured_ids}}
    args.results.mkdir(parents=True, exist_ok=True)
    (args.results / "report.json").write_text(json.dumps(report, indent=2))

    prior_set = set(prior_ids)
    for v in verdicts:
        line = f"{v['status']:<15} {v['case_id']}"
        if v.get("probes"):
            line += f"  probes: {', '.join(v['probes'])}"
        if v.get("detail"):
            line += f"  ({v['detail']})"
        if v["case_id"] in prior_set:
            line += "  [prior-complete]"
        print(line)
    ok = all(v["status"] == "pass" for v in verdicts)
    tally = f"{len(verdicts)} case(s)"
    if prior_ids:
        tally += (f"; RESUMED — {len(prior_ids)} prior-complete, "
                  f"{len(captured_ids)} captured this invocation")
    print(f"\n{'ALL PASS' if ok else 'NOT PASSING'} ({tally})")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
