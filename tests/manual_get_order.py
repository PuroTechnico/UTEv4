import aiohttp
import asyncio
import time, json, base64
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

KEY_ID = "8256582b-74c1-4733-baa7-ad21aa1c15a4"  # <-- fill in
KEY_PATH = "/home/kalshi/.secrets/kalshi_rest_secret/kalshi_rest_key.pem"
ORDER_ID = "2b2996f5-13a4-4895-90b1-d72bb612d5ec"

async def main():
    # Load private key
    with open(KEY_PATH, "rb") as f:
        private_key = serialization.load_pem_private_key(f.read(), password=None)

    # Timestamp in ms
    ts = str(int(time.time() * 1000))

    method = "GET"
    path = f"/trade-api/v2/portfolio/orders/{ORDER_ID}"

    # Signing string
    msg = f"{ts}{method}{path}".encode("utf-8")

    # RSA-PSS signature
    sig = private_key.sign(
        msg,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )

    sig_b64 = base64.b64encode(sig).decode()

    headers = {
        "KALSHI-ACCESS-KEY": KEY_ID,
        "KALSHI-ACCESS-TIMESTAMP": ts,
        "KALSHI-ACCESS-SIGNATURE": sig_b64,
    }

    url = f"https://api.elections.kalshi.com{path}"

    print("Querying:", url)
    print("Headers:", headers)

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            print("Status:", resp.status)
            print("Response:", await resp.text())

asyncio.run(main())
