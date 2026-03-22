import os
import sys
from datetime import datetime, timezone
from uuid import uuid4

from dotenv import load_dotenv

load_dotenv()

from scrappers.models.config import ORCHESTRATOR_SEED
from scrappers.models.models import SharedAgentState
from scrappers.orchestrator.chat_protocol import (
    chat_proto,
    collect_agent_response,
    get_pending_session,
    clear_pending_session,
)
from uagents import Agent, Context, Model
from uagents_core.contrib.protocols.chat import ChatMessage, EndSessionContent, TextContent

# Add fast/ to path for FinalSignal import
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "fast"))
from models import FinalSignal

ORCHESTRATOR_PORT: int = int(os.getenv("ORCHESTRATOR_PORT", "8005"))

orchestrator = Agent(
    name="orchestrator",
    seed=ORCHESTRATOR_SEED,
    port=ORCHESTRATOR_PORT,
    mailbox=True,
    publish_agent_details=True,
    network="testnet",
)

orchestrator.include(chat_proto, publish_manifest=True)


class HealthResponse(Model):
    status: str


@orchestrator.on_rest_get("/health", HealthResponse)
async def health(ctx: Context) -> HealthResponse:
    return HealthResponse(status="ok healthy")


@orchestrator.on_message(SharedAgentState)
async def handle_agent_response(ctx: Context, sender: str, state: SharedAgentState):
    """
    Receives SharedAgentState back from a scraper agent.
    When all scrapers have responded, triggers signal engine aggregation.
    """
    ctx.logger.info(
        f"Response from {state.source_agent}: session={state.chat_session_id}, "
        f"posts_sent={state.posts_sent}, result={state.result!r}"
    )

    all_done = await collect_agent_response(ctx, state)

    if not all_done:
        ctx.logger.info("Waiting for remaining scraper responses...")
        return

    ctx.logger.info("All scrapers done. Waiting for signal engine to aggregate...")


@orchestrator.on_message(FinalSignal)
async def handle_final_signal(ctx: Context, sender: str, signal: FinalSignal):
    """
    Receives FinalSignal from the signal engine after aggregation.
    Formats and sends the result back to the user.
    """
    ctx.logger.info(
        f"Received FinalSignal for {signal.ticker}: "
        f"direction={signal.direction}, score={signal.aggregate_score}, "
        f"confidence={signal.confidence_pct}%"
    )

    # Find the pending session for this ticker to get the user's address
    session_id = None
    pending = None
    from scrappers.orchestrator.chat_protocol import _pending_responses
    for sid, data in _pending_responses.items():
        if data["ticker"] == signal.ticker:
            session_id = sid
            pending = data
            break

    if not pending:
        ctx.logger.warning(f"No pending session found for {signal.ticker} — cannot relay to user.")
        return

    user_address = pending["sender"]
    clear_pending_session(session_id)

    # Format the signal as a readable message
    sources_summary = ""
    if signal.supporting_sources:
        top_sources = signal.supporting_sources[:5]
        sources_summary = "\n\nTop sources:\n" + "\n".join(
            f"  - [{s.source_name}] {s.sentiment_direction} "
            f"(score={s.sentiment_score:.2f}, confidence={s.confidence:.2f}): "
            f"{s.text[:100]}..."
            for s in top_sources
        )

    summary = (
        f"Signal for {signal.ticker}: {signal.direction}\n"
        f"Score: {signal.aggregate_score:.4f} | "
        f"Confidence: {signal.confidence_pct:.1f}% | "
        f"Strength: {signal.signal_strength}\n"
        f"Sources: {signal.source_count} | "
        f"Majority: {signal.majority_direction} ({signal.directional_agreement_pct:.1f}% agreement)\n"
        f"Distribution: {signal.score_distribution}"
    )

    if signal.forced_hold:
        summary += f"\nForced HOLD: {signal.forced_hold_reason}"

    summary += sources_summary

    await ctx.send(
        user_address,
        ChatMessage(
            timestamp=datetime.now(tz=timezone.utc),
            msg_id=uuid4(),
            content=[
                TextContent(type="text", text=summary),
                EndSessionContent(type="end-session"),
            ],
        ),
    )
    ctx.logger.info(f"Sent final signal for {signal.ticker} to user.")


if __name__ == "__main__":
    orchestrator.run()
