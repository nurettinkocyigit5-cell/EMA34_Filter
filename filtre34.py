import ccxt
import pandas as pd
import numpy as np

# OKX bağlantısı
exchange = ccxt.okx({
    'enableRateLimit': True,
})

TIMEFRAME = '1h'
EMA_PERIOD = 34
LIMIT = 100

def calculate_ema(series, period):
    return series.ewm(span=period, adjust=False).mean()

# USDT paritelerini al
markets = exchange.load_markets()
symbols = [
    s for s in markets
    if s.endswith('/USDT') and markets[s]['active']
]

filtered_coins = []

for symbol in symbols:
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

        # Kapanış > EMA34 koşulu
        if last_close > last_ema:
            filtered_coins.append({
                'symbol': symbol,
                'close': round(last_close, 4),
                'ema34': round(last_ema, 4)
            })

    except Exception:
        continue

# Sonuçlar
print("📊 1 Saatlik Grafikte Close > EMA34 Olan Coinler:\n")
for coin in filtered_coins:
    print(
        f"{coin['symbol']} | Close: {coin['close']} | EMA34: {coin['ema34']}"
    )
