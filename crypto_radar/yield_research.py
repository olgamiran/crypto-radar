"""Static educational catalogue of crypto yield mechanisms and their risks.

This module intentionally contains no live APY figures or product endorsements.
"""
from __future__ import annotations

from typing import Any

_YIELD_METHODS: tuple[dict[str, str], ...] = (
    {
        "id": "hold",
        "name": "Buy and hold",
        "category": "Baseline",
        "reward_source": "No yield; the result comes from the asset price changing.",
        "liquidity": "Usually liquid, subject to market and platform access.",
        "risk_level": "Market risk",
        "key_risks": "Price volatility, custody risk if held with a provider, lost keys if self-custodied.",
        "what_to_verify": "Asset fundamentals, custody arrangements, fees, and how the price is measured.",
    },
    {
        "id": "native-staking",
        "name": "Native staking",
        "category": "Staking",
        "reward_source": "Protocol rewards for helping secure a proof-of-stake network.",
        "liquidity": "Unbonding delays or lock-ups may apply; rules vary by network and provider.",
        "risk_level": "High",
        "key_risks": "Token price decline, slashing, validator downtime, lock-up and provider/custody risk.",
        "what_to_verify": "Network rules, unbonding period, validator commission, slashing policy, and custody model.",
    },
    {
        "id": "centralized-lending",
        "name": "Centralized crypto lending",
        "category": "Lending",
        "reward_source": "A provider lends assets to borrowers and may share interest with customers.",
        "liquidity": "Withdrawals can be limited, delayed, or suspended under stress.",
        "risk_level": "Very high",
        "key_risks": "Counterparty insolvency, rehypothecation, withdrawal restrictions, custody and legal risk.",
        "what_to_verify": "Who borrows the assets, how they are reused, withdrawal terms, legal entity, and applicable protections.",
    },
    {
        "id": "defi-lending",
        "name": "DeFi lending",
        "category": "Lending",
        "reward_source": "Borrower interest and protocol incentives in a smart-contract market.",
        "liquidity": "Depends on pool liquidity, utilization, network conditions, and contract rules.",
        "risk_level": "Very high",
        "key_risks": "Smart-contract exploits, oracle failures, liquidation cascades, variable rates, and token risk.",
        "what_to_verify": "Audits and their scope, oracle design, collateral rules, liquidity, admin keys, and incident history.",
    },
    {
        "id": "stablecoin-yield",
        "name": "Stablecoin yield products",
        "category": "Stablecoins",
        "reward_source": "May come from lending, reserves, liquidity provision, or protocol incentives.",
        "liquidity": "Depends on redemption terms, pool depth, provider, and the underlying strategy.",
        "risk_level": "High to very high",
        "key_risks": "Depeg, issuer/reserve risk, borrower or platform failure, smart contracts, and changing rewards.",
        "what_to_verify": "What actually generates yield, redemption rights, reserve disclosures, counterparties, and depeg history.",
    },
    {
        "id": "liquidity-provision",
        "name": "DeFi liquidity provision",
        "category": "Liquidity provision",
        "reward_source": "A share of trading fees and sometimes temporary token incentives.",
        "liquidity": "Withdrawal depends on pool mechanics and available liquidity.",
        "risk_level": "Very high",
        "key_risks": "Impermanent loss, smart-contract exploits, volatile incentives, pool imbalance, and token risk.",
        "what_to_verify": "Pool composition, fee history, incentive expiry, contract audits, and outcomes versus simply holding.",
    },
)


def get_research_methods(category: str | None = None) -> list[dict[str, str]]:
    """Return catalogue entries, optionally filtered by category.

    Values are general educational descriptions, not live offers or endorsements.
    """
    methods = [dict(item) for item in _YIELD_METHODS]
    if category and category != "All":
        methods = [item for item in methods if item["category"] == category]
    return methods


def get_categories() -> list[str]:
    """Return available category filters in stable display order."""
    return ["All", *dict.fromkeys(item["category"] for item in _YIELD_METHODS)]
