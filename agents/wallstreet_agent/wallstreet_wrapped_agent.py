from agents.models.config import WALLSTREET_SEED
from agents.models.models import SharedAgentState
from uagents import Agent, Context

wallstreet = Agent(
    name="wallstreet",
    seed=WALLSTREET_SEED,
    port=8001,
    mailbox=True,
    publish_agent_details=True,
)


def wallstreet_workflow(state: SharedAgentState) -> SharedAgentState:
    state.result = f"Wallstreet agent, Your message was: {state.query}"
    return state


@wallstreet.on_message(SharedAgentState)
async def handle_message(ctx: Context, sender: str, state: SharedAgentState):
    ctx.logger.info(f"Received state from orchestrator: session={state.chat_session_id}, query={state.query!r}")
    state = wallstreet_workflow(state)
    await ctx.send(sender, state)


if __name__ == "__main__":
    wallstreet.run()