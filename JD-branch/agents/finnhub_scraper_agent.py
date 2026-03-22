from __future__ import annotations

import os
from dotenv import load_dotenv, find_dotenv

from uagents import Agent, Context

from models.models import ScraperOutput
from data_fetchers.finnhub_fetcher import fetch_all_finnhub

load_dotenv(find_dotenv())

agent = Agent(
    name="finnhub_scraper_agent",
    seed=os.getenv("FINNHUB_AGENT_SEED_PHRASE"),
    port=8002,
    endpoint=["http://localhost:8002/submit"],
)


@agent.on_interval(period=60.0)
async def run_finnhub_scraper(ctx: Context):
    """
    Periodically fetch stock-related market data and emit ScraperOutput messages.
    """

    ctx.logger.info("Running Finnhub scraper agent...")

    try:
        results = await fetch_all_finnhub()

        for item in results:
            msg = ScraperOutput(**item)
            ctx.logger.info(f"[Finnhub] {msg.ticker} -> {msg.title}")

        ctx.logger.info(f"Broadcasted {len(results)} market items")

    except Exception as e:
        ctx.logger.error(f"Finnhub fetch failed: {e}")


if __name__ == "__main__":
    agent.run()