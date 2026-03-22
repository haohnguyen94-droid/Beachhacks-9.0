# Multi-API Key Setup Guide

## Overview

The scraper now supports **multiple NewsData.io API keys** to:
- ✅ Distribute requests across keys
- ✅ Avoid rate limiting
- ✅ Increase article fetch throughput
- ✅ Support higher request volumes

---

## Setup Instructions

### Step 1: Get Multiple API Keys

Sign up for multiple NewsData.io accounts:

1. Visit https://newsdata.io
2. Create account 1 → Copy API key
3. Create account 2 → Copy API key
4. Create account 3 → Copy API key (optional)
5. Etc.

**Example API Keys:**
```
abc123def456ghi789
xyz789uvw456rst123
pqr321nmo654lkj987
```

---

### Step 2: Update .env File

Edit your `.env` file and use **comma-separated** API keys:

**Single Key (Original)**
```bash
NEWSDATA_API_KEY=abc123def456ghi789
```

**Multiple Keys (New)**
```bash
NEWSDATA_API_KEY=abc123def456ghi789,xyz789uvw456rst123,pqr321nmo654lkj987
```

### Step 3: Restart Backend

```bash
cd /Users/brybry.o_o/beachhacks/Beachhacks-9.0
uvicorn UI.api:app --reload --port 8080
```

**Expected output on startup:**
```
[INFO] Uvicorn running on http://127.0.0.1:8080
[api] Loading ProsusAI/finbert …
[api] FinBERT loaded.
```

---

## How It Works

### Key Rotation

Each ticker request uses the **next key in sequence**:

```
Request 1 (AAPL)  → Key 1 (abc123...)
Request 2 (MSFT)  → Key 2 (xyz789...)
Request 3 (NVDA)  → Key 3 (pqr321...)
Request 4 (TSLA)  → Key 1 (abc123...) [cycles back]
Request 5 (AMZN)  → Key 2 (xyz789...)
...
```

### Rate Limit Handling

If a key hits a rate limit (429 error):
1. API detects 429 status code
2. Automatically tries the next key
3. Logs: `[api] Rate limited on key 2/3 for AAPL. Retrying with next key...`
4. Continues seamlessly

### Logging

Watch the backend logs to see key usage:

```
[api] Fetched articles for AAPL (key 1/3)
[api] Fetched articles for MSFT (key 2/3)
[api] Fetched articles for NVDA (key 3/3)
[api] Fetched articles for TSLA (key 1/3)
[api] Rate limited on key 2/3 for AMZN. Retrying with next key...
[api] Fetched articles for AMZN (key 3/3)
```

---

## Performance Benefits

### With 1 API Key
- Request rate limit: ~100 requests/hour
- Can analyze: 1-2 tickers safely
- Risk: Rate limited quickly on high volume

### With 3 API Keys
- Request rate limit: ~300 requests/hour (3 × 100)
- Can analyze: Multiple dashboard analyses + watchlist tickers
- Risk: Very low, spreads load evenly

### With 5+ API Keys
- Request rate limit: ~500+ requests/hour
- Can analyze: Unlimited dashboard + watchlist combos
- Risk: Minimal, excellent distribution

---

## Testing Multi-Key Setup

### Test 1: Verify Keys Loaded

```bash
# Terminal 3 - check startup logs
# You should see [api] FinBERT loaded. without errors
curl -s http://localhost:8080/api/status | jq '.finbert_loaded'
```

**Expected:** `true`

### Test 2: Run Analysis and Watch Key Rotation

**Terminal 1 logs** should show:
```
[api] Fetched articles for AAPL (key 1/3)
[api] Fetched articles for MSFT (key 2/3)
[api] Fetched articles for NVDA (key 3/3)
[api] Fetched articles for TSLA (key 1/3)
[api] Fetched articles for AMZN (key 2/3)
[api] Fetched articles for META (key 3/3)
[api] Fetched articles for GOOG (key 1/3)
[api] Fetched articles for JPM (key 2/3)
[api] Fetched articles for XOM (key 3/3)
[api] Fetched articles for UNH (key 1/3)
```

### Test 3: Trigger Analysis

```bash
# Terminal 3
curl -X POST http://localhost:8080/api/analyze | jq '.total_tickers'
```

**Expected:** `10` (all demo tickers processed)

---

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| "NEWSDATA_API_KEY not set" | Empty .env | Add API keys to .env, restart backend |
| (key 0/0) in logs | No keys parsed | Check .env formatting: `KEY1,KEY2,KEY3` (no spaces) |
| Still rate limited | All keys maxed | Add more API keys |
| Articles found 0 | Invalid keys | Verify keys work at https://newsdata.io |

---

## .env Format Reference

```bash
# ✅ CORRECT formats:
NEWSDATA_API_KEY=abc123,xyz789,pqr321
NEWSDATA_API_KEY=abc123, xyz789, pqr321
NEWSDATA_API_KEY=abc123,xyz789,pqr321,lmn456,opq789

# ❌ INCORRECT formats:
NEWSDATA_API_KEY=abc123; xyz789; pqr321  (semicolon instead of comma)
NEWSDATA_API_KEY="abc123,xyz789"          (don't quote)
NEWSDATA_API_KEY=abc123|xyz789|pqr321     (pipe instead of comma)
```

---

## Advanced: Monitor Key Distribution

To verify keys are being used equally, count occurrences in logs:

```bash
# Terminal 1 - restart backend, run analysis
# Then check key distribution:
# Expected: roughly equal distribution across keys
```

Example with 3 keys (10 tickers = ~3-4 uses per key):
```
Key 1: 4 uses ✓
Key 2: 3 uses ✓
Key 3: 3 uses ✓
```

---

## Backwards Compatibility

✅ **Still works with single key:**

```bash
# Old format still works fine
NEWSDATA_API_KEY=abc123def456ghi789
```

The system automatically detects single vs. multiple keys and handles both.

---

## Best Practices

1. **Use at least 2 keys** for production use
2. **Monitor logs** first time to verify key rotation
3. **Add 1 extra key** as backup for rate limit safety
4. **Keep keys in .env** (never in code)
5. **Restart backend** after changing .env
6. **Test with /api/analyze** before production use

---

## Summary

| Feature | Before | After |
|---------|--------|-------|
| API Keys | 1 only | Unlimited |
| Key Rotation | N/A | Automatic |
| Rate Limit Handling | Manual | Automatic fallback |
| Request Throughput | 100 req/hr | 100 × N req/hr |
| Setup Time | 5 min | 2 min (just add keys) |

**Ready to scale! 🚀**

