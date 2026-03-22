"""
SentimentIQ Demo API
Bridges the React frontend to the signal-engine pipeline.

Startup:
    cd Beachhacks-9.0-1
    uvicorn UI.api:app --reload --port 8080
"""

from __future__ import annotations

import asyncio
import math
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any

import httpx
import torch
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from transformers import AutoModelForSequenceClassification, AutoTokenizer

load_dotenv()

# ─── App ───────────────────────────────────────────────────────────
app = FastAPI(title="SentimentIQ Demo API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── FinBERT globals ──────────────────────────────────────────────
finbert_model = None
finbert_tokenizer = None

# ─── Config ────────────────────────────────────────────────────────
NEWSDATA_API_KEY = os.getenv("NEWSDATA_API_KEY", "")

DEMO_TICKERS = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "META", "GOOG", "JPM", "XOM", "UNH"]
TARGET_ARTICLES = 50

TICKER_SECTOR: dict[str, str] = {
    "AAPL": "Technology", "MSFT": "Technology", "NVDA": "Technology",
    "GOOG": "Technology", "META": "Communication",
    "TSLA": "Consumer Disc.", "AMZN": "Consumer Disc.",
    "JPM": "Financials", "GS": "Financials", "BAC": "Financials",
    "XOM": "Energy", "CVX": "Energy",
    "UNH": "Healthcare", "JNJ": "Healthcare", "PFE": "Healthcare",
    "NEE": "Utilities", "DUK": "Utilities",
}

TICKER_COMPANY: dict[str, str] = {
    "AAPL": "Apple Inc.", "MSFT": "Microsoft Corp.", "NVDA": "NVIDIA Corp.",
    "GOOG": "Alphabet Inc.", "META": "Meta Platforms",
    "TSLA": "Tesla Inc.", "AMZN": "Amazon.com Inc.",
    "JPM": "JPMorgan Chase", "GS": "Goldman Sachs", "BAC": "Bank of America",
    "XOM": "Exxon Mobil", "CVX": "Chevron Corp.",
    "UNH": "UnitedHealth Group", "JNJ": "Johnson & Johnson", "PFE": "Pfizer Inc.",
    "NEE": "NextEra Energy", "DUK": "Duke Energy",
}

SECTOR_ABBR: dict[str, str] = {
    "Technology": "TECH", "Healthcare": "HLTH", "Energy": "ENRG",
    "Financials": "FINC", "Consumer Disc.": "CONS", "Utilities": "UTIL",
    "Communication": "COMM",
}

# ─── FinBERT helpers ───────────────────────────────────────────────

@app.on_event("startup")
async def load_finbert():
    global finbert_model, finbert_tokenizer
    print("[api] Loading ProsusAI/finbert …")
    try:
        finbert_tokenizer = AutoTokenizer.from_pretrained("ProsusAI/finbert")
        finbert_model = AutoModelForSequenceClassification.from_pretrained("ProsusAI/finbert")
        finbert_model.eval()
        print("[api] FinBERT loaded.")
    except Exception as exc:
        print(f"[api] WARNING: FinBERT failed to load: {exc}")


def _score_text(text: str) -> dict[str, float]:
    """Synchronous FinBERT inference."""
    if finbert_model is None or finbert_tokenizer is None:
        raise RuntimeError("FinBERT not loaded")
    inputs = finbert_tokenizer(text, return_tensors="pt", truncation=True, max_length=512, padding=True)
    with torch.no_grad():
        probs = torch.nn.functional.softmax(finbert_model(**inputs).logits, dim=-1)[0]
    pos, neg, neu = probs[0].item(), probs[1].item(), probs[2].item()
    score = pos - neg
    confidence = max(pos, neg, neu)
    if score > 0.1:
        direction = "positive"
    elif score < -0.1:
        direction = "negative"
    else:
        direction = "neutral"
    return {"score": score, "confidence": confidence, "direction": direction}


async def score_text_async(text: str) -> dict[str, float]:
    return await asyncio.get_event_loop().run_in_executor(None, _score_text, text)


# ─── NewsData fetcher (relaxed for 50 articles) ───────────────────

async def fetch_articles(tickers: list[str], target: int = 50) -> list[dict]:
    """Fetch up to `target` articles across the given tickers from NewsData.io."""
    if not NEWSDATA_API_KEY:
        print("[api] WARNING: NEWSDATA_API_KEY not set – returning empty")
        return []

    results: list[dict] = []
    per_ticker = max(target // len(tickers), 5)

    async with httpx.AsyncClient(timeout=15) as client:
        for ticker in tickers:
            if len(results) >= target:
                break
            try:
                resp = await client.get(
                    "https://newsdata.io/api/1/news",
                    params={"apikey": NEWSDATA_API_KEY, "q": ticker, "language": "en"},
                )
                data = resp.json()
            except Exception as exc:
                print(f"[api] fetch error for {ticker}: {exc}")
                continue

            articles = data.get("results", [])
            count = 0
            for item in articles:
                if count >= per_ticker or len(results) >= target:
                    break
                title = item.get("title", "")
                desc = item.get("description", "") or ""
                text = f"{title}. {desc}"
                if len(text.strip()) < 20:
                    continue
                results.append({
                    "ticker": ticker,
                    "title": title,
                    "text": text[:512],
                    "url": item.get("link", ""),
                    "source_name": item.get("source_name", item.get("source_id", "newsdata")),
                    "published_at": item.get("pubDate", ""),
                    "scraped_at": datetime.now(timezone.utc).isoformat(),
                    "post_id": str(uuid.uuid4()),
                    "credibility_weight": 0.8,
                })
                count += 1

    print(f"[api] Fetched {len(results)} articles across {len(tickers)} tickers")
    return results


# ─── Aggregation (inline, mirrors fast/aggregator.py) ─────────────

def _recency_decay(scraped_at: str) -> float:
    try:
        dt = datetime.fromisoformat(scraped_at)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        hours = (datetime.now(timezone.utc) - dt).total_seconds() / 3600.0
        return math.exp(-0.5 * max(hours, 0.0))
    except Exception:
        return 1.0


def aggregate_scored(scored: list[dict]) -> dict:
    """Aggregate a list of scored articles for one ticker into a signal dict."""
    if not scored:
        return {}

    ticker = scored[0]["ticker"]
    weights = []
    for s in scored:
        w = s["credibility_weight"] * s["confidence"] * _recency_decay(s["scraped_at"])
        weights.append(w)

    total_w = sum(weights)
    if total_w == 0:
        return {"ticker": ticker, "direction": "HOLD", "aggregate_score": 0, "confidence_pct": 0,
                "signal_strength": "weak", "source_count": len(scored), "forced_hold": True}

    agg_score = sum(s["score"] * w for s, w in zip(scored, weights)) / total_w

    dir_w = {"positive": 0.0, "negative": 0.0, "neutral": 0.0}
    dist = {"positive": 0, "negative": 0, "neutral": 0}
    for s, w in zip(scored, weights):
        d = s["direction"]
        dir_w[d] += w
        dist[d] += 1

    majority = max(dir_w, key=lambda k: dir_w[k])
    conf_pct = round(dir_w[majority] / total_w * 100, 1)

    forced_hold = len(scored) < 3 or conf_pct < 55
    if forced_hold:
        direction = "HOLD"
    elif agg_score >= 0.20:
        direction = "BUY"
    elif agg_score <= -0.20:
        direction = "SELL"
    else:
        direction = "HOLD"

    if conf_pct >= 80:
        strength = "strong"
    elif conf_pct >= 60:
        strength = "moderate"
    else:
        strength = "weak"

    return {
        "ticker": ticker,
        "company": TICKER_COMPANY.get(ticker, ticker),
        "sector": TICKER_SECTOR.get(ticker, "Technology"),
        "direction": direction,
        "aggregate_score": round(agg_score, 4),
        "confidence_pct": conf_pct,
        "signal_strength": strength,
        "source_count": len(scored),
        "score_distribution": dist,
        "majority_direction": majority,
        "forced_hold": forced_hold,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


# ─── Cached result ────────────────────────────────────────────────
_cached_result: dict[str, Any] | None = None

# ─── Endpoints ─────────────────────────────────────────────────────

@app.get("/api/status")
async def status():
    return {"status": "ok", "finbert_loaded": finbert_model is not None}


@app.post("/api/analyze")
async def analyze():
    """
    Full demo pipeline:
    1. Fetch ~50 articles from NewsData across tickers
    2. Score each with FinBERT
    3. Aggregate per-ticker into signals
    4. Return structured data for the frontend
    """
    global _cached_result

    if finbert_model is None:
        return {"error": "FinBERT not loaded yet — wait for startup to complete"}

    # Step 1: Fetch articles
    articles = await fetch_articles(DEMO_TICKERS, TARGET_ARTICLES)
    if not articles:
        return {"error": "No articles fetched — check NEWSDATA_API_KEY"}

    # Step 2: Score with FinBERT
    scored_articles: list[dict] = []
    for art in articles:
        try:
            result = await score_text_async(art["text"])
            scored_articles.append({
                **art,
                "score": result["score"],
                "confidence": result["confidence"],
                "direction": result["direction"],
            })
        except Exception as exc:
            print(f"[api] scoring error: {exc}")
            continue

    print(f"[api] Scored {len(scored_articles)} articles")

    # Step 3: Aggregate per-ticker
    by_ticker: dict[str, list[dict]] = {}
    for s in scored_articles:
        by_ticker.setdefault(s["ticker"], []).append(s)

    signals: list[dict] = []
    for ticker, group in by_ticker.items():
        sig = aggregate_scored(group)
        if sig:
            # Attach supporting sources for detail view
            sig["sources"] = [
                {
                    "source_name": a["source_name"],
                    "title": a["title"],
                    "text": a["text"][:200],
                    "url": a["url"],
                    "score": round(a["score"], 4),
                    "confidence": round(a["confidence"], 4),
                    "direction": a["direction"],
                    "published_at": a["published_at"],
                }
                for a in group
            ]
            signals.append(sig)

    signals.sort(key=lambda s: abs(s["aggregate_score"]), reverse=True)

    # Step 4: Build dashboard featured articles (first 3 strongest-signal articles)
    all_scored_sorted = sorted(scored_articles, key=lambda a: abs(a["score"]), reverse=True)
    featured = []
    seen_tickers = set()
    for art in all_scored_sorted:
        if art["ticker"] not in seen_tickers and len(featured) < 3:
            seen_tickers.add(art["ticker"])
            sig_for_ticker = next((s for s in signals if s["ticker"] == art["ticker"]), None)
            featured.append({
                "ticker": art["ticker"],
                "company": TICKER_COMPANY.get(art["ticker"], art["ticker"]),
                "signal": sig_for_ticker["direction"] if sig_for_ticker else "HOLD",
                "confidence": round(sig_for_ticker["confidence_pct"] if sig_for_ticker else art["confidence"] * 100),
                "title": art["title"],
                "summary": art["text"][:180],
                "source": art["source_name"],
                "url": art["url"],
                "score": round(art["score"], 4),
            })

    # Step 5: Build sector aggregates for markets page
    by_sector: dict[str, list[dict]] = {}
    for sig in signals:
        sector = sig.get("sector", "Technology")
        by_sector.setdefault(sector, []).append(sig)

    sectors: list[dict] = []
    for sector_name, sector_signals in by_sector.items():
        total_score = sum(s["aggregate_score"] for s in sector_signals)
        avg_score = total_score / len(sector_signals)
        avg_conf = sum(s["confidence_pct"] for s in sector_signals) / len(sector_signals)
        bearish_count = sum(1 for s in sector_signals if s["aggregate_score"] < 0)
        bullish_count = sum(1 for s in sector_signals if s["aggregate_score"] > 0)
        neutral_count = len(sector_signals) - bearish_count - bullish_count

        if avg_score >= 0.1:
            sentiment = "BULLISH"
        elif avg_score <= -0.1:
            sentiment = "BEARISH"
        else:
            sentiment = "NEUTRAL"

        constituents = [
            {
                "ticker": s["ticker"],
                "name": s["company"],
                "signal": s["direction"],
                "conf": f"{s['confidence_pct']:.0f}%",
                "score": f"{s['aggregate_score']:+.2f}",
                "change": f"{s['aggregate_score'] * 10:+.2f}%",
            }
            for s in sector_signals
        ]

        sectors.append({
            "name": sector_name,
            "abbr": SECTOR_ABBR.get(sector_name, sector_name[:4].upper()),
            "sentiment": sentiment,
            "confidence": round(avg_conf),
            "impact": f"{avg_score * 10:+.2f}%",
            "avg_score": round(avg_score, 4),
            "stats": {
                "bearish": bearish_count,
                "bullish": bullish_count,
                "neutral": neutral_count,
                "avg_conf": round(avg_conf / 100, 2),
            },
            "constituents": constituents,
        })

    # Step 6: Dashboard stats
    buy_count = sum(1 for s in signals if s["direction"] == "BUY")
    sell_count = sum(1 for s in signals if s["direction"] == "SELL")
    avg_confidence = round(sum(s["confidence_pct"] for s in signals) / max(len(signals), 1))

    # Step 7: Heatmap
    heatmap = []
    for sec in sectors:
        heatmap.append({
            "label": sec["abbr"],
            "value": round(sec["avg_score"] * 100),
        })

    # Step 8: Top movers (biggest absolute score)
    top_movers = sorted(signals, key=lambda s: abs(s["aggregate_score"]), reverse=True)[:3]
    movers_out = [
        {
            "ticker": m["ticker"],
            "abbr": m["ticker"][:2],
            "sector": m["sector"],
            "change": f"{m['aggregate_score'] * 10:+.1f}%",
            "positive": m["aggregate_score"] > 0,
        }
        for m in top_movers
    ]

    result = {
        "total_articles": len(scored_articles),
        "total_tickers": len(signals),
        "featured": featured,
        "signals": signals,
        "sectors": sectors,
        "heatmap": heatmap,
        "top_movers": movers_out,
        "stats": {
            "stocks_tracked": len(signals),
            "strong_buy": buy_count,
            "strong_sell": sell_count,
            "avg_confidence": avg_confidence,
        },
    }

    _cached_result = result
    return result


@app.get("/api/results")
async def get_results():
    """Return cached results from the last analysis run."""
    if _cached_result is None:
        return {"error": "No analysis has been run yet. POST /api/analyze first."}
    return _cached_result
