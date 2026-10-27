from crypto_radar.yield_research import get_categories, get_research_methods


def test_catalogue_has_unique_ids_and_required_risk_fields():
    methods = get_research_methods()
    assert len(methods) >= 5
    assert len({item["id"] for item in methods}) == len(methods)
    for item in methods:
        assert item["name"]
        assert item["reward_source"]
        assert item["liquidity"]
        assert item["key_risks"]
        assert item["what_to_verify"]


def test_category_filter_returns_only_matching_methods():
    methods = get_research_methods("Lending")
    assert len(methods) == 2
    assert all(item["category"] == "Lending" for item in methods)


def test_catalogue_does_not_claim_live_apy():
    assert "All" in get_categories()
    for item in get_research_methods():
        assert "apy" not in item["reward_source"].lower()
