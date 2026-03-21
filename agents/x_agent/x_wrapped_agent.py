from agents.models.config import X_SEED
from agents.models.models import SharedAgentState
from uagents import Agent, Context

x = Agent(
    name="x",
    seed=X_SEED,
    port=8001,
    mailbox=True,
    publish_agent_details=True,
)


def x_workflow(state: SharedAgentState) -> SharedAgentState:
    state.result = f"X agent, Your message was: {state.query}"
    return state


@x.on_message(SharedAgentState)
async def handle_message(ctx: Context, sender: str, state: SharedAgentState):
    ctx.logger.info(f"Received state from orchestrator: session={state.chat_session_id}, query={state.query!r}")
    state = x_workflow(state)
    await ctx.send(sender, state)


if __name__ == "__main__":
    x.run()