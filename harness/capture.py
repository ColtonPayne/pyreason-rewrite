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
reference (module state is observed through `get_time`). A `get_setting`
probe reads one named knob off the engine's public settings object — the
surface the engine itself mutates (reason() force-flips `atom_trace` when
interpretation-change storage is off), so a knob's live value is a compared
observation like any other. A probe carrying
`allow_raise: true` likewise records a raise as data instead of failing the
capture; a probe *without* it that raises fails the capture, which the runner
judges `error` — so an author declares allow_raise on every probe a candidate
engine could plausibly make raise, or that engine's raise wears the
harness-failure label instead of comparing as a divergence. An `output_file`
probe reads back every .txt file the engine wrote into the capture's confined
working directory (the surface `settings.output_to_file` redirects stdout
into), timestamp-canonicalized — which is why that knob is only allowed in a
case that carries this probe; a memory_profile case additionally declares
`canonicalize_peak_mb` to reduce the run-varying peak-MB number to a
placeholder (PEAK_MB_RE, rationale at the definition site). An `accessor_fingerprint` probe renders one of
the get-family accessors' returns (`get_rules`, `get_logic_program`,
`get_interpretation`) into canonical comparable data — None stays None, a
rule list becomes per-rule parse-shaped dicts, and the program/interpretation
objects reduce to presence + identity-with-the-last-reason-return flags. A
`save_rule_trace` probe calls the engine's save_rule_trace into the confined
working directory (or a named subdirectory of it) and reads back the CSV
files it wrote, timestamp-canonicalized like the output_file probe's .txt.
An `apply_input` probe applies one loader-family input (a file-taking loader,
add_closed_world_predicate, or one of the callable-registering functions —
whose callable is a committed reference function selected by name from
harness/reference_fns.py) and records the outcome either way — a raise
as the module-qualified exception type + message, an acceptance as
`{"raised": false}` with the loaded state observed by whatever probes follow —
so a case can declare that applying a given input is expected to raise and
compare the exception itself. The same ops join the multi-step form's step
ops, for arms whose loaded state only shows through a later reason step.
An `interval_probe` or `label_probe` constructs the aliased public value
types (`pyreason.interval.closed` / `pyreason.label.Label`) directly and
records a fixed pipeline of observations — construction state, the
equality/hash/containment relations, intersection results, and (intervals)
the reset transition — the direct-construction reach for types the public
API otherwise only consumes internally.

The artifact is self-describing: the case id, the full case record it ran
(`case` — echoed verbatim from the parsed case file, so an artifact can be
read, re-judged, or audited without the case file beside it; every artifact
written after the case parsed carries it, error artifacts included), engine
identity + environment fingerprint, each probe's canonical output, a digest
per probe, and per-probe wall-clock (`timing.probes_s`, measured around the
probe's execution + canonical reduction — diagnostic only, like the rest of
`timing`: it rides outside the probe map, so it is never digested and never
compared). Exit codes: 0 artifact written, 1 the case failed inside the
engine, 2 usage (unreadable or invalid case — an authoring fault, never an
engine finding; the artifact's error text says which).
"""

import argparse
import json
import os
import re
import shutil
import sys
import time
from pathlib import Path

from harness import reference_fns
from harness.compare import canonical, digest

REPO = Path(__file__).resolve().parent.parent

PROBE_KINDS = {"filter_sort_nodes", "filter_sort_edges", "rule_trace_node",
               "rule_trace_edge", "get_time", "get_setting",
               "interpretation_dict", "expect_raise", "output_file",
               "accessor_fingerprint", "save_rule_trace", "apply_input",
               "interval_probe", "label_probe"}
# Probe kinds that consume the interpretation reason() returns — a case using
# any of them must carry an inputs.reason block (or a preceding reason step).
# get_time and get_setting read module state, output_file reads the confined
# working directory, expect_raise constructs in isolation,
# accessor_fingerprint reads the get-family accessors (whose before-any-reason
# returns are themselves compared observations), and apply_input mutates
# module state without touching the interpretation; all run without one.
# save_rule_trace consumes the interpretation like the trace-view probes do.
INTERP_PROBE_KINDS = {"filter_sort_nodes", "filter_sort_edges",
                      "rule_trace_node", "rule_trace_edge",
                      "interpretation_dict", "save_rule_trace"}
# expect_raise constructs map to the pinned public constructors; query and
# threshold join rule/fact because Query/Threshold are their own surface rows
# whose acceptance branch must carry the parsed/stored state (see
# parse_fingerprint), not just that construction succeeded.
EXPECT_RAISE_CONSTRUCTS = {"rule", "fact", "query", "threshold"}
EXPECT_RAISE_CTORS = {"rule": "Rule", "fact": "Fact", "query": "Query",
                      "threshold": "Threshold"}
# A threshold construction arm carries exactly the pinned constructor's three
# parameters; quantifier_type rides JSON as a list (converted to the tuple the
# pinned docstring names) or any other JSON value for the shape-fault arms.
THRESHOLD_ARG_KEYS = {"quantifier", "quantifier_type", "thresh"}
# The get-family accessors an accessor_fingerprint probe can render. Each
# fingerprint is the accessor's return reduced to canonical data (see
# probe_accessor_fingerprint); an unknown name is an authoring fault (exit 2).
FINGERPRINT_ACCESSORS = {"rules", "logic_program", "interpretation"}
# The apply_input surface: the pinned loader-family functions a case can
# apply mid-sequence with the outcome recorded as data. File-taking ops map
# to their legal keyword args (all boolean at the pin);
# add_closed_world_predicate takes a bare string. Each file op's args carry
# exactly one of `path` (a committed repo-relative fixture, existence-checked
# like graphml_path — a typo'd happy-arm path must never bank
# FileNotFoundError as engine behavior and pass self-proof) or `missing_path`
# (a repo-relative path checked NOT to exist — the missing-file behavior arm,
# which would otherwise be impossible to declare without reopening that same
# hazard). Both spellings stay confined to the repo.
APPLY_FILE_OPS = {"add_rules_from_file": {"infer_edges", "raise_errors"},
                  "add_rule_from_csv": {"raise_errors"},
                  "add_rule_from_json": {"raise_errors"},
                  "add_fact_from_json": {"raise_errors"},
                  "add_fact_from_csv": {"raise_errors"},
                  "load_inconsistent_predicate_list": set()}
# The callable-registering functions join the apply surface with a `name`
# selecting a committed reference function (harness/reference_fns.py) — the
# only way a Python callable can ride the JSON case format. The name is
# validated against the registry here (an unknown name is an authoring fault,
# exit 2); the njit-wrapped callable is resolved inside the engine env, and
# outside the recording try, so a resolution fault fails the capture instead
# of banking as engine behavior.
REGISTRY_OPS = {"add_annotation_function", "add_head_function"}
APPLY_OPS = set(APPLY_FILE_OPS) | {"add_closed_world_predicate"} | REGISTRY_OPS
# The multi-step ops: reason/add_fact/add_rule consume an args dict; the
# reset family takes none. add_fact exists because _reason clears the fact
# globals on exit, so a resumed reason() with no fact added since raises — a
# resume case that actually reasons must be able to add one between steps.
# add_rule exists because reset_rules clears rules AND the registered
# annotation/head functions together, so pinning that a registration was
# cleared needs a rule re-added after the reset (same builder as inputs.rules
# — custom_thresholds and weights ride along). The apply_input ops
# double as step ops so a loader can run before a reason step (a fact loader's
# only observable is the reasoning that consumes it); a step op that raises
# already banks its outcome record, so the expecting-raise semantics are
# identical in both surfaces.
STEP_OPS = {"reason", "add_fact", "add_rule", "reset", "reset_rules",
            "reset_settings"} | APPLY_OPS
ARG_STEP_OPS = {"reason", "add_fact", "add_rule"} | APPLY_OPS
# reason()'s keyword surface at the pin — an unknown key is an authoring typo
# that would otherwise bank a TypeError as engine behavior and pass self-proof.
# `queries` rides as a list of query-text strings the capture turns into
# pinned Query objects at the call site (built outside the recording try in
# the steps form: a Query construction raise there would wear the reason-step
# label, so malformed query text belongs to expect_raise construct="query").
REASON_ARGS = {"timesteps", "convergence_threshold",
               "convergence_bound_threshold", "again", "restart", "queries"}
# The settings-knob surface at the pin — the 18 public properties on _Settings.
# Checked statically in validation like REASON_ARGS: a typo'd knob would
# otherwise silently set or read an attribute the engine never consults,
# testing the default and passing self-proof while pinning nothing. Static so
# the capture never depends on how an engine's settings object stores a knob
# (a property, a plain attribute — the compared thing is the public value);
# the fast-tier gate asserts this set against the AST scan of the pinned
# source, so a pin move cannot silently stale it.
SETTINGS_KNOBS = {"verbose", "output_to_file", "output_file_name",
                  "graph_attribute_parsing", "abort_on_inconsistency",
                  "memory_profile", "reverse_digraph", "atom_trace",
                  "save_graph_attributes_to_trace", "canonical", "persistent",
                  "inconsistency_check", "static_graph_facts",
                  "store_interpretation_changes", "parallel_computing",
                  "update_mode", "allow_ground_rules", "fp_version"}
# output_to_file rebinds the engine process's stdout to a timestamp-named
# file in the working directory (pyreason.py:1513-1514/:1541-1542 at the pin)
# and never restores it. It is allowed only when the case carries an
# `output_file` probe, so the redirect file is always a compared observation,
# never an unread side effect; the capture confines the file by chdir'ing
# into a fresh per-capture directory before inputs apply (see main()).
# The engine embeds a wall-clock stamp in the file name (pyreason.py:1511) —
# that stamp is run schedule, not engine behavior, so the probe canonicalizes
# it; file presence, count, the interpolated output_file_name basename, and
# the full contents all compare exactly.
OUTPUT_TS_RE = re.compile(r"_\d{8}-\d{6}\.txt$")
# save_rule_trace embeds the same reason-time wall-clock stamp in its CSV
# names (`rule_trace_{nodes,edges}_{__timestamp}.csv`, output.py:103-104 at
# the pin, stamp set at pyreason.py:1511) — the identical run-schedule
# rationale, so the save_rule_trace probe canonicalizes it identically; the
# basenames around the stamp and the full CSV contents compare exactly.
TRACE_TS_RE = re.compile(r"_\d{8}-\d{6}\.csv$")
# A save_rule_trace probe's optional folder is a single plain path segment
# created inside the capture's confined working directory — separators, '..',
# and absolute paths are refused so an engine-written trace file can never
# land outside the per-capture directory.
TRACE_FOLDER_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
# Under memory_profile the engine prints "\nProgram used {peak} MB of memory"
# (pyreason.py:1520/:1526 at the pin), and under output_to_file that line
# lands in the redirect file the output_file probe compares. The peak number
# is run-varying measurement (103.20 vs 103.53 MB across identical fresh
# processes at screening), not engine behavior — the same run-schedule
# rationale as the timestamp canonicalizations, so an output_file probe
# declaring `canonicalize_peak_mb` reduces exactly that number to '<peak-mb>'
# and compares the line's fixed text and everything around it exactly. The
# flag is per-case opt-in (AC-2's recorded-normalization contract) and legal
# only when the case turns memory_profile on: nothing else at the pin writes
# this line, so canonicalizing it anywhere else could only mask engine text.
PEAK_MB_RE = re.compile(r"^Program used -?\d+(?:\.\d+)?(?:e[+-]?\d+)? "
                        r"MB of memory$", re.M)
PEAK_MB_CANON = "Program used <peak-mb> MB of memory"


def _apply_fault(owner: str, op, args) -> str | None:
    """Shared checks for one apply_input application — the probe kind and the
    step-op spelling validate identically, so an authoring fault exits 2 in
    both case forms."""
    if op not in APPLY_OPS:
        return (f"{owner}: unknown apply op {op!r} "
                f"(one of {sorted(APPLY_OPS)})")
    if not isinstance(args, dict):
        return f"{owner}: 'args' must be an object"
    if op == "add_closed_world_predicate":
        if set(args) != {"name"} or not isinstance(args["name"], str):
            return (f"{owner}: add_closed_world_predicate takes exactly a "
                    f"string 'name' — the non-string add is silent at the pin "
                    f"and its reason-time raise carries a run-varying message, "
                    f"so it cannot bank under exact compare")
        return None
    if op in REGISTRY_OPS:
        if set(args) != {"name"} or not isinstance(args["name"], str):
            return (f"{owner}: {op} takes exactly a string 'name' selecting "
                    f"a committed reference function")
        if args["name"] not in reference_fns.REGISTRY:
            return (f"{owner}: unknown reference function {args['name']!r} "
                    f"(registry: {sorted(reference_fns.REGISTRY)}) — a typo'd "
                    f"name must never bank a resolution fault as engine "
                    f"behavior")
        return None
    path_keys = {"path", "missing_path"} & set(args)
    if len(path_keys) != 1:
        return (f"{owner}: a file-taking apply op needs exactly one of "
                f"'path' (a committed fixture) or 'missing_path' (the "
                f"missing-file arm), got {sorted(path_keys) or 'neither'}")
    unknown = set(args) - path_keys - APPLY_FILE_OPS[op]
    if unknown:
        return (f"{owner}: unknown arg(s) {sorted(unknown)} for {op} "
                f"(known: {sorted(APPLY_FILE_OPS[op])})")
    for key in APPLY_FILE_OPS[op] & set(args):
        if not isinstance(args[key], bool):
            return f"{owner}: '{key}' must be a boolean"
    key = next(iter(path_keys))
    rel = args[key]
    if not isinstance(rel, str) or not rel:
        return f"{owner}: '{key}' must be a non-empty string"
    if Path(rel).is_absolute():
        return f"{owner}: '{key}' must be repo-relative, got {rel!r}"
    if not (REPO / rel).resolve().is_relative_to(REPO):
        return (f"{owner}: '{key}' resolves outside the repo: {rel!r} — "
                f"applied inputs stay confined to committed paths")
    if key == "path" and not (REPO / rel).is_file():
        return (f"{owner}: 'path' names no committed file: {rel!r} — a "
                f"mistyped fixture would bank FileNotFoundError as engine "
                f"behavior and pass self-proof; a deliberate missing-file "
                f"arm declares 'missing_path'")
    if key == "missing_path" and (REPO / rel).exists():
        return (f"{owner}: 'missing_path' names an existing file: {rel!r} — "
                f"the case would claim a missing-file observation while "
                f"banking a load")
    return None


def _reason_args_fault(args, owner: str) -> str | None:
    """Shared checks for one reason-arg dict — inputs.reason and every reason
    step validate identically."""
    if not set(args) <= REASON_ARGS:
        return (f"{owner}: unknown reason arg(s) "
                f"{sorted(set(args) - REASON_ARGS)} (known: {sorted(REASON_ARGS)})")
    if "queries" in args:
        queries = args["queries"]
        if not isinstance(queries, list) or not all(
                isinstance(q, str) and q for q in queries):
            return (f"{owner}: 'queries' must be a list of non-empty "
                    f"query-text strings — the capture constructs the pinned "
                    f"Query objects from them")
    return None


def _threshold_spec_fault(spec, owner: str) -> str | None:
    """Shape checks for one threshold spec in a rule's custom_thresholds.

    Structural only — quantifier/quantifier_type membership is the engine's
    own validation, pinned by expect_raise construct="threshold" arms; but a
    spec here rides input application, where a raise fails the capture, so
    the shape that reaches the pinned constructor must be author-controlled.
    """
    if not isinstance(spec, dict) or set(spec) != THRESHOLD_ARG_KEYS:
        return (f"{owner}: a threshold spec is an object with exactly "
                f"{sorted(THRESHOLD_ARG_KEYS)}")
    if not isinstance(spec["quantifier"], str):
        return f"{owner}: 'quantifier' must be a string"
    qt = spec["quantifier_type"]
    if not (isinstance(qt, str) or (isinstance(qt, list)
                                    and all(isinstance(x, str) for x in qt))):
        return (f"{owner}: 'quantifier_type' must be a list of strings "
                f"(converted to the pinned tuple) or a string")
    return None


def _rule_spec_fault(spec, owner: str) -> str | None:
    """Shared checks for one rule spec — inputs.rules entries and add_rule
    step args validate identically."""
    if not isinstance(spec, dict) or "text" not in spec:
        return f"{owner}: a rule spec needs an object with 'text'"
    if "custom_thresholds" in spec:
        ct = spec["custom_thresholds"]
        if isinstance(ct, list):
            entries = [(f"{owner}: custom_thresholds[{i}]", s)
                       for i, s in enumerate(ct)]
        elif isinstance(ct, dict):
            for key in ct:
                try:
                    int(key)
                except ValueError:
                    return (f"{owner}: custom_thresholds dict keys must be "
                            f"integer clause indices (JSON strings), got "
                            f"{key!r} — the capture converts them the way the "
                            f"pinned JSON rule loader does")
            entries = [(f"{owner}: custom_thresholds[{k!r}]", s)
                       for k, s in ct.items()]
        else:
            return (f"{owner}: custom_thresholds must be a list (one per "
                    f"clause) or an object keyed by clause index — the two "
                    f"pinned accepted forms")
        for entry_owner, entry_spec in entries:
            fault = _threshold_spec_fault(entry_spec, entry_owner)
            if fault:
                return fault
    if "weights" in spec:
        weights = spec["weights"]
        if not isinstance(weights, list) or not all(
                isinstance(w, (int, float)) and not isinstance(w, bool)
                for w in weights):
            return f"{owner}: 'weights' must be a list of numbers"
    return None


def _bound_spec_fault(spec, owner: str) -> str | None:
    """Checks for one interval_probe construction spec."""
    if not isinstance(spec, dict) \
            or not {"lower", "upper"} <= set(spec) <= {"lower", "upper", "static"}:
        return (f"{owner}: an interval spec is an object with 'lower' and "
                f"'upper' (and optional 'static')")
    for key in ("lower", "upper"):
        if isinstance(spec[key], bool) or not isinstance(spec[key], (int, float)):
            return f"{owner}: {key!r} must be a number"
    if not isinstance(spec.get("static", False), bool):
        return f"{owner}: 'static' must be a boolean"
    return None


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
        if p.get("kind") == "get_setting":
            if p.get("allow_raise"):
                return (f"get_setting probe {p['id']!r} cannot carry allow_raise — "
                        f"an engine whose settings object lacks the knob is a "
                        f"missing-surface structural fault, never a comparable "
                        f"observation")
            if p.get("knob") not in SETTINGS_KNOBS:
                return (f"get_setting probe {p['id']!r}: 'knob' must name one of "
                        f"the pinned settings knobs, got {p.get('knob')!r}")
        if p.get("kind") == "output_file" and p.get("allow_raise"):
            return (f"output_file probe {p['id']!r} cannot carry allow_raise — "
                    f"it reads the capture's own confined output directory, so "
                    f"a read fault there is a harness failure, never a "
                    f"comparable engine observation")
        if p.get("kind") == "output_file" \
                and not isinstance(p.get("canonicalize_peak_mb", False), bool):
            return (f"output_file probe {p['id']!r}: 'canonicalize_peak_mb' "
                    f"must be a boolean")
        if p.get("kind") == "apply_input":
            if p.get("allow_raise"):
                return (f"apply_input probe {p['id']!r} cannot carry "
                        f"allow_raise — it records raises itself, and the "
                        f"blanket catch would bank a missing-loader binding "
                        f"fault as engine behavior")
            fault = _apply_fault(f"apply_input probe {p['id']!r}",
                                 p.get("op"), p.get("args"))
            if fault:
                return fault
        if p.get("kind") == "accessor_fingerprint" \
                and p.get("accessor") not in FINGERPRINT_ACCESSORS:
            return (f"accessor_fingerprint probe {p['id']!r}: 'accessor' must "
                    f"name one of {sorted(FINGERPRINT_ACCESSORS)}, got "
                    f"{p.get('accessor')!r}")
        if p.get("kind") == "interval_probe":
            if p.get("allow_raise"):
                return (f"interval_probe probe {p['id']!r} cannot carry "
                        f"allow_raise — its pipeline is fixed harness code "
                        f"over author-validated numeric specs, so a raise "
                        f"there is a missing-type binding fault, never a "
                        f"comparable observation")
            for field in ("make", "other"):
                fault = _bound_spec_fault(p.get(field),
                                          f"interval_probe probe {p['id']!r} "
                                          f"field {field!r}")
                if fault:
                    return fault
        if p.get("kind") == "label_probe":
            if p.get("allow_raise"):
                return (f"label_probe probe {p['id']!r} cannot carry "
                        f"allow_raise — it records the one raising relation "
                        f"itself, and a blanket catch would bank a "
                        f"missing-type binding fault as engine behavior")
            for field in ("value", "other"):
                if not isinstance(p.get(field), str):
                    return (f"label_probe probe {p['id']!r}: {field!r} must "
                            f"be a string (the pinned value class is "
                            f"string-valued; the non-string arm is a "
                            f"jit-context rejection out of this probe's "
                            f"reach)")
        if p.get("kind") == "save_rule_trace" and "folder" in p:
            folder = p["folder"]
            if not isinstance(folder, str) or not TRACE_FOLDER_RE.match(folder):
                return (f"save_rule_trace probe {p['id']!r}: 'folder' must be "
                        f"a plain path segment (no separators, no '..', not "
                        f"absolute) so the trace files stay confined to the "
                        f"per-capture directory, got {folder!r}")
        if p.get("kind") != "expect_raise":
            continue
        if p.get("allow_raise"):
            return (f"expect_raise probe {p['id']!r} cannot carry allow_raise — "
                    f"it records raises itself, and the blanket catch would bank "
                    f"a missing-constructor binding fault as engine behavior")
        if p.get("construct") not in EXPECT_RAISE_CONSTRUCTS:
            return (f"expect_raise probe {p['id']!r} needs 'construct' in "
                    f"{sorted(EXPECT_RAISE_CONSTRUCTS)}")
        if not isinstance(p.get("args"), dict):
            return f"expect_raise probe {p['id']!r} needs an 'args' dict"
        if p["construct"] == "threshold":
            if set(p["args"]) != THRESHOLD_ARG_KEYS:
                return (f"expect_raise probe {p['id']!r}: a threshold "
                        f"construction takes exactly "
                        f"{sorted(THRESHOLD_ARG_KEYS)} — the pinned "
                        f"constructor's three parameters")
        elif "text" not in p["args"]:
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
        if op == "add_rule":
            fault = _rule_spec_fault(args, f"step {step['id']!r}")
            if fault:
                return fault
        if op == "reason":
            fault = _reason_args_fault(args, f"step {step['id']!r}")
            if fault:
                return fault
        if op in APPLY_OPS:
            fault = _apply_fault(f"step {step['id']!r}", op, args)
            if fault:
                return fault
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


def _graph_fault(graph_spec) -> str | None:
    """Checks for inputs.graph — the inline form or a committed-fixture path.

    A `graphml_path` names a GraphML file committed in this repo, resolved
    against the repo root (never the caller's cwd), and is checked for
    existence here: a mistyped or uncommitted fixture is an authoring fault
    (exit 2), never an engine observation. That deliberately forecloses casing
    load_graphml's missing-file behavior through this input — a raising loader
    needs its own probe form, since inputs are applied before any probe runs
    and a raise there fails the capture.
    """
    if not isinstance(graph_spec, dict):
        return "inputs.graph must be an object"
    if "graphml_path" not in graph_spec:
        return None
    path = graph_spec["graphml_path"]
    if set(graph_spec) != {"graphml_path"}:
        return ("inputs.graph mixes graphml_path with inline keys "
                f"{sorted(set(graph_spec) - {'graphml_path'})} — the fixture "
                f"file and an inline spec are exclusive forms")
    if not isinstance(path, str) or not path:
        return "graphml_path must be a non-empty string"
    if Path(path).is_absolute():
        return f"graphml_path must be repo-relative, got {path!r}"
    if not (REPO / path).resolve().is_relative_to(REPO):
        return (f"graphml_path resolves outside the repo: {path!r} — a fixture "
                f"must be a file committed in this repo")
    if not (REPO / path).is_file():
        return f"graphml_path names no committed file: {path!r}"
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
        if isinstance(reason_args, dict):
            fault = _reason_args_fault(reason_args, "inputs.reason")
            if fault:
                return fault
    unknown_knobs = set(case["inputs"].get("settings", {})) - SETTINGS_KNOBS
    if unknown_knobs:
        return (f"unknown settings knob(s) in a case: {sorted(unknown_knobs)} "
                f"(the pinned surface has 18)")
    rules = case["inputs"].get("rules", [])
    if not isinstance(rules, list):
        return "inputs.rules must be a list of rule specs"
    for i, spec in enumerate(rules):
        fault = _rule_spec_fault(spec, f"inputs.rules[{i}]")
        if fault:
            return fault
    ipl = case["inputs"].get("ipl", [])
    if not (isinstance(ipl, list) and all(
            isinstance(pair, list) and len(pair) == 2
            and all(isinstance(name, str) for name in pair) for pair in ipl)):
        return "inputs.ipl must be a list of [pred, pred] string pairs"
    if case["inputs"].get("settings", {}).get("output_to_file") is True \
            and not any(p.get("kind") == "output_file" for p in _all_probes(case)):
        return ("settings.output_to_file=true requires an output_file probe — "
                "the redirect file the engine writes must be a compared "
                "observation, never an unread side effect")
    if any(p.get("kind") == "output_file" and p.get("canonicalize_peak_mb")
           for p in _all_probes(case)) \
            and case["inputs"].get("settings", {}).get("memory_profile") is not True:
        return ("canonicalize_peak_mb requires settings.memory_profile=true — "
                "only the profiled branch writes the peak-MB line, so "
                "canonicalizing it anywhere else could only mask engine text")
    if "graph" in case["inputs"]:
        return _graph_fault(case["inputs"]["graph"])
    return None


def _all_probes(case: dict):
    """Every probe in either case form — the top-level list or each step's."""
    if "steps" in case:
        return [p for step in case["steps"] for p in step.get("probes", [])]
    return case.get("probes", [])


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
    was parsed, not just that parsing succeeded. The query branch renders all
    four parsed fields plus the echoed text (str/repr echo query_text at the
    pin) — the silent-misparse arms bank the misparse itself. The threshold
    branch renders the three stored attributes plus to_tuple(), pinning that
    storage is verbatim (thresh is unvalidated at the pin).
    """
    if construct == "rule":
        r = obj.rule
        return {"name": r.get_rule_name(), "type": r.get_rule_type(),
                "target": r.get_target().get_value(),
                "head_variables": list(r.get_head_variables()),
                "delta": r.get_delta(), "bnd": r.get_bnd(),
                "clause_count": len(r.get_clauses())}
    if construct == "query":
        return {"pred": obj.get_predicate().get_value(),
                "component": obj.get_component(),
                "component_type": obj.get_component_type(),
                "bounds": obj.get_bounds(), "text": str(obj)}
    if construct == "threshold":
        return {"quantifier": obj.quantifier,
                "quantifier_type": obj.quantifier_type,
                "thresh": obj.thresh, "to_tuple": obj.to_tuple()}
    return {"pred": obj.pred.get_value(), "component": obj.component,
            "bound": obj.bound, "type": obj.type}


def rule_fingerprint(r) -> dict:
    """One live rule (get_rules' element type) as canonical, digestable data.

    Deeper than parse_fingerprint's rule branch on purpose: get_rules returns
    the live __rules global, and reason() replaces it with a clause-reordered
    copy when the graph has more edges than nodes (pyreason.py:1598-1606 at
    the pin) — so the clause list, in order, is part of what the accessor
    must be held to, not just its length. Bounds reduce via the compare
    layer's interval duck-typing.
    """
    return {"name": r.get_rule_name(), "type": r.get_rule_type(),
            "target": r.get_target().get_value(),
            "head_variables": list(r.get_head_variables()),
            "delta": r.get_delta(), "bnd": r.get_bnd(),
            "clauses": [[c[0], c[1].get_value(), list(c[2]), c[3], c[4]]
                        for c in r.get_clauses()]}


def probe_accessor_fingerprint(pr, interpretation, probe):
    """Render one get-family accessor's return as canonical comparable data.

    None stays None in every branch — the pinned accessors' before-load /
    after-reset returns are themselves the compared observations. The program
    and interpretation fingerprints are structural: presence plus identity
    with the interpretation the capture's most recent successful reason()
    returned (the pinned accessors return live references, pyreason.py:535/
    :546, so identity is contract, not incidental). Program.interp is the
    exact attribute get_interpretation reads at the pin (pyreason.py:546) —
    the fingerprint holds a candidate engine's program object to that same
    seam. A raise (get_interpretation with no program) propagates; the author
    declares allow_raise to bank it as data.
    """
    accessor = probe["accessor"]
    if accessor == "rules":
        rules = pr.get_rules()
        return None if rules is None else [rule_fingerprint(r) for r in rules]
    if accessor == "logic_program":
        program = pr.get_logic_program()
        if program is None:
            return None
        return {"interp_present": program.interp is not None,
                "interp_is_reason_return": program.interp is interpretation
                if program.interp is not None else None}
    interp = pr.get_interpretation()
    if interp is None:
        return None
    return {"time": interp.time,
            "is_reason_return": interp is interpretation}


def probe_save_rule_trace(pr, interpretation, probe):
    """Call the engine's save_rule_trace and read back what it wrote.

    The write target is the capture's confined working directory (main()
    chdir'd there — case_wants_output_dir covers this kind), or a named
    subdirectory of it created here first: the pinned engine hands `folder`
    straight to pandas, which refuses a non-existent directory, and that
    refusal would be an authoring artifact, not engine behavior. Omitting
    `folder` exercises the pinned default `folder='./'` (pyreason.py:1645).
    The readback is every .csv in the target, sorted, names stamp-
    canonicalized (TRACE_TS_RE), contents verbatim — the compared observation
    is the files themselves. A raise before any write (the store-off assert)
    propagates unless the author declared allow_raise.
    """
    folder = probe.get("folder")
    target = Path.cwd()
    if folder is None:
        pr.save_rule_trace(interpretation)
    else:
        target = target / folder
        target.mkdir(exist_ok=True)
        pr.save_rule_trace(interpretation, folder)
    return [{"name": TRACE_TS_RE.sub("_<timestamp>.csv", path.name),
             "content": path.read_text()}
            for path in sorted(target.glob("*.csv"))]


def resolve_registrand(op: str, args: dict):
    """Resolve a registry op's named reference function, or None for every
    other apply op. Called OUTSIDE the recording try at both apply sites —
    resolution (registry lookup + njit decoration) is harness work, so its
    failure must fail the capture, never bank as engine behavior."""
    if op in REGISTRY_OPS:
        return reference_fns.resolve(args["name"])
    return None


def call_apply_input(fn, op: str, args: dict, registrand=None) -> None:
    """Apply one loader-family input through an already-resolved engine
    callable. Both path spellings resolve against the repo root (validation
    vouched for confinement and the declared existence state); raises
    propagate to the caller, which records them as the compared outcome. A
    registry op hands the pre-resolved reference callable to the engine —
    the registration itself (arity gate or silent append) is the recorded
    outcome."""
    if op in REGISTRY_OPS:
        fn(registrand)
        return
    if op == "add_closed_world_predicate":
        fn(args["name"])
        return
    args = dict(args)
    rel = args.pop("path", None)
    if rel is None:
        rel = args.pop("missing_path")
    fn(str(REPO / rel), **args)


def probe_apply_input(pr, probe):
    """Apply the probe's input and record what happens — the expecting-raise
    probe form. A raise is the observation (module-qualified type + message,
    exact-compared unless the case records a canonicalization rationale); an
    acceptance is `{"raised": false}`, with the loaded state observed by the
    probes that follow. The getattr and registrand resolution stay outside
    the try: an engine missing the loader is a binding fault that must fail
    the capture, never a banked engine observation — the expect_raise
    convention."""
    fn = getattr(pr, probe["op"])
    registrand = resolve_registrand(probe["op"], probe["args"])
    try:
        call_apply_input(fn, probe["op"], probe["args"], registrand)
    except Exception as exc:
        return raise_record(exc)
    return {"raised": False}


def raise_record(exc: Exception) -> dict:
    """A raise reduced to comparable data: module-qualified type + message."""
    return {"raised": True,
            "type": f"{type(exc).__module__}.{type(exc).__qualname__}",
            "message": str(exc)}


def probe_expect_raise(pr, probe):
    """Construct a Rule, Fact, Query, or Threshold from the probe's args and
    record what happens.

    The output is the observation either way — an acceptance is recorded with
    its parse fingerprint, a raise with the module-qualified exception type
    and message; the compare layer holds both engines to the same outcome.
    A missing constructor is a harness/binding fault and propagates as a
    capture failure rather than wearing the engine-behavior label.
    """
    args = probe["args"]
    construct = probe["construct"]
    ctor = getattr(pr, EXPECT_RAISE_CTORS[construct])
    try:
        if construct == "rule":
            obj = ctor(args["text"], args.get("name"),
                       args.get("infer_edges", False))
        elif construct == "fact":
            obj = ctor(args["text"], args.get("name"), args.get("start", 0),
                       args.get("end", 0), args.get("static", False))
        elif construct == "query":
            obj = ctor(args["text"])
        else:
            qt = args["quantifier_type"]
            # JSON has no tuple; the documented parameter type is a 2-tuple,
            # so a list spec is handed over as one. A string rides verbatim —
            # the pinned constructor's indexing faults are the observation.
            obj = ctor(args["quantifier"],
                       tuple(qt) if isinstance(qt, list) else qt,
                       args["thresh"])
    except Exception as exc:
        return raise_record(exc)
    return {"raised": False,
            "parse": parse_fingerprint(construct, obj)}


def interval_fingerprint(iv) -> dict:
    """One interval's full observable state, including the previous-bound
    fields (they drive has_changed and the reset transition) and the pinned
    repr text (to_str/__repr__, interval.py:71-81)."""
    return {"lower": float(iv.lower), "upper": float(iv.upper),
            "static": bool(iv.is_static()),
            "prev_lower": float(iv.prev_lower),
            "prev_upper": float(iv.prev_upper),
            "repr": iv.to_str()}


def probe_interval(pr, probe):
    """Construct two intervals through the aliased public constructor
    (pyreason.interval.closed) and run the fixed observation pipeline.

    The pipeline order is part of the contract: relations and intersection
    on the freshly-constructed pair first, then the reset transition, then
    intersection again — the post-reset intersection is what pins the
    Python-proxy prev-bound seeding (interval.py:69 seeds the result's prev
    from self's CURRENT bounds; the jitted overload_method seeds from self's
    prev, interval_type.py:63 — the two-implementation divergence the board
    carries; only the proxy arm is reachable without compiling new jitted
    code, so only it is banked).
    """
    closed = pr.interval.closed
    make, other_spec = probe["make"], probe["other"]
    iv = closed(make["lower"], make["upper"], make.get("static", False))
    other = closed(other_spec["lower"], other_spec["upper"],
                   other_spec.get("static", False))
    record = {
        "constructed": interval_fingerprint(iv),
        "other": interval_fingerprint(other),
        "eq": bool(iv == other),
        "hash_eq": hash(iv) == hash(other),
        "other_in_self": bool(other in iv),
        "self_in_other": bool(iv in other),
        "intersection": interval_fingerprint(iv.intersection(other)),
        "has_changed_fresh": bool(iv.has_changed()),
    }
    iv.reset()
    record["post_reset"] = interval_fingerprint(iv)
    record["has_changed_post_reset"] = bool(iv.has_changed())
    record["post_reset_intersection"] = interval_fingerprint(
        iv.intersection(other))
    return record


def probe_label(pr, probe):
    """Construct labels through the aliased public value class
    (pyreason.label.Label) and record the value/equality/hash relations.

    Relations, not raw hash values, are the compared observations — the
    pinned contract is equality-and-hash-by-string-value (label.py:9-17),
    not any particular hash number. The one raising relation (== against a
    plain string: the pinned __eq__ calls get_value() on its argument before
    the isinstance guard) is recorded as data, keeping the probe total.
    """
    label_cls = pr.label.Label
    lab = label_cls(probe["value"])
    same = label_cls(probe["value"])
    other = label_cls(probe["other"])
    try:
        eq_plain = bool(lab == probe["value"])
    except Exception as exc:
        eq_plain = raise_record(exc)
    return {"value": lab.get_value(), "str": str(lab), "repr": repr(lab),
            "eq_same_text": bool(lab == same),
            "eq_other_text": bool(lab == other),
            "hash_eq_same_text": hash(lab) == hash(same),
            "hash_eq_other_text": hash(lab) == hash(other),
            "eq_plain_str": eq_plain}


def run_probe(pr, interpretation, probe):
    kind = probe["kind"]
    if kind == "expect_raise":
        return probe_expect_raise(pr, probe)
    if kind == "interval_probe":
        return probe_interval(pr, probe)
    if kind == "label_probe":
        return probe_label(pr, probe)
    if kind == "apply_input":
        return probe_apply_input(pr, probe)
    if kind == "accessor_fingerprint":
        return probe_accessor_fingerprint(pr, interpretation, probe)
    if kind == "save_rule_trace":
        return probe_save_rule_trace(pr, interpretation, probe)
    if kind == "get_setting":
        # However the engine stores the knob — validation already vouched for
        # the name; an engine actually missing it fails the capture.
        return getattr(pr.settings, probe["knob"])
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
    if kind == "output_file":
        # Under output_to_file the pinned engine rebinds this process's
        # sys.stdout to the redirect file and never flushes or restores it
        # (pyreason.py:1513-1514/:1541-1542) — flush first so buffered prints
        # are part of the observation, then read every .txt in the capture's
        # working directory (main() confined it to a fresh per-capture dir).
        # The wall-clock stamp in the name is canonicalized (OUTPUT_TS_RE);
        # an empty list is the compared observation that no redirect file
        # was written. Probe order matters: sys.stdout stays redirected, so
        # authors place this probe after every probe whose output it should
        # observe. With canonicalize_peak_mb declared (memory_profile cases
        # only — validation holds the pairing) the run-varying peak-MB
        # number is reduced to '<peak-mb>' (PEAK_MB_RE rationale above);
        # every other character still compares exactly.
        sys.stdout.flush()
        canon = ((lambda text: PEAK_MB_RE.sub(PEAK_MB_CANON, text))
                 if probe.get("canonicalize_peak_mb") else (lambda text: text))
        return [{"name": OUTPUT_TS_RE.sub("_<timestamp>.txt", path.name),
                 "content": canon(path.read_text())}
                for path in sorted(Path.cwd().glob("*.txt"))]
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


def build_threshold(pr, spec: dict):
    """One validated threshold spec into the pinned Threshold object. A list
    quantifier_type becomes the documented 2-tuple; only shape was validated,
    so the pinned constructor's own membership checks still run — but on the
    input-application path a reject fails the capture, so rules[] specs stay
    valid and the reject arms live in expect_raise construct="threshold"."""
    qt = spec["quantifier_type"]
    return pr.Threshold(spec["quantifier"],
                        tuple(qt) if isinstance(qt, list) else qt,
                        spec["thresh"])


def build_rule(pr, spec: dict):
    """One validated rule spec into a pinned Rule — shared by inputs.rules
    and the add_rule step op. custom_thresholds passes both pinned accepted
    forms through (the list form and the clause-index dict form, keys
    int-converted the way the pinned JSON rule loader converts them); weights
    rides as the JSON list (the pinned parser converts to ndarray)."""
    kwargs = {}
    if "custom_thresholds" in spec:
        ct = spec["custom_thresholds"]
        if isinstance(ct, list):
            kwargs["custom_thresholds"] = [build_threshold(pr, s) for s in ct]
        else:
            kwargs["custom_thresholds"] = {
                int(k): build_threshold(pr, s) for k, s in ct.items()}
    if "weights" in spec:
        kwargs["weights"] = spec["weights"]
    return pr.Rule(spec["text"], spec.get("name"),
                   spec.get("infer_edges", False), **kwargs)


def build_reason_args(pr, args: dict) -> dict:
    """reason-step/inputs.reason args with query texts turned into pinned
    Query objects. Called outside the recording try (and before the engine's
    reason), so a Query construction raise is a capture failure — malformed
    query text belongs to expect_raise construct="query", where the raise is
    the recorded observation."""
    if "queries" not in args:
        return args
    args = dict(args)
    args["queries"] = [pr.Query(text) for text in args["queries"]]
    return args


def run_step(pr, step: dict, interpretation):
    """Execute one step op; the outcome record is data either way.

    Returns (outcome, interpretation) — the interpretation advances only on a
    successful reason, so probes after a raising step observe the state the
    raise left behind, exactly what a caller holding the old reference sees.
    """
    args = step.get("args", {})
    op = step["op"]
    # Resolved/built outside the try — an engine missing the loader binding,
    # a registry resolution fault, or a Query construction raise is a
    # capture failure, never a banked outcome (probe_apply_input parity).
    apply_fn = getattr(pr, op) if op in APPLY_OPS else None
    registrand = resolve_registrand(op, args)
    if op == "reason":
        args = build_reason_args(pr, args)
    try:
        if op in APPLY_OPS:
            call_apply_input(apply_fn, op, args, registrand)
        elif op == "reason":
            interpretation = pr.reason(**args)
        elif op == "add_fact":
            add_fact_from_args(pr, args)
        elif op == "add_rule":
            pr.add_rule(build_rule(pr, args))
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
    for knob, value in settings.items():
        setattr(pr.settings, knob, value)


def case_wants_output_dir(case: dict) -> bool:
    """Whether main() must confine the capture's working directory: the case
    turns the stdout redirect on, observes the (absent) redirect file, or
    calls save_rule_trace — whose pinned default folder is the cwd."""
    return (case["inputs"].get("settings", {}).get("output_to_file") is True
            or any(p.get("kind") in ("output_file", "save_rule_trace")
                   for p in _all_probes(case)))


def fresh_output_dir(out: Path) -> Path:
    """A per-capture directory beside the artifact for engine-written files.

    Cleared on every capture — a stale redirect file from a prior run would
    otherwise bank as this run's observation."""
    outdir = out.with_suffix(".outdir")
    if outdir.exists():
        shutil.rmtree(outdir)
    outdir.mkdir(parents=True)
    return outdir


def case_registers_functions(case: dict) -> bool:
    """Whether the case applies a callable-registering op in either spelling —
    the condition for main()'s kernel-cache snapshot/restore."""
    ops = {step.get("op") for step in case.get("steps", [])}
    ops |= {p.get("op") for p in _all_probes(case)
            if p.get("kind") == "apply_input"}
    return bool(ops & REGISTRY_OPS)


def engine_kernel_cache_dir() -> Path | None:
    """The engine env's bundled kernel-cache directory, located WITHOUT
    importing (and thereby initializing) the engine — importlib.util.find_spec
    reads packaging metadata only."""
    import importlib.util
    spec = importlib.util.find_spec("pyreason")
    if spec is None or not spec.submodule_search_locations:
        return None
    return Path(list(spec.submodule_search_locations)[0]) / "cache"


def snapshot_kernel_cache(cache_dir: Path | None):
    """The bundled kernel cache's file set plus every index file's bytes.

    A capture that registers reference functions specializes the engine's
    disk-cached kernels on signatures that embed the njit dispatchers. Those
    saves are pure loss, twice over: the pickled index keys reference
    harness.reference_fns, so any later engine process WITHOUT the repo root
    on sys.path fails the index load outright (ModuleNotFoundError at
    numba's _load_index — reproduced live 2026-07-07: a plain-script screen
    run from the repo root broke, because script invocation puts the
    script's directory, not the cwd, on sys.path — and the fault is a hard
    error, not self-healing); and the entries can never be hit again anyway
    (a fresh process's resolve() creates new dispatcher objects, so the
    pickled signature never matches — observed as a new multi-MB .nbc
    overload appended per capture). Re-pointing NUMBA_CACHE_DIR cannot
    prevent the saves: the engine package's __init__ re-points the variable
    at its bundled directory before the kernels are decorated, cache
    locators bake config.CACHE_DIR in at decoration time, and the compiler
    re-reads the environment on every compilation (numba
    core/compiler.py:400) — screened live: an early override left the
    per-capture directory empty and the bundled cache poisoned. So main()
    snapshots before the engine imports and restores after the capture:
    files added during a registrand capture are removed and rewritten
    indexes restored to their prior bytes, leaving the bundled cache exactly
    as a registrand-free run would. Data files are add-only (each new
    specialization gets a fresh counter-named .nbc), so index bytes — a few
    KB each — are the only content that needs snapshotting."""
    names: set = set()
    indexes: dict = {}
    if cache_dir is None or not cache_dir.is_dir():
        return names, indexes
    for p in cache_dir.rglob("*"):
        if p.is_file():
            rel = p.relative_to(cache_dir)
            names.add(rel)
            if p.suffix == ".nbi":
                indexes[rel] = p.read_bytes()
    return names, indexes


def restore_kernel_cache(cache_dir: Path | None, names: set, indexes: dict) -> None:
    """Undo this capture's kernel-cache writes (see snapshot_kernel_cache):
    delete files that were not present at snapshot time and restore any
    index whose bytes changed. Touches only the engine env's cache
    directory — rebuildable runtime state, never the pinned oracle tree."""
    if cache_dir is None or not cache_dir.is_dir():
        return
    for p in cache_dir.rglob("*"):
        if p.is_file() and p.relative_to(cache_dir) not in names:
            p.unlink()
    for rel, data in indexes.items():
        target = cache_dir / rel
        if not target.exists() or target.read_bytes() != data:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)


def run_case(case: dict) -> dict:
    t0 = time.perf_counter()
    import pyreason as pr
    import_s = time.perf_counter() - t0

    inputs = case["inputs"]
    apply_settings(pr, inputs.get("settings", {}))

    graph_spec = inputs.get("graph")
    if graph_spec is not None:
        if "graphml_path" in graph_spec:
            # Validation vouched the committed fixture exists; resolving against
            # the repo root keeps the load independent of the caller's cwd.
            pr.load_graphml(str(REPO / graph_spec["graphml_path"]))
        else:
            pr.load_graph(build_graph(graph_spec))

    for rule in inputs.get("rules", []):
        pr.add_rule(build_rule(pr, rule))
    for fact in inputs.get("facts", []):
        add_fact_from_args(pr, fact)
    for pred_a, pred_b in inputs.get("ipl", []):
        pr.add_inconsistent_predicate(pred_a, pred_b)

    interpretation = None
    reason_s = None
    probes = {}
    # Per-probe wall-clock (execution + canonical reduction). Diagnostic only:
    # timing rides outside the probe map, so it is never digested and never
    # compared — probe timing is run schedule, not engine behavior.
    probes_s = {}

    def timed_probe(probe):
        t1 = time.perf_counter()
        value = canonical(run_probe_recorded(pr, interpretation, probe))
        probes_s[probe["id"]] = round(time.perf_counter() - t1, 3)
        return value

    timing: dict = {"import_s": round(import_s, 3)}
    if "steps" in case:
        steps_s = {}
        for step in case["steps"]:
            t1 = time.perf_counter()
            outcome, interpretation = run_step(pr, step, interpretation)
            steps_s[step["id"]] = round(time.perf_counter() - t1, 3)
            probes[step["id"]] = canonical(outcome)
            for probe in step.get("probes", []):
                probes[probe["id"]] = timed_probe(probe)
        timing["steps_s"] = steps_s
    else:
        if "reason" in inputs:
            t1 = time.perf_counter()
            interpretation = pr.reason(**build_reason_args(pr, inputs["reason"]))
            reason_s = time.perf_counter() - t1
        for probe in case["probes"]:
            probes[probe["id"]] = timed_probe(probe)
        timing["reason_s"] = None if reason_s is None else round(reason_s, 3)
    timing["probes_s"] = probes_s

    return {
        "schema": 1,
        "case_id": case["id"],
        "case": case,
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
    # Absolute before any chdir — the artifact must land where the runner
    # asked regardless of where the engine's file output is confined.
    args.out = args.out.resolve()

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
                                  "case": case,
                                  "error": f"invalid case: {fault}"})
        print(f"invalid case: {fault}", file=sys.stderr)
        return 2

    registrand_case = case_registers_functions(case)
    cache_dir, cache_names, cache_indexes = None, set(), {}
    if registrand_case:
        cache_dir = engine_kernel_cache_dir()
        cache_names, cache_indexes = snapshot_kernel_cache(cache_dir)
    if case_wants_output_dir(case):
        # The pinned redirect path is cwd-relative ("./..." at
        # pyreason.py:1514) — chdir into a fresh per-capture directory so an
        # engine-written file can only ever land beside this capture's
        # artifact, never in the repo root or outside it.
        os.chdir(fresh_output_dir(args.out))

    try:
        artifact = run_case(case)
    except Exception as exc:  # the artifact must say HOW the engine failed
        write_artifact(args.out, {"schema": 1, "case_id": case.get("id"),
                                  "case": case, "error": repr(exc)})
        print(f"capture failed: {exc!r}", file=sys.stderr)
        return 1
    finally:
        if registrand_case:
            restore_kernel_cache(cache_dir, cache_names, cache_indexes)
    write_artifact(args.out, artifact)
    return 0


if __name__ == "__main__":
    sys.exit(main())
