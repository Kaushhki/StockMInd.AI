import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
from groq import Groq


GROQ_API_KEY = "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"

st.set_page_config(
    page_title="StockMind AI",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

CATEGORY_MARGINS={
    "Grains": 0.12, "Pulses": 0.14, "Oils": 0.16, "Dairy": 0.18,
    "Spices": 0.25, "Condiments": 0.22, "Snacks": 0.28, "Breakfast": 0.20,
    "Bakery": 0.30, "Noodles": 0.24, "Soups": 0.26, "Beverages": 0.22,
    "Health Drinks": 0.18, "Personal Care": 0.20, "Household": 0.18,
    "Vegetables": 0.35, "Frozen": 0.22, "Stationery": 0.30, "Health": 0.20,
}

SAMPLE_DATA = """product_id,product_name,category,current_stock,unit,reorder_point,reorder_quantity,unit_cost,lead_time_days,daily_sales_avg
P001,Basmati Rice 5kg,Grains,45,bags,20,50,180,3,4.2
P002,Sunflower Oil 1L,Oils,12,bottles,15,60,95,2,3.8
P003,Wheat Flour 10kg,Grains,8,bags,10,40,220,4,1.5
P004,Sugar 1kg,Grains,55,packs,25,100,48,2,6.1
P005,Tomato Ketchup 500g,Condiments,3,bottles,8,30,65,3,2.2
P006,Milk Powder 500g,Dairy,17,tins,12,40,145,2,2.9
P007,Green Dal 1kg,Pulses,28,packs,15,60,88,3,3.5
P008,Salt 1kg,Spices,60,packs,20,80,22,1,5.0
P009,Coconut Oil 500ml,Oils,6,bottles,10,40,125,2,1.8
P010,Biscuits Assorted,Snacks,22,boxes,30,80,145,1,8.5
P011,Toor Dal 1kg,Pulses,34,packs,15,60,110,3,3.2
P012,Chana Dal 1kg,Pulses,19,packs,12,50,95,3,2.8
P013,Moong Dal 1kg,Pulses,11,packs,12,50,105,3,2.1
P014,Urad Dal 1kg,Pulses,7,packs,10,40,115,3,1.9
P015,Masoor Dal 1kg,Pulses,25,packs,12,50,90,3,2.4
P016,Sona Masoori Rice 5kg,Grains,38,bags,18,45,165,3,3.9
P017,Brown Rice 1kg,Grains,14,packs,8,30,85,3,1.2
P018,Poha 500g,Grains,42,packs,20,60,38,2,4.5
P019,Semolina 500g,Grains,33,packs,15,50,32,2,3.1
P020,Vermicelli 200g,Grains,28,packs,15,60,28,2,3.8
P021,Mustard Oil 1L,Oils,9,bottles,10,40,135,2,2.3
P022,Groundnut Oil 1L,Oils,15,bottles,12,45,105,2,2.7
P023,Olive Oil 500ml,Oils,7,bottles,8,25,320,3,0.9
P024,Ghee 500g,Dairy,18,tins,10,35,480,2,2.1
P025,Butter 100g,Dairy,31,packs,20,80,52,1,5.6
P026,Paneer 200g,Dairy,24,packs,15,50,68,1,4.8
P027,Curd 400g,Dairy,40,cups,25,100,32,1,7.2
P028,Cheese Slices 200g,Dairy,13,packs,10,40,95,1,2.4
P029,Red Chilli Powder 200g,Spices,52,packs,25,80,45,2,5.8
P030,Turmeric Powder 200g,Spices,48,packs,25,80,38,2,5.2
P031,Coriander Powder 200g,Spices,39,packs,20,70,42,2,4.4
P032,Cumin Seeds 100g,Spices,44,packs,20,70,55,2,4.1
P033,Mustard Seeds 100g,Spices,37,packs,18,65,28,2,3.7
P034,Garam Masala 100g,Spices,29,packs,15,55,72,2,3.0
P035,Kitchen King Masala 100g,Spices,22,packs,12,50,68,2,2.5
P036,Chicken Masala 100g,Spices,18,packs,12,45,75,2,2.2
P037,Biryani Masala 50g,Spices,14,packs,10,40,55,2,1.8
P038,Chaat Masala 100g,Spices,26,packs,15,50,48,2,2.9
P039,Cardamom 50g,Spices,11,packs,8,30,145,3,1.1
P040,Black Pepper 100g,Spices,17,packs,10,35,125,3,1.7
P041,Tomato Puree 200g,Condiments,27,packs,15,55,38,2,3.3
P042,Green Chilli Sauce 200g,Condiments,19,bottles,10,40,55,2,2.1
P043,Soy Sauce 200ml,Condiments,16,bottles,10,35,65,2,1.9
P044,Vinegar 500ml,Condiments,22,bottles,12,45,32,2,2.0
P045,Mayonnaise 300g,Condiments,11,jars,8,30,85,2,1.5
P046,Mixed Pickle 500g,Condiments,14,jars,8,30,72,3,1.6
P047,Mango Pickle 500g,Condiments,20,jars,10,35,65,3,2.2
P048,Digestive Biscuits 200g,Snacks,35,packs,20,70,45,1,5.8
P049,Cream Crackers 200g,Snacks,28,packs,18,60,42,1,4.2
P050,Glucose Biscuits 100g,Snacks,55,packs,30,90,18,1,8.5
P051,Marie Biscuits 200g,Snacks,42,packs,25,80,38,1,6.1
P052,Namkeen Mix 200g,Snacks,38,packs,20,70,48,1,5.5
P053,Potato Chips 100g,Snacks,50,packs,30,100,32,1,9.2
P054,Popcorn Butter 100g,Snacks,24,packs,15,55,28,1,4.0
P055,Roasted Peanuts 200g,Snacks,31,packs,18,65,35,1,4.8
P056,Cashew Nuts 200g,Snacks,14,packs,10,35,185,2,1.9
P057,Almonds 200g,Snacks,11,packs,8,30,245,2,1.5
P058,Raisins 200g,Snacks,19,packs,10,40,88,2,2.3
P059,Cornflakes 500g,Breakfast,23,boxes,12,40,95,2,2.8
P060,Oats 500g,Breakfast,31,packs,18,55,72,2,3.5
P061,Muesli 500g,Breakfast,14,packs,8,30,145,2,1.7
P062,Upma Mix 200g,Breakfast,27,packs,15,50,38,2,3.1
P063,Idli Mix 500g,Breakfast,19,packs,10,40,58,2,2.3
P064,Dosa Mix 500g,Breakfast,22,packs,12,45,55,2,2.6
P065,Bread White 400g,Bakery,45,loaves,30,80,38,1,8.8
P066,Bread Brown 400g,Bakery,28,loaves,20,60,42,1,5.2
P067,Bread Multigrain 400g,Bakery,18,loaves,12,40,48,1,3.3
P068,Pav Buns 6pcs,Bakery,35,packs,22,70,28,1,6.5
P069,Burger Buns 4pcs,Bakery,22,packs,15,50,32,1,4.1
P070,Rusk 200g,Bakery,40,packs,22,75,35,1,6.2
P071,Pasta Penne 500g,Noodles,19,packs,10,40,68,2,2.4
P072,Pasta Spaghetti 500g,Noodles,14,packs,8,35,72,2,1.8
P073,Macaroni 500g,Noodles,11,packs,8,30,58,2,1.6
P074,Instant Noodles Masala,Noodles,62,packs,35,120,14,1,12.5
P075,Rice Noodles 200g,Noodles,16,packs,10,35,48,2,2.0
P076,Tomato Soup Powder 50g,Soups,21,packs,12,45,32,2,2.5
P077,Sweet Corn Soup 50g,Soups,18,packs,10,40,32,2,2.1
P078,Chicken Soup Powder 50g,Soups,12,packs,8,30,38,2,1.5
P079,Coca Cola 2L,Beverages,30,bottles,20,60,88,1,5.5
P080,Pepsi 2L,Beverages,25,bottles,18,55,85,1,4.8
P081,Sprite 2L,Beverages,20,bottles,15,50,85,1,3.9
P082,Thums Up 2L,Beverages,22,bottles,15,50,88,1,4.2
P083,Maaza Mango 600ml,Beverages,40,bottles,25,80,38,1,7.1
P084,Frooti 200ml,Beverages,55,tetra,30,100,18,1,10.2
P085,Green Tea 25 bags,Beverages,27,boxes,15,50,95,2,3.1
P086,Bru Coffee 50g,Beverages,29,packs,18,60,85,2,3.5
P087,Nescafe Classic 50g,Beverages,24,packs,15,55,98,2,2.9
P088,Horlicks 500g,Health Drinks,16,jars,10,35,245,2,1.8
P089,Bournvita 500g,Health Drinks,20,jars,12,40,255,2,2.2
P090,Complan 500g,Health Drinks,11,jars,8,28,285,2,1.3
P091,Colgate Toothpaste 200g,Personal Care,38,tubes,22,75,65,2,5.5
P092,Pepsodent Toothpaste 150g,Personal Care,31,tubes,18,65,55,2,4.4
P093,Dettol Soap 75g,Personal Care,55,bars,30,100,28,1,8.2
P094,Lux Soap 100g,Personal Care,48,bars,28,95,32,1,7.1
P095,Dove Soap 100g,Personal Care,35,bars,20,75,45,1,5.2
P096,Head Shoulders Shampoo 180ml,Personal Care,22,bottles,12,45,145,2,2.8
P097,Pantene Shampoo 180ml,Personal Care,18,bottles,10,40,155,2,2.3
P098,Surf Excel 1kg,Household,27,packs,15,50,115,2,3.2
P099,Ariel 1kg,Household,22,packs,12,45,125,2,2.7
P100,Vim Dishwash Bar 300g,Household,42,bars,25,80,32,1,5.8"""


@st.cache_data
def load_data():
    from io import StringIO
    df = pd.read_csv(StringIO(SAMPLE_DATA))
    
    # Forecasting calculations
    df["days_until_stockout"] = df.apply(
        lambda r: r["current_stock"] / r["daily_sales_avg"] if r["daily_sales_avg"] > 0 else 999, axis=1)
    df["needs_reorder"] = df["days_until_stockout"] <= df["lead_time_days"] * 1.5
    df["optimal_order_qty"] = df.apply(
        lambda r: max(int(r["daily_sales_avg"] * 30 + r["reorder_quantity"]), r["reorder_quantity"]), axis=1)
    df["total_reorder_cost"] = df["optimal_order_qty"] * df["unit_cost"]
    df["margin_pct"] = df["category"].map(lambda c: CATEGORY_MARGINS.get(c, 0.20))
    df["selling_price"] = df["unit_cost"] * (1 + df["margin_pct"])
    df["daily_profit"] = (df["selling_price"] - df["unit_cost"]) * df["daily_sales_avg"]
    df["monthly_profit_potential"] = df["daily_profit"] * 30
    df["revenue_at_risk"] = df.apply(lambda r: (
        r["selling_price"] * r["daily_sales_avg"] * max(0, r["lead_time_days"] - r["days_until_stockout"])), axis=1)
    
    def get_status(row):
        if row["days_until_stockout"] <= row["lead_time_days"]: return "CRITICAL"
        elif row["needs_reorder"]: return "REORDER"
        elif row["days_until_stockout"] > 90: return "OVERSTOCK"
        return "OK"
    
    df["status"] = df.apply(get_status, axis=1)
    return df


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
    box-shadow: 4px 0 20px rgba(0,0,0,0.5);
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
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    font-weight: 500 !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3);
}

[data-testid="stSidebar"] .stButton > button:hover {
    background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%) !important;
    border-color: #60a5fa !important;
    color: #ffffff !important;
    transform: translateX(5px) !important;
    box-shadow: 0 4px 16px rgba(59,130,246,0.4);
}

[data-testid="stChatMessage"] {
    background: rgba(17, 24, 39, 0.6) !important;
    border: 1px solid rgba(75, 85, 99, 0.3) !important;
    border-radius: 16px !important;
    padding: 1.2rem !important;
    margin-bottom: 0.8rem !important;
    backdrop-filter: blur(10px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}

[data-testid="stChatMessage"]:has([data-testid="chatAvatarIcon-user"]) {
    background: linear-gradient(135deg, rgba(59,130,246,0.1) 0%, rgba(37,99,235,0.05) 100%) !important;
    border-color: rgba(96,165,250,0.3) !important;
}

[data-testid="stChatInput"] {
    background: rgba(31, 41, 55, 0.8) !important;
    border: 2px solid #374151 !important;
    border-radius: 14px !important;
    backdrop-filter: blur(10px);
}

[data-testid="stChatInput"] textarea {
    background: transparent !important;
    color: #e5e7eb !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.95rem !important;
}

[data-testid="stMetric"] {
    background: linear-gradient(135deg, rgba(17,24,39,0.8) 0%, rgba(31,41,55,0.6) 100%) !important;
    border: 1px solid rgba(75,85,99,0.4) !important;
    border-radius: 14px !important;
    padding: 1.2rem !important;
    backdrop-filter: blur(10px);
    box-shadow: 0 4px 16px rgba(0,0,0,0.3);
    transition: all 0.3s ease;
}

[data-testid="stMetric"]:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.4);
    border-color: rgba(96,165,250,0.5);
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
    text-shadow: 0 0 20px rgba(59,130,246,0.5);
}

[data-testid="stTabs"] button {
    font-family: 'Inter', sans-serif !important;
    font-size: 0.85rem !important;
    color: #6b7280 !important;
    font-weight: 600 !important;
    padding: 0.8rem 1.5rem !important;
    transition: all 0.3s ease;
}

[data-testid="stTabs"] button:hover {
    color: #60a5fa !important;
}

[data-testid="stTabs"] button[aria-selected="true"] {
    color: #3b82f6 !important;
    border-bottom: 3px solid #3b82f6 !important;
    background: rgba(59,130,246,0.1) !important;
}

div[data-testid="stDataFrame"] {
    border: 1px solid rgba(75,85,99,0.3) !important;
    border-radius: 12px !important;
    overflow: hidden;
    backdrop-filter: blur(10px);
    box-shadow: 0 4px 16px rgba(0,0,0,0.2);
}

::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: rgba(17,24,39,0.5); border-radius: 4px; }
::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, #374151 0%, #1f2937 100%);
    border-radius: 4px;
    transition: background 0.3s ease;
}
::-webkit-scrollbar-thumb:hover { background: linear-gradient(180deg, #4b5563 0%, #374151 100%); }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_client():
    return Groq(api_key=GROQ_API_KEY)

def build_prompt(df):
    critical = df[df["status"] == "CRITICAL"]
    reorder  = df[df["status"] == "REORDER"]
    
    crit_lines = "\n".join(
        f"  - {r.product_name}: {r.current_stock} {r.unit} left, "
        f"{r.days_until_stockout:.1f} days, order {int(r.optimal_order_qty)}, "
        f"cost Rs {r.total_reorder_cost:,.0f}"
        for _, r in critical.iterrows()) or "  None"
    
    reorder_lines = "\n".join(
        f"  - {r.product_name}: {r.days_until_stockout:.1f} days left"
        for _, r in reorder.head(10).iterrows()) or "  None"
    
    top5 = "\n".join(
        f"  - {r.product_name}: Rs {r.daily_profit:.0f}/day"
        for _, r in df.nlargest(5, "daily_profit").iterrows())
    
    return f"""You are StockMind, an expert AI inventory management agent.
Today: {datetime.now().strftime('%d %B %Y')}
Total: {len(df)} products | Critical: {len(critical)} | Reorder: {len(reorder)} | Healthy: {len(df[df['status']=='OK'])}

CRITICAL ITEMS (order today):
{crit_lines}

REORDER SOON:
{reorder_lines}

TOP PROFIT ITEMS:
{top5}

Budget needed: Rs {df[df['needs_reorder']]['total_reorder_cost'].sum():,.0f}
Monthly profit: Rs {df['monthly_profit_potential'].sum():,.0f}

Rules: Give specific numbers. Use **bold** for key figures. Be concise and actionable."""

def ask_ai(client, messages, prompt):
    try:
        r = client.chat.completions.create(
           model="llama3-70b-8192",
            messages=[{"role": "system", "content": prompt}] + messages,
            temperature=0.35,
            max_tokens=1500)
        return r.choices[0].message.content
    except Exception as e:
        return f"⚠️ AI error: {str(e)}"

def render_sidebar(df):
    with st.sidebar:
        st.markdown("""
        <div style='padding:1.5rem 1.2rem;border-bottom:2px solid #30363d;text-align:center;'>
          <div style='font-family:Orbitron,monospace;font-weight:900;font-size:1.6rem;
                      background:linear-gradient(135deg,#60a5fa 0%,#3b82f6 50%,#2563eb 100%);
                      -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                      letter-spacing:0.05em;text-shadow:0 0 30px rgba(59,130,246,0.6);'>
            ⚡ STOCKMIND
          </div>
          <div style='font-size:0.7rem;color:#6b7280;margin-top:0.3rem;letter-spacing:0.15em;
                      text-transform:uppercase;font-weight:600;'>
            AI Inventory Intelligence
          </div>
        </div>
        """, unsafe_allow_html=True)
        
        if df.empty:
            st.warning("No data loaded")
            return
        
        c = len(df[df["status"] == "CRITICAL"])
        r = len(df[df["status"] == "REORDER"])
        o = len(df[df["status"] == "OVERSTOCK"])
        k = len(df[df["status"] == "OK"])
        monthly = df["monthly_profit_potential"].sum()
        at_risk = df["revenue_at_risk"].sum()
        
        st.markdown(f"""
        <div style='padding:1rem 1.2rem;border-bottom:1px solid #30363d;'>
          <div style='font-size:0.65rem;color:#6b7280;text-transform:uppercase;
                      letter-spacing:0.1em;margin-bottom:0.8rem;font-weight:700;'>
            LIVE STATUS
          </div>
          <div style='display:flex;flex-direction:column;gap:0.6rem;'>
            <div style='display:flex;justify-content:space-between;padding:0.4rem 0;'>
              <span style='color:#9ca3af;font-size:0.82rem;'>🔴 Critical</span>
              <span style='color:#ef4444;font-family:Orbitron,monospace;font-weight:700;'>{c}</span>
            </div>
            <div style='display:flex;justify-content:space-between;padding:0.4rem 0;'>
              <span style='color:#9ca3af;font-size:0.82rem;'>🟡 Reorder</span>
              <span style='color:#f59e0b;font-family:Orbitron,monospace;font-weight:700;'>{r}</span>
            </div>
            <div style='display:flex;justify-content:space-between;padding:0.4rem 0;'>
              <span style='color:#9ca3af;font-size:0.82rem;'>🟣 Overstock</span>
              <span style='color:#a78bfa;font-family:Orbitron,monospace;font-weight:700;'>{o}</span>
            </div>
            <div style='display:flex;justify-content:space-between;padding:0.4rem 0;'>
              <span style='color:#9ca3af;font-size:0.82rem;'>🟢 Healthy</span>
              <span style='color:#10b981;font-family:Orbitron,monospace;font-weight:700;'>{k}</span>
            </div>
          </div>
        </div>
        
        <div style='padding:1rem 1.2rem;border-bottom:1px solid #30363d;'>
          <div style='font-size:0.65rem;color:#6b7280;text-transform:uppercase;
                      letter-spacing:0.1em;margin-bottom:0.8rem;font-weight:700;'>
            PROFIT SNAPSHOT
          </div>
          <div style='margin-bottom:0.8rem;'>
            <div style='font-size:0.72rem;color:#6b7280;margin-bottom:0.2rem;'>Monthly Potential</div>
            <div style='font-family:Orbitron,monospace;font-weight:700;font-size:1.3rem;
                        color:#10b981;text-shadow:0 0 15px rgba(16,185,129,0.5);'>
              ₹{monthly:,.0f}
            </div>
          </div>
          <div>
            <div style='font-size:0.72rem;color:#6b7280;margin-bottom:0.2rem;'>Revenue at Risk</div>
            <div style='font-family:Orbitron,monospace;font-weight:700;font-size:1.2rem;
                        color:#ef4444;text-shadow:0 0 15px rgba(239,68,68,0.5);'>
              ₹{at_risk:,.0f}
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("""
        <div style='padding:0.8rem 1.2rem 0.4rem;'>
          <div style='font-size:0.65rem;color:#6b7280;text-transform:uppercase;
                      letter-spacing:0.1em;margin-bottom:0.6rem;font-weight:700;'>
            QUICK ASK
          </div>
        </div>
        """, unsafe_allow_html=True)
        
        for icon, q in [
            ("🚨", "What should I order today?"),
            ("📅", "What runs out this week?"),
            ("💰", "How can I increase profit?"),
            ("⚠️", "Explain all critical alerts"),
            ("📊", "Give me a full summary"),
            ("🔮", "Predict stockouts 14 days"),
            ("🗑️", "What am I wasting money on?"),
            ("🏆", "Top profit items"),
        ]:
            if st.button(f"{icon}  {q}", key=f"q_{q}", use_container_width=True):
                st.session_state.pending = q
        
        st.markdown("<div style='padding:0.4rem 1.2rem;'>", unsafe_allow_html=True)
        if st.button("🗑️  Clear Chat", use_container_width=True, key="clear"):
            st.session_state.messages = []
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("""
        <div style='padding:1rem 1.2rem;border-top:1px solid #30363d;margin-top:0.5rem;'>
          <div style='font-size:0.65rem;color:#6b7280;text-align:center;line-height:1.8;'>
            Powered by <span style='color:#60a5fa;font-weight:700;'>Groq</span>
            × <span style='color:#a78bfa;font-weight:700;'>LLaMA 3 70B</span><br>
            <span style='color:#4b5563;'>Free · Fast · Private</span>
          </div>
        </div>
        """, unsafe_allow_html=True)

def main():
    df = load_data()
    client = get_client()
    render_sidebar(df)
    
    # Header
    st.markdown(f"""
    <div style='display:flex;justify-content:space-between;align-items:center;
                padding:1.5rem 0 1.2rem;border-bottom:2px solid #30363d;margin-bottom:1.5rem;'>
      <div>
        <div style='font-family:Orbitron,monospace;font-weight:900;font-size:2.2rem;
                    background:linear-gradient(135deg,#60a5fa 0%,#3b82f6 50%,#2563eb 100%);
                    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
                    letter-spacing:0.02em;text-shadow:0 0 40px rgba(59,130,246,0.6);'>
          INVENTORY INTELLIGENCE
        </div>
        <div style='color:#6b7280;font-size:0.85rem;margin-top:0.4rem;font-weight:500;'>
          {datetime.now().strftime('%A, %d %B %Y')} &nbsp;·&nbsp; {len(df)} products tracked
        </div>
      </div>
      <div style='text-align:right;padding:0.8rem 1.2rem;background:rgba(59,130,246,0.1);
                  border-radius:10px;border:1px solid rgba(96,165,250,0.3);'>
        <div style='font-size:0.7rem;color:#6b7280;margin-bottom:0.2rem;'>AI ENGINE</div>
        <div style='color:#60a5fa;font-weight:700;font-family:Orbitron,monospace;font-size:0.9rem;'>
          LLaMA-3 70B
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)
    
    # KPIs
    cols = st.columns(5)
    kpis = [
        ("🔴 CRITICAL", len(df[df["status"] == "CRITICAL"]), "Order today"),
        ("🟡 REORDER", len(df[df["status"] == "REORDER"]), "Order soon"),
        ("💰 MONTHLY", f"₹{df['monthly_profit_potential'].sum()/1000:.1f}K", "Profit potential"),
        ("⚠️ AT RISK", f"₹{df['revenue_at_risk'].sum()/1000:.1f}K", "Revenue at risk"),
        ("📦 TOTAL", len(df), "Products tracked"),
    ]
    for col, (label, val, help_text) in zip(cols, kpis):
        col.metric(label, val, help=help_text)
    
    st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
    
    # Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "💬  CHAT WITH AI",
        "🚨  CRITICAL ALERTS",
        "💰  PROFIT ANALYSIS",
        "📋  FULL INVENTORY",
    ])
    
    # TAB 1: CHAT
    with tab1:
        if "messages" not in st.session_state:
            st.session_state.messages = []
        if "pending" not in st.session_state:
            st.session_state.pending = None
        
        if not st.session_state.messages:
            st.markdown(f"""
            <div style='background:linear-gradient(135deg,rgba(59,130,246,0.08),rgba(37,99,235,0.04));
                        border:1px solid rgba(96,165,250,0.2);border-radius:16px;
                        padding:1.5rem 1.8rem;margin-bottom:1.2rem;'>
              <div style='font-family:Orbitron,monospace;font-weight:700;font-size:1.1rem;
                          color:#f3f4f6;margin-bottom:0.6rem;'>
                👋 Hi! I'm StockMind — Your AI Inventory Manager
              </div>
              <div style='color:#9ca3af;font-size:0.9rem;line-height:1.8;'>
                I've analyzed all <strong style='color:#e5e7eb;'>{len(df)} products</strong> in your inventory.
                Right now you have <strong style='color:#ef4444;'>{len(df[df['status']=='CRITICAL'])} critical items</strong>
                to order today and <strong style='color:#f59e0b;'>{len(df[df['status']=='REORDER'])} items</strong> to reorder soon.<br><br>
                Ask me anything about your stock, profits, or get reorder advice. Use the quick buttons on the left to get started instantly.
              </div>
            </div>
            """, unsafe_allow_html=True)
        
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        if st.session_state.pending:
            q = st.session_state.pending
            st.session_state.pending = None
            st.session_state.messages.append({"role": "user", "content": q})
            with st.chat_message("user"):
                st.markdown(q)
            with st.chat_message("assistant"):
                with st.spinner("Analyzing your inventory..."):
                    reply = ask_ai(client, st.session_state.messages, build_prompt(df))
                st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()
        
        user_input = st.chat_input("Ask about your stock, profits, or get reorder advice...")
        if user_input:
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    reply = ask_ai(client, st.session_state.messages, build_prompt(df))
                st.markdown(reply)
            st.session_state.messages.append({"role": "assistant", "content": reply})
            st.rerun()
    
    # TAB 2: CRITICAL ALERTS
    with tab2:
        cdf = df[df["status"] == "CRITICAL"].sort_values("revenue_at_risk", ascending=False)
        rdf = df[df["status"] == "REORDER"].sort_values("days_until_stockout")
        
        if cdf.empty:
            st.success("✅ No critical stockouts detected right now!")
        else:
            st.error(f"🚨 {len(cdf)} items will stock out before your next delivery!")
            d = cdf[["product_name", "category", "current_stock", "unit",
                     "days_until_stockout", "optimal_order_qty",
                     "total_reorder_cost", "revenue_at_risk"]].copy()
            d.columns = ["Product", "Category", "Stock", "Unit", "Days Left",
                         "Order Qty", "Order Cost (₹)", "Revenue at Risk (₹)"]
            d["Days Left"] = d["Days Left"].round(1)
            d["Order Cost (₹)"] = d["Order Cost (₹)"].map("{:,.0f}".format)
            d["Revenue at Risk (₹)"] = d["Revenue at Risk (₹)"].map("{:,.0f}".format)
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
            d2["Cost (₹)"] = d2["Cost (₹)"].map("{:,.0f}".format)
            st.dataframe(d2, use_container_width=True, hide_index=True)
    
    # TAB 3: PROFIT ANALYSIS
    with tab3:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**🏆 Top 10 Most Profitable Products**")
            t = df.nlargest(10, "daily_profit")[
                ["product_name", "category", "daily_profit", "monthly_profit_potential", "margin_pct"]].copy()
            t.columns = ["Product", "Category", "Daily Profit (₹)", "Monthly Profit (₹)", "Margin"]
            t["Daily Profit (₹)"] = t["Daily Profit (₹)"].map("{:.0f}".format)
            t["Monthly Profit (₹)"] = t["Monthly Profit (₹)"].map("{:,.0f}".format)
            t["Margin"] = (t["Margin"] * 100).map("{:.0f}%".format)
            st.dataframe(t, use_container_width=True, hide_index=True)
        
        with c2:
            st.markdown("**⚠️ Overstock / Wastage Risk**")
            ov = df[df["status"] == "OVERSTOCK"][
                ["product_name", "category", "current_stock", "unit", "days_until_stockout"]].copy()
            if ov.empty:
                st.success("✅ No overstock risk detected.")
            else:
                ov.columns = ["Product", "Category", "Stock", "Unit", "Days Cover"]
                ov["Days Cover"] = ov["Days Cover"].round(0).astype(int)
                st.dataframe(ov, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.markdown("**📊 Profit by Category**")
        cat = df.groupby("category").agg(
            Daily=("daily_profit", "sum"),
            Monthly=("monthly_profit_potential", "sum"),
            Products=("product_id", "count")
        ).sort_values("Monthly", ascending=False).reset_index()
        cat.columns = ["Category", "Daily Profit (₹)", "Monthly Profit (₹)", "Products"]
        cat["Daily Profit (₹)"] = cat["Daily Profit (₹)"].map("{:,.0f}".format)
        cat["Monthly Profit (₹)"] = cat["Monthly Profit (₹)"].map("{:,.0f}".format)
        st.dataframe(cat, use_container_width=True, hide_index=True)
    
    # TAB 4: FULL INVENTORY
    with tab4:
        fc, sc = st.columns([3, 1])
        sel_cat = fc.selectbox("Category", ["All"] + sorted(df["category"].unique().tolist()), key="cat_f")
        sel_status = sc.selectbox("Status", ["All", "CRITICAL", "REORDER", "OVERSTOCK", "OK"], key="stat_f")
        
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
        show["Days Left"] = show["Days Left"].round(1)
        show["Cost (₹)"] = show["Cost (₹)"].map("{:,.0f}".format)
        show["Daily Profit (₹)"] = show["Daily Profit (₹)"].map("{:.0f}".format)
        st.dataframe(show, use_container_width=True, hide_index=True)
        st.caption(f"Showing {len(show)} of {len(df)} products")

if __name__ == "__main__":
    main()
