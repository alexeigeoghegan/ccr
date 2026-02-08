import streamlit as st
import yfinance as yf
import requests

# Page Configuration
st.set_page_config(page_title="METAL Dashboard", page_icon="⚒️", layout="wide")

# --- IMPROVED DATA FETCHING ---

@st.cache_data(ttl=300)
def get_live_price(ticker_list):
    """Try a list of tickers and return the first valid price found."""
    for symbol in ticker_list:
        try:
            ticker = yf.Ticker(symbol)
            df = ticker.history(period="1d")
            if not df.empty:
                return round(df['Close'].iloc[-1], 2)
        except:
            continue
    return "N/A"

def fetch_all_data():
    # DXY fallbacks: DX-Y.NYB, DXY, UUP (ETF proxy)
    dxy = get_live_price(["DX-Y.NYB", "DXY", "UUP"])
    
    # 10Y Yield: ^TNX is usually very stable
    ten_y = get_live_price(["^TNX"])
    
    # Oil fallbacks: CL=F (Front month), CLH26 (March 26), USO (ETF proxy)
    oil = get_live_price(["CL=F", "CLH26", "USO"])
    
    return {"DXY": dxy, "10Y": ten_y, "Oil": oil}

def get_fear_greed():
    try:
        r = requests.get("https://api.alternative.me/fng/").json()
        return r['data'][0]['value'], r['data'][0]['value_classification']
    except:
        return "N/A", "N/A"

# Load Data
macro = fetch_all_data()
fng_val, fng_label = get_fear_greed()

# --- TOP BANNER ---
st.markdown("### 🌍 Global Market Pulse")
b1, b2, b3 = st.columns(3)

with b1:
    st.metric("Dollar Index (DXY)", f"{macro['DXY']}")
with b2:
    st.metric("US 10Y Yield", f"{macro['10Y']}%" if macro['10Y'] != "N/A" else "N/A")
with b3:
    st.metric("WTI Crude Oil", f"${macro['Oil']}" if macro['Oil'] != "N/A" else "N/A")

st.markdown("---")

# --- METAL CORE ---
st.title("⚒️ METAL Cycle Risk Tracker")
m, e, t, a, l = st.columns(5)

with m:
    st.header("M")
    st.subheader("Macro")
    st.write(f"DXY: **{macro['DXY']}**")
    st.caption("High DXY = Pressure on Crypto")

with e:
    st.header("E")
    st.subheader("Emotion")
    st.write(f"Score: **{fng_val}**")
    st.caption(fng_label)

with t:
    st.header("T")
    st.subheader("Technicals")
    st.link_button("CBBI Index", "https://colintalkscrypto.com/cbbi/")

with a:
    st.header("A")
    st.subheader("Adoption")
    st.link_button("Power Law", "https://charts.bitbo.io/power-law-oscillator/")

with l:
    st.header("L")
    st.subheader("Leverage")
    st.link_button("CDRI Index", "https://www.coinglass.com/pro/i/CDRI")

# Sidebar for alerts
st.sidebar.title("METAL Alerts")
st.sidebar.info("Reference: Sell | Fifty Sell | 2 Anytime Alerts")
