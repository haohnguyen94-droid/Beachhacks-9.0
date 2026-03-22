from __future__ import annotations

import os
from dotenv import load_dotenv, find_dotenv

from uagents import Agent, Context

from models.models import ScraperOutput
from data_fetchers.newsdata_fetcher import fetch_all_news

load_dotenv(find_dotenv())

agent = Agent(
    name="newsdata_scraper_agent",
    seed=os.getenv("NEWSDATA_AGENT_SEED_PHRASE"),
    port=8001,
    endpoint=["http://localhost:8001/submit"],
)


@agent.on_interval(period=60.0)
async def run_news_scraper(ctx: Context):
    """
    Periodically fetch market-moving news articles and emit ScraperOutput messages.
    """

    ctx.logger.info("Running NewsData scraper agent...")

    try:
        results = await fetch_all_news()

        for item in results:
            msg = ScraperOutput(**item)
            ctx.logger.info(f"[News] {msg.ticker} -> {msg.title}")

        ctx.logger.info(f"Broadcasted {len(results)} news items")

    except Exception as e:
        ctx.logger.error(f"NewsData fetch failed: {e}")


if __name__ == "__main__":
    agent.run()