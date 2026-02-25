import streamlit as st
import streamlit.components.v1 as components
import ccxt
import pandas as pd

# পেজ সেটআপ
st.set_page_config(page_title="Haridas Pro Terminal", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

# Custom CSS
st.markdown("""
<style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {
        padding-top: 1rem;
        padding-bottom: 0rem;
    }
</style>
""", unsafe_allow_html=True)

# এক্সচেঞ্জ সেটআপ (KuCoin ব্যবহার করা হলো কারণ এতে সব কয়েন থাকে এবং সার্ভার ব্লক করে না)
exchange = ccxt.kucoin()

coins_map = {
    "BTC/USDT": "BINANCE:BTCUSDT",
    "ETH/USDT": "BINANCE:ETHUSDT",
    "SOL/USDT": "BINANCE:SOLUSDT",
    "BNB/USDT": "BINANCE:BNBUSDT",
    "XRP/USDT": "BINANCE:XRPUSDT",
    "DOGE/USDT": "BINANCE:DOGEUSDT",
    "ADA/USDT": "BINANCE:ADAUSDT",
    "SHIB/USDT": "BINANCE:SHIBUSDT",
    "PEPE/USDT": "BINANCE:PEPEUSDT",
    "LINK/USDT": "BINANCE:LINKUSDT"
}

# সেফ ডেটা ফেচিং (কোনো এরর আসলে স্কিপ করবে, অ্যাপ ক্র্যাশ করবে না)
@st.cache_data(ttl=60)
def fetch_market_data():
    data = []
    for sym, tv_sym in coins_map.items():
        try:
            t = exchange.fetch_ticker(sym)
            last = t.get('last')
            if last is None:
                continue
                
            change_pct = t.get('percentage', 0.0)
            change_amt = t.get('change', 0.0)

            # যদি API পার্সেন্টেজ না দেয়, তবে নিজে ক্যালকুলেট করা
            if change_pct is None and t.get('open'):
                change_pct = ((last - t.get('open')) / t.get('open')) * 100
            if change_amt is None and t.get('open'):
                change_amt = last - t.get('open')

            data.append({
                'Symbol': sym,
                'TV_Symbol': tv_sym,
                'Price': float(last),
                'Change_Amt': float(change_amt) if change_amt else 0.0,
                'Change_Pct': float(change_pct) if change_pct else 0.0
            })
        except Exception:
            pass # এরর হলে কয়েনটি স্কিপ করবে
            
    return pd.DataFrame(data)

df = fetch_market_data()

# ================= সাইডবার =================
st.sidebar.markdown("### ⚡ **Haridas Terminal**")
st.sidebar.markdown("---")

if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
    fetch_market_data.clear()
    st.rerun()

if not df.empty:
    filter_option = st.sidebar.selectbox("🎯 Filter Market:", ["All Coins", "Top Gainers 🚀", "Top Losers 🔻"])

    if filter_option == "Top Gainers 🚀":
        df = df.sort_values(by="Change_Pct", ascending=False)
    elif filter_option == "Top Losers 🔻":
        df = df.sort_values(by="Change_Pct", ascending=True)

    display_options = []
    option_to_tv_map = {}

    st.sidebar.markdown("<br>", unsafe_allow_html=True)
    
    for _, row in df.iterrows():
        sym = row['Symbol']
        price = row['Price']
        pct = row['Change_Pct']
        
        status_icon = "🟢" if pct > 0 else "🔴"
        display_text = f"{status_icon} {sym} | {pct:.2f}%"
        
        display_options.append(display_text)
        option_to_tv_map[display_text] = row['TV_Symbol']

    selected_display = st.sidebar.radio("Watchlist:", display_options)
    
    tv_symbol = option_to_tv_map[selected_display]
    coin_name = selected_display.split(" ")[1]
else:
    tv_symbol = "BINANCE:BTCUSDT"
    coin_name = "BTC/USDT"
    st.sidebar.error("ডেটা লোড হতে সমস্যা হচ্ছে! ইন্টারনেট বা এক্সচেঞ্জ এপিআই চেক করুন।")

# ================= মেইন ড্যাশবোর্ড =================
if not df.empty:
    top_cols = st.columns(3)
    quick_coins = ["BTC/USDT", "ETH/USDT", "SOL/USDT"]
    
    for i, col in enumerate(top_cols):
        if i < len(quick_coins):
            coin_data = df[df['Symbol'] == quick_coins[i]]
            if not coin_data.empty:
                c_price = coin_data.iloc[0]['Price']
                c_pct = coin_data.iloc[0]['Change_Pct']
                with col:
                    st.metric(label=quick_coins[i], value=f"${c_price:,.4f}", delta=f"{c_pct:.2f}%")

st.markdown("---")
st.markdown(f"#### 📈 Live Chart: **{coin_name}**")

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
