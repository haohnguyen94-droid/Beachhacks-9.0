# SentimentIQ Testing Runbook

## 🚀 Setup Phase (Do This Once)

### Step 1: Open 3 Terminals

**Terminal 1:**
```bash
cd /Users/brybry.o_o/beachhacks/Beachhacks-9.0
uvicorn UI.api:app --reload --port 8080
```
✅ Wait for: `[api] FinBERT loaded.`

**Terminal 2:**
```bash
cd /Users/brybry.o_o/beachhacks/Beachhacks-9.0/UI
npm run dev
```
✅ Wait for: `➜  Local:   http://localhost:5173/`

**Terminal 3:**
```bash
cd /Users/brybry.o_o/beachhacks/Beachhacks-9.0
# Ready for testing commands
```

---

## ✅ Quick Smoke Test (3 minutes)

Run these in **Terminal 3** one by one:

### 1. Health Check
```bash
curl -s http://localhost:8080/api/status | jq
```
**Expected:** `finbert_loaded: true`

### 2. Add First Ticker (AAPL)
```bash
curl -s -X POST http://localhost:8080/api/watchlist/add \
  -H "Content-Type: application/json" \
  -d '{"ticker":"AAPL"}' | jq '.signal | {ticker, direction, confidence_pct}'
```
**Expected:** Takes 15-30s, returns AAPL with BUY/SELL/HOLD signal

### 3. Check Duplicate Prevention
```bash
curl -s -X POST http://localhost:8080/api/watchlist/add \
  -H "Content-Type: application/json" \
  -d '{"ticker":"AAPL"}' | jq '.error'
```
**Expected:** `"'AAPL' is already in your watchlist."`

### 4. Check Invalid Ticker
```bash
curl -s -X POST http://localhost:8080/api/watchlist/add \
  -H "Content-Type: application/json" \
  -d '{"ticker":"BADTICKER"}' | jq '.error'
```
**Expected:** `"'BADTICKER' is not a recognized ticker symbol."`

### 5. Add Another Ticker (TSLA)
```bash
curl -s -X POST http://localhost:8080/api/watchlist/add \
  -H "Content-Type: application/json" \
  -d '{"ticker":"TSLA"}' | jq '.signal.ticker'
```
**Expected:** Takes 15-30s, returns `"TSLA"`

### 6. View Watchlist Count
```bash
curl -s http://localhost:8080/api/watchlist | jq '.watchlist | length'
```
**Expected:** `2`

### 7. Remove TSLA
```bash
curl -s -X DELETE http://localhost:8080/api/watchlist/TSLA | jq
```
**Expected:** `{"removed": "TSLA"}`

### 8. Verify Removal
```bash
curl -s http://localhost:8080/api/watchlist | jq '.watchlist | length'
```
**Expected:** `1`

### 9. KEY TEST - Verify Source Deduplication
```bash
curl -s http://localhost:8080/api/watchlist | jq '.watchlist[0].sources | length'
```
**Expected:** ≤ 10 (actual sources fetched)

Now check if all sources are unique:
```bash
curl -s http://localhost:8080/api/watchlist | jq '.watchlist[0].sources | map(.source_name) | unique | length'
```
**Expected:** Should match the total count (all unique)

---

## 🌐 Browser Testing

**Open:** `http://localhost:5173`

### Test 1: Dashboard View
- Click **DASHBOARD** tab
- Should see stats grid and signal cards
- Click **+ NEW SIGNAL** button
- Wait 15-30 seconds
- See populated dashboard

### Test 2: Watchlist View
- Click **WATCHLIST** tab in left sidebar
- See "1 tickers tracked" (AAPL from earlier)
- Type "MSFT" in input
- Click **+ ADD**
- Wait 15-30 seconds
- See MSFT row appears
- Counter shows "2 tickers tracked"

### Test 3: Open DetailModal
- Click any watchlist row (AAPL or MSFT)
- Modal opens with:
  - Large ticker name
  - BUY/SELL/HOLD badge
  - Company name
  - Aggregate Confidence (%)
  - AI REASONING paragraph
  - SENTIMENT BREAKDOWN chart
  - SUPPORTING SIGNALS section (should show ≤ 3 unique sources!)

### Test 4: Verify No Duplicate Sources
- Look at "SUPPORTING SIGNALS" section
- Count source cards
- Should be ≤ 3
- Check that no source name is repeated
- Close modal

### Test 5: Sort Functionality
- Click **SCORE** button → table re-sorts
- Click **CONFIDENCE** button → re-sorts again
- Click **TICKER** button → alphabetical
- Check button highlights green when selected

### Test 6: Remove Ticker
- Find MSFT row
- Click **✕** button on far right
- Row disappears
- Counter shows "1 tickers tracked"

### Test 7: Refresh Page
- Press F5 or Cmd+R
- Watchlist should reload
- AAPL should still be there
- Counts restored

---

## 🧪 Extended Test (10 minutes)

Run in **Terminal 3**:

### Add Multiple Tickers
```bash
for ticker in NVDA GOOG META MSFT JPM; do
  echo "Adding $ticker..."
  curl -s -X POST http://localhost:8080/api/watchlist/add \
    -H "Content-Type: application/json" \
    -d "{\"ticker\":\"$ticker\"}" | jq '.signal.ticker'
  echo "---"
done
```

### View Full Watchlist
```bash
curl -s http://localhost:8080/api/watchlist | jq '.watchlist | map({ticker, direction, confidence_pct})'
```
**Expected:** 6 tickers (AAPL + 5 new ones)

### Verify All Have Sources
```bash
curl -s http://localhost:8080/api/watchlist | jq '.watchlist | map({ticker, source_count})'
```
**Expected:** All have source_count > 0

---

## 🎯 Final Verification Checklist

After all tests, verify:

- [ ] Backend starts without errors
- [ ] Frontend loads at http://localhost:5173
- [ ] Can add valid ticker (AAPL)
- [ ] Cannot add duplicate ticker (error shown)
- [ ] Cannot add invalid ticker (error shown)
- [ ] Can remove ticker
- [ ] Watchlist persists on page reload
- [ ] DetailModal shows ≤ 3 unique sources (KEY TEST!)
- [ ] Sorting works (SCORE, CONFIDENCE, TICKER)
- [ ] Can add 5+ tickers without UI lag

**If all ✅ → SYSTEM WORKS!**

---

## 🔧 Troubleshooting

| Problem | Solution |
|---------|----------|
| Backend fails to start | Check Port 8080 is free: `lsof -i :8080` |
| "FinBERT failed to load" | Wait 30s, it's downloading the model |
| Frontend shows "Failed to connect" | Check backend is running on port 8080 |
| Request takes >60s | NewsData.io API is slow; wait and retry |
| Button stuck on "ANALYZING..." | Check Terminal 1 for Python errors |
| Sources show duplicates | Bug not fixed; check code dedup logic |

---

## 📋 Copy-Paste Ready Commands

**Quick setup:**
```bash
# Terminal 1
uvicorn UI.api:app --reload --port 8080

# Terminal 2  
cd /Users/brybry.o_o/beachhacks/Beachhacks-9.0/UI && npm run dev

# Terminal 3 (after both above are running)
cd /Users/brybry.o_o/beachhacks/Beachhacks-9.0
```

**Test health:**
```bash
curl -s http://localhost:8080/api/status | jq '.finbert_loaded'
```

**Full watchlist test:**
```bash
# Add
curl -X POST http://localhost:8080/api/watchlist/add -H "Content-Type: application/json" -d '{"ticker":"AAPL"}' | jq '.signal.ticker'

# List
curl http://localhost:8080/api/watchlist | jq '.watchlist | length'

# Remove
curl -X DELETE http://localhost:8080/api/watchlist/AAPL | jq '.removed'
```

