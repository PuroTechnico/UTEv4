import jwt
import time
import secrets
from cryptography.hazmat.primitives import serialization

key_name = open("/home/kalshi/.secrets/coinbase/api_key").read().strip()
key_secret = open("/home/kalshi/.secrets/coinbase/api_secret").read()

request_method = "GET"
request_path   = "/api/v3/brokerage/best_bid_ask"   # <-- CHANGE THIS PER REQUEST


def build_jwt(request_method, request_path):
    private_key = serialization.load_pem_private_key(
        key_secret.encode(),
        password=None
    )

    nonce = secrets.token_hex()

    payload = {
        "sub": key_name,
        "iss": "cdp",
        "nbf": int(time.time()),
        "exp": int(time.time()) + 120,
        "uri": f"{request_method} {request_path}",
        "nonce": nonce,
    }

    headers = {
        "kid": key_name,
        "nonce": nonce,
    }

    token = jwt.encode(
        payload,
        private_key,
        algorithm="ES256",
        headers=headers,
    )

    return token


if __name__ == "__main__":
    jwt_token = build_jwt(request_method, request_path)
    print(f'export JWT="{jwt_token}"')
