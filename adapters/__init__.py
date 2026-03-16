# Clean __init__ for adapters package
# Only expose the real, existing adapters

from .kalshi_adapter import KalshiAdapter
from .kalshi_rest_adapter import KalshiRESTAdapter
from .kalshi_ws_adapter import KalshiWebSocketAdapter
from .crypto_s3_adapter import CryptoS3Adapter

__all__ = [
    "KalshiAdapter",
    "KalshiRESTAdapter",
    "KalshiWebSocketAdapter",
    "CryptoS3Adapter",
]
