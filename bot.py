import time, threading, requests
from flask import Flask
app = Flask(__name__)

# Inicializamos todo para que no de Error: 'price'
last={"price":"$2140 cargando...","rsi":"...","vol":"...","signal":"Iniciando AUTO 5x"}

def calc_rsi(prices, period=14):
    try:
        gains=losses=0
        for i in range(1, period+1):
            diff=prices[-i]-prices[-i-1]
            if diff>0: gains+=diff
            else: losses+=abs(diff)
        if losses==0: return 70.0
        rs=(gains/period)/(losses/period)
        return 100-(100/(1+rs))
    except:
        return 50.0

def bot_loop():
    while True:
        try:
            # Usamos Binance que si funciona
            url="https://api.binance.com/api/v3/klines?symbol=ETHUSDT&interval=5m&limit=50"
            data=requests.get(url, timeout=10).json()
            
            # Si Binance devuelve error, no es lista
            if not isinstance(data, list):
                print(f"Binance dice: {data}")
                time.sleep(10)
                continue
                
            closes=[float(k[4]) for k in data]
            vols=[float(k[5]) for k in data]
            price=closes[-1]
            rsi=calc_rsi(closes)
            v_now=vols[-1]
            v_avg=sum(vols[-20:])/20
            vol_alto=v_now>v_avg*1.15
            
            sig="NADA - Esperando"
            if vol_alto and rsi<33: sig="LONG 5x - OPERA SOLO"
            elif vol_alto and rsi>67: sig="SHORT 5x - OPERA SOLO"
            
            v_txt="ALTO ✅ OPERA SOLO" if vol_alto else "BAJO - No opera"
            
            last["price"]=f"${price:.2f}"
            last["rsi"]=f"{rsi:.1f}"
            last["vol"]=f"{v_now:.2f} vs {v_avg:.2f} = {v_txt}"
            last["signal"]=sig
            
            print(f"OK {price:.2f} RSI {rsi:.1f} {sig}")
            
        except Exception as e:
            print(f"Error en loop: {e}")
            # No borramos last, para que no de Error: 'price'
            last["signal"]=f"Error: {e}"
        time.sleep(20)

threading.Thread(target=bot_loop, daemon=True).start()

@app.route("/")
def home():
    return '<meta http-equiv="refresh" content="0; url=/dashboard">'

@app.route("/dashboard")
def dashboard():
    # Usamos .get para que NUNCA de Error: 'price'
    price=last.get("price","$2140")
    rsi=last.get("rsi","...")
    vol=last.get("vol","...")
    sig=last.get("signal","Iniciando")
    color="#22c55e" if "LONG" in sig else "#ef4444" if "SHORT" in sig else "white"
    return f"<body style='background:#0f172a;color:white;font-family:sans-serif;padding:30px'><h1 style='font-size:50px'>{price}</h1><h2>RSI: {rsi}</h2><h3>{vol}</h3><h1 style='color:{color};border:2px solid {color};padding:15px'>{sig}</h1><p>Bot 5x AUTO - Solo Vol ALTO</p></body>"
