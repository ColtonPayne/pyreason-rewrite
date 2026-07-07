"""The settings object — 18 public knobs, each a type-validating property.

Behavior target: the pinned oracle's `_Settings` (oracle pyreason.py:43-456).
Every knob validates its type on set with the pinned TypeError text and
otherwise stores the value; `canonical` is the pinned deprecated alias of
`persistent` — both read and write one stored value. `reset()` restores the
18 pinned defaults. One descriptor class carries the validate-and-store
shape for all knobs instead of 18 hand-rolled property pairs.
"""

_BOOL_MSG = "value has to be a bool"


class _Knob:
    """One validating settings knob: isinstance-checks on set (the pinned
    strict check — an int is not a bool), stores under `store` (defaults to
    the knob's own name; `canonical` aliases the `persistent` store)."""

    def __init__(self, py_type, message=_BOOL_MSG, store=None):
        self._py_type = py_type
        self._message = message
        self._store = store

    def __set_name__(self, owner, name):
        if self._store is None:
            self._store = name

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self
        return obj._values[self._store]

    def __set__(self, obj, value):
        if not isinstance(value, self._py_type):
            raise TypeError(self._message)
        obj._values[self._store] = value


class Settings:
    """The engine's knob surface; one instance lives on each EngineState."""

    # 17 stored values — `canonical` shares the `persistent` store.
    _DEFAULTS = {
        "verbose": True,
        "output_to_file": False,
        "output_file_name": "pyreason_output",
        "graph_attribute_parsing": True,
        "abort_on_inconsistency": False,
        "memory_profile": False,
        "reverse_digraph": False,
        "atom_trace": False,
        "save_graph_attributes_to_trace": False,
        "persistent": False,
        "inconsistency_check": True,
        "static_graph_facts": True,
        "store_interpretation_changes": True,
        "parallel_computing": False,
        "update_mode": "intersection",
        "allow_ground_rules": False,
        "fp_version": False,
    }

    verbose = _Knob(bool)
    output_to_file = _Knob(bool)
    output_file_name = _Knob(str, "file_name has to be a string")
    graph_attribute_parsing = _Knob(bool)
    abort_on_inconsistency = _Knob(bool)
    memory_profile = _Knob(bool)
    reverse_digraph = _Knob(bool)
    atom_trace = _Knob(bool)
    save_graph_attributes_to_trace = _Knob(bool)
    canonical = _Knob(bool, store="persistent")  # deprecated alias of persistent
    persistent = _Knob(bool)
    inconsistency_check = _Knob(bool)
    static_graph_facts = _Knob(bool)
    store_interpretation_changes = _Knob(bool)
    parallel_computing = _Knob(bool)
    update_mode = _Knob(str, "value has to be a str")
    allow_ground_rules = _Knob(bool)
    fp_version = _Knob(bool)

    def __init__(self):
        self._values = {}
        self.reset()

    def reset(self):
        """Restore every knob to its pinned default."""
        self._values = dict(self._DEFAULTS)
