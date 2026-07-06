"""
alerts.py
Turns a forecasted inventory DataFrame into actionable alert groups:
critical stockouts, upcoming reorders, overstock risk, and cost/profit
summaries. Kept independent of any presentation layer so it can be
tested or reused (e.g. from a web API) without pulling in Rich or CLI code.
"""

import pandas as pd


def critical_items(df: pd.DataFrame) -> pd.DataFrame:
    """Items that will stock out before a new order could arrive."""
    return df[df["status"] == "CRITICAL"].sort_values("revenue_at_risk", ascending=False)


def reorder_items(df: pd.DataFrame) -> pd.DataFrame:
    """Items approaching their reorder point, but not yet critical."""
    return df[df["status"] == "REORDER"].sort_values("days_until_stockout")


def overstock_items(df: pd.DataFrame) -> pd.DataFrame:
    """Items with excessive stock cover, at risk of wastage/dead stock."""
    return df[df["status"] == "OVERSTOCK"].sort_values("days_until_stockout", ascending=False)


def healthy_items(df: pd.DataFrame) -> pd.DataFrame:
    """Items currently at a healthy stock level."""
    return df[df["status"] == "OK"]


def top_profit_items(df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
    """The n most profitable products by daily profit."""
    return df.nlargest(n, "daily_profit")


def cost_summary(df: pd.DataFrame) -> dict:
    """
    Aggregate figures used for the dashboard's summary panel and for
    the daily report: total spend needed to clear reorder alerts,
    revenue at risk, and overall profit potential.
    """
    reorder_needed = df[df["needs_reorder"]]
    return {
        "total_products": len(df),
        "critical_count": len(critical_items(df)),
        "reorder_count": len(reorder_items(df)),
        "overstock_count": len(overstock_items(df)),
        "healthy_count": len(healthy_items(df)),
        "budget_needed": reorder_needed["total_reorder_cost"].sum(),
        "revenue_at_risk": df["revenue_at_risk"].sum(),
        "monthly_profit_potential": df["monthly_profit_potential"].sum(),
    }


def build_alert_report(df: pd.DataFrame) -> dict:
    """
    Bundles everything the presentation layer (CLI dashboard / CSV export)
    needs into a single structure, so agent.py doesn't have to know about
    the underlying DataFrame logic at all.
    """
    return {
        "summary": cost_summary(df),
        "critical": critical_items(df),
        "reorder": reorder_items(df),
        "overstock": overstock_items(df),
        "top_profit": top_profit_items(df, 5),
    }
