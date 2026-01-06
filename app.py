import streamlit as st
import yfinance as yf
import requests
import pandas as pd
import urllib3
import plotly.graph_objects as go
from datetime import datetime

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Crypto Cycle Risk", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 38px; color: #00ffcc; font-weight: bold; }
    .stAlert { margin-top: -20px; text-align: center; font-weight: bold; font-size: 22px; border-radius: 10px;}
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

def calculate_index(dxy, yld, oil, fgi, cbbi, m2_mom, etf, fund, ssr):
    # MACRO 40% (Fin Cond 20% + M2 MoM 20%)
    score_fin = (normalize(dxy, 98, 108, True) + normalize(yld, 3, 5, True) + normalize(oil, 65, 95, True)) / 3
    # M2 MoM normalization (0.1% to 0.8% typical range)
    p_macro = (score_fin * 0.20) + (normalize(m2_mom, 0, 1.0) * 0.20) 
    p_sent = (fgi * 0.20)
    p_tech = (cbbi * 0.20)
    p_adopt = (normalize(etf, -1, 5) * 0.10)
    p_struct = (normalize(fund, 0, 0.06, True) * 0.05) + (normalize(ssr, 8, 22, True) * 0.05)
    return round(p_macro + p_sent + p_tech + p_adopt + p_struct, 1)

@st.cache_data(ttl=3600)
def get_all_market_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    data_dict = {}
    try:
        # Macro & Gold
        macro = yf.download(["DX-Y.NYB", "^TNX", "CL=F", "GC=F"], period="1mo", progress=False)['Close'].ffill().dropna()
        data_dict.update({
            'dxy': macro["DX-Y.NYB"].iloc[-1], 
            'yield': macro["^TNX"].iloc[-1], 
            'oil': macro["CL=F"].iloc[-1], 
            'gold': macro["GC=F"].iloc[-1],
            'macro_df': macro
        })
        # Technicals
        cbbi_res = requests.get("https://colintalkscrypto.com/cbbi/data/latest.json", headers=headers, verify=False).json()
        conf = cbbi_res.get("Confidence", cbbi_res)
        latest_ts = max(conf.keys(), key=int)
        data_dict['cbbi'] = float(conf[latest_ts]) * 100
    except:
        data_dict.update({'dxy':102,'yield':4.2,'oil':75,'gold':4470,'cbbi':54.0})
    
    # Static Data Points (Updated for Jan 6, 2026)
    data_dict.update({
        'fgi': 44, 
        'm2_mom': 0.35, 
        'total_cap': '3.2T', 
        'btc_dom': '58.4%', 
        'etf': 1.2, 
        'fund': 0.01, 
        'ssr': 12.0
    })
    return data_dict

# --- 3. DATA PROCESSING ---
raw = get_all_market_data()
history = []
if 'macro_df' in raw:
    for i in range(7):
        idx = -(i+1)
        score = calculate_index(raw['macro_df']["DX-Y.NYB"].iloc[idx], raw['macro_df']["^TNX"].iloc[idx], raw['macro_df']["CL=F"].iloc[idx],
                                raw.get('fgi'), raw.get('cbbi'), 0.35, 1.2, 0.01, 12.0)
        history.append({"Date": raw['macro_df'].index[idx].date(), "Score": score})
df_history = pd.DataFrame(history).sort_values("Date")
current_score = df_history["Score"].iloc[-1] if not df_history.empty else 50.0

# --- 4. TOP SECTION: GAUGE & ACTION ---
st.title("🛡️ Crypto Cycle Risk")
st.caption("Strategic Evaluation Engine")

fig_gauge = go.Figure(go.Indicator(
    mode = "gauge+number", value = current_score,
    gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#00ffcc"},
             'steps': [{'range': [0, 35], 'color': '#006400'},
                       {'range': [35, 70], 'color': '#8B8000'},
                       {'range': [70, 100], 'color': '#8B0000'}]}))
fig_gauge.update_layout(paper_bgcolor='#0e1117', font={'color': "white"}, height=320, margin=dict(t=30, b=0))
st.plotly_chart(fig_gauge, use_container_width=True)

# RECOMMENDED ACTION
if current_score < 35:
    st.success("RECOMMENDED ACTION: 🟢 ACCUMULATE")
elif current_score < 70:
    st.warning("RECOMMENDED ACTION: 🟡 HOLD / CAUTION")
else:
    st.error("RECOMMENDED ACTION: 🔴 TAKE PROFITS / HEDGE")

# --- 5. PERFORMANCE PILLARS ---
st.markdown("---")
col1, col2, col3, col4, col5 = st.columns(5)
disp_macro = (normalize(raw.get('dxy'),98,108,True) + normalize(raw.get('yield'),3,5,True) + normalize(raw.get('oil'),65,95,True))/3 * 0.5 + normalize(raw.get('m2_mom'),0,1.0)*0.5
disp_struct = normalize(raw.get('fund'),0,0.06,True)*0.5 + normalize(raw.get('ssr',12),8,22,True)*0.5

col1.metric("MACRO 40%", int(round(disp_macro)))
col2.metric("SENTIMENT 20%", int(raw.get('fgi')))
col3.metric("TECHNICALS 20%", int(round(raw.get('cbbi'))))
col4.metric("ADOPTION 10%", int(round(normalize(raw.get('etf'),-1,5))))
col5.metric("STRUCTURE 10%", int(round(disp_struct)))

# --- 6. TREND CHART ---
st.markdown("### 📈 7-Day Risk Trend")
fig_line = go.Figure(go.Scatter(x=df_history["Date"], y=df_history["Score"], mode='lines+markers', line=dict(color='#00ffcc', width=3), fill='tozeroy', fillcolor='rgba(0, 255, 204, 0.1)'))
fig_line.update_layout(paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', font={'color': 'white'}, height=250, margin=dict(t=10, b=10), yaxis=dict(range=[0, 100], showgrid=True, gridcolor='#333'))
st.plotly_chart(fig_line, use_container_width=True)

# --- 7. PILLAR DESCRIPTIONS ---
st.markdown("---")
d_col1, d_col2 = st.columns(2)
with d_col1:
    st.markdown("**Macro:** Global liquidity (M2 MoM) and financial conditions (DXY, Yields, Gold). High liquidity and weak USD lower risk scores.")
    st.markdown("**Sentiment:** Market psychology measured by Fear & Greed. Extreme Greed (high scores) increases risk of a correction.")
    st.markdown("**Technicals:** CBBI composite using on-chain and technical metrics. Identifies where we are in the long-term parabolic cycle.")
with d_col2:
    st.markdown("**Adoption:** Net BTC Spot ETF inflows. Measures institutional absorption of supply; rising inflows suggest a stronger floor.")
    st.markdown("**Structure:** Leverage and supply ratios. High funding and low SSR ratios indicate an overheated, over-leveraged market.")

# --- 8. SIDEBAR DATA FEED ---
st.sidebar.header("📡 Data Feed")
st.sidebar.write(f"DXY Index: `{round(raw.get('dxy',0), 2)}`")
st.sidebar.write(f"10Y Yield: `{round(raw.get('yield',0), 2)}%`")
st.sidebar.write(f"Oil Price: `${round(raw.get('oil',0), 2)}`")
st.sidebar.write(f"Gold Price: `${round(raw.get('gold',0), 2)}`")
st.sidebar.write(f"Global M2 (MoM): `{raw.get('m2_mom')}%`")
st.sidebar.write(f"Total Market Cap: `{raw.get('total_cap')}`")
st.sidebar.write(f"BTC Dominance: `{raw.get('btc_dom')}`")
st.sidebar.write(f"Fear & Greed: `{raw.get('fgi')}`")
st.sidebar.write(f"CBBI Index: `{round(raw.get('cbbi',0), 1)}`")
st.sidebar.write(f"ETF BTC Inflow (MoM): `{raw.get('etf')}%`")
st.sidebar.write(f"Funding Rates: `{raw.get('fund')}%`")
st.sidebar.write(f"SSR Ratio: `{raw.get('ssr')}`")
