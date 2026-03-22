"""Social media scraper agent.

Receives a ticker query from the orchestrator via SharedAgentState, generates
mock social media posts, sends them as ScraperOutput to the Sentiment Agent,
and responds back to the orchestrator with a summary.

Replace generate_posts_for_ticker() with a real Reddit/Twitter client when
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

SOCIAL_SEED: str = os.getenv("SOCIAL_SEED_PHRASE", "social_agent_default_seed")
SOCIAL_PORT: int = int(os.getenv("SOCIAL_AGENT_PORT", "8001"))
SENTIMENT_AGENT_ADDRESS: str = os.getenv("SENTIMENT_AGENT_ADDRESS", "")

social = Agent(
    name="social_scraper",
    seed=SOCIAL_SEED,
    port=SOCIAL_PORT,
    endpoint=[f"http://localhost:{SOCIAL_PORT}/submit"],
)

# ---------------------------------------------------------------------------
# Mock data — swap this section for real scraping
# ---------------------------------------------------------------------------

# Templates keyed by ticker. {ticker} is replaced at runtime.
MOCK_TEMPLATES: list[dict[str, str]] = [
    # Positive
    {"text": "{ticker} earnings blew past expectations, revenue up 12% YoY. Impressive quarter.", "source": "reddit"},
    {"text": "{ticker} bulls are vindicated. Price target raised by multiple analysts on social media.", "source": "reddit"},
    {"text": "{ticker} just secured another massive deal. Demand is insatiable, this stock is going higher.", "source": "stocktwits"},
    {"text": "Everyone on this sub is bullish on {ticker}. The momentum is undeniable right now.", "source": "reddit"},
    {"text": "{ticker} short sellers getting crushed. Sentiment has completely flipped positive.", "source": "x"},
    # Negative
    {"text": "{ticker} sales declining, losing market share fast. Bearish outlook from the community.", "source": "reddit"},
    {"text": "{ticker} margins are getting crushed. Management seems distracted. Selling my position.", "source": "stocktwits"},
    {"text": "{ticker} export restrictions tightening. Revenue could drop significantly. Overvalued.", "source": "x"},
    {"text": "Layoffs at {ticker} signal slowing growth. Not a good sign for investors.", "source": "reddit"},
    {"text": "{ticker} regulatory risk is massive. I'm staying away until there's clarity.", "source": "reddit"},
    # Neutral
    {"text": "{ticker} announced minor product updates. Nothing groundbreaking, market shrugged.", "source": "reddit"},
    {"text": "{ticker} holding steady after mixed numbers. Wait and see mode for most investors.", "source": "stocktwits"},
    {"text": "{ticker} conference next week could move the stock either direction. No position changes yet.", "source": "x"},
]

CREDIBILITY_WEIGHTS: dict[str, float] = {
    "reddit": 0.55,
    "x": 0.50,
    "stocktwits": 0.60,
}


def generate_posts_for_ticker(ticker: str, count: int = 3) -> list[ScraperOutput]:
    """Generate mock social media posts for a specific ticker."""
    posts = []
    templates = random.sample(MOCK_TEMPLATES, min(count, len(MOCK_TEMPLATES)))
    for tmpl in templates:
        posts.append(ScraperOutput(
            ticker=ticker.upper(),
            text=tmpl["text"].format(ticker=ticker.upper()),
            source_name=tmpl["source"],
            credibility_weight=CREDIBILITY_WEIGHTS.get(tmpl["source"], 0.55),
            scraped_at=datetime.now(timezone.utc).isoformat(),
            post_id=f"social-{uuid4().hex[:12]}",
        ))
    return posts


# ---------------------------------------------------------------------------
# Message handler — orchestrator sends us a ticker to scrape
# ---------------------------------------------------------------------------

@social.on_event("startup")
async def on_startup(ctx: Context) -> None:
    ctx.logger.info(f"Social scraper address: {social.address}")
    ctx.logger.info(f"Sentiment agent: {SENTIMENT_AGENT_ADDRESS}")
    if not SENTIMENT_AGENT_ADDRESS:
        ctx.logger.warning("SENTIMENT_AGENT_ADDRESS not set — ScraperOutput will not be forwarded.")


@social.on_message(SharedAgentState)
async def handle_scrape_request(ctx: Context, sender: str, state: SharedAgentState) -> None:
    """Receive a ticker from the orchestrator, scrape, forward to sentiment agent, reply."""
    ticker = state.query.strip().upper()
    ctx.logger.info(f"Scrape request for {ticker} (session={state.chat_session_id})")

    posts = generate_posts_for_ticker(ticker, count=random.randint(3, 5))

    # Forward each post to the sentiment agent
    sent = 0
    if SENTIMENT_AGENT_ADDRESS:
        for post in posts:
            await ctx.send(SENTIMENT_AGENT_ADDRESS, post)
            ctx.logger.info(f"Sent {post.ticker} from {post.source_name} to sentiment agent")
            sent += 1
    else:
        ctx.logger.warning("No SENTIMENT_AGENT_ADDRESS — posts not forwarded.")

    # Reply to orchestrator
    state.result = f"Social scraper sent {sent} posts for {ticker} to sentiment analysis."
    state.source_agent = "social_scraper"
    state.posts_sent = sent
    await ctx.send(sender, state)


if __name__ == "__main__":
    social.run()
