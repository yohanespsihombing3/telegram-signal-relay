from fastapi import FastAPI, Request
from pybit.unified_trading import HTTP
import os
import time

app = FastAPI()

bybit = HTTP(
    api_key=os.getenv("BYBIT_API_KEY"),
    api_secret=os.getenv("BYBIT_API_SECRET"),
    testnet=False
)

# =========================
# CONFIG
# =========================
RISK_PERCENT = 0.5        # % risk per trade
TP1_CLOSE_RATIO = 0.5    # 50%
CATEGORY = "linear"

# =========================
# STATE (SIMPLE MEMORY)
# =========================
active_trade = {}

# =========================
# UTILS
# =========================
def get_position(symbol):
    pos = bybit.get_positions(category=CATEGORY, symbol=symbol)
    for p in pos["result"]["list"]:
        if float(p["size"]) > 0:
            return p
    return None

def calculate_qty(entry, sl, balance, risk_pct):
    risk_usd = balance * (risk_pct / 100)
    sl_distance = abs(entry - sl)
    return round(risk_usd / sl_distance, 3)

def get_balance():
    bal = bybit.get_wallet_balance(accountType="UNIFIED")
    return float(bal["result"]["list"][0]["totalEquity"])

# =========================
# WEBHOOK
# =========================
@app.post("/webhook")
async def webhook(req: Request):
    data = await req.json()

    # ===== FILTER WAJIB =====
    if data.get("type") != "ENTRY":
        return {"status": "ignored"}

    if data.get("ema_confirm") != "YES":
        return {"status": "ema not confirmed"}

    if data.get("volatility") != "OK":
        return {"status": "low volatility"}

    symbol = data["symbol"] + "USDT"

    # Cegah double posisi
    if get_position(symbol):
        return {"status": "position already open"}

    side = "Buy" if data["direction"] == "LONG" else "Sell"

    entry = float(data["entry"])
    sl = float(data["stoploss"])
    tp1 = float(data["tp1"])

    balance = get_balance()
    qty = calculate_qty(entry, sl, balance, RISK_PERCENT)

    # ===== ENTRY =====
    bybit.place_order(
        category=CATEGORY,
        symbol=symbol,
        side=side,
        orderType="Market",
        qty=qty,
        stopLoss=sl,
        timeInForce="GoodTillCancel"
    )

    active_trade[symbol] = {
        "side": side,
        "entry": entry,
        "tp1": tp1,
        "qty": qty,
        "tp1_hit": False
    }

    return {"status": "entry placed", "qty": qty}

# =========================
# PRICE MONITOR (TP1 + BE)
# =========================
@app.on_event("startup")
async def monitor():
    while True:
        try:
            for symbol, trade in list(active_trade.items()):
                if trade["tp1_hit"]:
                    continue

                ticker = bybit.get_tickers(category=CATEGORY, symbol=symbol)
                price = float(ticker["result"]["list"][0]["lastPrice"])

                hit_tp1 = (
                    price >= trade["tp1"]
                    if trade["side"] == "Buy"
                    else price <= trade["tp1"]
                )

                if hit_tp1:
                    close_qty = round(trade["qty"] * TP1_CLOSE_RATIO, 3)

                    # Close 50%
                    bybit.place_order(
                        category=CATEGORY,
                        symbol=symbol,
                        side="Sell" if trade["side"] == "Buy" else "Buy",
                        orderType="Market",
                        qty=close_qty,
                        reduceOnly=True
                    )

                    # Move SL to BE
                    bybit.set_trading_stop(
                        category=CATEGORY,
                        symbol=symbol,
                        stopLoss=trade["entry"]
                    )

                    trade["tp1_hit"] = True

        except Exception as e:
            print("ERROR:", e)

        time.sleep(2)
