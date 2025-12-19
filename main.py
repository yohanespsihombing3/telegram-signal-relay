from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")


def send_telegram(msg):
    if not BOT_TOKEN or not CHAT_ID:
        print("❌ BOT_TOKEN atau CHAT_ID belum diset")
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML"
    }

    r = requests.post(url, json=payload)
    print("📨 Telegram response:", r.text)
    return r.ok


@app.route("/", methods=["GET"])
def home():
    return "Webhook is running"


@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(silent=True)

    if not data:
        return jsonify({"error": "No JSON received"}), 400

    signal_type = data.get("type", "SIGNAL")

    # ======================
    # PREPARE MESSAGE
    # ======================
    if signal_type == "PREPARE":
        msg = f"""
<b>🟡 DEWASMC PREPARE</b>

📊 <b>Symbol:</b> {data.get('symbol', '-')}
⏱ <b>TF:</b> {data.get('tf', '-')}

📈 <b>Side:</b> {data.get('side', '-')}
⚡ <b>EMA Confirm:</b> {data.get('ema_confirm', '-')}

⏳ <i>Menunggu valid BOS / CHoCH</i>

#DEWASMC #PREPARE
"""
        send_telegram(msg)
        return jsonify({"status": "prepare sent"}), 200

    # ======================
    # ENTRY MESSAGE
    # ======================
    if signal_type == "ENTRY":
        msg = f"""
<b>🚀 DEWASMC ENTRY</b>

📊 <b>Symbol:</b> {data.get('symbol', '-')}
⏱ <b>TF:</b> {data.get('tf', '-')}

📈 <b>Side:</b> {data.get('side', '-')}

🎯 <b>Entry:</b> {data.get('entry', '-')}
🛑 <b>SL:</b> {data.get('sl', '-')}

🎯 <b>TP1:</b> {data.get('tp1', '-')}
🎯 <b>TP2:</b> {data.get('tp2', '-')}
🎯 <b>TP3:</b> {data.get('tp3', '-')}

⚡ <b>EMA Confirm:</b> {data.get('ema_confirm', '-')}

#DEWASMC #ENTRY #SMC
"""
        send_telegram(msg)
        return jsonify({"status": "entry sent"}), 200

    # ======================
    # UNKNOWN TYPE
    # ======================
    return jsonify({"status": "ignored"}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
