import time, threading, requests
from flask import Flask
app = Flask(__name__)

last={"price":"$3578 cargando BYBIT...","rsi":"...","vol":"...","signal":"Conectando Bybit - NO Binance"}

def calc_rsi(p,per=14):
    try:
        g=l=0
        for i in range(1,per+1):
            d=p[-i]-p[-i-1]
            if d>0: g+=d
            else: l+=abs(d)
        if l==0: return 70
        return 100-(100/(1+(g/per)/(l/per)))
    except: return 50

def loop():
    while True:
        try:
            # BYBIT - SI funciona en Render USA
            url="https://api.bybit.com/v5/market/kline?category=linear&symbol=ETHUSDT&interval=5&limit=100"
            r=requests.get(url,timeout=10).json()
            klines=r["result"]["list"]
            klines=klines[::-1] # Bybit viene al revés
            closes=[float(k[4]) for k in klines]
            vols=[float(k[5]) for k in klines]
            price=closes[-1]
            rsi=calc_rsi(closes)
            vn=vols[-1]
            va=sum(vols[-20:])/20
            vol_alto=vn>va*1.15
            sig="NADA"
            if vol_alto and rsi<33: sig="LONG 5x ✅ OPERA SOLO"
            elif vol_alto and rsi>67: sig="SHORT 5x ✅ OPERA SOLO"
            else: sig="Esperando Vol ALTO"
            
            last["price"]=f"${price:.2f}"
            last["rsi"]=f"{rsi:.1f}"
            last["vol"]=f"{'ALTO ✅ OPERA' if vol_alto else 'BAJO - NO OPERA'}"
            last["signal"]=sig
            print(f"OK BYBIT {price:.2f} RSI {rsi:.1f} {sig}")
        except Exception as e:
            print(f"Error Bybit: {e}")
            last["signal"]=f"Reconectando Bybit... {e}"
        time.sleep(20)

threading.Thread(target=loop,daemon=True).start()

@app.route("/")
def home(): return '<meta http-equiv="refresh" content="0; url=/dashboard">'

@app.route("/dashboard")
def dash():
    return f"<body style='background:#0f172a;color:white;font-family:sans-serif;padding:30px'><h1 style='font-size:50px'>{last['price']}</h1><h2>RSI {last['rsi']}</h2><h2>Vol {last['vol']}</h2><h1 style='color:#22c55e;border:2px solid #22c55e;padding:15px'>{last['signal']}</h1><p>Bot 5x BYBIT - Funciona en Render USA - No Binance</p></body>"
