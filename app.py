import streamlit as st
import yfinance as yf
import requests
import pandas as pd
import urllib3
import plotly.graph_objects as go
from datetime import datetime, timedelta

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Crypto Cycle Risk", layout="wide")

# Custom Professional Theme & Metric Styling
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    [data-testid="stMetricValue"] { font-size: 45px !important; font-weight: 700 !important; }
    .stAlert { border: none; padding: 20px; border-radius: 15px; font-size: 26px; font-weight: 800; text-align: center; }
    /* Metric Color Logic Classes */
    .green-text { color: #00ffcc; }
    .yellow-text { color: #ffff00; }
    .red-text { color: #ff4b4b; }
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

def get_color(score):
    if score < 35: return "green"
    if score < 70: return "orange"
    return "red"

def calculate_index(dxy, yld, oil, fgi, cbbi, m2_mom, etf, fund, ssr):
    score_fin = (normalize(dxy, 98, 108, True) + normalize(yld, 3, 5, True) + normalize(oil, 65, 95, True)) / 3
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
        # Fetch 45 days to ensure 30 trading days of data
        macro = yf.download(["BTC-USD", "DX-Y.NYB", "^TNX", "CL=F", "GC=F"], period="2mo", progress=False)['Close'].ffill().dropna()
        data_dict.update({
            'btc': macro["BTC-USD"].iloc[-1],
            'dxy': macro["DX-Y.NYB"].iloc[-1], 
            'yield': macro["^TNX"].iloc[-1], 
            'oil': macro["CL=F"].iloc[-1], 
            'gold': macro["GC=F"].iloc[-1],
            'macro_df': macro
        })
        cbbi_res = requests.get("https://colintalkscrypto.com/cbbi/data/latest.json", headers=headers, verify=False).json()
        conf = cbbi_res.get("Confidence", cbbi_res)
        latest_ts = max(conf.keys(), key=int)
        data_dict['cbbi'] = float(conf[latest_ts]) * 100
    except:
        data_dict.update({'btc': 98500, 'dxy':102,'yield':4.2,'oil':75,'gold':4470,'cbbi':54.0})
    
    data_dict.update({'fgi': 44, 'm2_mom': 0.35, 'total_cap': '3.2T', 'btc_dom': '58.4%', 'etf': 1.2, 'fund': 0.01, 'ssr': 12.0})
    return data_dict

# --- 3. DATA PROCESSING ---
raw = get_all_market_data()
history = []
if 'macro_df' in raw:
    # 30 Day Trend Calculation
    for i in range(30):
        idx = -(i+1)
        score = calculate_index(raw['macro_df']["DX-Y.NYB"].iloc[idx], raw['macro_df']["^TNX"].iloc[idx], raw['macro_df']["CL=F"].iloc[idx],
                                raw.get('fgi'), raw.get('cbbi'), 0.35, 1.2, 0.01, 12.0)
        history.append({"Date": raw['macro_df'].index[idx].date(), "Score": score})
df_history = pd.DataFrame(history).sort_values("Date")
current_score = int(round(df_history["Score"].iloc[-1])) if not df_history.empty else 50

# --- 4. TOP SECTION: GAUGE & ACTION ---
st.title("🛡️ Crypto Cycle Risk")

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
    st.write("##") # Spacing
    if current_score < 35:
        st.success("🟢 ACCUMULATE")
    elif current_score < 70:
        st.warning("🟡 HOLD / CAUTION")
    else:
        st.error("🔴 TAKE PROFITS / HEDGE")
    st.write("Current index represents a consolidated risk score across 5 institutional pillars.")

# --- 5. PERFORMANCE PILLARS (Integers & Color Coded) ---
st.markdown("---")
c1, c2, c3, c4, c5 = st.columns(5)

# Calculate Pillar Totals for color logic
val_macro = int(round((normalize(raw.get('dxy'),98,108,True) + normalize(raw.get('yield'),3,5,True) + normalize(raw.get('oil'),65,95,True))/3 * 0.5 + normalize(raw.get('m2_mom'),0,1.0)*0.5))
val_sent = int(raw.get('fgi'))
val_tech = int(round(raw.get('cbbi')))
val_adopt = int(round(normalize(raw.get('etf'),-1,5)))
val_struct = int(round(normalize(raw.get('fund'),0,0.06,True)*0.5 + normalize(raw.get('ssr',12),8,22,True)*0.5))

def style_metric(label, value):
    color = "#00ffcc" if value < 35 else "#ffff00" if value < 70 else "#ff4b4b"
    return st.markdown(f"**{label}** <br> <span style='color:{color}; font-size:48px; font-weight:bold;'>{value}</span>", unsafe_allow_html=True)

with c1: style_metric("MACRO 40%", val_macro)
with c2: style_metric("SENTIMENT 20%", val_sent)
with c3: style_metric("TECHNICALS 20%", val_tech)
with c4: style_metric("ADOPTION 10%", val_adopt)
with c5: style_metric("STRUCTURE 10%", val_struct)

# --- 6. 30-DAY TREND CHART ---
st.markdown("### 📈 30-Day Risk Trend")
fig_line = go.Figure(go.Scatter(x=df_history["Date"], y=df_history["Score"], mode='lines', line=dict(color='#00ffcc', width=4), fill='tozeroy', fillcolor='rgba(0, 255, 204, 0.1)'))
fig_line.update_layout(paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', font={'color': 'white'}, height=350, margin=dict(t=10, b=10), 
                       xaxis=dict(showgrid=False), yaxis=dict(range=[0, 100], showgrid=True, gridcolor='#333'))
st.plotly_chart(fig_line, use_container_width=True)

# --- 7. PILLAR DESCRIPTIONS ---
st.markdown("---")
d_col1, d_col2 = st.columns(2)
with d_col1:
    st.markdown("**Macro:** Global liquidity (M2 MoM) and financial conditions (DXY, Yields, Gold). Weak USD and high liquidity favor risk assets.")
    st.markdown("**Sentiment:** Market psychology via Fear & Greed. Overheated sentiment indicates high-risk zones.")
    st.markdown("**Technicals:** CBBI composite. Aggregates on-chain maturity and technical oscillators to find cyclical extremes.")
with d_col2:
    st.markdown("**Adoption:** Net BTC Spot ETF flows. Institutional capital absorption serves as a primary demand indicator.")
    st.markdown("**Structure:** Market leverage. Excessive funding rates and low stablecoin supply ratios signal structural instability.")

# --- 8. SIDEBAR DATA FEED ---
st.sidebar.header("📡 Data Feed")
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
