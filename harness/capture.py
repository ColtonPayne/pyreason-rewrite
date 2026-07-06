"""Run one case inside one engine environment and emit a result artifact.

Executed as `<engine-python> -m harness.capture <case.json> <out.json>` from the
repo root — the engine (pyreason) is imported from whatever environment that
interpreter carries; this module itself uses only the stdlib plus
`harness.compare` (also stdlib-only). Each invocation is a bare process: the
engine's module-global state is born and dies with it.

The artifact is self-describing: the case id, engine identity + environment
fingerprint, each probe's canonical output, and a digest per probe. Exit codes:
0 artifact written, 1 the case failed inside the engine, 2 usage (unreadable or
invalid case — an authoring fault, never an engine finding; the artifact's
error text says which).
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

from harness.compare import canonical, digest

PROBE_KINDS = {"filter_sort_nodes", "filter_sort_edges", "rule_trace_node",
               "rule_trace_edge", "get_time", "interpretation_dict"}
# output_to_file rebinds the engine process's stdout and writes a
# timestamp-named file the harness never compares — rejected until file output
# becomes a first-class probe.
FORBIDDEN_SETTINGS = {"output_to_file"}


def validate_case(case: dict) -> str | None:
    """The case-schema guard: returns a one-line fault, or None when valid.

    Runs before the engine is imported, so an authoring fault can never wear
    the engine-failure label (exit 1); it exits 2 instead.
    """
    if not isinstance(case.get("id"), str) or not case["id"]:
        return "case has no string 'id'"
    probes = case.get("probes")
    if not isinstance(probes, list) or not probes:
        return "case declares no probes — a probe-less case proves nothing"
    ids = [p.get("id") for p in probes]
    if len(set(ids)) != len(ids) or not all(ids):
        return "probe ids must be present and unique"
    unknown = {p.get("kind") for p in probes} - PROBE_KINDS
    if unknown:
        return f"unknown probe kind(s): {sorted(unknown)}"
    if not isinstance(case.get("inputs"), dict):
        return "case has no 'inputs' object"
    forbidden = FORBIDDEN_SETTINGS & set(case["inputs"].get("settings", {}))
    if forbidden:
        return f"forbidden settings knob(s) in a case: {sorted(forbidden)}"
    return None


def build_graph(spec):
    import networkx as nx

    g = nx.DiGraph()
    for node in spec.get("nodes", []):
        if isinstance(node, list):
            g.add_node(node[0], **node[1])
        else:
            g.add_node(node)
    for edge in spec.get("edges", []):
        attrs = edge[2] if len(edge) > 2 else {}
        g.add_edge(edge[0], edge[1], **attrs)
    return g


def dataframe_to_plain(df):
    """A DataFrame as {columns, rows} — row order preserved (order is contract)."""
    return {
        "columns": [str(c) for c in df.columns],
        "rows": [list(row) for row in df.itertuples(index=False, name=None)],
    }


def run_probe(pr, interpretation, probe):
    kind = probe["kind"]
    if kind == "filter_sort_nodes":
        frames = pr.filter_and_sort_nodes(interpretation, probe["labels"])
        return [dataframe_to_plain(df) for df in frames]
    if kind == "filter_sort_edges":
        frames = pr.filter_and_sort_edges(interpretation, probe["labels"])
        return [dataframe_to_plain(df) for df in frames]
    if kind == "rule_trace_node":
        return dataframe_to_plain(pr.get_rule_trace(interpretation)[0])
    if kind == "rule_trace_edge":
        return dataframe_to_plain(pr.get_rule_trace(interpretation)[1])
    if kind == "get_time":
        return pr.get_time()
    if kind == "interpretation_dict":
        return interpretation.get_dict()
    raise ValueError(f"unknown probe kind: {kind}")


def apply_settings(pr, settings: dict):
    """Set each knob, refusing a name the engine's settings object doesn't own —
    a typo silently testing the default is a false pass against the case's intent."""
    for knob, value in settings.items():
        if not isinstance(getattr(type(pr.settings), knob, None), property):
            raise ValueError(f"unknown settings knob: {knob!r}")
        setattr(pr.settings, knob, value)


def run_case(case: dict) -> dict:
    t0 = time.perf_counter()
    import pyreason as pr
    import_s = time.perf_counter() - t0

    inputs = case["inputs"]
    apply_settings(pr, inputs.get("settings", {}))

    graph_spec = inputs.get("graph")
    if graph_spec is not None:
        if "graphml" in graph_spec:
            pr.load_graphml(graph_spec["graphml"])
        else:
            pr.load_graph(build_graph(graph_spec))

    for rule in inputs.get("rules", []):
        pr.add_rule(pr.Rule(rule["text"], rule.get("name"),
                            rule.get("infer_edges", False)))
    for fact in inputs.get("facts", []):
        pr.add_fact(pr.Fact(fact["text"], fact.get("name"),
                            fact.get("start", 0), fact.get("end", 0),
                            fact.get("static", False)))

    t1 = time.perf_counter()
    interpretation = pr.reason(**inputs.get("reason", {}))
    reason_s = time.perf_counter() - t1

    probes = {}
    for probe in case["probes"]:
        probes[probe["id"]] = canonical(run_probe(pr, interpretation, probe))

    return {
        "schema": 1,
        "case_id": case["id"],
        "engine": {
            "pyreason": str(getattr(pr, "__version__", "unknown")),
            "python": sys.version.split()[0],
            "platform": sys.platform,
            "executable": sys.executable,
        },
        "env": {"PYTHONHASHSEED": os.environ.get("PYTHONHASHSEED")},
        "probes": probes,
        "digests": {pid: digest(value) for pid, value in probes.items()},
        "timing": {"import_s": round(import_s, 3), "reason_s": round(reason_s, 3)},
    }


def write_artifact(out: Path, payload: dict) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, sort_keys=True))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="capture one case in this engine env")
    parser.add_argument("case", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args(argv)

    try:
        case = json.loads(args.case.read_text())
    except (OSError, ValueError) as exc:
        write_artifact(args.out, {"schema": 1, "case_id": None,
                                  "error": f"unreadable case file: {exc!r}"})
        print(f"unreadable case file: {exc!r}", file=sys.stderr)
        return 2
    fault = validate_case(case)
    if fault:
        write_artifact(args.out, {"schema": 1, "case_id": case.get("id"),
                                  "error": f"invalid case: {fault}"})
        print(f"invalid case: {fault}", file=sys.stderr)
        return 2

    try:
        artifact = run_case(case)
    except Exception as exc:  # the artifact must say HOW the engine failed
        write_artifact(args.out, {"schema": 1, "case_id": case.get("id"),
                                  "error": repr(exc)})
        print(f"capture failed: {exc!r}", file=sys.stderr)
        return 1
    write_artifact(args.out, artifact)
    return 0


if __name__ == "__main__":
    sys.exit(main())
