from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv

load_dotenv()

NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")

WATCHLIST = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN"]
MAX_ITEMS = 5

MOVEMENT_KEYWORDS = [
    "surge", "plunge", "jump", "drop", "rally",
    "earnings", "guidance", "downgrade", "upgrade",
    "acquisition", "layoffs", "regulation", "forecast"
]


def is_relevant(text: str) -> bool:
    text_lower = text.lower()
    return any(k in text_lower for k in MOVEMENT_KEYWORDS)


async def fetch_news_for_ticker(ticker: str) -> list[dict]:
    url = "https://newsdata.io/api/1/news"

    params = {
        "apikey": NEWSDATA_API_KEY,
        "q": ticker,
        "language": "en",
    }

    results = []

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        data = resp.json()

    articles = data.get("results", [])

    for item in articles:
        if len(results) >= MAX_ITEMS:
            break

        title = item.get("title", "")
        desc = item.get("description", "")
        text = f"{title}. {desc}"

        if not is_relevant(text):
            continue

        results.append({
            "ticker": ticker,
            "text": text[:512],
            "source_name": "newsdata",
            "source_type": "news",
            "credibility_weight": 0.8,
            "scraped_at": datetime.now(timezone.utc).isoformat(),
            "post_id": str(uuid.uuid4()),
            "title": title,
            "url": item.get("link", ""),
            "published_at": item.get("pubDate", ""),
            "raw_payload": item,
        })

    return results


async def fetch_all_news() -> list[dict]:
    """THIS is the function your agent is calling"""
    all_results = []

    for ticker in WATCHLIST:
        items = await fetch_news_for_ticker(ticker)
        print(f"{ticker}: {len(items)} articles")
        all_results.extend(items)

    return all_results