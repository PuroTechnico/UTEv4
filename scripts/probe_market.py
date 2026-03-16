import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import execution.client
from execution.client import create_kalshi_sdk_client

print("Client loaded from:", execution.client.__file__)

KEY_ID = "e4ab09b4-8941-41c1-9d18-21ffdcdf8ed6"
PRIVATE_KEY_PATH = "/home/kalshi/.secrets/kalshi/kalshi_full_key.pem"

SERIES = "KXBTC15M"

async def main():
    client = create_kalshi_sdk_client(KEY_ID, PRIVATE_KEY_PATH)

    # 1) Discover active market
    ticker = await client.get_active_market(SERIES)
    print(f"Active ticker: {ticker}")

    # 2) Fetch market details (SIGNED)
    m = await client.get_market(ticker)
    print("Raw market dict:")
    for k, v in m.items():
        print(f"  {k}: {v}")

if __name__ == "__main__":
    asyncio.run(main())
