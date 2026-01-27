import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

# --- 1. INDUSTRIAL THEME CONFIG ---
st.set_page_config(page_title="MELT Index | Professional Macro", layout="wide")

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

# --- 2. THE RAOUL PAL "LIQUIDITY IMPULSE" MACRO ENGINE ---
# Advanced Variables for Jan 2026
m2_z = 1.2          # Global M2 Growth Z-Score
net_liq_z = -0.5    # US Net Liquidity Growth Z-Score
dxy_z = 0.8         # DXY Growth Z-Score
hike_cut_ratio = 20 # Global Central Bank Policy

def calculate_macro_pillar(m2, liq, dxy, hc):
    # Mapping Z-scores to 0-100 (High score = High Risk)
    m2_s = np.clip((1 - (m2 + 3) / 6) * 100, 0, 100)
    liq_s = np.clip((1 - (liq + 3) / 6) * 100, 0, 100)
    dxy_s = np.clip(((dxy + 3) / 6) * 100, 0, 100)
    return int((m2_s * 0.25) + (liq_s * 0.25) + (dxy_s * 0.25) + (hc * 0.25))

# --- 3. THE REACTOR CORE ---
W_M, W_E, W_L, W_T = 0.4, 0.2, 0.2, 0.2
M_VAL = calculate_macro_pillar(m2_z, net_liq_z, dxy_z, hike_cut_ratio)
E_VAL, L_VAL = 29, 54

@st.cache_data(ttl=3600)
def get_technicals():
    try:
        import requests
        r = requests.get("https://colintalkscrypto.com/cbbi/data/latest.json", timeout=3)
        latest_key = sorted(r.json().keys())[-1]
        return int(r.json()[latest_key] * 100)
    except: return 50

T_VAL = get_technicals()
final_index = int((M_VAL * W_M) + (E_VAL * W_E) + (L_VAL * W_L) + (T_VAL * W_T))

def get_risk_meta(score):
    if score < 20: return "MELT UP", "#006400"
    if score < 40: return "SAFE", "#00ffcc"
    if score < 60: return "CAUTIOUS", "#ffa500"
    if score < 80: return "DANGEROUS", "#ef4444"
    return "MELT DOWN", "#8b0000"

strategy, strategy_color = get_risk_meta(final_index)

# --- 4. PROFESSIONAL TELEMETRY (CROSS-ASSET) ---
@st.cache_data(ttl=3600)
def fetch_pro_telemetry():
    # Adding SOL-BTC (Risk On/Off) and VIX (Macro Vol)
    tickers = {
        "BTC": "BTC-USD", 
        "GOLD": "GC=F", 
        "DXY": "DX-Y.NYB", 
        "10Y": "^TNX", 
        "OIL": "CL=F",
        "SOL_BTC": "SOL-BTC", # The "Risk Appetite" Pulse
        "VIX": "^VIX"         # The "Volatility Floor"
    }
    data = {}
    for key, symbol in tickers.items():
        try:
            h = yf.Ticker(symbol).history(period="2mo")
            curr = h['Close'].iloc[-1]
            mom = ((curr - h['Close'].iloc[-22]) / h['Close'].iloc[-22]) * 100
            data[key] = (curr, mom)
        except: data[key] = (0.0, 0.0)
    
    # Static Indices for Jan 2026
    data["M2"] = (98352.0, 0.17)
    data["ALT_SEASON"] = (17, -5.5)
    data["BBI"] = "UNDERVALUED PHASE"
    return data

tel = fetch_pro_telemetry()

# --- 5. GAUGE ENGINE ---
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
    fig.update_layout(title={'text': title, 'y': 0.9, 'x': 0.5, 'font': {'size': 18, 'color': '#00ffcc'}},
                      paper_bgcolor='rgba(0,0,0,0)', font={'family': "Courier New"}, margin=dict(l=30, r=30, t=50, b=30), height=550 if is_master else 260)
    return fig

# --- 6. UI LAYOUT ---
st.write("### MELT INDEX: PROFESSIONAL MACRO TERMINAL")
st.divider()

# High-Density Telemetry Bar
t_cols = st.columns(9)
def r_met(col, label, val, mom, pref="$", suff="", is_txt=False, is_ratio=False):
    if is_txt:
        col.markdown(f"<div class='telemetry-label'>{label}</div><div class='telemetry-val'>{val}</div>", unsafe_allow_html=True)
    else:
        c = "#00ffcc" if mom >= 0 else "#ef4444"
        format_str = f"{pref}{val:.6f}{suff}" if is_ratio else f"{pref}{val:,.2f}{suff}"
        col.markdown(f"<div class='telemetry-label'>{label}</div><div class='telemetry-val'>{format_str}</div><div class='telemetry-change' style='color:{c}'>{mom:+.2f}% MoM</div>", unsafe_allow_html=True)

r_met(t_cols[0], "BITCOIN", tel["BTC"][0], tel["BTC"][1])
r_met(t_cols[1], "GOLD", tel["GOLD"][0], tel["GOLD"][1])
r_met(t_cols[2], "OIL", tel["OIL"][0], tel["OIL"][1])
r_met(t_cols[3], "DXY INDEX", tel["DXY"][0], tel["DXY"][1], pref="")
r_met(t_cols[4], "US 10Y", tel["10Y"][0], tel["10Y"][1], pref="", suff="%")
r_met(t_cols[5], "GLOBAL M2", tel["M2"][0], tel["M2"][1], suff="B")
r_met(t_cols[6], "SOL/BTC", tel["SOL_BTC"][0], tel["SOL_BTC"][1], pref="", is_ratio=True)
r_met(t_cols[7], "VIX (VOL)", tel["VIX"][0], tel["VIX"][1], pref="")
r_met(t_cols[8], "BBI", tel["BBI"], 0, is_txt=True)

st.divider()

# Master Dial
st.plotly_chart(create_gauge(final_index, "", True), use_container_width=True)

# Pillar Gauges
p_cols = st.columns(4)
with p_cols[0]: st.plotly_chart(create_gauge(M_VAL, "MACRO (M)"), use_container_width=True)
with p_cols[1]: st.plotly_chart(create_gauge(E_VAL, "EMOTION (E)"), use_container_width=True)
with p_cols[2]: st.plotly_chart(create_gauge(L_VAL, "LEVERAGE (L)"), use_container_width=True)
with p_cols[3]: 
    st.plotly_chart(create_gauge(T_VAL, "TECHNICALS (T)", is_failed=(T_VAL==50)), use_container_width=True)
    if T_VAL == 50: st.markdown("<p class='sensor-failure'>⚠️ SENSOR FAILURE: OFFLINE</p>", unsafe_allow_html=True)

st.divider()
st.caption("REACTOR STATUS: STABLE // GLOBAL LIQUIDITY IMPULSE DETECTED // CROSS-ASSET CORRELATION: POSITIVE")
