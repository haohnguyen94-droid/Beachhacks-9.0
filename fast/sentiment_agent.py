# sentiment_agent.py — Stage 5: FinBERT Sentiment Scoring Agent
#
# Three-tier scoring logic:
#   Tier 1 — Every incoming article is scored by FinBERT (ProsusAI/finbert).
#            The model outputs positive/negative/neutral probabilities, which
#            are converted to a scalar score: score = P(pos) - P(neg).
#   Tier 2 — If FinBERT's confidence (max of the three probabilities) falls
#            below 0.70, a secondary call to Claude (Anthropic LLM) re-scores
#            the text. The higher-confidence result wins.
#   Tier 3 — When the final confidence exceeds 0.85, a follow-up LLM call
#            generates a plain-English explanation ("ai_reasoning") for the
#            dashboard's Evidence Drill-Down panel.

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

import anthropic
import torch
from dotenv import load_dotenv
from transformers import AutoModelForSequenceClassification, AutoTokenizer
from uagents import Agent, Context

load_dotenv()

from models import EntityExtracted, SentimentScored

# ---------------------------------------------------------------------------
# Module-level model references (populated on startup)
# ---------------------------------------------------------------------------

finbert_model: AutoModelForSequenceClassification | None = None
finbert_tokenizer: AutoTokenizer | None = None
anthropic_client: anthropic.Anthropic | None = None

# ---------------------------------------------------------------------------
# Agent definition
# ---------------------------------------------------------------------------

SIGNAL_ENGINE_ADDRESS: str = os.getenv("SIGNAL_ENGINE_ADDRESS", "")
SENTIMENT_AGENT_PORT: int = int(os.getenv("SENTIMENT_AGENT_PORT", "8002"))

agent = Agent(
    name="sentiment_agent",
    seed="sentiment_agent_seed_phrase",
    port=SENTIMENT_AGENT_PORT,
    endpoint=[f"http://localhost:{SENTIMENT_AGENT_PORT}/submit"],
)


@agent.on_event("startup")
async def load_models(ctx: Context) -> None:
    global finbert_model, finbert_tokenizer, anthropic_client

    ctx.logger.info(f"Sentiment agent address: {agent.address}")
    ctx.logger.info("Loading ProsusAI/finbert model and tokenizer...")
    try:
        finbert_tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
        finbert_model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
        finbert_model.eval()
        ctx.logger.info("FinBERT loaded successfully.")
    except Exception as exc:
        ctx.logger.error(f"Failed to load FinBERT: {exc}")

    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    if api_key:
        anthropic_client = anthropic.Anthropic(api_key=api_key)
        ctx.logger.info("Anthropic client initialised.")
    else:
        ctx.logger.warning("ANTHROPIC_API_KEY not set — Tier 2/3 LLM calls will be skipped.")


# ---------------------------------------------------------------------------
# Tier 1 — FinBERT scoring
# ---------------------------------------------------------------------------

async def score_with_finbert(context_window: str) -> dict[str, float]:
    """Run *context_window* through FinBERT and return score + confidence."""
    if finbert_model is None or finbert_tokenizer is None:
        raise RuntimeError("FinBERT model is not loaded.")

    inputs = finbert_tokenizer(
        context_window,
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


# ---------------------------------------------------------------------------
# Tier 2 — LLM re-scoring (low-confidence fallback)
# ---------------------------------------------------------------------------

async def score_with_llm(
    context_window: str,
    sentiment_words: list[str],
    keywords: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """Ask Claude for a structured sentiment score.  Returns parsed dict or None on failure."""
    if anthropic_client is None:
        return None

    prompt = (
        "You are a financial-sentiment analyst. Analyse the excerpt below and "
        "return ONLY a JSON object with these fields:\n"
        '  score (float, -1.0 to 1.0),\n'
        '  direction ("positive", "negative", or "neutral"),\n'
        '  confidence (float, 0.0 to 1.0),\n'
        '  reason (string, one sentence max).\n\n'
        "No markdown, no explanation — just the JSON object.\n\n"
        f"Excerpt:\n{context_window}\n\n"
        f"Sentiment words: {sentiment_words}\n"
        f"Keywords: {json.dumps(keywords)}\n"
    )

    try:
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        raw_text: str = response.content[0].text.strip()
        parsed: dict[str, Any] = json.loads(raw_text)

        # Validate required fields
        for field in ("score", "direction", "confidence", "reason"):
            if field not in parsed:
                return None
        return parsed
    except (json.JSONDecodeError, anthropic.APIError, Exception):
        return None


# ---------------------------------------------------------------------------
# Tier 3 — Evidence enrichment
# ---------------------------------------------------------------------------

async def enrich_with_reasoning(
    ticker: str,
    context_window: str,
    direction: str,
) -> str | None:
    """Generate a 2-3 sentence plain-English explanation for the dashboard."""
    if anthropic_client is None:
        return None

    prompt = (
        f"In 2-3 sentences, explain why the stock ticker {ticker} is being "
        f"discussed {'negatively' if direction == 'negative' else 'positively'} "
        f"based on the following excerpt. Be specific and cite details from the text.\n\n"
        f"Excerpt:\n{context_window}"
    )

    try:
        response = anthropic_client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=256,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
    except Exception:
        return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _direction_from_score(score: float) -> str:
    if score > 0.05:
        return "positive"
    if score < -0.05:
        return "negative"
    return "neutral"


# ---------------------------------------------------------------------------
# Message handler
# ---------------------------------------------------------------------------

@agent.on_message(model=EntityExtracted)
async def handle_entity_extracted(ctx: Context, sender: str, msg: EntityExtracted) -> None:
    try:
        # Guard: skip empty or trivially short context
        if not msg.context_window or len(msg.context_window.strip()) < 10:
            ctx.logger.warning(
                f"Skipping {msg.ticker}: context_window is empty or too short "
                f"({len(msg.context_window.strip()) if msg.context_window else 0} chars)."
            )
            return

        # --- Tier 1: FinBERT ---
        try:
            fb = await score_with_finbert(msg.context_window)
        except Exception as exc:
            ctx.logger.error(f"FinBERT error for {msg.ticker}: {exc} — skipping message.")
            return

        finbert_score: float = fb["score"]
        finbert_confidence: float = fb["confidence"]

        final_score = finbert_score
        final_confidence = finbert_confidence
        scoring_tier = 1
        llm_score: float | None = None
        llm_confidence: float | None = None

        # --- Tier 2: LLM re-scoring if FinBERT confidence < 0.70 ---
        if finbert_confidence < 0.70:
            llm_result = await score_with_llm(
                msg.context_window,
                msg.sentiment_words,
                msg.keywords,
            )
            if llm_result is not None:
                llm_score = float(llm_result["score"])
                llm_confidence = float(llm_result["confidence"])
                if llm_confidence > finbert_confidence:
                    final_score = llm_score
                    final_confidence = llm_confidence
                    scoring_tier = 2
                    ctx.logger.info(
                        f"{msg.ticker}: LLM re-score used (FinBERT conf={finbert_confidence:.2f}, "
                        f"LLM conf={llm_confidence:.2f})."
                    )
            else:
                ctx.logger.warning(
                    f"{msg.ticker}: LLM re-score failed — falling back to FinBERT."
                )

        direction = _direction_from_score(final_score)

        # --- Tier 3: Evidence enrichment if final confidence > 0.85 ---
        ai_reasoning: str | None = None
        if final_confidence > 0.85 and direction != "neutral":
            ai_reasoning = await enrich_with_reasoning(
                msg.ticker, msg.context_window, direction,
            )
            if ai_reasoning:
                scoring_tier = 3

        scored_at = datetime.now(timezone.utc).isoformat()

        result = SentimentScored(
            ticker=msg.ticker,
            finbert_score=round(finbert_score, 4),
            finbert_confidence=round(finbert_confidence, 4),
            llm_score=round(llm_score, 4) if llm_score is not None else None,
            llm_confidence=round(llm_confidence, 4) if llm_confidence is not None else None,
            final_score=round(final_score, 4),
            final_confidence=round(final_confidence, 4),
            direction=direction,
            scoring_tier=scoring_tier,
            ai_reasoning=ai_reasoning,
            source_name=msg.source_name,
            credibility_weight=msg.credibility_weight,
            ticker_context=msg.context_window,
            keywords=msg.keywords,
            scraped_at=msg.scraped_at,
            scored_at=scored_at,
        )

        ctx.logger.info(
            f"Scored {msg.ticker}: final_score={result.final_score}, "
            f"direction={result.direction}, confidence={result.final_confidence:.2f}, "
            f"tier={result.scoring_tier}"
        )

        if SIGNAL_ENGINE_ADDRESS:
            await ctx.send(SIGNAL_ENGINE_ADDRESS, result)
        else:
            ctx.logger.warning("SIGNAL_ENGINE_ADDRESS not set — scored message not forwarded.")

    except Exception as exc:
        ctx.logger.error(f"Unhandled error processing {msg.ticker}: {exc}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    agent.run()
