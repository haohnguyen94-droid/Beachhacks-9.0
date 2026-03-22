import os

from dotenv import find_dotenv, load_dotenv
from uagents_core.identity import Identity

load_dotenv(find_dotenv())

# --- Agent seeds ---
ORCHESTRATOR_SEED: str = os.getenv("ORCHESTRATOR_SEED_PHRASE", "orchestrator_default_seed")
NEWSDATA_SEED: str = os.getenv("NEWSDATA_AGENT_SEED_PHRASE", "newsdata_agent_default_seed")
FINNHUB_SEED: str = os.getenv("FINNHUB_AGENT_SEED_PHRASE", "finnhub_agent_default_seed")
SENTIMENT_AGENT_SEED: str = os.getenv("SENTIMENT_AGENT_SEED", "sentiment_agent_seed_phrase")
SIGNAL_ENGINE_SEED: str = os.getenv("SIGNAL_ENGINE_SEED", "signal_engine_seed_phrase")

# --- Derived addresses ---
NEWSDATA_ADDRESS: str = Identity.from_seed(seed=NEWSDATA_SEED, index=0).address
FINNHUB_ADDRESS: str = Identity.from_seed(seed=FINNHUB_SEED, index=0).address
SENTIMENT_AGENT_ADDRESS: str = Identity.from_seed(seed=SENTIMENT_AGENT_SEED, index=0).address
SIGNAL_ENGINE_ADDRESS: str = Identity.from_seed(seed=SIGNAL_ENGINE_SEED, index=0).address
