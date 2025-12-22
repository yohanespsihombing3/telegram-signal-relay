import json
import time
import hashlib
from flask import Flask, request, jsonify
import requests
import os

# =========================
# BASIC CONFIG
# =========================
app = Flask(__name__)

PORT = int(os.getenv("PORT", 5000))

# Telegram config (optional)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# =========================
# ANTI SPAM MEMORY
# =========================
LAST_SIGNAL = {}
SIGNAL_COOLDOWN = 60  # seconds

# =========================
# HELPER FUNCTIONS
# =========================

def safe_get(data, key, default="N/A"):
    """Safe JSON getter"""
    return str(data.get(key, default))

def signal_hash(data):
    """Create unique signal fingerprint"""
    raw = (
        safe_get(data, "symbol") +
        safe_get(data, "timeframe") +
        safe_get(data, "direction") +
        safe_get(data, "entry")
    )
    return hashlib.md5(raw.encode()).hexdigest()

def is_duplicate(sig_hash):
    """Anti duplicate signal"""
    now = time.time()
    last_time = LAST_SIGNAL.get(sig_hash)

    if last_time and (now - last_time) < SIGNAL_COOLDOWN:
        return True

    LAST_SIGNAL[sig_hash] = now
    return False

def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print("Telegram error:", e)

# =========================
# WEBHOOK ENDPOINT
# =========================

@app.route("/webhook", methods=["POST"])
def webhook():
    try:
        data = request.get_json(force=True)
    except Exception:
        return jsonify({"status": "error", "reason": "Invalid JSON"}), 400

    if not isinstance(data, dict):
        return jsonify({"status": "error", "reason": "JSON must be object"}), 400

    # Required minimal fields
    required = ["type", "symbol", "direction", "entry"]

    for field in required:
        if field not in data:
            return jsonify({
                "status": "error",
                "reason": f"Missing field: {field}"
            }), 400

    # Duplicate check
    sig_hash = signal_hash(data)
    if is_duplicate(sig_hash):
        return jsonify({
            "status": "ignored",
            "reason": "Duplicate signal"
        }), 200

    # =========================
    # PARSE DATA SAFELY
    # =========================
    symbol     = safe_get(data, "symbol")
    tf         = safe_get(data, "timeframe")
    direction  = safe_get(data, "direction")
    entry      = safe_get(data, "entry")
    sl         = safe_get(data, "stoploss")
    tp1        = safe_get(data, "tp1")
    tp2        = safe_get(data, "tp2")
    tp3        = safe_get(data, "tp3")
    ema_conf   = safe_get(data, "ema_confirm")
    confidence = safe_get(data, "confidence")

    # =========================
    # TELEGRAM MESSAGE
    # =========================
    message = f"""
🚀 *NEW SIGNAL*
━━━━━━━━━━━━━━
📊 Symbol : `{symbol}`
⏱ TF     : `{tf}`
📈 Type   : *{direction}*
🎯 Entry  : `{entry}`
🛑 SL     : `{sl}`

🎯 TP1    : `{tp1}`
🎯 TP2    : `{tp2}`
🎯 TP3    : `{tp3}`

📉 EMA    : *{ema_conf}*
🧠 Conf   : *{confidence}*
━━━━━━━━━━━━━━
"""

    send_telegram(message)

    print("Signal received:", json.dumps(data, indent=2))

    return jsonify({
        "status": "success",
        "symbol": symbol,
        "direction": direction
    }), 200

# =========================
# HEALTH CHECK
# =========================
@app.route("/", methods=["GET"])
def health():
    return "Webhook running OK", 200

# =========================
# MAIN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT)
