from __future__ import annotations

from uagents import Model


class ScrapeRequest(Model):
    """Request sent from the orchestrator to scraper agents."""

    request_id: str
    tickers: list[str] = []
    crypto_symbols: list[str] = []
    limit: int = 5


class ScraperOutput(Model):
    """Normalized raw item returned by scraper agents."""

    ticker: str
    text: str
    source_name: str
    source_type: str
    credibility_weight: float
    scraped_at: str
    post_id: str = ""
    title: str = ""
    url: str = ""
    published_at: str = ""
    raw_payload: dict = {}


class ScrapeBatch(Model):
    """Batch response sent from a scraper agent back to the orchestrator."""

    request_id: str
    source_agent: str
    items: list[ScraperOutput]