import jwt
from cryptography.hazmat.primitives import serialization
import time
import secrets

key_name       = "organizations/0caeafca-85df-47a5-9130-c3050b88b603/apiKeys/92a1a9fd-697e-4fcb-9aed-6e59512a5442"
key_secret     = "-----BEGIN EC PRIVATE KEY-----\nMHcCAQEEIOmLIsp4S2bJ3BGQ/OJy+FMfu+PGBNYxd+uDfVf4mMGkoAoGCCqGSM49\nAwEHoUQDQgAENl0h44GD/3sb3Jn6KvhIk+JoFhGet1psE2G1CyS2+qsUVh6bRIro\nA2ow4g1q0WAosvhNt15w3/tqkpUBcjd+dg==\n-----END EC PRIVATE KEY-----\n"

request_method = "GET"
request_host   = "api.coinbase.com"
request_path   = "/api/v3/brokerage/accounts"
def build_jwt(uri):
    private_key_bytes = key_secret.encode('utf-8')
    private_key = serialization.load_pem_private_key(private_key_bytes, password=None)
    jwt_payload = {
        'sub': key_name,
        'iss': "cdp",
        'nbf': int(time.time()),
        'exp': int(time.time()) + 120,
        'uri': uri,
    }
    jwt_token = jwt.encode(
        jwt_payload,
        private_key,
        algorithm='ES256',
        headers={'kid': key_name, 'nonce': secrets.token_hex()},
    )
    return jwt_token
def main():
    uri = f"{request_method} {request_host}{request_path}"
    jwt_token = build_jwt(uri)
    print(jwt_token)
if __name__ == "__main__":
    main()
