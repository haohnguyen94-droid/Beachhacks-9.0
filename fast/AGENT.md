# SentimentIQ — Agent Architecture

## Overview

SentimentIQ is a financial sentiment analysis platform that scrapes posts and articles from major financial sources, scores them using FinBERT, and aggregates the results into BUY / SELL / HOLD signals.

## Pipeline

```
Scraper Agents (port 8000-8001)
    │
    │  ScraperOutput { ticker, text, source_name, credibility_weight, scraped_at }
    ▼
Sentiment Agent (port 8002)
    │
    │  SentimentScored { ticker, finbert_score, direction, confidence, ... }
    ▼
Signal Engine (port 8003)
    │
    │  FinalSignal { ticker, direction: BUY/SELL/HOLD, confidence_pct, ... }
    ▼
Dashboard / PostgreSQL
```

## Agents

### Sentiment Agent (`sentiment_agent.py`)

- **Receives:** `ScraperOutput` from scraper agents
- **Produces:** `SentimentScored` sent to Signal Engine
- **Model:** ProsusAI/finbert (loaded once on startup, ~438MB)
- **Logic:** Runs raw text through FinBERT, outputs a score (-1.0 to +1.0) and confidence (0.0 to 1.0)
- **Port:** 8002 (configurable via `SENTIMENT_AGENT_PORT`)

### Signal Engine (`signal_engine.py`)

- **Receives:** `SentimentScored` from Sentiment Agent
- **Produces:** `FinalSignal` sent to Dashboard Agent and written to PostgreSQL
- **Logic:**
  1. Buffers incoming scores per ticker for 15 minutes
  2. Computes weighted aggregate: `credibility × confidence × recency_decay`
  3. Measures directional agreement across sources for confidence %
  4. Outputs BUY (score >= 0.20), SELL (score <= -0.20), or HOLD
  5. Forces HOLD if fewer than 3 sources or confidence < 55%
- **Port:** 8003 (configurable via `SIGNAL_ENGINE_PORT`)

## Shared Models (`models.py`)

All agents import from `models.py` to ensure message compatibility:

| Model | From | To |
|-------|------|----|
| `ScraperOutput` | Scrapers | Sentiment Agent |
| `SentimentScored` | Sentiment Agent | Signal Engine |
| `FinalSignal` | Signal Engine | Dashboard / DB |

## Files

```
fast/
├── models.py              # Shared Pydantic message models
├── sentiment_agent.py     # FinBERT scoring agent
├── signal_engine.py       # Aggregation + BUY/SELL/HOLD engine
├── aggregator.py          # Pure aggregation logic (no agent deps)
├── test_aggregator.py     # Tests for aggregation logic
├── requirements.txt       # Pinned dependencies
├── .env                   # Environment variables (gitignored)
└── main.py                # FastAPI server (standalone)
```

## Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `SENTIMENT_AGENT_PORT` | No | 8002 | Port for the sentiment agent |
| `SIGNAL_ENGINE_ADDRESS` | Yes* | — | Address of the signal engine agent |
| `SIGNAL_ENGINE_PORT` | No | 8003 | Port for the signal engine |
| `DASHBOARD_AGENT_ADDRESS` | No | — | Address of the dashboard agent |
| `DATABASE_URL` | No | — | PostgreSQL connection string |
| `AGGREGATION_INTERVAL` | No | 900.0 | Seconds between aggregation runs |
| `ANTHROPIC_API_KEY` | No | — | For future LLM tier (not currently used) |

*Required for sentiment agent to forward scores to signal engine.

## Setup

```bash
cd fast
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Running

Terminal 1 — start signal engine first:
```bash
cd fast && source venv/bin/activate
python signal_engine.py
# Copy the logged address → paste into .env as SIGNAL_ENGINE_ADDRESS
```

Terminal 2 — start sentiment agent:
```bash
cd fast && source venv/bin/activate
python sentiment_agent.py
# Copy the logged address → give to scraper agents
```

## Testing

```bash
cd fast && source venv/bin/activate
pytest test_aggregator.py -v
```

## Source Credibility Weights

Scrapers should assign these weights when sending `ScraperOutput`:

| Source | Weight | Category |
|--------|--------|----------|
| Reuters, Bloomberg, WSJ, FT | 0.90-0.95 | financial_media |
| CNBC, Yahoo Finance | 0.80-0.85 | financial_media |
| Seeking Alpha, Motley Fool | 0.70-0.75 | analyst |
| Reddit, X, StockTwits | 0.50-0.60 | social |

## Signal Thresholds

| Condition | Result |
|-----------|--------|
| Score >= 0.20 and confidence >= 55% and sources >= 3 | **BUY** |
| Score <= -0.20 and confidence >= 55% and sources >= 3 | **SELL** |
| Everything else | **HOLD** |
| Confidence < 55% | Forced **HOLD** |
| Sources < 3 | Forced **HOLD** |
