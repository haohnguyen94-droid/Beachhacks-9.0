from scrappers.models.config import NEWS_SEED
from scrappers.models.models import SharedAgentState
from uagents import Agent, Context

news = Agent(
    name="news agent",
    seed=NEWS_SEED,
    port=8002,
    mailbox=True,
    publish_agent_details=True,
)


def news_workflow(state: SharedAgentState) -> SharedAgentState:
    state.result = f"This is the news agent, what do you want?"
    return state


@news.on_message(SharedAgentState)
async def handle_message(ctx: Context, sender: str, state: SharedAgentState):
    ctx.logger.info(f"Received state from orchestrator: session={state.chat_session_id}, query={state.query!r}")
    state = news_workflow(state)
    await ctx.send(sender, state)


if __name__ == "__main__":
    news.run()