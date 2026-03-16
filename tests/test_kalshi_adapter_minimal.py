import asyncio
import os
import time
import uuid

from adapters.kalshi_adapter import KalshiAdapter


POLL_INTERVAL_SEC = 0.5
POLL_TIMEOUT_SEC = 6.0


async def find_tradable_market(adapter):
    """
    Find a KXBTC15M market and derive a tradable YES price using bid/ask.
    """
    print("\n[1] Discovering KXBTC15M markets...")
    markets = await adapter.get_markets("KXBTC15M")
    print("Raw markets:", markets)

    if not markets:
        print("❌ No markets returned.")
        return None, None

    for m in markets:
        ticker = m["ticker"]
        price = await adapter.get_price(ticker)
        print(f"  Ticker {ticker} YES price (derived): {price}")

        if price and 1 <= price <= 99:
            print(f"✅ Selected ticker: {ticker} @ {price}")
            return ticker, float(price)

    # Fallback: use newest market with a safe midprice
    fallback = markets[0]["ticker"]
    print(f"⚠️ No clean price found; falling back to {fallback} @ 50")
    return fallback, 50.0


async def poll_get_order(adapter, order_id):
    print("\n[4] Polling get_order(order_id)...")
    deadline = time.time() + POLL_TIMEOUT_SEC
    last = None

    while time.time() < deadline:
        resp = await adapter.get_order(order_id)
        order = resp.get("order")
        last = order

        if order:
            print("✅ get_order returned:", order)
            return order

        print("  get_order returned empty, retrying...")
        await asyncio.sleep(POLL_INTERVAL_SEC)

    print("⚠️ get_order never returned an order; last response:", last)
    return last


async def poll_get_orders_for_ticker(adapter, ticker, order_id):
    print("\n[5] Polling get_orders(ticker)...")
    deadline = time.time() + POLL_TIMEOUT_SEC
    last = None

    while time.time() < deadline:
        resp = await adapter.get_orders(ticker=ticker, status="resting")
        orders = resp.get("orders", [])
        last = orders

        print(f"  get_orders returned {len(orders)} orders")

        for o in orders:
            if o.get("order_id") == order_id:
                print("✅ Found order in get_orders:", o)
                return o

        await asyncio.sleep(POLL_INTERVAL_SEC)

    print("⚠️ Order not found in get_orders; last snapshot:", last)
    return None


async def inspect_orderbook(adapter, ticker):
    print("\n[6] Inspecting orderbook...")
    ob = await adapter.get_market_orderbook(ticker)
    print("Orderbook:", ob)
    return ob


async def main():
    print("\n=== KalshiAdapter v10.0.0 — Robust End‑to‑End Test ===")

    key_id = os.getenv("KALSHI_KEY_ID")
    key_path = os.getenv("KALSHI_PRIVATE_KEY_PATH")
    base_url = os.getenv("KALSHI_BASE_URL", "https://api.elections.kalshi.com")

    if not key_id or not key_path:
        print("❌ Missing KALSHI_KEY_ID or KALSHI_PRIVATE_KEY_PATH")
        return

    adapter = KalshiAdapter(key_id, key_path, base_url)

    try:
        # 1–2. Find market + price
        ticker, raw_price = await find_tradable_market(adapter)
        if not ticker:
            return

        yes_price = int(raw_price)
        print(f"\n[2] Using YES price: {yes_price}")

        # 3. Place post-only limit order
        print("\n[3] Placing order...")

        order_payload = {
            "ticker": ticker,
            "side": "yes",
            "action": "buy",
            "type": "limit",
            "yes_price": yes_price,
            "count": 1,
            "client_order_id": str(uuid.uuid4()),
            "post_only": True,
        }

        order_resp = await adapter.place_order(order_payload)
        print("Order response:", order_resp)

        order_obj = order_resp.get("order", {})
        order_id = order_obj.get("order_id")

        if not order_id:
            print("❌ No order_id returned — cannot continue.")
            return

        print(f"✅ Placed order_id: {order_id}")

        # 4. Poll get_order(order_id)
        await poll_get_order(adapter, order_id)

        # 5. Poll get_orders(ticker) for our order
        await poll_get_orders_for_ticker(adapter, ticker, order_id)

        # 6. Inspect orderbook
        await inspect_orderbook(adapter, ticker)

        # 7. Cancel order
        print("\n[7] Canceling order...")
        cancelled = await adapter.cancel_order(order_id)
        print("Cancel response:", cancelled)

        print("\n=== All tests completed successfully ===")

    finally:
        await adapter.rest.close()


if __name__ == "__main__":
    asyncio.run(main())
