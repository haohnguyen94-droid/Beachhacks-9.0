"""Chat protocol for the orchestrator.

Accepts a ticker symbol (e.g. "AAPL") from the user via ASI:One / Agentverse
chat, dispatches scrape requests to all scraper agents (mock + real API),
collects their responses, triggers signal engine aggregation, and replies
to the user with the final signal.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from uuid import uuid4

from uagents import Context, Protocol
from scrappers.models.config import (
    SOCIAL_ADDRESS,
    NEWS_ADDRESS,
    NEWSDATA_ADDRESS,
    FINNHUB_ADDRESS,
    SIGNAL_ENGINE_ADDRESS,
)
from scrappers.models.models import SharedAgentState
from scrappers.services.state_service import state_service
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "fast"))
from models import AggregateRequest

chat_proto = Protocol(spec=chat_protocol_spec)

# Track how many agent responses we've received per session
_pending_responses: dict[str, dict] = {}

# Valid ticker pattern
TICKER_RE = re.compile(r"^[A-Z]{1,5}$")

SUPPORTED_TICKERS = {"AAPL", "TSLA", "NVDA", "MSFT", "GOOGL", "AMZN"}

# All scraper agents to dispatch to
SCRAPER_AGENTS = [
    ("social_scraper", SOCIAL_ADDRESS),
    ("news_scraper", NEWS_ADDRESS),
    ("newsdata_scraper", NEWSDATA_ADDRESS),
    ("finnhub_scraper", FINNHUB_ADDRESS),
]


def _extract_ticker(text: str) -> str | None:
    """Try to extract a ticker symbol from the user's message."""
    for word in text.upper().split():
        cleaned = word.strip(".,!?")
        if TICKER_RE.match(cleaned) and cleaned in SUPPORTED_TICKERS:
            return cleaned
    return None


@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
    await ctx.send(
        sender,
        ChatAcknowledgement(timestamp=datetime.now(), acknowledged_msg_id=msg.msg_id),
    )

    text = " ".join(
        item.text for item in msg.content if isinstance(item, TextContent)
    )
    ctx.logger.info(f"Received: {text}")

    chat_session_id = str(ctx.session)
    ticker = _extract_ticker(text)

    if not ticker:
        await ctx.send(
            sender,
            ChatMessage(
                timestamp=datetime.now(tz=timezone.utc),
                msg_id=uuid4(),
                content=[
                    TextContent(
                        type="text",
                        text=(
                            f"Send me a ticker symbol to analyze. "
                            f"Supported: {', '.join(sorted(SUPPORTED_TICKERS))}"
                        ),
                    ),
                    EndSessionContent(type="end-session"),
                ],
            ),
        )
        return

    # Create shared state with the ticker as the query
    state = SharedAgentState(
        chat_session_id=chat_session_id,
        query=ticker,
        user_sender_address=sender,
    )
    state_service.set_state(chat_session_id, state)

    # Track that we expect responses from all scraper agents
    _pending_responses[chat_session_id] = {
        "ticker": ticker,
        "sender": sender,
        "responses": [],
        "expected": len(SCRAPER_AGENTS),
    }

    # Dispatch to all scraper agents
    for agent_name, agent_address in SCRAPER_AGENTS:
        await ctx.send(agent_address, state)
        ctx.logger.info(f"Dispatched {ticker} to {agent_name}")

    # Acknowledge to user that analysis is in progress
    scraper_names = ", ".join(name for name, _ in SCRAPER_AGENTS)
    await ctx.send(
        sender,
        ChatMessage(
            timestamp=datetime.now(tz=timezone.utc),
            msg_id=uuid4(),
            content=[
                TextContent(
                    type="text",
                    text=f"Analyzing {ticker} — dispatched to {scraper_names}. Collecting data...",
                ),
            ],
        ),
    )


@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass


async def collect_agent_response(ctx: Context, state: SharedAgentState) -> bool:
    """Record an agent response. Returns True when all agents have replied and aggregation is triggered."""
    session = state.chat_session_id
    if session not in _pending_responses:
        return False

    pending = _pending_responses[session]
    pending["responses"].append(state)

    if len(pending["responses"]) < pending["expected"]:
        return False

    # All scrapers responded — trigger signal engine aggregation
    ticker = pending["ticker"]
    total_posts = sum(r.posts_sent for r in pending["responses"])

    ctx.logger.info(
        f"All scrapers responded for {ticker}. "
        f"Total {total_posts} articles sent to sentiment. "
        f"Triggering signal engine aggregation..."
    )

    # Send aggregation request to signal engine
    orchestrator_address = str(ctx.address)
    await ctx.send(
        SIGNAL_ENGINE_ADDRESS,
        AggregateRequest(
            ticker=ticker,
            chat_session_id=session,
            requester_address=orchestrator_address,
        ),
    )

    return True


def get_pending_session(session_id: str) -> dict | None:
    """Get pending session data (used by orchestrator to look up sender)."""
    return _pending_responses.get(session_id)


def clear_pending_session(session_id: str) -> None:
    """Clean up a completed session."""
    _pending_responses.pop(session_id, None)
