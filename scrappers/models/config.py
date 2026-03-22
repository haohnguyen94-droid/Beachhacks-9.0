import os

from dotenv import find_dotenv, load_dotenv
from uagents_core.identity import Identity

load_dotenv(find_dotenv())

SOCIAL_SEED: str = os.getenv("SOCIAL_SEED_PHRASE", "social_agent_default_seed")
NEWS_SEED: str = os.getenv("NEWS_SEED_PHRASE", "news_agent_default_seed")
ORCHESTRATOR_SEED: str = os.getenv("ORCHESTRATOR_SEED_PHRASE", "orchestrator_default_seed")

SOCIAL_ADDRESS: str = Identity.from_seed(seed=SOCIAL_SEED, index=0).address
NEWS_ADDRESS: str = Identity.from_seed(seed=NEWS_SEED, index=0).address

# Sentiment agent address — scrapers send ScraperOutput here
SENTIMENT_AGENT_SEED: str = os.getenv("SENTIMENT_AGENT_SEED", "sentiment_agent_seed_phrase")
SENTIMENT_AGENT_ADDRESS: str = Identity.from_seed(seed=SENTIMENT_AGENT_SEED, index=0).address
