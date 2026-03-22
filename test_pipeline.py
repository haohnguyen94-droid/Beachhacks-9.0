"""Local pipeline test agent — sends ScraperOutput directly to the sentiment
agent using the uagents framework to verify the pipeline works end-to-end.

Usage:
    python test_pipeline.py [TICKER]
    python test_pipeline.py AAPL

Requires: sentiment_agent and signal_engine to be running.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from uuid import uuid4

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "fast"))

from dotenv import load_dotenv

load_dotenv()

from uagents import Agent, Context
from models import ScraperOutput

SENTIMENT_AGENT_ADDRESS: str = os.getenv("SENTIMENT_AGENT_ADDRESS", "")
TICKER: str = sys.argv[1].upper() if len(sys.argv) > 1 else "AAPL"

test_agent = Agent(
    name="test_sender",
    seed="test_sender_temp_seed_12345",
    port=9999,
    endpoint=["http://localhost:9999/submit"],
)

TEST_POSTS = [
    {"text": f"{TICKER} earnings blew past expectations, revenue up 12% YoY. Strong quarter.", "source": "reddit", "cred": 0.55},
    {"text": f"{TICKER} faces antitrust pressure, potential multi-billion dollar fine coming.", "source": "reuters", "cred": 0.90},
    {"text": f"{TICKER} announced minor product updates. Nothing groundbreaking.", "source": "yahoo_finance", "cred": 0.70},
    {"text": f"{TICKER} secures massive partnership deal. Analysts raise price targets.", "source": "bloomberg", "cred": 0.90},
    {"text": f"{TICKER} margins getting crushed by competition. Bearish outlook.", "source": "stocktwits", "cred": 0.60},
]


@test_agent.on_event("startup")
async def send_test_data(ctx: Context) -> None:
    if not SENTIMENT_AGENT_ADDRESS:
        ctx.logger.error("SENTIMENT_AGENT_ADDRESS not set in .env")
        return

    ctx.logger.info(f"Sending {len(TEST_POSTS)} test posts for {TICKER} to {SENTIMENT_AGENT_ADDRESS}")

    for post in TEST_POSTS:
        msg = ScraperOutput(
            ticker=TICKER,
            text=post["text"],
            source_name=post["source"],
            credibility_weight=post["cred"],
            scraped_at=datetime.now(timezone.utc).isoformat(),
            post_id=f"test-{uuid4().hex[:12]}",
        )
        await ctx.send(SENTIMENT_AGENT_ADDRESS, msg)
        ctx.logger.info(f"Sent: {post['source']} -> {TICKER}")

    ctx.logger.info(f"All {len(TEST_POSTS)} posts sent! Check sentiment agent logs.")
    ctx.logger.info(f"After aggregation, check: http://localhost:8000/signals/latest")


if __name__ == "__main__":
    test_agent.run()
