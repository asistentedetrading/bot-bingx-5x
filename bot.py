from flask import Flask
import requests, time, threading

app = Flask(__name__)

SYMBOL = "ETH-USDT"
last_data = {"price":"Cargando...","rsi":"...","vol_now":"...","vol_avg":"...","vol_status":"Cargando...","signal":"Cargando...","time":"..."}

def calc_rsi(prices, period=14):
    try:
        gains = []
        losses = []
        for i in range(1, len(prices)):
            diff = prices[i] - prices[i-1]
            if diff >= 0:
                gains.append(diff)
                losses.append(0)
            else:
                gains.append(0)
                losses.append(abs(diff))
        avg_gain = sum(gains[-period:]) / period
        avg_loss = sum(losses[-period:]) / period
        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    except:
        return 50

def get_data():
    global last_data
    while True:
        try:
            url = f"https://open-api.bingx.com/openApi/swap/v2/quote/klines?symbol={SYMBOL}&interval=5m&limit=100"
            r = requests.get(url, timeout=10).json()
            data = r.get('data', [])
            if isinstance(data, dict):
                data = data.get('data', [])
            
            closes = []
            vols = []
            for x in data:
                if isinstance(x, dict):
                    closes.append(float(x.get('close',0)))
                    vols.append(float(x.get('volume',0)))
                else: # lista
                    closes.append(float(x[4]))
                    vols.append(float(x[5]))

            price = closes[-1]
            rsi = calc_rsi(closes)
            vol_now = vols[-1]
            vol_avg = sum(vols[-20:]) / 20
            vol_status = "ALTO ✅" if vol_now > vol_avg*1.2 else "BAJO ⚠️"
            
            signal = f"RSI {rsi:.1f}"
            if rsi < 30 and vol_now > vol_avg:
                signal = f"LONG - RSI {rsi:.1f} + Vol ALTO"
            elif rsi > 70 and vol_now > vol_avg:
                signal = f"SHORT - RSI {rsi:.1f} + Vol ALTO"
            else:
                signal = f"ESPERA - RSI {rsi:.1f} Vol {vol_status}"

            last_data = {
                "price": f"${price:.2f}",
                "rsi": f"{rsi:.1f}",
                "vol_now": f"{vol_now:.2f}",
                "vol_avg": f"{vol_avg:.2f}",
                "vol_status": vol_status,
                "signal": signal,
                "time": time.strftime("%H:%M:%S")
            }
            print(f"{price} {signal}")
        except Exception as e:
            print(f"Error: {e}")
            last_data["signal"] = f"Error: {e}"
        time.sleep(20)

@app.route("/")
def home():
    return f"<a href='/dashboard'>Ir a Dashboard Volumen</a> - Bot {SYMBOL} activo"

@app.route("/dashboard")
def dashboard():
    d = last_data
    return f"""
    <html><head><meta name='viewport' content='width=device-width'><meta http-equiv='refresh' content='20'>
    <style>body{{font-family:sans-serif;background:#0f1115;color:#fff;padding:20px}} .card{{background:#1a1d24;padding:20px;border-radius:15px}} h2{{color:#00ff88}}</style>
    </head><body>
    <h1>📊 {SYMBOL} - Volumen Dashboard</h1>
    <div class="card">
    <h2>{d['price']}</h2>
    <p><b>RSI:</b> {d['rsi']}</p>
    <p><b>Volumen Ahora:</b> {d['vol_now']}</p>
    <p><b>Volumen Promedio 20 velas:</b> {d['vol_avg']}</p>
    <p><b>Estado Volumen:</b> {d['vol_status']}</p>
    <hr>
    <h3>Señal: {d['signal']}</h3>
    <p>Actualizado: {d['time']} - Se recarga cada 20s</p>
    </div>
    <p>✅ Solo entra si dice ALTO</p>
    </body></html>
    """

threading.Thread(target=get_data, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
