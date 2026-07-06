#!/usr/bin/env python3
"""hive_preflight — federation preflight doctor for the pyreason-rewrite campaign repo.

Verifies every shared hivemind mechanism this repo consumes, from this machine, right now:
the umbrella manifest resolves this repo, hstate answers, the corpus link gate is green,
the lrag `pyreason-analysis` collection answers a read-only probe, the oracle clone sits
clean at its pinned commit, the ledger seam is writable, and git identity + hooks are wired.

Run it as campaign Step 0 on any machine (`uv run python tools/hive_preflight.py`); the
marked e2e test wraps it as the MVP acceptance check. Every failure prints an actionable
hint. Exit codes: 0 all checks pass, 1 at least one check failed, 2 usage error.
`--json` emits the machine-readable report the ledger banks.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_NAME = "pyreason-rewrite"
LRAG_COLLECTION = "pyreason-analysis"
LRAG_PROBE_QUERY = "interval lower bound clamp bug"
DEFAULT_UMBRELLA = Path.home() / "Projects" / "ai-hivemind"
LINKS_CHECK_TIMEOUT = 300
CMD_TIMEOUT = 120


def default_run_cmd(argv: list[str], timeout: int = CMD_TIMEOUT, cwd: str | None = None):
    """Run a command, returning (returncode, combined output). Never raises."""
    try:
        proc = subprocess.run(
            argv, capture_output=True, text=True, timeout=timeout, cwd=cwd
        )
        return proc.returncode, proc.stdout + proc.stderr
    except FileNotFoundError as exc:
        return 127, str(exc)
    except subprocess.TimeoutExpired:
        return 124, f"timed out after {timeout}s"


def read_pin(pin_path: Path) -> str:
    """First non-empty, non-comment line of oracle/PIN is the pinned SHA."""
    for line in pin_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            return line
    return ""


def build_checks(root: Path, umbrella: Path, run_cmd) -> list[tuple[str, object, str]]:
    """Each check is (name, thunk -> (ok, detail), hint-on-failure)."""
    manifest = umbrella / "repos.toml"
    hive_state = umbrella / "hive-state"
    local_rag = umbrella / "local-rag"

    def python_version():
        v = sys.version_info
        return v >= (3, 11), f"python {v.major}.{v.minor}.{v.micro}"

    def uv_present():
        path = shutil.which("uv")
        return path is not None, path or "uv not on PATH"

    def umbrella_manifest():
        return manifest.is_file(), str(manifest)

    def manifest_entry():
        import tomllib

        with open(manifest, "rb") as fh:
            repos = tomllib.load(fh)
        entry = repos.get(REPO_NAME)
        if entry is None:
            return False, f"no `{REPO_NAME}` entry in {manifest}"
        entry_root = Path(entry)
        if not entry_root.is_absolute():
            entry_root = umbrella / entry_root
        ok = entry_root.resolve() == root.resolve()
        return ok, f"{REPO_NAME} = {entry!r} -> {entry_root}"

    def hstate_invokable():
        rc, out = run_cmd(
            ["uv", "run", "--directory", str(hive_state), "hstate", "--help"]
        )
        return rc == 0, f"rc={rc}" if rc == 0 else f"rc={rc}: {out[-300:]}"

    def links_gate():
        rc, out = run_cmd(
            [
                "uv", "run", "--directory", str(hive_state),
                "hstate", "links", "check", "--manifest", str(manifest),
            ],
            timeout=LINKS_CHECK_TIMEOUT,
        )
        return rc == 0, "corpus link graph green" if rc == 0 else out[-500:]

    def lrag_probe():
        rc, out = run_cmd(
            [
                "uv", "run", "--directory", str(local_rag),
                "lrag", "retrieve", LRAG_PROBE_QUERY,
                "-c", LRAG_COLLECTION, "--no-sync",
            ]
        )
        if rc != 0:
            return False, f"rc={rc}: {out[-300:]}"
        hit = LRAG_COLLECTION in out
        return hit, "probe returned hits" if hit else "probe returned no documents"

    def oracle_pin():
        pin_path = root / "oracle" / "PIN"
        clone = root / "oracle" / "pyreason"
        if not pin_path.is_file():
            return False, f"{pin_path} missing"
        pinned = read_pin(pin_path)
        rc, head = run_cmd(["git", "-C", str(clone), "rev-parse", "HEAD"])
        if rc != 0:
            return False, f"oracle clone unreadable: {head[-200:]}"
        head = head.strip()
        if head != pinned:
            return False, f"HEAD {head[:12]} != pinned {pinned[:12]}"
        rc, dirty = run_cmd(["git", "-C", str(clone), "status", "--porcelain"])
        clean = rc == 0 and not dirty.strip()
        return clean, f"pinned at {pinned[:12]}, clean" if clean else "oracle tree dirty"

    def ledger_writable():
        ledger = root / "docs" / "ledger"
        ok = ledger.is_dir() and os.access(ledger, os.W_OK)
        return ok, str(ledger)

    def git_wiring():
        rc_n, name = run_cmd(["git", "-C", str(root), "config", "user.name"])
        rc_e, email = run_cmd(["git", "-C", str(root), "config", "user.email"])
        rc_h, hooks = run_cmd(["git", "-C", str(root), "config", "core.hooksPath"])
        identity = rc_n == 0 and name.strip() and rc_e == 0 and email.strip()
        hooked = rc_h == 0 and hooks.strip() == "scripts/hooks"
        detail = f"identity={'ok' if identity else 'MISSING'}, hooksPath={hooks.strip() or 'unset'}"
        return bool(identity and hooked), detail

    return [
        ("python-version", python_version,
         "campaign tooling needs python >= 3.11 (tomllib); run via `uv run`"),
        ("uv-present", uv_present,
         "install uv (operator action — never install unprompted from an agent session)"),
        ("umbrella-manifest", umbrella_manifest,
         "umbrella not found: set HIVEMIND_ROOT to the ai-hivemind checkout (syncthing may still be seeding)"),
        ("manifest-entry", manifest_entry,
         f"add `{REPO_NAME} = \"<absolute path to this repo>\"` to the umbrella repos.toml and re-ingest links"),
        ("hstate-invokable", hstate_invokable,
         "hive-state sibling missing or its .venv unprovisioned; check the umbrella checkout"),
        ("links-gate", links_gate,
         "corpus link graph is red — repair via the /hive-state-links skill before campaign work"),
        ("lrag-probe", lrag_probe,
         f"lrag collection `{LRAG_COLLECTION}` absent or empty; register + sync it from the machine that owns the registry (single writer)"),
        ("oracle-pin", oracle_pin,
         "re-clone or `git -C oracle/pyreason checkout <PIN>`; never build on a drifted oracle"),
        ("ledger-writable", ledger_writable,
         "docs/ledger/ missing — restore it from git; sessions bank there"),
        ("git-wiring", git_wiring,
         "set git user.name/user.email and `git config core.hooksPath scripts/hooks` in this repo"),
    ]


def run_all(checks) -> list[dict]:
    results = []
    for name, thunk, hint in checks:
        try:
            ok, detail = thunk()
        except Exception as exc:  # a crashed check is a failed check, not a crashed doctor
            ok, detail = False, f"check crashed: {exc!r}"
        results.append({"name": name, "ok": bool(ok), "detail": str(detail),
                        "hint": None if ok else hint})
    return results


def main(argv: list[str] | None = None, run_cmd=default_run_cmd,
         root: Path | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--json", action="store_true", help="emit a JSON report")
    parser.add_argument("--umbrella", type=Path, default=None,
                        help="umbrella root (default: $HIVEMIND_ROOT or ~/Projects/ai-hivemind)")
    args = parser.parse_args(argv)

    root = root or Path(__file__).resolve().parent.parent
    umbrella = args.umbrella or Path(os.environ.get("HIVEMIND_ROOT", DEFAULT_UMBRELLA))

    results = run_all(build_checks(root, umbrella, run_cmd))
    ok = all(r["ok"] for r in results)

    if args.json:
        print(json.dumps({"repo": REPO_NAME, "root": str(root),
                          "umbrella": str(umbrella), "ok": ok, "results": results},
                         indent=2))
    else:
        for r in results:
            print(f"{'PASS' if r['ok'] else 'FAIL'}  {r['name']:<18} {r['detail']}")
            if not r["ok"]:
                print(f"      hint: {r['hint']}")
        print(f"\n{'all checks passed' if ok else 'PREFLIGHT FAILED'} "
              f"({sum(r['ok'] for r in results)}/{len(results)})")

    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
