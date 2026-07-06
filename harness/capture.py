"""Run one case inside one engine environment and emit a result artifact.

Executed as `<engine-python> -m harness.capture <case.json> <out.json>` from the
repo root — the engine (pyreason) is imported from whatever environment that
interpreter carries; this module itself uses only the stdlib plus
`harness.compare` (also stdlib-only). Each invocation is a bare process: the
engine's module-global state is born and dies with it.

The artifact is self-describing: the case id, engine identity + environment
fingerprint, each probe's canonical output, and a digest per probe. Exit codes:
0 artifact written, 1 the case failed inside the engine, 2 usage.
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

from harness.compare import canonical, digest


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
        return interpretation.get_interpretation_dict()
    raise ValueError(f"unknown probe kind: {kind}")


def run_case(case: dict) -> dict:
    t0 = time.perf_counter()
    import pyreason as pr
    import_s = time.perf_counter() - t0

    inputs = case["inputs"]
    for knob, value in inputs.get("settings", {}).items():
        setattr(pr.settings, knob, value)

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


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("case", type=Path)
    parser.add_argument("out", type=Path)
    args = parser.parse_args(argv)

    case = json.loads(args.case.read_text())
    try:
        artifact = run_case(case)
    except Exception as exc:  # the artifact must say HOW the engine failed
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(
            {"schema": 1, "case_id": case.get("id"), "error": repr(exc)}, indent=2))
        print(f"capture failed: {exc!r}", file=sys.stderr)
        return 1
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(artifact, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
