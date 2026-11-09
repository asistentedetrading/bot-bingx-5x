from flask import Flask
import requests, time, threading

app = Flask(__name__)

SYMBOL = "ETH-USDT"
last_data = {"price":"Cargando...","rsi":"...","vol_now":"...","vol_avg":"...","vol_status":"...","signal":"Iniciando..."}

def calc_rsi(prices, p=14):
    try:
        if len(prices) < p+1: return 50
        g=l=0
        for i in range(1,p+1):
            d=prices[-i]-prices[-i-1]
            if d>0: g+=d
            else: l+=abs(d)
        if l==0: return 70
        rs=(g/p)/(l/p)
        return 100-(100/(1+rs))
    except: return 50

def get_klines():
    # 1. BingX V3 - es el que te da el precio real de BingX que ves en $2131
    try:
        url = f"https://open-api.bingx.com/openApi/swap/v3/quote/klines?symbol={SYMBOL}&interval=5m&limit=100"
        r = requests.get(url, timeout=10).json()
        data = r.get('data', [])
        if data and isinstance(data[0], dict):
            closes = [float(x['close']) for x in data]
            vols = [float(x['volume']) for x in data]
            if closes[0] > 1000 and closes[0] < 5000: # valida que sea ETH real
                return closes, vols
    except Exception as e:
        print(f"BingX V3 error: {e}")

    # 2. Fallback Binance si BingX falla
    try:
        url = "https://api.binance.com/api/v3/klines?symbol=ETHUSDT&interval=5m&limit=100"
        data = requests.get(url, timeout=10).json()
        closes = [float(x[4]) for x in data]
        vols = [float(x[5]) for x in data]
        return closes, vols
    except Exception as e:
        print(f"Binance error: {e}")
        raise

def loop():
    global last_data
    print(f"BOT {SYMBOL} INICIADO - precio real ~2131")
    while True:
        try:
            closes, vols = get_klines()
            price = closes[-1]
            rsi = calc_rsi(closes)
            vol_now = vols[-1]
            vol_avg = sum(vols[-20:])/20
            vol_status = "ALTO ✅ ENTRA" if vol_now > vol_avg*1.15 else "BAJO ⚠️ ESPERA"
            
            if rsi < 33 and vol_now > vol_avg: signal = f"LONG RSI {rsi:.1f} Vol ALTO"
            elif rsi > 67 and vol_now > vol_avg: signal = f"SHORT RSI {rsi:.1f} Vol ALTO"
            else: signal = f"NADA RSI {rsi:.1f} Vol {vol_status}"

            last_data = {"price":f"${price:.2f}","rsi":f"{rsi:.1f}","vol_now":f"{vol_now:.2f}","vol_avg":f"{vol_avg:.2f}","vol_status":vol_status,"signal":signal,"time":time.strftime("%H:%M:%S")}
            print(f"{last_data['time']} {price} {signal}")
        except Exception as e:
            print(f"Error loop: {e}")
            time.sleep(5)
        time.sleep(20)

@app.route("/")
def home(): return '<a href="/dashboard">VER DASHBOARD VOLUMEN - Precio Real 2131</a>'

@app.route("/dashboard")
def dashboard():
    d=last_data
    c="#00ff88" if "ALTO" in d['vol_status'] else "#ffaa00"
    return f"""
    <html><head><meta name='viewport' content='width=device-width'><meta http-equiv='refresh' content='15'></head>
    <body style="font-family:sans-serif;background:#0f1115;color:#fff;padding:20px">
    <h1>📊 ETH-USDT - Precio Real BingX</h1>
    <div style="background:#1a1d24;padding:20px;border-radius:16px">
    <h1 style="color:{c};font-size:42px">{d['price']}</h1>
    <p>Debe decir ~$2131 como ves en BingX</p>
    <p>RSI: <b>{d['rsi']}</b></p>
    <p>Vol Ahora: <b>{d['vol_now']}</b></p>
    <p>Vol Prom 20: <b>{d['vol_avg']}</b></p>
    <p>Estado: <b style="color:{c}">{d['vol_status']}</b></p>
    <hr><h2>{d['signal']}</h2><p>{d['time']}</p></div></body></html>
    """

threading.Thread(target=loop, daemon=True).start()
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
