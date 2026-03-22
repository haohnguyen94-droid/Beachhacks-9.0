from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from uagents import Agent, Context, Model

from models.models import ScrapeBatch, ScrapeRequest

NEWSDATA_AGENT_ADDRESS ="agent1qt9c3mtftwx2hljvk5f9k4kj40p4smkvev42kazlv8ymk00tve2qccyytun"
FINNHUB_AGENT_ADDRESS ="agent1q0xg4mdwd5drqmutwflsvk327qyz57khfq26l77nzqmw9qtwszye60t0fej"
CRYPTO_AGENT_ADDRESS = "agent1qg8yv3jnzj3fudyw3dpd8ku7fhndtu0edu8vpv8wj824j75epvjjx6p99rn"

agent = Agent(
    name="orchestrator",
    seed=os.getenv("ORCHESTRATOR_SEED_PHRASE", "orchestrator_seed"),
    port=8003,
    endpoint=["http://localhost:8003/submit"],
    mailbox=False,
)


class RunScrapeRequest(Model):
    tickers: list[str] = []
    crypto_symbols: list[str] = []
    limit: int = 5


class RunScrapeResponse(Model):
    """REST response body after dispatching scrape jobs."""

    request_id: str
    status: str


class BatchState:
    def __init__(self, tickers: list[str], crypto_symbols: list[str], limit: int) -> None:
        self.tickers = tickers
        self.crypto_symbols = crypto_symbols
        self.limit = limit
        self.received_sources: set[str] = set()
        self.source_items: dict[str, list[dict]] = {
            "newsdata_scraper_agent": [],
            "finnhub_scraper_agent": [],
            "crypto_scraper_agent": [],
        }


REQUEST_STORE: dict[str, BatchState] = {}


def ensure_output_dir() -> Path:
    """Create output directory if missing."""
    output_dir = Path("outputs")
    output_dir.mkdir(exist_ok=True)
    return output_dir


def save_json(request_id: str, payload: dict) -> str:
    """Persist merged JSON for the frontend."""
    output_dir = ensure_output_dir()
    file_path = output_dir / f"{request_id}.json"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    return str(file_path)

def normalize_text(value: str) -> str:
    """Normalize text for simple deduplication."""
    return " ".join((value or "").strip().lower().split())

def dedupe_items(items: list[dict]) -> list[dict]:
    """Deduplicate items using title + text fingerprint instead of URL."""
    seen: set[str] = set()
    deduped: list[dict] = []

    for item in items:
        title = normalize_text(item.get("title", ""))
        text = normalize_text(item.get("text", ""))[:160]

        # Stronger dedupe key: ignore URL, focus on actual story content
        key = f"{title}|{text}"

        if not title and not text:
            continue

        if key in seen:
            continue

        seen.add(key)
        deduped.append(item)

    return deduped

def simplify_item(item: dict) -> dict:
    """Keep only frontend-relevant fields."""
    return {
        "ticker": item.get("ticker", ""),
        "title": item.get("title", ""),
        "text": item.get("text", ""),
        "source_name": item.get("source_name", ""),
        "source_type": item.get("source_type", ""),
        "credibility_weight": item.get("credibility_weight", 0.0),
        "scraped_at": item.get("scraped_at", ""),
        "published_at": item.get("published_at", ""),
        "url": item.get("url", ""),
        "post_id": item.get("post_id", ""),
    }

def build_frontend_json(request_id: str, state: BatchState) -> dict:
    """Build a deduplicated, frontend-friendly JSON payload."""

    raw_news_items = state.source_items.get("newsdata_scraper_agent", [])
    raw_finnhub_items = state.source_items.get("finnhub_scraper_agent", [])
    raw_crypto_items = state.source_items.get("crypto_scraper_agent", [])

    # Simplify first
    news_items = [simplify_item(item) for item in raw_news_items]
    finnhub_items = [simplify_item(item) for item in raw_finnhub_items]
    crypto_items = [simplify_item(item) for item in raw_crypto_items]

    # Dedupe inside each source
    news_items = dedupe_items(news_items)
    finnhub_items = dedupe_items(finnhub_items)
    crypto_items = dedupe_items(crypto_items)

    # Merge and dedupe again globally
    merged_items = dedupe_items(news_items + finnhub_items + crypto_items)
    # Sort newest first
    merged_items.sort(
        key=lambda item: item.get("published_at") or item.get("scraped_at") or "",
        reverse=True,
    )

    source_counts = {
    "newsdata": len(news_items),
    "finnhub": len(finnhub_items),
    "crypto": len(crypto_items),
}

    by_ticker: dict[str, int] = {}
    for item in merged_items:
        ticker = item.get("ticker", "UNKNOWN")
        by_ticker[ticker] = by_ticker.get(ticker, 0) + 1

    top_headlines = [
        item["title"]
        for item in merged_items[:10]
        if item.get("title")
    ]

    return {
        "status": "success",
        "request_id": request_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "tickers": state.tickers,
        "crypto_symbols": state.crypto_symbols,
        "source_counts": source_counts,
        "by_ticker": by_ticker,
        "top_headlines": top_headlines,
        "latest_items": merged_items[:5],
        "sources": {
            "newsdata": news_items,
            "finnhub": finnhub_items,
            "crypto": crypto_items,
        },
        "merged_items": merged_items,
        "total_items": len(merged_items),
    }


@agent.on_rest_post("/run", RunScrapeRequest, RunScrapeResponse)
async def run_scrape(ctx: Context, req: RunScrapeRequest) -> RunScrapeResponse:
    """Start a scrape request and fan out work to both scraper agents."""

    request_id = str(uuid4())
    REQUEST_STORE[request_id] = BatchState(
    tickers=req.tickers,
    crypto_symbols=req.crypto_symbols,
    limit=req.limit,
)
    scrape_msg = ScrapeRequest(
    request_id=request_id,
    tickers=req.tickers,
    crypto_symbols=req.crypto_symbols,
    limit=req.limit,
)

    if NEWSDATA_AGENT_ADDRESS:
        await ctx.send(NEWSDATA_AGENT_ADDRESS, scrape_msg)
        ctx.logger.info(f"Dispatched request {request_id} to NewsData agent")

    if FINNHUB_AGENT_ADDRESS:
        await ctx.send(FINNHUB_AGENT_ADDRESS, scrape_msg)
        ctx.logger.info(f"Dispatched request {request_id} to Finnhub agent")

    if CRYPTO_AGENT_ADDRESS:
        await ctx.send(CRYPTO_AGENT_ADDRESS, scrape_msg)
        ctx.logger.info(f"Dispatched request {request_id} to Crypto agent")

    return RunScrapeResponse(
        request_id=request_id,
        status="dispatched",
    )


@agent.on_message(model=ScrapeBatch)
async def handle_scrape_batch(ctx: Context, sender: str, msg: ScrapeBatch) -> None:
    """Collect batch results from scraper agents and write merged JSON when complete."""

    state = REQUEST_STORE.get(msg.request_id)
    if state is None:
        ctx.logger.warning(f"Unknown request_id received: {msg.request_id}")
        return

    state.received_sources.add(msg.source_agent)
    state.source_items[msg.source_agent] = [item.model_dump() for item in msg.items]

    ctx.logger.info(
        f"Received batch from {msg.source_agent}: request_id={msg.request_id}, items={len(msg.items)}"
    )

    expected_sources = {
    "newsdata_scraper_agent",
    "finnhub_scraper_agent",
    "crypto_scraper_agent",
}

    if state.received_sources == expected_sources:
        payload = build_frontend_json(msg.request_id, state)
        file_path = save_json(msg.request_id, payload)

        ctx.logger.info(
            f"Request {msg.request_id} completed. JSON written to {file_path}"
        )


if __name__ == "__main__":
    agent.run()