from __future__ import annotations

import os
from datetime import datetime, timezone

from uagents import Agent, Context

from models.models import ScrapeBatch, ScrapeRequest, ScraperOutput

agent = Agent(
    name="crypto_scraper_agent",
    seed=os.getenv("CRYPTO_AGENT_SEED_PHRASE", "crypto_scraper_seed"),
    port=8004,
    endpoint=["http://localhost:8004/submit"],
    mailbox=False,
)


def build_mock_crypto_items(symbol: str, limit: int = 5) -> list[dict]:
    now = datetime.now(timezone.utc).isoformat()

    samples = [
        {
            "ticker": symbol,
            "text": f"{symbol} rose after stronger market momentum and increased institutional interest.",
            "source_name": "crypto_agent",
            "source_type": "crypto",
            "credibility_weight": 0.75,
            "scraped_at": now,
            "post_id": f"{symbol.lower()}_crypto_1",
            "title": f"{symbol} gains on strong momentum",
            "url": f"https://example.com/{symbol.lower()}-momentum",
            "published_at": now,
            "raw_payload": {"symbol": symbol, "kind": "momentum"},
        },
        {
            "ticker": symbol,
            "text": f"{symbol} saw elevated trading activity as volatility expanded during the session.",
            "source_name": "crypto_agent",
            "source_type": "crypto",
            "credibility_weight": 0.75,
            "scraped_at": now,
            "post_id": f"{symbol.lower()}_crypto_2",
            "title": f"{symbol} volatility spikes",
            "url": f"https://example.com/{symbol.lower()}-volatility",
            "published_at": now,
            "raw_payload": {"symbol": symbol, "kind": "volatility"},
        },
        {
            "ticker": symbol,
            "text": f"{symbol} remained in focus as traders reacted to macro and risk-on sentiment.",
            "source_name": "crypto_agent",
            "source_type": "crypto",
            "credibility_weight": 0.75,
            "scraped_at": now,
            "post_id": f"{symbol.lower()}_crypto_3",
            "title": f"{symbol} reacts to broader market sentiment",
            "url": f"https://example.com/{symbol.lower()}-macro",
            "published_at": now,
            "raw_payload": {"symbol": symbol, "kind": "macro"},
        },
    ]

    return samples[:limit]


@agent.on_message(model=ScrapeRequest)
async def handle_scrape_request(ctx: Context, sender: str, msg: ScrapeRequest) -> None:
    ctx.logger.info(
        f"Received crypto scrape request: request_id={msg.request_id}, crypto_symbols={msg.crypto_symbols}, limit={msg.limit}"
    )

    all_items: list[ScraperOutput] = []

    for symbol in msg.crypto_symbols:
        raw_items = build_mock_crypto_items(symbol=symbol, limit=msg.limit)
        ctx.logger.info(f"Crypto fetched {len(raw_items)} items for {symbol}")

        for item in raw_items:
            all_items.append(ScraperOutput(**item))

    batch = ScrapeBatch(
        request_id=msg.request_id,
        source_agent="crypto_scraper_agent",
        items=all_items,
    )

    await ctx.send(sender, batch)
    ctx.logger.info(f"Returned {len(all_items)} Crypto items to orchestrator")


if __name__ == "__main__":
    agent.run()