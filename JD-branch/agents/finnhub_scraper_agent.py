from __future__ import annotations

import os

from uagents import Agent, Context

from data_fetchers.finnhub_fetcher import fetch_finnhub_news_for_ticker
from models.models import ScrapeBatch, ScrapeRequest, ScraperOutput

ORCHESTRATOR_ADDRESS = os.getenv("ORCHESTRATOR_ADDRESS", "")

agent = Agent(
    name="finnhub_scraper_agent",
    seed=os.getenv("FINNHUB_AGENT_SEED_PHRASE", "finnhub_scraper_seed"),
    port=8002,
    endpoint=["http://localhost:8002/submit"],
    mailbox=False,
)


@agent.on_message(model=ScrapeRequest)
async def handle_scrape_request(ctx: Context, sender: str, msg: ScrapeRequest) -> None:
    """Fetch Finnhub items for requested tickers and return a batch to the orchestrator."""

    ctx.logger.info(
        f"Received scrape request: request_id={msg.request_id}, tickers={msg.tickers}, limit={msg.limit}"
    )

    all_items: list[ScraperOutput] = []

    for ticker in msg.tickers:
        raw_items = await fetch_finnhub_news_for_ticker(ticker=ticker, limit=msg.limit)
        ctx.logger.info(f"Finnhub fetched {len(raw_items)} items for {ticker}")

        for item in raw_items:
            all_items.append(ScraperOutput(**item))

    batch = ScrapeBatch(
        request_id=msg.request_id,
        source_agent="finnhub_scraper_agent",
        items=all_items,
    )

    target = sender or ORCHESTRATOR_ADDRESS
    ctx.logger.info(f"Sending {len(all_items)} items back to orchestrator")
    await ctx.send(target, batch)
    ctx.logger.info(f"Returned {len(all_items)} Finnhub items to orchestrator")


if __name__ == "__main__":
    agent.run()