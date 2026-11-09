import os, time, threading, requests
from flask import Flask

app = Flask(__name__)

state = {"price": "Iniciando...", "signal": "Iniciando..."}

def get_price():
    # API que NUNCA bloquea a USA
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd", timeout=15, headers={"User-Agent":"Mozilla/5.0"})
        print(f"COINGECKO DICE: {r.text}")
        return float(r.json()["ethereum"]["usd"])
    except Exception as e:
        print(f"Fallo CoinGecko {e}")
        try:
            r = requests.get("https://www.okx.com/api/v5/market/ticker?instId=ETH-USDT", timeout=10)
            return float(r.json()["data"][0]["last"])
        except:
            return None

def loop():
    while True:
        price = get_price()
        if price:
            state["price"] = f"${price:.2f}"
            state["signal"] = f"✅ BOT FUNCIONANDO - Precio real ${price:.2f}"
            print(f"ACTUALIZADO {price}")
        else:
            state["signal"] = "Reintentando..."
        time.sleep(15)

threading.Thread(target=loop, daemon=True).start()

@app.route("/")
def home():
    return '<meta http-equiv="refresh" content="0; url=/dashboard">'

@app.route("/dashboard")
def dashboard():
    return f"""
    <html><body style="background:#0f172a;color:white;font-family:sans-serif;padding:40px">
    <h1 style="font-size:60px;margin:0">{state['price']}</h1>
    <h1 style="border:4px solid #22c55e;padding:20px;color:#22c55e">{state['signal']}</h1>
    <p>Si ves $3578 y pico real, ya está resuelto. Sin Binance, sin Bybit.</p>
    <p>Render USA - CoinGecko + OKX</p>
    </body></html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
