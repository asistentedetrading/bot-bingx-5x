import time, hmac, hashlib, requests, pandas as pd, os
from datetime import datetime

API_KEY = os.getenv("API_KEY")
SECRET = os.getenv("SECRET")
SYMBOL = "ETH-USDT"
TIMEFRAME = "5m"
LEVERAGE = 5
QTY_USDT = 20
SL_PCT = 1.5
TP_PCT = 3.0
BASE_URL = "https://open-api.bingx.com"

def sign(p):
    q = "&".join([f"{k}={v}" for k,v in sorted(p.items())])
    return hmac.new(SECRET.encode(), q.encode(), hashlib.sha256).hexdigest()

def get_klines(limit=250):
    url = f"{BASE_URL}/openApi/swap/v3/quote/klines?symbol={SYMBOL}&interval={TIMEFRAME}&limit={limit}"
    r = requests.get(url).json()
    df = pd.DataFrame(r['data'], columns=['time','open','high','low','close','vol'])
    df['close'] = df['close'].astype(float)
    return df

def calc_signals(df):
    df['EMA200'] = df['close'].ewm(span=200).mean()
    delta = df['close'].diff()
    gain = delta.where(delta>0,0).rolling(14).mean()
    loss = -delta.where(delta<0,0).rolling(14).mean()
    rs = gain/loss
    df['RSI'] = 100 - (100/(1+rs))
    last = df.iloc[-1]
    if last['RSI'] < 35 and last['close'] > last['EMA200']: return "LONG", last['RSI'], last['close']
    if last['RSI'] > 65 and last['close'] < last['EMA200']: return "SHORT", last['RSI'], last['close']
    return "NADA", last['RSI'], last['close']

def open_order(side, price, rsi):
    side_order = "BUY" if side=="LONG" else "SELL"
    ts = int(time.time()*1000)
    sl = price*(1-SL_PCT/100) if side=="LONG" else price*(1+SL_PCT/100)
    tp = price*(1+TP_PCT/100) if side=="LONG" else price*(1-TP_PCT/100)
    params = {"symbol":SYMBOL,"side":side_order,"positionSide":side,"type":"MARKET","quantity":QTY_USDT,"takeProfit":f"{tp:.2f}","stopLoss":f"{sl:.2f}","timestamp":ts}
    params["signature"]=sign(params)
    r = requests.post(BASE_URL+"/openApi/swap/v2/trade/order", headers={"X-BX-APIKEY":API_KEY}, data=params)
    print(f"{side} {price} RSI:{rsi:.1f} -> {r.text}")

print(f"BOT INICIADO {SYMBOL} {TIMEFRAME} ${QTY_USDT} {LEVERAGE}x")
while True:
    try:
        df=get_klines()
        signal,rsi,price=calc_signals(df)
        print(f"{datetime.now().strftime('%H:%M:%S')} {price} RSI:{rsi:.1f} -> {signal}")
        if signal!="NADA":
            open_order(signal,price,rsi)
            time.sleep(300)
        time.sleep(20)
    except Exception as e:
        print(e)
        time.sleep(15)
