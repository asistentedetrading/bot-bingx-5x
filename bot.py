from flask import Flask
import requests, time, threading

app = Flask(__name__)

SYMBOL = "ETH-USDT"
last_data = {"price":"Cargando...","rsi":"...","vol_now":"...","vol_avg":"...","vol_status":"Cargando...","signal":"Iniciando...","time":"..."}

def calc_rsi(prices, period=14):
    if len(prices) < period+1:
        return 50
    gains = 0
    losses = 0
    for i in range(1, period+1):
        diff = prices[-i] - prices[-i-1]
        if diff > 0:
            gains += diff
        else:
            losses += abs(diff)
    if losses == 0:
        return 70
    rs = (gains/period) / (losses/period)
    return 100 - (100/(1+rs))

def get_klines():
    # Intenta V3 primero (el bueno)
    try:
        url = f"https://open-api.bingx.com/openApi/swap/v3/quote/klines?symbol={SYMBOL}&interval=5m&limit=100"
        r = requests.get(url, timeout=10).json()
        data = r.get('data', [])
        if data and isinstance(data[0], dict) and 'close' in data[0]:
            closes = [float(x['close']) for x in data]
            vols = [float(x['volume']) for x in data]
            return closes, vols
    except Exception as e:
        print(f"V3 fallo: {e}")
    
    # Si V3 falla, intenta V2
    try:
        url2 = f"https://open-api.bingx.com/openApi/swap/v2/quote/klines?symbol={SYMBOL}&interval=5m&limit=100"
        r2 = requests.get(url2, timeout=10).json()
        data2 = r2.get('data', [])
        if isinstance(data2, dict):
            data2 = data2.get('data', [])
        closes = [float(x[4]) for x in data2]
        vols = [float(x[5]) for x in data2]
        return closes, vols
    except Exception as e:
        print(f"V2 fallo: {e}")
        raise

def bot_loop():
    global last_data
    print(f"BOT INICIADO {SYMBOL} 5m $20 5x")
    while True:
        try:
            closes, vols = get_klines()
            price = closes[-1]
            rsi = calc_rsi(closes)
            vol_now = vols[-1]
            vol_avg = sum(vols[-20:]) / 20
            vol_status = "ALTO ✅" if vol_now > vol_avg*1.2 else "BAJO ⚠️"
            
            if rsi < 32 and vol_now > vol_avg:
                signal = f"LONG RSI:{rsi:.1f} Vol:{vol_status}"
            elif rsi > 68 and vol_now > vol_avg:
                signal = f"SHORT RSI:{rsi:.1f} Vol:{vol_status}"
            else:
                signal = f"NADA - RSI:{rsi:.1f} Vol:{vol_status}"

            last_data = {
                "price": f"${price:.2f}",
                "rsi": f"{rsi:.1f}",
                "vol_now": f"{vol_now:.4f}",
                "vol_avg": f"{vol_avg:.4f}",
                "vol_status": vol_status,
                "signal": signal,
                "time": time.strftime("%H:%M:%S")
            }
            print(f"{time.strftime('%H:%M:%S')} {price} {signal}")
            
        except Exception as e:
            print(f"Error bot: {e}")
            last_data["signal"] = f"Error: {e}"
        time.sleep(20)

@app.route("/")
def home():
    return f'<h1>Bot {SYMBOL} activo</h1><a href="/dashboard">Ver Dashboard Volumen</a>'

@app.route("/dashboard")
def dashboard():
    d = last_data
    return f"""
    <html><head><meta name='viewport' content='width=device-width, initial-scale=1'><meta http-equiv='refresh' content='15'>
    <style>body{{font-family:sans-serif;background:#0f1115;color:white;padding:20px}} .card{{background:#1a1d24;padding:20px;border-radius:16px;}} .price{{font-size:32px;color:#00ff88}} .alto{{color:#00ff88}} .bajo{{color:#ffaa00}}</style>
    </head><body>
    <h1>📊 {SYMBOL} - Volumen Real</h1>
    <div class="card">
    <div class="price">{d['price']}</div>
    <p><b>RSI (14):</b> {d['rsi']}</p>
    <p><b>Volumen Ahora:</b> {d['vol_now']}</p>
    <p><b>Volumen Promedio 20 velas:</b> {d['vol_avg']}</p>
    <p><b>Estado Volumen:</b> <span class='{"alto" if "ALTO" in d['vol_status'] else "bajo"}'>{d['vol_status']}</span></p>
    <hr>
    <h2>Señal: {d['signal']}</h2>
    <p>Actualizado: {d['time']}</p>
    <p>✅ Solo entra si Volumen ALTO</p>
    </div>
    </body></html>
    """

threading.Thread(target=bot_loop, daemon=True).start()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
