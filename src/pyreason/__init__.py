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

from . import interval, label
from ._settings import Settings
from ._state import EngineState
from . import _loaders, _state
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
