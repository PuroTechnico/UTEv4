# pipelines/snapshot_pipeline.py — v4.0.0 (FULL ASYNC)
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional

from adapters.crypto_s3_adapter import CryptoS3Adapter
from adapters.kalshi_rest_adapter import KalshiRESTAdapter
from database.db import get_table_columns, insert, to_json
from discovery.market_locator import CryptoMarketLocator
from models.snapshots import MarketSnapshot

logger = logging.getLogger("SnapshotPipeline")


class SnapshotPipeline:
    """
    Fully async snapshot pipeline for UTE v4.
    Responsible for:
        • Fetching active crypto markets
        • Fetching market data from Kalshi
        • Writing snapshots to DB
    """

    def __init__(
        self,
        universe,
        kalshi: KalshiRESTAdapter,
        locator: CryptoMarketLocator,
        crypto_s3: Optional[CryptoS3Adapter] = None,
    ):
        self.universe = universe
        self.kalshi = kalshi
        self.locator = locator
        self.crypto_s3 = crypto_s3

    # ------------------------------------------------------------
    # PUBLIC ENTRYPOINT
    # ------------------------------------------------------------
    async def run(self) -> Dict[str, Dict]:
        """
        Execute the full snapshot pipeline.

        Returns the v3.2 engine-compatible structure:
            {
                "market": {ticker: MarketSnapshot, ...},
                "crypto_s3": {symbol: snapshot, ...},
                "weather": {ticker: weather_record, ...},
            }
        """
        logger.info("SnapshotPipeline: starting run")

        market_snapshots = await self._fetch_all_markets()
        crypto_s3_snapshots = await self._fetch_crypto_s3_snapshots()
        weather_snapshots = await self._fetch_weather_snapshots()

        logger.info(
            "SnapshotPipeline: completed run - markets=%d crypto_s3=%d weather=%d",
            len(market_snapshots),
            len(crypto_s3_snapshots),
            len(weather_snapshots),
        )

        return {
            "market": market_snapshots,
            "crypto_s3": crypto_s3_snapshots,
            "weather": weather_snapshots,
        }

    # ------------------------------------------------------------
    # INTERNAL: FETCH ALL ACTIVE MARKETS (FULL ASYNC)
    # ------------------------------------------------------------
    async def _fetch_all_markets(self) -> Dict[str, MarketSnapshot]:
        out: Dict[str, MarketSnapshot] = {}
        now = datetime.now(timezone.utc)

        # Combine all crypto series families
        all_crypto_series: List[Dict] = (
            self.universe["crypto_15m"]
            + self.universe["crypto_hourly"]
            + self.universe["crypto_daily"]
        )

        # --------------------------------------------------------
        # Iterate through each series and discover active markets
        # --------------------------------------------------------
        logger.debug(
            "SnapshotPipeline: fetching markets for %d crypto series",
            len(all_crypto_series),
        )

        for series in all_crypto_series:
            active_markets = await self.locator.locate(series, now)
            if not active_markets:
                logger.warning(
                    "SnapshotPipeline: no active markets for series %s",
                    series.get("ticker"),
                )

            for ticker in active_markets:
                # Fetch market details from Kalshi
                try:
                    resp = await self.kalshi.get_market(ticker)
                except Exception as exc:
                    logger.warning(
                        "SnapshotPipeline: failed to fetch market %s: %s", ticker, exc
                    )
                    continue
                market = resp.get("market", resp)

                yes_price = float(market.get("yes_bid") or 0) / 100.0
                no_price = float(market.get("no_bid") or 0) / 100.0
                spread = abs(yes_price - no_price)
                volume = int(market.get("volume") or 0)
                tte_minutes = float(market.get("tte_minutes") or 0)

                snap = MarketSnapshot(
                    venue_id="kalshi",
                    ticker=ticker,
                    yes_price=yes_price,
                    no_price=no_price,
                    spread=spread,
                    volume=volume,
                    tte_minutes=tte_minutes,
                    timestamp=now,
                    liquidity_metrics=None,
                    volatility_metrics=None,
                )

                # Persist snapshot
                insert(
                    "market_snapshot",
                    {
                        "venue_id": snap.venue_id,
                        "ticker": snap.ticker,
                        "yes_price": snap.yes_price,
                        "no_price": snap.no_price,
                        "spread": snap.spread,
                        "volume": snap.volume,
                        "tte_minutes": snap.tte_minutes,
                        "timestamp": snap.timestamp.isoformat(),
                        "liquidity_metrics": snap.liquidity_metrics,
                        "volatility_metrics": snap.volatility_metrics,
                    },
                )

                out[ticker] = snap

        return out

    # ------------------------------------------------------------
    # INTERNAL: FETCH CRYPTO S3 MARKET SNAPSHOTS (SYNC API)
    # ------------------------------------------------------------
    async def _fetch_crypto_s3_snapshots(self) -> Dict[str, Dict]:
        out: Dict[str, Dict] = {}
        if self.crypto_s3 is None:
            logger.info(
                "SnapshotPipeline: crypto_s3 adapter missing, skipping S3 snapshots"
            )
            return out

        logger.debug("SnapshotPipeline: fetching crypto_s3 snapshots")
        for symbol in ["BTC", "ETH", "XRP", "SOL", "DOGE"]:
            snapshot = self.crypto_s3.build_snapshot(symbol)
            if snapshot is None:
                continue

            columns = set(get_table_columns("crypto_snapshot"))
            if "symbol" in columns:
                insert(
                    "crypto_snapshot",
                    {
                        "symbol": snapshot.symbol,
                        "maturity_ts_ms": snapshot.maturity_ts_ms,
                        "live_price": snapshot.live_price,
                        "candle_1m": to_json(snapshot.candle_1m),
                        "candle_15m": to_json(snapshot.candle_15m),
                        "candle_1h": to_json(snapshot.candle_1h),
                        "candle_6h": to_json(snapshot.candle_6h),
                        "second_series": to_json(snapshot.second_series),
                        "snapshot_ts": snapshot.snapshot_ts.isoformat(),
                    },
                )
            else:
                # Legacy schema compatibility (pre-v4 crypto_snapshot)
                insert(
                    "crypto_snapshot",
                    {
                        "venue_id": "crypto_s3",
                        "asset": snapshot.symbol,
                        "price": snapshot.live_price,
                        "timestamp": snapshot.snapshot_ts.isoformat(),
                        "vol_1h": None,
                        "vol_24h": None,
                        "sparkline": None,
                    },
                )

            out[symbol] = {
                "live_price": snapshot.live_price,
                "maturity_ts_ms": snapshot.maturity_ts_ms,
                "snapshot_ts": snapshot.snapshot_ts.isoformat(),
            }

        return out

    # ------------------------------------------------------------
    # INTERNAL: FETCH WEATHER SNAPSHOTS (BASIC)
    # ------------------------------------------------------------
    async def _fetch_weather_snapshots(self) -> Dict[str, Dict]:
        out: Dict[str, Dict] = {}
        now = datetime.now(timezone.utc)

        weather_series = self.universe.get("weather", [])
        logger.debug(
            "SnapshotPipeline: fetching weather snapshots for %d series",
            len(weather_series),
        )

        for series in weather_series:
            ticker = series.get("ticker")
            if not ticker:
                logger.warning(
                    "SnapshotPipeline: weather series missing ticker, skipping"
                )
                continue

            try:
                resp = await self.kalshi.get_market(ticker)
            except Exception:
                continue

            market = resp.get("market", resp)

            # Required fields by schema must be present as non-null values.
            location_name = series.get("title", ticker)
            lat = float(series.get("lat", 0.0) or 0.0)
            lon = float(series.get("lon", 0.0) or 0.0)
            expected_high = float(market.get("yes_bid") or 0) / 100.0
            asos_temp = None
            oracle_timestamp = now.isoformat()
            strikes_f = to_json(series.get("strikes", [])) or "[]"
            strike_type_by_strike = (
                to_json(series.get("strike_type_by_strike", {})) or "{}"
            )
            kalshi_ticker_by_strike = (
                to_json(series.get("kalshi_ticker_by_strike", {})) or "{}"
            )
            yes_bid = str(market.get("yes_bid") or "0")
            yes_ask = str(market.get("yes_ask") or "0")
            no_bid = str(market.get("no_bid") or "0")
            no_ask = str(market.get("no_ask") or "0")
            model_prob_by_strike = (
                to_json(series.get("model_prob_by_strike", {})) or "{}"
            )

            insert(
                "weather_snapshot",
                {
                    "location_name": location_name,
                    "lat": lat,
                    "lon": lon,
                    "station_id": series.get("station_id", ""),
                    "expected_high": expected_high,
                    "asos_temp": asos_temp,
                    "oracle_timestamp": oracle_timestamp,
                    "strikes_f": strikes_f,
                    "strike_type_by_strike": strike_type_by_strike,
                    "kalshi_ticker_by_strike": kalshi_ticker_by_strike,
                    "yes_bid": yes_bid,
                    "yes_ask": yes_ask,
                    "no_bid": no_bid,
                    "no_ask": no_ask,
                    "model_prob_by_strike": model_prob_by_strike,
                },
            )

            out[ticker] = {
                "location_name": location_name,
                "lat": lat,
                "lon": lon,
                "expected_high": expected_high,
                "oracle_timestamp": oracle_timestamp,
            }

        return out
