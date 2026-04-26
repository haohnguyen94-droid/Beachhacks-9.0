# SentimentIQ Terminal

> AI-powered sentiment analysis platform for real-time stock market signals powered by FinBERT transformer model

[![Status](https://img.shields.io/badge/status-active-brightgreen)](#)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](#)
[![React](https://img.shields.io/badge/react-18.3-blue)](#)
[![License](https://img.shields.io/badge/license-MIT-green)](#license)

---

## 📋 Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Installation](#installation)
- [Environment Variables](#environment-variables)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Project Structure](#project-structure)
- [Design Decisions](#design-decisions)
- [Future Improvements](#future-improvements)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

**SentimentIQ Terminal** is an AI-powered sentiment analysis platform that analyzes financial news articles and generates actionable trading signals for stock market assets. Using the **FinBERT** transformer model (fine-tuned for financial sentiment), the system scores articles from multiple news sources, aggregates sentiment data with credibility weighting and recency decay, and produces buy/sell/hold signals with confidence metrics.

### The Problem
Traders and investors struggle to process vast amounts of financial news efficiently. Manual sentiment analysis is time-consuming and inconsistent. SentimentIQ automates this workflow with institutional-grade AI, providing real-time, data-driven trading signals.

### The Solution
- **Automated News Aggregation**: Fetches financial news from NewsData.io across multiple sources
- **Advanced Sentiment Scoring**: Uses FinBERT (financial BERT) for precise financial sentiment analysis
- **Intelligent Aggregation**: Weights sentiment by source credibility, confidence, and time decay
- **Interactive Dashboard**: Visualizes signals, sectors, and trends in a modern, intuitive interface
- **Personal Watchlist**: Track specific tickers with custom sentiment analysis

---

## ✨ Features

### Core Features

#### 1. **Signal Generation Engine**
- Fetches up to 50 financial news articles per analysis run
- Scores each article with FinBERT transformer model
- Generates BUY/SELL/HOLD signals with confidence percentages
- Weighted aggregation using credibility, confidence, and recency decay

#### 2. **Interactive Dashboard**
- Real-time stats: stocks tracked, strong signals, average confidence
- Featured signal cards with rotating view (3 cards at a time)
- Filter signals by direction (ALL, BUY, SELL, HOLD)
- Click-to-detail modal with full AI reasoning and source breakdown
- Responsive layout with dark terminal aesthetic

#### 3. **Market & Sector Analysis**
- Segment signals by market sector (Technology, Healthcare, Finance, etc.)
- Per-sector sentiment breakdown and confidence metrics
- Sector trend visualization (SVG area charts)
- Constituent performance tables with per-stock metrics
- Sentiment heatmap (3×1 grid) showing sector health at a glance

#### 4. **Personal Watchlist** ⭐ **NEW**
- Add custom tickers with real-time sentiment analysis
- Validated against ~100 known ticker symbols
- Client + server-side duplicate prevention
- Deduplicated sources (shows max 3 unique news sources)
- Sort by score, confidence, or alphabetically
- Remove individual tickers with one click

#### 5. **Advanced Data Visualization**
- Confidence bars (colored by signal type)
- Sentiment breakdown charts (positive/neutral/negative percentages)
- SVG area charts with gradient fills for trend visualization
- Color-coded badges and heatmap cells

### Signal Strength Logic
- **BUY**: `aggregate_score >= 0.20` (bullish sentiment)
- **SELL**: `aggregate_score <= -0.20` (bearish sentiment)
- **HOLD**: `aggregate_score` between -0.20 and 0.20 (neutral)
- **Forced HOLD**: < 3 sources OR confidence < 55% (insufficient data)

---

## 🛠️ Tech Stack

### Frontend
| Technology | Version | Purpose |
|-----------|---------|---------|
| **React** | 18.3 | UI framework |
| **Vite** | 6.0 | Build tool & dev server |
| **Tailwind CSS** | 3.4 | Utility-first styling |
| **Fetch API** | Native | HTTP client |
| **React Hooks** | 18.3 | State management |

### Backend
| Technology | Version | Purpose |
|-----------|---------|---------|
| **FastAPI** | Latest | REST API framework |
| **Uvicorn** | Latest | ASGI server |
| **Python** | 3.10+ | Backend language |
| **Transformers** | Latest | FinBERT model loading |
| **PyTorch** | Latest | Model inference |
| **httpx** | Latest | Async HTTP client |

### ML & Data
| Technology | Purpose |
|-----------|---------|
| **FinBERT** | Financial sentiment classification |
| **NewsData.io API** | Financial news aggregation |
| **Pydantic** | Data validation & serialization |

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     SentimentIQ Terminal                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐              ┌──────────────────────┐ │
│  │  React Frontend  │◄────HTTP────►│  FastAPI Backend     │ │
│  │  (Port 5173)     │              │  (Port 8080)         │ │
│  └──────────────────┘              └──────────────────────┘ │
│       • Dashboard                        • Signal Engine      │
│       • Markets View                     • FinBERT Scoring    │
│       • Watchlist                        • Score Aggregation  │
│       • DetailModal                      • Watchlist Manager  │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                              ▲
                              │
                    ┌─────────┴────────┐
                    │                  │
              ┌─────────────┐    ┌──────────────┐
              │ NewsData.io │    │  FinBERT ML  │
              │ News API    │    │  Model       │
              └─────────────┘    └──────────────┘
```

### Data Flow

1. **Analysis Initiation** → User clicks "+ NEW SIGNAL" button
2. **Article Fetching** → FastAPI fetches ~50 articles from NewsData.io
3. **Sentiment Scoring** → FinBERT scores each article (positive/negative/neutral)
4. **Per-Ticker Aggregation** → Weighted average by credibility × confidence × recency decay
5. **Signal Generation** → Produces BUY/SELL/HOLD with confidence percentages
6. **Sector Aggregation** → Groups signals by sector, calculates sector-level metrics
7. **Response Caching** → Stores result for reuse
8. **Frontend Rendering** → Dashboard displays signals

---

## 🚀 Installation

### Prerequisites
- **Node.js** 18+ and **npm**
- **Python** 3.10+
- **pip** (Python package manager)

### Step 1: Clone Repository
```bash
git clone https://github.com/your-username/Beachhacks-9.0.git
cd Beachhacks-9.0
```

### Step 2: Backend Setup

#### Install Python Dependencies
```bash
pip install -r requirements.txt
```

#### Configure Environment Variables
```bash
# Create .env file
echo "NEWSDATA_API_KEY=your_api_key_here" > .env
```

#### Start Backend Server
```bash
uvicorn UI.api:app --reload --port 8080
```

**Expected Output:**
```
[INFO] Uvicorn running on http://127.0.0.1:8080
[api] Loading ProsusAI/finbert …
[api] FinBERT loaded.
```

### Step 3: Frontend Setup

#### Install Node Dependencies
```bash
cd UI
npm install
```

#### Start Dev Server
```bash
npm run dev
```

**Expected Output:**
```
  VITE v6.0.0  ready in ### ms
  ➜  Local:   http://localhost:5173/
```

### Step 4: Access Application
```
http://localhost:5173
```

---

## 🔧 Environment Variables

Create a `.env` file in the project root:

```bash
# Required: NewsData.io API Key
NEWSDATA_API_KEY=your_newsdata_api_key_here

# Optional: API Base URL (defaults to http://localhost:8080)
# VITE_API_BASE=http://localhost:8080
```

### Getting NewsData.io API Key

1. Visit https://newsdata.io
2. Sign up for a free account
3. Navigate to API Keys section
4. Copy your API key
5. Add to `.env` file

---

## 📖 Usage

### Running an Analysis

1. Open `http://localhost:5173` in your browser
2. Click the **DASHBOARD** tab
3. Click the **+ NEW SIGNAL** button
4. Wait 15-30 seconds while the system analyzes articles
5. Dashboard populates with signals, stats, and heatmap

### Using the Watchlist

1. Click **WATCHLIST** in left sidebar
2. Type a ticker (e.g., "AAPL")
3. Click **+ ADD** or press Enter
4. Wait 15-30 seconds for analysis
5. Click any row to view detailed modal
6. Click **✕** to remove ticker

### Exploring Markets View

1. Click **MARKETS** tab
2. View sector-level sentiment analysis
3. Check heatmap, top movers, and alerts in right sidebar

---

## 📡 API Endpoints

### Core Endpoints

#### `GET /api/status`
Health check and model status

```bash
curl http://localhost:8080/api/status
```

#### `POST /api/analyze`
Run full sentiment analysis pipeline

```bash
curl -X POST http://localhost:8080/api/analyze
```

#### `GET /api/results`
Get cached results from last analysis

```bash
curl http://localhost:8080/api/results
```

### Watchlist Endpoints

#### `GET /api/watchlist`
Get all watchlist tickers

```bash
curl http://localhost:8080/api/watchlist
```

#### `POST /api/watchlist/add`
Add ticker to watchlist

```bash
curl -X POST http://localhost:8080/api/watchlist/add \
  -H "Content-Type: application/json" \
  -d '{"ticker":"AAPL"}'
```

#### `DELETE /api/watchlist/{ticker}`
Remove ticker from watchlist

```bash
curl -X DELETE http://localhost:8080/api/watchlist/AAPL
```

---

## 📁 Project Structure

```
Beachhacks-9.0/
├── UI/                              # React frontend + FastAPI backend
│   ├── SentimentIQ.jsx              # Main React component
│   ├── api.py                       # FastAPI backend
│   ├── main.jsx                     # React entry point
│   ├── index.html                   # HTML shell
│   ├── vite.config.js               # Vite configuration
│   ├── tailwind.config.js           # Tailwind customization
│   ├── package.json                 # Node dependencies
│   └── node_modules/                # Installed packages
│
├── fast/                            # Signal engine reference
├── scrappers/                       # Data collection agents
├── testing/                         # Test files
│
├── WATCHLIST_TESTING.md             # Comprehensive testing guide
├── requirements.txt                 # Python dependencies
├── .env.example                     # Environment template
├── Makefile                         # Build commands
└── README.md                        # This file
```

---

## 🎨 Design Decisions

### 1. **Monolithic Backend (FastAPI + FinBERT)**
Single service for API and ML inference; simplified deployment; FinBERT loads once at startup.

### 2. **In-Memory Watchlist (No Database)**
Stores watchlist in Python dict; no persistence needed for demo; meets hackathon requirements.

### 3. **Dual Duplicate Prevention**
Validates duplicates on frontend (UX) and backend (data integrity).

### 4. **Source Deduplication (Max 3 Unique)**
Shows only unique sources in DetailModal; cleaner UI; focuses on diversity.

### 5. **Weighted Aggregation Formula**
Weight = `credibility × confidence × recency_decay`; accounts for source reliability, model certainty, and freshness.

### 6. **Dark Terminal Aesthetic**
Eye-friendly for extended use; resembles trading terminals; modern feel with neon accents.

---

## 🔮 Future Improvements

### Short Term
- [ ] Database integration (PostgreSQL) for persistent watchlist
- [ ] User authentication (JWT-based sessions)
- [ ] Signal history & backtesting
- [ ] Real-time updates (WebSocket)
- [ ] Redis caching layer
- [ ] Error logging (Sentry)

### Medium Term
- [ ] Portfolio management & alerts
- [ ] Custom FinBERT fine-tuning
- [ ] Technical analysis integration
- [ ] Social media sentiment (Twitter, Reddit)
- [ ] Sector correlation analysis

### Long Term
- [ ] Backtesting engine
- [ ] Paper trading simulation
- [ ] Live trading integration (Alpaca, Interactive Brokers)
- [ ] Ensemble ML models
- [ ] Advanced charting (Plotly, D3.js)
- [ ] Tiered pricing API

---

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Testing
See [WATCHLIST_TESTING.md](WATCHLIST_TESTING.md) for comprehensive testing guide.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 📞 Support

- **Issues**: Report bugs in the [Issues](https://github.com/your-username/Beachhacks-9.0/issues) tab
- **Testing**: See [WATCHLIST_TESTING.md](WATCHLIST_TESTING.md) for detailed testing guide
- **Documentation**: Code comments and docstrings throughout

---

<div align="center">

**Made with ❤️ for [Beachhacks 9.0](https://beachhacks.com)**

⭐ If you find this useful, please star the repository!

</div>
