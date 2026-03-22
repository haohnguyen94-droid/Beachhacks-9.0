# SentimentIQ Multi-Agent Market Data Pipeline

SentimentIQ is a multi-agent financial data pipeline built with Fetch.ai `uAgents`.

It uses specialized scraper agents to collect:
- equity and company news from **NewsData**
- market/company headlines from **Finnhub**
- crypto insights from a dedicated **Crypto Agent**

All raw outputs are sent to an **Orchestrator Agent**, which:
- dispatches scraping jobs
- collects normalized results
- removes duplicates
- merges cross-source items
- exports a frontend-ready JSON file

---

## Architecture

```text
Frontend / test runner
        |
        v
   Orchestrator Agent
    /      |       \
   v       v        v
NewsData  Finnhub  Crypto Agent
    \       |       /
     \      |      /
      ----- merged JSON -----> outputs/<request_id>.json
```

---

## Setup

### 1. Create virtual environment

#### macOS / Linux
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

#### Windows (PowerShell)
```powershell
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

---

### 2. Configure environment variables

Create `.env` in root:

```env
NEWSDATA_API_KEY=your_newsdata_key
FINNHUB_API_KEY=your_finnhub_key

NEWSDATA_AGENT_SEED_PHRASE=news_seed
FINNHUB_AGENT_SEED_PHRASE=finn_seed
CRYPTO_AGENT_SEED_PHRASE=crypto_seed
ORCHESTRATOR_SEED_PHRASE=orch_seed
```

---
## Before running
```
Sign up or sign in to your account on https://agentverse.ai and https://asi1.ai/
```
---
## Run the system

Open **5 terminals**

### Terminal 1 — NewsData Agent
```bash
python -m agents.newsdata_scraper_agent
```

### Terminal 2 — Finnhub Agent
```bash
python -m agents.finnhub_scraper_agent
```

### Terminal 3 — Crypto Agent
```bash
python -m agents.crypto_scraper_agent
```

### Terminal 4 — Orchestrator
```bash
python -m agents.orchestrator
```

### Terminal 5 — Trigger pipeline
```bash
python -m agents.test_orchestrator_run
```

---

## Output

Generated JSON file:

```text
outputs/<request_id>.json
```

Contains:
- merged cross-source items
- per-ticker breakdown
- crypto + stock signals
- deduplicated headlines
- frontend-ready structure

---

## Example Payload

```json
{
  "tickers": ["AAPL", "NVDA"],
  "crypto_symbols": ["BTC", "ETH"],
  "limit": 5
}
```

---

## Notes

- Restart all agents if you change code
- Keep agent addresses updated in `orchestrator.py`
- `.env` should not be committed
- Use same seed phrases to keep stable agent addresses

---

## Summary

This system demonstrates a scalable multi-agent architecture where:
- agents specialize in different data domains
- an orchestrator coordinates execution
- outputs are unified into structured market intelligence