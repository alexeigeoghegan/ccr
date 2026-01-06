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
    [data-testid="stMetricValue"] { font-size: 40px !important; font-weight: 700 !important; }
    .stAlert { border: none; padding: 20px; border-radius: 15px; font-size: 28px; font-weight: 800; text-align: center; }
    .logic-box { background-color: #161b22; padding: 20px; border-radius: 10px; border-left: 5px solid #00ffcc; margin-bottom: 15px; font-size: 14px; color: #e0e0e0; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. CORE LOGIC ---
def norm_risk(val, mi, ma, inv=False):
    """Calculates risk: High score = High Danger. inv=True means High input = Low Risk."""
    try:
        val = float(val)
        val = max(min(val, ma), mi)
        score = ((val - mi) / (ma - mi)) * 100
        return (100 - score) if inv else score
    except: return 50.0

def calculate_total_risk(dxy, yld, oil, fgi, cbbi, m2_mom, etf, fund, ssr):
    # MACRO 40% (Fin Cond 20% + M2 20%)
    # DXY/Yield/Oil UP = High Risk
    score_fin = (norm_risk(dxy, 98, 108) + norm_risk(yld, 3, 5) + norm_risk(oil, 65, 95)) / 3
    # M2/ETF UP = Low Risk (inv=True)
    p_macro = (score_fin * 0.20) + (norm_risk(m2_mom, 0, 1.0, inv=True) * 0.20) 
    
    p_sent = (fgi * 0.20)
    p_tech = (cbbi * 0.20)
    p_adopt = (norm_risk(etf, -1, 5, inv=True) * 0.10)
    
    # STRUCTURE 10% (Fund UP = High Risk, SSR UP = High Risk)
    p_struct = (norm_risk(fund, 0, 0.06) * 0.05) + (norm_risk(ssr, 8, 22) * 0.05)
    
    return int(round(p_macro + p_sent + p_tech + p_adopt + p_struct))

@st.cache_data(ttl=3600)
def get_data():
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        macro = yf.download(["BTC-USD", "DX-Y.NYB", "^TNX", "CL=F", "GC=F"], period="2mo", progress=False)['Close'].ffill().dropna()
        # CBBI fetch
        cbbi_res = requests.get("https://colintalkscrypto.com/cbbi/data/latest.json", headers=headers, verify=False).json()
        conf = cbbi_res.get("Confidence", cbbi_res)
        latest_ts = max(conf.keys(), key=int)
        cbbi_val = 55.0 # Explicitly set as requested
        
        # 30-Day History Loop
        history = []
        for i in range(30):
            idx = -(i+1)
            history.append({
                "Date": macro.index[idx].date(),
                "Score": calculate_total_risk(macro["DX-Y.NYB"].iloc[idx], macro["^TNX"].iloc[idx], macro["CL=F"].iloc[idx],
                                              44, 55, 0.35, 1.2, 0.01, 12.0)
            })
        
        return pd.DataFrame(history).sort_values("Date"), {
            'btc': macro["BTC-USD"].iloc[-1], 'dxy': macro["DX-Y.NYB"].iloc[-1], 
            'yield': macro["^TNX"].iloc[-1], 'oil': macro["CL=F"].iloc[-1], 
            'gold': macro["GC=F"].iloc[-1], 'fgi': 44, 'cbbi': 55, 'm2_mom': 0.35, 
            'cap': '3.2T', 'dom': '58.4%', 'etf': 1.2, 'fund': 0.01, 'ssr': 12.0
        }
    except:
        return pd.DataFrame(), {}

df_hist, d = get_data()
current_score = df_hist["Score"].iloc[-1] if not df_hist.empty else 50

# --- 3. UI DASHBOARD ---
st.title("Crypto Cycle Risk")

col_g, col_a = st.columns([2, 1])
with col_g:
    fig = go.Figure(go.Indicator(mode="gauge+number", value=current_score,
        gauge={'axis': {'range': [0, 100]}, 'bar': {'color': "#00ffcc"},
               'steps': [{'range': [0, 35], 'color': '#006400'},
                         {'range': [35, 70], 'color': '#8B8000'},
                         {'range': [70, 100], 'color': '#8B0000'}]}))
    fig.update_layout(paper_bgcolor='#0e1117', font={'color': "white"}, height=320, margin=dict(t=0, b=0))
    st.plotly_chart(fig, use_container_width=True)

with col_a:
    st.write("##")
    if current_score < 35: st.success("ACCUMULATE")
    elif current_score < 70: st.warning("HOLD / CAUTION")
    else: st.error("TAKE PROFITS / HEDGE")

# --- 4. COLOR-CODED PILLARS ---
st.markdown("---")
c1, c2, c3, c4, c5 = st.columns(5)

# Calculate Individual Component Risks for display
s_mac = int(round((norm_risk(d['dxy'],98,108)*0.33 + norm_risk(d['yield'],3,5)*0.33 + norm_risk(d['oil'],65,95)*0.34)*0.5 + norm_risk(d['m2_mom'],0,1.0,True)*0.5))
s_sen, s_tec = d['fgi'], int(d['cbbi'])
s_ado = int(round(norm_risk(d['etf'],-1,5,True)))
s_str = int(round(norm_risk(d['fund'],0,0.06)*0.5 + norm_risk(d['ssr'],8,22)*0.5))

def draw_pill(label, val):
    clr = "#00ffcc" if val < 35 else "#ffff00" if val < 70 else "#ff4b4b"
    st.markdown(f"**{label}** <br> <span style='color:{clr}; font-size:42px; font-weight:bold;'>{val}</span>", unsafe_allow_html=True)

with c1: draw_pill("MACRO 40%", s_mac)
with c2: draw_pill("SENTIMENT 20%", s_sen)
with c3: draw_pill("TECHNICALS 20%", s_tec)
with c4: draw_pill("ADOPTION 10%", s_ado)
with c5: draw_pill("STRUCTURE 10%", s_str)

# --- 5. 30-DAY TREND ---
st.markdown("### 📈 30-Day Risk Trend")
fig_line = go.Figure(go.Scatter(x=df_hist["Date"], y=df_hist["Score"], mode='lines', line=dict(color='#00ffcc', width=4), fill='tozeroy', fillcolor='rgba(0, 255, 204, 0.1)'))
fig_line.update_layout(paper_bgcolor='#0e1117', plot_bgcolor='#0e1117', font={'color': 'white'}, height=280, margin=dict(t=10, b=10), yaxis=dict(range=[0, 100], gridcolor='#333'))
st.plotly_chart(fig_line, use_container_width=True)

# --- 6. LOGIC BREAKDOWN ---
st.markdown("---")
st.subheader("Pillar Derivation Logic")
l1, l2 = st.columns(2)
with l1:
    st.markdown(f"""<div class="logic-box"><b>Macro (40%):</b> 50% Financial Conditions (DXY, Yields, Oil) + 50% M2 Liquidity. Risk increases when USD strengthens or liquidity contracts. <br><i>Calculated: ({s_mac} risk)</i></div>""", unsafe_allow_html=True)
    st.markdown(f"""<div class="logic-box"><b>Sentiment (20%):</b> Direct Fear & Greed Index score. Measures irrational exuberance. <br><i>Current: {s_sen} (Fearful/Neutral)</i></div>""", unsafe_allow_html=True)
    st.markdown(f"""<div class="logic-box"><b>Technicals (20%):</b> CBBI score. Aggregates 11 cycle indicators. <br><i>Current: {s_tec} (Mid-Cycle)</i></div>""", unsafe_allow_html=True)
with l2:
    st.markdown(f"""<div class="logic-box"><b>Adoption (10%):</b> BTC Spot ETF Inflow momentum. High institutional buying (5% MoM cap) reduces risk scores. <br><i>Calculated: ({s_ado} risk)</i></div>""", unsafe_allow_html=True)
    st.markdown(f"""<div class="logic-box"><b>Structure (10%):</b> 50% Funding Rates + 50% SSR. Risk spikes when leverage (Funding) is high or stablecoin buying power (SSR) is exhausted. <br><i>Calculated: ({s_str} risk)</i></div>""", unsafe_allow_html=True)

# --- 7. SIDEBAR ---
st.sidebar.write(f"Bitcoin: `${d.get('btc',0):,.0f}`")
st.sidebar.write(f"DXY Index: `{d.get('dxy',0):.2f}`")
st.sidebar.write(f"10Y Yield: `{d.get('yield',0):.2f}%`")
st.sidebar.write(f"Gold: `${d.get('gold',0):,.0f}`")
st.sidebar.write(f"Oil: `${d.get('oil',0):.1f}`")
st.sidebar.write(f"M2 MoM: `{d.get('m2_mom')}%`")
st.sidebar.write(f"Total Cap: `{d.get('cap')}`")
st.sidebar.write(f"BTC Dom: `{d.get('dom')}`")
st.sidebar.write(f"Fear & Greed: `{d.get('fgi')}`")
st.sidebar.write(f"CBBI Index: `{d.get('cbbi')}`")
st.sidebar.write(f"ETF Inflow: `{d.get('etf')}%`")
st.sidebar.write(f"Funding: `{d.get('fund')}%`")
st.sidebar.write(f"SSR Ratio: `{d.get('ssr')}`")
