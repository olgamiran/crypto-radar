import pytest

from crypto_radar.income import build_scenarios, calculate_income_scenario


def test_zero_apr_and_zero_price_change_preserves_principal_without_fees():
    result = calculate_income_scenario(1000, 0, 12)
    assert result["rewards"] == 0
    assert result["ending_value"] == 1000
    assert result["profit_loss"] == 0


def test_monthly_compounding_produces_positive_rewards():
    result = calculate_income_scenario(1000, 12, 12)
    assert result["rewards"] > 120
    assert result["ending_value"] == pytest.approx(1126.825, rel=1e-3)


def test_price_drop_can_outweigh_yield():
    result = calculate_income_scenario(1000, 10, 12, price_change_pct=-50)
    assert result["profit_loss"] < 0


def test_invalid_inputs_are_rejected():
    with pytest.raises(ValueError):
        calculate_income_scenario(-1, 5, 12)
    with pytest.raises(ValueError):
        calculate_income_scenario(100, 5, 12, price_change_pct=-101)


def test_scenarios_include_four_price_paths():
    rows = build_scenarios(1000, 5, 12)
    assert [row["asset_price_change_pct"] for row in rows] == [-50, -20, 0, 20]


def test_income_method_comparison_uses_independent_price_assumptions():
    from crypto_radar.income import compare_income_methods

    rows = compare_income_methods(1000, 12, -20, [
        {"method": "Buy and hold", "apr_pct": 0, "fee_pct": 0},
        {"method": "Native staking", "apr_pct": 6, "fee_pct": 1},
        {"method": "Stablecoin yield", "apr_pct": 4, "fee_pct": 0, "price_change_pct": -5},
    ])
    assert len(rows) == 3
    assert rows[0]["Virtual ending value ($)"] == pytest.approx(800)
    assert rows[1]["Virtual rewards ($)"] > 0
    assert rows[1]["Virtual ending value ($)"] > rows[0]["Virtual ending value ($)"]
    assert rows[2]["Asset price change (%)"] == -5
    assert rows[2]["Virtual ending value ($)"] < 1050


def test_income_method_comparison_rejects_invalid_assumptions():
    from crypto_radar.income import compare_income_methods

    with pytest.raises(ValueError):
        compare_income_methods(0, 12, 0, [{"method": "Hold", "apr_pct": 0, "fee_pct": 0}])
    with pytest.raises(ValueError):
        compare_income_methods(1000, 12, 0, [{"method": "Staking", "apr_pct": float("nan"), "fee_pct": 0}])
    with pytest.raises(ValueError):
        compare_income_methods(1000, 12, 0, [])


def test_income_stress_shocks_are_independent_and_combined():
    from crypto_radar.income import stress_test_income_methods

    rows = stress_test_income_methods(
        1000, 12,
        [{"method": "Staking", "apr_pct": 12, "fee_pct": 0, "price_change_pct": 0}],
        apr_cut_pct=50, price_shock_pct=-30, loss_haircut_pct=25,
    )
    by_scenario = {row["Scenario"]: row for row in rows}
    assert len(rows) == 5
    baseline = by_scenario["Baseline"]["Virtual ending value ($)"]
    assert by_scenario["APR reduction"]["APR (%)"] == 6
    assert by_scenario["APR reduction"]["Virtual ending value ($)"] < baseline
    assert by_scenario["Additional price decline"]["Asset price change (%)"] == -30
    assert by_scenario["Partial capital loss"]["Virtual ending value ($)"] == pytest.approx(baseline * 0.75)
    assert by_scenario["Combined shocks"]["Virtual ending value ($)"] < by_scenario["Partial capital loss"]["Virtual ending value ($)"]
    assert by_scenario["Baseline"]["Change vs baseline ($)"] == pytest.approx(0)


def test_income_stress_caps_price_drop_at_total_loss():
    from crypto_radar.income import stress_test_income_methods

    rows = stress_test_income_methods(
        1000, 12,
        [{"method": "Stablecoin yield", "apr_pct": 5, "fee_pct": 0, "price_change_pct": -80}],
        price_shock_pct=-50,
    )
    shock = next(row for row in rows if row["Scenario"] == "Additional price decline")
    assert shock["Asset price change (%)"] == -100
    assert shock["Virtual ending value ($)"] == pytest.approx(0)


def test_income_stress_rejects_invalid_shocks():
    from crypto_radar.income import stress_test_income_methods

    assumption = [{"method": "Hold", "apr_pct": 0, "fee_pct": 0}]
    with pytest.raises(ValueError):
        stress_test_income_methods(1000, 12, assumption, loss_haircut_pct=101)
    with pytest.raises(ValueError):
        stress_test_income_methods(1000, 12, assumption, apr_cut_pct=float("nan"))
