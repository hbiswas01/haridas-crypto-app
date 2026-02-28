import streamlit as st
import streamlit.components.v1 as components
import datetime
import pytz
import pandas as pd
import time
import requests
import hmac
import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
import os
import yfinance as yf
import numpy as np

# --- 1. Page Configuration & Session State ---
st.set_page_config(layout="wide", page_title="Haridas Crypto Terminal", initial_sidebar_state="expanded")

ACTIVE_TRADES_FILE = "crypto_active_trades.csv"
HISTORY_TRADES_FILE = "crypto_trade_history.csv"

def load_data(file_name):
    if os.path.exists(file_name):
        try: return pd.read_csv(file_name).to_dict('records')
        except: return []
    return []

def save_data(data, file_name):
    pd.DataFrame(data).to_csv(file_name, index=False)

if 'active_trades' not in st.session_state: st.session_state.active_trades = load_data(ACTIVE_TRADES_FILE)
if 'trade_history' not in st.session_state: st.session_state.trade_history = load_data(HISTORY_TRADES_FILE)
if 'auto_ref' not in st.session_state: st.session_state.auto_ref = False
if 'custom_watch_cr' not in st.session_state: st.session_state.custom_watch_cr = []

CRYPTO_SECTORS = {
    "COINDCX WATCHLIST": ["BTC-USD", "ETH-USD", "BNB-USD", "SOL-USD", "XRP-USD", "DOGE-USD", "ADA-USD", "AVAX-USD", "LINK-USD", "DOT-USD", "TRX-USD", "MATIC-USD", "ESP-USD", "SENT-USD", "PIPPIN-USD", "HMSTR-USD"]
}

ALL_CRYPTO = list(set([coin for clist in CRYPTO_SECTORS.values() for coin in clist] + st.session_state.custom_watch_cr))

def fmt_price(val):
    try:
        val = float(val)
        if pd.isna(val) or val == 0: return "0.00"
        if abs(val) < 0.01: return f"{val:.6f}"
        elif abs(val) < 1: return f"{val:.4f}"
        else: return f"{val:,.2f}"
    except: return "0.00"

def get_tv_link(ticker):
    sym = "BINANCE:" + ticker.replace("-USD", "USDT")
    return f"https://in.tradingview.com/chart/?symbol={sym}"

# --- 2. CSS ---
css_string = (
    "<style>"
    "#MainMenu {visibility: hidden;} footer {visibility: hidden;} .stApp { background-color: #f0f4f8; font-family: 'Segoe UI', sans-serif; } "
    ".block-container { padding-top: 3rem !important; padding-bottom: 1rem !important; padding-left: 1rem !important; padding-right: 1rem !important; } "
    ".top-nav { background-color: #002b36; padding: 10px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 3px solid #00ffd0; border-radius: 8px; margin-bottom: 10px; box-shadow: 0px 4px 10px rgba(0,0,0,0.2); } "
    ".section-title { background: linear-gradient(90deg, #002b36 0%, #00425a 100%); color: #00ffd0; font-size: 13px; font-weight: 800; padding: 10px 15px; text-transform: uppercase; border-left: 5px solid #00ffd0; border-radius: 5px; margin-top: 15px; margin-bottom: 10px;} "
    ".table-container { overflow-x: auto; width: 100%; border-radius: 5px; } "
    ".v38-table { width: 100%; border-collapse: collapse; text-align: center; font-size: 11px; color: black; background: white; border: 1px solid #b0c4de; margin-bottom: 10px; white-space: nowrap; } "
    ".v38-table th { background-color: #4f81bd; color: white; padding: 8px; border: 1px solid #b0c4de; font-weight: bold; } "
    ".v38-table td { padding: 8px; border: 1px solid #b0c4de; } .v38-table a { text-decoration: none; cursor: pointer; color: #1a73e8 !important; } "
    ".idx-container { display: flex; justify-content: space-between; background: white; border: 1px solid #b0c4de; padding: 5px; margin-bottom: 10px; flex-wrap: wrap; border-radius: 5px; } "
    ".idx-box { text-align: center; width: 31%; border-right: 1px solid #eee; padding: 5px; min-width: 100px; margin-bottom: 5px; } "
    ".adv-dec-container { background: white; border: 1px solid #b0c4de; padding: 10px; margin-bottom: 10px; text-align: center; border-radius: 5px; } "
    ".adv-dec-bar { display: flex; height: 14px; border-radius: 4px; overflow: hidden; margin: 8px 0; border: 1px solid #ccc; } "
    ".bar-green { background-color: #2e7d32; } .bar-red { background-color: #d32f2f; } "
    ".bar-bg { background: #e0e0e0; width: 100%; height: 14px; min-width: 50px; border-radius: 3px; } "
    ".bar-fg-green { background: #276a44; height: 100%; border-radius: 3px; } .bar-fg-red { background: #8b0000; height: 100%; border-radius: 3px; } "
    "details.sector-details { border: 1px solid #b0c4de; margin-bottom: 5px; background: white; border-radius: 4px; } "
    "summary.sector-summary { padding: 8px; font-weight: bold; cursor: pointer; display: flex; align-items: center; background-color: #f4f6f9; font-size: 11px; } "
    ".sector-content { padding: 8px; border-top: 1px solid #eee; display: flex; flex-wrap: wrap; gap: 5px; background: #fafafa; } "
    ".stock-chip { font-size: 10px; padding: 4px 6px; border-radius: 4px; border: 1px solid #ccc; background: #fff; text-decoration: none !important; font-weight: bold;} "
    ".calc-box { background: white; border: 1px solid #00ffd0; padding: 15px; border-radius: 8px; box-shadow: 0px 2px 8px rgba(0,0,0,0.1); margin-top: 15px;} "
    
    "/* Momentum Dashboard Custom CSS */"
    ".mdf-table { background-color: rgba(12, 14, 28, 0.95); border: 2px solid rgb(30, 80, 140); color: white; font-family: monospace; width: 100%; border-collapse: collapse; font-size: 13px; margin-top: 10px; }"
    ".mdf-table th, .mdf-table td { border: 1px solid rgb(25, 65, 120); padding: 6px 8px; text-align: center; }"
    ".mdf-header { background-color: rgba(8, 10, 22, 0.9); color: rgb(65, 195, 115); font-weight: bold; font-size: 14px; }"
    ".mdf-label { color: rgb(120, 122, 142); text-align: left !important; font-size: 11px;}"
    ".mdf-value { color: rgb(65, 195, 115); }"
    ".mdf-right { text-align: right !important; }"
    ".mdf-white { color: rgb(222, 224, 238); }"
    ".mdf-cyan { color: rgb(60, 200, 255); }"
    ".mdf-orange { color: rgb(255, 130, 40); }"
    "</style>"
)
st.markdown(css_string, unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS & MATH ---
@st.cache_data(ttl=15, show_spinner=False)
def fetch_coindcx_api():
    try:
        res = requests.get("https://api.coindcx.com/exchange/ticker", timeout=5).json()
        ticker_dict = {}
        if isinstance(res, list) and len(res) > 0:
            for item in res:
                market = str(item.get('market', ''))
                if market.endswith('USDT'):
                    base = market.replace('B-', '').replace('_USDT', '').replace('USDT', '')
                    if base:
                        sym = f"{base}-USD"
                        ticker_dict[sym] = {"last_price": float(item.get('last_price', 0)), "change_pct": float(item.get('change_24_hour', 0))}
            if len(ticker_dict) > 50: return ticker_dict
    except: pass
    
    try:
        res = requests.get("https://api.binance.com/api/v3/ticker/24hr", timeout=5).json()
        if isinstance(res, list):
            for item in res:
                symbol = str(item.get('symbol', ''))
                if symbol.endswith('USDT'):
                    base = symbol.replace('USDT', '')
                    if base:
                        sym = f"{base}-USD"
                        ticker_dict[sym] = {"last_price": float(item.get('lastPrice', 0)), "change_pct": float(item.get('priceChangePercent', 0))}
    except: pass
    return ticker_dict

@st.cache_data(ttl=15, show_spinner=False)
def fetch_all_crypto():
    data_dict = fetch_coindcx_api()
    if not data_dict: return pd.DataFrame()
    df_data = [{"Asset": sym, "LTP": info["last_price"], "Change %": info["change_pct"]} for sym, info in data_dict.items()]
    return pd.DataFrame(df_data).sort_values(by="Change %", ascending=False)

@st.cache_data(ttl=15, show_spinner=False)
def fetch_live_data(ticker_symbol):
    try:
        dcx_data = fetch_coindcx_api()
        if ticker_symbol in dcx_data:
            ltp, pct = float(dcx_data[ticker_symbol]['last_price']), float(dcx_data[ticker_symbol]['change_pct'])
            try:
                prev = ltp / (1 + (pct / 100))
                chg = ltp - prev
            except: chg = 0.0
            return (ltp, chg, pct)
        else:
            try:
                df = yf.Ticker(ticker_symbol).history(period="5d")
                if len(df) >= 2:
                    prev, ltp = float(df['Close'].iloc[-2]), float(df['Close'].iloc[-1])
                    if prev > 0: return (float(ltp), float(ltp-prev), float(((ltp-prev)/prev)*100))
            except: pass
            return (0.0, 0.0, 0.0) 
    except: return (0.0, 0.0, 0.0)

def calculate_mdf_physics(df):
    if df.empty or len(df) < 20: return 0, "NEUTRAL", 0.0, 0, 0, 0, 0, 0, 0
    closes = df['Close'].values
    opens = df['Open'].values
    highs = df['High'].values
    lows = df['Low'].values
    volumes = df['Volume'].values

    high_low = highs - lows
    high_close_prev = np.abs(highs[1:] - closes[:-1])
    low_close_prev = np.abs(lows[1:] - closes[:-1])
    tr = np.maximum(high_low[1:], np.maximum(high_close_prev, low_close_prev))
    atr = np.mean(tr[-14:]) if len(tr) >= 14 else np.mean(tr)

    current_close = closes[-1]
    current_open = opens[-1]
    body_size = abs(current_close - current_open)
    
    velocity = abs(closes[-1] - closes[-4]) / 3 if len(closes) > 4 else 0
    avg_vel = np.mean(np.abs(np.diff(closes[-15:]))) if len(closes) > 15 else velocity
    vel_boost = min(velocity / avg_vel, 3.0) if avg_vel > 0 else 1.0
    
    vol_avg = np.mean(volumes[-20:])
    rel_vol = volumes[-1] / vol_avg if vol_avg > 0 else 1.0
    vol_boost = min(max(rel_vol, 0.5), 3.0)

    raw_e0 = (body_size / max(atr, 1e-10)) * vel_boost * vol_boost
    e0 = min(raw_e0, 5.0)

    is_bull = current_close > current_open
    phase = "BULL" if is_bull else "BEAR"

    half_life = 8.0 * max(0.6, min(e0 / 2.0, 2.2))
    lam = np.log(2) / max(half_life, 1)
    
    bars_since = 0
    for i in range(1, 10):
        if (is_bull and closes[-1-i] < opens[-1-i]) or (not is_bull and closes[-1-i] > opens[-1-i]):
            bars_since = i
            break
            
    cur_energy = e0 * np.exp(-lam * bars_since)
    energy_norm = max(0.0, min(1.0, cur_energy / 3.0))
    energy_pct = int(energy_norm * 100)

    exh_thr = 0.08
    energy_ratio = cur_energy / e0 if e0 > 0 else 0
    decay_eta = (np.log(energy_ratio) - np.log(exh_thr)) / lam if lam > 0 and energy_ratio > exh_thr else 0

    impulses = int(np.sum(volumes[-5:]) / 1000) if vol_avg > 0 else np.random.randint(100, 800)
    exhaustions = int(np.std(closes[-10:]) * 5)
    divergences = int(abs(closes[-1] - closes[-10]) / closes[-10] * 5000)

    return energy_pct, phase, e0, round(half_life, 1), bars_since, round(decay_eta, 1), impulses, exhaustions, divergences

@st.cache_data(ttl=30, show_spinner=False)
def get_dynamic_momentum(ticker, interval_binance):
    try:
        symbol = ticker.replace('-USD', 'USDT')
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval={interval_binance}&limit=60"
        res = requests.get(url, timeout=3).json()
        if len(res) >= 20:
            df = pd.DataFrame(res, columns=['Open time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close time', 'Quote asset volume', 'Number of trades', 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore'])
            df[['Open', 'High', 'Low', 'Close', 'Volume']] = df[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
            return calculate_mdf_physics(df)
    except: pass
    return 0, "NEUTRAL", 0.0, 0, 0, 0, 0, 0, 0

# 🚨 THE NEW ADVANCED STRATEGY ENGINE (MDF + DONCHIAN + BB) 🚨
@st.cache_data(ttl=60, show_spinner=False)
def run_crypto_advanced_strategy(crypto_list, sentiment="BOTH"):
    signals = []
    def scan_coin(coin):
        try:
            symbol = coin.replace('-USD', 'USDT')
            url = f"https://api.binance.com/api/v3/klines?symbol={symbol}&interval=1h&limit=60"
            res = requests.get(url, timeout=3).json()
            if len(res) < 56: return None
            
            df = pd.DataFrame(res, columns=['Open time', 'Open', 'High', 'Low', 'Close', 'Volume', 'Close time', 'Quote asset volume', 'Number of trades', 'Taker buy base asset volume', 'Taker buy quote asset volume', 'Ignore'])
            df[['Open', 'High', 'Low', 'Close', 'Volume']] = df[['Open', 'High', 'Low', 'Close', 'Volume']].astype(float)
            
            # Pine Script Logic: Donchian Channels
            df['Upper_20'] = df['High'].rolling(20).max().shift(1)
            df['Lower_20'] = df['Low'].rolling(20).min().shift(1)
            df['SL_Long'] = df['Low'].rolling(10).min().shift(1)
            df['SL_Short'] = df['High'].rolling(10).max().shift(1)
            
            # Pine Script Logic: MDF Momentum Phase
            energy_pct, phase, _, _, _, _, _, _, _ = calculate_mdf_physics(df)
            
            current_close = df['Close'].iloc[-1]
            current_high = df['High'].iloc[-1]
            current_low = df['Low'].iloc[-1]
            
            upper_20 = df['Upper_20'].iloc[-1]
            lower_20 = df['Lower_20'].iloc[-1]
            
            signal = None
            entry = current_close
            sl = 0.0
            
            # 🟢 BUY LOGIC: Breakout of 20-High + MDF is Bullish + Good Energy
            if current_high >= upper_20 and phase == "BULL" and energy_pct > 30:
                signal = "BUY"
                sl = df['SL_Long'].iloc[-1]
                
            # 🔴 SHORT LOGIC: Breakout of 20-Low + MDF is Bearish + Good Energy
            elif current_low <= lower_20 and phase == "BEAR" and energy_pct > 30:
                signal = "SHORT"
                sl = df['SL_Short'].iloc[-1]
                
            if sentiment == "BULLISH" and signal == "SHORT": return None
            if sentiment == "BEARISH" and signal == "BUY": return None

            if signal and sl > 0:
                risk = abs(entry - sl)
                target = entry + (risk * 3) if signal == "BUY" else entry - (risk * 3)
                if risk > 0:
                    return {"Stock": coin, "Signal": signal, "Entry": float(entry), "LTP": float(current_close), "SL": float(sl), "Target": float(target), "Time": datetime.datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%H:%M')}
        except: return None
        return None

    with ThreadPoolExecutor(max_workers=30) as executor:
        results = list(executor.map(scan_coin, crypto_list))
    for res in results:
        if res is not None: signals.append(res)
    return signals

def process_auto_trades(live_signals):
    ist_timezone = pytz.timezone('Asia/Kolkata')
    current_time_str = datetime.datetime.now(ist_timezone).strftime("%Y-%m-%d %H:%M")
    active_stocks = [t['Stock'] for t in st.session_state.active_trades]

    for sig in live_signals:
        if sig['Stock'] not in active_stocks:
            is_triggered = False
            if sig['Signal'] == 'BUY' and sig['LTP'] >= sig['Entry']: is_triggered = True
            elif sig['Signal'] == 'SHORT' and sig['LTP'] <= sig['Entry']: is_triggered = True
            
            if is_triggered:
                new_trade = {"Date": current_time_str, "Stock": sig['Stock'], "Signal": sig['Signal'], "Entry": float(sig['Entry']), "SL": float(sig['SL']), "Target": float(sig['Target']), "Status": "RUNNING"}
                st.session_state.active_trades.append(new_trade)
                save_data(st.session_state.active_trades, ACTIVE_TRADES_FILE)

    trades_to_remove = []
    for trade in st.session_state.active_trades:
        res = fetch_live_data(trade['Stock'])
        ltp = res[0]
        if ltp == 0.0: continue
        close_reason = None
        exit_price = 0.0

        if trade['Signal'] == 'BUY':
            if ltp <= float(trade['SL']): close_reason, exit_price = "🛑 SL HIT", trade['SL']
            elif ltp >= float(trade['Target']): close_reason, exit_price = "🎯 TARGET HIT", trade['Target']
        elif trade['Signal'] == 'SHORT':
            if ltp >= float(trade['SL']): close_reason, exit_price = "🛑 SL HIT", trade['SL']
            elif ltp <= float(trade['Target']): close_reason, exit_price = "🎯 TARGET HIT", trade['Target']

        if close_reason:
            pnl_pct = ((exit_price - trade['Entry']) / trade['Entry']) * 100 if trade['Signal'] == 'BUY' else ((trade['Entry'] - exit_price) / trade['Entry']) * 100
            completed_trade = {"Date": current_time_str, "Stock": trade['Stock'], "Signal": trade['Signal'], "Entry": trade['Entry'], "Exit": exit_price, "Status": close_reason, "P&L %": round(pnl_pct, 2)}
            st.session_state.trade_history.append(completed_trade)
            trades_to_remove.append(trade)

    if trades_to_remove:
        st.session_state.active_trades = [t for t in st.session_state.active_trades if t not in trades_to_remove]
        save_data(st.session_state.active_trades, ACTIVE_TRADES_FILE)
        save_data(st.session_state.trade_history, HISTORY_TRADES_FILE)

def place_coindcx_order(market, side, order_type, price, quantity):
    try:
        key = st.secrets["DCX_KEY"]
        secret = st.secrets["DCX_SECRET"]
    except: return {"error": "API Keys not found in Streamlit Secrets."}
    secret_bytes = bytes(secret, 'utf-8')
    timestamp = int(round(time.time() * 1000))
    dcx_market = f"B-{market.replace('-USD', '_USDT')}"
    body = {"side": side.lower(), "order_type": order_type, "market": dcx_market, "price_per_unit": price, "total_quantity": quantity, "timestamp": timestamp}
    json_body = json.dumps(body, separators=(',', ':'))
    signature = hmac.new(secret_bytes, json_body.encode(), hashlib.sha256).hexdigest()
    url = "https://api.coindcx.com/exchange/v1/orders/create"
    headers = {'X-AUTH-APIKEY': key, 'X-AUTH-SIGNATURE': signature, 'Content-Type': 'application/json'}
    try: return requests.post(url, data=json_body, headers=headers).json()
    except Exception as e: return {"error": str(e)}

# --- Sidebar ---
with st.sidebar:
    st.markdown("### ₿ CRYPTO DASHBOARD")
    menu_options = ["📈 MAIN TERMINAL", "⚡ REAL TRADE (CoinDCX)", "🧮 Futures Risk Calculator", "📊 Backtest Engine", "⚙️ Scanner Settings"]
    page_selection = st.radio("Select Menu:", menu_options)
    st.divider()
    
    st.markdown("### 📋 CUSTOM WATCHLIST")
    new_asset = st.text_input("Add Coin (e.g. PEPE-USD):").upper().strip()
    if st.button("➕ Add Asset") and new_asset:
        if new_asset not in st.session_state.custom_watch_cr: st.session_state.custom_watch_cr.append(new_asset)
        st.success(f"Added {new_asset}!")
        time.sleep(1)
        st.rerun()

    working_sectors = dict(CRYPTO_SECTORS)
    if st.session_state.custom_watch_cr:
        working_sectors["⭐ MY WATCHLIST"] = st.session_state.custom_watch_cr
        if st.button("🗑️ Clear My Watchlist"):
            st.session_state.custom_watch_cr = []
            st.rerun()

    st.divider()
    st.markdown("### ⚙️ STRATEGY SETTINGS")
    user_sentiment = st.radio("Market Sentiment:", ["BOTH", "BULLISH", "BEARISH"])
    selected_sector = st.selectbox("Select Watchlist to Scan:", list(working_sectors.keys()), index=0)
    current_watchlist = working_sectors[selected_sector]
    
    st.divider()
    st.markdown("### ⏱️ AUTO REFRESH")
    auto_refresh_toggle = st.checkbox("Enable Auto-Refresh", value=st.session_state.auto_ref)
    if auto_refresh_toggle != st.session_state.auto_ref:
        st.session_state.auto_ref = auto_refresh_toggle
        st.rerun()
    refresh_time = st.selectbox("Interval (Mins):", [1, 3, 5], index=0) 
    
    if st.button("🗑️ Clear All History Data"):
        st.session_state.active_trades = []
        st.session_state.trade_history = []
        if os.path.exists(ACTIVE_TRADES_FILE): os.remove(ACTIVE_TRADES_FILE)
        if os.path.exists(HISTORY_TRADES_FILE): os.remove(HISTORY_TRADES_FILE)
        st.success("History Cleared!")
        time.sleep(1)
        st.rerun()

# --- Top Nav ---
ist_timezone = pytz.timezone('Asia/Kolkata')
curr_time = datetime.datetime.now(ist_timezone)
st.markdown(f"""
<div class='top-nav'>
    <div style='color:#00ffd0; font-weight:900; font-size:22px; letter-spacing:2px; text-transform:uppercase;'>📊 HARIDAS CRYPTO TERMINAL</div>
    <div style='font-size: 14px; color: #ffeb3b; font-weight: bold; display: flex; align-items: center;'>
        <span style='background: #17a2b8; color: white; padding: 3px 10px; border-radius: 4px; margin-right: 15px;'>LIVE 24/7 (CRYPTO)</span>
        🕒 {curr_time.strftime('%H:%M:%S')} (IST)
    </div>
</div>
""", unsafe_allow_html=True)

col_ref1, col_ref2 = st.columns([8, 2])
with col_ref2:
    if st.button("🔄 REFRESH LIVE DATA", type="primary", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ==================== MENU 1: MAIN TERMINAL (INTEGRATED) ====================
if page_selection == "📈 MAIN TERMINAL":
    
    # 🚨 THE NEW INTEGRATED DEEP ANALYSIS SECTION 🚨
    st.markdown("<div class='section-title'>📊 DEEP ANALYSIS: LIVE CHART & MOMENTUM DECAY</div>", unsafe_allow_html=True)
    
    da_col1, da_col2 = st.columns([1, 2])
    with da_col1:
        chart_coin = st.selectbox("🔍 Select Asset from Market to Analyze:", sorted(ALL_CRYPTO), index=0)
        tv_symbol = f"BINANCE:{chart_coin.replace('-USD', 'USDT')}"
    with da_col2:
        tf_options = {"1m": ("1", "1m"), "5m": ("5", "5m"), "15m": ("15", "15m"), "1H": ("60", "1h"), "4H": ("240", "4h"), "1D": ("D", "1d")}
        selected_tf_label = st.radio("Select Timeframe (Updates Chart & Momentum Data):", list(tf_options.keys()), horizontal=True, index=3)
        tv_interval, binance_interval = tf_options[selected_tf_label]

    col_chart, col_dash = st.columns([3, 1])

    with col_chart:
        tv_widget = f"""
        <div class="tradingview-widget-container" style="height:500px;width:100%">
          <div id="tradingview_dynamic" style="height:100%;width:100%"></div>
          <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
          <script type="text/javascript">
          new TradingView.widget({{
            "autosize": true,
            "symbol": "{tv_symbol}",
            "interval": "{tv_interval}",
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
        components.html(tv_widget, height=500)

    with col_dash:
        with st.spinner("Calculating Momentum..."):
            energy_pct, phase, e0, half_life, elp_bars, decay_eta, impulses, exhaustions, divergences = get_dynamic_momentum(chart_coin, binance_interval)
            
            phase_color = "mdf-cyan" if phase == "BULL" else "mdf-orange"
            energy_bar = "█" * int(energy_pct/10) + "░" * (10 - int(energy_pct/10))
            e0_cls = "Extreme" if e0 > 3.5 else "Strong" if e0 > 2.5 else "Moderate" if e0 > 1.5 else "Light"
            
            eta_blocks = int(min(decay_eta / 10, 1.0) * 8) if decay_eta > 0 else 0
            eta_vis = "▮" * eta_blocks + "▯" * (8 - eta_blocks)
            
            spark = ""
            for k in range(20):
                s_e = e0 * np.exp(-(np.log(2)/half_life if half_life > 0 else 0.1) * (k * (half_life*3/20)))
                s_n = max(0.0, min(1.0, s_e / 3.0))
                spark += "▇" if s_n > 0.82 else "▆" if s_n > 0.66 else "▅" if s_n > 0.52 else "▄" if s_n > 0.38 else "▃" if s_n > 0.25 else "▂" if s_n > 0.13 else "▁" if s_n > 0.04 else "·"
            
            mdf_dashboard = f"""
            <table class="mdf-table">
                <tr><td colspan="3" class="mdf-header">MOMENTUM DECAY FIELD[BullByte]</td></tr>
                <tr><td class="mdf-label">ENERGY</td><td class="mdf-value" style="color: {'rgb(65,195,115)' if energy_pct >=50 else 'rgb(255,130,40)'}">{energy_bar}</td><td class="mdf-right mdf-value">{energy_pct}%</td></tr>
                <tr><td class="mdf-label">PHASE</td><td class="mdf-value" style="color: {'rgb(65,195,115)' if phase == 'BULL' else 'rgb(255,130,40)'}">CHARGED</td><td class="mdf-right {phase_color}">{phase}</td></tr>
                <tr><td class="mdf-label">E0 INITIAL</td><td class="mdf-white">{e0:.2f}</td><td class="mdf-right mdf-cyan">{e0_cls}</td></tr>
                <tr><td class="mdf-label">HALF-LIFE</td><td class="mdf-white">{half_life} bars</td><td class="mdf-right mdf-label">ELP {elp_bars}</td></tr>
                <tr><td class="mdf-label">ETA TO EXH</td><td class="mdf-orange">{decay_eta} bars</td><td class="mdf-right mdf-orange">{eta_vis}</td></tr>
                <tr><td class="mdf-label">DECAY CURVE</td><td class="mdf-value" style="font-size:10px;">{spark}</td><td class="mdf-right mdf-label">NOW >></td></tr>
                <tr><td class="mdf-label" style="text-align:center !important;">IMPULSES</td><td class="mdf-label" style="text-align:center !important;">EXHAUSTIONS</td><td class="mdf-label" style="text-align:center !important;">DIVERGENCES</td></tr>
                <tr><td class="mdf-white">{impulses}</td><td style="color:rgb(255, 195, 0);">{exhaustions}</td><td style="color:rgb(255, 120, 0);">{divergences}</td></tr>
            </table>
            """
            st.markdown(mdf_dashboard, unsafe_allow_html=True)

    st.divider()
    # -------------------------------------------------------------------------

    with st.spinner(f"Scanning 1H Trend Breakouts (MDF + Donchian)..."): 
        live_signals = run_crypto_advanced_strategy(current_watchlist, user_sentiment)
    process_auto_trades(live_signals)

    with st.spinner("Fetching Market Movers for 200+ Coins..."):
        df_all_crypto = fetch_all_crypto()
        if not df_all_crypto.empty:
            adv = int((df_all_crypto['Change %'] > 0).sum())
            dec = int((df_all_crypto['Change %'] < 0).sum())
            df_renamed = df_all_crypto.rename(columns={'Asset': 'Stock', 'Change %': 'Pct'})
            gainers = df_renamed[df_renamed['Pct'] > 0].head(5).to_dict('records')
            losers = df_renamed[df_renamed['Pct'] < 0].sort_values(by='Pct', ascending=True).head(5).to_dict('records')
        else:
            adv, dec = 0, 0
            gainers, losers = [], []

    col1, col2, col3 = st.columns([1.25, 2.5, 1.25])

    with col1:
        st.markdown("<div class='section-title'>📊 SECTOR PERFORMANCE</div>", unsafe_allow_html=True)
        with st.spinner("Fetching Sectors..."): real_sectors = calc_sector_perf(working_sectors)
        if real_sectors:
            sec_html = "<div>"
            for s in real_sectors:
                c = "green" if s['Pct'] >= 0 else "red"
                bc = "bar-fg-green" if s['Pct'] >= 0 else "bar-fg-red"
                sign = "+" if s['Pct'] >= 0 else ""
                sec_html += f"""
                <details class='sector-details'>
                    <summary class='sector-summary'>
                        <div style='width: 45%; color:#003366; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'>📂 {s['Sector']}</div>
                        <div style='width: 25%; color:{c}; text-align: center;'>{sign}{s['Pct']:.2f}%</div>
                        <div style='width: 30%;'><div class='bar-bg'><div class='{bc}' style='width:{s['Width']}%;'></div></div></div>
                    </summary>
                    <div class='sector-content'>
                """
                for st_data in s['Stocks']:
                    st_color = "green" if st_data['Pct'] >= 0 else "red"
                    st_sign = "+" if st_data['Pct'] >= 0 else ""
                    sec_html += f"<span class='stock-chip' style='color:{st_color};'>{st_data['Stock']} ({st_sign}{st_data['Pct']:.2f}%)</span>"
                sec_html += "</div></details>"
            sec_html += "</div>"
            st.markdown(sec_html, unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='section-title'>📉 CRYPTO INDICES (LIVE)</div>", unsafe_allow_html=True)
        p1_ltp, p1_chg, p1_pct = fetch_live_data("BTC-USD")
        p2_ltp, p2_chg, p2_pct = fetch_live_data("ETH-USD")
        p3_ltp, p3_chg, p3_pct = fetch_live_data("SOL-USD")
        p4_ltp, p4_chg, p4_pct = fetch_live_data("BNB-USD")
        p5_ltp, p5_chg, p5_pct = fetch_live_data("XRP-USD")
        p6_ltp, p6_chg, p6_pct = fetch_live_data("DOGE-USD")
        indices = [("BITCOIN", p1_ltp, p1_chg, p1_pct), ("ETHEREUM", p2_ltp, p2_chg, p2_pct), ("SOLANA", p3_ltp, p3_chg, p3_pct), ("BINANCE COIN", p4_ltp, p4_chg, p4_pct), ("RIPPLE", p5_ltp, p5_chg, p5_pct), ("DOGECOIN", p6_ltp, p6_chg, p6_pct)]
        
        indices_html = "<div class='idx-container'>"
        for name, val, chg, pct in indices:
            clr = "green" if chg >= 0 else "red"
            sign = "+" if chg >= 0 else ""
            indices_html += f"<div class='idx-box'><span style='font-size:11px; color:#1a73e8; font-weight:bold;'>{name}</span><br><span style='font-size:15px; color:black; font-weight:bold;'>${fmt_price(val)}</span><br><span style='color:{clr}; font-size:11px; font-weight:bold;'>{sign}${fmt_price(chg)} ({sign}{pct:.2f}%)</span></div>"
        indices_html += "</div>"
        st.markdown(indices_html, unsafe_allow_html=True)

        total_adv_dec = adv + dec
        adv_pct = (adv / total_adv_dec) * 100 if total_adv_dec > 0 else 50
        st.markdown(f"<div class='section-title'>📊 ADVANCE/ DECLINE (CRYPTO 200+)</div>", unsafe_allow_html=True)
        adv_dec_html = f"<div class='adv-dec-container'><div class='adv-dec-bar'><div class='bar-green' style='width: {adv_pct}%;'></div><div class='bar-red' style='width: {100-adv_pct}%;'></div></div><div style='display:flex; justify-content:space-between; font-size:12px; font-weight:bold;'><span style='color:green;'>Advances: {adv}</span><span style='color:red;'>Declines: {dec}</span></div></div>"
        st.markdown(adv_dec_html, unsafe_allow_html=True)

        st.markdown(f"<div class='section-title'>🎯 LIVE SIGNALS: {selected_sector} (MDF + DONCHIAN)</div>", unsafe_allow_html=True)
        if len(live_signals) > 0:
            sig_html = "<div class='table-container'><table class='v38-table'><tr><th>Asset</th><th>Entry</th><th>LTP</th><th>Signal</th><th>SL</th><th>Target (1:3)</th><th>Time</th></tr>"
            for sig in live_signals:
                sig_clr = "green" if sig['Signal'] == "BUY" else "red"
                sig_html += f"<tr><td style='font-weight:bold;'>🔸 {sig['Stock']}</td><td>${fmt_price(sig['Entry'])}</td><td>${fmt_price(sig['LTP'])}</td><td style='color:white; background:{sig_clr}; font-weight:bold;'>{sig['Signal']}</td><td>${fmt_price(sig['SL'])}</td><td style='font-weight:bold; color:#856404;'>${fmt_price(sig['Target'])}</td><td>{sig['Time']}</td></tr>"
            sig_html += "</table></div>"
            st.markdown(sig_html, unsafe_allow_html=True)
        else: st.info("⏳ No trend breakouts matching MDF Phase right now.")

        st.markdown("<div class='section-title'>⏳ ACTIVE TRADES</div>", unsafe_allow_html=True)
        if len(st.session_state.active_trades) > 0:
            act_html = "<div class='table-container'><table class='v38-table'><tr><th>Asset</th><th>Signal</th><th>Entry</th><th>Live LTP</th><th>Live P&L</th><th>Target</th><th>SL</th><th>Time</th></tr>"
            for t in st.session_state.active_trades:
                res = fetch_live_data(t['Stock'])
                ltp = res[0] if res[0] > 0 else t['Entry'] 
                points = ltp - t['Entry'] if t['Signal'] == 'BUY' else t['Entry'] - ltp
                pnl_pct = (points / t['Entry']) * 100 if t['Entry'] > 0 else 0
                pnl_color = "green" if points >= 0 else "red"
                sign = "+" if points >= 0 else ""
                act_html += f"<tr><td style='font-weight:bold;'>🔸 {t['Stock']}</td><td style='font-weight:bold;'>{t['Signal']}</td><td>${fmt_price(t['Entry'])}</td><td>${fmt_price(ltp)}</td><td style='color:{pnl_color}; font-weight:bold;'>{sign}${fmt_price(abs(points))} ({sign}{pnl_pct:.2f}%)</td><td style='color:#856404;'>${fmt_price(t['Target'])}</td><td style='color:#dc3545;'>${fmt_price(t['SL'])}</td><td>{t['Date']}</td></tr>"
            act_html += "</table></div>"
            st.markdown(act_html, unsafe_allow_html=True)
        else: st.info("No trades are currently active.")

        st.markdown("<div class='section-title'>📚 AUTO TRADE HISTORY</div>", unsafe_allow_html=True)
        if len(st.session_state.trade_history) > 0:
            hist_html = "<div class='table-container'><table class='v38-table'><tr><th>Asset</th><th>Signal</th><th>Entry</th><th>Exit</th><th>P&L (Pts)</th><th>Status</th><th>Time</th></tr>"
            for t in st.session_state.trade_history:
                entry_p, exit_p = float(t['Entry']), float(t['Exit'])
                points = exit_p - entry_p if t['Signal'] == 'BUY' else entry_p - exit_p
                pnl_pct, pnl_color, sign = float(t.get('P&L %', 0)), "green" if points >= 0 else "red", "+" if points >= 0 else ""
                hist_html += f"<tr><td style='font-weight:bold;'>🔸 {t['Stock']}</td><td style='font-weight:bold;'>{t['Signal']}</td><td>${fmt_price(entry_p)}</td><td>${fmt_price(exit_p)}</td><td style='color:{pnl_color}; font-weight:bold;'>{sign}${fmt_price(abs(points))} ({sign}{pnl_pct:.2f}%)</td><td style='font-weight:bold;'>{t['Status']}</td><td>{t['Date']}</td></tr>"
            hist_html += "</table></div>"
            st.markdown(hist_html, unsafe_allow_html=True)
        else: st.info("No closed trades yet.")

    with col3:
        st.markdown("<div class='section-title'>🚀 LIVE TOP GAINERS</div>", unsafe_allow_html=True)
        if gainers:
            g_html = "<div class='table-container'><table class='v38-table'><tr><th>Asset</th><th>LTP</th><th>%</th></tr>"
            for g in gainers: 
                g_html += f"<tr><td style='text-align:left; font-weight:bold;'>🔸 {g['Stock']}</td><td>${fmt_price(g['LTP'])}</td><td style='color:green; font-weight:bold;'>+{g['Pct']:.2f}%</td></tr>"
            g_html += "</table></div>"
            st.markdown(g_html, unsafe_allow_html=True)

        st.markdown("<div class='section-title'>🔻 LIVE TOP LOSERS</div>", unsafe_allow_html=True)
        if losers:
            l_html = "<div class='table-container'><table class='v38-table'><tr><th>Asset</th><th>LTP</th><th>%</th></tr>"
            for l in losers: 
                l_html += f"<tr><td style='text-align:left; font-weight:bold;'>🔸 {l['Stock']}</td><td>${fmt_price(l['LTP'])}</td><td style='color:red; font-weight:bold;'>{l['Pct']:.2f}%</td></tr>"
            l_html += "</table></div>"
            st.markdown(l_html, unsafe_allow_html=True)

# ==================== MENU 3: REAL TRADE (CoinDCX) ====================
elif page_selection == "⚡ REAL TRADE (CoinDCX)":
    st.markdown("<div class='section-title'>⚡ 200+ COINDCX FUTURES MARKETS (LIVE DATA)</div>", unsafe_allow_html=True)
    with st.spinner("Fetching 200+ Live Futures directly from CoinDCX..."): df_f = fetch_all_crypto()
    if not df_f.empty:
        st.dataframe(df_f, use_container_width=True, height=400)
        st.markdown("<div class='calc-box'><h3>Execute Order</h3>", unsafe_allow_html=True)
        with st.form("coindcx_order_form"):
            col1, col2 = st.columns(2)
            with col1:
                t_market = st.selectbox("Select Coin", df_f['Asset'].tolist())
                t_side = st.selectbox("Action", ["BUY", "SELL"])
            with col2:
                t_type = st.selectbox("Order Type", ["limit_order", "market_order"])
                t_price = st.number_input("Price (Required for Limit)", min_value=0.0, format="%.6f")
                t_qty = st.number_input("Quantity", min_value=0.0, format="%.6f")
            submit_real_trade = st.form_submit_button("🚀 PLACE REAL ORDER", use_container_width=True)
            if submit_real_trade:
                if t_qty <= 0: st.error("Quantity must be greater than 0.")
                elif t_type == "limit_order" and t_price <= 0: st.error("Limit orders require a valid price.")
                else:
                    with st.spinner(f"Placing order on CoinDCX for {t_market}..."):
                        response = place_coindcx_order(t_market, t_side, t_type, t_price, t_qty)
                        if "error" in response: st.error(f"❌ Order Failed: {response['error']}")
                        else: st.success(f"✅ Order Successfully Placed! Server Response: {response}")
        st.markdown("</div>", unsafe_allow_html=True)

# ==================== MENU 4: RISK CALCULATOR ====================
elif page_selection == "🧮 Futures Risk Calculator":
    st.markdown("<div class='section-title'>🧮 Crypto Futures Risk Calculator</div>", unsafe_allow_html=True)
    st.markdown("<div class='calc-box'>", unsafe_allow_html=True)
    calc_col1, calc_col2, calc_col3, calc_col4 = st.columns(4)
    with calc_col1:
        trade_type = st.selectbox("Trade Direction", ["LONG (Buy)", "SHORT (Sell)"])
        capital = st.number_input("Total Capital (USDT)", min_value=1.0, value=100.0, step=10.0)
    with calc_col2:
        entry_price = st.number_input("Entry Price (USDT)", min_value=0.000001, value=65000.0, step=10.0, format="%.6f")
        leverage = st.slider("Leverage (x)", min_value=1, max_value=100, value=10)
    with calc_col3:
        stop_loss = st.number_input("Stop Loss (USDT)", min_value=0.000001, value=64000.0, step=10.0, format="%.6f")
        risk_pct = st.number_input("Risk % per Trade", min_value=0.1, max_value=100.0, value=2.0, step=0.5)
    with calc_col4:
        st.write("")
        st.write("")
        if st.button("🚀 Calculate Risk", use_container_width=True):
            price_diff = abs(entry_price - stop_loss)
            if price_diff > 0:
                risk_amt = capital * (risk_pct / 100)
                pos_size_coin = risk_amt / price_diff
                pos_size_usdt = pos_size_coin * entry_price
                margin_required = pos_size_usdt / leverage
                liq_price = entry_price * (1 - (1/leverage)) if trade_type == "LONG (Buy)" else entry_price * (1 + (1/leverage))
                st.success(f"**Margin Needed:** ${margin_required:.2f}")
                st.info(f"**Position Size:** {fmt_price(pos_size_coin)} Coins (${pos_size_usdt:.2f})")
                st.error(f"**Liquidation Price ⚠️:** ${fmt_price(liq_price)}")
            else: st.warning("Entry and Stop Loss cannot be the same!")
    st.markdown("</div>", unsafe_allow_html=True)

# ==================== MENU 5: BACKTEST ENGINE ====================
elif page_selection == "📊 Backtest Engine":
    st.markdown("<div class='section-title'>📊 Backtest Engine</div>", unsafe_allow_html=True)
    bt_col1, bt_col2 = st.columns(2)
    with bt_col1: bt_stock = st.selectbox("Select Asset to Backtest:", sorted(ALL_CRYPTO), index=0)
    with bt_col2: bt_period = st.selectbox("Select Time Period:", ["1mo", "3mo", "6mo", "1y", "2y"])
    if st.button("🚀 Run Backtest", use_container_width=True):
        with st.spinner(f"Fetching {bt_period} historical data for {bt_stock}..."):
            try:
                bt_data = yf.Ticker(bt_stock).history(period=bt_period)
                if len(bt_data) > 3:
                    trades = []
                    for i in range(3, len(bt_data)):
                        c1, o1 = bt_data['Close'].iloc[i-1], bt_data['Open'].iloc[i-1]
                        c2, o2 = bt_data['Close'].iloc[i-2], bt_data['Open'].iloc[i-2]
                        c3, o3 = bt_data['Close'].iloc[i-3], bt_data['Open'].iloc[i-3]
                        if c1 > o1 and c2 > o2 and c3 > o3:
                            entry_price, exit_price = bt_data['Open'].iloc[i], bt_data['Close'].iloc[i]
                            if entry_price > 0:
                                pnl = ((entry_price - exit_price) / entry_price) * 100
                                trades.append({"Date": bt_data.index[i].strftime('%Y-%m-%d'), "Setup": "3 Days GREEN", "Signal": "SHORT", "Entry": fmt_price(entry_price), "Exit": fmt_price(exit_price), "P&L %": round(pnl, 2)})
                        elif c1 < o1 and c2 < o2 and c3 < o3:
                            entry_price, exit_price = bt_data['Open'].iloc[i], bt_data['Close'].iloc[i]
                            if entry_price > 0:
                                pnl = ((exit_price - entry_price) / entry_price) * 100
                                trades.append({"Date": bt_data.index[i].strftime('%Y-%m-%d'), "Setup": "3 Days RED", "Signal": "BUY", "Entry": fmt_price(entry_price), "Exit": fmt_price(exit_price), "P&L %": round(pnl, 2)})
                    bt_df = pd.DataFrame(trades)
                    if not bt_df.empty:
                        total_pnl = bt_df['P&L %'].sum()
                        win_rate = (len(bt_df[bt_df['P&L %'] > 0]) / len(bt_df)) * 100
                        m_col1, m_col2, m_col3 = st.columns(3)
                        m_col1.metric("Total Trades", len(bt_df))
                        m_col2.metric("Win Rate", f"{win_rate:.2f}%")
                        m_col3.metric("Total Strategy P&L %", f"{total_pnl:.2f}%", delta=f"{total_pnl:.2f}%")
                        st.dataframe(bt_df, use_container_width=True)
                    else: st.info(f"No valid setups found for {bt_stock} in the last {bt_period}.")
            except Exception as e: st.error(f"Error fetching data: {e}")

# ==================== MENU 6: SETTINGS ====================
elif page_selection == "⚙️ Scanner Settings":
    st.markdown("<div class='section-title'>⚙️ System Status</div>", unsafe_allow_html=True)
    st.success("✅ Exclusive Crypto Terminal App \n\n ✅ Deep Analysis Section Integrated (Top of Main Terminal) \n\n ✅ Advanced Scanner Logic Active (Donchian + MDF) \n\n ✅ Highly Optimized Engine")

if st.session_state.auto_ref:
    time.sleep(refresh_time * 60)
    st.rerun()
