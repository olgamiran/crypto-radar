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


def test_research_overview_includes_unresearched_methods():
    from crypto_radar.yield_research import build_yield_research_overview

    rows = build_yield_research_overview()
    assert len(rows) == len(get_research_methods())
    assert all(row["Best documentation"] == "Not researched" for row in rows)
    assert all(row["Saved scenarios"] == 0 for row in rows)


def test_research_overview_matches_saved_method_aliases_and_evidence():
    from crypto_radar.yield_research import build_yield_research_overview, filter_yield_research_overview

    snapshot = {
        "version": 1, "name": "Lending research", "kind": "comparison",
        "inputs": {"principal": 1000, "months": 12, "methods": [
            {"method": "Centralized lending", "apr_pct": 4, "fee_pct": 1, "price_change_pct": -5}
        ]},
        "research": {"assumption_source": "Hypothetical", "checked_on": "2026-01-01",
                     "withdrawal_terms": "May be frozen", "risk_notes": "Counterparty risk"},
    }
    rows = build_yield_research_overview([snapshot])
    lending = next(row for row in rows if row["Method"] == "Centralized crypto lending")
    assert lending["Saved scenarios"] == 1
    assert lending["Best documentation"] == "4/4"
    assert len(filter_yield_research_overview(rows, documentation="Fully documented")) == 1
    assert len(filter_yield_research_overview(rows, documentation="No saved research")) == len(rows) - 1


def test_research_overview_filters_risk_and_liquidity():
    from crypto_radar.yield_research import build_yield_research_overview, filter_yield_research_overview

    rows = build_yield_research_overview()
    filtered = filter_yield_research_overview(rows, risk="Very high", liquidity="Pool liquidity-dependent")
    assert filtered
    assert all(row["General risk"] == "Very high" for row in filtered)
    assert all(row["Liquidity type"] == "Pool liquidity-dependent" for row in filtered)
