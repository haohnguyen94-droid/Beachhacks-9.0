"""Tests for the signal aggregation logic."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest

from fast.aggregator import aggregate_signals, RECENCY_DECAY_LAMBDA
from fast.models import SentimentScored

# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _hours_ago(hours: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()


def _make_msg(
    ticker: str = "TSLA",
    score: float = 0.5,
    confidence: float = 0.9,
    direction: str = "positive",
    source: str = "reuters",
    cred: float = 0.90,
    scraped_hours_ago: float = 0.0,
) -> SentimentScored:
    return SentimentScored(
        ticker=ticker,
        finbert_score=score,
        finbert_confidence=confidence,
        final_score=score,
        final_confidence=confidence,
        direction=direction,
        source_name=source,
        credibility_weight=cred,
        text="Test article text.",
        scraped_at=_hours_ago(scraped_hours_ago),
        scored_at=_now_iso(),
        post_id="test_123",
    )


# ---------------------------------------------------------------------------
# Test A — Majority negative → SELL with high confidence
# ---------------------------------------------------------------------------

def test_majority_negative_produces_sell() -> None:
    msgs = [
        _make_msg(score=-0.7, confidence=0.92, direction="negative", source="reuters"),
        _make_msg(score=-0.6, confidence=0.88, direction="negative", source="bloomberg"),
        _make_msg(score=-0.8, confidence=0.95, direction="negative", source="cnbc"),
        _make_msg(score=0.1, confidence=0.60, direction="positive", source="reddit", cred=0.55),
    ]
    signal = aggregate_signals(msgs)

    assert signal.direction == "SELL"
    assert signal.aggregate_score < -0.20
    assert signal.confidence_pct > 55.0
    assert signal.majority_direction == "negative"
    assert signal.forced_hold is False


# ---------------------------------------------------------------------------
# Test B — Majority positive → BUY with high confidence
# ---------------------------------------------------------------------------

def test_majority_positive_produces_buy() -> None:
    msgs = [
        _make_msg(score=0.7, confidence=0.90, direction="positive", source="wsj"),
        _make_msg(score=0.6, confidence=0.85, direction="positive", source="bloomberg"),
        _make_msg(score=0.8, confidence=0.93, direction="positive", source="reuters"),
    ]
    signal = aggregate_signals(msgs)

    assert signal.direction == "BUY"
    assert signal.aggregate_score >= 0.20
    assert signal.confidence_pct > 55.0
    assert signal.forced_hold is False


# ---------------------------------------------------------------------------
# Test C — Mixed signals → HOLD
# ---------------------------------------------------------------------------

def test_mixed_signals_produce_hold() -> None:
    msgs = [
        _make_msg(score=0.5, confidence=0.85, direction="positive", source="reuters"),
        _make_msg(score=-0.5, confidence=0.85, direction="negative", source="bloomberg"),
        _make_msg(score=0.02, confidence=0.80, direction="neutral", source="cnbc"),
    ]
    signal = aggregate_signals(msgs)

    assert signal.direction == "HOLD"
    assert signal.forced_hold is False


# ---------------------------------------------------------------------------
# Test D — Fewer than MIN_SOURCES → forced HOLD
# ---------------------------------------------------------------------------

def test_insufficient_sources_forces_hold() -> None:
    msgs = [
        _make_msg(score=-0.9, confidence=0.95, direction="negative", source="reuters"),
        _make_msg(score=-0.8, confidence=0.93, direction="negative", source="bloomberg"),
    ]
    signal = aggregate_signals(msgs)

    assert signal.direction == "HOLD"
    assert signal.forced_hold is True
    assert signal.forced_hold_reason == "insufficient_sources"


# ---------------------------------------------------------------------------
# Test E — Recency decay down-weights old articles
# ---------------------------------------------------------------------------

def test_recency_decay_favors_recent() -> None:
    # One recent positive, one old negative (6 hours ago, heavily decayed)
    msgs = [
        _make_msg(score=0.6, confidence=0.90, direction="positive", source="reuters",
                  scraped_hours_ago=0.0),
        _make_msg(score=0.6, confidence=0.90, direction="positive", source="bloomberg",
                  scraped_hours_ago=0.0),
        _make_msg(score=0.6, confidence=0.90, direction="positive", source="cnbc",
                  scraped_hours_ago=0.0),
        _make_msg(score=-0.9, confidence=0.95, direction="negative", source="wsj",
                  scraped_hours_ago=6.0),  # decayed to ~5% weight
    ]
    signal = aggregate_signals(msgs)

    # The old negative should barely affect the score — result should still be BUY
    assert signal.direction == "BUY"
    assert signal.aggregate_score > 0.20


# ---------------------------------------------------------------------------
# Test F — Source breakdown grouping
# ---------------------------------------------------------------------------

def test_source_breakdown_grouping() -> None:
    msgs = [
        _make_msg(score=0.5, confidence=0.90, direction="positive", source="reuters"),
        _make_msg(score=0.4, confidence=0.85, direction="positive", source="bloomberg"),
        _make_msg(score=-0.3, confidence=0.80, direction="negative", source="reddit"),
    ]
    signal = aggregate_signals(msgs)

    assert "financial_media" in signal.source_breakdown
    assert "social" in signal.source_breakdown
    assert signal.source_breakdown["financial_media"]["count"] == 2
    assert signal.source_breakdown["social"]["count"] == 1

    # Weight percentages should sum to ~100%
    total_pct = sum(cat["weight_pct"] for cat in signal.source_breakdown.values())
    assert 99.0 <= total_pct <= 101.0
