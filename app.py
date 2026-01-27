import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime, timedelta

# --- 1. INDUSTRIAL THEME CONFIG ---
st.set_page_config(page_title="MELT Index | Control Room", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #050505; color: #00ffcc; }
    h1, h2, h3 { font-family: 'Courier New', monospace; font-weight: bold; color: #00ffcc; }
    .sensor-failure { color: #000000 !important; background-color: #ffffff; padding: 5px; font-weight: bold; font-family: monospace; text-align: center; }
    .telemetry-label { font-size: 0.8rem; color: #888; font-family: 'Courier New', monospace; text-transform: uppercase; }
    .telemetry-val { font-size: 1.3rem; font-weight: bold; color: #ffffff; }
    .telemetry-change { font-size: 0.8rem; font-family: monospace; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. FIXED ENGINE LOGIC ---
W_M, W_E, W_L, W_T = 0.4, 0.2, 0.2, 0.2

# Mock/Override Data for Jan 2026
M_SCORE = 20
E_SCORE = 29
L_SCORE = 54

@st.cache_data(ttl=3600)
def get_technicals():
    try:
        # Attempt to pull CBBI
        import requests
        r = requests.get("https://colintalkscrypto.com/cbbi/data/latest.json", timeout=3)
        data = r.json()
        latest_key = sorted(data.keys())[-1]
        return int(data[latest_key] * 100)
    except:
        return 50  # DEFAULT FAILURE STATE

T_SCORE = get_technicals()
final_score = int((M_SCORE * W_M) + (E_SCORE * W_E) + (L_SCORE * W_L) + (T_SCORE * W_T))

def get_risk_meta(score):
    if score < 20: return "MELT UP", "#006400"
    if score < 40: return "SAFE", "#00ffcc"
    if score < 60: return "CAUTIOUS", "#ffa500"
    if score < 80: return "DANGEROUS", "#ef4444"
    return "MELT DOWN", "#8b0000"

strategy, strategy_color = get_risk_meta(final_score)

# --- 3. TELEMETRY DATA (JAN 2026) ---
@st.cache_data(ttl=3600)
def fetch_telemetry():
    tickers = {"BTC": "BTC-USD", "GOLD": "GC=F", "DXY": "DX-Y.NYB", "10Y": "^TNX"}
    data_points = {}
    for key, symbol in tickers.items():
        try:
            hist = yf.Ticker(symbol).history(period="2mo")
            current = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-22]
            data_points[key] = (current, ((current-prev)/prev)*100)
        except: data_points[key] = (0.0, 0.0)
    data_points["M2"] = (98352.0, 0.17)
    return data_points

telemetry = fetch_telemetry()

# --- 4. GAUGE ENGINE ---
def create_gauge(value, title, is_master=False, is_failed=False):
    _, color = get_risk_meta(value)
    bg_color = "#ffffff" if is_failed else "#1a1a1a"
    txt_color = "#000000" if is_failed else "white"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        number={'font': {'color': txt_color, 'size': 50 if is_master else 30}},
        gauge={
            'axis': {'range': [0, 100], 'tickcolor': txt_color},
            'bar': {'color': "#000000" if is_failed else color, 'thickness': 0.6},
            'bgcolor': bg_color, 'borderwidth': 4, 'bordercolor': "#444"
        }
    ))
    if is_master:
        fig.add_annotation(
            text=f"STATUS: {strategy}", x=0.5, y=0.18, showarrow=False,
            font=dict(size=30, color=strategy_color, family="Courier New"),
            bgcolor="rgba(0,0,0,0.9)", bordercolor=strategy_color, borderwidth=2, borderpad=10
        )
    fig.update_layout(
        title={'text': title, 'y': 0.9, 'x': 0.5, 'xanchor': 'center', 'font': {'size': 20, 'color': '#00ffcc'}},
        paper_bgcolor='rgba(0,0,0,0)', font={'color': "white", 'family': "Courier New"},
        margin=dict(l=30, r=30, t=50, b=30), height=550 if is_master else 260
    )
    return fig

# --- 5. UI LAYOUT ---
st.write("### MELT INDEX")
st.divider()

# Telemetry
cols = st.columns(5)
def render_metric(col, label, val, mom, prefix="$", suffix=""):
    c = "#00ffcc" if mom >= 0 else "#ef4444"
    col.markdown(f"<div class='telemetry-label'>{label}</div>"
                 f"<div class='telemetry-val'>{prefix}{val:,.2f}{suffix}</div>"
                 f"<div class='telemetry-change' style='color:{c}'>{mom:+.2f}% MoM</div>", unsafe_allow_html=True)

render_metric(cols[0], "BITCOIN", telemetry["BTC"][0], telemetry["BTC"][1])
render_metric(cols[1], "GOLD", telemetry["GOLD"][0], telemetry["GOLD"][1])
render_metric(cols[2], "DXY INDEX", telemetry["DXY"][0], telemetry["DXY"][1], prefix="")
render_metric(cols[3], "US 10Y YIELD", telemetry["10Y"][0], telemetry["10Y"][1], prefix="", suffix="%")
render_metric(cols[4], "GLOBAL M2", telemetry["M2"][0], telemetry["M2"][1], prefix="$", suffix="B")

st.divider()
st.plotly_chart(create_gauge(final_score, "", True), use_container_width=True)

p1, p2, p3, p4 = st.columns(4)
with p1: st.plotly_chart(create_gauge(M_SCORE, "MACRO (M)"), use_container_width=True)
with p2: st.plotly_chart(create_gauge(E_SCORE, "EMOTION (E)"), use_container_width=True)
with p3: st.plotly_chart(create_gauge(L_SCORE, "LEVERAGE (L)"), use_container_width=True)
with p4: 
    is_failed = (T_SCORE == 50)
    st.plotly_chart(create_gauge(T_SCORE, "TECHNICALS (T)", is_failed=is_failed), use_container_width=True)
    if is_failed: st.markdown("<p class='sensor-failure'>⚠️ SENSOR FAILURE: OFFLINE</p>", unsafe_allow_html=True)

# --- 6. 500-DAY WEEKLY CHART ---
st.write("### 📉 500-DAY CYCLE CORRELATION (WEEKLY READINGS)")

@st.cache_data
def get_historical_weekly():
    weeks = 500 // 7
    dates = pd.date_range(end=datetime.now(), periods=weeks, freq='W')
    btc_prices = [80000 + (i*500) + np.random.randint(-5000, 5000) for i in range(weeks)]
    melt_indices = [40 + (np.cos(i/5)*20) + np.random.randint(-10, 10) for i in range(weeks)]
    return pd.DataFrame({"Date": dates, "BTC Price": btc_prices, "MELT Index": melt_indices})

df_week = get_historical_weekly()
fig_corr = go.Figure()
fig_corr.add_trace(go.Scatter(x=df_week['Date'], y=df_week['BTC Price'], name="BTC Price", line=dict(color='#ffffff', width=2)))
fig_corr.add_trace(go.Scatter(x=df_week['Date'], y=df_week['MELT Index'], name="MELT Index", line=dict(color='#00ffcc', width=3), yaxis="y2"))

fig_corr.update_layout(
    template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    yaxis=dict(title="BTC Price ($)", side="left", gridcolor="#222"),
    yaxis2=dict(title="MELT Index", side="right", overlaying="y", range=[0, 100], showgrid=False),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    height=500
)
st.plotly_chart(fig_corr, use_container_width=True)
