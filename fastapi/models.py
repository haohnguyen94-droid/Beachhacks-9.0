from __future__ import annotations

from uagents import Model

class EntityExtracted(Model):
    """Output of the NLP/SpaCy agent — input to the Sentiment scoring agent."""
    ticker: str
    company_name: str
    context_window: str
    ner_entities: list
    sentiment_words: list
    keywords: list
    entity_verb_pairs: list
    source_name: str
    credibility_weight: float
    scraped_at: str


class SentimentScored(Model):
    """Output of the Sentiment agent — input to the Signal Engine agent."""
    ticker: str
    finbert_score: float
    finbert_confidence: float
    llm_score: float | None = None
    llm_confidence: float | None = None
    final_score: float
    final_confidence: float
    direction: str
    scoring_tier: int
    ai_reasoning: str | None = None
    source_name: str
    credibility_weight: float
    ticker_context: str
    keywords: list
    scraped_at: str
    scored_at: str
