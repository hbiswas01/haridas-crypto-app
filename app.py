import streamlit as st
import ccxt

st.set_page_config(page_title="Haridas Crypto Setup", layout="wide")
st.title("🚀 Haridas Crypto Setup App")

# Binance-এর বদলে Bybit ব্যবহার করা হলো
exchange = ccxt.bybit() 

def get_price(symbol):
    try:
        ticker = exchange.fetch_ticker(symbol)
        return ticker['last']
    except Exception as e:
        # শুধু 'Error' না দেখিয়ে আসল সমস্যাটি স্ক্রিনে দেখাবে
        return f"Error: {e}" 

col1, col2 = st.columns(2)
with col1:
    st.subheader("Bitcoin (BTC/USDT)")
    st.metric(label="Live Price", value=f"${get_price('BTC/USDT')}")
with col2:
    st.subheader("Solana (SOL/USDT)")
    st.metric(label="Live Price", value=f"${get_price('SOL/USDT')}")
