import time
import hashlib
import requests
import os
from flask import Flask, request, jsonify

# ======================
# APP INIT
# ======================
app = Flask(__name__)
PORT = int(os.getenv("PORT", 10000))

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# ======================
# SIGNAL LOCK (ANTI DUPLICATE)
# ======================
LAST_SIGNAL = {}
LOCK_TIME = 60  # seconds

# ======================
# UTILS
# ======================
def safe(data, key, default="N/A"):
    return str(data.get(key, default))

def make_hash(symbol, side, price):
    raw = f"{symbol}-{side}-{price}"
    return hashlib.md5(raw.encode()).hexdigest()

def is_locked(sig_hash):
    now = time.time()
    if sig_hash in LAST_SIGNAL:
        if now - LAST_SIGNAL[sig_hash] < LOCK_TIME:
            return True
    LAST_SIGNAL[sig_hash] = now
    return False

def send_telegram(msg):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram ENV missing")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg
    }

    try:
        r = requests.post(url, json=payload, timeout=10)
        print("Telegram:", r.status_code, r.text)
    except Exception as e:
        print("Telegram error:", e)

# ======================
# WEBHOOK
# ======================
@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"status": "error", "msg": "Invalid JSON"}), 400

    # ===== REQUIRED FIELDS =====
    required = ["symbol", "side", "price"]
    for r in required:
        if r not in data:
            return jsonify({"status": "error", "msg": f"Missing {r}"}), 400

    symbol = safe(data, "symbol")
    tf     = safe(data, "timeframe")
    side   = safe(data, "side")
    price  = safe(data, "price")
    sl     = safe(data, "sl")
    tp     = safe(data, "tp")
    ema    = safe(data, "ema_confirm", "NO")

    # ===== ANTI DUPLICATE =====
    sig_hash = make_hash(symbol, side, price)
    if is_locked(sig_hash):
        return jsonify({"status": "ignored", "reason": "duplicate signal"}), 200

    # ===== TELEGRAM MESSAGE =====
    message = f"""
NEW TRADE INFO
------------------------
Symbol   : {symbol}
TF       : {tf}
Side     : {side}
Entry    : {price}
Stoploss : {sl}
TakeProfit : {tp}
EMA Confirm : {ema}
------------------------
"""

    send_telegram(message.strip())

    print("Signal sent:", data)

    return jsonify({"status": "success"}), 200

# ======================
# HEALTH CHECK
# ======================
@app.route("/", methods=["GET"])
def home():
    return "Webhook Trade Info Running", 200

# ======================
# RUN
# ======================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
