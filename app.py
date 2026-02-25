import streamlit as st
import ccxt

st.set_page_config(page_title="Haridas Crypto Setup", layout="wide")
st.title("🚀 Haridas Crypto Setup App")

exchange = ccxt.kraken()

def get_price(symbol):
    try:
        ticker = exchange.fetch_ticker(symbol)
        return ticker['last']
    except Exception as e:
        return None

# রিফ্রেশ বাটন তৈরি
st.write("---")
if st.button("🔄 Refresh Prices"):
    st.rerun()
st.write("---")

col1, col2 = st.columns(2)

btc_price = get_price('BTC/USDT')
sol_price = get_price('SOL/USDT')

with col1:
    st.subheader("Bitcoin (BTC/USDT)")
    if btc_price:
        st.metric(label="Live Price", value=f"${btc_price}")
    else:
        st.error("ডেটা লোড হতে সমস্যা হচ্ছে!")

with col2:
    st.subheader("Solana (SOL/USDT)")
    if sol_price:
        st.metric(label="Live Price", value=f"${sol_price}")
    else:
        st.error("ডেটা লোড হতে সমস্যা হচ্ছে!")
