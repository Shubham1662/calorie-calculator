"""14-day trend aggregation and chart building."""

from datetime import date, timedelta

import altair as alt
import pandas as pd

# Validated chart palette (see ARCHITECTURE.md)
BAR_UNDER = "#2a78d6"   # at/under target
BAR_OVER = "#d03b3b"    # over target
TARGET_RULE = "#898781"  # muted ink, readable on light and dark surfaces


def daily_totals_14d(log: pd.DataFrame, today: date | None = None) -> pd.DataFrame:
    """Total calories per day for the last 14 days, missing days filled with 0."""
    today = today or date.today()
    days = [today - timedelta(days=i) for i in range(13, -1, -1)]
    frame = pd.DataFrame({"date": [d.isoformat() for d in days]})
    totals = log.groupby("date", as_index=False)["calories"].sum()
    frame = frame.merge(totals, on="date", how="left").fillna({"calories": 0})
    frame["day"] = pd.to_datetime(frame["date"]).dt.strftime("%d %b")
    return frame


def trend_chart(totals: pd.DataFrame, target: int) -> alt.Chart:
    """Bar chart of daily intake vs. the target line, sized for a phone screen."""
    totals = totals.copy()
    totals["status"] = totals["calories"].apply(
        lambda c: "Over target" if c > target else "Under target"
    )
    bars = (
        alt.Chart(totals)
        .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4, size=14)
        .encode(
            x=alt.X("day:N", sort=None, title=None,
                    axis=alt.Axis(labelAngle=-45, labelFontSize=10)),
            y=alt.Y("calories:Q", title="kcal"),
            color=alt.Color(
                "status:N",
                scale=alt.Scale(domain=["Under target", "Over target"],
                                range=[BAR_UNDER, BAR_OVER]),
                legend=alt.Legend(title=None, orient="top"),
            ),
            tooltip=[
                alt.Tooltip("day:N", title="Day"),
                alt.Tooltip("calories:Q", title="kcal", format=".0f"),
            ],
        )
    )
    rule = (
        alt.Chart(pd.DataFrame({"target": [target]}))
        .mark_rule(color=TARGET_RULE, strokeDash=[5, 4], size=2)
        .encode(y="target:Q")
    )
    return (bars + rule).properties(height=300)
