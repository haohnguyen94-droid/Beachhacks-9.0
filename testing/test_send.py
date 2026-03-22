"""Send a test EntityExtracted message to the sentiment agent."""

from uagents import Agent, Context
from fast.models import EntityExtracted

SENTIMENT_AGENT_ADDRESS = "YOUR_SENTIMENT_AGENT_ADDRESS_HERE"

sender = Agent(name="test_sender", seed="test_sender_seed_phrase", port=8010,
               endpoint=["http://localhost:8010/submit"])

@sender.on_event("startup")
async def send_test(ctx: Context) -> None:
    msg = EntityExtracted(
        ticker="TSLA",
        company_name="Tesla Inc.",
        context_window=(
            "Tesla reported a sharp decline in deliveries this quarter, missing "
            "analyst expectations by 15%. The stock dropped 8% in after-hours trading "
            "as investors reacted to weakening demand in key markets."
        ),
        ner_entities=["Tesla"],
        sentiment_words=["decline", "missing", "dropped", "weakening"],
        keywords=[{"term": "delivery miss", "score": 0.92}],
        entity_verb_pairs=[["Tesla", "reported"], ["stock", "dropped"]],
        source_name="Bloomberg",
        credibility_weight=0.95,
        scraped_at="2026-03-21T12:00:00Z",
    )
    await ctx.send(SENTIMENT_AGENT_ADDRESS, msg)
    ctx.logger.info("Test message sent!")

if __name__ == "__main__":
    sender.run()
