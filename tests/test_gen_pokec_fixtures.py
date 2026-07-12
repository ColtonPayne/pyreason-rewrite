"""Fast-tier tests for tools/gen_pokec_fixtures.py's pure layer — the pets
normalization and the customer picker that define the reconstructed §4.2
fixtures' identity. No SNAP data, no I/O: the streaming layer is exercised by
the on-box generation runs the fixtures' provenance cites."""

from gen_pokec_fixtures import (CUSTOMER_RATIO, normalize_pets,
                                pick_customers, render_case)


def test_normalize_pets_maps_the_dominant_slovak_stems():
    """proves: the fixed stem map turns the dataset's top free-text forms
    into the intended pet tokens, sorted and deduplicated."""
    assert normalize_pets("mam psa") == ("dog",)
    assert normalize_pets("pes, macka") == ("cat", "dog")
    assert normalize_pets("mam macku, mam psa") == ("cat", "dog")
    assert normalize_pets("rybky") == ("fish",)
    assert normalize_pets("korytnacka") == ("turtle",)
    assert normalize_pets("PES") == ("dog",)  # case-insensitive


def test_normalize_pets_negations_and_null_are_ownerless():
    """proves: null/empty and the all-negation forms produce no tokens (the
    rows that must not become hasPet owners), while a negation mixed with a
    concrete pet keeps the pet."""
    assert normalize_pets("null") == ()
    assert normalize_pets("") == ()
    assert normalize_pets("nemam ziadne") == ()
    assert normalize_pets("nemam rad") == ()
    assert normalize_pets("nemam rad macky, ale mam psa") == ("cat", "dog")


def test_pick_customers_hits_the_paper_proportion_and_spreads():
    """proves: the picker returns round(CUSTOMER_RATIO * nodes) owners
    (>=5 floor), deterministically spread across the sorted owner list, and
    never more than the owners available."""
    owners = list(range(0, 10_000, 2))  # 5000 owners
    picked = pick_customers(owners, 100_000)
    assert len(picked) == round(CUSTOMER_RATIO * 100_000)
    assert picked == sorted(picked)
    assert set(picked) <= set(owners)
    assert picked[0] == owners[0]
    spread = picked[-1] - picked[0]
    assert spread > owners[-1] // 2  # spread, not a head cluster
    assert pick_customers([1, 2, 3], 10_000) == [1, 2, 3]  # capped at owners
    assert len(pick_customers(list(range(100)), 100)) == 5  # the floor


def test_render_case_carries_the_paper_rules_and_bounded_window():
    """proves: the rendered case is one-step-form with the paper's two
    relevance rules, customer facts spanning the bounded window, and the
    relevance probe — the shape bench and the equivalence runner share."""
    case = render_case("10k", {"users": 10, "friend_edges": 20,
                               "haspet_edges": 5, "pet_types": 2,
                               "nodes": 12}, [7, 42])
    assert case["id"] == "perf-pokec-10k"
    assert "steps" not in case and "reason" in case["inputs"]
    assert case["inputs"]["reason"]["timesteps"] == 8
    rules = [r["text"] for r in case["inputs"]["rules"]]
    assert rules[0].startswith("relevance(x) : [0.6,1] <-1 relevance(y)")
    assert "hasPet(x,p):[1,1], hasPet(y,p):[1,1]" in rules[1]
    facts = case["inputs"]["facts"]
    assert [f["text"] for f in facts] == ["relevance(u7)", "relevance(u42)"]
    assert all(f["start"] == 0 and f["end"] == 8 for f in facts)
    assert case["probes"][0]["kind"] == "filter_sort_nodes"
