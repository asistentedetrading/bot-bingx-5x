import os, time, threading, requests
from flask import Flask

app = Flask(__name__)

# Lo que ves en tu dashboard
estado = {
    "price": "$3578 cargando...",
    "signal": "Conectando CoinGecko (100% seguro)..."
}

def precio_real():
    # Este endpoint es el más simple del mundo y NUNCA lo bloquea USA
    url = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd"
    r = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    print(f"RESPUESTA COINGECKO: {r.text}")
    data = r.json()
    return float(data["ethereum"]["usd"])

def loop():
    while True:
        try:
            p = precio_real()
            estado["price"] = f"${p:.2f}"
            estado["signal"] = f"✅ COÑO POR FIN FUNCIONA - ${p:.2f} - Precio real CoinGecko"
            print(f"FUNCIONA! {p}")
        except Exception as e:
            print(f"Error: {e}")
            estado["signal"] = f"Reintentando... {e}"
        time.sleep(15)

threading.Thread(target=loop, daemon=True).start()

@app.route("/")
def home():
    return '<meta http-equiv="refresh" content="0; url=/dashboard">'

@app.route("/dashboard")
def dashboard():
    return f"""
    <html><body style="background:#0f172a;color:white;font-family:sans-serif;padding:40px;text-align:center">
    <h1 style="font-size:70px">{estado['price']}</h1>
    <h1 style="border:5px solid #22c55e;padding:25px;color:#22c55e;border-radius:15px">{estado['signal']}</h1>
    <p>Si ves esto en verde, ya resolvimos lo de las 3pm</p>
    </body></html>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
