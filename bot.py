from flask import Flask
import os, time, threading, requests
import pandas as pd

app = Flask(__name__)

SYMBOL = "ETH-USDT"
last_data = {"price": 0, "rsi": 0, "vol_now": 0, "vol_avg": 0, "vol_status": "Cargando...", "signal": "Cargando...", "time": "...", "error": ""}

def get_data():
    try:
        # Endpoint corregido v2
        url = f"https://open-api.bingx.com/openApi/swap/v2/quote/klines?symbol={SYMBOL}&interval=5m&limit=100"
        resp = requests.get(url, timeout=10).json()
        # print(resp) para debug
        if 'data' not in resp:
            last_data["error"] = f"API error: {str(resp)[:200]}"
            return
        
        data = resp['data']
        # BingX v2 devuelve lista directa
        if isinstance(data, dict) and 'data' in data:
            data = data['data']
        
        closes = [float(x[4]) if isinstance(x, list) else float(x['close']) for x in data]
        vols = [float(x[5]) if isinstance(x, list) else float(x['volume']) for x in data]
        
        import ta
        df = pd.DataFrame({'close': closes})
        rsi = ta.momentum.RSIIndicator(df['close'], 14).rsi().iloc[-1]
        
        vol_now = vols[-1]
        vol_avg = sum(vols[-20:]) / 20
        vol_status = "ALTO ✅" if vol_now > vol_avg*1.2 else "BAJO ⚠️"
        
        price = closes[-1]
        
        signal = "Esperando"
        if rsi < 30 and vol_now > vol_avg:
            signal = f"LONG - RSI {rsi:.1f} + Vol ALTO"
        elif rsi > 70 and vol_now > vol_avg:
            signal = f"SHORT - RSI {rsi:.1f} + Vol ALTO"
        else:
            signal = f"NADA - RSI {rsi:.1f} Vol {vol_status}"

        last_data.update({
            "price": price, "rsi": round(rsi,2),
            "vol_now": round(vol_now,4), "vol_avg": round(vol_avg,4),
            "vol_status": vol_status, "signal": signal,
            "time": time.strftime("%H:%M:%S"),
            "error": ""
        })
    except Exception as e:
        last_data["error"] = str(e)
        print(f"Error: {e}")

def bot_loop():
    while True:
        get_data()
        time.sleep(20)

@app.route("/")
def home():
    return f"Bot activo - <a href='/dashboard'>Ir a Dashboard Volumen</a>"

@app.route("/dashboard")
def dashboard():
    d = last_data
    return f"""
    <html><head><meta name='viewport' content='width=device-width'><meta http-equiv='refresh' content='20'></head>
    <body style="font-family:sans-serif; background:#0f1115; color:#fff; padding:20px">
    <h1>📊 ETH Bot 5x - Volumen</h1>
    <div style="background:#1a1d24; padding:20px; border-radius:12px">
    <h2>${d['price']}</h2>
    <p><b>RSI:</b> {d['rsi']}</p>
    <p><b>Volumen Ahora:</b> {d['vol_now']}</p>
    <p><b>Promedio 20:</b> {d['vol_avg']}</p>
    <p><b>Estado Volumen:</b> {d['vol_status']}</p>
    <hr>
    <h3>Señal: {d['signal']}</h3>
    <p>Actualizado: {d['time']}</p>
    <p style="color:orange">Debug: {d['error']}</p>
    </div>
    </body></html>
    """

threading.Thread(target=bot_loop, daemon=True).start()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
