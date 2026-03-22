from agents.models.config import SOCIAL_SEED
from agents.models.models import SharedAgentState
from uagents import Agent, Context

social = Agent(
    name="social agent",
    seed=SOCIAL_SEED,
    port=8001,
    mailbox=True,
    publish_agent_details=True,
)


def social_workflow(state: SharedAgentState) -> SharedAgentState:
    state.result = f"This is the Reddit Agent! Your message was: {state.query}"
    return state


@social.on_message(SharedAgentState)
async def handle_message(ctx: Context, sender: str, state: SharedAgentState):
    ctx.logger.info(f"Received state from orchestrator: session={state.chat_session_id}, query={state.query!r}")
    state = social_workflow(state)
    await ctx.send(sender, state)


if __name__ == "__main__":
    social.run()