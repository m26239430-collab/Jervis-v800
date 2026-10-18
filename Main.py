import yfinance as yf, requests, os, datetime
BOT = os.getenv("BOT_TOKEN")
CHAT = os.getenv("CHAT_ID")

def send(msg):
    url = f"https://api.telegram.org/bot{BOT}/sendMessage"
    requests.post(url, data={"chat_id": CHAT, "text": msg})

df = yf.download("EURUSD=X", period="1d", interval="5m", progress=False)
price = float(df['Close'].iloc[-1]) if len(df)>20 else 0
send(f"✅ JERVIS LIVE\nPrice: {price}")
