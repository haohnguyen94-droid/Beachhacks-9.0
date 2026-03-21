from agents.models.config import FINANCIAL_SEED
from agents.models.models import SharedAgentState
from uagents import Agent, Context

financialtimes = Agent(
    name="financialtimes",
    seed=FINANCIAL_SEED,
    port=8001,
    mailbox=True,
    publish_agent_details=True,
)


def financial_times_workflow(state: SharedAgentState) -> SharedAgentState:
    state.result = f"Financial Times, Your message was: {state.query}"
    return state


@financialtimes.on_message(SharedAgentState)
async def handle_message(ctx: Context, sender: str, state: SharedAgentState):
    ctx.logger.info(f"Received state from orchestrator: session={state.chat_session_id}, query={state.query!r}")
    state = financial_times_workflow(state)
    await ctx.send(sender, state)


if __name__ == "__main__":
    financialtimes.run()