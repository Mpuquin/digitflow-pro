# DigitFlow Pro+ — Streamlit Web App (Prototype)
# Run this on Streamlit Cloud or local Streamlit and access from your phone browser

import streamlit as st
import pandas as pd
import websocket
import threading
import json
from collections import Counter
import time

# SETTINGS
SYMBOLS = ["R_10", "R_25", "R_50", "R_75", "R_100"]
TICK_HISTORY = 50
VALIDITY_TICKS = 7  # recommended signal validity ticks

st.set_page_config(page_title="DigitFlow Pro+", layout="wide")
st.title("📊 DigitFlow Pro+ — High-Probability Digit Signal Dashboard")

selected_symbol = st.selectbox("Select Volatility Index:", SYMBOLS)
placeholder = st.empty()

# Global tick storage
ticks_data = {symbol: [] for symbol in SYMBOLS}
signal_info = {symbol: {"digit": None, "valid_for": 0, "confidence": 0} for symbol in SYMBOLS}

# Analysis function
def analyze(symbol):
    ticks = ticks_data[symbol]
    if len(ticks) < TICK_HISTORY:
        return None
    counts = Counter(ticks)
    df = pd.DataFrame({
        "Digit": list(range(10)),
        "Count": [counts.get(i, 0) for i in range(10)]
    })
    df["Percent"] = df["Count"] / sum(counts.values()) * 100
    df = df.sort_values("Percent", ascending=False)
    hot_digit = df.iloc[0]["Digit"]
    confidence = df.iloc[0]["Percent"]
    validity_secs = VALIDITY_TICKS  # approx seconds
    signal_info[symbol] = {
        "digit": int(hot_digit),
        "valid_for": validity_secs,
        "confidence": min(95, round(confidence)),
    }
    return df

# WebSocket handling
def on_message(ws, message):
    msg = json.loads(message)
    if "tick" in msg:
        symbol = msg["tick"]["symbol"]
        digit = int(msg["tick"]["quote"][-1])
        ticks_data[symbol].append(digit)
        if len(ticks_data[symbol]) > TICK_HISTORY:
            ticks_data[symbol].pop(0)

# Subscribe to all symbols
def on_open(ws):
    for symbol in SYMBOLS:
        ws.send(json.dumps({"ticks": symbol, "subscribe": 1}))

# Run WebSocket client
def run_ws():
    ws = websocket.WebSocketApp(
        "wss://ws.binaryws.com/websockets/v3?app_id=1089",
        on_message=on_message,
        on_open=on_open
    )
    ws.run_forever()

threading.Thread(target=run_ws, daemon=True).start()

# Streamlit live update loop
while True:
    df = analyze(selected_symbol)
    if df is not None:
        with placeholder.container():
            st.subheader(f"Analysis for {selected_symbol}")
            st.dataframe(df.reset_index(drop=True), use_container_width=True)
            sig = signal_info[selected_symbol]
            st.markdown(f"✅ **Recommended Digit to Trade:** `{sig['digit']}`")
            st.markdown(f"⏳ **Signal Valid for Next:** `{sig['valid_for']} seconds`")
            st.markdown(f"⭐ **Confidence:** `{sig['confidence']}%`")
    time.sleep(1)
