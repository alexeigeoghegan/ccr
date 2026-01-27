import requests
import pandas as pd

def get_crypto_sentiment():
    """Fetches the Fear & Greed Index (0-100)."""
    url = "https://api.alternative.me/fng/"
    response = requests.get(url).json()
    return int(response['data'][0]['value'])

def get_btc_data():
    """Fetches BTC price and 24h change from CoinGecko."""
    url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd&include_24hr_change=true"
    data = requests.get(url).json()
    return data['bitcoin']['usd'], data['bitcoin']['usd_24h_change']

def calculate_risk_index():
    fng_score = get_crypto_sentiment()
    btc_price, btc_change = get_btc_data()
    
    # Simple Logic: 
    # High Fear & Greed = High Risk (To the downside)
    # Low Fear & Greed = Low Risk (Opportunity to buy)
    
    risk_score = fng_score # This is our baseline
    
    print(f"--- Bitcoin Risk Report ---")
    print(f"Current Price: ${btc_price:,.2f}")
    print(f"Sentiment Score: {fng_score}/100")
    
    if risk_score > 75:
        return "🔴 HIGH RISK: Consider rotating to Cash."
    elif risk_score < 30:
        return "🟢 LOW RISK: Consider increasing BTC exposure."
    else:
        return "🟡 NEUTRAL: Maintain current positions."

print(calculate_risk_index())
