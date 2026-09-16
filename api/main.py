from fastapi import FastAPI , HTTPException
import random
from datetime import datetime

app = FastAPI()



instruments = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "TSLA"]
price_ranges = {
    "AAPL": (150, 250),
    "MSFT": (300, 500),
    "NVDA": (500, 800),
    "GOOGL": (150, 250),
    "AMZN": (150, 250),
    "TSLA": (200, 400),
}
batch_size = random.randint(5,20)
@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/v1/market-data")
def market_data():
    data = []
    batch_size = random.randint(5,20)
    for _ in range(batch_size):
        instrument = random.choice(instruments)
        min_price, max_price = price_ranges[instrument]
        record = {
            "instrument_id": instrument,
            "price": round(random.uniform(min_price,max_price),2),
            "volume": random.randint(100,10000),
            "timestamp": datetime.now()
            }
        data.append(record)

    if random.random() < 0.05:
            raise HTTPException(
                status_code=500,
                detail="Synthetic upstream failure"
            )
    
    if random.random() < 0.15:
        data[0]['volume'] = "test"
        data[0]['price'] = None
    
    return data