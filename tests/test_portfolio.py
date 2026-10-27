import pytest

from crypto_radar.portfolio import build_portfolio_snapshot


def test_buy_marks_holding_to_current_price_and_tracks_cash():
    snapshot = build_portfolio_snapshot(
        1000,
        [{"type": "BUY", "asset": "BTC", "quantity": 0.01, "price_usd": 20000, "fee_usd": 1}],
        {"BTC": 25000},
    )
    assert snapshot["cash"] == pytest.approx(799)
    assert snapshot["holdings_value"] == pytest.approx(250)
    assert snapshot["equity"] == pytest.approx(1049)
    assert snapshot["profit_loss"] == pytest.approx(49)
    assert snapshot["total_fees"] == pytest.approx(1)


def test_reward_adds_units_without_spending_principal():
    snapshot = build_portfolio_snapshot(
        500,
        [{"type": "REWARD", "asset": "ETH", "quantity": 0.1, "price_usd": 2000, "fee_usd": 0}],
    )
    assert snapshot["cash"] == pytest.approx(500)
    assert snapshot["holdings"]["ETH"] == pytest.approx(0.1)
    assert snapshot["equity"] == pytest.approx(700)


def test_sell_returns_cash_and_reduces_units():
    transactions = [
        {"type": "BUY", "asset": "ETH", "quantity": 1, "price_usd": 1000, "fee_usd": 0},
        {"type": "SELL", "asset": "ETH", "quantity": 0.25, "price_usd": 1200, "fee_usd": 2},
    ]
    snapshot = build_portfolio_snapshot(2000, transactions, {"ETH": 1200})
    assert snapshot["cash"] == pytest.approx(1298)
    assert snapshot["holdings"]["ETH"] == pytest.approx(0.75)
    assert snapshot["equity"] == pytest.approx(2198)


def test_rejects_buy_that_exceeds_virtual_cash():
    with pytest.raises(ValueError, match="insufficient virtual cash"):
        build_portfolio_snapshot(
            100,
            [{"type": "BUY", "asset": "BTC", "quantity": 1, "price_usd": 200, "fee_usd": 0}],
        )


def test_rejects_selling_more_than_owned():
    with pytest.raises(ValueError, match="cannot sell more"):
        build_portfolio_snapshot(
            1000,
            [{"type": "SELL", "asset": "BTC", "quantity": 1, "price_usd": 20000, "fee_usd": 0}],
        )


def test_fee_only_transaction_reduces_cash():
    snapshot = build_portfolio_snapshot(
        100,
        [{"type": "FEE", "asset": "", "quantity": 0, "price_usd": 0, "fee_usd": 3}],
    )
    assert snapshot["cash"] == pytest.approx(97)
    assert snapshot["total_fees"] == pytest.approx(3)


def test_rejects_negative_starting_cash():
    with pytest.raises(ValueError):
        build_portfolio_snapshot(-1, [])


def test_rejects_non_finite_fee():
    with pytest.raises(ValueError, match="finite and non-negative"):
        build_portfolio_snapshot(
            100,
            [{"type": "FEE", "asset": "", "quantity": 0, "price_usd": 0, "fee_usd": float("nan")}],
        )
