"""Financial news scraper agent.

Receives a ticker query from the orchestrator via SharedAgentState, generates
mock news articles, sends them as ScraperOutput to the Sentiment Agent,
and responds back to the orchestrator with a summary.

Replace generate_articles_for_ticker() with a real NewsAPI/RSS client when
ready — the interface (ScraperOutput out, SharedAgentState back) stays the same.
"""

from __future__ import annotations

import os
import random
import sys
from datetime import datetime, timezone
from uuid import uuid4

from dotenv import load_dotenv
from uagents import Agent, Context

load_dotenv()

# Add fast/ to path so we can import the canonical models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "fast"))
from models import ScraperOutput

from scrappers.models.models import SharedAgentState

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

NEWS_SEED: str = os.getenv("NEWS_SEED_PHRASE", "news_agent_default_seed")
NEWS_PORT: int = int(os.getenv("NEWS_AGENT_PORT", "8004"))
SENTIMENT_AGENT_ADDRESS: str = os.getenv("SENTIMENT_AGENT_ADDRESS", "")

news = Agent(
    name="news_scraper",
    seed=NEWS_SEED,
    port=NEWS_PORT,
    mailbox=True,
    publish_agent_details=True,
    network="testnet",
)

# ---------------------------------------------------------------------------
# Mock data — swap this section for real scraping
# ---------------------------------------------------------------------------

MOCK_TEMPLATES: list[dict[str, str]] = [
    # Positive
    {"text": "{ticker} reports record quarterly revenue, beating analyst estimates by 5%. Strong growth across all segments.", "source": "reuters"},
    {"text": "{ticker} delivers above guidance. Gross margins stabilize as cost optimization takes hold.", "source": "bloomberg"},
    {"text": "{ticker} secures major partnership deal. Analysts raise price targets across the board.", "source": "cnbc"},
    {"text": "{ticker} revenue growth re-accelerating. AI-driven services now contributing significant run rate.", "source": "wsj"},
    {"text": "{ticker} beats on both top and bottom line. Third consecutive profitable quarter for growth segment.", "source": "financial_times"},
    # Negative
    {"text": "{ticker} faces antitrust pressure in EU, potential multi-billion dollar fine. Revenue model under threat.", "source": "reuters"},
    {"text": "{ticker} issues massive recall over safety concerns. Regulatory investigation escalates.", "source": "bloomberg"},
    {"text": "{ticker} faces expanded export restrictions. Analysts estimate billions in annual revenue at risk.", "source": "wsj"},
    {"text": "{ticker} warns of slower growth ahead as enterprise customers pull back on spending.", "source": "cnbc"},
    {"text": "{ticker} hit with landmark antitrust ruling. Appeal expected but uncertainty weighs on shares.", "source": "financial_times"},
    # Neutral
    {"text": "{ticker} announces annual conference date. Market expects incremental updates, no major announcements.", "source": "yahoo_finance"},
    {"text": "{ticker} opens new facility on schedule. Production timeline remains unchanged from prior guidance.", "source": "reuters"},
    {"text": "{ticker} partners with industry leaders on long-term initiative. Revenue impact not expected until 2027.", "source": "bloomberg"},
]

CREDIBILITY_WEIGHTS: dict[str, float] = {
    "reuters": 0.90,
    "bloomberg": 0.90,
    "wsj": 0.85,
    "cnbc": 0.75,
    "financial_times": 0.85,
    "yahoo_finance": 0.70,
}


def generate_articles_for_ticker(ticker: str, count: int = 3) -> list[ScraperOutput]:
    """Generate mock news articles for a specific ticker."""
    articles = []
    templates = random.sample(MOCK_TEMPLATES, min(count, len(MOCK_TEMPLATES)))
    for tmpl in templates:
        articles.append(ScraperOutput(
            ticker=ticker.upper(),
            text=tmpl["text"].format(ticker=ticker.upper()),
            source_name=tmpl["source"],
            credibility_weight=CREDIBILITY_WEIGHTS.get(tmpl["source"], 0.75),
            scraped_at=datetime.now(timezone.utc).isoformat(),
            post_id=f"news-{uuid4().hex[:12]}",
        ))
    return articles


# ---------------------------------------------------------------------------
# Message handler — orchestrator sends us a ticker to scrape
# ---------------------------------------------------------------------------

@news.on_event("startup")
async def on_startup(ctx: Context) -> None:
    ctx.logger.info(f"News scraper address: {news.address}")
    ctx.logger.info(f"Sentiment agent: {SENTIMENT_AGENT_ADDRESS}")
    if not SENTIMENT_AGENT_ADDRESS:
        ctx.logger.warning("SENTIMENT_AGENT_ADDRESS not set — ScraperOutput will not be forwarded.")


@news.on_message(SharedAgentState)
async def handle_scrape_request(ctx: Context, sender: str, state: SharedAgentState) -> None:
    """Receive a ticker from the orchestrator, scrape, forward to sentiment agent, reply."""
    ticker = state.query.strip().upper()
    ctx.logger.info(f"Scrape request for {ticker} (session={state.chat_session_id})")

    articles = generate_articles_for_ticker(ticker, count=random.randint(3, 4))

    # Forward each article to the sentiment agent
    sent = 0
    if SENTIMENT_AGENT_ADDRESS:
        for article in articles:
            await ctx.send(SENTIMENT_AGENT_ADDRESS, article)
            ctx.logger.info(f"Sent {article.ticker} from {article.source_name} to sentiment agent")
            sent += 1
    else:
        ctx.logger.warning("No SENTIMENT_AGENT_ADDRESS — articles not forwarded.")

    # Reply to orchestrator
    state.result = f"News scraper sent {sent} articles for {ticker} to sentiment analysis."
    state.source_agent = "news_scraper"
    state.posts_sent = sent
    await ctx.send(sender, state)


if __name__ == "__main__":
    news.run()
