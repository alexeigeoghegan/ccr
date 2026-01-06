import streamlit as st
import yfinance as yf
import pandas as pd
import urllib3
import plotly.graph_objects as go
from datetime import datetime

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="MASTER Crypto Risk Index", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    .stAlert { border: none; padding: 25px; border-radius: 12px; font-size: 28px; font-weight: 800; text-align: center; color: white !important; }
    .logic-box { background-color: #1c2128; padding: 20px; border-radius: 10px; border: 1px solid #30363d; margin-top: 10px; font-size: 14px; line-height: 1.7; }
    .instr-box { background-color: #0d1117; padding: 20px; border-radius: 8px; margin-top: 20px; font-size: 15px; border: 1px solid #30363d; border-top: 4px solid #00ffcc; text-align: center; }
    .sidebar-header { font-size: 16px; font-weight: 700; color: #00ffcc; margin-top: 20px; border-bottom: 1px solid #30363d; padding-bottom: 5px; text-transform: uppercase; letter-spacing: 1px; }
    .data-label { color: #8b949e; font-size: 14px; margin-bottom: 2px; }
    .data-value { color: #ffffff; font-family: 'Courier New', monospace; font-size: 16px; font-weight: bold; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE FUNCTIONS ---
def norm_bipolar(val, bound, inv=False):
    """Maps range [-bound, +bound] to [0, 100] Risk."""
    try:
        val = float(val)
        score = ((val - (-bound)) / (bound - (-bound))) * 100
        score = max(min(score, 100), 0)
        return (100 - score) if inv else score
    except: return 50.0

def create_mini_dial(label, value):
    clr = "#00ffcc" if value < 35 else "#fbbf24" if value < 70 else "#ef4444"
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value,
        title={'text': label, 'font': {'size': 18, 'color': '#ffffff', 'weight': 'bold'}},
        gauge={'axis': {'range': [0, 100], 'visible': False}, 'bar': {'color': clr}, 'bgcolor': "#1c2128", 'borderwidth': 0}))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "#ffffff"}, height=160, margin=dict(t=30, b=0, l=15, r=15))
    return fig

@st.cache_data(ttl=3600)
def get_live_data():
    # 2026 Strategy Snapshot
    d = {'btc': 94230, 'dxy': 98.60, 'yield': 4.18, 'oil': 57.2, 'fgi': 48, 'cbbi': 54, 
         'm2_mom': 0.65, 'etf_mom': 1.1, 'stable_mom': 2.4, 'fund': 0.011, 'oi_mom': 4.2}
    try:
        data = yf.download(["BTC-USD", "DX-Y.NYB", "^TNX", "CL=F"], period="2mo", progress=False)['Close'].ffill().dropna()
        def calc_mom(col):
            curr, prev = data[col].iloc[-1], data[col].iloc[-22]
            return ((curr - prev) / prev) * 100, curr
        dxy_m, dxy_c = calc_mom("DX-Y.NYB")
        yld_m, yld_c = calc_mom("^TNX")
        oil_m, oil_c = calc_mom("CL=F")
        d.update({'btc': data["BTC-USD"].iloc[-1], 'dxy': dxy_c, 'yield': yld_c, 'oil': oil_c, 'dxy_mom': dxy_m, 'yld_mom': yld_m, 'oil_mom': oil_m})
    except:
        d.update({'dxy_mom': 0.46, 'yld_mom': 0.72, 'oil_mom': 3.10})
    return d

# --- 3. MASTER SCORING ENGINE ---
d = get_live_data()
B_DXY, B_YLD, B_OIL, B_M2, B_ETF, B_STB, S_FND, B_OI = 2.5, 5.0, 10.0, 2.5, 5.0, 5.0, 0.08, 10.0

risk_m = int(round(((norm_bipolar(d.get('dxy_mom',0), B_DXY, False) + norm_bipolar(d.get('yld_mom',0), B_YLD, False) + norm_bipolar(d.get('oil_mom',0), B_OIL, False)) / 3) * 0.5 + norm_bipolar(d['m2_mom'], B_M2, True) * 0.5))
risk_a = int(round(norm_bipolar(d['etf_mom'], B_ETF, True) * 0.5 + norm_bipolar(d['stable_mom'], B_STB, True) * 0.5))
risk_s, risk_t = int(d['fgi']), int(d['cbbi'])
risk_e_fnd = (max(min(d['fund'], S_FND), 0) / S_FND) * 100
risk_e_oi = norm_bipolar(d['oi_mom'], B_OI, False)
risk_e = int(round(risk_e_fnd * 0.5 + risk_e_oi * 0.5))

risk_score = int(round((risk_m*0.4) + (risk_s*0.2) + (risk_t*0.2) + (risk_a*0.1) + (risk_e*0.1)))

if risk_score < 35: act_label, act_color, g_color = "ACCUMULATE", "#008060", "#00ffcc"
elif risk_score < 70: act_label, act_color, g_color = "HOLD", "#d97706", "#fbbf24"
else: act_label, act_color, g_color = "TAKE PROFITS / HEDGE", "#b91c1c", "#ef4444"

# --- 4. SIDEBAR (MASTER FEEDS) ---
with st.sidebar:
    st.title("MASTER Feeds")
    st.markdown(f"**Updated:** {datetime.now().strftime('%d %b %Y')}")
    st.markdown('<div class="sidebar-header">Macro Drivers</div>', unsafe_allow_html=True)
    st.markdown(f'<p class="data-label">DXY Index</p><p class="data-value">{d["dxy"]:.2f} ({d.get("dxy_mom",0):+.2f}%)</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="data-label">10Y Yield</p><p class="data-value">{d["yield"]:.2f}% ({d.get("yld_mom",0):+.2f}%)</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="data-label">Global M2 MoM</p><p class="data-value">{d["m2_mom"]}%</p>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-header">Adoption & Exposure</div>', unsafe_allow_html=True)
    st.markdown(f'<p class="data-label">ETF Inflow MoM</p><p class="data-value">{d["etf_mom"]}%</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="data-label">Stablecoin Growth</p><p class="data-value">{d["stable_mom"]}%</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="data-label">Funding Rate</p><p class="data-value">{d["fund"]}%</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="data-label">Open Interest MoM</p><p class="data-value">{d["oi_mom"]:+.2f}%</p>', unsafe_allow_html=True)

    st.markdown('<div class="sidebar-header">Other Drivers</div>', unsafe_allow_html=True)
    st.markdown(f'<p class="data-label">Fear & Greed</p><p class="data-value">{d["fgi"]}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="data-label">CBBI Index</p><p class="data-value">{d["cbbi"]}</p>', unsafe_allow_html=True)

# --- 5. MAIN UI ---
st.title("MASTER Crypto Risk Index")
c1, c2, c3, c4, c5 = st.columns(5)
c1.plotly_chart(create_mini_dial("MACRO (M)", risk_m), use_container_width=True)
c2.plotly_chart(create_mini_dial("ADOPTION (A)", risk_a), use_container_width=True)
c3.plotly_chart(create_mini_dial("SENTIMENT (S)", risk_s), use_container_width=True)
c4.plotly_chart(create_mini_dial("TECHNIC. (T)", risk_t), use_container_width=True)
c5.plotly_chart(create_mini_dial("EXPOSURE (E)", risk_e), use_container_width=True)

st.markdown("---")
col_gauge, col_action = st.columns([1.8, 1])
with col_gauge:
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=risk_score,
        title={'text': "TOTAL RISK (R)", 'font': {'size': 24, 'color': '#ffffff', 'weight': 'bold'}},
        gauge={'axis': {'range': [0, 100], 'tickcolor': "#8b949e"}, 'bar': {'color': g_color}, 'bgcolor': "rgba(0,0,0,0)",
               'steps': [{'range': [0, 35], 'color': 'rgba(0, 255, 204, 0.1)'}, {'range': [35, 70], 'color': 'rgba(251, 191, 36, 0.1)'}, {'range': [70, 100], 'color': 'rgba(239, 68, 68, 0.1)'}]}))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "#ffffff"}, height=380, margin=dict(t=50, b=0))
    st.plotly_chart(fig, use_container_width=True)

with col_action:
    st.write("##")
    st.write("##")
    st.markdown(f'<div class="stAlert" style="background-color:{act_color};">{act_label}</div>', unsafe_allow_html=True)

# Consolidated Methodology Box
st.markdown("---")
st.subheader("Threshold Specifications")
st.markdown(f"""
<div class="logic-box">
    <b>(M) Macro:</b> Split 50/50 between Financial Momentum and Global Liquidity. Risk scales bipolarly where 0 risk is ±{B_DXY}% for DXY, ±{B_YLD}% for Yields, and ±{B_OIL}% for Oil. M2 Liquidity is inverted: a +{B_M2}% expansion results in 0 risk, while a -{B_M2}% contraction results in 100 risk.<br><br>
    <b>(A) Adoption:</b> Blends institutional demand (BTC ETF Flows) and crypto-native liquidity (Stablecoin Supply Expansion). Both use a ±5% bipolar scale where growth equals 0 risk and contraction equals 100 risk.<br><br>
    <b>(S) Sentiment:</b> Maps the Fear & Greed Index 1:1. High scores (>75) indicate dangerous retail exuberance; low scores (<25) indicate cyclical fear.<br><br>
    <b>(T) Technicals:</b> Maps the CBBI Index 1:1. This aggregates 11 on-chain and technical oscillators to track the 4-year cycle maturity.<br><br>
    <b>(E) Exposure:</b> Monitors systemic leverage. Calculated 50% on Funding Rates (0% to {S_FND}% ceiling) and 50% on Open Interest MoM change (±{B_OI}% bipolar scale).
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
    <div class="instr-box">
        <b>Purpose:</b> This dashboard aggregates various data to help determine risk optimal capital allocation.
        <br><i><b>Disclaimer:</b> Not financial advice. Data for educational purposes only.</i>
    </div>
    """, unsafe_allow_html=True)
