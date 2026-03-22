"""Chat protocol for the orchestrator.

Accepts a ticker symbol (e.g. "AAPL") from the user via ASI:One / Agentverse
chat, dispatches scrape requests to both the social and news agents, collects
their responses, and replies to the user with a summary.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone
from uuid import uuid4

from uagents import Context, Protocol
from scrappers.models.config import SOCIAL_ADDRESS, NEWS_ADDRESS
from scrappers.models.models import SharedAgentState
from scrappers.services.state_service import state_service
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)

chat_proto = Protocol(spec=chat_protocol_spec)

# Track how many agent responses we've received per session
_pending_responses: dict[str, dict] = {}

# Valid ticker pattern
TICKER_RE = re.compile(r"^[A-Z]{1,5}$")

SUPPORTED_TICKERS = {"AAPL", "TSLA", "NVDA", "MSFT", "GOOGL"}


def _extract_ticker(text: str) -> str | None:
    """Try to extract a ticker symbol from the user's message."""
    # Check each word for a valid ticker
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

    # Track that we expect 2 responses (social + news)
    _pending_responses[chat_session_id] = {
        "ticker": ticker,
        "sender": sender,
        "responses": [],
        "expected": 2,
    }

    # Dispatch to both scraper agents
    await ctx.send(SOCIAL_ADDRESS, state)
    ctx.logger.info(f"Dispatched {ticker} to social scraper")

    await ctx.send(NEWS_ADDRESS, state)
    ctx.logger.info(f"Dispatched {ticker} to news scraper")

    # Acknowledge to user that analysis is in progress
    await ctx.send(
        sender,
        ChatMessage(
            timestamp=datetime.now(tz=timezone.utc),
            msg_id=uuid4(),
            content=[
                TextContent(
                    type="text",
                    text=f"Analyzing {ticker} — dispatched to social media and news scrapers. Collecting data...",
                ),
            ],
        ),
    )


@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass


def collect_agent_response(state: SharedAgentState) -> str | None:
    """Record an agent response. Returns a summary string when all agents have replied, else None."""
    session = state.chat_session_id
    if session not in _pending_responses:
        return state.result

    pending = _pending_responses[session]
    pending["responses"].append(state)

    if len(pending["responses"]) < pending["expected"]:
        return None

    # All agents responded — build summary
    ticker = pending["ticker"]
    total_posts = sum(r.posts_sent for r in pending["responses"])
    agent_summaries = [r.result for r in pending["responses"]]

    del _pending_responses[session]

    return (
        f"Analysis for {ticker} initiated.\n\n"
        + "\n".join(f"- {s}" for s in agent_summaries)
        + f"\n\nTotal: {total_posts} sources sent to sentiment analysis. "
        f"Check the dashboard at /signals/latest for results once aggregation completes."
    )
