"""Run one case inside one engine environment and emit a result artifact.

Executed as `<engine-python> -m harness.capture <case.json> <out.json>` from the
repo root — the engine (pyreason) is imported from whatever environment that
interpreter carries; this module itself uses only the stdlib plus
`harness.compare` (also stdlib-only). Each invocation is a bare process: the
engine's module-global state is born and dies with it.

A case takes one of two forms. The one-step form runs an optional single
`inputs.reason` block, then its top-level `probes`. The multi-step form
declares `steps` instead: an ordered list of ops (`reason`, `add_fact`,
`reset`, `reset_rules`, `reset_settings`), each with an id and an optional
probe list run after the op. Every step banks an outcome record under its id —
`{"raised": false}` or the module-qualified exception + message — so an op that
raises is a compared observation, never a capture failure. Interpretation-
consuming probes read the object returned by the most recent successful
`reason` step; after a `reset` that is deliberately the caller's stale
reference (module state is observed through `get_time`). A probe carrying
`allow_raise: true` likewise records a raise as data instead of failing the
capture; a probe *without* it that raises fails the capture, which the runner
judges `error` — so an author declares allow_raise on every probe a candidate
engine could plausibly make raise, or that engine's raise wears the
harness-failure label instead of comparing as a divergence.

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
               "rule_trace_edge", "get_time", "interpretation_dict",
               "expect_raise"}
# Probe kinds that consume the interpretation reason() returns — a case using
# any of them must carry an inputs.reason block. get_time reads module state
# and expect_raise constructs in isolation; both run without one.
INTERP_PROBE_KINDS = {"filter_sort_nodes", "filter_sort_edges",
                      "rule_trace_node", "rule_trace_edge",
                      "interpretation_dict"}
EXPECT_RAISE_CONSTRUCTS = {"rule", "fact"}
# The multi-step ops: reason/add_fact consume an args dict; the reset family
# takes none. add_fact exists because _reason clears the fact globals on exit,
# so a resumed reason() with no fact added since raises — a resume case that
# actually reasons must be able to add one between steps.
STEP_OPS = {"reason", "add_fact", "reset", "reset_rules", "reset_settings"}
ARG_STEP_OPS = {"reason", "add_fact"}
# reason()'s keyword surface at the pin — an unknown key is an authoring typo
# that would otherwise bank a TypeError as engine behavior and pass self-proof.
# `queries` joins when the harness can construct Query objects from case JSON.
REASON_ARGS = {"timesteps", "convergence_threshold",
               "convergence_bound_threshold", "again", "restart"}
# output_to_file rebinds the engine process's stdout and writes a
# timestamp-named file the harness never compares — rejected until file output
# becomes a first-class probe.
FORBIDDEN_SETTINGS = {"output_to_file"}


def _probe_list_fault(probes: list, owner: str) -> str | None:
    """Shared per-probe checks for the top-level list and each step's list."""
    unknown = {p.get("kind") for p in probes} - PROBE_KINDS
    if unknown:
        return f"unknown probe kind(s) in {owner}: {sorted(unknown)}"
    for p in probes:
        if not isinstance(p.get("id"), str) or not p["id"]:
            return f"{owner}: probe ids must be present strings"
        if not isinstance(p.get("allow_raise", False), bool):
            return f"probe {p['id']!r}: 'allow_raise' must be a boolean"
        if p.get("kind") != "expect_raise":
            continue
        if p.get("allow_raise"):
            return (f"expect_raise probe {p['id']!r} cannot carry allow_raise — "
                    f"it records raises itself, and the blanket catch would bank "
                    f"a missing-constructor binding fault as engine behavior")
        if p.get("construct") not in EXPECT_RAISE_CONSTRUCTS:
            return (f"expect_raise probe {p['id']!r} needs 'construct' in "
                    f"{sorted(EXPECT_RAISE_CONSTRUCTS)}")
        if not isinstance(p.get("args"), dict) or "text" not in p["args"]:
            return f"expect_raise probe {p['id']!r} needs an 'args' dict with 'text'"
    return None


def _steps_fault(case: dict, steps) -> str | None:
    """Schema checks for the multi-step form; ids are unique case-wide because
    step outcomes and probe outputs share the artifact's one probe map."""
    if "probes" in case:
        return "a steps case carries every probe inside its steps, not at top level"
    if "reason" in case["inputs"]:
        return "steps and inputs.reason are mutually exclusive — inputs.reason is the one-step form"
    if not isinstance(steps, list) or not steps:
        return "steps must be a non-empty list"
    ids = []
    reason_seen = False
    for i, step in enumerate(steps):
        if not isinstance(step, dict) or not isinstance(step.get("id"), str) \
                or not step["id"]:
            return f"step {i} must be an object with a string 'id'"
        op = step.get("op")
        if op not in STEP_OPS:
            return f"step {step['id']!r}: unknown op {op!r} (one of {sorted(STEP_OPS)})"
        args = step.get("args", {})
        if not isinstance(args, dict):
            return f"step {step['id']!r}: 'args' must be an object"
        if op == "add_fact" and "text" not in args:
            return f"step {step['id']!r}: add_fact needs an 'args' dict with 'text'"
        if op == "reason" and not set(args) <= REASON_ARGS:
            return (f"step {step['id']!r}: unknown reason arg(s) "
                    f"{sorted(set(args) - REASON_ARGS)} (known: {sorted(REASON_ARGS)})")
        if op not in ARG_STEP_OPS and args:
            return f"step {step['id']!r}: op {op!r} takes no args"
        if not isinstance(step.get("outcome_only", False), bool):
            return f"step {step['id']!r}: 'outcome_only' must be a boolean"
        probes = step.get("probes", [])
        if not isinstance(probes, list):
            return f"step {step['id']!r}: 'probes' must be a list"
        if op == "reason" and not probes and not step.get("outcome_only"):
            return (f"step {step['id']!r}: a reason step with no probes banks "
                    f"only {{'raised': false}} on success — declare probes that "
                    f"observe its result, or mark it 'outcome_only': true when "
                    f"the outcome record alone is the signal")
        fault = _probe_list_fault(probes, f"step {step['id']!r}")
        if fault:
            return fault
        reason_seen = reason_seen or op == "reason"
        for p in probes:
            if p["kind"] in INTERP_PROBE_KINDS and not reason_seen:
                return (f"probe {p['id']!r} consumes the interpretation but no "
                        f"reason step precedes it")
        ids.append(step["id"])
        ids.extend(p["id"] for p in probes)
    if len(set(ids)) != len(ids):
        return "step and probe ids must be unique across the case"
    return None


def validate_case(case: dict) -> str | None:
    """The case-schema guard: returns a one-line fault, or None when valid.

    Runs before the engine is imported, so an authoring fault can never wear
    the engine-failure label (exit 1); it exits 2 instead.
    """
    if not isinstance(case.get("id"), str) or not case["id"]:
        return "case has no string 'id'"
    if not isinstance(case.get("inputs"), dict):
        return "case has no 'inputs' object"
    if "steps" in case:
        fault = _steps_fault(case, case["steps"])
        if fault:
            return fault
    else:
        probes = case.get("probes")
        if not isinstance(probes, list) or not probes:
            return "case declares no probes — a probe-less case proves nothing"
        ids = [p.get("id") for p in probes]
        if len(set(ids)) != len(ids) or not all(ids):
            return "probe ids must be present and unique"
        fault = _probe_list_fault(probes, "probes")
        if fault:
            return fault
        interp_probes = [p["id"] for p in probes if p.get("kind") in INTERP_PROBE_KINDS]
        if interp_probes and "reason" not in case["inputs"]:
            return (f"probe(s) {interp_probes} consume the interpretation but the "
                    f"case has no inputs.reason block")
        reason_args = case["inputs"].get("reason", {})
        if isinstance(reason_args, dict) and not set(reason_args) <= REASON_ARGS:
            return (f"unknown reason arg(s) "
                    f"{sorted(set(reason_args) - REASON_ARGS)} in inputs.reason "
                    f"(known: {sorted(REASON_ARGS)})")
    ipl = case["inputs"].get("ipl", [])
    if not (isinstance(ipl, list) and all(
            isinstance(pair, list) and len(pair) == 2
            and all(isinstance(name, str) for name in pair) for pair in ipl)):
        return "inputs.ipl must be a list of [pred, pred] string pairs"
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


def parse_fingerprint(construct: str, obj) -> dict:
    """Reduce an accepted construction to the parse outcome it embodies.

    A bare "accepted" would let two engines that accept the same text into
    different parses compare equal — the acceptance branch must carry what
    was parsed, not just that parsing succeeded.
    """
    if construct == "rule":
        r = obj.rule
        return {"name": r.get_rule_name(), "type": r.get_rule_type(),
                "target": r.get_target().get_value(),
                "head_variables": list(r.get_head_variables()),
                "delta": r.get_delta(), "bnd": r.get_bnd(),
                "clause_count": len(r.get_clauses())}
    return {"pred": obj.pred.get_value(), "component": obj.component,
            "bound": obj.bound, "type": obj.type}


def raise_record(exc: Exception) -> dict:
    """A raise reduced to comparable data: module-qualified type + message."""
    return {"raised": True,
            "type": f"{type(exc).__module__}.{type(exc).__qualname__}",
            "message": str(exc)}


def probe_expect_raise(pr, probe):
    """Construct a Rule or Fact from the probe's args and record what happens.

    The output is the observation either way — an acceptance is recorded with
    its parse fingerprint, a raise with the module-qualified exception type
    and message; the compare layer holds both engines to the same outcome.
    A missing constructor is a harness/binding fault and propagates as a
    capture failure rather than wearing the engine-behavior label.
    """
    args = probe["args"]
    ctor = getattr(pr, "Rule" if probe["construct"] == "rule" else "Fact")
    try:
        if probe["construct"] == "rule":
            obj = ctor(args["text"], args.get("name"),
                       args.get("infer_edges", False))
        else:
            obj = ctor(args["text"], args.get("name"), args.get("start", 0),
                       args.get("end", 0), args.get("static", False))
    except Exception as exc:
        return raise_record(exc)
    return {"raised": False,
            "parse": parse_fingerprint(probe["construct"], obj)}


def run_probe(pr, interpretation, probe):
    kind = probe["kind"]
    if kind == "expect_raise":
        return probe_expect_raise(pr, probe)
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


def run_probe_recorded(pr, interpretation, probe):
    """run_probe, with a declared-raise escape hatch.

    Without allow_raise a probe exception is a capture failure (exit 1) — the
    default, so a typo'd probe cannot silently bank an exception as engine
    behavior. With it, the raise is the observation (wrapped either way so a
    raise record and a bare value can never be confused)."""
    if not probe.get("allow_raise", False):
        return run_probe(pr, interpretation, probe)
    try:
        value = run_probe(pr, interpretation, probe)
    except Exception as exc:
        return raise_record(exc)
    return {"raised": False, "value": value}


def add_fact_from_args(pr, args: dict):
    pr.add_fact(pr.Fact(args["text"], args.get("name"), args.get("start", 0),
                        args.get("end", 0), args.get("static", False)))


def run_step(pr, step: dict, interpretation):
    """Execute one step op; the outcome record is data either way.

    Returns (outcome, interpretation) — the interpretation advances only on a
    successful reason, so probes after a raising step observe the state the
    raise left behind, exactly what a caller holding the old reference sees.
    """
    args = step.get("args", {})
    op = step["op"]
    try:
        if op == "reason":
            interpretation = pr.reason(**args)
        elif op == "add_fact":
            add_fact_from_args(pr, args)
        elif op == "reset":
            pr.reset()
        elif op == "reset_rules":
            pr.reset_rules()
        else:
            pr.reset_settings()
    except Exception as exc:
        return raise_record(exc), interpretation
    return {"raised": False}, interpretation


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
        add_fact_from_args(pr, fact)
    for pred_a, pred_b in inputs.get("ipl", []):
        pr.add_inconsistent_predicate(pred_a, pred_b)

    interpretation = None
    reason_s = None
    probes = {}
    timing: dict = {"import_s": round(import_s, 3)}
    if "steps" in case:
        steps_s = {}
        for step in case["steps"]:
            t1 = time.perf_counter()
            outcome, interpretation = run_step(pr, step, interpretation)
            steps_s[step["id"]] = round(time.perf_counter() - t1, 3)
            probes[step["id"]] = canonical(outcome)
            for probe in step.get("probes", []):
                probes[probe["id"]] = canonical(
                    run_probe_recorded(pr, interpretation, probe))
        timing["steps_s"] = steps_s
    else:
        if "reason" in inputs:
            t1 = time.perf_counter()
            interpretation = pr.reason(**inputs["reason"])
            reason_s = time.perf_counter() - t1
        for probe in case["probes"]:
            probes[probe["id"]] = canonical(
                run_probe_recorded(pr, interpretation, probe))
        timing["reason_s"] = None if reason_s is None else round(reason_s, 3)

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
        "timing": timing,
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
