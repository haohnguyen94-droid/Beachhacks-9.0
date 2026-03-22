# Agent-Based Workflow Integration

This document explains how to run SentimentIQ with the distributed agent architecture.

## Architecture

```
┌─────────────────┐
│  React Frontend │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────────────┐
│  FastAPI (8080)         │
│  /api/analyze endpoint  │
└────────┬────────────────┘
         │ uagents
         ▼
┌─────────────────────────┐
│  Orchestrator (8005)    │
│  Triggers workflow      │
└────────┬────────────────┘
         │ uagents
         ▼
┌─────────────────────────┐
│  News Scraper (8004)    │
│  Fetches articles       │
└────────┬────────────────┘
         │ ScraperOutput
         ▼
┌─────────────────────────┐
│  Sentiment Agent (8002) │
│  Scores with FinBERT    │
└────────┬────────────────┘
         │ SentimentScored
         ▼
┌─────────────────────────┐
│  Signal Engine (8003)   │
│  Aggregates signals     │
└────────┬────────────────┘
         │ FinalSignal
         ▼
┌─────────────────────────┐
│  FastAPI (8080)         │
│  /api/signals endpoint  │
└─────────────────────────┘
```

## Running the Agent Workflow

### Step 1: Update .env with Agent Addresses

After each agent starts, it prints its address. Update your `.env`:

```bash
# Agent addresses (get these from agent startup logs)
ORCHESTRATOR_ADDRESS=agent1qXXXXXXXXXXXXXX...
SENTIMENT_AGENT_ADDRESS=agent1qYYYYYYYYYYYYYY...
SIGNAL_ENGINE_ADDRESS=agent1qZZZZZZZZZZZZZZ...
```

### Step 2: Start All Services

Open **6 terminals**:

**Terminal 1: Orchestrator**
```bash
cd /Users/brybry.o_o/beachhacks/Beachhacks-9.0
python fast/orchestrator_agent.py
# Note the printed address, add to .env
```

**Terminal 2: News Scraper**
```bash
cd /Users/brybry.o_o/beachhacks/Beachhacks-9.0
export PYTHONPATH=/Users/brybry.o_o/beachhacks/Beachhacks-9.0/fast:$PYTHONPATH
python scrappers/news_agent/news_agent_integrated.py
# Note the address, add to SENTIMENT_AGENT_ADDRESS in .env
```

**Terminal 3: Sentiment Agent**
```bash
cd /Users/brybry.o_o/beachhacks/Beachhacks-9.0/fast
python sentiment_agent.py
# Note the address, add to SIGNAL_ENGINE_ADDRESS in .env
```

**Terminal 4: Signal Engine**
```bash
cd /Users/brybry.o_o/beachhacks/Beachhacks-9.0/fast
python signal_engine.py
# Receives signals, sends to FastAPI
```

**Terminal 5: FastAPI Backend**
```bash
cd /Users/brybry.o_o/beachhacks/Beachhacks-9.0
uvicorn UI.api_agents:app --reload --port 8080
```

**Terminal 6: Frontend**
```bash
cd /Users/brybry.o_o/beachhacks/Beachhacks-9.0/UI
npm run dev
```

### Step 3: Test the Workflow

1. Open `http://localhost:5173`
2. Click **DASHBOARD** → **+ NEW SIGNAL**
3. Watch the agents work:
   - Orchestrator sends ticker queries
   - News scraper fetches articles
   - Sentiment agent scores them
   - Signal engine aggregates
   - Results appear in FastAPI
4. Signals auto-populate on dashboard

## Agent Addresses

After starting each agent, it prints something like:
```
INFO:     Agent address: agent1qf0s8fkfkwu9dgnqrzhenysex6f0khvnpp5vr09acwzw4t9e7yjq...
```

**Copy this and update .env:**

```bash
# In .env:
ORCHESTRATOR_ADDRESS=agent1qf0s8fkfkwu9dgnqrzhenysex6f0khvnpp5vr09acwzw4t9e7yjq...
SENTIMENT_AGENT_ADDRESS=agent1qwmltvjxte04e380qjuv3mdhkgdlgpc6ddw8vmf3eqfpzp5gjkzh...
SIGNAL_ENGINE_ADDRESS=agent1qXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX...
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| "Agent address not found" | Wait 5s for agent to start, it prints address on startup |
| "Failed to contact orchestrator" | Make sure ORCHESTRATOR_ADDRESS is in .env and agents are running |
| No signals appearing | Check that all 4 agents are running and have correct addresses in .env |
| "FinBERT not loaded" | Sentiment agent takes 30-60s to load model on first run |

## Performance

Expected timing:
- Orchestrator → News Scraper: instant
- News Scraper → Sentiment Agent: 2-5s (fetching articles)
- Sentiment Agent → Signal Engine: 15-30s (FinBERT scoring)
- Signal Engine → FastAPI: <1s (aggregation + HTTP POST)
- **Total: 20-40 seconds per analysis**

## Switching Back to Monolith

To go back to the simple FastAPI version:
```bash
# Use original api.py instead of api_agents.py
uvicorn UI.api:app --reload --port 8080
```

