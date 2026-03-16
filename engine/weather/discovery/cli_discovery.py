# engine/weather/discovery/cli_discovery.py — v1.0.0
# Smart Discovery: CLI settlement URL lookup

from typing import Dict, Any, Optional


class CliDiscovery:
    """
    Discovers CLI settlement URLs from taxonomy.
    Cached because CLI URLs are static per market.
    """

    def __init__(self, series_data: Optional[Dict[str, Any]]):
        self._series_data = series_data or {}
        self._cache: Dict[str, str] = {}

    async def get_cli_url(self, ticker: str) -> Optional[str]:
        if ticker in self._cache:
            return self._cache[ticker]

        # TODO: integrate with your dynamic series taxonomy
        cli_url = self._series_data.get(ticker, {}).get("cli_url")
        self._cache[ticker] = cli_url
        return cli_url
