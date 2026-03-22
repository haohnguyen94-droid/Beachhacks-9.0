import os
from dotenv import find_dotenv, load_dotenv
from uagents_core.identity import Identity

load_dotenv(find_dotenv())

SOCIAL_SEED = os.getenv("SOCIAL_SEED_PHRASE")
NEWS_SEED = os.getenv("WALLSTREET_SEED_PHRASE")

ORCHESTRATOR_SEED = os.getenv("ORCHESTRATOR_SEED_PHRASE")

SOCIAL_ADDRESS = Identity.from_seed(seed=SOCIAL_SEED, index=0).address
NEWS_ADDRESS = Identity.from_seed(seed=NEWS_SEED, index=0).address
