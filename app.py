import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(page_title="Haridas Crypto Setup", layout="wide")
st.title("⚡ Haridas Ultra-Fast Crypto Terminal")
st.write("Live LTP & Real-Time Chart (Zero Delay)")

# TradingView-এর লাইভ চার্ট এবং LTP উইজেট (WebSocket)
tv_widget = """
<div class="tradingview-widget-container" style="height:100%;width:100%">
  <div id="tradingview_fast" style="height:600px;width:100%"></div>
  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget(
  {
  "autosize": true,
  "symbol": "BINANCE:BTCUSDT",
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
  "container_id": "tradingview_fast"
}
  );
  </script>
</div>
"""

# Streamlit-এ HTML উইজেট রেন্ডার করা
components.html(tv_widget, height=600)
