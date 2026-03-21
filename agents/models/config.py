import os
from dotenv import find_dotenv, load_dotenv
from uagents_core.identity import Identity

load_dotenv(find_dotenv())

REDDIT_SEED = os.getenv("REDDIT_SEED_PHRASE")
WALLSTREET_SEED = os.getenv("WALLSTREET_SEED_PHRASE")
X_SEED = os.getenv("X_SEED_PHRASE")
YAHOO_SEED = os.getenv("YAHOO_SEED_PHRASE")
FINANCIAL_SEED = os.getenv("FINANCIAL_SEED_PHRASE")

ORCHESTRATOR_SEED = os.getenv("ORCHESTRATOR_SEED_PHRASE")

REDDIT_ADDRESS = Identity.from_seed(seed=REDDIT_SEED, index=0).address
WALLSTREET_ADDRESS = Identity.from_seed(seed=WALLSTREET_SEED, index=0).address
X_ADDRESS = Identity.from_seed(seed=X_SEED, index=0).address
YAHOO_ADDRESS = Identity.from_seed(seed=YAHOO_SEED, index=0).address
FINANCIAL_ADDRESS = Identity.from_seed(seed=FINANCIAL_SEED, index=0).address