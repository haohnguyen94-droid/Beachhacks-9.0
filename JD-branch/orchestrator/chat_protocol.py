import re
from datetime import datetime, timezone
from uuid import uuid4

from uagents import Context, Protocol
from models.config import NEWSDATA_ADDRESS, FINNHUB_ADDRESS, SIGNAL_ENGINE_ADDRESS, ORCHESTRATOR_SEED
from uagents_core.identity import Identity
from models.models import SharedAgentState, AggregateRequest
from services.state_service import state_service
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    EndSessionContent,
    TextContent,
    chat_protocol_spec,
)

chat_proto = Protocol(spec=chat_protocol_spec)

# Track scraper responses per session
_pending_responses: dict[str, dict] = {}

ORCHESTRATOR_ADDRESS: str = Identity.from_seed(seed=ORCHESTRATOR_SEED, index=0).address

TICKER_RE = re.compile(r"^[A-Z]{1,5}$")


def _extract_ticker(text: str) -> str | None:
    """Pull a valid ticker symbol out of the message, ignoring agent addresses."""
    for word in text.upper().split():
        cleaned = word.strip(".,!?")
        if cleaned.startswith("@AGENT") or cleaned.startswith("AGENT1Q"):
            continue
        if TICKER_RE.match(cleaned):
            return cleaned
    return None


SCRAPER_AGENTS = [
    ("newsdata_scraper", NEWSDATA_ADDRESS),
    ("finnhub_scraper", FINNHUB_ADDRESS),
]


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
                    TextContent(type="text", text=f"Could not find a valid ticker in: {text}"),
                    EndSessionContent(type="end-session"),
                ],
            ),
        )
        return

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

    # Dispatch ticker to all scraper agents
    for agent_name, agent_address in SCRAPER_AGENTS:
        await ctx.send(agent_address, state)
        ctx.logger.info(f"Dispatched {ticker} to {agent_name}")

    # Acknowledge to user
    await ctx.send(
        sender,
        ChatMessage(
            timestamp=datetime.now(tz=timezone.utc),
            msg_id=uuid4(),
            content=[
                TextContent(
                    type="text",
                    text=f"Analyzing {ticker} — dispatched to newsdata and finnhub scrapers. Collecting data...",
                ),
            ],
        ),
    )


@chat_proto.on_message(ChatAcknowledgement)
async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    pass


async def collect_agent_response(ctx: Context, state: SharedAgentState) -> bool:
    """Record a scraper response. Returns True when all have replied and aggregation is triggered."""
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

    await ctx.send(
        SIGNAL_ENGINE_ADDRESS,
        AggregateRequest(
            ticker=ticker,
            chat_session_id=session,
            requester_address=ORCHESTRATOR_ADDRESS,
        ),
    )

    return True


def get_pending_session(session_id: str) -> dict | None:
    return _pending_responses.get(session_id)


def clear_pending_session(session_id: str) -> None:
    _pending_responses.pop(session_id, None)
