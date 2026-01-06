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
    div[data-testid="stMetricValue"] { font-size: 32px; color: #00ffcc; }
    .stAlert { margin-top: -20px; text-align: center; font-weight: bold; font-size: 20px;}
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

def calculate_index(dxy, yld, oil, fgi, cbbi, m2, etf, fund, ssr):
    # MACRO 40% (Fin Cond 20% + M2 20%)
    score_fin = (normalize(dxy, 98, 108, True) + normalize(yld, 3, 5, True) + normalize(oil, 65, 95, True)) / 3
    p_macro = (score_fin * 0.20) + (normalize(m2, -1, 10) * 0.20) 
    p_sent = (fgi * 0.20)
    p_tech = (cbbi * 0.20)
    p_adopt = (normalize(etf, -1, 5) * 0.10)
    # STRUCTURE 10% (Fund 5% + SSR 5%)
    p_struct = (normalize(fund, 0, 0.06, True) * 0.05) + (normalize(ssr, 8, 22, True) * 0.05)
    return round(p_macro + p_sent + p_tech + p_adopt + p_struct, 1)

@st.cache_data(ttl=3600)
def get_all_market_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    data_dict = {}
    try:
        macro = yf.download(["DX-Y.NYB", "^TNX", "CL=F"], period="1mo", progress=False)['Close'].ffill().dropna()
        data_dict.update({'dxy':macro["DX-Y.NYB"].iloc[-1], 'yield':macro["^TNX"].iloc[-1], 'oil':macro["CL=F"].iloc[-1], 'macro_df':macro})
        fng = requests.get("https://api.alternative.me/fng/?limit=10", headers=headers, timeout=10).json()
        data_dict['fng_vals'] = [int(x['value']) for x in fng['data']]
        cbbi_res = requests.get("https://colintalkscrypto.com/cbbi/data/latest.json", headers=headers, verify=False).json()
        conf = cbbi_res.get("Confidence", cbbi_res)
        latest_ts = max(conf.keys(), key=int)
        data_dict['cbbi'] = float(conf[latest_ts]) * 100
    except:
        data_dict.update({'dxy':102,'yield':4.2,'oil':75,'fng_vals':[50]*10,'cbbi':54.0})
    data_dict.update({'m2': 4.5, 'etf': 1.2, 'fund': 0.01, 'ssr': 12.0})
    return data_dict

# --- 3. EXECUTION ---
raw = get_all_market_data()
history = []
if 'macro_df' in raw:
    for i in range(7):
        idx = -(i+1)
        score = calculate_index(raw['macro_df']["DX-Y.NYB"].iloc[idx], raw['macro_df']["^TNX"].iloc[idx], raw['macro_df']["CL=F"].iloc[idx],
                                raw['fng_vals'][i] if i < len(raw['fng_vals']) else 50, raw.get('cbbi', 50), 4.5, 1.2, 0.01, 12.0)
        history.append({"Date": raw['macro_df'].index[idx].date(), "Score": score})
df_history = pd.DataFrame(history).sort_values("Date")
current_score = df_history["Score"].iloc[-1] if not df_history.empty else 50.0

# --- 4. DASHBOARD UI ---
st.title("🛡️ Crypto Cycle Risk")
st.caption("Strategic Evaluation Engine")

# GAUGE CHART
fig_gauge = go.Figure(go.Indicator(
    mode = "gauge+number", value = current_score,
    gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#00ffcc"},
             'steps': [{'range': [0, 35], 'color': '#006400'},
                       {'range': [35, 70], 'color': '#8B8000'},
                       {'range': [70, 100], 'color': '#8B0000'}]}))
fig_gauge.update_layout(paper_bgcolor='#0e1117', font={'color': "white"}, height=320, margin=dict(t=30, b=0))
st.plotly_chart(fig_gauge, use_container_width=True)

# DYNAMIC ACTION LABEL
if current_score < 35:
    st.success("RECOMMENDED ACTION: 🟢 ACCUMULATE")
elif current_score < 70:
    st.warning("RECOMMENDED ACTION: 🟡 HOLD / CAUTION")
else:
    st.error("RECOMMENDED ACTION: 🔴 TAKE PROFITS / HEDGE")

# PERFORMANCE PILLARS
st.markdown("---")
col1, col2, col3, col4, col5 = st.columns(5)
disp_macro = (normalize(raw.get('dxy'),98,108,True) + normalize(raw.get('yield'),3,5,True) + normalize(raw.get('oil'),65,95,True))/3 * 0.5 + normalize(raw.get('m2'),-1,10)*0.5
disp_struct = normalize(raw.get('fund'),0,0.06,True)*0.5 + normalize(raw.get('ssr',12),8,22,True)*0.5

col1.metric("MACRO 40%", f"{int(round(disp_macro))}")
col2.metric("SENTIMENT 20%", f"{int(round(raw.get('fng_vals',[50])[0]))}")
col3.metric("TECHNICALS 20%", f"{int(round(raw.get('cbbi',50)))}")
col4.metric("ADOPTION 10%", f"{int(round(normalize(raw.get('etf'),-1,5)))}")
col5.metric("STRUCTURE 10%", f"{int(round(disp_struct))}")

# TREND CHART
st.markdown("### 📈 7-Day Risk Trend")
fig_line = go.Figure(go.Scatter(x=df_history["Date"], y=df_history["Score"], mode='lines+markers', line=dict(color='#00ffcc', width=3), fill='tozeroy', fillcolor='rgba(0, 255, 204, 0.1)'))
fig_line.update_layout(paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', font={'color': 'white'}, height=250, margin=dict(t=10, b=10), yaxis=dict(range=[0, 100]))
st
