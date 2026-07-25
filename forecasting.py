

import math
from pathlib import Path
import pandas as pd

CATEGORY_MARGINS = {
    "Grains": 0.12, "Pulses": 0.14, "Oils": 0.16, "Dairy": 0.18,
    "Spices": 0.25, "Condiments": 0.22, "Snacks": 0.28, "Breakfast": 0.20,
    "Bakery": 0.30, "Noodles": 0.24, "Soups": 0.26, "Beverages": 0.22,
    "Health Drinks": 0.18, "Personal Care": 0.20, "Household": 0.18,
    "Vegetables": 0.35, "Frozen": 0.22, "Stationery": 0.30, "Health": 0.20,
    "Sweeteners": 0.15,
}
DEFAULT_MARGIN = 0.20


ORDERING_COST = 50
HOLDING_RATE = 0.20

DEFAULT_DATA_PATH = Path(__file__).parent / "data" / "sample_inventory.csv"

REQUIRED_COLUMNS = {
    "product_id", "product_name", "category", "current_stock", "unit",
    "reorder_point", "reorder_quantity", "unit_cost", "lead_time_days",
    "daily_sales_avg",
}


class InventoryDataError(ValueError):
    """Raised when uploaded/loaded inventory data doesn't match the
    expected schema, so callers can show a clear message instead of a
    confusing pandas traceback."""
    pass


def calculate_eoq(annual_demand, ordering_cost, holding_cost_per_unit):
    if holding_cost_per_unit <= 0 or annual_demand <= 0:
        return 0
    return math.sqrt((2 * annual_demand * ordering_cost) / holding_cost_per_unit)


def _validate_columns(df: pd.DataFrame):
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise InventoryDataError(
            f"Missing required column(s): {', '.join(sorted(missing))}. "
            f"Expected columns: {', '.join(sorted(REQUIRED_COLUMNS))}."
        )


def load_data(source=None) -> pd.DataFrame:
    

    if source is None:
        source = DEFAULT_DATA_PATH

    try:
        df = pd.read_csv(source)
    except Exception as e:
        raise InventoryDataError(f"Could not read CSV: {e}")

    _validate_columns(df)

    numeric_cols = ["current_stock", "reorder_point", "reorder_quantity",
                     "unit_cost", "lead_time_days", "daily_sales_avg"]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    if df[numeric_cols].isnull().any().any():
        bad_rows = df[df[numeric_cols].isnull().any(axis=1)]["product_id"].tolist()
        raise InventoryDataError(
            f"Non-numeric or missing values found in numeric columns for product(s): "
            f"{', '.join(map(str, bad_rows))}"
        )

    df["days_until_stockout"] = df.apply(
        lambda r: r["current_stock"] / r["daily_sales_avg"] if r["daily_sales_avg"] > 0 else 999,
        axis=1
    )
    df["needs_reorder"] = df["days_until_stockout"] <= df["lead_time_days"] * 1.5

    df["annual_demand"] = df["daily_sales_avg"] * 365
    df["holding_cost_per_unit"] = df["unit_cost"] * HOLDING_RATE
    df["eoq"] = df.apply(
        lambda r: calculate_eoq(r["annual_demand"], ORDERING_COST, r["holding_cost_per_unit"]),
        axis=1
    )
    df["optimal_order_qty"] = df.apply(
        lambda r: max(int(round(r["eoq"])), int(r["reorder_quantity"])),
        axis=1
    )
    df["total_reorder_cost"] = df["optimal_order_qty"] * df["unit_cost"]

    df["margin_pct"] = df["category"].map(lambda c: CATEGORY_MARGINS.get(c, DEFAULT_MARGIN))
    df["selling_price"] = df["unit_cost"] * (1 + df["margin_pct"])
    df["daily_profit"] = (df["selling_price"] - df["unit_cost"]) * df["daily_sales_avg"]
    df["monthly_profit_potential"] = df["daily_profit"] * 30

    df["revenue_at_risk"] = df.apply(
        lambda r: r["selling_price"] * r["daily_sales_avg"] *
                  max(0, r["lead_time_days"] - r["days_until_stockout"]),
        axis=1
    )

    df["status"] = df.apply(_classify_status, axis=1)
    return df


def _classify_status(row) -> str:
    if row["days_until_stockout"] <= row["lead_time_days"]:
        return "CRITICAL"
    elif row["needs_reorder"]:
        return "REORDER"
    elif row["days_until_stockout"] > 90:
        return "OVERSTOCK"
    return "OK"
