import streamlit as st
import ccxt
import pandas as pd

# Sayfa ayarları
st.set_page_config(
    page_title="OKX EMA34 Scanner",
    layout="wide"
)

st.title("📈 OKX EMA34 Üzeri Kapanış Tarayıcı")
st.caption("1 saatlik grafikte kapanışı EMA34 üzerinde olan coinler")

TIMEFRAME = "1h"
EMA_PERIOD = 34
LIMIT = 100

@st.cache_data(ttl=300)
def get_symbols():
    exchange = ccxt.okx({'enableRateLimit': True})
    markets = exchange.load_markets()
    return [
        s for s in markets
        if s.endswith('/USDT') and markets[s]['active']
    ]

def calculate_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

def scan_market():
    exchange = ccxt.okx({'enableRateLimit': True})
    rows = []

    for symbol in get_symbols():
        try:
            ohlcv = exchange.fetch_ohlcv(
                symbol,
                timeframe=TIMEFRAME,
                limit=LIMIT
            )

            df = pd.DataFrame(
                ohlcv,
                columns=['time','open','high','low','close','volume']
            )

            df['ema34'] = calculate_ema(df['close'], EMA_PERIOD)

            last_close = df['close'].iloc[-1]
            last_ema = df['ema34'].iloc[-1]

            if last_close > last_ema:
                rows.append({
                    "Coin": symbol,
                    "Close": round(last_close, 4),
                    "EMA34": round(last_ema, 4),
                    "Fark %": round((last_close - last_ema) / last_ema * 100, 2)
                })

        except:
            continue

    return pd.DataFrame(rows)

# 🔘 TARAMAYI BAŞLAT BUTONU
if st.button("🚀 Taramayı Başlat"):
    with st.spinner("OKX verileri taranıyor..."):
        result = scan_market()

    if result.empty:
        st.warning("Kriterlere uyan coin bulunamadı.")
    else:
        st.success(f"{len(result)} coin bulundu")
        st.dataframe(
            result.sort_values("Fark %", ascending=False),
            use_container_width=True
        )

st.markdown("---")
st.caption("⚠️ Yatırım tavsiyesi değildir. Teknik analiz filtreleme aracıdır.")
