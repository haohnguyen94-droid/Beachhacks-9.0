import os
import sys
from datetime import datetime, timezone
from uuid import uuid4

from dotenv import load_dotenv, find_dotenv

# Add JD-branch root to path so models/, services/, orchestrator/ resolve
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

load_dotenv(find_dotenv())

from models.config import ORCHESTRATOR_SEED
from models.models import SharedAgentState, FinalSignal
from orchestrator.chat_protocol import (
    chat_proto,
    collect_agent_response,
    _pending_responses,
    clear_pending_session,
)
from uagents import Agent, Context, Model
from uagents_core.contrib.protocols.chat import ChatMessage, EndSessionContent, TextContent

ORCHESTRATOR_PORT: int = int(os.getenv("ORCHESTRATOR_PORT", "8005"))

orchestrator = Agent(
    name="orchestrator",
    seed=ORCHESTRATOR_SEED,
    port=ORCHESTRATOR_PORT,
    mailbox=True,
    publish_agent_details=True,
)

orchestrator.include(chat_proto, publish_manifest=True)


class HealthResponse(Model):
    status: str


class HttpMessagePost(Model):
    content: str


class HttpMessageResponse(Model):
    echo: str


@orchestrator.on_rest_get("/health", HealthResponse)
async def health(ctx: Context) -> HealthResponse:
    return HealthResponse(status="ok healthy")


@orchestrator.on_rest_post("/message", HttpMessagePost, HttpMessageResponse)
async def message(ctx: Context, req: HttpMessagePost) -> HttpMessageResponse:
    return HttpMessageResponse(echo=req.content)


@orchestrator.on_message(SharedAgentState)
async def handle_agent_response(ctx: Context, sender: str, state: SharedAgentState):
    """
    Receives SharedAgentState back from a scraper agent.
    When all scrapers have responded, triggers signal engine aggregation.
    """
    ctx.logger.info(
        f"Received state back from {state.source_agent}: "
        f"session={state.chat_session_id}, posts_sent={state.posts_sent}, "
        f"result={state.result!r}"
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
    Formats and sends the result back to the original user.
    """
    ctx.logger.info(
        f"FinalSignal for {signal.ticker}: {signal.direction} | "
        f"score={signal.aggregate_score:.4f} | "
        f"confidence={signal.confidence_pct:.1f}% | "
        f"strength={signal.signal_strength}"
    )

    # Find the pending session for this ticker
    session_id = None
    pending = None
    for sid, data in list(_pending_responses.items()):
        if data["ticker"] == signal.ticker:
            session_id = sid
            pending = data
            break

    if not pending:
        ctx.logger.warning(f"No pending session for {signal.ticker} — cannot relay to user.")
        return

    user_address = pending["sender"]
    clear_pending_session(session_id)

    # Format signal as readable message
    sources_info = ""
    if signal.supporting_sources:
        top = signal.supporting_sources[:5]
        sources_info = "\n\nTop sources:\n" + "\n".join(
            f"  - [{s.source_name}] {s.sentiment_direction} "
            f"(score={s.sentiment_score:.2f}): {s.text[:120]}..."
            for s in top
        )

    response = (
        f"=== Signal for {signal.ticker} ===\n"
        f"Direction: {signal.direction}\n"
        f"Score: {signal.aggregate_score:.4f}\n"
        f"Confidence: {signal.confidence_pct:.1f}%\n"
        f"Strength: {signal.signal_strength}\n"
        f"Sources: {signal.source_count}\n"
        f"Majority: {signal.majority_direction} "
        f"({signal.directional_agreement_pct:.1f}% agreement)\n"
        f"Distribution: {signal.score_distribution}"
    )
    if signal.forced_hold:
        response += f"\nForced HOLD: {signal.forced_hold_reason}"
    response += sources_info

    await ctx.send(
        user_address,
        ChatMessage(
            timestamp=datetime.now(tz=timezone.utc),
            msg_id=uuid4(),
            content=[
                TextContent(type="text", text=response),
                EndSessionContent(type="end-session"),
            ],
        ),
    )
    ctx.logger.info(f"Sent final signal for {signal.ticker} to user.")


if __name__ == "__main__":
    orchestrator.run()
