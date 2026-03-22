from __future__ import annotations

from uagents import Model


class ScraperOutput(Model):
    """Output of the scraper agents — input to the Sentiment scoring agent."""
    ticker: str
    text: str                       # raw post/article text
    source_name: str                # "reddit", "wsj", "financial_times", "yahoo_finance"
    credibility_weight: float       # 0.50-0.95 depending on source
    scraped_at: str
    post_id: str = ""
    source_type: str = ""           # "news", "market_data", "social"
    title: str = ""
    url: str = ""
    published_at: str = ""
    raw_payload: dict = {}


class AggregateRequest(Model):
    """Sent by the orchestrator to the signal engine to trigger immediate aggregation."""
    ticker: str
    chat_session_id: str
    requester_address: str          # where to send the FinalSignal back


class SentimentScored(Model):
    """Output of the Sentiment agent — input to the Signal Engine agent."""
    ticker: str
    finbert_score: float
    finbert_confidence: float
    final_score: float
    final_confidence: float
    direction: str                  # "positive", "negative", "neutral"
    source_name: str
    credibility_weight: float
    text: str                       # original text that was scored
    scraped_at: str
    scored_at: str
    post_id: str = ""


class SourceEvidence(Model):
    """A single source that contributed to the signal — shown to the user as supporting evidence."""
    source_name: str                    # "reuters", "reddit", etc.
    source_category: str                # "financial_media", "analyst", "social", "macro"
    text: str                           # original article/post text (or snippet)
    sentiment_score: float              # individual FinBERT score, -1.0 to +1.0
    sentiment_direction: str            # "positive", "negative", "neutral"
    confidence: float                   # FinBERT confidence, 0.0 to 1.0
    credibility_weight: float           # source credibility, 0.50-0.95
    scraped_at: str
    post_id: str = ""


class FinalSignal(Model):
    """Output of the Signal Engine — sent to dashboard and written to DB."""
    ticker: str
    direction: str                      # "BUY", "SELL", "HOLD"
    aggregate_score: float              # weighted mean, -1.0 to +1.0
    confidence_pct: float               # 0.0 to 100.0
    signal_strength: str                # "strong", "moderate", "weak"
    source_count: int
    window_start: str
    window_end: str
    generated_at: str
    source_breakdown: dict              # per-category counts, scores, weight %
    majority_direction: str             # "positive", "negative", "neutral"
    directional_agreement_pct: float
    score_distribution: dict            # {"positive": N, "negative": N, "neutral": N}
    forced_hold: bool
    forced_hold_reason: str | None = None
    supporting_sources: list[SourceEvidence] = []  # individual sources for user transparency
