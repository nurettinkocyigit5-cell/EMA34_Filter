import streamlit as st
import pandas as pd
import requests
from datetime import datetime

# --- Telegram bilgileri ---
TOKEN = "BOT_TOKEN"       # BotFather'dan aldığın token
CHAT_ID = "YOUR_CHAT_ID"  # Telegram chat ID

# --- Sayfa ayarları ---
st.set_page_config(page_title="EMA34 Yukarı Kıran Coinler", layout="wide")
st.title("EMA34 Yukarı Kıran Coinler (15dk Tarama) - OKX + Telegram")

# --- Telegram mesaj gönderme ---
def send_telegram(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message, "parse_mode": "Markdown"}
    requests.post(url, data=payload)

# --- OKX USDT coin listesi ---
@st.cache_data(ttl=900)
def get_okx_tickers():
    url = "https://www.okx.com/api/v5/market/tickers?instType=SPOT"
    data = requests.get(url).json()
    symbols = [item["instId"] for item in data["data"] if item["instId"].endswith("-USDT")]
    return symbols

# --- Kline verisi ---
@st.cache_data(ttl=900)
def get_klines(symbol, interval="1H", limit=50):
    url = f"https://www.okx.com/api/v5/market/candles?instId={symbol}&bar={interval}&limit={limit}"
    data = requests.get(url).json()
    df = pd.DataFrame(data["data"])
    df = df[[0,4]]  # timestamp, close
    df.columns = ["timestamp","close"]
    df["close"] = df["close"].astype(float)
    return df

# --- EMA34 hesaplama ---
def calculate_ema34(df):
    df["EMA34"] = df["close"].ewm(span=34, adjust=False).mean()
    return df

# --- EMA34'ü yukarı kıran coinleri filtrele ---
def filter_coins(symbols):
    results = []
    for sym in symbols:
        df = calculate_ema34(get_klines(sym))
        if df["close"].iloc[-1] > df["EMA34"].iloc[-1] and df["close"].iloc[-2] <= df["EMA34"].iloc[-2]:
            results.append(f"{sym}: {df['close'].iloc[-1]:.2f} USDT")
    return results

# --- 15 dakikada bir sayfa yenileme ---
st_autorefresh_interval = 15 * 60 * 1000  # 15 dakika
st.experimental_set_query_params(reload=int(datetime.now().timestamp()))
st.experimental_rerun()

# --- Ana işlem ---
symbols = get_okx_tickers()
filtered = filter_coins(symbols)

# --- Webde göster ---
st.subheader(f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - EMA34'ü yukarı kıran coinler")
if filtered:
    st.dataframe(pd.DataFrame(filtered, columns=["Coin ve Fiyat"]))
else:
    st.write("Şu anda EMA34'ü yukarı kıran coin yok.")

# --- Telegram mesaj gönder ---
if filtered:
    message = "*EMA34'ü yukarı kıran coinler:*\n" + "\n".join(filtered)
    send_telegram(message)
