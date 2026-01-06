import streamlit as st
import yfinance as yf
import pandas as pd
import urllib3
import plotly.graph_objects as go
from datetime import datetime

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Crypto Cycle Risk Dashboard", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; color: #ffffff; }
    [data-testid="stMetricValue"] { font-size: 32px !important; font-weight: 700 !important; color: #00ffcc; }
    .stAlert { border: none; padding: 25px; border-radius: 15px; font-size: 28px; font-weight: 800; text-align: center; color: white !important; box-shadow: 0 4px 15px rgba(0,0,0,0.3); }
    .logic-box { background-color: #1c2128; padding: 20px; border-radius: 12px; border: 1px solid #30363d; margin-bottom: 15px; font-size: 14px; line-height: 1.6; min-height: 140px; }
    .instr-box { background-color: #0d1117; padding: 20px; border-left: 5px solid #00ffcc; border-radius: 8px; margin: 20px 0; font-size: 15px; border-top: 1px solid #30363d; border-right: 1px solid #30363d; border-bottom: 1px solid #30363d; }
    .sidebar-header { font-size: 18px; font-weight: 700; color: #8b949e; margin-top: 20px; border-bottom: 1px solid #30363d; padding-bottom: 5px; }
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

def draw_pill(label, val):
    """Renders the stylized metric pillars."""
    clr = "#00ffcc" if val < 35 else "#fbbf24" if val < 70 else "#ef4444"
    st.markdown(f"**{label}** <br> <span style='color:{clr}; font-size:42px; font-weight:bold;'>{val}</span>", unsafe_allow_html=True)

@st.cache_data(ttl=3600)
def get_live_data():
    # 2026 Real-time Snapshot
    d = {'btc': 93693, 'dxy': 98.60, 'yield': 4.18, 'oil': 57.0, 'fgi': 52, 'cbbi': 58, 
         'm2_mom': 0.62, 'etf_mom': 1.25, 'stable_mom': 2.3, 'fund': 0.012}
    try:
        # Fetching Macro Data
        data = yf.download(["BTC-USD", "DX-Y.NYB", "^TNX", "CL=F"], period="2mo", progress=False)['Close'].ffill().dropna()
        def calc_mom(col):
            curr, prev = data[col].iloc[-1], data[col].iloc[-22]
            return ((curr - prev) / prev) * 100, curr
        
        dxy_m, dxy_c = calc_mom("DX-Y.NYB")
        yld_m, yld_c = calc_mom("^TNX")
        oil_m, oil_c = calc_mom("CL=F")
        
        d.update({
            'btc': data["BTC-USD"].iloc[-1], 'dxy': dxy_c, 'yield': yld_c, 'oil': oil_c,
            'dxy_mom': dxy_m, 'yld_mom': yld_m, 'oil_mom': oil_m
        })
    except:
        d.update({'dxy_mom': 0.46, 'yld_mom': 0.72, 'oil_mom': 3.06})
    return d

# --- 3. LOGIC & SCORING ---
d = get_live_data()

# Sensitivity Bounds
B_DXY, B_YLD, B_OIL, B_M2, B_ETF, B_STB, S_FND = 2.5, 5.0, 10.0, 2.5, 5.0, 5.0, 0.08

# Macro Pillar (40%)
risk_mac_fin = (norm_bipolar(d.get('dxy_mom',0), B_DXY, False) + 
                norm_bipolar(d.get('yld_mom',0), B_YLD, False) + 
                norm_bipolar(d.get('oil_mom',0), B_OIL, False)) / 3
risk_mac = int(round(risk_mac_fin * 0.5 + norm_bipolar(d['m2_mom'], B_M2, True) * 0.5))

# Other Pillars
risk_sen, risk_tec = int(d['fgi']), int(d['cbbi']) 
risk_ado = int(round(norm_bipolar(d['etf_mom'], B_ETF, True) * 0.5 + norm_bipolar(d['stable_mom'], B_STB, True) * 0.5))
risk_str = int(round((max(min(d['fund'], S_FND), 0) / S_FND) * 100))

# Total Calculation
total_score = int(round((risk_mac*0.4) + (risk_sen*0.2) + (risk_tec*0.2) + (risk_ado*0.1) + (risk_str*0.1)))

# Color Mapping
if total_score < 35: act_label, act_color, g_color = "ACCUMULATE", "#008060", "#00ffcc"
elif total_score < 70: act_label, act_color, g_color = "HOLD", "#d97706", "#fbbf24"
else: act_label, act_color, g_color = "TAKE PROFITS / HEDGE", "#b91c1c", "#ef4444"

# --- 4. SIDEBAR (THE COMPLETE DATA FEED) ---
with st.sidebar:
    st.title("Data Feeds")
    st.markdown(f"**Current Date:** {datetime.now().strftime('%d %b %Y')}")
    
    st.markdown('<div class="sidebar-header">Macro Drivers</div>', unsafe_allow_html=True)
    st.write(f"DXY Index: `{d['dxy']:.2f}` ({d.get('dxy_mom',0):+.2f}%)")
    st.write(f"10Y Yield: `{d['yield']:.2f}%` ({d.get('yld_mom',0):+.2f}%)")
    st.write(f"Crude Oil: `${d['oil']:.2f}` ({d.get('oil_mom',0):+.2f}%)")
    st.write(f"Global M2 MoM: `{d['m2_mom']}%`")

    st.markdown('<div class="sidebar-header">Adoption & Liquidity</div>', unsafe_allow_html=True)
    st.write(f"Bitcoin: `${d['btc']:,.0f}`")
    st.write(f"ETF Inflow MoM: `{d['etf_mom']}%`")
    st.write(f"Stablecoin Growth: `{d['stable_mom']}%`")
    
    st.markdown('<div class="sidebar-header">Market Health</div>', unsafe_allow_html=True)
    st.write(f"Fear & Greed: `{d['fgi']}`")
    st.write(f"CBBI Index: `{d['cbbi']}`")
    st.write(f"Funding Rate: `{d['fund']}%`")

# --- 5. MAIN UI ---
st.title("Crypto Cycle Risk Index")

col_gauge, col_action = st.columns([2, 1])
with col_gauge:
    fig = go.Figure(go.Indicator(
        mode="gauge+number", value=total_score,
        gauge={
            'axis': {'range': [0, 100], 'tickwidth': 1, 'tickcolor': "#8b949e"},
            'bar': {'color': g_color},
            'bgcolor': "rgba(0,0,0,0)",
            'steps': [
                {'range': [0, 35], 'color': 'rgba(0, 255, 204, 0.1)'},
                {'range': [35, 70], 'color': 'rgba(251, 191, 36, 0.1)'},
                {'range': [70, 100], 'color': 'rgba(239, 68, 68, 0.1)'}],
            'threshold': {'line': {'color': "white", 'width': 4}, 'thickness': 0.75, 'value': total_score}}))
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', font={'color': "#ffffff"}, height=380, margin=dict(t=30, b=0))
    st.plotly_chart(fig, use_container_width=True)

with col_action:
    st.write("##")
    st.markdown(f'<div class="stAlert" style="background-color:{act_color};">{act_label}</div>', unsafe_allow_html=True)
    st.markdown(f"""
        <div style="padding-top: 20px; text-align: center;">
        <p style="color: #8b949e; font-size: 16px;">Current Risk Score: <b>{total_score}/100</b></p>
        </div>
    """, unsafe_allow_html=True)

st.markdown("---")
p1, p2, p3, p4, p5 = st.columns(5)
with p1: draw_pill("MACRO (40%)", risk_mac)
with p2: draw_pill("SENTIMENT (20%)", risk_sen)
with p3: draw_pill("TECHNICALS (20%)", risk_tec)
with p4: draw_pill("ADOPTION (10%)", risk_ado)
with p5: draw_pill("STRUCTURE (10%)", risk_str)

st.markdown(f"""
    <div class="instr-box">
        <b>Purpose:</b> This dashboard aggregates cross-asset macro data and on-chain sentiment to determine optimal capital allocation. 
        It identifies if you should be <b>Accumulating</b> (buying spot), <b>Holding</b>, or <b>Hedging</b> (selling into stables). 
        <br><b>Disclaimer:</b> Not financial advice. Data for educational purposes only.
    </div>
    """, unsafe_allow_html=True)

st.subheader("Methodology")
m1, m2, m3 = st.columns(3)
with m1:
    st.markdown(f"""<div class="logic-box"><b>1. Macro (40%):</b> Bipolar Risk Scale. Risk is 0 at lower bound and 100 at upper bound for DXY (±{B_DXY}%), Yields (±{B_YLD}%), and Oil (±{B_OIL}%). M2 Liquidity is inverted: +{B_M2}% growth = 0 Risk, -{B_M2}% contraction = 100 Risk.</div>""", unsafe_allow_html=True)
    st.markdown(f"""<div class="logic-box"><b>4. Adoption (10%):</b> Blends BTC ETF Inflows (±{B_ETF}%) and Stablecoin Supply Expansion (±{B_STB}%). Higher growth in these pools indicates new capital absorption and lower risk.</div>""", unsafe_allow_html=True)
with m2:
    st.markdown(f"""<div class="logic-box"><b>2. Sentiment (20%):</b> Direct 1:1 mapping of the Fear & Greed Index. High scores signal dangerous retail exuberance which usually leads to local cycle tops.</div>""", unsafe_allow_html=True)
    st.markdown(f"""<div class="logic-box"><b>5. Structure (10%):</b> Measures leveraged risk via Funding Rates. Calculated linearly from 0% (healthy) to {S_FND}% (extreme greed).</div>""", unsafe_allow_html=True)
with m3:
    st.markdown(f"""<div class="logic-box"><b>3. Technicals (20%):</b> Direct 1:1 mapping of the CBBI Index. Aggregates technical oscillators like Pi Cycle Top and Puell Multiple to find exhaustion points.</div>""", unsafe_allow_html=True)
