"""Deterministic generator for the Pokec scaling-experiment fixtures (paper §4.2).

Reconstructs the PyReason paper's Pokec advertising-relevance experiment from
the public SNAP dataset (soc-pokec-relationships.txt.gz +
soc-pokec-profiles.txt.gz, verified 30,622,564 edges / 1,632,803 profiles —
the paper's exact population), then writes one GraphML fixture and one
harness case JSON per rung. Stdlib-only and fully deterministic: every output
byte is a pure function of the SNAP inputs and the RUNGS table.

Reconstruction model (disclosed, since the paper's exact artifacts are not
public):

- **Rungs are id-prefix induced subgraphs.** A rung keeps the N smallest
  user_ids and every friendship edge with both endpoints kept. Streamable,
  deterministic, and each rung is a strict subset of the next — the right
  shape for a scaling screen. `full` keeps everyone.
- **The hasPet augmentation** mirrors the paper's (Table 8: +17 nodes,
  +1,010,550 edges): the profiles' free-text Slovak `pets` column (column 13)
  is normalized by a fixed keyword map (PET_STEMS below) to pet-type tokens;
  each (user, token) becomes a directed `hasPet` edge to a shared pet node.
  The paper's exact normalization is unpublished; ours is a deterministic
  best-effort and the oracle-vs-rewrite comparison is unaffected (both
  engines see identical inputs).
- **Customers** ("current customers", always relevant) are seeded facts:
  round(2308/1632803 * rung_nodes) pet owners — the paper's proportion —
  picked as every k-th of the rung's sorted owner list (spread, not
  clustered). relevance facts span the whole window like the ladder's seeds.
- **Rules are the paper's two relevance rules verbatim** (§4.2), timesteps=8
  (the paper's convergence point; bounded per the ladder's B16 constraint).

Usage (data dir holds the two SNAP .gz files):
    python tools/gen_pokec_fixtures.py --data-dir ~/pyreason-campaign/data/pokec \
        --rungs 10k,50k,200k,full --write

GraphML fixtures land in harness/fixtures/pokec/ (gitignored — regenerable,
and `full` is ~GB-scale); case JSONs land in harness/cases/ (committed). The
case's `graphml_path` stays repo-relative like every other case.
"""

import argparse
import gzip
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FIXTURE_DIR = REPO / "harness" / "fixtures" / "pokec"
CASE_DIR = REPO / "harness" / "cases"

PETS_COL = 13          # 0-based index of `pets` in soc-pokec-profiles.txt
TIMESTEPS = 8          # the paper's convergence point (Table 3)
CUSTOMER_RATIO = 2308 / 1632803  # the paper's current-customer proportion

# rung name -> node count (id-prefix cutoff); None = the whole population.
# 25k exists for the equivalence-at-scale anchor: the largest rung whose
# oracle capture stays overnight-feasible (~6 h at the measured x^1.87).
RUNGS = {"10k": 10_000, "25k": 25_000, "50k": 50_000,
         "200k": 200_000, "full": None}

# Fixed Slovak-stem -> pet-token map, applied to the lowercased pets text by
# substring containment, negations first (order matters and is part of the
# fixture's identity — change it only with a regeneration + case rescreen).
NEGATION_STEMS = ("nemam", "ziadne", "nechcem", "neznasam")
PET_STEMS = (
    ("psa", "dog"), ("pes", "dog"), ("psik", "dog"), ("psy", "dog"),
    ("mack", "cat"), ("macic", "cat"),
    ("rybk", "fish"), ("rybic", "fish"), ("akvari", "fish"),
    ("vtacik", "bird"), ("vtaci", "bird"), ("kanarik", "bird"),
    ("papagaj", "parrot"), ("andulk", "parrot"),
    ("korytnac", "turtle"),
    ("skrecok", "hamster"), ("skreck", "hamster"),
    ("hlodav", "rodent"), ("mys", "rodent"), ("potkan", "rodent"),
    ("morca", "guineapig"),
    ("zajac", "rabbit"), ("kralik", "rabbit"),
    ("had", "snake"), ("pavuk", "spider"), ("jaster", "lizard"),
    ("kon", "horse"), ("fretk", "ferret"), ("ryb", "fish"),
)


def normalize_pets(text: str) -> tuple:
    """The pets free text -> sorted tuple of pet tokens ('' and negation-only
    text -> ()). Substring stems on the lowercased text; a row that mixes a
    negation with a concrete pet keeps the pet (the negation stems only stop
    the all-negation rows from becoming owners)."""
    if not text or text == "null":
        return ()
    low = text.lower()
    tokens = sorted({tok for stem, tok in PET_STEMS if stem in low})
    if tokens:
        return tuple(tokens)
    return ()


def read_profiles(profiles_gz: Path, cutoff):
    """(sorted kept user_ids, {user_id: pet-token tuple for owners}).

    Streams the profiles file; keeps the `cutoff` smallest user_ids (all if
    None). Does not assume the file is id-sorted — ids are collected and
    sorted (1.6M ints)."""
    ids = []
    pets = {}
    with gzip.open(profiles_gz, "rt", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            cols = line.rstrip("\n").split("\t")
            try:
                uid = int(cols[0])
            except (ValueError, IndexError):
                continue
            ids.append(uid)
            toks = normalize_pets(cols[PETS_COL]) if len(cols) > PETS_COL else ()
            if toks:
                pets[uid] = toks
    ids.sort()
    kept = ids if cutoff is None else ids[:cutoff]
    kept_set = set(kept)
    return kept, {u: t for u, t in pets.items() if u in kept_set}


def pick_customers(owner_ids: list, n_nodes: int) -> list:
    """Every k-th of the sorted owner list, hitting the paper's proportion
    (>=5 so tiny rungs still have a seed set)."""
    target = max(5, round(CUSTOMER_RATIO * n_nodes))
    target = min(target, len(owner_ids))
    if target == 0:
        return []
    step = len(owner_ids) / target
    return [owner_ids[int(i * step)] for i in range(target)]


def write_graphml(out_path: Path, kept_ids: list, kept_set: set,
                  pets: dict, relationships_gz: Path) -> dict:
    """Streams the fixture to disk (the full rung is GB-scale text): nodes
    u<id> + one node per pet token, friend edges (attr friend=1) filtered to
    the rung, hasPet edges (attr hasPet=1). Returns edge/node counts."""
    pet_tokens = sorted({t for toks in pets.values() for t in toks})
    n_friend = 0
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as out:
        out.write("<?xml version='1.0' encoding='utf-8'?>\n")
        out.write('<graphml xmlns="http://graphml.graphdrawing.org/xmlns" '
                  'xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" '
                  'xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns '
                  'http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">\n')
        out.write('  <key id="d0" for="edge" attr.name="friend" '
                  'attr.type="long" />\n')
        out.write('  <key id="d1" for="edge" attr.name="hasPet" '
                  'attr.type="long" />\n')
        out.write('  <graph edgedefault="directed">\n')
        for uid in kept_ids:
            out.write(f'    <node id="u{uid}" />\n')
        for tok in pet_tokens:
            out.write(f'    <node id="{tok}" />\n')
        with gzip.open(relationships_gz, "rt", encoding="utf-8") as fh:
            for line in fh:
                parts = line.split()
                if len(parts) != 2:
                    continue
                src, dst = int(parts[0]), int(parts[1])
                if src in kept_set and dst in kept_set:
                    out.write(f'    <edge source="u{src}" target="u{dst}">'
                              f'<data key="d0">1</data></edge>\n')
                    n_friend += 1
        n_haspet = 0
        for uid in sorted(pets):
            for tok in pets[uid]:
                out.write(f'    <edge source="u{uid}" target="{tok}">'
                          f'<data key="d1">1</data></edge>\n')
                n_haspet += 1
        out.write('  </graph>\n</graphml>\n')
    return {"nodes": len(kept_ids) + len(pet_tokens), "users": len(kept_ids),
            "pet_types": len(pet_tokens), "friend_edges": n_friend,
            "haspet_edges": n_haspet}


def render_case(rung: str, counts: dict, customers: list) -> dict:
    """The harness case: the paper's two §4.2 rules verbatim, customer seed
    facts spanning the bounded window, relevance probes for the Table-3
    metric. Equivalence and bench share this one case (the ladder pattern)."""
    return {
        "id": f"perf-pokec-{rung}",
        "purpose": (
            f"Pokec §4.2 replication rung '{rung}': {counts['users']} users / "
            f"{counts['friend_edges']} friend edges / {counts['haspet_edges']} "
            f"hasPet edges over {counts['pet_types']} pet types "
            f"(id-prefix induced subgraph of SNAP soc-Pokec; reconstruction "
            f"model in tools/gen_pokec_fixtures.py). The paper's two "
            f"advertising-relevance rules, {len(customers)} seeded customer "
            f"facts (the paper's proportion), timesteps={TIMESTEPS} — "
            f"explicitly bounded per the ladder's B16 constraint."),
        "runtime_class": "long",
        "provenance": (
            "PyReason paper §4.2 (arXiv:2302.13482) over public SNAP "
            "soc-Pokec; fixture harness/fixtures/pokec/pokec-%s.graphml "
            "generated by tools/gen_pokec_fixtures.py (deterministic, "
            "gitignored — regenerate from the SNAP files)." % rung),
        "surface_items": [
            "fn:load_graphml", "fn:add_rule", "fn:add_fact", "fn:reason",
            "fn:filter_and_sort_nodes", "fn:get_time",
            "type:Rule", "type:Fact", "dsl:rule-text", "dsl:fact-text",
            "setting:verbose",
        ],
        "inputs": {
            "settings": {"verbose": False},
            "graph": {"graphml_path": f"harness/fixtures/pokec/pokec-{rung}.graphml"},
            "rules": [
                {"text": "relevance(x) : [0.6,1] <-1 relevance(y):[1,1], "
                         "friend(x,y):[1,1]",
                 "name": "relevance_friend_rule"},
                {"text": "relevance(x) : [1,1] <-1 relevance(y):[1,1], "
                         "friend(x,y):[1,1], hasPet(x,p):[1,1], "
                         "hasPet(y,p):[1,1]",
                 "name": "relevance_same_pet_rule"},
            ],
            "facts": [
                {"text": f"relevance(u{uid})", "name": f"customer_{i}",
                 "start": 0, "end": TIMESTEPS}
                for i, uid in enumerate(customers)
            ],
            "reason": {"timesteps": TIMESTEPS},
        },
        "probes": [
            {"id": "nodes-relevance", "kind": "filter_sort_nodes",
             "labels": ["relevance"]},
            {"id": "time", "kind": "get_time"},
        ],
        "comparison": {"probes": {}},
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", type=Path, required=True,
                        help="directory holding the two SNAP .gz files")
    parser.add_argument("--rungs", default="10k",
                        help="comma-separated subset of: " + ",".join(RUNGS))
    parser.add_argument("--write", action="store_true",
                        help="write outputs (default: report what would change)")
    args = parser.parse_args(argv)

    rels = args.data_dir / "soc-pokec-relationships.txt.gz"
    profs = args.data_dir / "soc-pokec-profiles.txt.gz"
    if not rels.is_file() or not profs.is_file():
        print(f"SNAP files not found under {args.data_dir}", file=sys.stderr)
        return 2
    rungs = [r.strip() for r in args.rungs.split(",") if r.strip()]
    unknown = [r for r in rungs if r not in RUNGS]
    if unknown:
        print(f"unknown rung(s): {unknown}", file=sys.stderr)
        return 2

    for rung in rungs:
        cutoff = RUNGS[rung]
        kept_ids, pets = read_profiles(profs, cutoff)
        owners = sorted(pets)
        customers = pick_customers(owners, len(kept_ids))
        gml_path = FIXTURE_DIR / f"pokec-{rung}.graphml"
        case_path = CASE_DIR / f"perf-pokec-{rung}.json"
        if not args.write:
            print(f"{rung}: would write {gml_path} + {case_path} "
                  f"({len(kept_ids)} users, {len(owners)} owners, "
                  f"{len(customers)} customers)")
            continue
        counts = write_graphml(gml_path, kept_ids, set(kept_ids), pets, rels)
        case = render_case(rung, counts, customers)
        case_path.write_text(json.dumps(case, indent=2, sort_keys=False) + "\n")
        print(f"{rung}: {counts} customers={len(customers)} -> "
              f"{gml_path.name}, {case_path.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
