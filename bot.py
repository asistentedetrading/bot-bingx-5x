import requests, time, threading
from flask import Flask
app = Flask(__name__)
last={"price":"$2140 cargando...","rsi":"...","vol":"...","signal":"Iniciando..."}

def calc_rsi(p,per=14):
    g=l=0
    for i in range(1,per+1):
        d=p[-i]-p[-i-1]
        if d>0: g+=d
        else: l+=abs(d)
    if l==0: return 70
    return 100-(100/(1+(g/per)/(l/per)))

def loop():
    while True:
        try:
            r=requests.get("https://api.binance.com/api/v3/klines?symbol=ETHUSDT&interval=5m&limit=100",timeout=10).json()
            c=[float(x[4]) for x in r]; v=[float(x[5]) for x in r]
            price=c[-1]; rsi=calc_rsi(c)
            vn=v[-1]; va=sum(v[-20:])/20
            vt="ALTO ✅" if vn>va*1.15 else "BAJO ⚠️"
            sig="LONG" if rsi<33 and vn>va else "SHORT" if rsi>67 and vn>va else "NADA"
            last.update({"price":f"${price:.2f}","rsi":f"{rsi:.1f}","vol":f"{vn:.2f} vs {va:.2f} = {vt}","signal":sig})
            print(f"OK {price:.2f} {sig}")
        except Exception as e: print(e)
        time.sleep(20)

@app.route("/")
def home(): return '<meta http-equiv="refresh" content="0; url=/dashboard">'

@app.route("/dashboard")
def dash():
    d=last
    return f"<body style='background:#0f172a;color:white;font-family:sans-serif;padding:30px'><h1 style='font-size:55px'>{d['price']}</h1><h2>RSI: {d['rsi']}</h2><h2>Vol: {d['vol']}</h2><h1 style='color:#22c55e'>{d['signal']}</h1><p>ETH Live ~ $2140 | Bot en Render OK</p></body>"

threading.Thread(target=loop,daemon=True).start()
