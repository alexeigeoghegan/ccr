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
    .sensor-failure { color: #000000 !important; background-color: #ffffff !important; padding: 5px; font-weight: bold; font-family: monospace; text-align: center; border-radius: 5px; }
    .telemetry-label { font-size: 0.75rem; color: #888; font-family: 'Courier New', monospace; text-transform: uppercase; }
    .telemetry-val { font-size: 1.2rem; font-weight: bold; color: #ffffff; }
    .telemetry-change { font-size: 0.75rem; font-family: monospace; }
    .schematic-text { font-size: 0.85rem; color: #888; font-family: 'Courier New', monospace; line-height: 1.4; padding: 10px; border-left: 1px solid #444; margin-top: -20px; }
    .master-schematic { text-align: center; color: #00ffcc; font-family: 'Courier New', monospace; margin-top: -30px; margin-bottom: 30px; font-size: 0.9rem; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. ENGINE LOGIC (LOCKED WEIGHTS) ---
W_M, W_E, W_L, W_T = 0.4, 0.2, 0.2, 0.2

# Macro Z-Score Inputs (Jan 2026 Protocol)
m2_z, net_liq_z, dxy_z, hike_cut_ratio = 1.2, -0.5, 0.8, 20

def calculate_macro_pillar(m2, liq, dxy, hc):
    # Mapping Z-scores (-3 to 3) to 0-100 (High Score = High Risk)
    m2_s = np.clip((1 - (m2 + 3) / 6) * 100, 0, 100)
    liq_s = np.clip((1 - (liq + 3) / 6) * 100, 0, 100)
    dxy_s = np.clip(((dxy + 3) / 6) * 100, 0, 100)
    return int((m2_s * 0.25) + (liq_s * 0.25) + (dxy_s * 0.25) + (hc * 0.25))

M_VAL = calculate_macro_pillar(m2_z, net_liq_z, dxy_z, hike_cut_ratio)
E_VAL, L_VAL = 29, 54

@st.cache_data(ttl=3600)
def get_technicals():
    try:
        import requests
        r = requests.get("https://colintalkscrypto.com/cbbi/data/latest.json", timeout=3)
        latest_key = sorted(r.json().keys())[-1]
        return int(r.json()[latest_key] * 100)
    except: return 50 # SENSOR BLIND

T_VAL = get_technicals()
final_index = int((M_VAL * W_M) + (E_VAL * W_E) + (L_VAL * W_L) + (T_VAL * W_T))

def get_risk_meta(score):
    if score < 20: return "MELT UP", "#006400"
    if score < 40: return "SAFE", "#00ffcc"
    if score < 60: return "CAUTIOUS", "#ffa500"
    if score < 80: return "DANGEROUS", "#ef4444"
    return "MELT DOWN", "#8b0000"

strategy, strategy_color = get_risk_meta(final_index)

# --- 3. TELEMETRY FETCH ---
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
    
    # 2026 Core Market Data
    data["TOTAL_MCAP"] = (3050.0, 0.10) # $3.05 Trillion
    data["MVRV_X10"] = (21.4, 1.5)     # MVRV Z-Score 2.14 * 10
    data["M2"] = (98352.0, 0.17)
    data["ALT_SEASON"] = (17, -5.5)
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
    fig.update_layout(title={'text': title, 'y': 0.9, 'x': 0.5, 'font': {'size': 18, 'color': '#00ffcc'}},
                      paper_bgcolor='rgba(0,0,0,0)', font={'family': "Courier New"}, margin=dict(l=30, r=30, t=50, b=30), height=500 if is_master else 260)
    return fig

# --- 5. UI LAYOUT ---
st.write("### MELT INDEX: PROFESSIONAL MACRO TERMINAL")
st.divider()

# High-Density Telemetry Bar
t_cols = st.columns(8)
def r_met(col, label, val, mom, pref="$", suff="", is_txt=False):
    c = "#00ffcc" if mom >= 0 else "#ef4444"
    col.markdown(f"<div class='telemetry-label'>{label}</div><div class='telemetry-val'>{pref}{val:,.2f}{suff}</div><div class='telemetry-change' style='color:{c}'>{mom:+.2f}% MoM</div>", unsafe_allow_html=True)

r_met(t_cols[0], "BITCOIN", tel["BTC"][0], tel["BTC"][1])
