from uagents import Model


class ScraperOutput(Model):
    """Output of the scraper agents — input to the Sentiment scoring agent."""
    ticker: str
    text: str
    source_name: str
    credibility_weight: float
    scraped_at: str
    post_id: str = ""
    source_type: str = ""
    title: str = ""
    url: str = ""
    published_at: str = ""
    raw_payload: dict = {}


class SharedAgentState(Model):
    chat_session_id: str
    query: str                      # ticker symbol (e.g. "AAPL")
    user_sender_address: str
    result: str = ""
    source_agent: str = ""
    posts_sent: int = 0


class AggregateRequest(Model):
    """Sent by the orchestrator to the signal engine to trigger immediate aggregation."""
    ticker: str
    chat_session_id: str
    requester_address: str


class SentimentScored(Model):
    """Output of the Sentiment agent — input to the Signal Engine."""
    ticker: str
    finbert_score: float
    finbert_confidence: float
    final_score: float
    final_confidence: float
    direction: str
    source_name: str
    credibility_weight: float
    text: str
    scraped_at: str
    scored_at: str
    post_id: str = ""


class SourceEvidence(Model):
    """A single source that contributed to the signal."""
    source_name: str
    source_category: str
    text: str
    sentiment_score: float
    sentiment_direction: str
    confidence: float
    credibility_weight: float
    scraped_at: str
    post_id: str = ""


class FinalSignal(Model):
    """Output of the Signal Engine — the end result sent back to orchestrator."""
    ticker: str
    direction: str
    aggregate_score: float
    confidence_pct: float
    signal_strength: str
    source_count: int
    window_start: str
    window_end: str
    generated_at: str
    source_breakdown: dict
    majority_direction: str
    directional_agreement_pct: float
    score_distribution: dict
    forced_hold: bool
    forced_hold_reason: str | None = None
    supporting_sources: list[SourceEvidence] = []
