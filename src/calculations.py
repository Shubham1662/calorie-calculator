"""Calorie calculation layer — pure functions, no I/O."""

import pandas as pd


def calories_for(calories_per_serving: float, quantity: float) -> float:
    return calories_per_serving * quantity


def entries_for_date(log: pd.DataFrame, date: str) -> pd.DataFrame:
    """All log entries for one ISO date, keeping the original row index."""
    return log[log["date"] == date]


def total_for_date(log: pd.DataFrame, date: str) -> float:
    return float(entries_for_date(log, date)["calories"].sum())


def remaining(target: int, consumed: float) -> float:
    return target - consumed
