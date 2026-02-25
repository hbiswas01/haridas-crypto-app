import streamlit as st
import streamlit.components.v1 as components

# পেজ সেটআপ
st.set_page_config(page_title="Haridas Pro Terminal", layout="wide", initial_sidebar_state="expanded")

# সাইডবারে কয়েনের লিস্ট তৈরি
st.sidebar.title("🪙 Crypto List")
st.sidebar.write("যেকোনো কয়েনে ক্লিক করুন:")

# তোমার ফেভারিট ও জনপ্রিয় কয়েনের ডিকশনারি
coins = {
    "Bitcoin (BTC)": "BINANCE:BTCUSDT",
    "Ethereum (ETH)": "BINANCE:ETHUSDT",
    "Solana (SOL)": "BINANCE:SOLUSDT",
    "Binance Coin (BNB)": "BINANCE:BNBUSDT",
    "Ripple (XRP)": "BINANCE:XRPUSDT",
    "Dogecoin (DOGE)": "BINANCE:DOGEUSDT",
    "Shiba Inu (SHIB)": "BINANCE:SHIBUSDT",
    "Pepe (PEPE)": "BINANCE:PEPEUSDT",
    "Cardano (ADA)": "BINANCE:ADAUSDT"
}

# রেডিও বাটন দিয়ে লিস্ট তৈরি (যাতে ক্লিক করা যায়)
selected_coin = st.sidebar.radio("", list(coins.keys()))

# যে কয়েন সিলেক্ট হবে, তার TradingView সিম্বল নেওয়া
tv_symbol = coins[selected_coin]

# মেইন স্ক্রিনে চার্টের হেডিং
st.title("⚡ Haridas Pro Crypto Terminal")
st.subheader(f"Live 1-Min Chart: {selected_coin}")

# TradingView-এর ডাইনামিক উইজেট (f-string ব্যবহার করে সিম্বল পাল্টানো হচ্ছে)
# কোডে {{ এবং }} ব্যবহার করা হয়েছে যাতে HTML ঠিকমতো কাজ করে
tv_widget = f"""
<div class="tradingview-widget-container" style="height:650px;width:100%">
  <div id="tradingview_dynamic" style="height:100%;width:100%"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget({{
    "autosize": true,
    "symbol": "{tv_symbol}",
    "interval": "1",
    "timezone": "Asia/Kolkata",
    "theme": "dark",
    "style": "1",
    "locale": "en",
    "enable_publishing": false,
    "backgroundColor": "#0E1117",
    "gridColor": "#1f293d",
    "hide_top_toolbar": false,
    "hide_legend": false,
    "save_image": false,
    "container_id": "tradingview_dynamic"
  }});
  </script>
</div>
"""

# চার্ট রেন্ডার করা
components.html(tv_widget, height=650)
