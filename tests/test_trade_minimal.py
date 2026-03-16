import requests
import datetime
import base64
import uuid
import json
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.asymmetric import padding
from datetime import timezone

# --- Configuration ---
API_KEY_ID = '8256582b-74c1-4733-baa7-ad21aa1c15a4'
PRIVATE_KEY_PATH = '/home/kalshi/.secrets/kalshi_rest_secret/kalshi_rest_key.pem'
# FIX: Use trading-api for BTC 15m markets
BASE_URL = 'https://api.elections.kalshi.com'  # ← this is the current production URL 
ORDERS_PATH = '/trade-api/v2/portfolio/orders'
MARKETS_PATH = '/trade-api/v2/markets'
SERIES = 'KXBTC15M'
# FIX: Ensure ticker does not have extra suffixes like -00
TICKER = 'KXBTC15M-26MAR070045' 
SIDE = 'yes'
PRICE = 45 
COUNT = 1 

def load_private_key(key_path):
    with open(key_path, "rb") as f:
        return serialization.load_pem_private_key(f.read(), password=None, backend=default_backend())

def create_signature(private_key, timestamp, method, path):
    # FIX: Kalshi V2 signature is strictly: Timestamp + Method + Path
    path_without_query = path.split('?')[0]
    message = f"{timestamp}{method.upper()}{path_without_query}"
    
    print(f"Signing message: {message}")
    
    sig = private_key.sign(
        message.encode('utf-8'),
        padding.PSS(mgf=padding.MGF1(hashes.SHA256()), salt_length=padding.PSS.DIGEST_LENGTH),
        hashes.SHA256()
    )
    return base64.b64encode(sig).decode('utf-8')

def get_active_ticker(series):
    params = {'series_ticker': series, 'status': 'open', 'limit': 1}
    # Public endpoints also use the trading-api domain
    url = f"{BASE_URL}{MARKETS_PATH}"
    response = requests.get(url, params=params)
    if response.status_code == 200:
        markets = response.json().get('markets', [])
        if markets:
            return markets[0]['ticker']
    print("No active market found—using fallback TICKER")
    return TICKER

# --- Execution ---
private_key = load_private_key(PRIVATE_KEY_PATH)
ticker = get_active_ticker(SERIES)
print(f"Targeting Ticker: {ticker}")

timestamp_str = str(int(datetime.datetime.now(timezone.utc).timestamp() * 1000))

# Sign without the body
signature = create_signature(private_key, timestamp_str, "POST", ORDERS_PATH)

body = {
    "ticker": ticker,
    "action": "buy",
    "side": SIDE,
    "count": COUNT,
    "type": "limit",
    "yes_price": PRICE if SIDE == 'yes' else None,
    "no_price": PRICE if SIDE == 'no' else None,
    "client_order_id": str(uuid.uuid4())
}

headers = {
    'Content-Type': 'application/json',
    'KALSHI-ACCESS-KEY': API_KEY_ID,
    'KALSHI-ACCESS-SIGNATURE': signature,
    'KALSHI-ACCESS-TIMESTAMP': timestamp_str
}

print(f"Requesting: {BASE_URL}{ORDERS_PATH}")
response = requests.post(f"{BASE_URL}{ORDERS_PATH}", headers=headers, json=body, timeout=10)

print(f"Response Status: {response.status_code}")
print(f"Response Text: {response.text}")

if response.status_code == 201:
    order = response.json().get('order', {})
    print(f"✅ Success! Order ID: {order.get('order_id')}")
else:
    print("❌ Order failed.")
