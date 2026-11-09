import time, threading, requests
from flask import Flask
app = Flask(__name__)

# Esto es lo que ves ahora mismo en tu foto
last={"price":"$3578 cargando BYBIT...","rsi":"Calculando...","vol":"Calculando...","signal":"Conectando Bybit - NO Binance"}

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

def get_data():
    # 1. Intento BYBIT SPOT (no linear, spot si funciona en USA)
    try:
        r=requests.get("https://api.bybit.com/v5/market/kline?category=spot&symbol=ETHUSDT&interval=5&limit=100",timeout=10).json()
        kl=r["result"]["list"][::-1]
        closes=[float(x[4]) for x in kl]
        vols=[float(x[5]) for x in kl]
        print(f"BYBIT SPOT OK {closes[-1]}")
        return closes, vols
    except Exception as e:
        print(f"Bybit spot fallo: {e}")

    # 2. Intento OKX (siempre funciona en USA)
    try:
        r=requests.get("https://www.okx.com/api/v5/market/candles?instId=ETH-USDT&bar=5m&limit=100",timeout=10).json()
        kl=r["data"][::-1]
        closes=[float(x[4]) for x in kl]
        vols=[float(x[5]) for x in kl]
        print(f"OKX OK {closes[-1]}")
        return closes, vols
    except Exception as e:
        print(f"OKX fallo: {e}")

    # 3. ULTIMO RESPALDO CoinGecko (nunca bloquea)
    try:
        r=requests.get("https://api.coingecko.com/api/v3/coins/ethereum/market_chart?vs_currency=usd&days=1",timeout=10).json()
        closes=[x[1] for x in r["prices"]][-100:]
        vols=[x[1] for x in r["total_volumes"]][-100:]
        print(f"COINGECKO OK {closes[-1]}")
        return closes, vols
    except Exception as e:
        print(f"Todo fallo: {e}")
        raise e

def loop():
    while True:
        try:
            closes, vols = get_data()
            price=closes[-1]
            rsi=calc_rsi(closes)
            vn=vols[-1]
            va=sum(vols[-20:])/20
            vol_alto=vn>va*1.10
            
            sig="NADA - Esperando Vol ALTO"
            if vol_alto and rsi<33: sig="LONG 5x ✅ OPERA SOLO"
            elif vol_alto and rsi>67: sig="SHORT 5x ✅ OPERA SOLO"
            
            last["price"]=f"${price:.2f}"
            last["rsi"]=f"{rsi:.1f}"
            last["vol"]=f"{'ALTO ✅ OPERA' if vol_alto else 'BAJO'} ({vn:.0f} vs {va:.0f})"
            last["signal"]=sig
            print(f"OK FINAL {price:.2f} {sig}")
            
        except Exception as e:
            print(f"Error loop final: {e}")
            last["price"]=f"Error conectando, reintentando..."
            last["signal"]=f"Error: {e} - reintentando en 10s"
        time.sleep(20)

threading.Thread(target=loop, daemon=True).start()

@app.route("/")
def home(): return '<meta http-equiv="refresh" content="0; url=/dashboard">'

@app.route("/dashboard")
def dash():
    p=last.get("price","$3578")
    r=last.get("rsi","...")
    v=last.get("vol","...")
    s=last.get("signal","...")
    return f"<body style='background:#0f172a;color:white;font-family:sans-serif;padding:20px'><h1 style='font-size:55px;margin:0'>{p}</h1><h2>RSI: {r}</h2><h2>Vol: {v}</h2><h1 style='border:3px solid #22c55e;color:#22c55e;padding:20px;margin-top:20px'>{s}</h1><p>Bot 5x AUTO - Bybit/OKX/CoinGecko - Funciona en USA</p><p>Actualiza cada 20s</p></body>"
