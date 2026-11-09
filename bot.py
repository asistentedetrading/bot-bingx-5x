import os, time, threading, requests
from flask import Flask

app = Flask(__name__)

# --- CONFIGURACION TU ESTRATEGIA ---
SYMBOL = "ETH"
LEVERAGE = 5
SL_PCT = 1.5
TP_PCT = 3.0
RSI_LONG = 33
RSI_SHORT = 67
VOL_MULTIPLIER = 1.08 # Si volumen actual es 8% más que promedio = ALTO
COOLDOWN_MIN = 15

headers = {"User-Agent": "Mozilla/5.0"}

# Estado que verás en el dashboard
state = {
    "price": "Iniciando...",
    "rsi": "...",
    "vol": "...",
    "signal": "Iniciando bot 5x...",
    "pos": "Sin posición",
    "last_trade": "Nunca"
}

last_trade_time = 0
in_position = False

def log(msg):
    print(f"[BOT] {msg}")

def get_price():
    """Precio real que SI funciona en Render USA"""
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd", headers=headers, timeout=15)
        price = float(r.json()["ethereum"]["usd"])
        log(f"Precio OK: {price}")
        return price
    except Exception as e:
        log(f"CoinGecko fallo {e}, probando OKX")
        try:
            r = requests.get("https://www.okx.com/api/v5/market/ticker?instId=ETH-USDT", headers=headers, timeout=10)
            price = float(r.json()["data"][0]["last"])
            log(f"OKX OK: {price}")
            return price
        except Exception as e2:
            log(f"Todo fallo: {e2}")
            return None

def get_history():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/coins/ethereum/market_chart?vs_currency=usd&days=1", headers=headers, timeout=15)
        data = r.json()
        closes = [x[1] for x in data["prices"]][-100:]
        vols = [x[1] for x in data["total_volumes"]][-100:]
        return closes, vols
    except Exception as e:
        log(f"Historial fallo {e}")
        return None, None

def calc_rsi(prices, period=14):
    try:
        gains = 0; losses = 0
        for i in range(1, period+1):
            diff = prices[-i] - prices[-i-1]
            if diff > 0: gains += diff
            else: losses += abs(diff)
        if losses == 0: return 70
        rs = (gains/period) / (losses/period)
        return 100 - (100 / (1 + rs))
    except:
        return 50

def trading_loop():
    global last_trade_time, in_position
    while True:
        try:
            price = get_price()
            closes, vols = get_history()
            if not price or not closes:
                state["signal"] = "Reconectando... esperando API"
                time.sleep(10)
                continue

            closes[-1] = price # usamos precio real actual
            rsi = calc_rsi(closes)
            v_now = vols[-1]
            v_avg = sum(vols[-20:]) / 20
            vol_alto = v_now > v_avg * VOL_MULTIPLIER

            # Guardar para dashboard
            state["price"] = f"${price:.2f}"
            state["rsi"] = f"{rsi:.1f}"
            state["vol"] = f"{'ALTO ✅ OPERA 5x' if vol_alto else 'BAJO ❌ NO OPERA'} ({v_now/1e9:.1f}B vs {v_avg/1e9:.1f}B)"

            # Lógica de cooldown
            can_trade = (time.time() - last_trade_time) > (COOLDOWN_MIN * 60)

            signal = "ESPERANDO - Vol bajo"
            if vol_alto and can_trade and not in_position:
                if rsi < RSI_LONG:
                    signal = f"LONG 5x ✅ RSI {rsi:.1f} + Vol ALTO -> COMPRAR"
                    # AQUÍ VA TU CODIGO DE BINGX: bingx.create_order(...)
                    state["pos"] = f"LONG 5x abierto en ${price:.2f} | SL {SL_PCT}% TP {TP_PCT}%"
                    state["last_trade"] = f"LONG en {price:.2f}"
                    last_trade_time = time.time()
                    in_position = True
                    log(">>> OPERACION LONG 5x EJECUTADA (simulada)")
                elif rsi > RSI_SHORT:
                    signal = f"SHORT 5x ✅ RSI {rsi:.1f} + Vol ALTO -> VENDER"
                    state["pos"] = f"SHORT 5x abierto en ${price:.2f} | SL {SL_PCT}% TP {TP_PCT}%"
                    state["last_trade"] = f"SHORT en {price:.2f}"
                    last_trade_time = time.time()
                    in_position = True
                    log(">>> OPERACION SHORT 5x EJECUTADA (simulada)")
            elif not vol_alto:
                signal = f"Vol BAJO - No se opera 5x (RSI {rsi:.1f})"
            elif not can_trade:
                signal = f"Cooldown {COOLDOWN_MIN}min - esperando..."
            elif in_position:
                signal = f"En posición - Gestionando SL {SL_PCT}% TP {TP_PCT}%"
                # Aquí simulo cierre después de un rato
                if time.time() - last_trade_time > 300: # 5 min simula cierre
                    in_position = False
                    state["pos"] = "Sin posición - esperando próxima"

            state["signal"] = signal
            log(f"{state['price']} | RSI {rsi:.1f} | {state['vol']} | {signal}")

        except Exception as e:
            log(f"Error loop: {e}")
            state["signal"] = f"Error: {e}"

        time.sleep(20)

threading.Thread(target=trading_loop, daemon=True).start()

@app.route("/")
def home():
    return '<meta http-equiv="refresh" content="0; url=/dashboard">'

@app.route("/dashboard")
def dashboard():
    return f"""
    <body style="background:#0f172a;color:white;font-family:Arial;padding:20px;max-width:800px;margin:auto">
        <h1 style="color:#22c55e">BOT BINGX 5x - TRABAJO BIEN</h1>
        <div style="background:#1e293b;padding:20px;border-radius:10px;margin-top:20px">
            <h1 style="font-size:55px;margin:0">{state['price']}</h1>
            <h3>RSI: {state['rsi']}</h3>
            <h3>Volumen: {state['vol']}</h3>
            <hr style="border-color:#334155">
            <h2 style="border:2px solid #22c55e;padding:15px;border-radius:8px">{state['signal']}</h2>
            <p><b>Posición:</b> {state['pos']}</p>
            <p><b>Último trade:</b> {state['last_trade']}</p>
            <p style="color:#94a3b8;font-size:12px">Estrategia: 40% RSI / 60% Volumen | SL {SL_PCT}% TP {TP_PCT}% | Solo 5x en Vol ALTO | No Binance</p>
        </div>
        <p>Actualiza solo - Render USA OK</p>
    </body>
    """

if __name__ == "__main__":
    app.run()
