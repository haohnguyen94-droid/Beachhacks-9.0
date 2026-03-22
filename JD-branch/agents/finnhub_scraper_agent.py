"""Finnhub scraper agent.

Receives a ticker from the orchestrator via SharedAgentState, fetches real
company news from the Finnhub API, sends them as ScraperOutput to the
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
from data_fetchers.finnhub_fetcher import fetch_finnhub_news

FINNHUB_SEED: str = os.getenv("FINNHUB_AGENT_SEED_PHRASE", "finnhub_agent_default_seed")
FINNHUB_PORT: int = int(os.getenv("FINNHUB_AGENT_PORT", "8007"))

agent = Agent(
    name="finnhub_scraper",
    seed=FINNHUB_SEED,
    port=FINNHUB_PORT,
    endpoint=[f"http://localhost:{FINNHUB_PORT}/submit"],
)


@agent.on_event("startup")
async def on_startup(ctx: Context) -> None:
    ctx.logger.info(f"Finnhub scraper address: {agent.address}")
    ctx.logger.info(f"Sentiment agent: {SENTIMENT_AGENT_ADDRESS}")
    if not SENTIMENT_AGENT_ADDRESS:
        ctx.logger.warning("SENTIMENT_AGENT_ADDRESS not set — ScraperOutput will not be forwarded.")


@agent.on_message(SharedAgentState)
async def handle_scrape_request(ctx: Context, sender: str, state: SharedAgentState) -> None:
    ticker = state.query.strip().upper()
    ctx.logger.info(f"Scrape request for {ticker} (session={state.chat_session_id})")

    try:
        results = await fetch_finnhub_news(ticker)
    except Exception as e:
        ctx.logger.error(f"Finnhub fetch failed for {ticker}: {e}")
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

    state.result = f"Finnhub scraper sent {sent} articles for {ticker} to sentiment analysis."
    state.source_agent = "finnhub_scraper"
    state.posts_sent = sent
    await ctx.send(sender, state)


if __name__ == "__main__":
    agent.run()
