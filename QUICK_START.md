# Quick Start - 5 Minute Test

## 🚀 Start All Services

### Terminal 1
```bash
cd /Users/brybry.o_o/beachhacks/Beachhacks-9.0
uvicorn UI.api:app --reload --port 8080
```
Wait for: `[api] FinBERT loaded.`

### Terminal 2
```bash
cd /Users/brybry.o_o/beachhacks/Beachhacks-9.0/UI
npm run dev
```
Wait for: `➜  Local:   http://localhost:5173/`

---

## ✅ Terminal 3 - Run Tests

```bash
cd /Users/brybry.o_o/beachhacks/Beachhacks-9.0

# 1. Health check
curl -s http://localhost:8080/api/status | jq '.finbert_loaded'

# 2. Add AAPL (wait 15-30s)
curl -X POST http://localhost:8080/api/watchlist/add \
  -H "Content-Type: application/json" \
  -d '{"ticker":"AAPL"}' | jq '.signal.ticker'

# 3. Try duplicate (should error)
curl -X POST http://localhost:8080/api/watchlist/add \
  -H "Content-Type: application/json" \
  -d '{"ticker":"AAPL"}' | jq '.error'

# 4. Try invalid ticker (should error)
curl -X POST http://localhost:8080/api/watchlist/add \
  -H "Content-Type: application/json" \
  -d '{"ticker":"BADTICKER"}' | jq '.error'

# 5. Add TSLA (wait 15-30s)
curl -X POST http://localhost:8080/api/watchlist/add \
  -H "Content-Type: application/json" \
  -d '{"ticker":"TSLA"}' | jq '.signal.ticker'

# 6. Check count (should be 2)
curl -s http://localhost:8080/api/watchlist | jq '.watchlist | length'

# 7. Remove TSLA
curl -X DELETE http://localhost:8080/api/watchlist/TSLA | jq '.removed'

# 8. Verify removal (should be 1)
curl -s http://localhost:8080/api/watchlist | jq '.watchlist | length'

# 9. KEY TEST: Check sources are unique
curl -s http://localhost:8080/api/watchlist | jq '.watchlist[0].sources | map(.source_name) | unique | length'
```

---

## 🌐 Browser Tests (http://localhost:5173)

1. **DASHBOARD**: See stats grid → Click "+ NEW SIGNAL" → Wait 15-30s ✓
2. **WATCHLIST**: Click tab → Type "MSFT" → Click ADD → Wait 15-30s ✓
3. **DETAIL MODAL**: Click AAPL or MSFT row → See sources (≤3 unique) ✓
4. **SORT**: Click SCORE/CONFIDENCE/TICKER → Table re-sorts ✓
5. **REMOVE**: Click ✕ on row → Row disappears ✓
6. **REFRESH**: Press F5 → Data persists ✓

---

## ✅ Success Checklist

- [ ] Backend loads FinBERT
- [ ] Frontend loads at :5173
- [ ] Can add AAPL
- [ ] Duplicate rejected
- [ ] Invalid rejected
- [ ] Can add TSLA
- [ ] Can remove TSLA
- [ ] Sources unique (≤3)
- [ ] Sorting works
- [ ] Data persists

**All checks pass? → SYSTEM WORKS! 🎉**

---

## 📚 Full Documentation

- **[TESTING_RUNBOOK.md](TESTING_RUNBOOK.md)** - Detailed testing guide
- **[WATCHLIST_TESTING.md](WATCHLIST_TESTING.md)** - Comprehensive 5-phase testing
- **[README.md](README.md)** - Project documentation

