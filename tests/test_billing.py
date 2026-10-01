import pandas as pd
import pytest

from src.megaline_analytics import calculate_billing


def test_billing_rounds_calls_and_data_and_clips_overages():
    monthly = pd.DataFrame(
        [
            {
                "user_id": 1,
                "year_month": "2018-01",
                "plan": "surf",
                "city": "Test",
                "billable_minutes": 501,
                "message_count": 51,
                "mb_used": 15361,
            }
        ]
    )
    plans = pd.DataFrame(
        [
            {
                "plan_name": "surf",
                "messages_included": 50,
                "mb_per_month_included": 15360,
                "minutes_included": 500,
                "usd_monthly_pay": 20,
                "usd_per_gb": 10,
                "usd_per_message": 0.03,
                "usd_per_minute": 0.03,
            }
        ]
    )
    result = calculate_billing(monthly, plans).iloc[0]
    assert result["gb_used"] == 16
    assert result["extra_minutes"] == 1
    assert result["extra_messages"] == 1
    assert result["extra_gb"] == 1
    assert result["monthly_revenue"] == pytest.approx(30.06)


def test_billing_does_not_charge_under_allowance():
    monthly = pd.DataFrame(
        [
            {
                "user_id": 1,
                "year_month": "2018-01",
                "plan": "surf",
                "city": "Test",
                "billable_minutes": 400,
                "message_count": 20,
                "mb_used": 1000,
            }
        ]
    )
    plans = pd.DataFrame(
        [
            {
                "plan_name": "surf",
                "messages_included": 50,
                "mb_per_month_included": 15360,
                "minutes_included": 500,
                "usd_monthly_pay": 20,
                "usd_per_gb": 10,
                "usd_per_message": 0.03,
                "usd_per_minute": 0.03,
            }
        ]
    )
    result = calculate_billing(monthly, plans).iloc[0]
    assert result["monthly_revenue"] == 20
