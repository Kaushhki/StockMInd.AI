"""
agent.py
The presentation + orchestration layer. Renders the CLI dashboard with
Rich, exports daily reports to CSV, and runs the whole thing on an
automated daily schedule using the `schedule` library.

Run once immediately:
    python agent.py --once

Run continuously on a daily schedule (default 08:00):
    python agent.py --daily-at 08:00
"""

import argparse
import time
from datetime import datetime
from pathlib import Path

import schedule
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.align import Align

from forecasting import load_data
from alerts import build_alert_report
from ai_insights import generate_insight
import db

console = Console()

REPORTS_DIR = Path("reports")


def render_summary_panel(summary: dict) -> Panel:
    text = (
        f"[bold]{summary['total_products']}[/bold] products tracked   "
        f"[red]{summary['critical_count']} critical[/red]   "
        f"[yellow]{summary['reorder_count']} reorder soon[/yellow]   "
        f"[magenta]{summary['overstock_count']} overstock[/magenta]   "
        f"[green]{summary['healthy_count']} healthy[/green]\n\n"
        f"[bold red]Revenue at risk:[/bold red] Rs {summary['revenue_at_risk']:,.0f}    "
        f"[bold green]Monthly profit potential:[/bold green] Rs {summary['monthly_profit_potential']:,.0f}    "
        f"[bold]Reorder budget needed:[/bold] Rs {summary['budget_needed']:,.0f}"
    )
    return Panel(Align.left(text), title="Inventory Status", border_style="blue")


def render_critical_table(df) -> Table:
    table = Table(title="🚨 Critical Stockouts — Order Today", border_style="red")
    table.add_column("Product")
    table.add_column("Stock", justify="right")
    table.add_column("Days Left", justify="right")
    table.add_column("Order Qty", justify="right")
    table.add_column("Order Cost (Rs)", justify="right")
    table.add_column("Revenue at Risk (Rs)", justify="right")

    for _, r in df.iterrows():
        table.add_row(
            r["product_name"],
            f"{r['current_stock']} {r['unit']}",
            f"{r['days_until_stockout']:.1f}",
            str(int(r["optimal_order_qty"])),
            f"{r['total_reorder_cost']:,.0f}",
            f"{r['revenue_at_risk']:,.0f}",
        )
    return table


def render_reorder_table(df) -> Table:
    table = Table(title="🟡 Reorder Soon", border_style="yellow")
    table.add_column("Product")
    table.add_column("Days Left", justify="right")
    table.add_column("Order Qty", justify="right")
    table.add_column("Order Cost (Rs)", justify="right")

    for _, r in df.head(10).iterrows():
        table.add_row(
            r["product_name"],
            f"{r['days_until_stockout']:.1f}",
            str(int(r["optimal_order_qty"])),
            f"{r['total_reorder_cost']:,.0f}",
        )
    return table


def render_top_profit_table(df) -> Table:
    table = Table(title="🏆 Top Profit Items", border_style="green")
    table.add_column("Product")
    table.add_column("Daily Profit (Rs)", justify="right")
    table.add_column("Monthly Profit (Rs)", justify="right")

    for _, r in df.iterrows():
        table.add_row(
            r["product_name"],
            f"{r['daily_profit']:.0f}",
            f"{r['monthly_profit_potential']:,.0f}",
        )
    return table


def render_dashboard(report: dict):
    console.rule(f"[bold blue]Inventory Intelligence — {datetime.now().strftime('%A, %d %B %Y %H:%M')}")
    console.print(render_summary_panel(report["summary"]))
    console.print()

    if report["critical"].empty:
        console.print(Panel("✅ No critical stockouts detected right now.", border_style="green"))
    else:
        console.print(render_critical_table(report["critical"]))
    console.print()

    if not report["reorder"].empty:
        console.print(render_reorder_table(report["reorder"]))
        console.print()

    console.print(render_top_profit_table(report["top_profit"]))
    console.print()

    console.print("[dim]Generating AI briefing...[/dim]")
    insight = generate_insight(report)
    console.print(Panel(insight, title="🤖 StockMind AI Briefing", border_style="cyan"))
    console.print()


def export_csv_report(df, report: dict) -> Path:
    """Writes the full inventory snapshot plus a summary line to a
    timestamped CSV file inside REPORTS_DIR, for downstream use."""
    REPORTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    path = REPORTS_DIR / f"inventory_report_{timestamp}.csv"

    export_cols = [
        "product_id", "product_name", "category", "current_stock", "unit",
        "days_until_stockout", "status", "optimal_order_qty",
        "total_reorder_cost", "daily_profit", "monthly_profit_potential",
        "revenue_at_risk",
    ]
    df[export_cols].to_csv(path, index=False)
    console.print(f"[dim]Report exported to {path}[/dim]")
    return path


def run_agent(csv_path=None):
    """One full cycle: load data, forecast, build alerts, render, export."""
    df = load_data(csv_path)
    report = build_alert_report(df)
    render_dashboard(report)
    export_csv_report(df, report)
    db.save_snapshot(report["summary"])


def run_scheduled(daily_at: str, csv_path=None):
    console.print(f"[bold]Scheduler started[/bold] — running daily at {daily_at}. Press Ctrl+C to stop.")
    schedule.every().day.at(daily_at).do(run_agent, csv_path=csv_path)

    # Run once immediately so you don't have to wait until the scheduled
    # time to see the first report.
    run_agent(csv_path)

    while True:
        schedule.run_pending()
        time.sleep(30)


def main():
    parser = argparse.ArgumentParser(description="Automated inventory forecasting agent.")
    parser.add_argument("--once", action="store_true", help="Run a single forecast cycle and exit.")
    parser.add_argument("--daily-at", metavar="HH:MM", default=None,
                         help="Run continuously, once per day at this time (e.g. 08:00).")
    parser.add_argument("--csv", metavar="PATH", default=None,
                         help="Path to a custom inventory CSV. Defaults to the bundled sample data.")
    args = parser.parse_args()

    if args.daily_at:
        run_scheduled(args.daily_at, csv_path=args.csv)
    else:
        # Default behavior (including --once, or no flags at all): run one cycle.
        run_agent(csv_path=args.csv)


if __name__ == "__main__":
    main()
