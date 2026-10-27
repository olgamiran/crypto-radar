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
