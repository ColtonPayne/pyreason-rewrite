"""Fast-tier gate for the AC-1 surface inventory (docs/surface.md).

The inventory makes "all pyreason-API features" countable; these tests mechanize it
against the pinned oracle source. The scan parses the API module with stdlib `ast`
only — it never imports the oracle — so the gate runs offline on a machine with no
oracle environment. Each row kind lives in a different source shape, so each is
asserted per kind: functions are top-level defs, knobs are `_Settings` properties,
types are the API module's own import statements.
"""

import ast
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
API_MODULE = REPO / "oracle" / "pyreason" / "pyreason" / "pyreason.py"
INVENTORY = REPO / "docs" / "surface.md"

# The charter-set public type surface (operator-set, 2026-07-06): four classes the API
# module imports by name plus the two reached through its aliased submodule imports.
# torch-gated names (LogicIntegratedClassifier, ModelInterfaceOptions) are out of scope.
NAME_IMPORTED_TYPES = {"Rule", "Fact", "Query", "Threshold"}
SUBMODULE_ALIAS_TYPES = {"interval": "Interval", "label": "Label"}
DSL_ROWS = {"rule-text", "fact-text"}
STATUSES = {"uncovered", "cased", "equivalent", "divergent-queued", "adjudicated"}


def scan_api():
    """Parse the pinned API module source into its per-kind public-surface sets."""
    tree = ast.parse(API_MODULE.read_text())
    functions = {
        node.name
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
    }
    settings_cls = next(
        node
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == "_Settings"
    )
    knobs = {
        node.name
        for node in settings_cls.body
        if isinstance(node, ast.FunctionDef)
        and any(
            isinstance(d, ast.Name) and d.id == "property" for d in node.decorator_list
        )
    }
    imported_names = set()
    import_aliases = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom):
            imported_names.update(a.asname or a.name for a in node.names)
        elif isinstance(node, ast.Import):
            for a in node.names:
                if a.asname:
                    import_aliases.add(a.asname)
    return functions, knobs, imported_names, import_aliases


def parse_inventory():
    """Parse docs/surface.md rows into {kind: {id: {field: value}}}."""
    rows = {}
    block_re = re.compile(r"^## (fn|type|setting|dsl):(\S+)$", re.M)
    text = INVENTORY.read_text()
    matches = list(block_re.finditer(text))
    for m, nxt in zip(matches, matches[1:] + [None]):
        body = text[m.end() : nxt.start() if nxt else len(text)]
        fields = dict(re.findall(r"^- ([a-z ]+):(.*)$", body, re.M))
        classes = re.findall(r"^  - ([a-z0-9_-]+)$", body, re.M)
        rows.setdefault(m.group(1), {})[m.group(2)] = {
            "fields": {k: v.strip() for k, v in fields.items()},
            "classes": classes,
        }
    return rows


def test_function_rows_match_pinned_api():
    """proves: the inventory's fn: rows equal the pinned API module's public top-level
    functions exactly, so an omitted or phantom function row reds the gate."""
    functions, _, _, _ = scan_api()
    rows = set(parse_inventory().get("fn", {}))
    assert rows == functions, (
        f"missing from inventory: {sorted(functions - rows)}; "
        f"phantom in inventory: {sorted(rows - functions)}"
    )


def test_knob_rows_match_pinned_settings():
    """proves: the inventory's setting: rows equal the `_Settings` class's @property
    names in the pinned API module exactly."""
    _, knobs, _, _ = scan_api()
    rows = set(parse_inventory().get("setting", {}))
    assert rows == knobs, (
        f"missing from inventory: {sorted(knobs - rows)}; "
        f"phantom in inventory: {sorted(rows - knobs)}"
    )


def test_type_rows_match_pinned_imports():
    """proves: the inventory carries exactly the six charter-set public types, each
    anchored to an import statement actually present in the pinned API module."""
    _, _, imported_names, import_aliases = scan_api()
    rows = set(parse_inventory().get("type", {}))
    expected = NAME_IMPORTED_TYPES | set(SUBMODULE_ALIAS_TYPES.values())
    assert rows == expected, f"type rows {sorted(rows)} != charter set {sorted(expected)}"
    assert NAME_IMPORTED_TYPES <= imported_names, (
        f"pinned module no longer name-imports {sorted(NAME_IMPORTED_TYPES - imported_names)}"
    )
    missing_aliases = set(SUBMODULE_ALIAS_TYPES) - import_aliases
    assert not missing_aliases, (
        f"pinned module no longer aliases submodules {sorted(missing_aliases)}"
    )


def test_dsl_rows_are_the_two_text_dsls():
    """proves: the Rule and Fact text DSLs carry their own inventory rows, and no
    other dsl: row exists."""
    rows = set(parse_inventory().get("dsl", {}))
    assert rows == DSL_ROWS


def test_every_row_carries_the_seam_contract():
    """proves: every inventory row carries an oracle anchor, at least one enumerated
    input class, and a status from the AC-1 enum — no row is a bare name."""
    for kind, rows in parse_inventory().items():
        for item, row in rows.items():
            anchor = row["fields"].get("oracle anchor", "")
            assert re.search(r"\S+\.(py|md):\d+|\S+/\S+", anchor), (
                f"{kind}:{item} has no oracle anchor"
            )
            assert row["classes"], f"{kind}:{item} enumerates no input classes"
            assert row["fields"].get("status") in STATUSES, (
                f"{kind}:{item} status {row['fields'].get('status')!r} not in {STATUSES}"
            )
