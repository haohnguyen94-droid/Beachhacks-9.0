# Quick Multi-API Setup (2 minutes)

## Copy-Paste Setup

### Step 1: Update .env
```bash
# Edit your .env file
# From:
NEWSDATA_API_KEY=your_single_key

# To:
NEWSDATA_API_KEY=key1,key2,key3
```

Example with real keys:
```bash
NEWSDATA_API_KEY=abc123def456ghi789,xyz789uvw456rst123,pqr321nmo654lkj987
```

### Step 2: Restart Backend
```bash
cd /Users/brybry.o_o/beachhacks/Beachhacks-9.0
# Stop existing (Ctrl+C)
# Then:
uvicorn UI.api:app --reload --port 8080
```

### Step 3: Test
```bash
# Terminal 3
curl -X POST http://localhost:8080/api/analyze | jq '.total_tickers'
```

**Expected:** `10` ✓

---

## Expected Log Output

Watch Terminal 1 for key rotation:
```
[api] Fetched articles for AAPL (key 1/3)
[api] Fetched articles for MSFT (key 2/3)
[api] Fetched articles for NVDA (key 3/3)
[api] Fetched articles for TSLA (key 1/3)
```

---

## Key Rotation Pattern

```
Ticker 1  → Key 1
Ticker 2  → Key 2
Ticker 3  → Key 3
Ticker 4  → Key 1 (cycles)
Ticker 5  → Key 2
...
```

---

## Rate Limit Auto-Recovery

If a key hits 429:
```
[api] Rate limited on key 2/3 for AAPL. Retrying with next key...
```

System automatically uses the next key. No action needed!

---

## Performance

| Keys | Throughput | Good For |
|------|-----------|----------|
| 1 | 100 req/hr | Testing |
| 2 | 200 req/hr | Development |
| 3 | 300 req/hr | Production |
| 5+ | 500+ req/hr | Heavy use |

---

## That's it! 🚀

Multi-key scraping is now active. Just monitor the logs to see key distribution.

