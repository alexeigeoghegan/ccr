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
    div[data-testid="stMetricValue"] { font-size: 35px; color: #00ffcc; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. DATA COLLECTION ENGINE ---
@st.cache_data(ttl=3600)
def get_market_data():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    data = {}
    
    try:
        # MACRO: Financial Conditions
        macro_df = yf.download(["DX-Y.NYB", "^TNX", "CL=F"], period="5d", progress=False)['Close']
        data['dxy'] = macro_df["DX-Y.NYB"].iloc[-1]
        data['yield'] = macro_df["^TNX"].iloc[-1]
        data['oil'] = macro_df["CL=F"].iloc[-1]

        # SENTIMENT: Fear & Greed
        fng_res = requests.get("https://api.alternative.me/fng/", headers=headers, timeout=10)
        data['fgi'] = int(fng_res.json()['data'][0]['value'])

        # TECHNICALS: CBBI (Fixed dictionary parsing)
        cbbi_res = requests.get("https://colintalkscrypto.com/cbbi/data/latest.json", headers=headers, timeout=12, verify=False)
        cbbi_json = cbbi_res.json()
        
        # Latest logic: get the last value in the "Confidence" dict
        confidence_dict = cbbi_json.get("Confidence", cbbi_json)
        latest_timestamp = max(confidence_dict.keys())
        data['cbbi'] = float(confidence_dict[latest_timestamp]) * 100

        # PROXIES
        data['m2_growth'] = 4.2    
        data['etf_inflows'] = 1.5  
        data['funding'] = 0.01     
        data['ssr'] = 13.5         
        
    except Exception as e:
        st.sidebar.warning(f"Note: Live API sync issues ({e}). Using neutral defaults.")
        data = {
            'dxy': 102.0, 'yield': 4.2, 'oil': 78.0, 
            'fgi': 50.0, 'cbbi': 50.0, 'm2_growth': 4.0, 
            'etf_inflows': 1.0, 'funding': 0.01, 'ssr': 15.0
        }
    return data

def normalize(val, mi, ma, inv=False):
    val = max(min(val, ma), mi)
    s = ((val - mi) / (ma - mi)) * 100
    return (100 - s) if inv else s

# Execute data fetch
d = get_market_data()

# --- 3. PILLAR CALCULATIONS (40/20/20/10/10) ---
score_fin = (normalize(d['dxy'], 98, 108, True) + normalize(d['yield'], 3, 5, True) + normalize(d['oil'], 65, 95, True)) / 3
score_liq = normalize(d['m2_growth'], -1, 10)
p_macro = (score_fin * 0.20) + (score_liq * 0.20) 

p_sent = (d['fgi'] * 0.20)
p_tech = (d['cbbi'] * 0.20)
p_adopt = (normalize(d['etf_inflows'], -1, 5) * 0.10)
p_struct = (normalize(d['funding'], 0, 0.06, True) * 0.05) + (normalize(d['ssr'], 8, 22, True) * 0.05)

total_index = round(p_macro + p_sent + p_tech + p_adopt + p_struct, 1)

# --- 4. HEADER & GAUGE CHART ---
st.title("🛡️ Crypto Cycle Risk")
st.caption("Strategic Multi-Pillar Market Analysis")

# Gauge Chart at the Top
fig = go.Figure(go.Indicator(
    mode = "gauge+number",
    value = total_index,
    domain = {'x': [0, 1], 'y': [0, 1]},
    title = {'text': "Market Risk Level", 'font': {'size': 24}},
    gauge = {
        'axis': {'range': [None, 100], 'tickwidth': 1},
        'bar': {'color': "#00ffcc"},
        'bgcolor': "white",
        'borderwidth': 2,
        'bordercolor': "gray",
        'steps': [
            {'range': [0, 30], 'color': '#008000'},
            {'range': [30, 70], 'color': '#FFFF00'},
            {'range': [70, 100], 'color': '#FF0000'}],
        'threshold': {
            'line': {'color': "red", 'width': 4},
            'thickness': 0.75,
            'value': 90}}))

fig.update_layout(paper_bgcolor = '#0e1117', font = {'color': "white", 'family': "Arial"}, height=350)
st.plotly_chart(fig, use_container_width=True)

# --- 5. UI DASHBOARD ---
st.markdown("---")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("MACRO (40%)", f"{round((p_macro/0.40), 1)}%")
c2.metric("SENTIMENT (20%)", f"{round(d['fgi'], 1)}%")
c3.metric("TECHNICALS (20%)", f"{round(d['cbbi'], 1)}%")
c4.metric("ADOPTION (10%)", f"{round(p_adopt/0.10, 1)}%")
c5.metric("STRUCTURE (10%)", f"{round(p_struct/0.10, 1)}%")

# Sidebar Feed
st.sidebar.header("Raw Market Feed")
st.sidebar.write(f"DXY Index: `{round(d['dxy'], 2)}`")
st.sidebar.write(f"10Y Yield: `{round(d['yield'], 2)}%`")
st.sidebar.write(f"CBBI Index: `{round(d['cbbi'], 1)}`")
