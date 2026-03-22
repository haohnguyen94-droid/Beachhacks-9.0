#!/bin/bash

# Start all SentimentIQ agents and services
# Each service runs in a separate terminal (requires iTerm2 on macOS or similar)

PROJECT_ROOT="/Users/brybry.o_o/beachhacks/Beachhacks-9.0"

echo "🚀 Starting SentimentIQ Agent Workflow..."
echo ""
echo "⚠️  IMPORTANT: Read AGENT_WORKFLOW.md for agent addresses setup"
echo ""

# Kill any existing processes on the ports
echo "🧹 Cleaning up old processes..."
kill $(lsof -ti:8001,8002,8003,8004,8005,8080,5173) 2>/dev/null

sleep 2

echo ""
echo "📋 Terminal commands to copy-paste (open 6 terminals):"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "TERMINAL 1: Orchestrator Agent"
echo "═══════════════════════════════════════════════════════════════"
echo "cd $PROJECT_ROOT && python fast/orchestrator_agent.py"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "TERMINAL 2: News Scraper Agent"
echo "═══════════════════════════════════════════════════════════════"
echo "cd $PROJECT_ROOT && export PYTHONPATH=$PROJECT_ROOT/fast:\$PYTHONPATH && python scrappers/news_agent/news_agent_integrated.py"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "TERMINAL 3: Sentiment Agent"
echo "═══════════════════════════════════════════════════════════════"
echo "cd $PROJECT_ROOT/fast && python sentiment_agent.py"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "TERMINAL 4: Signal Engine Agent"
echo "═══════════════════════════════════════════════════════════════"
echo "cd $PROJECT_ROOT/fast && python signal_engine.py"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "TERMINAL 5: FastAPI Backend"
echo "═══════════════════════════════════════════════════════════════"
echo "cd $PROJECT_ROOT && uvicorn UI.api_agents:app --reload --port 8080"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "TERMINAL 6: React Frontend"
echo "═══════════════════════════════════════════════════════════════"
echo "cd $PROJECT_ROOT/UI && npm run dev"
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo ""
echo "✅ After all agents start:"
echo "1. Copy the printed agent addresses from terminals 1-3"
echo "2. Update .env with ORCHESTRATOR_ADDRESS, SENTIMENT_AGENT_ADDRESS, SIGNAL_ENGINE_ADDRESS"
echo "3. Restart sentiment_agent and signal_engine"
echo "4. Open http://localhost:5173 in browser"
echo "5. Click DASHBOARD → + NEW SIGNAL to start analysis"
echo ""

