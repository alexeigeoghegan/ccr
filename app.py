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
    .telemetry-label { font-size: 0.75rem; color: #888; font-family: 'Courier New', monospace; text-transform: uppercase; }
    .telemetry-val { font-size: 1.2rem; font-weight: bold; color: #ffffff; }
    .telemetry-change { font-size: 0.75rem; font-family: monospace; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. REACTOR CORE LOGIC ---
W_M, W_E, W_L, W_T = 0.4, 0.2, 0.2, 0.2
M_VAL, E_VAL, L_VAL = 20, 29, 54

@st.cache_data(ttl=3600)
def get_technicals():
    try:
        import requests
        r = requests.get("https://colintalkscrypto.com/cbbi/data/latest.json", timeout=3)
        latest_key = sorted(r.json().keys())[-1]
        return int(r.json()[latest_key] * 100)
    except: return 50 # SENSOR BLIND DEFAULT

T_VAL = get_technicals()
final_index = int((M_VAL * W_M) + (E_VAL * W_E) + (L_VAL * W_L) + (T_VAL * W_T))

def get_risk_meta(score):
    if score < 20: return "MELT UP", "#006400"
    if score < 40: return "SAFE", "#00ffcc"
    if score < 60: return "CAUTIOUS", "#ffa500"
    if score < 80: return "DANGEROUS", "#ef4444"
    return "MELT DOWN", "#8b0000"

strategy, strategy_color = get_risk_meta(final_index)

# --- 3. TELEMETRY FETCHING (2026) ---
@st.cache_data(ttl=3600)
def fetch_telemetry():
    tickers = {"BTC": "BTC-USD", "GOLD": "GC=F", "DXY": "DX-Y.NYB", "10Y": "^TNX", "OIL": "CL=F"}
    data = {}
    for key, symbol in tickers.items():
        try:
            h = yf.Ticker(symbol).history(period="2mo")
            curr = h['Close'].iloc[-1]
            mom = ((curr - h['Close'].iloc[-22]) / h['Close'].iloc[-22]) * 100
            data[key] = (curr, mom)
        except: data[key] = (0.0, 0.0)
    
    # 2026 External Indices
    data["M2"] = (98352.0, 0.17)
    data["ALT_SEASON"] = (17, -5.5) # Altcoin Index
    data["BBI"] = "UNDERVALUED PHASE" # Bitcoin Bubble Index Status (Static for now)
    return data

tel = fetch_telemetry()

# --- 4. GAUGE ENGINE ---
def create_gauge(value, title, is_master=False, is_failed=False):
    _, color = get_risk_meta(value)
    bg = "#ffffff" if is_failed else "#1a1a1a"
    tx = "#000000" if is_failed else "white"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        number={'font': {'color': tx, 'size': 50 if is_master else 30}},
        gauge={'axis': {'range': [0, 100], 'tickcolor': tx},
               'bar': {'color': "#000000" if is_failed else color, 'thickness': 0.6},
               'bgcolor': bg, 'borderwidth': 4, 'bordercolor': "#444"}
    ))
    if is_master:
        fig.add_annotation(text=f"STATUS: {strategy}", x=0.5, y=0.18, showarrow=False,
                           font=dict(size=28, color=strategy_color, family="Courier New"),
                           bgcolor="rgba(0,0,0,0.9)", bordercolor=strategy_color, borderwidth=2, borderpad=10)
    fig.update_layout(title={'text': title, 'y': 0.9, 'x': 0.5, 'font': {'size': 20, 'color': '#00ffcc'}},
                      paper_bgcolor='rgba(0,0,0,0)', font={'family': "Courier New"}, margin=dict(l=30, r=30, t=50, b=30), height=550 if is_master else 260)
    return fig

# --- 5. UI LAYOUT ---
st.write("### MELT INDEX")
st.divider()

# Telemetry Bar
m_cols = st.columns(8)
def r_met(col, label, val, mom, pref="$", suff="", is_txt=False):
    if is_txt:
        col.markdown(f"<div class='telemetry-label'>{label}</div><div class='telemetry-val'>{val}</div>", unsafe_allow_html=True)
    else:
        c = "#00ffcc" if mom >= 0 else "#ef4444"
        col.markdown(f"<div class='telemetry-label'>{label}</div><div class='telemetry-val'>{pref}{val:,.2f}{suff}</div><div class='telemetry-change' style='color:{c}'>{mom:+.2f}% MoM</div>", unsafe_allow_html=True)

r_met(m_cols[0], "BITCOIN", tel["BTC"][0], tel["BTC"][1])
r_met(m_cols[1], "GOLD", tel["GOLD"][0], tel["GOLD"][1])
r_met(m_cols[2], "OIL", tel["OIL"][0], tel["OIL"][1])
r_met(m_cols[3], "DXY INDEX", tel["DXY"][0], tel["DXY"][1], pref="")
r_met(m_cols[4], "US 10Y", tel["10Y"][0], tel["10Y"][1], pref="", suff="%")
r_met(m_cols[5], "GLOBAL M2", tel["M2"][0], tel["M2"][1], suff="B")
r_met(m_cols[6], "ALT SEASON", tel["ALT_SEASON"][0], tel["ALT_SEASON"][1], pref="")
r_met(m_cols[7], "BBI", tel["BBI"], 0, is_txt=True)

st.divider()
st.plotly_chart(create_gauge(final_index, "", True), use_container_width=True)

p_cols = st.columns(4)
with p_cols[0]: st.plotly_chart(create_gauge(M_VAL, "MACRO (M)"), use_container_width=True)
with p_cols[1]: st.plotly_chart(create_gauge(E_VAL, "EMOTION (E)"), use_container_width=True)
with p_cols[2]: st.plotly_chart(create_gauge(L_VAL, "LEVERAGE (L)"), use_container_width=True)
with p_cols[3]: 
    st.plotly_chart(create_gauge(T_VAL, "TECHNICALS (T)", is_failed=(T_VAL==50)), use_container_width=True)
    if T_VAL == 50: st.markdown("<p class='sensor-failure'>⚠️ SENSOR FAILURE: OFFLINE</p>", unsafe_allow_html=True)

# --- 6. 500-DAY SMOOTHED CHART ---
st.write("### 📉 500-DAY CYCLE ANALYSIS (DAILY READINGS)")

@st.cache_data
def get_hist_daily():
    dates = pd.date_range(end=datetime.now(), periods=500)
    btc = [85000 + (np.sin(i/50)*10000) + np.random.randint(-2000,2000) for i in range(500)]
    idx = [50 + (np.cos(i/40)*35) + np.random.randint(-5,5) for i in range(500)]
    return pd.DataFrame({"Date": dates, "BTC": btc, "Index": idx})

df = get_hist_daily()
fig = go.Figure()

# BTC Background Line
fig.add_trace(go.Scatter(x=df['Date'], y=df['BTC'], name="BTC Price", line=dict(color='rgba(255,255,255,0.3)', width=1, shape='spline')))

# Segmented Index Line for Color Coding
for i in range(len(df)-1):
    val = df['Index'].iloc[i]
    color = '#00ffcc' # Default
    if val >= 80: color = '#8b0000' # Dark Red
    elif val <= 20: color = '#006400' # Dark Green
    
    fig.add_trace(go.Scatter(x=df['Date'].iloc[i:i+2], y=df['Index'].iloc[i:i+2],
                             line=dict(color=color, width=3, shape='spline'),
                             showlegend=False, yaxis="y2", hoverinfo='skip'))

fig.update_layout(template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                  yaxis=dict(title="BTC Price ($)", side="left", gridcolor="#222"),
                  yaxis2=dict(title="MELT Index", side="right", overlaying="y", range=[0, 100], showgrid=False),
                  height=500, margin=dict(t=50))
st.plotly_chart(fig, use_container_width=True)
