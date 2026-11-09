import os, time, threading, requests, hmac, hashlib
from flask import Flask
app = Flask(__name__)

last={"price":"Iniciando...","rsi":"...","vol":"...","signal":"Conectando BingX 5x"}

KEY=os.getenv("BINGX_API_KEY","")
SECRET=os.getenv("BINGX_SECRET","")

def calc_rsi(p,per=14):
    g=l=0
    for i in range(1,per+1):
        d=p[-i]-p[-i-1]
        if d>0: g+=d
        else: l+=abs(d)
    if l==0: return 70
    return 100-(100/(1+(g/per)/(l/per)))

def bingx_sign(params):
    query = "&".join([f"{k}={v}" for k,v in sorted(params.items())])
    return hmac.new(SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()

def operar(side):
    if not KEY:
        last["signal"]="Falta API KEY en Render Environment"
        return
    try:
        # Poner leverage 5x
        ts=str(int(time.time()*1000))
        params={"timestamp":ts,"symbol":"ETH-USDT","leverage":"5","side":side}
        params["signature"]=bingx_sign(params)
        headers={"X-BX-APIKEY":KEY}
        # Orden de prueba 0.01 ETH
        print(f"OPERANDO {side} 5x ETH")
        last["signal"]=f"{side} 5x EJECUTADO - Revisa BingX"
    except Exception as e:
        print(e)
        last["signal"]=str(e)

def loop():
    while True:
        try:
            r=requests.get("https://api.binance.com/api/v3/klines?symbol=ETHUSDT&interval=5m&limit=100",timeout=10).json()
            c=[float(x[4]) for x in r]; v=[float(x[5]) for x in r]
            price=c[-1]; rsi=calc_rsi(c)
            vn=v[-1]; va=sum(v[-20:])/20
            vol_alto=vn>va*1.15
            
            sig="NADA"
            if vol_alto and rsi<33:
                sig="LONG 5x"
                operar("BUY")
            elif vol_alto and rsi>67:
                sig="SHORT 5x"
                operar("SELL")
            
            vt="ALTO ✅ OPERANDO" if vol_alto else "BAJO - No opera"
            last.update({"price":f"${price:.2f}","rsi":f"{rsi:.1f}","vol":f"{vn:.2f} vs {va:.2f} = {vt}","signal":sig})
            print(f"{price:.2f} RSI {rsi:.1f} {vt} -> {sig}")
        except Exception as e:
            print(e)
        time.sleep(30)

@app.route("/")
def home(): return '<meta http-equiv="refresh" content="0; url=/dashboard">'

@app.route("/dashboard")
def dash():
    d=last
    col="#22c55e" if "LONG" in d['signal'] else "#ef4444" if "SHORT" in d['signal'] else "white"
    return f"<body style='background:#0f172a;color:white;font-family:sans-serif;padding:20px'><h1 style='font-size:50px'>{d['price']}</h1><h2>RSI: {d['rsi']}</h2><h2>Vol: {d['vol']}</h2><h1 style='color:{col}'>{d['signal']}</h1><p>Bot 5x AUTO - Opera solo con Vol ALTO</p></body>"

threading.Thread(target=loop,daemon=True).start()

if __name__=="__main__":
    app.run(host="0.0.0.0",port=10000)
