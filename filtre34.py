import streamlit as st
import pandas as pd
import requests

# --- Sayfa ayarları ---
st.set_page_config(page_title="EMA34 Yukarı Kıran Coinler", layout="wide")
st.title("EMA34 Yukarı Kıran Coinler (1 Saatlik) - OKX")

# --- OKX spot USDT paritelerini çek ---
@st.cache_data(ttl=60)
def get_okx_tickers():
    url = "https://www.okx.com/api/v5/market/tickers?instType=SPOT"
    data = requests.get(url).json()
    symbols = [item["instId"] for item in data["data"] if item["instId"].endswith("-USDT")]
    return symbols

# --- 1 saatlik kline verisi çek ---
@st.cache_data(ttl=60)
def get_klines(symbol, interval="1H", limit=50):
    url = f"https://www.okx.com/api/v5/market/candles?instId={symbol}&bar={interval}&limit={limit}"
    data = requests.get(url).json()
    
    # Sadece timestamp ve close al
    df = pd.DataFrame(data["data"])
    df = df[[0, 4]]  # 0->timestamp, 4->close
    df.columns = ["timestamp", "close"]
    df["close"] = df["close"].astype(float)
    return df

# --- EMA34 hesapla ---
def calculate_ema34(df):
    df["EMA34"] = df["close"].ewm(span=34, adjust=False).mean()
    return df

# --- EMA34'ü yukarı kıran coinleri filtrele ---
def filter_coins(symbols):
    results = []
    for sym in symbols:
        df = get_klines(sym)
        df = calculate_ema34(df)
        # EMA34'ü yukarı kırma koşulu
        if df["close"].iloc[-1] > df["EMA34"].iloc[-1] and df["close"].iloc[-2] <= df["EMA34"].iloc[-2]:
            results.append({
                "Coin": sym,
                "Fiyat": df["close"].iloc[-1],
                "EMA34": df["EMA34"].iloc[-1]
            })
    return pd.DataFrame(results)

# --- Ana işlem ---
symbols = get_okx_tickers()
st.info(f"Toplam {len(symbols)} coin kontrol ediliyor... Bu işlem birkaç saniye sürebilir.")

df_filtered = filter_coins(symbols)

if not df_filtered.empty:
    st.success(f"{len(df_filtered)} coin EMA34'ü yukarı kırdı!")
    st.dataframe(df_filtered.sort_values(by="Fiyat", ascending=False))
else:
    st.warning("Şu anda EMA34'ü yukarı kıran coin yok.")
