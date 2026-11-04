"""Simple, assumption-based calculator for hypothetical crypto income."""
from __future__ import annotations


def calculate_income_scenario(
    principal: float,
    apr_pct: float,
    months: int,
    price_change_pct: float = 0.0,
    fee_pct: float = 0.0,
) -> dict[str, float]:
    """Estimate a hypothetical yield scenario; this is not a forecast.

    APR is treated as a nominal annual rate compounded monthly. The asset-price
    change is applied to principal plus rewards. Fee is a one-off percentage of
    the starting principal. Taxes, changing rates, lockups, defaults, depegs,
    and protocol/provider failures are not modeled.
    """
    if principal < 0:
        raise ValueError("Principal must be zero or greater.")
    if apr_pct < 0:
        raise ValueError("APR must be zero or greater.")
    if months < 0:
        raise ValueError("Months must be zero or greater.")
    if fee_pct < 0 or fee_pct >= 100:
        raise ValueError("Fee must be at least 0 and less than 100 percent.")
    if price_change_pct < -100:
        raise ValueError("Asset price change cannot be below -100 percent.")

    monthly_rate = (apr_pct / 100) / 12
    rewards = principal * ((1 + monthly_rate) ** months - 1)
    gross_balance = principal + rewards
    value_after_price_change = gross_balance * (1 + price_change_pct / 100)
    fees = principal * fee_pct / 100
    ending_value = max(value_after_price_change - fees, 0.0)

    return {
        "principal": float(principal),
        "rewards": float(rewards),
        "fees": float(fees),
        "ending_value": float(ending_value),
        "profit_loss": float(ending_value - principal),
        "return_pct": float((ending_value / principal - 1) * 100) if principal else 0.0,
    }


def build_scenarios(
    principal: float,
    apr_pct: float,
    months: int,
    fee_pct: float = 0.0,
) -> list[dict[str, float]]:
    """Compare the same hypothetical yield under several asset-price changes."""
    scenarios = []
    for price_change in (-50.0, -20.0, 0.0, 20.0):
        row = calculate_income_scenario(
            principal=principal,
            apr_pct=apr_pct,
            months=months,
            price_change_pct=price_change,
            fee_pct=fee_pct,
        )
        row["asset_price_change_pct"] = price_change
        scenarios.append(row)
    return scenarios


def compare_income_methods(
    principal: float,
    months: int,
    price_change_pct: float,
    assumptions: list[dict[str, float | str]],
) -> list[dict[str, float | str]]:
    """Compare user-entered hypothetical methods against the same holding baseline.

    Each row has method, apr_pct, fee_pct and optional price_change_pct.
    The per-method price change permits a stablecoin/depeg assumption distinct
    from a volatile asset. No APR or provider data is supplied by this model.
    """
    import math

    if not assumptions:
        raise ValueError("Provide at least one income method.")
    if not math.isfinite(float(principal)) or principal <= 0:
        raise ValueError("Starting virtual balance must be positive and finite.")
    if not isinstance(months, int) or not 1 <= months <= 60:
        raise ValueError("Duration must be between 1 and 60 months.")
    if not math.isfinite(float(price_change_pct)) or price_change_pct < -100:
        raise ValueError("Price change must be finite and at least -100 percent.")
    rows = []
    for item in assumptions:
        name = str(item["method"])
        apr = float(item["apr_pct"])
        fee = float(item["fee_pct"])
        change = float(item.get("price_change_pct", price_change_pct))
        if not name.strip() or not all(map(math.isfinite, (apr, fee, change))):
            raise ValueError("Method names and numeric assumptions must be valid.")
        if not 0 <= apr <= 1000 or not 0 <= fee < 100 or not -100 <= change <= 1000:
            raise ValueError("APR, fees, or asset price change is outside the allowed range.")
        result = calculate_income_scenario(principal, apr, months, change, fee)
        rows.append({
            "Method": name,
            "Assumed APR (%)": apr,
            "Asset price change (%)": change,
            "One-off fee (%)": fee,
            "Virtual rewards ($)": result["rewards"],
            "Virtual ending value ($)": result["ending_value"],
            "Virtual profit / loss ($)": result["profit_loss"],
            "Virtual return (%)": result["return_pct"],
        })
    return rows


def stress_test_income_methods(
    principal: float,
    months: int,
    assumptions: list[dict[str, float | str]],
    apr_cut_pct: float = 50.0,
    price_shock_pct: float = -30.0,
    loss_haircut_pct: float = 25.0,
) -> list[dict[str, float | str]]:
    """Independent hypothetical shocks applied to each method's baseline.

    APR cut is a relative reduction to the assumed APR. Price shock is an
    additional percentage-point change to the method's baseline price change,
    capped at -100%. Loss haircut is a fraction of the final recoverable
    balance; it does not estimate a probability of default.
    """
    import math

    shocks = (float(apr_cut_pct), float(price_shock_pct), float(loss_haircut_pct))
    if not all(map(math.isfinite, shocks)):
        raise ValueError("Stress-test shocks must be finite.")
    if not 0 <= apr_cut_pct <= 100 or not -100 <= price_shock_pct <= 0:
        raise ValueError("APR cut and price shock are outside allowed ranges.")
    if not 0 <= loss_haircut_pct <= 100:
        raise ValueError("Loss haircut must be between 0 and 100 percent.")

    # Reuse comparison validation so the stress test and baseline agree.
    baseline = compare_income_methods(principal, months, 0.0, assumptions)
    results = []
    for item, base in zip(assumptions, baseline):
        apr = float(item["apr_pct"])
        fee = float(item["fee_pct"])
        price = float(item.get("price_change_pct", 0.0))
        scenarios = [
            ("Baseline", apr, price, 0.0),
            ("APR reduction", apr * (1 - apr_cut_pct / 100), price, 0.0),
            ("Additional price decline", apr, max(-100.0, price + price_shock_pct), 0.0),
            ("Partial capital loss", apr, price, loss_haircut_pct),
            ("Combined shocks", apr * (1 - apr_cut_pct / 100),
             max(-100.0, price + price_shock_pct), loss_haircut_pct),
        ]
        for label, scenario_apr, scenario_price, haircut in scenarios:
            modeled = calculate_income_scenario(
                principal, scenario_apr, months, scenario_price, fee
            )
            ending = modeled["ending_value"] * (1 - haircut / 100)
            results.append({
                "Method": str(item["method"]),
                "Scenario": label,
                "APR (%)": scenario_apr,
                "Asset price change (%)": scenario_price,
                "Capital loss haircut (%)": haircut,
                "Virtual ending value ($)": ending,
                "Virtual profit / loss ($)": ending - principal,
                "Virtual return (%)": (ending / principal - 1) * 100,
                "Change vs baseline ($)": ending - float(base["Virtual ending value ($)"]),
            })
    return results


def validate_income_snapshot(snapshot: object) -> dict:
    """Validate portable, versioned virtual-income research snapshots."""
    import math

    if not isinstance(snapshot, dict) or snapshot.get("version") != 1:
        raise ValueError("Unsupported research snapshot format or version.")
    name = snapshot.get("name")
    if not isinstance(name, str) or not 1 <= len(name.strip()) <= 80:
        raise ValueError("Snapshot name must contain 1–80 characters.")
    kind = snapshot.get("kind")
    if kind not in ("comparison", "stress"):
        raise ValueError("Unknown snapshot kind.")
    data = snapshot.get("inputs")
    if not isinstance(data, dict):
        raise ValueError("Snapshot inputs must be an object.")
    if not isinstance(data.get("months"), int) or not 1 <= data["months"] <= 60:
        raise ValueError("Invalid duration.")
    principal = data.get("principal")
    if not isinstance(principal, (int, float)) or isinstance(principal, bool) or not math.isfinite(principal) or not 0 < principal <= 1e9:
        raise ValueError("Invalid virtual principal.")
    methods = data.get("methods")
    if not isinstance(methods, list) or not 1 <= len(methods) <= 10:
        raise ValueError("Snapshot must contain 1–10 methods.")
    clean_methods = []
    for item in methods:
        if not isinstance(item, dict) or not isinstance(item.get("method"), str) or not 1 <= len(item["method"].strip()) <= 80:
            raise ValueError("Invalid method name.")
        values = {}
        for key, minimum, maximum in (("apr_pct", 0, 1000), ("fee_pct", 0, 99.999), ("price_change_pct", -100, 1000)):
            value = item.get(key)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or not minimum <= value <= maximum:
                raise ValueError(f"Invalid method assumption: {key}.")
            values[key] = float(value)
        clean_methods.append({"method": item["method"].strip(), **values})
    cleaned = {"principal": float(principal), "months": data["months"], "methods": clean_methods}
    if kind == "stress":
        for key, minimum, maximum in (("apr_cut_pct", 0, 100), ("price_shock_pct", -100, 0), ("loss_haircut_pct", 0, 100)):
            value = data.get(key)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value) or not minimum <= value <= maximum:
                raise ValueError(f"Invalid stress assumption: {key}.")
            cleaned[key] = float(value)
    return {"version": 1, "name": name.strip(), "kind": kind, "inputs": cleaned}


def evaluate_income_snapshot(snapshot: dict) -> list[dict]:
    """Recompute saved research from assumptions, never trust stored outcomes."""
    saved = validate_income_snapshot(snapshot)
    data = saved["inputs"]
    if saved["kind"] == "stress":
        return stress_test_income_methods(
            data["principal"], data["months"], data["methods"],
            data["apr_cut_pct"], data["price_shock_pct"], data["loss_haircut_pct"],
        )
    return compare_income_methods(data["principal"], data["months"], 0.0, data["methods"])


def build_income_research_journal(snapshots: list[dict]) -> list[dict]:
    """Flatten saved hypothetical research into comparable, clearly scoped rows.

    A comparison method yields one baseline row. A stress experiment yields
    baseline and combined-shock rows. Different principal/duration assumptions
    are displayed rather than silently treated as comparable dollar outcomes.
    """
    if not isinstance(snapshots, list) or len(snapshots) > 30:
        raise ValueError("Research journal supports up to 30 snapshots.")
    rows = []
    for index, raw in enumerate(snapshots, start=1):
        snapshot = validate_income_snapshot(raw)
        inputs = snapshot["inputs"]
        for outcome in evaluate_income_snapshot(snapshot):
            scenario = outcome.get("Scenario", "Baseline")
            if scenario not in ("Baseline", "Combined shocks"):
                continue
            rows.append({
                "Saved #": index,
                "Research name": snapshot["name"],
                "Kind": snapshot["kind"],
                "Method": outcome["Method"],
                "Scenario": scenario,
                "Starting balance ($)": inputs["principal"],
                "Duration (months)": inputs["months"],
                "Assumed APR (%)": outcome.get("APR (%)", outcome.get("Assumed APR (%)")),
                "Asset price change (%)": outcome["Asset price change (%)"],
                "Ending value ($)": outcome["Virtual ending value ($)"],
                "Profit / loss ($)": outcome["Virtual profit / loss ($)"],
                "Return (%)": outcome["Virtual return (%)"],
            })
    return rows


def assess_income_research_quality(snapshot: dict) -> dict:
    """Check documentation completeness, not investment merit or safety.

    Metadata is optional and kept outside calculation inputs so older JSON
    snapshots remain valid. Missing evidence never becomes an invented source.
    """
    saved = validate_income_snapshot(snapshot)
    evidence = snapshot.get("research", {})
    if not isinstance(evidence, dict):
        raise ValueError("Research metadata must be an object.")
    fields = ("assumption_source", "checked_on", "withdrawal_terms", "risk_notes")
    supplied = {}
    for field in fields:
        value = evidence.get(field, "")
        if not isinstance(value, str) or len(value) > 1000:
            raise ValueError(f"Invalid research field: {field}.")
        supplied[field] = value.strip()
    warnings = []
    for field, description in (
        ("assumption_source", "Document where the APR and fee assumptions came from."),
        ("checked_on", "Record when the assumptions were checked (YYYY-MM-DD)."),
        ("withdrawal_terms", "Document withdrawal restrictions or lock-up conditions."),
        ("risk_notes", "Document key loss, custody and protocol risks."),
    ):
        if not supplied[field]:
            warnings.append(description)
    if supplied["checked_on"]:
        from datetime import date
        try:
            checked = date.fromisoformat(supplied["checked_on"])
            if checked.isoformat() != supplied["checked_on"] or checked > date.today():
                raise ValueError
        except ValueError:
            warnings.append("Use a valid, non-future YYYY-MM-DD verification date.")
    if saved["kind"] == "comparison":
        warnings.append("No combined-shock stress scenario is included in this saved comparison.")
    for method in saved["inputs"]["methods"]:
        if method["apr_pct"] > 30:
            warnings.append(f"{method['method']}: APR above 30% needs extra verification; this is not a risk score.")
    completed = sum(bool(supplied[field]) for field in fields)
    return {
        "name": saved["name"],
        "kind": saved["kind"],
        "documented_fields": completed,
        "total_fields": len(fields),
        "has_stress_test": saved["kind"] == "stress",
        "warnings": warnings,
        "documentation_status": "Documented" if completed == len(fields) and not warnings else "Needs review",
    }
