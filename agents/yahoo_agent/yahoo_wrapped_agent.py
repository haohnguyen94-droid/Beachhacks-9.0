from agents.models.config import YAHOO_SEED
from agents.models.models import SharedAgentState
from uagents import Agent, Context

yahoo = Agent(
    name="yahoo",
    seed=YAHOO_SEED,
    port=8001,
    mailbox=True,
    publish_agent_details=True,
)


def yahoo_workflow(state: SharedAgentState) -> SharedAgentState:
    state.result = f"Yahoo agent, Your message was: {state.query}"
    return state


@yahoo.on_message(SharedAgentState)
async def handle_message(ctx: Context, sender: str, state: SharedAgentState):
    ctx.logger.info(f"Received state from orchestrator: session={state.chat_session_id}, query={state.query!r}")
    state = yahoo_workflow(state)
    await ctx.send(sender, state)


if __name__ == "__main__":
    yahoo.run()