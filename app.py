import streamlit as st
import yfinance as yf
import requests
import pandas as pd
import urllib3
import plotly.graph_objects as go
from datetime import datetime

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. PAGE SETUP ---
st.set_page_config(page_title="Crypto Cycle Risk", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 32px; color: #00ffcc; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE LOGIC ---
def normalize(val, mi, ma, inv=False):
    val = max(min(val, ma), mi)
    s = ((val - mi) / (ma - mi)) * 100
    return (100 - s) if inv else s

def calculate_index(dxy, yld, oil, fgi, cbbi, m2, etf, fund, ssr):
    score_fin = (normalize(dxy, 98, 108, True) + normalize(yld, 3, 5, True) + normalize(oil, 65, 95, True)) / 3
    p_macro = (score_fin * 0.20) + (normalize(m2, -1, 10) * 0.20) 
    p_sent = (fgi * 0.20)
    p_tech = (cbbi * 0.20)
    p_adopt = (normalize(etf, -1, 5) * 0.10)
    p_struct = (normalize(fund, 0, 0.06, True) * 0.05) + (normalize(ssr, 8, 22, True) * 0.05)
    return round(p_macro + p_sent + p_tech + p_adopt + p_struct, 1)

@st.cache_data(ttl=3600)
def get_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        # Fetch Macro
        macro = yf.download(["DX-Y.NYB", "^TNX", "CL=F"], period="1mo", progress=False)['Close']
        macro = macro.ffill().dropna()
        
        # Fetch Sentiment (Last 10 days)
        fng = requests.get("https://api.alternative.me/fng/?limit=10", headers=headers).json()
        fng_vals = [int(x['value']) for x in fng['data']]
        
        # Fetch Technicals (CBBI)
        cbbi_res = requests.get("https://colintalkscrypto.com/cbbi/data/latest.json", headers=headers, verify=False).json()
        conf = cbbi_res.get("Confidence", cbbi_res)
        latest_ts = max(conf.keys(), key=int)
        cbbi_val = float(conf[latest_ts]) * 100
        
        history = []
        for i in range(7):
            idx = -(i+1)
            history.append({
                "Date": macro.index[idx].date(),
                "Risk Score": calculate_index(
                    macro["DX-Y.NYB"].iloc[idx], macro["^TNX"].iloc[idx], macro["CL=F"].iloc[idx],
                    fng_vals[i] if i < len(fng_vals) else 50, cbbi_val, 4.2, 1.5, 0.01, 13.5
                )
            })
        return pd.DataFrame(history).sort_values("Date"), {
            'dxy': macro["DX-Y.NYB"].iloc[-1], 'yield': macro["^TNX"].iloc[-1], 'oil': macro["CL=F"].iloc[-1],
            'fgi': fng_vals[0], 'cbbi': cbbi_val, 'm2': 4.2, 'etf': 1.5, 'fund': 0.01, 'ssr': 13.5
        }
    except Exception as e:
        st.sidebar.error(f"Sync Issue: {e}")
        return pd.DataFrame(), {}

df_history, d = get_data()
total_score = df_history["Risk Score"].iloc[-1] if not df_history.empty else 50.0

# --- 3. UI DASHBOARD ---
st.title("🛡️ Crypto Cycle Risk")
st.caption("Weighting: Macro 40% | Sent 20% | Tech 20% | Adopt 10% | Struct 10%")

# Gauge Chart
fig_gauge = go.Figure(go.Indicator(
    mode = "gauge+number", value = total_score,
    gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#00ffcc"},
             'steps': [{'range': [0, 30], 'color': '#006400'},
                       {'range': [30, 70], 'color': '#8B8000'},
                       {'range': [70, 100], 'color': '#8B0000'}]}))
fig_gauge.update_layout(paper_bgcolor='#0e1117', font={'color': "white"}, height=300)
st.plotly_chart(fig_gauge, use_container_width=True)

# Pillars
st.markdown("---")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("MACRO", f"{round(normalize(d['dxy'],98,108,True)*0.5 + normalize(d['m2'],-1,10)*0.5,1)}%")
col2.metric("SENTIMENT", f"{d['fgi']}%")
col3.metric("TECHNICALS", f"{round(d['cbbi'],1)}%")
col4.metric("ADOPTION", f"{round(normalize(d['etf'],-1,5),1)}%")
col5.metric("STRUCTURE", f"{round(normalize(d['fund'],0,0.06,True)*0.5 + normalize(d['ssr'],8,22,True)*0.5,1)}%")

# Trend Line
st.markdown("### 📈 7-Day Risk Trend")
fig_line = go.Figure(go.Scatter(x=df_history["Date"], y=df_history["Risk Score"], 
                               mode='lines+markers', line=dict(color='#00ffcc', width=3),
                               fill='tozeroy', fillcolor='rgba(0, 255, 204, 0.1)'))
fig_line.update_layout(paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', font={'color': 'white'}, height=300)
st.plotly_chart(fig_line, use_container_width=True)

st.sidebar.write(f"DXY Index: `{round(d.get('dxy',0), 2)}`")
st.sidebar.write(f"10Y Yield: `{round(d.get('yield',0), 2)}%`")
