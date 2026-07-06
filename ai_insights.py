"""
ai_insights.py
Uses Groq's API to turn the raw forecasting/alerts numbers into a short,
plain-English briefing — the "AI" part of StockMind AI. Kept in its own
module so the rest of the app (forecasting, alerts, CLI dashboard) works
perfectly fine even if this fails or the API key isn't set.
"""

import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

MODEL = "openai/gpt-oss-120b"  # current Groq model; update if Groq deprecates it


def _get_client():
    api_key = os.environ.get("GROQ_API_KEY")

    # When deployed on Streamlit Community Cloud, secrets are provided
    # via st.secrets rather than a .env file. Fall back to that if the
    # env var isn't set and streamlit is available.
    if not api_key:
        try:
            import streamlit as st
            api_key = st.secrets.get("GROQ_API_KEY")
        except Exception:
            pass

    if not api_key:
        return None
    return Groq(api_key=api_key)


def build_prompt(report: dict) -> str:
    """Builds a compact prompt from the alerts report so we send Groq a
    short summary of the numbers rather than the whole inventory table."""
    summary = report["summary"]
    critical = report["critical"]
    reorder = report["reorder"]
    top_profit = report["top_profit"]

    crit_lines = "\n".join(
        f"  - {r.product_name}: {r.current_stock} {r.unit} left, "
        f"{r.days_until_stockout:.1f} days, order {int(r.optimal_order_qty)}, "
        f"cost Rs {r.total_reorder_cost:,.0f}"
        for _, r in critical.iterrows()
    ) or "  None"

    reorder_lines = "\n".join(
        f"  - {r.product_name}: {r.days_until_stockout:.1f} days left"
        for _, r in reorder.head(10).iterrows()
    ) or "  None"

    profit_lines = "\n".join(
        f"  - {r.product_name}: Rs {r.daily_profit:.0f}/day"
        for _, r in top_profit.iterrows()
    )

    return f"""You are StockMind, an AI inventory management assistant.

Total products: {summary['total_products']} | Critical: {summary['critical_count']} | Reorder soon: {summary['reorder_count']} | Healthy: {summary['healthy_count']}

CRITICAL ITEMS (order today):
{crit_lines}

REORDER SOON:
{reorder_lines}

TOP PROFIT ITEMS:
{profit_lines}

Budget needed for reorders: Rs {summary['budget_needed']:,.0f}
Monthly profit potential: Rs {summary['monthly_profit_potential']:,.0f}
Revenue at risk from stockouts: Rs {summary['revenue_at_risk']:,.0f}

Write a short (4-6 sentence) plain-English briefing a store owner could
read in 30 seconds. Mention the most urgent action, the budget needed,
and one profit opportunity. Use **bold** for key numbers. Be direct and
practical, no fluff."""


def generate_insight(report: dict) -> str:
    """
    Returns a short AI-generated briefing string, or a clear fallback
    message if the API key is missing or the request fails — this
    should never crash the rest of the agent.
    """
    client = _get_client()
    if client is None:
        return ("⚠️ AI insights unavailable: GROQ_API_KEY not found. "
                "Add it to your .env file to enable AI-generated summaries.")

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "user", "content": build_prompt(report)}],
            temperature=0.3,
            max_tokens=400,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ AI insight generation failed: {e}"


def chat_reply(report: dict, conversation: list) -> str:
    """
    Multi-turn chat, grounded in the current inventory data. `conversation`
    is a list of {"role": "user"/"assistant", "content": ...} dicts (the
    running chat history, most recent message last). The live inventory
    numbers are injected as the system prompt on every call, so answers
    stay accurate even as stock levels change between messages.
    """
    client = _get_client()
    if client is None:
        return ("⚠️ AI chat unavailable: GROQ_API_KEY not found. "
                "Add it to your .env file to enable chat.")

    system_prompt = build_prompt(report) + (
        "\n\nYou're now chatting directly with the store owner. Answer their "
        "specific question using the data above. Give specific numbers. "
        "Use **bold** for key figures. Be concise and actionable."
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{"role": "system", "content": system_prompt}] + conversation,
            temperature=0.35,
            max_tokens=800,
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"⚠️ AI error: {e}"
