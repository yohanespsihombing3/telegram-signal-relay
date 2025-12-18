from flask import Flask, request, jsonify
import requests
import os

app = Flask(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
CHAT_ID = os.environ.get("CHAT_ID")

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": CHAT_ID,
        "text": msg,
        "parse_mode": "HTML"
    }
    return requests.post(url, json=payload)

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    if not data:
        return jsonify({"error": "No JSON"}), 400

    msg = f"""
<b>🚀 DEWASMC PRO SIGNAL</b>

<b>Type:</b> {data.get("type")}
<b>Symbol:</b> {data.get("symbol")}
<b>TF:</b> {data.get("tf")}
<b>Side:</b> {data.get("side")}
<b>EMA:</b> {data.get("ema_confirm")}

<b>Entry:</b> {data.get("entry","-")}
<b>SL:</b> {data.get("sl","-")}

TP1: {data.get("tp1","-")}
TP2: {data.get("tp2","-")}
TP3: {data.get("tp3","-")}
"""

    send_telegram(msg)
    return jsonify({"status": "ok"}), 200

if __name__ == "__main__":
    app.run()
