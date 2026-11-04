import json
from datetime import date, timedelta

import pytest

from crypto_radar.opportunities import (
    build_opportunity_table, opportunity_card_quality, validate_opportunity_card,
)


def sample_card():
    return {
        "version": 1, "name": "Example pool", "protocol": "Example protocol",
        "method_id": "defi-lending", "asset": "TEST", "chain": "Testnet",
        "source_url": "https://example.org/docs", "checked_on": "2026-01-01",
        "observed_apr_pct": None, "reward_source": "Borrower interest",
        "withdrawal_terms": "Subject to pool liquidity",
        "risk_notes": "Smart-contract risk",
    }


def test_card_roundtrip_and_table():
    restored = validate_opportunity_card(json.loads(json.dumps(sample_card())))
    assert restored["observed_apr_pct"] is None
    assert opportunity_card_quality(restored)["complete_fields"] == 4
    rows = build_opportunity_table([restored])
    assert rows[0]["Method"] == "defi-lending"
    assert rows[0]["Documented fields"] == "4/5"


def test_card_rejects_missing_source_and_invalid_apr():
    card = sample_card()
    with pytest.raises(ValueError):
        validate_opportunity_card({**card, "source_url": "not-a-url"})
    with pytest.raises(ValueError):
        validate_opportunity_card({**card, "observed_apr_pct": float("nan")})
    with pytest.raises(ValueError):
        validate_opportunity_card({**card, "method_id": "unknown"})


def test_card_rejects_future_dates_and_credentials_in_url():
    card = sample_card()
    future = (date.today() + timedelta(days=1)).isoformat()
    with pytest.raises(ValueError):
        validate_opportunity_card({**card, "checked_on": future})
    with pytest.raises(ValueError):
        validate_opportunity_card({**card, "source_url": "https://user:password@example.org"})


def test_card_table_limits_entries():
    with pytest.raises(ValueError):
        build_opportunity_table([sample_card()] * 51)
