from agents.models.config import REDDIT_SEED
from agents.models.models import SharedAgentState
from uagents import Agent, Context

reddit = Agent(
    name="reddit agent",
    seed=REDDIT_SEED,
    port=8001,
    mailbox=True,
    publish_agent_details=True,
)


def reddit_workflow(state: SharedAgentState) -> SharedAgentState:
    state.result = f"This is the Reddit Agent! Your message was: {state.query}"
    return state


@reddit.on_message(SharedAgentState)
async def handle_message(ctx: Context, sender: str, state: SharedAgentState):
    ctx.logger.info(f"Received state from orchestrator: session={state.chat_session_id}, query={state.query!r}")
    state = reddit_workflow(state)
    await ctx.send(sender, state)


if __name__ == "__main__":
    reddit.run()