


import streamlit as st
import uuid
from datetime import datetime

from forecasting import load_data, InventoryDataError
from alerts import build_alert_report
from ai_insights import chat_reply
import db

st.set_page_config(
    page_title="StockMind AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)



st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;500;600;700&display=swap');

* { margin: 0; padding: 0; box-sizing: border-box; }

.stApp {
    background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 50%, #0f1419 100%);
    color: #e8eaf6;
    font-family: 'Inter', sans-serif;
}

#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1rem 2rem !important; max-width: 100% !important; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0d1117 0%, #161b22 100%) !important;
    border-right: 2px solid #30363d !important;
}

[data-testid="stSidebar"] * { color: #c9d1d9 !important; }

[data-testid="stSidebar"] .stButton > button {
    background: linear-gradient(135deg, #1f2937 0%, #111827 100%) !important;
    border: 1px solid #374151 !important;
    color: #9ca3af !important;
    border-radius: 10px !important;
    font-size: 0.8rem !important;
    padding: 0.6rem 1rem !important;
    text-align: left !important;
    width: 100% !important;
    transition: all 0.3s ease !important;
    font-weight: 500 !important;
}

[data-testid="stSidebar"] .stButton > button:hover {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
    border-color: #60a5fa !important;
    color: #ffffff !important;
    transform: translateX(5px) !important;
}

[data-testid="stChatMessage"] {
    background: rgba(17, 24, 39, 0.6) !important;
    border: 1px solid rgba(75, 85, 99, 0.3) !important;
    border-radius: 16px !important;
    padding: 1.2rem !important;
    margin-bottom: 0.8rem !important;
}

[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(17,24,39,0.8) 0%, rgba(31,41,55,0.6) 100%) !important;
    border: 1px solid rgba(75,85,99,0.4) !important;
    border-radius: 14px !important;
    padding: 1.2rem !important;
}

[data-testid="stMetricLabel"] {
    color: #9ca3af !important;
    font-size: 0.75rem !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    font-weight: 600 !important;
}

[data-testid="stMetricValue"] {
    color: #f3f4f6 !important;
    font-family: 'Orbitron', monospace !important;
    font-size: 1.8rem !important;
    font-weight: 700 !important;
}

[data-testid="stTabs"] button[aria-selected="true"] {
    color: #3b82f6 !important;
    border-bottom: 3px solid #3b82f6 !important;
}

div[data-testid="stDataFrame"] {
    border: 1px solid rgba(75,85,99,0.3) !important;
    border-radius: 12px !important;
    overflow: hidden;
}
</style>
""", unsafe_allow_html=True)




@st.cache_data(ttl=60, show_spinner=False)
def _load_and_report(file_bytes):
    """Cached on the raw file bytes (or None for the bundled sample
    data), so switching files or waiting past the 60s TTL triggers a
    fresh computation, but repeated reruns with the same file don't."""
    import io
    source = io.BytesIO(file_bytes) if file_bytes is not None else None
    df = load_data(source)
    report = build_alert_report(df)
    return df, report


def get_report(uploaded_file):
    file_bytes = uploaded_file.getvalue() if uploaded_file is not None else None
    return _load_and_report(file_bytes)


def render_sidebar_uploader():
    with st.sidebar:
        st.markdown("""
        <div style='padding:1.5rem 1.2rem;border-bottom:2px solid #30363d;text-align:center;'>
          <div style='font-family:Orbitron,monospace;font-weight:900;font-size:1.6rem;
                      background:linear-gradient(135deg,#60a5fa 0%,#3b82f6 50%,#2563eb 100%);
                      -webkit-background-clip:text;-webkit-text-fill-color:transparent;'>
            ⚡ STOCKMIND AI
          </div>
          <div style='font-size:0.7rem;color:#6b7280;margin-top:0.3rem;letter-spacing:0.15em;
                      text-transform:uppercase;font-weight:600;'>
            AI Inventory Intelligence
          </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("**Data Source**")
        uploaded_file = st.file_uploader(
            "Upload your inventory CSV",
            type=["csv"],
            help="Must include columns: product_id, product_name, category, "
                 "current_stock, unit, reorder_point, reorder_quantity, "
                 "unit_cost, lead_time_days, daily_sales_avg"
        )
        if uploaded_file is None:
            st.caption("Using bundled sample data (200 products)")
        else:
            st.caption(f"Using uploaded file: {uploaded_file.name}")

    return uploaded_file


def render_sidebar_status(summary: dict):
    with st.sidebar:
        st.markdown(f"""
        <div style='padding:1rem 1.2rem;border-bottom:1px solid #30363d;'>
          <div style='font-size:0.65rem;color:#6b7280;text-transform:uppercase;
                      letter-spacing:0.1em;margin-bottom:0.8rem;font-weight:700;'>LIVE STATUS</div>
          <div style='display:flex;justify-content:space-between;padding:0.4rem 0;'>
            <span style='color:#9ca3af;font-size:0.82rem;'>🔴 Critical</span>
            <span style='color:#ef4444;font-family:Orbitron,monospace;font-weight:700;'>{summary['critical_count']}</span>
          </div>
          <div style='display:flex;justify-content:space-between;padding:0.4rem 0;'>
            <span style='color:#9ca3af;font-size:0.82rem;'>🟡 Reorder</span>
            <span style='color:#f59e0b;font-family:Orbitron,monospace;font-weight:700;'>{summary['reorder_count']}</span>
          </div>
          <div style='display:flex;justify-content:space-between;padding:0.4rem 0;'>
            <span style='color:#9ca3af;font-size:0.82rem;'>🟣 Overstock</span>
            <span style='color:#a78bfa;font-family:Orbitron,monospace;font-weight:700;'>{summary['overstock_count']}</span>
          </div>
          <div style='display:flex;justify-content:space-between;padding:0.4rem 0;'>
            <span style='color:#9ca3af;font-size:0.82rem;'>🟢 Healthy</span>
            <span style='color:#10b981;font-family:Orbitron,monospace;font-weight:700;'>{summary['healthy_count']}</span>
          </div>
        </div>
        <div style='padding:1rem 1.2rem;border-bottom:1px solid #30363d;'>
          <div style='font-size:0.72rem;color:#6b7280;margin-bottom:0.2rem;'>Monthly Profit Potential</div>
          <div style='font-family:Orbitron,monospace;font-weight:700;font-size:1.3rem;color:#10b981;'>
            ₹{summary['monthly_profit_potential']:,.0f}
          </div>
          <div style='font-size:0.72rem;color:#6b7280;margin:0.6rem 0 0.2rem;'>Revenue at Risk</div>
          <div style='font-family:Orbitron,monospace;font-weight:700;font-size:1.2rem;color:#ef4444;'>
            ₹{summary['revenue_at_risk']:,.0f}
          </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🔄  Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()

        st.markdown("<div style='padding-top:0.8rem;'></div>", unsafe_allow_html=True)
        st.markdown("**Quick Ask**")
        for icon, q in [
            ("🚨", "What should I order today?"),
            ("📅", "What runs out this week?"),
            ("💰", "How can I increase profit?"),
            ("⚠️", "Explain all critical alerts"),
            ("🏆", "Top profit items"),
        ]:
            if st.button(f"{icon}  {q}", key=f"q_{q}", use_container_width=True):
                st.session_state.pending = q

        if st.button("🗑️  Clear Chat", use_container_width=True):
            st.session_state.messages = []
            db.clear_chat_history(st.session_state.session_id)
            st.rerun()


def render_header(df):
    st.markdown(f"""
    <div style='display:flex;justify-content:space-between;align-items:center;
                padding:1.5rem 0 1.2rem;border-bottom:2px solid #30363d;margin-bottom:1.5rem;'>
      <div>
        <div style='font-family:Orbitron,monospace;font-weight:900;font-size:2.2rem;
                    background:linear-gradient(135deg,#60a5fa 0%,#3b82f6 50%,#2563eb 100%);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;'>
          INVENTORY INTELLIGENCE
        </div>
        <div style='color:#6b7280;font-size:0.85rem;margin-top:0.4rem;font-weight:500;'>
          {datetime.now().strftime('%A, %d %B %Y — %H:%M')} &nbsp;·&nbsp; {len(df)} products tracked
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)


def main():
    if "session_id" not in st.session_state:
        st.session_state.session_id = str(uuid.uuid4())
    if "messages" not in st.session_state:
        st.session_state.messages = db.get_chat_history(st.session_state.session_id)
    if "pending" not in st.session_state:
        st.session_state.pending = None

    uploaded_file = render_sidebar_uploader()

    try:
        df, report = get_report(uploaded_file)
    except InventoryDataError as e:
        st.error(f"There's a problem with the uploaded file: {e}")
        st.info("Falling back to the bundled sample dataset until a valid file is uploaded.")
        df, report = get_report(None)

    summary = report["summary"]
    db.save_snapshot(summary)
    render_sidebar_status(summary)

    render_header(df)

    cols = st.columns(5)
    kpis = [
        ("🔴 CRITICAL", summary["critical_count"], "Order today"),
        ("🟡 REORDER", summary["reorder_count"], "Order soon"),
        ("💰 MONTHLY", f"₹{summary['monthly_profit_potential']/1000:.1f}K", "Profit potential"),
        ("⚠️ AT RISK", f"₹{summary['revenue_at_risk']/1000:.1f}K", "Revenue at risk"),
        ("📦 TOTAL", summary["total_products"], "Products tracked"),
    ]
    for col, (label, val, help_text) in zip(cols, kpis):
        col.metric(label, val, help=help_text)

    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "💬  CHAT WITH AI", "🚨  CRITICAL ALERTS", "💰  PROFIT ANALYSIS",
        "📋  FULL INVENTORY", "📈  TRENDS",
    ])

    
    with tab1:
        if not st.session_state.messages:
            st.markdown(f"""
            <div style='background:linear-gradient(135deg,rgba(59,130,246,0.08),rgba(37,99,235,0.04));
                        border:1px solid rgba(96,165,250,0.2);border-radius:16px;
                        padding:1.5rem 1.8rem;margin-bottom:1.2rem;'>
              <div style='font-weight:700;font-size:1.1rem;color:#f3f4f6;margin-bottom:0.6rem;'>
                👋 Hi! I'm StockMind — Your AI Inventory Manager
              </div>
              <div style='color:#9ca3af;font-size:0.9rem;line-height:1.8;'>
                You have <strong style='color:#ef4444;'>{summary['critical_count']} critical items</strong>
                to order today and <strong style='color:#f59e0b;'>{summary['reorder_count']} items</strong> to reorder soon.
                Ask me anything, or use the Quick Ask buttons on the left.
              </div>
            </div>
            """, unsafe_allow_html=True)

        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        def handle_question(q):
            st.session_state.messages.append({"role": "user", "content": q})
            db.save_chat_message(st.session_state.session_id, "user", q)
            with st.chat_message("user"):
                st.markdown(q)
            with st.chat_message("assistant"):
                with st.spinner("Analyzing your inventory..."):
                    reply = chat_reply(report, st.session_state.messages)
                st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            db.save_chat_message(st.session_state.session_id, "assistant", reply)

        if st.session_state.pending:
            q = st.session_state.pending
            st.session_state.pending = None
            handle_question(q)
            st.rerun()

        user_input = st.chat_input("Ask about your stock, profits, or get reorder advice...")
        if user_input:
            handle_question(user_input)
            st.rerun()

    
    with tab2:
        cdf, rdf = report["critical"], report["reorder"]
        if cdf.empty:
            st.success("✅ No critical stockouts detected right now!")
        else:
            st.error(f"🚨 {len(cdf)} items will stock out before your next delivery!")
            d = cdf[["product_name", "category", "current_stock", "unit", "days_until_stockout",
                      "optimal_order_qty", "total_reorder_cost", "revenue_at_risk"]].copy()
            d.columns = ["Product", "Category", "Stock", "Unit", "Days Left",
                         "Order Qty", "Order Cost (₹)", "Revenue at Risk (₹)"]
            d["Days Left"] = d["Days Left"].round(1)
            st.dataframe(d, use_container_width=True, hide_index=True)

            a, b = st.columns(2)
            a.metric("💸 Total Order Budget", f"₹{cdf['total_reorder_cost'].sum():,.0f}")
            b.metric("⚠️ Revenue You'll Lose", f"₹{cdf['revenue_at_risk'].sum():,.0f}")

        if not rdf.empty:
            st.markdown("---")
            st.warning(f"🟡 {len(rdf)} items need reordering soon")
            d2 = rdf[["product_name", "category", "current_stock", "unit",
                      "days_until_stockout", "optimal_order_qty", "total_reorder_cost"]].copy()
            d2.columns = ["Product", "Category", "Stock", "Unit", "Days Left", "Order Qty", "Cost (₹)"]
            d2["Days Left"] = d2["Days Left"].round(1)
            st.dataframe(d2, use_container_width=True, hide_index=True)

   
    with tab3:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**🏆 Top 10 Most Profitable Products**")
            t = df.nlargest(10, "daily_profit")[
                ["product_name", "category", "daily_profit", "monthly_profit_potential", "margin_pct"]].copy()
            t.columns = ["Product", "Category", "Daily Profit (₹)", "Monthly Profit (₹)", "Margin"]
            t["Margin"] = (t["Margin"] * 100).map("{:.0f}%".format)
            st.dataframe(t, use_container_width=True, hide_index=True)

        with c2:
            st.markdown("**⚠️ Overstock / Wastage Risk**")
            ov = report["overstock"][["product_name", "category", "current_stock", "unit", "days_until_stockout"]].copy()
            if ov.empty:
                st.success("✅ No overstock risk detected.")
            else:
                ov.columns = ["Product", "Category", "Stock", "Unit", "Days Cover"]
                st.dataframe(ov, use_container_width=True, hide_index=True)

    
    with tab4:
        fc, sc = st.columns([3, 1])
        sel_cat = fc.selectbox("Category", ["All"] + sorted(df["category"].unique().tolist()))
        sel_status = sc.selectbox("Status", ["All", "CRITICAL", "REORDER", "OVERSTOCK", "OK"])

        filt = df.copy()
        if sel_cat != "All":
            filt = filt[filt["category"] == sel_cat]
        if sel_status != "All":
            filt = filt[filt["status"] == sel_status]

        show = filt[["product_id", "product_name", "category", "current_stock", "unit",
                     "days_until_stockout", "status", "daily_sales_avg",
                     "optimal_order_qty", "total_reorder_cost", "daily_profit"]].copy()
        show.columns = ["ID", "Product", "Category", "Stock", "Unit", "Days Left",
                        "Status", "Daily Sales", "Reorder Qty", "Cost (₹)", "Daily Profit (₹)"]
        st.dataframe(show, use_container_width=True, hide_index=True)
        st.caption(f"Showing {len(show)} of {len(df)} products")

    
    with tab5:
        history = db.get_snapshot_history(limit=500)
        if len(history) < 2:
            st.info(
                "Not enough history yet to show trends. Every time this app runs "
                "(or the data refreshes), a snapshot is saved automatically — check "
                "back after a few refreshes or daily runs to see trends build up."
            )
        else:
            import pandas as pd
            hist_df = pd.DataFrame(history)
            hist_df["created_at"] = pd.to_datetime(hist_df["created_at"])
            hist_df = hist_df.set_index("created_at")

            st.markdown("**Alert Counts Over Time**")
            st.line_chart(hist_df[["critical_count", "reorder_count", "overstock_count"]])

            st.markdown("**Monthly Profit Potential Over Time**")
            st.line_chart(hist_df[["monthly_profit_potential"]])

            st.markdown("**Revenue at Risk Over Time**")
            st.line_chart(hist_df[["revenue_at_risk"]])

            st.caption(f"{len(history)} snapshots recorded since tracking began.")


if __name__ == "__main__":
    main()
