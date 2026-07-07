"""Trace and filter views over a reasoned interpretation.

Behavior target: the pinned Output/Filter pair (oracle scripts/utils/
output.py + filter.py). The pinned implementations render through pandas
DataFrames; this environment carries no pandas, so views return `Frame` — a
value object exposing exactly the DataFrame surface the equivalence harness
consumes (`columns`, `itertuples(index=False, name=None)`, `empty`) with
identical cell values, row order, and ragged-row None padding. Cell-for-cell
equality with the pinned frames is what the banked artifacts compare.
"""

import csv
import os
import pathlib

from . import interval


class Frame:
    """A fixed table: column names + rows, DataFrame-shaped where consumed."""

    def __init__(self, columns, rows):
        self.columns = list(columns)
        self._rows = [list(r) for r in rows]

    def itertuples(self, index=True, name='Pandas'):
        # The harness calls itertuples(index=False, name=None): bare row
        # tuples. The index/name arguments only exist for signature parity.
        for i, row in enumerate(self._rows):
            if index:
                yield tuple([i] + row)
            else:
                yield tuple(row)

    @property
    def empty(self):
        return not self._rows


_TRACE_HEADER_NODE = ['Time', 'Fixed-Point-Operation', 'Node', 'Label',
                      'Old Bound', 'New Bound', 'Occurred Due To', 'Consistent',
                      'Triggered By', 'Inconsistency Message']
_TRACE_HEADER_EDGE = ['Time', 'Fixed-Point-Operation', 'Edge', 'Label',
                      'Old Bound', 'New Bound', 'Occurred Due To', 'Consistent',
                      'Triggered By', 'Inconsistency Message']
# The fixed columns before the per-clause tail (output.py:93)
_CLAUSE_OFFSET = 10


def _trace_frame(trace, trace_atoms, atom_trace, header_base, clause_map):
    """One trace list into its Frame (output.py:12-97).

    Row shape: the 9-tuple's fields, Old Bound/Occurred Due To as '-'
    placeholders unless atom_trace banked the real values, then one column
    per clause holding that clause's qualified nodes OR edges. Ragged rows
    (fact rows, rules with fewer clauses) pad with None — and when a clause
    map exists, each rule row's clause tail is rewritten back into the
    author's original clause order.
    """
    header = list(header_base)
    data = []
    max_j = -1
    for i, r in enumerate(trace):
        row = [r[0], r[1], r[2], r[3].get_value(), '-', r[4].to_str(), '-',
               r[5], r[6], r[8]]
        # With atom_trace off the stored name still names the change source
        if not atom_trace and r[7] != '':
            row[6] = r[7]
        if atom_trace:
            qn, qe, old_bnd, name = trace_atoms[i]
            row[4] = old_bnd.to_str()
            row[6] = name
            for j in range(len(qn)):
                max_j = max(j, max_j)
                if len(qe[j]) == 0:
                    row.append(list(qn[j]))
                elif len(qn[j]) == 0:
                    row.append(list(qe[j]))
        data.append(row)

    if atom_trace and max_j != -1:
        for i in range(1, max_j + 2):
            header.append(f'Clause-{i}')

    # Pad ragged rows the way a DataFrame build does
    for row in data:
        row.extend([None] * (len(header) - len(row)))

    # Render clause columns back in the author's clause order
    if clause_map is not None:
        n_clause_cols = len(header) - _CLAUSE_OFFSET
        for row in data:
            if row[6] in clause_map:
                tail = row[_CLAUSE_OFFSET:]
                new_tail = [None] * n_clause_cols
                for orig_pos, target_pos in clause_map[row[6]].items():
                    new_tail[target_pos] = tail[orig_pos]
                row[_CLAUSE_OFFSET:] = new_tail

    return Frame(header, data)


def get_rule_trace(interpretation, clause_map):
    """The full change trace as (node frame, edge frame)."""
    node_frame = _trace_frame(interpretation.rule_trace_node,
                              interpretation.rule_trace_node_atoms,
                              interpretation.atom_trace, _TRACE_HEADER_NODE,
                              clause_map)
    edge_frame = _trace_frame(interpretation.rule_trace_edge,
                              interpretation.rule_trace_edge_atoms,
                              interpretation.atom_trace, _TRACE_HEADER_EDGE,
                              clause_map)
    return node_frame, edge_frame


def save_rule_trace(interpretation, clause_map, timestamp, folder='./'):
    """Write the trace frames as the pinned CSV pair (output.py:99-105):
    `rule_trace_{nodes,edges}_{timestamp}.csv` under `folder` (joined the
    same way — os.path.join on the caller's string, no validation). A
    nonexistent folder raises the pinned pandas parent-directory refusal —
    `OSError: Cannot save file into a non-existent directory: '<parent>'`
    (pandas io/common.py check_parent_directory, hit by `to_csv` before any
    write; screened live on the pin 2026-07-07, review slice 6) — never the
    bare open() errno message.

    The byte target is the pinned `DataFrame.to_csv(path, index=False)`
    output: comma-delimited, QUOTE_MINIMAL double-quote quoting, os.linesep
    row ends, None/NaN cells empty, every other cell str()-rendered — which
    is exactly the csv module's writer over the Frame's cells (csv.writer
    str()s non-strings and writes None as ''), so the compared observation
    is the file contents themselves, cell-for-cell with the pin's.
    """
    node_frame, edge_frame = get_rule_trace(interpretation, clause_map)
    for kind, frame in (('nodes', node_frame), ('edges', edge_frame)):
        path = os.path.join(folder, f'rule_trace_{kind}_{timestamp}.csv')
        # The pinned to_csv checks the parent before opening (pandas
        # io/common.py check_parent_directory) and raises this exact shape
        parent = pathlib.Path(path).parent
        if not parent.is_dir():
            raise OSError(
                rf"Cannot save file into a non-existent directory: '{parent}'")
        with open(path, 'w', newline='') as f:
            writer = csv.writer(f, lineterminator=os.linesep)
            writer.writerow(frame.columns)
            writer.writerows(frame.itertuples(index=False, name=None))


def _filter_and_sort(trace, tmax, labels, bound, sort_by, descending):
    """The shared filter/sort pipeline (filter.py:8-117): keep each
    (component, label)'s LATEST change per timestep, sort every kept change
    by bound across all timesteps (stable, so trace order breaks ties),
    then emit one frame per timestep with a [0,1] default cell for the
    requested labels a qualifying component doesn't carry. The pinned node
    and edge pipelines differ only in DataFrame mechanics (an edge component
    rides a two-level index that is recombined into a tuple column) — the
    resulting cells are identical, so one pipeline serves both."""
    latest_changes = {t: {} for t in range(tmax + 1)}
    for change in trace:
        t, comp, label, bnd = change[0], change[2], change[3], change[4]
        latest_changes[t][(comp, label)] = bnd

    list_to_be_sorted = []
    for t, d in latest_changes.items():
        for (comp, label), bnd in d.items():
            list_to_be_sorted.append((bnd, t, comp, label))

    reverse = bool(descending)
    if sort_by == 'lower':
        list_to_be_sorted.sort(key=lambda x: x[0].lower, reverse=reverse)
    elif sort_by == 'upper':
        list_to_be_sorted.sort(key=lambda x: x[0].upper, reverse=reverse)

    df = {t: {} for t in range(tmax + 1)}
    for bnd, t, comp, label in list_to_be_sorted:
        df[t][(comp, label)] = bnd

    components = [{} for _ in range(tmax + 1)]
    for t, d in df.items():
        for (comp, label), bnd in d.items():
            if label.get_value() in labels and bnd in bound:
                if comp not in components[t]:
                    components[t][comp] = {lab: [0, 1] for lab in labels}
                components[t][comp][label.get_value()] = [bnd.lower, bnd.upper]

    frames = []
    columns = ['component', *labels]
    for t in range(tmax + 1):
        rows = [[comp] + [cells[lab] for lab in labels]
                for comp, cells in components[t].items()]
        frames.append(Frame(columns, rows))
    return frames


def filter_and_sort_nodes(interpretation, labels, bound=None, sort_by='lower',
                          descending=True):
    if bound is None:
        bound = interval.closed(0, 1)
    return _filter_and_sort(interpretation.rule_trace_node, interpretation.time,
                            labels, bound, sort_by, descending)


def filter_and_sort_edges(interpretation, labels, bound=None, sort_by='lower',
                          descending=True):
    if bound is None:
        bound = interval.closed(0, 1)
    return _filter_and_sort(interpretation.rule_trace_edge, interpretation.time,
                            labels, bound, sort_by, descending)
