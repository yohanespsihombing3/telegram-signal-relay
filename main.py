from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Literal
import os

app = FastAPI(title="TradingView → Bybit Webhook")

# =========================
# MODEL SESUAI ALERT JSON
# =========================
class TVAlert(BaseModel):
    type: Literal["ENTRY"]
    symbol: str
    exchange: str
    timeframe: str
    direction: Literal["LONG", "SHORT"]
    entry: str
    stoploss: str
    tp1: str
    tp2: str
    tp3: str
    ema_confirm: Literal["YES", "NO"]
    volatility: Literal["OK", "LOW"]
    confidence: Literal["HIGH", "MEDIUM"]

# =========================
# HEALTH CHECK
# =========================
@app.get("/")
def root():
    return {"status": "alive", "service": "tv-bybit-webhook"}

# =========================
# WEBHOOK ENDPOINT
# =========================
@app.post("/webhook")
def webhook(alert: TVAlert):
    """
    Endpoint menerima alert JSON dari TradingView
    """

    # FILTER DASAR (AMAN)
    if alert.ema_confirm != "YES":
        return {"status": "ignored", "reason": "EMA not confirmed"}

    if alert.volatility != "OK":
        return {"status": "ignored", "reason": "Low volatility"}

    # Mapping direction
    side = "Buy" if alert.direction == "LONG" else "Sell"

    # RESPONSE (sementara)
    return {
        "status": "received",
        "symbol": alert.symbol,
        "side": side,
        "entry": alert.entry,
        "sl": alert.stoploss,
        "tp": [alert.tp1, alert.tp2, alert.tp3],
        "confidence": alert.confidence
    }

