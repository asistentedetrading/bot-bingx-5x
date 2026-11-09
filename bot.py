from flask import Flask
import os, requests, time, threading
app = Flask(__name__)
last = {"p": "Cargando $2140..."}

def loop():
    while True:
        try:
            r = requests.get("https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT", timeout=10).json()
            last["p"] = f"${float(r['price']):.2f}"
            print(f"PRECIO OK: {last['p']}")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(15)

threading.Thread(target=loop, daemon=True).start()

@app.route("/")
def home(): return f"BOT ETH {last['p']} - PUERTO OK"
@app.route("/dashboard")
def dash(): return f"<h1 style='color:green'>{last['p']} PUERTO ABIERTO OK</h1><h2>Si ves esto ya no hay Timed Out</h2>"
