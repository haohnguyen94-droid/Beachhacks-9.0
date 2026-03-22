"""NewsData scraper agent.

Receives a ticker from the orchestrator via SharedAgentState, fetches real
news articles from the NewsData API, sends them as ScraperOutput to the
Sentiment Agent, and replies to the orchestrator with a count.
"""

from __future__ import annotations

import os
import sys

# Add JD-branch root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv, find_dotenv
from uagents import Agent, Context

load_dotenv(find_dotenv())

from models.models import ScraperOutput, SharedAgentState
from models.config import SENTIMENT_AGENT_ADDRESS
from data_fetchers.newsdata_fetcher import fetch_news_for_ticker

NEWSDATA_SEED: str = os.getenv("NEWSDATA_AGENT_SEED_PHRASE", "newsdata_agent_default_seed")
NEWSDATA_PORT: int = int(os.getenv("NEWSDATA_AGENT_PORT", "8006"))

agent = Agent(
    name="newsdata_scraper",
    seed=NEWSDATA_SEED,
    port=NEWSDATA_PORT,
    endpoint=[f"http://localhost:{NEWSDATA_PORT}/submit"],
)


@agent.on_event("startup")
async def on_startup(ctx: Context) -> None:
    ctx.logger.info(f"NewsData scraper address: {agent.address}")
    ctx.logger.info(f"Sentiment agent: {SENTIMENT_AGENT_ADDRESS}")
    if not SENTIMENT_AGENT_ADDRESS:
        ctx.logger.warning("SENTIMENT_AGENT_ADDRESS not set — ScraperOutput will not be forwarded.")


@agent.on_message(SharedAgentState)
async def handle_scrape_request(ctx: Context, sender: str, state: SharedAgentState) -> None:
    ticker = state.query.strip().upper()
    ctx.logger.info(f"Scrape request for {ticker} (session={state.chat_session_id})")

    try:
        results = await fetch_news_for_ticker(ticker)
    except Exception as e:
        ctx.logger.error(f"NewsData fetch failed for {ticker}: {e}")
        results = []

    sent = 0
    if SENTIMENT_AGENT_ADDRESS:
        for item in results:
            msg = ScraperOutput(**item)
            await ctx.send(SENTIMENT_AGENT_ADDRESS, msg)
            ctx.logger.info(f"Sent {msg.ticker} [{msg.source_name}] to sentiment agent")
            sent += 1
    else:
        ctx.logger.warning("No SENTIMENT_AGENT_ADDRESS — articles not forwarded.")

    state.result = f"NewsData scraper sent {sent} articles for {ticker} to sentiment analysis."
    state.source_agent = "newsdata_scraper"
    state.posts_sent = sent
    await ctx.send(sender, state)


if __name__ == "__main__":
    agent.run()
