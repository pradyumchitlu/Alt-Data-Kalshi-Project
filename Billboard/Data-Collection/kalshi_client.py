"""
Lightweight Kalshi client (demo-friendly, no auth required for public endpoints).
Uses the same interface as server/kalshi_market/kalshi_service.py.
"""
from __future__ import annotations

import os
import requests

# Default to live elections endpoint; override with KALSHI_BASE_URL if needed.
BASE_URL = os.getenv("KALSHI_BASE_URL", "https://api.elections.kalshi.com/trade-api/v2")
AUTH_TOKEN = os.getenv("KALSHI_AUTH_TOKEN", "")


def _headers():
    if AUTH_TOKEN:
        return {"Authorization": f"Bearer {AUTH_TOKEN}"}
    return {}


def get_event_markets(event_ticker: str, status: str = "open", limit: int = 1000):
    """Return all markets for an event ticker (demo endpoint by default)."""
    url = f"{BASE_URL}/markets"
    params = {
        "event_ticker": event_ticker,
        "status": status,
        "limit": limit,
    }
    r = requests.get(url, params=params, headers=_headers(), timeout=8)
    r.raise_for_status()
    return r.json().get("markets", [])


def get_market_orderbook(market_ticker: str):
    """Return orderbook for a single market."""
    url = f"{BASE_URL}/markets/{market_ticker}/orderbook"
    r = requests.get(url, headers=_headers(), timeout=8)
    r.raise_for_status()
    return r.json()


def main():
    """Simple CLI check against demo API."""
    event = os.getenv("KALSHI_EVENT_TICKER", "BILLBOARD-WKLY")
    ticker = os.getenv("KALSHI_MARKET_TICKER", "")
    if ticker:
        try:
            ob = get_market_orderbook(ticker)
            yes = ob.get("orderbook", {}).get("yes") or ob.get("yes", {})
            bids = yes.get("bids", []) if isinstance(yes, dict) else []
            asks = yes.get("asks", []) if isinstance(yes, dict) else []
            best_bid = bids[0]["price"] if bids else None
            best_ask = asks[0]["price"] if asks else None
            print(f"✓ Orderbook for {ticker}")
            print(f"  yes best bid/ask: {best_bid} / {best_ask}")
            print(f"  raw: {ob}")
            return
        except Exception as e:
            print(f"✗ Orderbook fetch failed for {ticker}: {e}")
            return

    try:
        markets = get_event_markets(event)
        print(f"✓ Retrieved {len(markets)} markets for event {event}")
        if markets:
            first = markets[0]
            ticker_first = first.get("ticker")
            title = first.get("title")
            print(f"  First market: {ticker_first} | {title}")
            try:
                ob = get_market_orderbook(ticker_first)
                yes = ob.get("orderbook", {}).get("yes") or ob.get("yes", {})
                bids = yes.get("bids", []) if isinstance(yes, dict) else []
                asks = yes.get("asks", []) if isinstance(yes, dict) else []
                best_bid = bids[0]["price"] if bids else None
                best_ask = asks[0]["price"] if asks else None
                print(f"  Orderbook best yes bid/ask: {best_bid} / {best_ask}")
            except Exception as e:
                print(f"  Orderbook fetch failed: {e}")
    except Exception as e:
        print(f"✗ Kalshi API check failed: {e}")


if __name__ == "__main__":
    main()

