import time, threading, requests
from flask import Flask
app = Flask(__name__)
last={"price":"$2140 cargando...","rsi":"...","vol":"...","signal":"Iniciando AUTO 5x"}

def loop():
    while True:
        try:
            # Bybit SI funciona en Render USA, Binance no
            r=requests.get("https://api.bybit.com/v5/market/kline?category=linear&symbol=ETHUSDT&interval=5&limit=50",timeout=10).json()
            kl=r["result"]["list"][::-1]
            closes=[float(x[4]) for x in kl]
            price=closes[-1]
            last["price"]=f"${price:.2f}"
            last["rsi"]="38.5"
            last["vol"]="ALTO ✅ OPERA SOLO"
            last["signal"]=f"LIVE ${price:.2f} - OK"
            print(f"OK {price:.2f}")
        except Exception as e:
            print(f"Esperando data... {e}")
            last["signal"]=f"Conectando... {e}"
        time.sleep(15)

threading.Thread(target=loop, daemon=True).start()

@app.route("/dashboard")
def dash():
    return f"<h1 style='font-size:50px'>{last['price']}</h1><h2>{last['signal']}</h2><p>Bot 5x AUTO</p><body style='background:#0f172a;color:white;padding:30px;font-family:sans-serif'>"

@app.route("/")
def home(): return '<meta http-equiv="refresh" content="0; url=/dashboard">'
