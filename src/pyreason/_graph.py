"""Graph loading and graph-attribute parsing over the explicit state.

Behavior target: the pinned `load_graph` path (oracle pyreason.py:589-608 +
scripts/utils/graphml_parser.py). Loading copies the caller's graph into a
fresh DiGraph and — when `graph_attribute_parsing` is on — reduces every
node/edge attribute to one graph-attribute fact plus a specific-label entry:

- a numeric (or numeric-string) value v in [0,1] becomes label `key` with
  bound [v, 1];
- a string 'l,u' with both integers in [0,1] becomes label `key` with bound
  [l, u];
- anything else becomes the valueless label `key-value` with bound [1,1].

Every graph fact is named 'graph-attribute-fact' (the engine keys its
trace-suppression on that exact name) and active at t=0 only; the
`static_graph_facts` knob rides as the facts' static flag. The unconditional
"Added N ..." print is the pinned loader's own output, kept as observable
behavior. With attribute parsing off the four products are empty — graph
structure loads, attributes leave no trace.
"""

import networkx as nx

from . import interval
from .label import Label


class _GraphFact:
    """One graph-attribute fact — the engine-facing fact record shape
    (name/component/label/bound/times/static), node and edge alike."""

    __slots__ = ("name", "component", "pred", "bound",
                 "start_time", "end_time", "static")

    def __init__(self, component, pred, bound, static):
        self.name = 'graph-attribute-fact'
        self.component = component
        self.pred = pred
        self.bound = bound
        self.start_time = 0
        self.end_time = 0
        self.static = static


def _attribute_to_label_bound(key, value):
    """One attribute (key, value) to its (label_str, lower, upper) — the
    pinned coercion ladder, comma-pair check last so it can override."""
    if (isinstance(value, (float, int)) and 1 >= value >= 0) or (
            isinstance(value, str) and value.replace('.', '').isdigit()
            and 1 >= float(value) >= 0):
        label_str = str(key)
        lower_bnd = float(value)
        upper_bnd = 1
    else:
        label_str = f'{key}-{value}'
        lower_bnd = 1
        upper_bnd = 1
    if isinstance(value, str):
        bnd_str = value.split(',')
        if len(bnd_str) == 2:
            try:
                low = int(bnd_str[0])
                up = int(bnd_str[1])
                if 1 >= low >= 0 and 1 >= up >= 0:
                    lower_bnd = low
                    upper_bnd = up
                    label_str = str(key)
            except (ValueError, TypeError):
                pass
    return label_str, lower_bnd, upper_bnd


def parse_graph_attributes(graph, static_facts):
    """Reduce the loaded graph's attributes to graph facts + specific labels."""
    facts_node = []
    facts_edge = []
    specific_node_labels = {}
    specific_edge_labels = {}
    for n in graph.nodes:
        for key, value in graph.nodes[n].items():
            label_str, lower_bnd, upper_bnd = _attribute_to_label_bound(key, value)
            specific_node_labels.setdefault(Label(label_str), []).append(n)
            facts_node.append(_GraphFact(n, Label(label_str),
                                         interval.closed(lower_bnd, upper_bnd),
                                         static_facts))
    for e in graph.edges:
        for key, value in graph.edges[e].items():
            label_str, lower_bnd, upper_bnd = _attribute_to_label_bound(key, value)
            specific_edge_labels.setdefault(Label(label_str), []).append((e[0], e[1]))
            facts_edge.append(_GraphFact((e[0], e[1]), Label(label_str),
                                         interval.closed(lower_bnd, upper_bnd),
                                         static_facts))

    # The pinned parser's own unconditional output (graphml_parser.py:93) —
    # observable under the stdout-redirect knob, so kept verbatim.
    print("Added ", len(facts_node), "graph-attribute node facts and ",
          len(facts_edge), "graph_attribute edge facts.")
    return facts_node, facts_edge, specific_node_labels, specific_edge_labels


def load_graph(state, graph) -> None:
    """Load a networkx DiGraph into the state — copy, then attribute-parse."""
    state.graph = nx.DiGraph(graph)
    if state.settings.graph_attribute_parsing:
        (state.graph_facts_node, state.graph_facts_edge,
         state.specific_graph_node_labels, state.specific_graph_edge_labels) = \
            parse_graph_attributes(state.graph, state.settings.static_graph_facts)
    else:
        state.graph_facts_node = []
        state.graph_facts_edge = []
        state.specific_graph_node_labels = {}
        state.specific_graph_edge_labels = {}
