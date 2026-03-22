# Using ProsusAI's FinBERT agent, return a score based on sentiment
# Returns a confidence score and probabilities of an article being
# positive/negative/neutral

from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone

import torch
from dotenv import load_dotenv
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from uagents import Agent, Context

load_dotenv()

from models import ScraperOutput, SentimentScored

# Model references

finbert_model: AutoModelForSequenceClassification | None = None
finbert_tokenizer: AutoTokenizer | None = None

# Agent initialization

SIGNAL_ENGINE_ADDRESS: str = os.getenv("SIGNAL_ENGINE_ADDRESS", "")
SENTIMENT_AGENT_PORT: int = int(os.getenv("SENTIMENT_AGENT_PORT", "8002"))
SENTIMENT_AGENT_SEED: str = os.getenv("SENTIMENT_AGENT_SEED", "sentiment_agent_seed_phrase")

agent = Agent(
    name="sentiment_agent",
    seed=SENTIMENT_AGENT_SEED,
    port=SENTIMENT_AGENT_PORT,
    endpoint=[f"http://localhost:{SENTIMENT_AGENT_PORT}/submit"],
    mailbox=True,
    publish_agent_details=True,
    network="testnet",
)


@agent.on_event("startup")
async def load_models(ctx: Context) -> None:
    global finbert_model, finbert_tokenizer

    ctx.logger.info(f"Sentiment agent address: {agent.address}")
    ctx.logger.info("Loading ProsusAI/finbert model and tokenizer...")
    try:
        finbert_tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
        finbert_model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
        finbert_model.eval()
        ctx.logger.info("FinBERT loaded successfully.")
    except Exception as exc:
        ctx.logger.error(f"Failed to load FinBERT: {exc}")


# FinBERT Model Scoring

def _run_finbert(text: str) -> dict[str, float]:
    """Synchronous FinBERT inference — runs in a thread to avoid blocking."""
    inputs = finbert_tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        max_length=512,
        padding=True,
    )

    with torch.no_grad():
        outputs = finbert_model(**inputs)
        probabilities = torch.nn.functional.softmax(outputs.logits, dim=-1)[0]

    # FinBERT label order: positive, negative, neutral
    positive_prob: float = probabilities[0].item()
    negative_prob: float = probabilities[1].item()
    neutral_prob: float = probabilities[2].item()

    score = positive_prob - negative_prob
    confidence = max(positive_prob, negative_prob, neutral_prob)

    return {"score": score, "confidence": confidence}


async def score_with_finbert(text: str) -> dict[str, float]:
    """Run text through FinBERT in a thread so the event loop stays free."""
    if finbert_model is None or finbert_tokenizer is None:
        raise RuntimeError("FinBERT model is not loaded.")

    return await asyncio.get_event_loop().run_in_executor(None, _run_finbert, text)


# Helper functions

def _direction_from_score(score: float) -> str:
    if score > 0.1:
        return "positive"
    if score < -0.1:
        return "negative"
    return "neutral"


# Message handler

@agent.on_message(model=ScraperOutput)
async def handle_scraper_output(ctx: Context, sender: str, msg: ScraperOutput) -> None:
    try:
        # Guard: skip empty or trivially short text
        if not msg.text or len(msg.text.strip()) < 10:
            ctx.logger.warning(
                f"Skipping {msg.ticker}: text is empty or too short "
                f"({len(msg.text.strip()) if msg.text else 0} chars)."
            )
            return

        # FinBERT scoring
        try:
            fb = await score_with_finbert(msg.text)
        except Exception as exc:
            ctx.logger.error(f"FinBERT error for {msg.ticker}: {exc} — skipping message.")
            return

        finbert_score: float = fb["score"]
        finbert_confidence: float = fb["confidence"]
        direction = _direction_from_score(finbert_score)
        scored_at = datetime.now(timezone.utc).isoformat()

        # FinBERT's Sentiment Score
        result = SentimentScored(
            ticker=msg.ticker,
            finbert_score=round(finbert_score, 4),
            finbert_confidence=round(finbert_confidence, 4),
            final_score=round(finbert_score, 4),
            final_confidence=round(finbert_confidence, 4),
            direction=direction,
            source_name=msg.source_name,
            credibility_weight=msg.credibility_weight,
            text=msg.text,
            scraped_at=msg.scraped_at,
            scored_at=scored_at,
            post_id=msg.post_id,
        )

        ctx.logger.info(
            f"Scored {msg.ticker}: score={result.final_score}, "
            f"direction={result.direction}, confidence={result.final_confidence:.2f}"
        )

        # Send the result to the signal engine
        if SIGNAL_ENGINE_ADDRESS:
            await ctx.send(SIGNAL_ENGINE_ADDRESS, result)
        else:
            ctx.logger.warning("SIGNAL_ENGINE_ADDRESS not set — scored message not forwarded.")

    except Exception as exc:
        ctx.logger.error(f"Unhandled error processing {msg.ticker}: {exc}")


# Run program
if __name__ == "__main__":
    agent.run()
