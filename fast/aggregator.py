"""Pure aggregation logic for the Signal Engine.

This module contains no agent or database dependencies — it takes a list of
SentimentScored messages and returns a FinalSignal.  Fully testable in isolation.
"""

from __future__ import annotations

import math
from datetime import datetime, timezone

from models import FinalSignal, SentimentScored, SourceEvidence

# ---------------------------------------------------------------------------
# Configurable thresholds
# ---------------------------------------------------------------------------

STRONG_POSITIVE_THRESHOLD: float = 0.20
STRONG_NEGATIVE_THRESHOLD: float = -0.20
MIN_CONFIDENCE_FOR_SIGNAL: float = 55.0
MIN_SOURCES_FOR_SIGNAL: int = 3
RECENCY_DECAY_LAMBDA: float = 0.5

# ---------------------------------------------------------------------------
# Source category mapping
# ---------------------------------------------------------------------------

SOURCE_CATEGORIES: dict[str, str] = {
    "reuters": "financial_media",
    "bloomberg": "financial_media",
    "cnbc": "financial_media",
    "ft": "financial_media",
    "financial_times": "financial_media",
    "wsj": "financial_media",
    "wallstreetjournal": "financial_media",
    "seeking_alpha": "analyst",
    "seekingalpha": "analyst",
    "motley_fool": "analyst",
    "motleyfool": "analyst",
    "barrons": "analyst",
    "reddit": "social",
    "x": "social",
    "twitter": "social",
    "stocktwits": "social",
    "fred": "macro",
    "bls": "macro",
    "bea": "macro",
    "yahoo_finance": "financial_media",
    "yahoofinance": "financial_media",
}


def _categorize_source(source_name: str) -> str:
    """Map a source name to one of the four categories."""
    return SOURCE_CATEGORIES.get(source_name.lower().replace(" ", "_"), "financial_media")


def _recency_decay(scraped_at: str, now: datetime) -> float:
    """Calculate recency decay factor: e^(-lambda * hours_since_scraped)."""
    try:
        scraped_dt = datetime.fromisoformat(scraped_at)
        if scraped_dt.tzinfo is None:
            scraped_dt = scraped_dt.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return 1.0

    hours_since = (now - scraped_dt).total_seconds() / 3600.0
    if hours_since < 0:
        hours_since = 0.0

    return math.exp(-RECENCY_DECAY_LAMBDA * hours_since)


def _signal_strength(confidence_pct: float) -> str:
    """Map confidence percentage to a strength label."""
    if confidence_pct >= 80.0:
        return "strong"
    if confidence_pct >= 60.0:
        return "moderate"
    return "weak"


def aggregate_signals(messages: list[SentimentScored]) -> FinalSignal:
    """Aggregate a list of SentimentScored messages for a single ticker into a FinalSignal.

    Args:
        messages: All SentimentScored messages for one ticker within the window.

    Returns:
        A FinalSignal with the aggregated score, direction, confidence, and breakdown.
    """
    now = datetime.now(timezone.utc)
    ticker = messages[0].ticker if messages else "UNKNOWN"

    # --- Step 1: compute composite weights ---
    weights: list[float] = []
    for msg in messages:
        decay = _recency_decay(msg.scraped_at, now)
        w = msg.credibility_weight * msg.finbert_confidence * decay
        weights.append(w)

    total_weight = sum(weights)

    # Edge case: all weights are zero
    if total_weight == 0:
        return FinalSignal(
            ticker=ticker,
            direction="HOLD",
            aggregate_score=0.0,
            confidence_pct=0.0,
            signal_strength="weak",
            source_count=len(messages),
            window_start=messages[0].scraped_at if messages else now.isoformat(),
            window_end=messages[-1].scraped_at if messages else now.isoformat(),
            generated_at=now.isoformat(),
            source_breakdown={},
            majority_direction="neutral",
            directional_agreement_pct=0.0,
            score_distribution={"positive": 0, "negative": 0, "neutral": 0},
            forced_hold=True,
            forced_hold_reason="zero_weight",
        )

    # --- Step 2: weighted aggregate score ---
    aggregate_score = sum(
        msg.final_score * w for msg, w in zip(messages, weights)
    ) / total_weight

    # --- Step 3: directional agreement confidence ---
    direction_weights: dict[str, float] = {"positive": 0.0, "negative": 0.0, "neutral": 0.0}
    score_distribution: dict[str, int] = {"positive": 0, "negative": 0, "neutral": 0}

    for msg, w in zip(messages, weights):
        d = msg.direction
        if d in direction_weights:
            direction_weights[d] += w
            score_distribution[d] += 1

    majority_direction = max(direction_weights, key=lambda k: direction_weights[k])
    directional_weight = direction_weights[majority_direction] / total_weight
    confidence_pct = round(directional_weight * 100, 1)

    # --- Step 4: BUY / SELL / HOLD classification ---
    forced_hold = False
    forced_hold_reason: str | None = None

    if len(messages) < MIN_SOURCES_FOR_SIGNAL:
        forced_hold = True
        forced_hold_reason = "insufficient_sources"
    elif confidence_pct < MIN_CONFIDENCE_FOR_SIGNAL:
        forced_hold = True
        forced_hold_reason = "low_confidence"

    if forced_hold:
        direction = "HOLD"
    elif aggregate_score >= STRONG_POSITIVE_THRESHOLD:
        direction = "BUY"
    elif aggregate_score <= STRONG_NEGATIVE_THRESHOLD:
        direction = "SELL"
    else:
        direction = "HOLD"

    # --- Step 5: source breakdown ---
    category_data: dict[str, dict] = {}
    for msg, w in zip(messages, weights):
        cat = _categorize_source(msg.source_name)
        if cat not in category_data:
            category_data[cat] = {"count": 0, "weighted_score_sum": 0.0, "weight_sum": 0.0}
        category_data[cat]["count"] += 1
        category_data[cat]["weighted_score_sum"] += msg.final_score * w
        category_data[cat]["weight_sum"] += w

    source_breakdown: dict[str, dict] = {}
    for cat, data in category_data.items():
        avg_score = data["weighted_score_sum"] / data["weight_sum"] if data["weight_sum"] > 0 else 0.0
        weight_pct = round((data["weight_sum"] / total_weight) * 100, 1)
        source_breakdown[cat] = {
            "count": data["count"],
            "avg_weighted_score": round(avg_score, 4),
            "weight_pct": weight_pct,
        }

    # --- Step 6: build supporting sources (sorted by weight, highest first) ---
    evidence = []
    for msg, w in zip(messages, weights):
        evidence.append((w, SourceEvidence(
            source_name=msg.source_name,
            source_category=_categorize_source(msg.source_name),
            text=msg.text,
            sentiment_score=round(msg.finbert_score, 4),
            sentiment_direction=msg.direction,
            confidence=round(msg.finbert_confidence, 4),
            credibility_weight=msg.credibility_weight,
            scraped_at=msg.scraped_at,
            post_id=msg.post_id,
        )))
    evidence.sort(key=lambda x: x[0], reverse=True)
    supporting_sources = [e for _, e in evidence]

    # --- Window timestamps ---
    scraped_times = [msg.scraped_at for msg in messages]
    window_start = min(scraped_times)
    window_end = max(scraped_times)

    return FinalSignal(
        ticker=ticker,
        direction=direction,
        aggregate_score=round(aggregate_score, 4),
        confidence_pct=confidence_pct,
        signal_strength=_signal_strength(confidence_pct),
        source_count=len(messages),
        window_start=window_start,
        window_end=window_end,
        generated_at=now.isoformat(),
        source_breakdown=source_breakdown,
        majority_direction=majority_direction,
        directional_agreement_pct=confidence_pct,
        score_distribution=score_distribution,
        forced_hold=forced_hold,
        forced_hold_reason=forced_hold_reason,
        supporting_sources=supporting_sources,
    )
