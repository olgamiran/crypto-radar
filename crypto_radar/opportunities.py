"""Portable, manually entered research cards for hypothetical crypto yield opportunities.

Cards are notes, not verified listings, endorsements or live offers.
"""
from __future__ import annotations

from datetime import date
from urllib.parse import urlparse
import math


def validate_opportunity_card(card: object) -> dict:
    if not isinstance(card, dict) or card.get("version") != 1:
        raise ValueError("Unsupported opportunity card format.")
    allowed_methods = {
        "hold", "native-staking", "centralized-lending", "defi-lending",
        "stablecoin-yield", "liquidity-provision",
    }
    if card.get("method_id") not in allowed_methods:
        raise ValueError("Select a known yield mechanism.")
    result = {"version": 1, "method_id": card["method_id"]}
    for key, limit, required in (
        ("name", 100, True), ("protocol", 100, True), ("asset", 80, True),
        ("chain", 80, False), ("source_url", 500, True),
        ("withdrawal_terms", 1000, False), ("risk_notes", 1000, False),
        ("reward_source", 1000, False),
    ):
        value = card.get(key, "")
        if not isinstance(value, str) or len(value) > limit or (required and not value.strip()):
            raise ValueError(f"Invalid or missing card field: {key}.")
        result[key] = value.strip()
    url = urlparse(result["source_url"])
    if url.scheme not in ("https", "http") or not url.hostname or url.username or url.password:
        raise ValueError("Source must be a valid HTTP(S) URL without credentials.")
    checked = card.get("checked_on", "")
    if not isinstance(checked, str):
        raise ValueError("Verification date must be a string.")
    try:
        day = date.fromisoformat(checked)
        if day.isoformat() != checked or day > date.today():
            raise ValueError
    except ValueError:
        raise ValueError("Use a valid non-future verification date (YYYY-MM-DD).") from None
    result["checked_on"] = checked
    apr = card.get("observed_apr_pct")
    if apr is not None:
        if isinstance(apr, bool) or not isinstance(apr, (int, float)) or not math.isfinite(apr) or not 0 <= apr <= 1000:
            raise ValueError("Observed APR must be between 0 and 1000 percent.")
        apr = float(apr)
    result["observed_apr_pct"] = apr
    return result


def opportunity_card_quality(card: dict) -> dict:
    validated = validate_opportunity_card(card)
    missing = [
        label for key, label in (
            ("chain", "Network/chain"),
            ("withdrawal_terms", "Withdrawal and lock-up terms"),
            ("risk_notes", "Risk notes"),
            ("reward_source", "Source of rewards"),
        ) if not validated[key]
    ]
    if validated["observed_apr_pct"] is None:
        missing.append("Observed APR (optional; not a safety indicator)")
    return {"complete_fields": 5 - len(missing), "total_fields": 5, "missing": missing}


def build_opportunity_table(cards: list[dict]) -> list[dict]:
    if not isinstance(cards, list) or len(cards) > 50:
        raise ValueError("At most 50 research cards are supported.")
    rows = []
    for card in cards:
        entry = validate_opportunity_card(card)
        quality = opportunity_card_quality(entry)
        rows.append({
            "Opportunity": entry["name"],
            "Protocol / provider": entry["protocol"],
            "Method": entry["method_id"],
            "Asset": entry["asset"],
            "Chain": entry["chain"],
            "Observed APR (%)": entry["observed_apr_pct"],
            "Checked on": entry["checked_on"],
            "Documented fields": f"{quality['complete_fields']}/{quality['total_fields']}",
            "Source": entry["source_url"],
            "Withdrawal terms": entry["withdrawal_terms"],
            "Risks": entry["risk_notes"],
        })
    return rows
