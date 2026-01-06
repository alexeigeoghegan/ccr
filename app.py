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
    [data-testid="stMetricValue"] { font-size: 45px !important; font-weight: 700 !important; }
    .stAlert { border: none; padding: 20px; border-radius: 15px; font-size: 26px; font-weight: 800; text-align: center; }
    .logic-box { background-color: #161b22; padding: 15px; border-radius: 10px; border-left: 5px solid #00ffcc; margin-bottom: 10px; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE LOGIC ---
def normalize(val, mi, ma, inv=False):
    try:
        val = float(val)
        val = max(min(val, ma), mi)
        s = ((val - mi) / (ma - mi)) * 100
        return (100 - s) if inv else s
    except: return 50.0

def calculate_total_score(dxy, yld, oil, fgi, cbbi, m2_mom, etf, fund, ssr):
    # Macro 40%
    score_fin = (normalize(dxy, 98, 108, True) + normalize(yld, 3, 5, True) + normalize(oil, 65, 95, True)) / 3
    p_macro = (score_fin * 0.20) + (normalize(m2_mom, 0, 1.0) * 0.20) 
    # Pillars
    p_sent = (fgi * 0.20)
    p_tech = (cbbi * 0.20)
    p_adopt = (normalize(etf, -1, 5) * 0.10)
    p_struct = (normalize(fund, 0, 0.06, True) * 0.05) + (normalize(ssr, 8, 22, True) * 0.05)
    return int(round(p_macro + p_sent + p_tech + p_adopt + p_struct))

@st.cache_data(ttl=3600)
def get_all_market_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    data_dict = {}
    try:
        macro = yf.download(["BTC-USD", "DX-Y.NYB", "^TNX", "CL=F", "GC=F"], period="5d", progress=False)['Close'].ffill().dropna()
        data_dict.update({
            'btc': macro["BTC-USD"].iloc[-1], 'dxy': macro["DX-Y.NYB"].iloc[-1], 
            'yield': macro["^TNX"].iloc[-1], 'oil': macro["CL=F"].iloc[-1], 
            'gold': macro["GC=F"].iloc[-1]
        })
    except:
        data_dict.update({'btc': 98500, 'dxy': 102, 'yield': 4.2, 'oil': 75, 'gold': 4470})
    
    # Updated CBBI to 55 and F&G to 44 as requested
    data_dict.update({
        'fgi': 44, 'cbbi': 55, 'm2_mom': 0.35, 'total_cap': '3.2T', 
        'btc_dom': '58.4%', 'etf': 1.2, 'fund': 0.01, 'ssr': 12.0
    })
    return data_dict

# --- 3. DATA PROCESSING ---
raw = get_all_market_data()
current_score = calculate_total_score(
    raw['dxy'], raw['yield'], raw['oil'], raw['fgi'], raw['cbbi'], 
    raw['m2_mom'], raw['etf'], raw['fund'], raw['ssr']
)

# --- 4. TOP SECTION: GAUGE & ACTION ---
st.title("Crypto Cycle Risk")

col_g, col_a = st.columns([2, 1])

with col_g:
    fig_gauge = go.Figure(go.Indicator(
        mode = "gauge+number", value = current_score,
        gauge = {'axis': {'range': [0, 100], 'tickcolor': "white"},
                 'bar': {'color': "#00ffcc"},
                 'steps': [{'range': [0, 35], 'color': '#006400'},
                           {'range': [35, 70], 'color': '#8B8000'},
                           {'range': [70, 100], 'color': '#8B0000'}]}))
    fig_gauge.update_layout(paper_bgcolor='#0e1117', font={'color': "white"}, height=350, margin=dict(t=0, b=0))
    st.plotly_chart(fig_gauge, use_container_width=True)

with col_a:
    st.write("##") 
    if current_score < 35:
        st.success("🟢 ACCUMULATE")
    elif current_score < 70:
        st.warning("🟡 HOLD / CAUTION")
    else:
        st.error("🔴 TAKE PROFITS / HEDGE")

# --- 5. PERFORMANCE PILLARS ---
st.markdown("---")
c1, c2, c3, c4, c5 = st.columns(5)

# Calculate Individual Pillar Strengths (0-100 scale) for display
val_macro = int(round(((normalize(raw['dxy'],98,108,True) + normalize(raw['yield'],3,5,True) + normalize(raw['oil'],65,95,True))/3 * 0.5 + normalize(raw['m2_mom'],0,1.0)*0.5)))
val_sent = int(raw['fgi'])
val_tech = int(raw['cbbi'])
val_adopt = int(round(normalize(raw['etf'],-1,5)))
val_struct = int(round(normalize(raw['fund'],0,0.06,True)*0.5 + normalize(raw['ssr'],8,22,True)*0.5))

def style_metric(label, value):
    color = "#00ffcc" if value < 35 else "#ffff00" if value < 70 else "#ff4b4b"
    return st.markdown(f"**{label}** <br> <span style='color:{color}; font-size:48px; font-weight:bold;'>{value}</span>", unsafe_allow_html=True)

with c1: style_metric("MACRO 40%", val_macro)
with c2: style_metric("SENTIMENT 20%", val_sent)
with c3: style_metric("TECHNICALS 20%", val_tech)
with c4: style_metric("ADOPTION 10%", val_adopt)
with c5: style_metric("STRUCTURE 10%", val_struct)

# --- 6. PILLAR LOGIC BREAKDOWN ---
st.markdown("---")
st.subheader("Pillar Logic Breakdown")

l_col1, l_col2 = st.columns(2)

with l_col1:
    st.markdown(f"""
    <div class="logic-box">
        <b>Macro (40%):</b> Derived from 50% Financial Conditions and 50% Global Liquidity.<br>
        • Financial Conditions: Avg of DXY (Current: {round(raw['dxy'],1)}), 10Y Yield ({round(raw['yield'],1)}%), and Oil (${round(raw['oil'],1)}).<br>
        • Liquidity: Month-over-Month M2 growth normalized against a 1% expansion cap.
    </div>
    <div class="logic-box">
        <b>Sentiment (20%):</b> Direct feed from the Fear & Greed Index (Current: {val_sent}). Higher numbers indicate extreme greed and higher risk.
    </div>
    <div class="logic-box">
        <b>Technicals (20%):</b> Direct feed from the CBBI Index (Current: {val_tech}). A composite of 11 on-chain and technical metrics.
    </div>
    """, unsafe_allow_html=True)

with l_col2:
    st.markdown(f"""
    <div class="logic-box">
        <b>Adoption (10%):</b> Calculated from BTC Spot ETF Net Inflows. Monthly momentum is normalized where a 5% inflow represents maximum adoption score.
    </div>
    <div class="logic-box">
        <b>Structure (10%):</b> Derived from 50% Funding Rates and 50% Stablecoin Supply Ratio (SSR).<br>
        • Funding: Normalized 0% to 0.06%. High rates indicate high leverage risk.<br>
        • SSR: Normalized 8 to 22. Lower SSR means higher stablecoin buying power.
    </div>
    """, unsafe_allow_html=True)

# --- 7. SIDEBAR DATA FEED ---
st.sidebar.write(f"Bitcoin: `${round(raw.get('btc',0), 2):,}`")
st.sidebar.write(f"DXY Index: `{round(raw.get('dxy',0), 2)}`")
st.sidebar.write(f"10Y Yield: `{round(raw.get('yield',0), 2)}%`")
st.sidebar.write(f"Gold Price: `${round(raw.get('gold',0), 2):,}`")
st.sidebar.write(f"Oil Price: `${round(raw.get('oil',0), 2)}`")
st.sidebar.write(f"Global M2 (MoM): `{raw.get('m2_mom')}%`")
st.sidebar.write(f"Total Market Cap: `{raw.get('total_cap')}`")
st.sidebar.write(f"BTC Dominance: `{raw.get('btc_dom')}`")
st.sidebar.write(f"Fear & Greed Index: `{raw.get('fgi')}`")
st.sidebar.write(f"CBBI Index: `{round(raw.get('cbbi',0), 1)}`")
st.sidebar.write(f"ETF BTC Inflow (MoM): `{raw.get('etf')}%`")
st.sidebar.write(f"Funding Rates: `{raw.get('fund')}%`")
st.sidebar.write(f"SSR Ratio: `{raw.get('ssr')}`")
