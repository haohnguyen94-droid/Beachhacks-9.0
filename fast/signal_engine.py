# Signal Engine — aggregates FinBERT sentiment scores per ticker over a
# 15-minute window and produces a BUY / SELL / HOLD signal with confidence %.

from __future__ import annotations

import asyncio
import json
import os

from dotenv import load_dotenv
from uagents import Agent, Context

load_dotenv()

from aggregator import aggregate_signals
from models import FinalSignal, SentimentScored

# Agent initialization

DASHBOARD_AGENT_ADDRESS: str = os.getenv("DASHBOARD_AGENT_ADDRESS", "")
DATABASE_URL: str = os.getenv("DATABASE_URL", "")
SIGNAL_ENGINE_PORT: int = int(os.getenv("SIGNAL_ENGINE_PORT", "8003"))
AGGREGATION_INTERVAL: float = float(os.getenv("AGGREGATION_INTERVAL", "900.0"))  # 15 min

agent = Agent(
    name="signal_engine",
    seed="signal_engine_seed_phrase",
    port=SIGNAL_ENGINE_PORT,
    endpoint=[f"http://localhost:{SIGNAL_ENGINE_PORT}/submit"],
)

# Buffer: ticker -> list of SentimentScored messages
message_buffer: dict[str, list[SentimentScored]] = {}
buffer_locks: dict[str, asyncio.Lock] = {}


def _get_lock(ticker: str) -> asyncio.Lock:
    """Get or create a lock for a ticker."""
    if ticker not in buffer_locks:
        buffer_locks[ticker] = asyncio.Lock()
    return buffer_locks[ticker]


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
        # Log handled at caller — just re-raise for the caller's try/except
        raise exc


# Startup

@agent.on_event("startup")
async def startup(ctx: Context) -> None:
    ctx.logger.info(f"Signal engine address: {agent.address}")
    ctx.logger.info(f"Aggregation interval: {AGGREGATION_INTERVAL}s")
    if DATABASE_URL:
        ctx.logger.info("DATABASE_URL set — will write signals to PostgreSQL.")
    else:
        ctx.logger.warning("DATABASE_URL not set — signals will not be persisted.")


# Message handler — buffer incoming scores

@agent.on_message(model=SentimentScored)
async def handle_sentiment_scored(ctx: Context, sender: str, msg: SentimentScored) -> None:
    try:
        lock = _get_lock(msg.ticker)
        async with lock:
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


# Interval handler — aggregate and emit signals

@agent.on_interval(period=AGGREGATION_INTERVAL)
async def aggregate_window(ctx: Context) -> None:
    try:
        tickers = list(message_buffer.keys())

        for ticker in tickers:
            lock = _get_lock(ticker)
            async with lock:
                messages = message_buffer.pop(ticker, [])

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

            # Forward to dashboard
            if DASHBOARD_AGENT_ADDRESS:
                await ctx.send(DASHBOARD_AGENT_ADDRESS, signal)
            else:
                ctx.logger.warning("DASHBOARD_AGENT_ADDRESS not set — signal not forwarded.")

    except Exception as exc:
        ctx.logger.error(f"Error during aggregation: {exc}")


# Run program
if __name__ == "__main__":
    agent.run()
