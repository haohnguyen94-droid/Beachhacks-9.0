import os
from datetime import datetime, timezone
from uuid import uuid4

from dotenv import load_dotenv

load_dotenv()

from scrappers.models.config import ORCHESTRATOR_SEED
from scrappers.models.models import SharedAgentState
from scrappers.orchestrator.chat_protocol import chat_proto, collect_agent_response
from uagents import Agent, Context, Model
from uagents_core.contrib.protocols.chat import ChatMessage, EndSessionContent, TextContent

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
    Waits until both social and news agents have responded, then relays
    the combined summary back to the original user.
    """
    ctx.logger.info(
        f"Response from {state.source_agent}: session={state.chat_session_id}, "
        f"posts_sent={state.posts_sent}, result={state.result!r}"
    )

    summary = collect_agent_response(state)

    if summary is None:
        # Still waiting for the other agent
        ctx.logger.info("Waiting for remaining agent response...")
        return

    # Both agents responded — send summary to user
    ctx.logger.info(f"All agents responded. Sending summary to user.")
    await ctx.send(
        state.user_sender_address,
        ChatMessage(
            timestamp=datetime.now(tz=timezone.utc),
            msg_id=uuid4(),
            content=[
                TextContent(type="text", text=summary),
                EndSessionContent(type="end-session"),
            ],
        ),
    )


if __name__ == "__main__":
    orchestrator.run()
