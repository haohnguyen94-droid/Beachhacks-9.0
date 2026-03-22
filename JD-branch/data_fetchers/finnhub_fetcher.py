from __future__ import annotations

import os
import uuid
from datetime import datetime, timezone

import httpx
from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())

FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")


async def fetch_finnhub_news_for_ticker(ticker: str, limit: int = 5) -> list[dict]:
    """Fetch and normalize Finnhub company news for one ticker."""
    if not FINNHUB_API_KEY:
        raise RuntimeError("FINNHUB_API_KEY is missing. Check your .env file.")

    url = "https://finnhub.io/api/v1/company-news"
    params = {
        "symbol": ticker,
        "from": "2025-01-01",
        "to": datetime.now().strftime("%Y-%m-%d"),
        "token": FINNHUB_API_KEY,
    }

    results: list[dict] = []

    async with httpx.AsyncClient(timeout=15) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    print(f"[Finnhub] {ticker}: raw results = {len(data) if isinstance(data, list) else data}")

    if not isinstance(data, list):
        return results

    for item in data[:limit]:
        headline = item.get("headline", "") or ""
        summary = item.get("summary", "") or ""
        text = f"{headline}. {summary}".strip()

        if not text:
            continue

        print(f"[Finnhub] candidate: {headline}")

        published_at = ""
        ts = item.get("datetime", 0)
        if ts:
            try:
                published_at = datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
            except Exception:
                published_at = ""

        results.append(
            {
                "ticker": ticker,
                "text": text[:512],
                "source_name": "finnhub",
                "source_type": "market_data",
                "credibility_weight": 0.85,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
                "post_id": str(uuid.uuid4()),
                "title": headline,
                "url": item.get("url", "") or "",
                "published_at": published_at,
                "raw_payload": item,
            }
        )

    return results