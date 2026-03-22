import httpx

payload = {
    "tickers": ["AAPL", "NVDA"],
    "crypto_symbols": ["BTC", "ETH"],
    "limit": 5
}

response = httpx.post("http://localhost:8003/run", json=payload)

print(response.status_code)
print(response.json())