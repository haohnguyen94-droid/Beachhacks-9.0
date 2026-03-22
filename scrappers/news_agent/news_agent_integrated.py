"""Financial news scraper agent — integrated with real NewsData.io API.

Receives ticker requests via uagents, fetches real news articles from NewsData.io,
and sends them as ScraperOutput to the Sentiment Agent.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from uuid import uuid4

import httpx
from dotenv import load_dotenv
from uagents import Agent, Context, Model

load_dotenv()

# Add fast/ to path for models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "fast"))
from models import ScraperOutput

# ─── Config ───────────────────────────────────────────────────────────

NEWS_SEED: str = os.getenv("NEWS_SEED_PHRASE", "news_agent_seed")
NEWS_PORT: int = int(os.getenv("NEWS_AGENT_PORT", "8004"))
SENTIMENT_AGENT_ADDRESS: str = os.getenv("SENTIMENT_AGENT_ADDRESS", "")

# API key rotation for NewsData
_api_keys_raw = os.getenv("NEWSDATA_API_KEY", "")
API_KEYS = [key.strip() for key in _api_keys_raw.split(",") if key.strip()]
_current_key_index = 0

def get_next_api_key() -> str:
    """Rotate through available API keys."""
    global _current_key_index
    if not API_KEYS:
        return ""
    key = API_KEYS[_current_key_index]
    _current_key_index = (_current_key_index + 1) % len(API_KEYS)
    return key

# ─── Agent ────────────────────────────────────────────────────────────

news_agent = Agent(
    name="news_scraper_agent",
    seed=NEWS_SEED,
    port=NEWS_PORT,
    endpoint=[f"http://localhost:{NEWS_PORT}/submit"],
    mailbox=True,
    publish_agent_details=True,
    network="testnet",
)

# ─── Startup ───────────────────────────────────────────────────────────

@news_agent.on_event("startup")
async def startup(ctx: Context) -> None:
    ctx.logger.info(f"News Scraper Agent started at {news_agent.address}")
    ctx.logger.info(f"Sentiment Agent Address: {SENTIMENT_AGENT_ADDRESS}")
    ctx.logger.info(f"Using {len(API_KEYS)} API keys for NewsData.io")

# ─── NewsData Fetcher ──────────────────────────────────────────────────

async def fetch_articles_from_newsdata(ticker: str, count: int = 5) -> list[ScraperOutput]:
    """Fetch real articles from NewsData.io using rotating API keys."""
    results = []
    
    api_key = get_next_api_key()
    if not api_key:
        return results
    
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.get(
                "https://newsdata.io/api/1/news",
                params={
                    "apikey": api_key,
                    "q": ticker,
                    "language": "en",
                }
            )
            data = response.json()
            
            articles = data.get("results", [])
            for item in articles[:count]:
                if not isinstance(item, dict):
                    continue
                
                title = item.get("title", "")
                desc = item.get("description", "") or ""
                text = f"{title}. {desc}"
                
                if len(text.strip()) < 20:
                    continue
                
                results.append(ScraperOutput(
                    ticker=ticker.upper(),
                    text=text[:512],
                    source_name=item.get("source_name", "newsdata"),
                    credibility_weight=0.80,
                    scraped_at=datetime.now(timezone.utc).isoformat(),
                    post_id=str(uuid4()),
                    source_type="news",
                    title=title,
                    url=item.get("link", ""),
                    published_at=item.get("pubDate", ""),
                ))
    except Exception as exc:
        return []
    
    return results

# ─── Message Handler ──────────────────────────────────────────────────

class TickerQuery(Model):
    """Simple request to scrape a ticker."""
    ticker: str

@news_agent.on_message(model=TickerQuery)
async def handle_ticker_query(ctx: Context, sender: str, msg: TickerQuery) -> None:
    """Receive ticker query, fetch articles, send to Sentiment Agent."""
    ctx.logger.info(f"Received query for ticker: {msg.ticker}")

    # Fetch articles from NewsData
    articles = await fetch_articles_from_newsdata(msg.ticker, count=5)
    ctx.logger.info(f"Fetched {len(articles)} articles for {msg.ticker}")

    # Send each article to sentiment agent
    if SENTIMENT_AGENT_ADDRESS:
        for article in articles:
            await ctx.send(SENTIMENT_AGENT_ADDRESS, article)
            ctx.logger.info(f"Sent article to sentiment agent: {article.title[:50]}")

# ─── HTTP Handler for FastAPI triggers ────────────────────────────────────

async def process_tickers_for_fastapi(tickers: list[str]) -> dict:
    """Process a list of tickers and fetch articles for each."""
    if not SENTIMENT_AGENT_ADDRESS:
        return {"error": "SENTIMENT_AGENT_ADDRESS not configured"}

    total_articles = 0
    for ticker in tickers:
        articles = await fetch_articles_from_newsdata(ticker, count=5)
        total_articles += len(articles)

        # Send each article to sentiment agent
        for article in articles:
            # We can't use ctx.send here, so we'll return articles for FastAPI to handle
            pass

    return {"tickers": tickers, "total_articles": total_articles}

if __name__ == "__main__":
    news_agent.run()
