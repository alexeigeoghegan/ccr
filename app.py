import streamlit as st
import yfinance as yf
import requests
import pandas as pd
import urllib3
import plotly.graph_objects as go

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Crypto Cycle Risk", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    [data-testid="stMetricValue"] { font-size: 40px !important; font-weight: 700 !important; }
    .stAlert { border: none; padding: 25px; border-radius: 15px; font-size: 32px; font-weight: 900; text-align: center; color: white !important; }
    .logic-box { background-color: #161b22; padding: 15px; border-radius: 10px; border-left: 5px solid #00ffcc; margin-bottom: 10px; font-size: 14px; line-height: 1.6; min-height: 120px; }
    .instr-box { background-color: #1c2128; padding: 20px; border: 1px solid #30363d; border-radius: 15px; margin: 20px 0; font-size: 15px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIC: RISK NORMALIZATION ---
def norm_risk(val, sensitivity, inv=False):
    try:
        score = (float(val) / float(sensitivity)) * 100
        score = max(min(score, 100), 0)
        return (100 - score) if inv else score
    except: return 50.0

@st.cache_data(ttl=3600)
def get_data():
    # 2026 Baseline Snapshot
    d = {'btc': 93246, 'dxy': 98.60, 'yield': 4.18, 'oil': 57.0, 'gold': 4506, 'fgi': 44, 'cbbi': 55, 
         'm2_mom': 0.35, 'cap': '3.2T', 'dom': '58.4%', 'etf': 1.2, 'stable_growth': 2.1, 'fund': 0.01, 'ssr': 12.0}
    try:
        data = yf.download(["BTC-USD", "DX-Y.NYB", "^TNX", "CL=F", "GC=F"], period="2mo", progress=False)['Close'].ffill().dropna()
        def get_raw_mom(col):
            curr, prev = data[col].iloc[-1], data[col].iloc[-22]
            return ((curr - prev) / prev) * 100, curr
        dxy_m, dxy_c = get_raw_mom("DX-Y.NYB")
        yld_m, yld_c = get_raw_mom("^TNX")
        oil_m, oil_c = get_raw_mom("CL=F")
        d.update({'btc': data["BTC-USD"].iloc[-1], 'dxy': dxy_c, 'yield': yld_c, 'oil': oil_c, 'gold': data["GC=F"].iloc[-1],
                  'dxy_mom': dxy_m, 'yld_mom': yld_m, 'oil_mom': oil_m})
    except:
        d.update({'dxy_mom': 0.46, 'yld_mom': 0.72, 'oil_mom': 3.06})
    return d

d = get_data()

# --- 3. FIXED GOLDEN SETTINGS ---
S_DXY, S_YLD, S_OIL, S_M2, S_ETF, S_STB, S_FND = 2.5, 5.0, 12.0, 0.8, 4.0, 5.0, 0.08

# --- 4. PILLAR SCORING ---
risk_mac_fin = (norm_risk(d['dxy_mom'], S_DXY) + norm_risk(d['yld_mom'], S_YLD) + norm_risk(d['oil_mom'], S_OIL)) / 3
risk_mac_liq = norm_risk(d['m2_mom'], S_M2, inv=True) 
risk_mac = int(round(risk_mac_fin * 0.5 + risk_mac_liq * 0.5))

risk_sen, risk_tec = int(d['fgi']), int(d['cbbi']) 
risk_ado_etf = norm_risk(d['etf'], S_ETF, inv=True)
risk_ado_stb = norm_risk(d['stable_growth'], S_STB, inv=True)
risk_ado = int(round(risk_ado_etf * 0.5 + risk_ado_stb * 0.5))
risk_str = int(round(norm_risk(d['fund'], S_FND)))

total_score = int(round((risk_mac*0.4) + (risk_sen*0.2) + (risk_tec*0.
