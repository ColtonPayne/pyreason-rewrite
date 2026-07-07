"""pyreason — the campaign rewrite's module-global API facade.

Equivalence target: the pinned oracle API module (oracle
pyreason/pyreason.py at e1a94af3, v3.6.0). The facade exists because the
pinned public surface is module-global (`import pyreason as pr; pr.add_rule(...)`),
and the equivalence harness drives exactly that surface; the engine itself
is NOT module-global — every function here delegates to pure functions over
one explicit `EngineState` (see _state.py), so all cross-call state lives in
one named, resettable object.

Only the surface the committed equivalence cases and seam tests consume
exists here; further pinned functions land with the packets whose cases
consume them. The value types (`interval.closed`, `label.Label`) are reached
through their submodules, mirroring the pinned aliased-submodule imports.
"""

from typing import List, Tuple

import networkx as nx

from . import interval, label
from ._settings import Settings
from ._state import EngineState
from . import _graph, _loaders, _output, _state
from .fact import Fact
from .query import Query
from .rule import Rule
from .threshold import Threshold

__version__ = '0.1.0.dev0'

# The one module-global engine state the facade wraps. A fresh process is a
# fresh engine; embedders that need more than one engine hold EngineStates
# of their own and call the _state/_loaders functions directly.
_state_obj = EngineState()

settings: Settings = _state_obj.settings


def get_rules():
    """The live rule list, or None before any rule was added."""
    return _state_obj.rules


def get_logic_program():
    """The logic program object, or None before reason() first builds one."""
    return _state_obj.program


def get_interpretation():
    """The current interpretation.

    Raises the pinned bare Exception when no program exists yet — the
    before-any-reason arm the accessors-fresh-state case banks.
    """
    if _state_obj.program is None:
        raise Exception('No interpretation found. Please run `pr.reason()` first')
    return _state_obj.program.interp


def get_time() -> int:
    """The current time: interpretation time + 1, or 0 when no
    interpretation exists (the pinned swallow of get_interpretation's raise)."""
    try:
        i = get_interpretation()
    except Exception:
        return 0
    return i.time + 1


def reset() -> None:
    """Clear the loaded facts, graph, and rules (the pinned partial clear:
    settings, IPL, clause maps, and graph-parse products survive; a live
    program is left with its interpretation nulled, not dropped)."""
    _state.reset(_state_obj)


def reset_rules() -> None:
    """Clear the rules and the registered annotation/head functions; facts,
    graph, settings, and any live interpretation stay."""
    _state.reset_rules(_state_obj)


def reset_settings() -> None:
    """Restore every settings knob to its default."""
    _state_obj.settings.reset()


def add_rule(pr_rule: Rule) -> None:
    """Add a constructed Rule to the program."""
    _state.add_rule(_state_obj, pr_rule)


def add_fact(pyreason_fact: Fact) -> None:
    """Add a constructed Fact to the program."""
    _state.add_fact(_state_obj, pyreason_fact)


def add_rules_from_file(file_path: str, infer_edges: bool = False,
                        raise_errors: bool = False) -> None:
    """Add rules from a text file — one rule per non-empty non-# line;
    raise_errors=False warns and skips invalid lines."""
    _loaders.add_rules_from_file(_state_obj, file_path, infer_edges, raise_errors)


def add_rule_from_csv(csv_path: str, raise_errors: bool = True) -> None:
    """Load rules from a CSV file of `rule_text, name, infer_edges,
    set_static` rows; raise_errors=False warns and skips invalid rows."""
    _loaders.add_rule_from_csv(_state_obj, csv_path, raise_errors)


def add_rule_from_json(json_path: str, raise_errors: bool = True) -> None:
    """Load rules from a JSON array of rule objects; raise_errors=False
    warns and skips invalid items."""
    _loaders.add_rule_from_json(_state_obj, json_path, raise_errors)


def add_fact_from_json(json_path: str, raise_errors=True) -> None:
    """Load facts from a JSON array of fact objects; raise_errors=False
    warns and skips invalid items."""
    _loaders.add_fact_from_json(_state_obj, json_path, raise_errors)


def add_fact_from_csv(csv_path: str, raise_errors=True) -> None:
    """Load facts from a CSV file of `fact_text, name, start_time, end_time,
    static` rows; raise_errors=False warns and skips invalid rows."""
    _loaders.add_fact_from_csv(_state_obj, csv_path, raise_errors)


def load_graphml(path: str) -> None:
    """Load a GraphML file into the engine (edges reversed when
    reverse_digraph is on — read at load time, unlike load_graph; attributes
    parsed into graph facts under the graph_attribute_parsing knob)."""
    _graph.load_graphml(_state_obj, path)


def load_graph(graph: nx.DiGraph) -> None:
    """Load a networkx DiGraph into the engine (copied; attributes parsed
    into graph facts under the graph_attribute_parsing knob)."""
    _graph.load_graph(_state_obj, graph)


def add_inconsistent_predicate(pred1: str, pred2: str) -> None:
    """Add an inconsistent predicate pair to the IPL."""
    _state.add_inconsistent_predicate(_state_obj, pred1, pred2)


def add_annotation_function(function) -> None:
    """Register an annotation function rules can name in their heads; only
    the 2-arg and 6-arg signatures are accepted (TypeError otherwise)."""
    _state.add_annotation_function(_state_obj, function)


def add_head_function(function) -> None:
    """Register a head function rules can call around a head variable."""
    _state.add_head_function(_state_obj, function)


def add_closed_world_predicate(predicate_name: str) -> None:
    """Treat the named predicate's unknown ([0,1] or absent) bounds as [0,0]
    during rule satisfaction checks."""
    _state.add_closed_world_predicate(_state_obj, predicate_name)


def reason(timesteps: int = -1, convergence_threshold: int = -1,
           convergence_bound_threshold: float = -1, queries: List[Query] = None,
           again: bool = False, restart: bool = True):
    """Run the reasoner over the loaded graph, rules, and facts; returns the
    final interpretation. timesteps=-1 runs to convergence — perfect
    convergence when both thresholds are defaulted, delta-interpretation
    under convergence_threshold, delta-bound under
    convergence_bound_threshold (which dominates)."""
    return _state.reason(_state_obj, timesteps, convergence_threshold,
                         convergence_bound_threshold, queries, again, restart)


def get_rule_trace(interpretation) -> Tuple[_output.Frame, _output.Frame]:
    """The change trace as (node frame, edge frame) — every stored change,
    with per-clause ground atoms when atom_trace was on."""
    assert settings.store_interpretation_changes, 'store interpretation changes setting is off, turn on to save rule trace'
    return _output.get_rule_trace(interpretation, _state_obj.clause_maps)


def filter_and_sort_nodes(interpretation, labels: List[str],
                          bound: interval.Interval = None,
                          sort_by: str = 'lower', descending: bool = True):
    """Per-timestep frames of the node changes carrying the given labels,
    filtered to `bound` and sorted by a bound endpoint."""
    assert settings.store_interpretation_changes, 'store interpretation changes setting is off, turn on to filter and sort nodes'
    return _output.filter_and_sort_nodes(interpretation, labels, bound,
                                         sort_by, descending)


def filter_and_sort_edges(interpretation, labels: List[str],
                          bound: interval.Interval = None,
                          sort_by: str = 'lower', descending: bool = True):
    """Per-timestep frames of the edge changes carrying the given labels,
    filtered to `bound` and sorted by a bound endpoint."""
    assert settings.store_interpretation_changes, 'store interpretation changes setting is off, turn on to filter and sort edges'
    return _output.filter_and_sort_edges(interpretation, labels, bound,
                                         sort_by, descending)
