"""The query-text parser — entry point for `pyreason.Query`.

Behavior target: the pinned oracle's query parser (oracle
scripts/utils/query_parser.py), banked by the query-construct case. This
parser validates nothing by design-of-record: the pin's two silent misparses
are part of the equivalence contract and are reproduced, not repaired —
- text without parentheses truncates the predicate to `pred_comp[:-1]` and
  reads the component as `pred_comp[0:-1]` (idx is -1);
- '~pred(x):[l,u]' keeps the '~' inside the predicate name, because the
  explicit-bounds branch never strips it.
The one raising arm is a non-numeric bound (float() raises). Tightening any
of this is an AC-6 adjudication proposal, never a silent improvement.
"""

from . import interval
from .label import Label


def parse_query(query: str):
    query = query.replace(' ', '')

    if ':' in query:
        pred_comp, bounds = query.split(':')
        bounds = bounds.replace('[', '').replace(']', '')
        lower, upper = bounds.split(',')
        lower, upper = float(lower), float(upper)
    else:
        if query[0] == '~':
            pred_comp = query[1:]
            lower, upper = 0, 0
        else:
            pred_comp = query
            lower, upper = 1, 1

    bnd = interval.closed(lower, upper)

    # Split predicate and component (idx may be -1 — the pinned misparse)
    idx = pred_comp.find('(')
    pred = Label(pred_comp[:idx])
    component = pred_comp[idx + 1:-1]

    if ',' in component:
        component = tuple(component.split(','))
        comp_type = 'edge'
    else:
        comp_type = 'node'

    return pred, component, comp_type, bnd
