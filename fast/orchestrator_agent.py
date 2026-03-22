"""Orchestrator Agent — triggers the analysis workflow.

When the FastAPI backend receives an /api/analyze request,
it sends a request to this orchestrator to start the agent workflow.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone

from dotenv import load_dotenv
from uagents import Agent, Context, Model

load_dotenv()

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from models import ScraperOutput

# ─── Config ───────────────────────────────────────────────────────────

ORCHESTRATOR_SEED: str = os.getenv("ORCHESTRATOR_SEED_PHRASE", "orchestrator_seed")
ORCHESTRATOR_PORT: int = 8005
NEWS_AGENT_ADDRESS: str = os.getenv("NEWS_AGENT_ADDRESS", "")

DEMO_TICKERS = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "META", "GOOG", "JPM", "XOM", "UNH"]

# ─── Message Types ────────────────────────────────────────────────────

class AnalysisRequest(Model):
    """Request to start analysis workflow."""
    tickers: list[str] = DEMO_TICKERS
    request_id: str = ""

class TickerQuery(Model):
    """Query to scrape a specific ticker."""
    ticker: str

# ─── Agent ────────────────────────────────────────────────────────────

orchestrator = Agent(
    name="orchestrator",
    seed=ORCHESTRATOR_SEED,
    port=ORCHESTRATOR_PORT,
    endpoint=[f"http://localhost:{ORCHESTRATOR_PORT}/submit"],
    mailbox=True,
    publish_agent_details=True,
    network="testnet",
)

# ─── Startup ───────────────────────────────────────────────────────────

@orchestrator.on_event("startup")
async def startup(ctx: Context) -> None:
    ctx.logger.info(f"Orchestrator Agent started at {orchestrator.address}")
    ctx.logger.info(f"News Agent Address: {NEWS_AGENT_ADDRESS}")

# ─── Shared workflow trigger ──────────────────────────────────────────

async def trigger_analysis_workflow(tickers: list[str] | None = None) -> None:
    """Shared function to start the analysis workflow."""
    tickers = tickers or DEMO_TICKERS

    if not NEWS_AGENT_ADDRESS:
        print("[orchestrator] ERROR: NEWS_AGENT_ADDRESS not set in .env")
        return

    print(f"[orchestrator] Starting analysis workflow for {len(tickers)} tickers")
    # Send ticker queries to news agent
    for ticker in tickers:
        query = TickerQuery(ticker=ticker)
        # Note: This would require an active Context, so we'll use message handler instead
        print(f"[orchestrator] Would send query for {ticker} to {NEWS_AGENT_ADDRESS}")

# ─── Message Handler ──────────────────────────────────────────────────

@orchestrator.on_message(model=AnalysisRequest)
async def handle_analysis_request(ctx: Context, sender: str, msg: AnalysisRequest) -> None:
    """Start the agent workflow for all tickers."""
    ctx.logger.info(f"Starting analysis workflow for tickers: {msg.tickers}")

    if not NEWS_AGENT_ADDRESS:
        ctx.logger.error("NEWS_AGENT_ADDRESS not set in .env")
        return

    # Send ticker queries to news agent
    for ticker in msg.tickers:
        query = TickerQuery(ticker=ticker)
        await ctx.send(NEWS_AGENT_ADDRESS, query)
        ctx.logger.info(f"Sent query for {ticker} to news agent")

if __name__ == "__main__":
    orchestrator.run()
