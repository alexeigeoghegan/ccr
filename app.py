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
    .stAlert { border: none; padding: 20px; border-radius: 12px; font-size: 24px; font-weight: 800; text-align: center; color: white !important; }
    .logic-box { background-color: #1c2128; padding: 15px; border-radius: 10px; border: 1px solid #30363d; margin-bottom: 10px; font-size: 13px; line-height: 1.5; min-height: 110px; }
    .instr-box { background-color: #0d1117; padding: 15px; border-left: 5px solid #00ffcc; border-radius: 8px; margin: 15px 0; font-size: 14px; border: 1px solid #30363d; border-left: 5px solid #00ffcc; }
    .sidebar-header { font-size: 16px; font-weight: 700; color: #8b949e; margin-top: 15px; border-bottom: 1px solid #30363d; padding-bottom: 5px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE FUNCTIONS ---
def norm_bipolar(val, bound, inv=False):
    try:
        val = float(val)
        score = ((val - (-bound)) / (bound - (-bound))) * 100
        score = max(min(score, 100), 0)
        return (100 - score) if inv else score
    except: return 50.0

def create_mini_dial(label, value):
    """Creates a small, sleek gauge for the top row pillars."""
    clr = "#00ffcc" if value < 35 else "#fbbf24" if value < 70 else "#ef4444"
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value,
        title={'text': label, 'font': {'size': 16, 'color': '#8b949e'}},
        gauge={
            'axis': {'range': [0, 100], 'visible': False},
            'bar': {'color': clr},
            'bgcolor': "#1c2128",
            'borderwidth': 0}))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "#ffffff"}, height=150, margin=dict(t=0, b=0, l=10, r=10))
    return fig

@st.cache_data(ttl=3600)
def get_live_data():
    d = {'btc': 93693, 'dxy': 98.60, 'yield': 4.18, 'oil': 57.0, 'fgi': 52, 'cbbi': 58, 
         'm2_mom': 0.62, 'etf_mom': 1.25, 'stable_mom': 2.3, 'fund': 0.012}
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
        d.update({'dxy_mom': 0.46, 'yld_mom': 0.72, 'oil_mom': 3.06})
    return d

# --- 3. MASTER SCORING ENGINE ---
d = get_live_data()
B_DXY, B_YLD, B_OIL, B_M2, B_ETF, B_STB, S_FND = 2.5, 5.0, 10.0, 2.5, 5.0, 5.0, 0.08

risk_m = int(round(((norm_bipolar(d.get('dxy_mom',0), B_DXY, False) + norm_bipolar(d.get('yld_mom',0), B_YLD, False) + norm_bipolar(d.get('oil_mom',0), B_OIL, False)) / 3) * 0.5 + norm_bipolar(d['m2_mom'], B_M2, True) * 0.5))
risk_a = int(round(norm_bipolar(d['etf_mom'], B_ETF, True) * 0.5 + norm_bipolar(d['stable_mom'], B_STB, True) * 0.5))
risk_s, risk_t = int(d['fgi']), int(d['cbbi'])
risk_e = int(round((max(min(d['fund'], S_FND), 0) / S_FND) * 100))
risk_score = int(round((risk_m*0.4) + (risk_s*0.2) + (risk_t*0.2) + (risk_a*0.1) + (risk_e*0.1)))

if risk_score < 35: act_label, act_color, g_color = "ACCUMULATE", "#008060", "#00ffcc"
elif risk_score < 70: act_label, act_color, g_color = "HOLD", "#d97706", "#fbbf24"
else: act_label, act_color, g_color = "TAKE PROFITS / HEDGE", "#b91c1c", "#ef4444"

# --- 4. SIDEBAR ---
with st.sidebar:
    st.title("MASTER Feed")
    st.markdown(f"**Updated:** {datetime.now().strftime('%d %b %Y')}")
    st.markdown('<div class="sidebar-header">Macro Drivers</div>', unsafe_allow_html=True)
    st.write(f"DXY: `{d['dxy']:.2f}` ({d.get('dxy_mom',0):+.2f}%)")
    st.write(f"10Y Yield: `{d['yield']:.2f}%` ({d.get('yld_mom',0):+.2f}%)")
    st.write(f"Crude Oil: `${d['oil']:.2f}` ({d.get('oil_mom',0):+.2f}%)")
    st.write(f"Global M2 MoM: `{d['m2_mom']}%`")
    st.markdown('<div class="sidebar-header">Other Drivers</div>', unsafe_allow_html=True)
    st.write(f"ETF Inflow: `{d['etf_mom']}%` | Stable: `{d['stable_mom']}%`")
    st.write(f"Fear & Greed: `{d['fgi']}` | CBBI: `{d['cbbi']}`")
    st.write(f"Exposure (Funding): `{d['fund']}%`")

# --- 5. MAIN UI ---
st.title("MASTER Risk Framework")

# Top Row: Mini Dials
c1, c2, c3, c4, c5 = st.columns(5)
c1.plotly_chart(create_mini_dial("MACRO (M)", risk_m), use_container_width=True)
c2.plotly_chart(create_mini_dial("ADOPTION (A)", risk_a), use_container_width=True)
c3.plotly_chart(create_mini_dial("SENTIMENT (S)", risk_s), use_container_width=True)
c4.plotly_chart(create_mini_dial("TECHNIC. (T)", risk_t), use_container_width=True)
c5.plotly_chart(create_mini_dial("EXPOSURE (E)", risk_e), use_container_width=True)

st.markdown("---")

# Middle Row: Main Gauge and Action
col_gauge, col_action = st.columns([1.8, 1])
with col_gauge:
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=risk_score,
        gauge={'axis': {'range': [0, 100], 'tickcolor': "#8b949e"}, 'bar': {'color': g_color}, 'bgcolor': "rgba(0,0,0,0)",
               'steps': [{'range': [0, 35], 'color': 'rgba(0, 255, 204, 0.1)'}, {'range': [35, 70], 'color': 'rgba(251, 191, 36, 0.1)'}, {'range': [70, 100], 'color': 'rgba(239, 68, 68, 0.1)'}]}))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "#ffffff"}, height=350, margin=dict(t=0, b=0))
    st.plotly_chart(fig, use_container_width=True)

with col_action:
    st.write("##")
    st.markdown(f'<div class="stAlert" style="background-color:{act_color};">{act_label}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="instr-box"><b>Purpose:</b> This dashboard aggregates various data into a singular measure to help determine risk optimal capital allocation. <br><br><i>Disclaimer: Not financial advice.</i></div>', unsafe_allow_html=True)

# Bottom Row: Methodology
st.markdown("---")
st.subheader("Methodology")
m1, m2, m3 = st.columns(3)
with m1:
    st.markdown(f"""<div class="logic-box"><b>1. Macro (M):</b> Bipolar Risk Scale (±{B_DXY}% DXY, ±{B_YLD}% Yield, ±{B_OIL}% Oil). M2 Liquidity is inverted: +{B_M2}% growth = 0 Risk.</div>""", unsafe_allow_html=True)
    st.markdown(f"""<div class="logic-box"><b>4. Adoption (A):</b> Blends BTC ETF Inflows (±{B_ETF}%) and Stablecoin Supply expansion (±{B_STB}%). Growth lowers risk.</div>""", unsafe_allow_html=True)
with m2:
    st.markdown(f"""<div class="logic-box"><b>2. Sentiment (S):</b> 1:1 mapping of Fear & Greed Index. Identifies dangerous retail exuberance.</div>""", unsafe_allow_html=True)
    st.markdown(f"""<div class="logic-box"><b>5. Exposure (E):</b> Measures leveraged market risk. Scaled from 0% to {S_FND}% funding.</div>""", unsafe_allow_html=True)
with m3:
    st.markdown(f"""<div class="logic-box"><b>3. Technicals (T):</b> 1:1 mapping of CBBI Index. Aggregates on-chain oscillators to find cyclical exhaustion.</div>""", unsafe_allow_html=True)
