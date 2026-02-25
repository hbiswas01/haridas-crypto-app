import streamlit as st
import streamlit.components.v1 as components
import ccxt
import pandas as pd

# পেজ সেটআপ (এখানে initial_sidebar_state="collapsed" দেওয়া যায় যদি শুরুতে সাইডবার হাইড রাখতে চাও)
st.set_page_config(page_title="Haridas Pro Terminal", page_icon="⚡", layout="wide", initial_sidebar_state="expanded")

# Custom CSS - সুন্দর গ্লোয়িং বাটন অ্যাড করা হলো
st.markdown("""
<style>
    /* Streamlit-এর রাইট সাইড মেনু এবং ফুটার হাইড করা */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* হেডার পুরোপুরি হাইড না করে ট্রান্সপারেন্ট করা, যাতে বাটন কাজ করে */
    header {background-color: transparent !important;}
    
    /* ডানদিকের ডিফল্ট টুলস হাইড করা */
    .stApp > header > div:not(:first-child) {display: none;}
    
    /* 🎯 সাইডবার খোলার সুন্দর গ্লোয়িং ফ্লোটিং বাটন (Open Button) */
    [data-testid="collapsedControl"] {
        background-color: #0E1117 !important;
        border: 2px solid #00ff88 !important;
        border-radius: 50% !important;
        color: #00ff88 !important;
        box-shadow: 0 0 10px rgba(0, 255, 136, 0.4);
        top: 15px !important;
        left: 15px !important;
        transition: 0.3s ease-in-out;
        z-index: 99999;
    }
    [data-testid="collapsedControl"]:hover {
        box-shadow: 0 0 20px rgba(0, 255, 136, 0.8);
        transform: scale(1.1);
    }

    /* সাইডবার বন্ধ করার ভেতরের বাটন (Close Button) */
    [data-testid="stSidebarCollapseButton"] {
        color: #ff4b4b !important;
        transition: 0.3s;
    }
    [data-testid="stSidebarCollapseButton"]:hover {
        transform: scale(1.1);
        color: #ff0000 !important;
    }

    /* ওপরের স্পেস কমানো */
    .block-container {
        padding-top: 3rem;
        padding-bottom: 0rem;
    }
    
    /* Momentum Dashboard Custom CSS */
    .mdf-table {
        background-color: rgba(12, 14, 28, 0.95);
        border: 2px solid rgb(30, 80, 140);
        color: white;
        font-family: monospace;
        width: 100%;
        border-collapse: collapse;
        font-size: 13px;
        margin-top: 10px;
    }
    .mdf-table th, .mdf-table td {
        border: 1px solid rgb(25, 65, 120);
        padding: 6px 8px;
        text-align: center;
    }
    .mdf-header {
        background-color: rgba(8, 10, 22, 0.9);
        color: rgb(65, 195, 115);
        font-weight: bold;
        font-size: 14px;
    }
    .mdf-label { color: rgb(120, 122, 142); text-align: left !important; font-size: 11px;}
    .mdf-value { color: rgb(65, 195, 115); }
    .mdf-right { text-align: right !important; }
    .mdf-white { color: rgb(222, 224, 238); }
    .mdf-cyan { color: rgb(60, 200, 255); }
    .mdf-orange { color: rgb(255, 130, 40); }
</style>
""", unsafe_allow_html=True)

# এক্সচেঞ্জ সেটআপ (KuCoin)
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
            pass
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
    st.sidebar.error("ডেটা লোড হতে সমস্যা হচ্ছে!")

# ================= মেইন ড্যাশবোর্ড =================

col_chart, col_dash = st.columns([3, 1])

with col_chart:
    st.markdown(f"#### 📈 Live Fast Chart: **{coin_name}**")
    tv_widget = f"""
    <div class="tradingview-widget-container" style="height:600px;width:100%">
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
    components.html(tv_widget, height=600)

with col_dash:
    st.markdown("#### ⚙️ Momentum Status")
    
    # Custom HTML Table for Momentum Dashboard
    mdf_dashboard = """
    <table class="mdf-table">
        <tr><td colspan="3" class="mdf-header">MOMENTUM DECAY FIELD[BullByte]</td></tr>
        <tr><td class="mdf-label">ENERGY</td><td class="mdf-value">██████████████░░</td><td class="mdf-right mdf-value">98%</td></tr>
        <tr><td class="mdf-label">PHASE</td><td class="mdf-value">CHARGED</td><td class="mdf-right mdf-value">BULL</td></tr>
        <tr><td class="mdf-label">E0 INITIAL</td><td class="mdf-white">2.93</td><td class="mdf-right mdf-cyan">Strong</td></tr>
        <tr><td class="mdf-label">HALF-LIFE</td><td class="mdf-white">9.1 bars</td><td class="mdf-right mdf-label">ELP 0</td></tr>
        <tr><td class="mdf-label">ETA TO EXH</td><td class="mdf-orange">33 bars</td><td class="mdf-right mdf-orange">▮▮▮▮▮▮▮▯</td></tr>
        <tr><td class="mdf-label">DECAY CURVE</td><td class="mdf-value" style="font-size:10px;">▇▆▅▄▃▂▁·····</td><td class="mdf-right mdf-label">NOW >></td></tr>
        <tr><td class="mdf-label" style="text-align:center !important;">IMPULSES</td><td class="mdf-label" style="text-align:center !important;">EXHAUSTIONS</td><td class="mdf-label" style="text-align:center !important;">DIVERGENCES</td></tr>
        <tr><td class="mdf-white">591</td><td style="color:rgb(255, 195, 0);">35</td><td style="color:rgb(255, 120, 0);">119</td></tr>
    </table>
    """
    st.markdown(mdf_dashboard, unsafe_allow_html=True)
    st.info("💡 নোট: এটি একটি UI ডিজাইন।")
