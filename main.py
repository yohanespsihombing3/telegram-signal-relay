from flask import Flask, request, jsonify
import requests
import os
from datetime import datetime

app = Flask(__name__)

# =========================
# ENV
# =========================
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

TG_URL = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"

# =========================
# TELEGRAM SENDER
# =========================
def send_telegram(text):
    payload = {
        "chat_id": CHAT_ID,
        "text": text,
        "disable_web_page_preview": False
    }
    return requests.post(TG_URL, json=payload, timeout=10)

# =========================
# HEALTH CHECK
# =========================
@app.route("/", methods=["GET"])
def home():
    return "TradingView → Telegram Relay ACTIVE", 200

# =========================
# WEBHOOK
# =========================
@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)

    symbol = data.get("symbol", "UNKNOWN")
    exchange = data.get("exchange", "BINANCE")
    timeframe = data.get("timeframe", "N/A")

    tv_link = f"https://www.tradingview.com/chart/?symbol={exchange}:{symbol}"

    message = f"""
🚨 <b>NEW SIGNAL</b>

<b>Symbol:</b> {symbol}
<b>Timeframe:</b> {timeframe}

🔗 <a href="{tv_link}">OPEN LIVE CHART</a>
"""

    send_telegram(message)

    return jsonify({"status": "sent"}), 200

# =========================
# RUN
# =========================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)

