from fastapi import FastAPI, Request

app = FastAPI()

@app.get("/")
def root():
    return {"status": "ok"}

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()
    print("ALERT MASUK:", data)
    return {"received": True}

