from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

import httpx
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY")

MOVEMENT_KEYWORDS = [
    "surge",
    "plunge",
    "jump",
    "drop",
    "rally",
    "earnings",
    "guidance",
    "downgrade",
    "upgrade",
    "acquisition",
    "layoffs",
    "regulation",
    "forecast",
]


def is_relevant(text: str) -> bool:
    """Filter for market-moving articles."""
    text_lower = text.lower()
    return any(keyword in text_lower for keyword in MOVEMENT_KEYWORDS)


async def fetch_news_for_ticker(ticker: str, limit: int = 5) -> list[dict]:
    """Fetch and normalize NewsData articles for one ticker."""
    if not NEWSDATA_API_KEY:
        raise RuntimeError("NEWSDATA_API_KEY is missing. Check your .env file.")

    url = "https://newsdata.io/api/1/news"
    params = {
        "apikey": NEWSDATA_API_KEY,
        "q": ticker,
        "language": "en",
    }

    results: list[dict] = []

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    articles = data.get("results", [])
    print(f"[NewsData] {ticker}: raw results = {len(articles)}")

    for item in articles:
        if len(results) >= limit:
            break

        title = item.get("title", "") or ""
        desc = item.get("description", "") or ""
        text = f"{title}. {desc}".strip()

        if not text:
            continue

        print(f"[NewsData] candidate title: {title}")

        results.append(
            {
                "ticker": ticker,
                "text": text[:512],
                "source_name": "newsdata",
                "source_type": "news",
                "credibility_weight": 0.80,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "post_id": str(uuid.uuid4()),
                "title": title,
                "url": item.get("link", "") or "",
                "published_at": item.get("pubDate", "") or "",
                "raw_payload": item,
            }
        )

    return results