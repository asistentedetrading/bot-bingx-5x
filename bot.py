import os, time, threading, requests
from flask import Flask

app = Flask(__name__)

state = {"price": "Buscando ETH real...", "signal": "Conectando..."}

def precio_real_eth():
    # Sin disparates, precio real
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd", headers={"User-Agent":"Mozilla/5.0"}, timeout=20)
        print(f"PRECIO REAL: {r.text}", flush=True)
        price = float(r.json()["ethereum"]["usd"])
        return price
    except Exception as e:
        print(f"Error: {e}", flush=True)
        return None

def loop():
    while True:
        p = precio_real_eth()
        if p:
            state["price"] = f"${p:.2f}"
            state["signal"] = f"✅ PRECIO REAL - ETH ${p:.2f} - Ya no más disparate de $3579"
            print(f"ETH REAL {p}", flush=True)
        else:
            state["signal"] = "Reintentando precio real..."
        time.sleep(15)

threading.Thread(target=loop, daemon=True).start()

@app.route("/")
def home():
    return '<meta http-equiv="refresh" content="0; url=/dashboard">'

@app.route("/dashboard")
def dashboard():
    return f"<body style='background:#0f172a;color:white;font-family:sans-serif;padding:40px'><h1 style='font-size:70px'>{state['price']}</h1><h1 style='border:5px solid #22c55e;padding:20px;color:#22c55e'>{state['signal']}</h1><p>ETH ahora mismo $2132 - Sin disparates de $3579</p></body>"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
    
