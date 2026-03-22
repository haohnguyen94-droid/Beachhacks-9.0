"""Test the orchestrator by sending a ChatMessage locally.

Usage:
    python test_orchestrator.py [TICKER]

Requires: orchestrator to be running.
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from uuid import uuid4

from dotenv import load_dotenv

load_dotenv()

from uagents import Agent, Context
from uagents_core.contrib.protocols.chat import ChatMessage, TextContent

ORCHESTRATOR_ADDRESS: str = os.getenv("ORCHESTRATOR_ADDRESS", "agent1qvvzs865d75hvgqg0peq2x5wtyj6kgux2lmqv8fngth8f78j0tt9qr640c8")
TICKER: str = sys.argv[1].upper() if len(sys.argv) > 1 else "AAPL"

test_agent = Agent(
    name="test_chat",
    seed="test_chat_temp_seed_99999",
    port=9998,
    endpoint=["http://localhost:9998/submit"],
)


@test_agent.on_event("startup")
async def send_chat(ctx: Context) -> None:
    ctx.logger.info(f"Sending ChatMessage '{TICKER}' to orchestrator at {ORCHESTRATOR_ADDRESS}")

    msg = ChatMessage(
        timestamp=datetime.now(tz=timezone.utc),
        msg_id=uuid4(),
        content=[TextContent(type="text", text=TICKER)],
    )
    await ctx.send(ORCHESTRATOR_ADDRESS, msg)
    ctx.logger.info("ChatMessage sent! Check orchestrator terminal.")


@test_agent.on_message(ChatMessage)
async def handle_response(ctx: Context, sender: str, msg: ChatMessage) -> None:
    text = " ".join(
        item.text for item in msg.content if isinstance(item, TextContent)
    )
    ctx.logger.info(f"Response from orchestrator: {text}")


if __name__ == "__main__":
    test_agent.run()
