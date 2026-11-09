import os, time, threading, requests
from flask import Flask
app = Flask(__name__)

last = {"price":"$2140 cargando...","rsi":"...","vol":"...","signal":"Iniciando bot..."}

def calc_rsi(prices, p=14):
    g=l=0
    for i in range(1,p+1):
        d=prices[-i]-prices[-i-1]
        if d>0: g+=d
        else: l+=abs(d)
    if l==0: return 70
    rs=(g/p)/(l/p) if l!=0 else 10
    return 100-(100/(1+rs))

def loop():
    while True:
        try:
            r=requests.get("https://api.binance.com/api/v3/klines?symbol=ETHUSDT&interval=5m&limit=100",timeout=10).json()
            closes=[float(x[4]) for x in r]
            vols=[float(x[5]) for x in r]
            price=closes[-1]
            rsi=calc_rsi(closes)
            v_now=vols[-1]
            v_avg=sum(vols[-20:])/20
            v_txt="ALTO ✅" if v_now>v_avg*1.15 else "BAJO ⚠️"
            sig="LONG" if rsi<33 and v_now>v_avg else "SHORT" if rsi>67 and v_now>v_avg else "NADA"
            last.update({"price":f"${price:.2f}","rsi":f"{rsi:.1f}","vol":f"{v_now:.2f} vs avg {v_avg:.2f} = {v_txt}","signal":f"{sig} - RSI {rsi:.1f}"})
            print(f"OK {price} {sig}")
        except Exception as e:
            print(e)
        time.sleep(20)

@app.route("/")
def home(): return '<meta http-equiv="refresh" content="0; url=/dashboard">'

@app.route("/dashboard")
def dash():
    d=last
    return f"<body style='background:#0f172a;color:#fff;font-family:sans-serif;padding:30px'><h1 style='font-size:50px'>{d['price']}</h1><h2>RSI: {d['rsi']}</h2><h2>Vol: {d['vol']}</h2><h1 style='color:#22c55e'>{d['signal']}</h1><p>ETH ahora ~ $2140 | Puerto OK | Bot Live en Render</p><p>Se actualiza solo cada 20s - recarga la pagina</p></body>"

threading.Thread(target=loop, daemon=True).start()
