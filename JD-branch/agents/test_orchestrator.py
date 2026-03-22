from __future__ import annotations

import httpx


def main() -> None:
    payload = {
        "tickers": ["AAPL", "NVDA"],
        "limit": 5,
    }

    response = httpx.post("http://localhost:8003/run", json=payload, timeout=30)
    print(response.status_code)
    print(response.json())


if __name__ == "__main__":
    main()