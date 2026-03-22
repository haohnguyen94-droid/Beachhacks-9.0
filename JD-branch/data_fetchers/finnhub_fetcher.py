from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv

load_dotenv()

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")

WATCHLIST = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN"]
MAX_ITEMS = 5


async def fetch_finnhub_news(ticker: str) -> list[dict]:
    """
    Fetch company news from Finnhub API and normalize to ScraperOutput format.
    """

    url = "https://finnhub.io/api/v1/company-news"

    params = {
        "symbol": ticker,
        "from": "2024-01-01",
        "to": datetime.now().strftime("%Y-%m-%d"),
        "token": FINNHUB_API_KEY,
    }

    results = []

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url, params=params)
            data = resp.json()
    except Exception:
        return results

    for item in data[:MAX_ITEMS]:
        text = f"{item.get('headline', '')}. {item.get('summary', '')}"

        results.append({
            "ticker": ticker,
            "text": text[:512],
            "source_name": "finnhub",
            "source_type": "market_data",
            "credibility_weight": 0.85,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "post_id": str(uuid.uuid4()),
            "title": item.get("headline", ""),
            "url": item.get("url", ""),
            "published_at": datetime.fromtimestamp(
                item.get("datetime", 0)
            ).isoformat(),
            "raw_payload": item,
        })

    return results


async def fetch_all_finnhub() -> list[dict]:
    """
    Fetch Finnhub data for all watchlist tickers.
    """

    all_results = []

    for ticker in WATCHLIST:
        items = await fetch_finnhub_news(ticker)
        print(f"{ticker}: {len(items)} items")
        all_results.extend(items)

    return all_results



if __name__ == "__main__":
    import asyncio

    data = asyncio.run(fetch_all_finnhub())
    print(f"\nTotal items: {len(data)}")

    for d in data[:3]:
        print(d)