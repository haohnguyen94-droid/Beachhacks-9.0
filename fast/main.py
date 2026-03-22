from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(title="SentimentIQ Dashboard API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory signal store
signals: list[dict[str, Any]] = []


# Pydantic model for receiving signals via POST
class SignalPayload(BaseModel):
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


@app.get("/")
def root():
    return {"status": "running", "signals_count": len(signals)}


@app.post("/signals")
def receive_signal(payload: SignalPayload):
    """Receives a FinalSignal from the Signal Engine."""
    signals.append(payload.model_dump())
    return {"status": "received", "ticker": payload.ticker, "direction": payload.direction}


@app.get("/signals")
def get_signals():
    """Returns all signals, most recent first."""
    return sorted(signals, key=lambda s: s["generated_at"], reverse=True)


@app.get("/signals/latest")
def get_latest_signals():
    """Returns the most recent signal per ticker."""
    latest: dict[str, dict] = {}
    for s in signals:
        ticker = s["ticker"]
        if ticker not in latest or s["generated_at"] > latest[ticker]["generated_at"]:
            latest[ticker] = s
    return list(latest.values())


@app.get("/signals/ticker/{ticker}")
def get_signals_by_ticker(ticker: str):
    """Returns all signals for a specific ticker."""
    ticker_upper = ticker.upper()
    return [s for s in signals if s["ticker"] == ticker_upper]
