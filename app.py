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

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 32px; color: #00ffcc; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. LOGIC FOR SCORING (Reusable for Historical) ---
def normalize(val, mi, ma, inv=False):
    val = max(min(val, ma), mi)
    s = ((val - mi) / (ma - mi)) * 100
    return (100 - s) if inv else s

def calculate_index(dxy, yld, oil, fgi, cbbi, m2, etf, fund, ssr):
    # MACRO (40%)
    score_fin = (normalize(dxy, 98, 108, True) + normalize(yld, 3, 5, True) + normalize(oil, 65, 95, True)) / 3
    score_liq = normalize(m2, -1, 10)
    p_macro = (score_fin * 0.20) + (score_liq * 0.20) 
    
    # Pillars
    p_sent = (fgi * 0.20)
    p_tech = (cbbi * 0.20)
    p_adopt = (normalize(etf, -1, 5) * 0.10)
    p_struct = (normalize(fund, 0, 0.06, True) * 0.05) + (normalize(ssr, 8, 22, True) * 0.05)
    
    return round(p_macro + p_sent + p_tech + p_adopt + p_struct, 1)

# --- 3. DATA COLLECTION ENGINE ---
@st.cache_data(ttl=3600)
def get_historical_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        # Fetch 14 days to ensure we have enough for a 7-day trailing window
        macro_df = yf.download(["DX-Y.NYB", "^TNX", "CL=F"], period="1mo", progress=False)['Close']
        macro_df = macro_df.fillna(method='ffill').dropna()
        
        # Sentiment & Technicals (Current only for simplicity, or mock historical)
        fng_res = requests.get("https://api.alternative.me/fng/?limit=10", headers=headers).json()
        fng_values = [int(x['value']) for x in fng_res['data']]
        
        # CBBI Latest
        cbbi_res = requests.get("https://colintalkscrypto.com/cbbi/data/latest.json", headers=headers, verify=False).json()
        conf = cbbi_res.get("Confidence", cbbi_res)
        latest_ts = max(conf.keys(), key=int)
        cbbi_latest = float(conf[latest_ts]) * 100
        
        # Construct a 7-day dataframe
        history = []
        for i in range(7):
            idx = -(i+1)
            day_score = calculate_index(
                macro_df["DX-Y.NYB"].iloc[idx], macro_df["^TNX"].iloc[idx], macro_df["CL=F"].iloc[idx],
                fng_values[i] if i < len(fng_values) else 50,
                cbbi_latest, # Constant for this version
                4.2, 1.5, 0.01, 13.5
            )
            history.append({"Date": macro_df.index[idx].date(), "Risk Score": day_score})
            
        return pd.DataFrame(history).sort_values("Date"), {
            'dxy': macro_df["DX-Y.NYB"].iloc[-1], 'yield': macro_df["^TNX"].iloc[-1], 
            'oil': macro_df["CL=F"].iloc[-1], 'fgi': fng_values[0], 'cbbi': cbbi_latest,
            'm2': 4.2, 'etf': 1.5, 'fund': 0.01, 'ssr': 13.5
        }
    except:
        return pd.DataFrame(), {}

df_history, d = get_historical_data()
total_index = df_history["Risk Score"].iloc[-1] if not df_history.empty else 50.0

# --- 4. HEADER & GAUGE ---
st.title("🛡️ Crypto Cycle Risk")
st.caption("Strategic Market Evaluation | 40% Macro | 20% Sent | 20% Tech | 10% Adopt | 10% Struct")

fig_gauge = go.Figure(go.Indicator(
    mode = "gauge+number", value = total_index,
    gauge = {
        'axis': {'range': [None, 100]},
        'bar': {'color': "#00ffcc"},
        'steps': [
            {'range': [0, 30], 'color': '#006400'},
            {'range': [30, 70], 'color': '#8B8000'},
            {'range': [70, 100], 'color': '#8B0000'}]}))
fig_gauge.update_layout(paper_bgcolor = '#0e1117', font = {'color': "white"}, height=300, margin=dict(t=30, b=0))
st.plotly_chart(fig_gauge, use_container_width=True)

# --- 5. PILLARS ---
st.markdown("---")
c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("MACRO", f"{round(normalize(d['dxy'],98,108,True)*0.5 + normalize(d['m2'],-1,10)*0.5,1)}%")
c2.metric("SENTIMENT", f"{d['fgi']}%")
c3.metric("TECHNICALS", f"{round(d['cbbi'],1)}%")
c4.metric("ADOPTION", f"{round(normalize(d['etf'],-1,5),1)}%")
c5.metric("STRUCTURE", f"{round(normalize(d['fund'],0,0.06,True)*0.5 + normalize(d['ssr'],8,22,True)*0.5,1)}%")

# --- 6. HISTORICAL TREND CHART ---
st.markdown("### 📈 7-Day Risk Trend")
fig_trend = go.Figure()
fig_trend.add_trace(go.Scatter(
    x=df_history["Date"], y=df_history["Risk Score"],
    mode='lines+markers', line=dict(color='#00ffcc', width=3),
    fill='tozeroy', fillcolor='rgba(0, 255, 204, 0.1)'
))
fig_trend.update_layout(
    paper_bgcolor='#0e1117', plot_bgcolor='#0e1117',
    font={'color': 'white'}, margin=dict(t=20, b=20),
    xaxis=dict(showgrid=False), yaxis=dict(showgrid=True, gridcolor='#262730', range=[0, 100])
)
st.plotly_chart(fig_trend, use_container_width=True)

# Sidebar
st.sidebar.header("Live Feed")
st.sidebar.write(f"DXY Index: `{round(d['dxy'], 2)}`")
st.sidebar.write(f"10Y Yield: `{round(d['yield'], 2)}%`")
