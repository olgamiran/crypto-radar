import pandas as pd

from crypto_radar.data import assess_price_data


def test_assess_price_data_reports_gaps_duplicates_and_invalid_closes():
    index = pd.to_datetime([
        "2026-01-01", "2026-01-02", "2026-01-02", "2026-01-05", "2026-01-06"
    ])
    prices = pd.DataFrame({"Close": [10, 11, 12, 0, None]}, index=index)

    result = assess_price_data(prices)

    assert result["bars"] == 5
    assert result["start_date"] == "2026-01-01"
    assert result["end_date"] == "2026-01-06"
    assert result["duplicate_timestamps"] == 1
    assert result["missing_calendar_days"] == 2
    assert result["max_gap_days"] == 3
    assert result["invalid_close_rows"] == 2


def test_assess_price_data_handles_empty_input():
    result = assess_price_data(pd.DataFrame())

    assert result["bars"] == 0
    assert result["start_date"] is None
    assert result["latest_age_days"] is None
