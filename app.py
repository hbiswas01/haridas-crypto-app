import streamlit as st
import streamlit.components.v1 as components
import ccxt
import pandas as pd

# পেজ সেটআপ
st.set_page_config(page_title="Haridas Pro Terminal", layout="wide", initial_sidebar_state="expanded")

# এক্সচেঞ্জ ইনিশিয়ালাইজ করা (Kraken ব্যবহার করা হয়েছে সার্ভার ব্লক এড়াতে)
@st.cache_resource
def get_exchange():
    return ccxt.kraken()

exchange = get_exchange()

# কোন কোন কয়েন আমরা লিস্টে দেখাবো তার ম্যাপ (CCXT সিম্বল থেকে TradingView সিম্বল)
coins_map = {
    "BTC/USDT": "BINANCE:BTCUSDT",
    "ETH/USDT": "BINANCE:ETHUSDT",
    "SOL/USDT": "BINANCE:SOLUSDT",
    "XRP/USDT": "BINANCE:XRPUSDT",
    "DOGE/USDT": "BINANCE:DOGEUSDT",
    "ADA/USDT": "BINANCE:ADAUSDT",
    "DOT/USDT": "BINANCE:DOTUSDT",
    "LTC/USDT": "BINANCE:LTCUSDT",
    "BCH/USDT": "BINANCE:BCHUSDT",
    "LINK/USDT": "BINANCE:LINKUSDT"
}

# ডেটা আনার ফাংশন (প্রতিবার ক্লিক করলে যেন অ্যাপ স্লো না হয়, তাই ৬০ সেকেন্ড ডেটা সেভ থাকবে)
@st.cache_data(ttl=60)
def fetch_market_data():
    symbols = list(coins_map.keys())
    try:
        tickers = exchange.fetch_tickers(symbols)
        data = []
        for sym in symbols:
            if sym in tickers:
                t = tickers[sym]
                last = t.get('last', 0.0)
                change_pct = t.get('percentage', 0.0)
                change_amt = t.get('change', 0.0)

                # যদি কোনো ডেটা মিসিং থাকে, তবে ক্যালকুলেট করে নেওয়া
                if change_pct is None and last and t.get('open'):
                    change_pct = ((last - t['open']) / t['open']) * 100
                if change_amt is None and last and t.get('open'):
                    change_amt = last - t['open']

                data.append({
                    'Symbol': sym,
                    'TV_Symbol': coins_map[sym],
                    'Price': float(last) if last else 0.0,
                    'Change_Amt': float(change_amt) if change_amt else 0.0,
                    'Change_Pct': float(change_pct) if change_pct else 0.0
                })
        return pd.DataFrame(data)
    except Exception as e:
        return pd.DataFrame()

df = fetch_market_data()

# সাইডবার এবং ফিল্টার তৈরি
st.sidebar.title("🪙 Market Watch")

if st.sidebar.button("🔄 Refresh Market Data"):
    fetch_market_data.clear() # ক্যাশ ক্লিয়ার করে নতুন ডেটা আনবে
    st.rerun()

if not df.empty:
    # Top Gainer ও Top Loser ফিল্টার
    filter_option = st.sidebar.selectbox("🎯 Filter By:", ["All Coins", "Top Gainers 🚀", "Top Losers 🔻"])

    if filter_option == "Top Gainers 🚀":
        df = df.sort_values(by="Change_Pct", ascending=False)
    elif filter_option == "Top Losers 🔻":
        df = df.sort_values(by="Change_Pct", ascending=True)

    # লিস্ট তৈরি করা (দাম এবং P&L সহ)
    display_options = []
    option_to_tv_map = {}

    st.sidebar.write("---")
    
    for _, row in df.iterrows():
        sym = row['Symbol']
        price = row['Price']
        pct = row['Change_Pct']
        amt = row['Change_Amt']

        # লাভ হলে +, লস হলে - চিহ্ন
        sign_pct = "+" if pct > 0 else ""
        sign_amt = "+" if amt > 0 else ""

        # স্টাইলিশ টেক্সট তৈরি
        display_text = f"{sym} | ${price:,.2f} | {sign_pct}{pct:.2f}% ({sign_amt}${amt:,.2f})"
        display_options.append(display_text)
        option_to_tv_map[display_text] = row['TV_Symbol']

    # রেডিও বাটন যেখানে কয়েন সিলেক্ট করা যাবে
    selected_display = st.sidebar.radio("Select a Coin:", display_options)
    
    # সিলেক্ট করা কয়েনের আসল নাম এবং TradingView সিম্বল আলাদা করা
    tv_symbol = option_to_tv_map[selected_display]
    coin_name = selected_display.split(" | ")[0]
else:
    tv_symbol = "BINANCE:BTCUSDT"
    coin_name = "BTC/USDT"
    st.sidebar.error("ডেটা লোড হতে সমস্যা হচ্ছে!")

# মেইন স্ক্রিন (ডানদিকের লাইভ চার্ট)
st.title("⚡ Haridas Pro Crypto Terminal")
st.subheader(f"Live 1-Min Chart: {coin_name}")

# TradingView-এর ডাইনামিক উইজেট
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

components.html(tv_widget, height=650)
