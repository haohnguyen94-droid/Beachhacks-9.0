# Signal Engine — aggregates FinBERT sentiment scores per ticker over a
# configurable window and produces a BUY / SELL / HOLD signal with confidence %.

from __future__ import annotations

import asyncio
import json
import os

import httpx
from dotenv import load_dotenv
from uagents import Agent, Context

load_dotenv()

from aggregator import aggregate_signals
from models import AggregateRequest, FinalSignal, SentimentScored

# Agent initialization

DASHBOARD_URL: str = os.getenv("DASHBOARD_URL", "http://localhost:8000")
DATABASE_URL: str = os.getenv("DATABASE_URL", "")
SIGNAL_ENGINE_PORT: int = int(os.getenv("SIGNAL_ENGINE_PORT", "8003"))
AGGREGATION_INTERVAL: float = float(os.getenv("AGGREGATION_INTERVAL", "900.0"))
SIGNAL_ENGINE_SEED: str = os.getenv("SIGNAL_ENGINE_SEED", "signal_engine_seed_phrase")

agent = Agent(
    name="signal_engine",
    seed=SIGNAL_ENGINE_SEED,
    port=SIGNAL_ENGINE_PORT,
    endpoint=[f"http://localhost:{SIGNAL_ENGINE_PORT}/submit"],
    mailbox=True,
    publish_agent_details=True,
    network="testnet",
)

# Buffer: ticker -> list of SentimentScored messages
message_buffer: dict[str, list[SentimentScored]] = {}
buffer_locks: dict[str, asyncio.Lock] = {}
seen_post_ids: dict[str, set[str]] = {}


def _get_lock(ticker: str) -> asyncio.Lock:
    """Get or create a lock for a ticker."""
    if ticker not in buffer_locks:
        buffer_locks[ticker] = asyncio.Lock()
    return buffer_locks[ticker]


# Send signal to dashboard API

async def send_to_dashboard(signal: FinalSignal) -> None:
    """POST a FinalSignal to the FastAPI dashboard."""
    payload = {
        "ticker": signal.ticker,
        "direction": signal.direction,
        "aggregate_score": signal.aggregate_score,
        "confidence_pct": signal.confidence_pct,
        "signal_strength": signal.signal_strength,
        "source_count": signal.source_count,
        "window_start": signal.window_start,
        "window_end": signal.window_end,
        "generated_at": signal.generated_at,
        "source_breakdown": signal.source_breakdown,
        "majority_direction": signal.majority_direction,
        "directional_agreement_pct": signal.directional_agreement_pct,
        "score_distribution": signal.score_distribution,
        "forced_hold": signal.forced_hold,
        "forced_hold_reason": signal.forced_hold_reason,
        "supporting_sources": [
            {
                "source_name": s.source_name,
                "source_category": s.source_category,
                "text": s.text,
                "sentiment_score": s.sentiment_score,
                "sentiment_direction": s.sentiment_direction,
                "confidence": s.confidence,
                "credibility_weight": s.credibility_weight,
                "scraped_at": s.scraped_at,
                "post_id": s.post_id,
            }
            for s in signal.supporting_sources
        ],
    }
    async with httpx.AsyncClient() as client:
        await client.post(f"{DASHBOARD_URL}/signals", json=payload)


# Database write

async def write_to_db(signal: FinalSignal) -> None:
    """Write a FinalSignal to PostgreSQL via asyncpg. Fails gracefully."""
    if not DATABASE_URL:
        return

    try:
        import asyncpg
    except ImportError:
        return

    try:
        conn = await asyncpg.connect(DATABASE_URL)
        await conn.execute(
            """
            INSERT INTO signals (
                ticker, direction, aggregate_score, confidence_pct,
                signal_strength, source_count, window_start, window_end,
                generated_at, source_breakdown, majority_direction,
                directional_agreement_pct, score_distribution,
                forced_hold, forced_hold_reason
            ) VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10::jsonb,$11,$12,$13::jsonb,$14,$15)
            ON CONFLICT (ticker, window_start) DO UPDATE SET
                direction = EXCLUDED.direction,
                aggregate_score = EXCLUDED.aggregate_score,
                confidence_pct = EXCLUDED.confidence_pct,
                signal_strength = EXCLUDED.signal_strength,
                source_count = EXCLUDED.source_count,
                window_end = EXCLUDED.window_end,
                generated_at = EXCLUDED.generated_at,
                source_breakdown = EXCLUDED.source_breakdown,
                majority_direction = EXCLUDED.majority_direction,
                directional_agreement_pct = EXCLUDED.directional_agreement_pct,
                score_distribution = EXCLUDED.score_distribution,
                forced_hold = EXCLUDED.forced_hold,
                forced_hold_reason = EXCLUDED.forced_hold_reason
            """,
            signal.ticker, signal.direction, signal.aggregate_score,
            signal.confidence_pct, signal.signal_strength, signal.source_count,
            signal.window_start, signal.window_end, signal.generated_at,
            json.dumps(signal.source_breakdown), signal.majority_direction,
            signal.directional_agreement_pct, json.dumps(signal.score_distribution),
            signal.forced_hold, signal.forced_hold_reason,
        )
        await conn.close()
    except Exception as exc:
        raise exc


# Startup

@agent.on_event("startup")
async def startup(ctx: Context) -> None:
    ctx.logger.info(f"Signal engine address: {agent.address}")
    ctx.logger.info(f"Aggregation interval: {AGGREGATION_INTERVAL}s")
    ctx.logger.info(f"Dashboard URL: {DASHBOARD_URL}")
    if DATABASE_URL:
        ctx.logger.info("DATABASE_URL set — will write signals to PostgreSQL.")
    else:
        ctx.logger.warning("DATABASE_URL not set — signals will not be persisted to DB.")


# Message handler — buffer incoming scores

@agent.on_message(model=SentimentScored)
async def handle_sentiment_scored(ctx: Context, sender: str, msg: SentimentScored) -> None:
    try:
        lock = _get_lock(msg.ticker)
        async with lock:
            # Deduplication
            if msg.ticker not in seen_post_ids:
                seen_post_ids[msg.ticker] = set()
            if msg.post_id and msg.post_id in seen_post_ids[msg.ticker]:
                ctx.logger.info(f"Skipping duplicate post_id={msg.post_id} for {msg.ticker}")
                return
            if msg.post_id:
                seen_post_ids[msg.ticker].add(msg.post_id)

            if msg.ticker not in message_buffer:
                message_buffer[msg.ticker] = []
            message_buffer[msg.ticker].append(msg)
            buffer_size = len(message_buffer[msg.ticker])

        ctx.logger.info(
            f"Buffered {msg.ticker} from {msg.source_name} "
            f"(score={msg.final_score}, buffer_size={buffer_size})"
        )
    except Exception as exc:
        ctx.logger.error(f"Error buffering message for {msg.ticker}: {exc}")


# On-demand aggregation — triggered by the orchestrator after scrapers finish

@agent.on_message(model=AggregateRequest)
async def handle_aggregate_request(ctx: Context, sender: str, msg: AggregateRequest) -> None:
    """Aggregate buffered scores for a ticker immediately and send FinalSignal back."""
    ticker = msg.ticker
    ctx.logger.info(f"Received AggregateRequest for {ticker} from {sender}")

    # Wait briefly for any in-flight sentiment scores to arrive
    await asyncio.sleep(5)

    lock = _get_lock(ticker)
    async with lock:
        messages = message_buffer.pop(ticker, [])
        seen_post_ids.pop(ticker, None)

    if not messages:
        ctx.logger.warning(f"No buffered messages for {ticker} — cannot aggregate.")
        return

    signal = aggregate_signals(messages)

    ctx.logger.info(
        f"On-demand signal {signal.ticker}: direction={signal.direction}, "
        f"score={signal.aggregate_score}, confidence={signal.confidence_pct}%, "
        f"sources={signal.source_count}"
    )

    # Send FinalSignal back to the requester (orchestrator)
    await ctx.send(msg.requester_address, signal)
    ctx.logger.info(f"Sent FinalSignal for {ticker} back to orchestrator.")

    # Also write to dashboard and DB
    try:
        await send_to_dashboard(signal)
    except Exception as exc:
        ctx.logger.error(f"Dashboard POST failed for {ticker}: {exc}")
    try:
        await write_to_db(signal)
    except Exception as exc:
        ctx.logger.error(f"DB write failed for {ticker}: {exc}")


# Interval handler — aggregate and emit signals

@agent.on_interval(period=AGGREGATION_INTERVAL)
async def aggregate_window(ctx: Context) -> None:
    try:
        tickers = list(message_buffer.keys())

        for ticker in tickers:
            lock = _get_lock(ticker)
            async with lock:
                messages = message_buffer.pop(ticker, [])
                seen_post_ids.pop(ticker, None)

            if not messages:
                continue

            signal = aggregate_signals(messages)

            ctx.logger.info(
                f"Signal {signal.ticker}: direction={signal.direction}, "
                f"score={signal.aggregate_score}, confidence={signal.confidence_pct}%, "
                f"sources={signal.source_count}, forced_hold={signal.forced_hold}"
            )

            # Write to database
            try:
                await write_to_db(signal)
            except Exception as exc:
                ctx.logger.error(f"DB write failed for {ticker}: {exc}")

            # Forward to dashboard API
            try:
                await send_to_dashboard(signal)
                ctx.logger.info(f"Sent {ticker} signal to dashboard.")
            except Exception as exc:
                ctx.logger.error(f"Dashboard POST failed for {ticker}: {exc}")

    except Exception as exc:
        ctx.logger.error(f"Error during aggregation: {exc}")


# Run program
if __name__ == "__main__":
    agent.run()
