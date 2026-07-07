"""The public Query constructor — query text in, parsed query out.

Signature and semantics match the pinned oracle constructor
(oracle scripts/query/query.py): the four parsed fields are exposed through
getters, and str/repr echo the original query text verbatim.
"""

from ._query_parser import parse_query


class Query:
    """One query parsed from a string of form 'pred(node)', 'pred(n1,n2)',
    or 'pred(node) : [l, u]'. Bounds default to [1, 1]; a leading '~' (in the
    no-bounds form) inverts them to [0, 0].

    :param query_text: the query string
    """

    def __init__(self, query_text: str):
        self.__pred, self.__component, self.__comp_type, self.__bnd = parse_query(query_text)
        self.query_text = query_text

    def get_predicate(self):
        return self.__pred

    def get_component(self):
        return self.__component

    def get_component_type(self):
        return self.__comp_type

    def get_bounds(self):
        return self.__bnd

    def __str__(self):
        return self.query_text

    def __repr__(self):
        return self.query_text
