"""Tests for sentiment_agent.py — covers all three tiers plus edge cases."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio

from fast.sentiment_agent import sentiment_agent
from fast.models import EntityExtracted
from fast.sentiment_agent import (
    _direction_from_score,
    enrich_with_reasoning,
    handle_entity_extracted,
    score_with_finbert,
    score_with_llm,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _load_finbert() -> None:
    """Ensure FinBERT is loaded once for the test session."""
    if sentiment_agent.finbert_model is None:
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        sentiment_agent.finbert_tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
        sentiment_agent.finbert_model = AutoModelForSequenceClassification.from_pretrained(
            "ProsusAI/finbert"
        )
        sentiment_agent.finbert_model.eval()


def _make_entity(context_window: str, ticker: str = "AAPL") -> EntityExtracted:
    return EntityExtracted(
        ticker=ticker,
        company_name="Apple Inc.",
        context_window=context_window,
        ner_entities=["Apple"],
        sentiment_words=["surged", "record"],
        keywords=[{"term": "revenue growth", "score": 0.91}],
        entity_verb_pairs=[["Apple", "surged"]],
        source_name="Reuters",
        credibility_weight=0.90,
        scraped_at="2025-06-01T12:00:00Z",
    )


def _mock_ctx() -> MagicMock:
    ctx = MagicMock()
    ctx.logger = MagicMock()
    ctx.send = AsyncMock()
    return ctx


# ---------------------------------------------------------------------------
# Test A — Clearly negative financial sentence
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_finbert_negative_sentence() -> None:
    text = (
        "The company reported a massive loss in quarterly earnings, revenue plunged "
        "by 40%, and management issued a profit warning for the next fiscal year."
    )
    result = await score_with_finbert(text)

    assert result["score"] < 0.0, "Expected a negative score for a bearish sentence."
    assert 0.0 <= result["confidence"] <= 1.0


# ---------------------------------------------------------------------------
# Test B — Clearly positive financial sentence
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_finbert_positive_sentence() -> None:
    text = (
        "Apple reported record-breaking revenue of $120 billion, beating analyst "
        "expectations by a wide margin while announcing a major share buyback programme."
    )
    result = await score_with_finbert(text)

    assert result["score"] > 0.0, "Expected a positive score for a bullish sentence."
    assert 0.0 <= result["confidence"] <= 1.0


# ---------------------------------------------------------------------------
# Test C — LLM fallback triggers when FinBERT confidence < 0.70
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_llm_fallback_on_low_confidence() -> None:
    """Simulate a low-confidence FinBERT result and verify the handler calls the LLM."""
    msg = _make_entity(
        "The outlook for the semiconductor sector remains uncertain amid mixed signals "
        "from both trade negotiations and consumer-demand forecasts."
    )
    ctx = _mock_ctx()

    low_conf_finbert = {"score": 0.02, "confidence": 0.45}
    llm_response = {
        "score": -0.3,
        "direction": "negative",
        "confidence": 0.80,
        "reason": "Trade uncertainty weighs on semiconductor outlook.",
    }

    with (
        patch("sentiment_agent.score_with_finbert", return_value=low_conf_finbert) as fb_mock,
        patch("sentiment_agent.score_with_llm", return_value=llm_response) as llm_mock,
        patch("sentiment_agent.enrich_with_reasoning", return_value=None),
        patch("sentiment_agent.SIGNAL_ENGINE_ADDRESS", ""),
    ):
        await handle_entity_extracted(ctx, "sender_address", msg)

        fb_mock.assert_called_once()
        llm_mock.assert_called_once()

        # The handler should have logged a Tier 2 decision
        log_calls = [str(c) for c in ctx.logger.info.call_args_list]
        combined = " ".join(log_calls)
        assert "tier=2" in combined, "Expected scoring_tier=2 when LLM confidence beats FinBERT."


# ---------------------------------------------------------------------------
# Test D — Empty context_window is skipped gracefully
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_empty_context_window_skipped() -> None:
    msg = _make_entity(context_window="", ticker="MSFT")
    ctx = _mock_ctx()

    with patch("sentiment_agent.SIGNAL_ENGINE_ADDRESS", ""):
        await handle_entity_extracted(ctx, "sender_address", msg)

    ctx.logger.warning.assert_called()
    warning_text = str(ctx.logger.warning.call_args)
    assert "Skipping" in warning_text or "empty" in warning_text.lower()
    ctx.send.assert_not_called()


# ---------------------------------------------------------------------------
# Test E — direction helper
# ---------------------------------------------------------------------------

def test_direction_from_score() -> None:
    assert _direction_from_score(0.5) == "positive"
    assert _direction_from_score(-0.3) == "negative"
    assert _direction_from_score(0.01) == "neutral"
    assert _direction_from_score(-0.02) == "neutral"
