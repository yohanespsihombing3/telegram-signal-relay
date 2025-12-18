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
    data = request.json
    if not data:
        return jsonify({"error": "No JSON received"}), 400

    msg = f"""
<b>{data.get('prefix', 'SIGNAL')}</b>
<b>🚀 DEWASMC ELITE SIGNAL</b>

📊 <b>Symbol:</b> {data.get('symbol', '-')}
⏱ <b>TF:</b> {data.get('tf', '-')}
📈 <b>Direction:</b> {data.get('side', '-')}

🎯 <b>Entry:</b> {data.get('entry', '-')}
🛑 <b>SL:</b> {data.get('sl', '-')}

TP: {data.get('tp', '-')}
"""

    sent = send_telegram(msg)

    return jsonify({"status": "ok", "sent": sent}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)


