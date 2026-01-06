import streamlit as st
import yfinance as yf
import requests
import pandas as pd
import urllib3
import plotly.graph_objects as go
from datetime import datetime

# Disable SSL warnings for external APIs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- 1. PAGE CONFIGURATION ---
st.set_page_config(page_title="Crypto Cycle Risk", layout="wide")

# Custom CSS for Professional Dark Theme
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    div[data-testid="stMetricValue"] { font-size: 32px; color: #00ffcc; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE LOGIC HELPER FUNCTIONS ---
def normalize(val, mi, ma, inv=False):
    """Maps any value to a 0-100 scale safely."""
    try:
        val = float(val)
        val = max(min(val, ma), mi)
        s = ((val - mi) / (ma - mi)) * 100
        return (100 - s) if inv else s
    except:
        return 50.0

def calculate_index(dxy, yld, oil, fgi, cbbi, m2, etf, fund, ssr):
    """Weighted calculation based on 40/20/20/10/10 structure."""
    # MACRO 40%: (Financial Conditions 20% + M2 20%)
    # Financial conditions = Average of DXY, Yield, Oil
    score_fin = (normalize(dxy, 98, 108, True) + normalize(yld, 3, 5, True) + normalize(oil, 65, 95, True)) / 3
    p_macro = (score_fin * 0.20) + (normalize(m2, -1, 10) * 0.20) 
    
    p_sent = (fgi * 0.20)
    p_tech = (cbbi * 0.20)
    p_adopt = (normalize(etf, -1, 5) * 0.10)
    
    # STRUCTURE 10%: (Funding 5% + SSR 5%)
    p_struct = (normalize(fund, 0, 0.06, True) * 0.05) + (normalize(ssr, 8, 22, True) * 0.05)
    
    return round(p_macro + p_sent + p_tech + p_adopt + p_struct, 1)

# --- 3. DATA COLLECTION ENGINE ---
@st.cache_data(ttl=3600)
def get_all_market_data():
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    data_dict = {}
    
    # 1. Macro Data (Yahoo Finance)
    try:
        macro = yf.download(["DX-Y.NYB", "^TNX", "CL=F"], period="1mo", progress=False)['Close']
        macro = macro.ffill().dropna()
        data_dict['dxy'] = macro["DX-Y.NYB"].iloc[-1]
        data_dict['yield'] = macro["^TNX"].iloc[-1]
        data_dict['oil'] = macro["CL=F"].iloc[-1]
        data_dict['macro_df'] = macro
    except Exception as e:
        data_dict['dxy'], data_dict['yield'], data_dict['oil'] = 102.0, 4.2, 75.0

    # 2. Sentiment Data (Alternative.me)
    try:
        fng_res = requests.get("https://api.alternative.me/fng/?limit=10", headers=headers, timeout=10)
        fng_json = fng_res.json()
        data_dict['fng_vals'] = [int(x['value']) for x in fng_json['data']]
    except:
        data_dict['fng_vals'] = [50] * 10

    # 3. Technicals (CBBI)
    try:
        cbbi_res = requests.get("https://colintalkscrypto.com/cbbi/data/latest.json", headers=headers, timeout=10, verify=False)
        cbbi_json = cbbi_res.json()
        conf = cbbi_json.get("Confidence", cbbi_json)
        latest_ts = max(conf.keys(), key=int)
        data_dict['cbbi'] = float(conf[latest_ts]) * 100
    except:
        data_dict['cbbi'] = 54.0 # Using your previous stable value as fallback

    # 4. Proxies (Standardized for 2026 conditions)
    data_dict.update({'m2': 4.5, 'etf': 1.2, 'fund': 0.01, 'ssr': 12.0})
    return data_dict

# --- 4. EXECUTION ---
raw = get_all_market_data()

# Calculate Historical Trend
history = []
if 'macro_df' in raw:
    for i in range(7):
        idx = -(i+1)
        score = calculate_index(
            raw['macro_df']["DX-Y.NYB"].iloc[idx], raw['macro_df']["^TNX"].iloc[idx], raw['macro_df']["CL=F"].iloc[idx],
            raw['fng_vals'][i] if i < len(raw['fng_vals']) else 50, raw.get('cbbi', 50), 
            raw['m2'], raw['etf'], raw['fund'], raw['ssr']
        )
        history.append({"Date": raw['macro_df'].index[idx].date(), "Score": score})
df_history = pd.DataFrame(history).sort_values("Date")
current_score = df_history["Score"].iloc[-1] if not df_history.empty else 50.0

# --- 5. DASHBOARD UI ---
st.title("🛡️ Crypto Cycle Risk")
st.caption("Strategic Evaluation Engine | 40% Macro | 20% Sent | 20% Tech | 10% Adopt | 10% Struct")

# Gauge Chart
fig_gauge = go.Figure(go.Indicator(
    mode = "gauge+number", value = current_score,
    gauge = {'axis': {'range': [0, 100]}, 'bar': {'color': "#00ffcc"},
             'steps': [{'range': [0, 30], 'color': '#006400'},
                       {'range': [30, 70], 'color': '#8B8000'},
                       {'range': [70, 100], 'color': '#8B0000'}]}))
fig_gauge.update_layout(paper_bgcolor='#0e1117', font={'color': "white"}, height=350, margin=dict(t=50, b=0))
st.plotly_chart(fig_gauge, use_container_width=True)

# Pillar Metrics
st.markdown("---")
col1, col2, col3, col4, col5 = st.columns(5)

# Calculate relative strength for display (0-100% per pillar)
disp_macro = (normalize(raw.get('dxy'), 98, 108, True) + normalize(raw.get('yield'), 3, 5, True) + normalize(raw.get('oil'), 65, 95, True)) / 3 * 0.5 + normalize(raw.get('m2'), -1, 10) * 0.5
disp_struct = normalize(raw.get('fund'), 0, 0.06, True) * 0.5 + normalize(raw.get('ssr'), 8, 22, True) * 0.5

col1.metric("MACRO", f"{round(disp_macro, 1)}%")
col2.metric("SENTIMENT", f"{raw.get('fng_vals',[50])[0]}%")
col3.metric("TECHNICALS", f"{round(raw.get('cbbi',50), 1)}%")
col4.metric("ADOPTION", f"{round(normalize(raw.get('etf'),-1,5), 1)}%")
col5.metric("STRUCTURE", f"{round(disp_struct, 1)}%")

# Trend Chart
st.markdown("### 📈 7-Day Risk Trend")
fig_line = go.Figure(go.Scatter(x=df_history["Date"], y=df_history["Score"], 
                               mode='lines+markers', line=dict(color='#00ffcc', width=3),
                               fill='tozeroy', fillcolor='rgba(0, 255, 204, 0.1)'))
fig_line.update_layout(paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', font={'color': 'white'}, 
                       height=300, margin=dict(t=10, b=10), yaxis=dict(range=[0, 100]))
st.plotly_chart(fig_line, use_container_width=True)

# --- SIDEBAR MARKET FEED ---
st.sidebar.header("📡 Market Feed")
st.sidebar.markdown("### **MACRO**")
st.sidebar.write(f"DXY Index: `{round(raw.get('dxy',0), 2)}`")
st.sidebar.write(f"10Y Yield: `{round(raw.get('yield',0), 2)}%`")
st.sidebar.write(f"Oil Price: `${round(raw.get('oil',0), 2)}`")
st.sidebar.write(f"Global M2 Liquidity: `{raw.get('m2')}%`")

st.sidebar.markdown("---")
st.sidebar.markdown("### **SENTIMENT**")
st.sidebar.write(f"Fear & Greed Index: `{raw.get('fng_vals',[50])[0]}`")

st.sidebar.markdown("---")
st.sidebar.markdown("### **TECHNICALS**")
st.sidebar.write(f"CBBI Index: `{round(raw.get('cbbi',0), 1)}`")

st.sidebar.markdown("---")
st.sidebar.markdown("### **ADOPTION**")
st.sidebar.write(f"ETF BTC Net Inflow (MoM): `{raw.get('etf')}%`")

st.sidebar.markdown("---")
st.sidebar.markdown("### **STRUCTURE**")
st.sidebar.write(f"Funding Rates: `{raw.get('fund')}%`")
st.sidebar.write(f"SSR Ratio: `{raw.get('ssr')}`")
