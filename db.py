"""
db.py
Lightweight SQLite persistence layer. Stores:
  - chat history, so conversations survive a page refresh / app restart
  - inventory snapshots over time, so trends (e.g. "how did critical
    count change this week") can be tracked rather than only ever
    showing a single live moment.

SQLite is used deliberately here instead of a heavier database — it's
a single file (stockmind.db), needs no separate server process, and is
genuinely appropriate for a single-store/single-user inventory tool.
Swapping this for Postgres later would only require changing the
connection logic in this file; nothing else in the app depends on it.
"""

import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path(__file__).parent / "stockmind.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT NOT NULL,
            total_products INTEGER,
            critical_count INTEGER,
            reorder_count INTEGER,
            overstock_count INTEGER,
            healthy_count INTEGER,
            budget_needed REAL,
            revenue_at_risk REAL,
            monthly_profit_potential REAL
        )
    """)
    conn.commit()
    conn.close()


def save_chat_message(session_id: str, role: str, content: str):
    conn = get_connection()
    conn.execute(
        "INSERT INTO chat_messages (session_id, role, content, created_at) VALUES (?, ?, ?, ?)",
        (session_id, role, content, datetime.now().isoformat())
    )
    conn.commit()
    conn.close()


def get_chat_history(session_id: str) -> list:
    conn = get_connection()
    rows = conn.execute(
        "SELECT role, content FROM chat_messages WHERE session_id = ? ORDER BY id ASC",
        (session_id,)
    ).fetchall()
    conn.close()
    return [{"role": r["role"], "content": r["content"]} for r in rows]


def clear_chat_history(session_id: str):
    conn = get_connection()
    conn.execute("DELETE FROM chat_messages WHERE session_id = ?", (session_id,))
    conn.commit()
    conn.close()


def save_snapshot(summary: dict):
    """Records a point-in-time snapshot of the inventory summary, so
    trends can be charted over multiple runs/days."""
    conn = get_connection()
    conn.execute("""
        INSERT INTO snapshots (
            created_at, total_products, critical_count, reorder_count,
            overstock_count, healthy_count, budget_needed, revenue_at_risk,
            monthly_profit_potential
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().isoformat(),
        summary["total_products"], summary["critical_count"], summary["reorder_count"],
        summary["overstock_count"], summary["healthy_count"], summary["budget_needed"],
        summary["revenue_at_risk"], summary["monthly_profit_potential"],
    ))
    conn.commit()
    conn.close()


def get_snapshot_history(limit: int = 100):
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM snapshots ORDER BY created_at ASC LIMIT ?",
        (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


init_db()
