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
    .logic-box { background-color: #1c2128; padding: 18px; border-radius: 10px; border: 1px solid #30363d; margin-bottom: 12px; font-size: 14px; line-height: 1.6; min-height: 180px; }
    .instr-box { background-color: #0d1117; padding: 20px; border-radius: 8px; margin: 20px 0; font-size: 15px; border: 1px solid #30363d; border-top: 4px solid #00ffcc; text-align: center; }
    .sidebar-header { font-size: 16px; font-weight: 700; color: #00ffcc; margin-top: 20px; border-bottom: 1px solid #30363d; padding-bottom: 5px; text-transform: uppercase; letter-spacing: 1px; }
    .data-label { color: #8b949e; font-size: 14px; margin-bottom: 2px; }
    .data-value { color: #ffffff; font-family: 'Courier New', monospace; font-size: 16px; font-weight: bold; margin-bottom: 10px; }
    .trend-label { font-size: 12px; font-weight: bold; margin-top: -10px; text-align: center; }
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

def create_mini_dial(label, value, trend_val=0):
    clr = "#00ffcc" if value < 35 else "#fbbf24" if value < 70 else "#ef4444"
    trend_color = "#00ffcc" if trend_val < 0 else "#ef4444" # Risk dropping is green
    trend_arrow = "▼" if trend_val < 0 else "▲"
    
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=value,
        title={'text': label, 'font': {'size': 18, 'color': '#ffffff', 'weight': 'bold'}},
        gauge={
            'axis': {'range': [0, 100], 'visible': False},
            'bar': {'color': clr},
            'bgcolor': "#1c2128",
            'borderwidth': 0}))
    
    fig.add_annotation(x=0.5, y=-0.15, text=f"<span style='color:{trend_color}'>{trend_arrow} {abs(trend_val):.1f}% (30d)</span>", 
                       showarrow=False, font=dict(size=12))
    
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "#ffffff"}, height=180, margin=dict(t=30, b=40, l=15, r=15))
    return fig

@st.cache_data(ttl=3600)
def get_live_data():
    # Baselines for trend comparison (representing 30 days ago)
    b = {'m2': 0.40, 'etf': 1.5, 'stb': 1.8, 'fgi': 42, 'cbbi': 50, 'fund': 0.01}
    
    d = {'btc': 94230, 'dxy': 98.60, 'yield': 4.18, 'oil': 57.2, 'fgi': 48, 'cbbi': 54, 
         'm2_mom': 0.65, 'etf_mom': 1.1, 'stable_mom': 2.4, 'fund': 0.011}
    
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
        
    # Calculate Pillar Trends (Current Risk - Previous Risk estimate)
    d['trend_m'] = (d['dxy_mom'] + d['yld_mom']) / 2 # simplified trend proxy
    d['trend_a'] = d['etf_mom'] - b['etf']
    d['trend_s'] = d['fgi'] - b['fgi']
    d['trend_t'] = d['cbbi'] - b['cbbi']
    d['trend_e'] = (d['fund'] - b['fund']) * 100
    
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

# --- 4. SIDEBAR (MASTER FEEDS) ---
with st.sidebar:
    st.title("MASTER Feeds")
    st.markdown(f"**Updated:** {datetime.now().strftime('%d %b %Y')}")
    st.markdown('<div class="sidebar-header">Macro Drivers</div>', unsafe_allow_html=True)
    st.markdown(f'<p class="data-label">DXY Index</p><p class="data-value">{d["dxy"]:.2f} ({d.get("dxy_mom",0):+.2f}%)</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="data-label">10Y Yield</p><p class="data-value">{d["yield"]:.2f}% ({d.get("yld_mom",0):+.2f}%)</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="data-label">Crude Oil</p><p class="data-value">${d["oil"]:.2f} ({d.get("oil_mom",0):+.2f}%)</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="data-label">Global M2 MoM</p><p class="data-value">{d["m2_mom"]}%</p>', unsafe_allow_html=True)
    st.markdown('<div class="sidebar-header">Other Drivers</div>', unsafe_allow_html=True)
    st.markdown(f'<p class="data-label">BTC Spot Price</p><p class="data-value">${d["btc"]:,.0f}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="data-label">ETF Inflow MoM</p><p class="data-value">{d["etf_mom"]}%</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="data-label">Stablecoin Growth</p><p class="data-value">{d["stable_mom"]}%</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="data-label">Fear & Greed</p><p class="data-value">{d["fgi"]}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="data-label">CBBI Index</p><p class="data-value">{d["cbbi"]}</p>', unsafe_allow_html=True)
    st.markdown(f'<p class="data-label">Funding Rate</p><p class="data-value">{d["fund"]}%</p>', unsafe_allow_html=True)

# --- 5. MAIN UI ---
st.title("MASTER Crypto Risk Index")

# Top Row: Mini Dials (M A S T E) with Trends
c1, c2, c3, c4, c5 = st.columns(5)
c1.plotly_chart(create_mini_dial("MACRO (M)", risk_m, d['trend_m']), use_container_width=True)
c2.plotly_chart(create_mini_dial("ADOPTION (A)", risk_a, d['trend_a']), use_container_width=True)
c3.plotly_chart(create_mini_dial("SENTIMENT (S)", risk_s, d['trend_s']), use_container_width=True)
c4.plotly_chart(create_mini_dial("TECHNIC. (T)", risk_t, d['trend_t']), use_container_width=True)
c5.plotly_chart(create_mini_dial("EXPOSURE (E)", risk_e, d['trend_e']), use_container_width=True)

st.markdown("---")

# Middle Row: Main Gauge
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

# Bottom Row: Detailed Methodology
st.markdown("---")
st.subheader("MASTER Methodology & Thresholds")
m1, m2, m3 = st.columns(3)
with m1:
    st.markdown(f"""<div class="logic-box"><b>(M) MACRO:</b> 50% Financial Momentum / 50% Liquidity.<br>
    Calculated as a Bipolar Scale where <b>±{B_DXY}% DXY</b>, <b>±{B_YLD}% Yields</b>, and <b>±{B_OIL}% Oil</b> represent the 0-100 risk bounds. 
    Liquidity (M2) is inverted: a <b>+{B_M2}%</b> growth results in 0 risk, while a <b>-{B_M2}%</b> contraction triggers 100 risk.</div>""", unsafe_allow_html=True)
    st.markdown(f"""<div class="logic-box"><b>(A) ADOPTION:</b> Blends institutional and native demand.<br>
    Scores 50% on <b>BTC ETF Net Inflows</b> (±{B_ETF}% bound) and 50% on <b>Stablecoin Supply Expansion</b> (±{B_STB}% bound). 
    Expansion at or above the upper bound result in 0 risk, signaling high capital absorption.</div>""", unsafe_allow_html=True)
with m2:
    st.markdown(f"""<div class="logic-box"><b>(S) SENTIMENT:</b> Uses the Crypto Fear & Greed Index.<br>
    Direct 1:1 mapping of market psychology. Extreme Greed (>75) signals cycle-peak exuberance and high reversal probability, while Extreme Fear (<25) suggests accumulation opportunities.</div>""", unsafe_allow_html=True)
    st.markdown(f"""<div class="logic-box"><b>(E) EXPOSURE:</b> Monitors structural leverage.<br>
    Calculated linearly based on 8-hour <b>Funding Rates</b>. A 0% rate (neutral spot demand) results in 0 risk, while a rise to <b>{S_FND}%</b> (extreme long leverage) triggers 100 risk.</div>""", unsafe_allow_html=True)
with m3:
    st.markdown(f"""<div class="logic-box"><b>(T) TECHNICALS:</b> Driven by the CBBI Index.<br>
    Aggregates 11 on-chain and technical oscillators (Pi Cycle, Puell Multiple, MVRV Z-Score). This acts as the "Cycle Clock," measuring historical price exhaustion on a 0-100 scale.</div>""", unsafe_allow_html=True)

st.markdown(f"""
    <div class="instr-box">
        <b>Purpose:</b> This dashboard aggregates various data to help determine risk optimal capital allocation.
        <br><i><b>Disclaimer:</b> Not financial advice. Data for educational purposes only.</i>
    </div>
    """, unsafe_allow_html=True)
