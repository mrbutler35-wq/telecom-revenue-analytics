"""Reusable data preparation, billing, and statistical analysis helpers."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
from scipy import stats


DATA_FILES = {
    "users": "megaline_users.csv",
    "calls": "megaline_calls.csv",
    "messages": "megaline_messages.csv",
    "internet": "megaline_internet.csv",
    "plans": "megaline_plans.csv",
}


def _find_data_file(data_dir: Path, filename: str) -> Path:
    candidates = [data_dir / filename, data_dir.parent / filename]
    legacy_name = filename.replace(".csv", " (1).csv")
    candidates.extend([data_dir / legacy_name, data_dir.parent / legacy_name])
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(
        f"Could not find {filename}. Put the source file in {data_dir}."
    )


def load_data(data_dir: str | Path = "data") -> dict[str, pd.DataFrame]:
    """Load the five source tables from a local data directory."""
    directory = Path(data_dir)
    users = pd.read_csv(
        _find_data_file(directory, DATA_FILES["users"]),
        parse_dates=["reg_date", "churn_date"],
    )
    calls = pd.read_csv(_find_data_file(directory, DATA_FILES["calls"]))
    messages = pd.read_csv(_find_data_file(directory, DATA_FILES["messages"]))
    internet = pd.read_csv(_find_data_file(directory, DATA_FILES["internet"]))
    plans = pd.read_csv(_find_data_file(directory, DATA_FILES["plans"]))
    return {
        "users": users,
        "calls": calls,
        "messages": messages,
        "internet": internet,
        "plans": plans,
    }


def _month_key(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series).dt.to_period("M").astype(str)


def aggregate_usage(
    users: pd.DataFrame,
    calls: pd.DataFrame,
    messages: pd.DataFrame,
    internet: pd.DataFrame,
) -> pd.DataFrame:
    """Aggregate activity to one row per observed customer-month."""
    calls = calls.copy()
    calls["year_month"] = _month_key(calls["call_date"])
    calls["billable_minutes"] = np.ceil(calls["duration"]).astype(int)
    call_monthly = calls.groupby(["user_id", "year_month"], as_index=False)[
        "billable_minutes"
    ].sum()

    messages = messages.copy()
    messages["year_month"] = _month_key(messages["message_date"])
    message_monthly = messages.groupby(["user_id", "year_month"]).size().reset_index(
        name="message_count"
    )

    internet = internet.copy()
    internet["year_month"] = _month_key(internet["session_date"])
    internet_monthly = internet.groupby(["user_id", "year_month"], as_index=False)[
        "mb_used"
    ].sum()
    internet_monthly = internet_monthly.rename(columns={"mb_used": "mb_used"})

    monthly = call_monthly.merge(
        message_monthly, on=["user_id", "year_month"], how="outer"
    ).merge(internet_monthly, on=["user_id", "year_month"], how="outer")
    monthly = monthly.fillna(
        {"billable_minutes": 0, "message_count": 0, "mb_used": 0}
    )
    monthly[["billable_minutes", "message_count"]] = monthly[
        ["billable_minutes", "message_count"]
    ].astype(int)
    monthly = monthly.merge(
        users[["user_id", "plan", "city"]], on="user_id", how="left", validate="many_to_one"
    )
    if monthly[["plan", "city"]].isna().any().any():
        raise ValueError("Usage rows contain user IDs missing from the users table.")
    return monthly.sort_values(["user_id", "year_month"]).reset_index(drop=True)


def calculate_billing(monthly: pd.DataFrame, plans: pd.DataFrame) -> pd.DataFrame:
    """Apply plan allowances and overage rates to each customer-month."""
    plans = plans.rename(columns={"usd_monthly_pay": "usd_monthly_fee"}).copy()
    result = monthly.merge(
        plans, left_on="plan", right_on="plan_name", how="left", validate="many_to_one"
    )
    if result["usd_monthly_fee"].isna().any():
        raise ValueError("Usage rows contain plans missing from the plans table.")
    result["gb_used"] = np.ceil(result["mb_used"] / 1024).astype(int)
    result["extra_minutes"] = (
        result["billable_minutes"] - result["minutes_included"]
    ).clip(lower=0)
    result["extra_messages"] = (
        result["message_count"] - result["messages_included"]
    ).clip(lower=0)
    result["extra_gb"] = (
        result["gb_used"] - result["mb_per_month_included"] / 1024
    ).clip(lower=0)
    result["revenue_minutes"] = result["extra_minutes"] * result["usd_per_minute"]
    result["revenue_messages"] = result["extra_messages"] * result["usd_per_message"]
    result["revenue_data"] = result["extra_gb"] * result["usd_per_gb"]
    result["monthly_revenue"] = (
        result["usd_monthly_fee"]
        + result["revenue_minutes"]
        + result["revenue_messages"]
        + result["revenue_data"]
    )
    return result


def welch_t_test(
    values_a: Iterable[float], values_b: Iterable[float]
) -> tuple[float, float]:
    """Return Welch's independent two-sample t statistic and p-value."""
    a = pd.Series(values_a).dropna()
    b = pd.Series(values_b).dropna()
    if len(a) < 2 or len(b) < 2:
        raise ValueError("Each test group must contain at least two observations.")
    result = stats.ttest_ind(a, b, equal_var=False)
    return float(result.statistic), float(result.pvalue)


def analyze(data_dir: str | Path = "data") -> tuple[dict[str, pd.DataFrame], pd.DataFrame]:
    """Load, aggregate, and bill the complete local dataset."""
    data = load_data(data_dir)
    monthly = aggregate_usage(
        data["users"], data["calls"], data["messages"], data["internet"]
    )
    return data, calculate_billing(monthly, data["plans"])
