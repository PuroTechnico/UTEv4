-- ============================================================
-- UTE v3.3 — Canonical Typed Schema v4.1
-- Coinbase removed, Crypto S3 added
-- ============================================================

PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

-- ------------------------------------------------------------
-- 1. Market Snapshots (Kalshi)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS market_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venue_id TEXT NOT NULL,
    ticker TEXT NOT NULL,
    yes_price REAL NOT NULL,
    no_price REAL NOT NULL,
    spread REAL NOT NULL,
    volume INTEGER NOT NULL,
    tte_minutes REAL NOT NULL,
    timestamp TEXT NOT NULL,
    liquidity_metrics TEXT,
    volatility_metrics TEXT
);

CREATE INDEX IF NOT EXISTS idx_market_snapshot_ticker_time
ON market_snapshot (ticker, timestamp DESC);

-- ------------------------------------------------------------
-- 2. Crypto Snapshots (Crypto S3 — CF Benchmarks)
-- Coinbase schema removed
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS crypto_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    symbol TEXT NOT NULL,              -- BTC, ETH, XRP, SOL, DOGE
    maturity_ts_ms INTEGER NOT NULL,   -- CF Benchmarks settlement timestamp (ms)
    live_price REAL NOT NULL,          -- Real‑time S3 price

    candle_1m TEXT,                    -- JSON list of OHLC candles
    candle_15m TEXT,
    candle_1h TEXT,
    candle_6h TEXT,

    second_series TEXT NOT NULL,       -- JSON list of second‑level prices
    snapshot_ts TEXT NOT NULL          -- ISO timestamp of snapshot
);

CREATE INDEX IF NOT EXISTS idx_crypto_snapshot_symbol_time
ON crypto_snapshot (symbol, snapshot_ts DESC);

-- ------------------------------------------------------------
-- 3. Weather Snapshots (v3.1)
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS weather_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Location metadata
    location_name TEXT NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    station_id TEXT,

    -- Oracle data
    expected_high REAL,
    asos_temp REAL,
    oracle_timestamp TEXT NOT NULL,

    -- Strike universe
    strikes_f TEXT NOT NULL,
    strike_type_by_strike TEXT NOT NULL,
    kalshi_ticker_by_strike TEXT NOT NULL,

    -- Kalshi prices
    yes_bid TEXT NOT NULL,
    yes_ask TEXT NOT NULL,
    no_bid TEXT NOT NULL,
    no_ask TEXT NOT NULL,

    -- Model probabilities
    model_prob_by_strike TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_weather_snapshot_location_time
ON weather_snapshot (location_name, oracle_timestamp DESC);

-- ------------------------------------------------------------
-- 4. Opportunity Snapshots
-- Coinbase field removed
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS opportunity_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    asset TEXT NOT NULL,
    kalshi_yes REAL NOT NULL,
    kalshi_no REAL NOT NULL,
    spread REAL NOT NULL,
    volume INTEGER NOT NULL,
    edge_score REAL NOT NULL,
    readiness REAL NOT NULL,
    tte REAL NOT NULL,
    skip_reason TEXT,
    timestamp TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_opportunity_snapshot_asset_time
ON opportunity_snapshot (asset, timestamp DESC);

-- ------------------------------------------------------------
-- 5. Execution Records
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS execution_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venue_id TEXT NOT NULL,
    ticker TEXT NOT NULL,
    side TEXT NOT NULL,
    size REAL NOT NULL,
    price REAL NOT NULL,
    timestamp TEXT NOT NULL,
    intent_id TEXT NOT NULL
);

-- ------------------------------------------------------------
-- 6. Fill Records
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fill_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venue_id TEXT NOT NULL,
    ticker TEXT NOT NULL,
    side TEXT NOT NULL,
    size REAL NOT NULL,
    price REAL NOT NULL,
    fee_cost REAL NOT NULL,
    is_taker INTEGER NOT NULL,
    created_time TEXT NOT NULL,
    trade_id TEXT
);

-- ------------------------------------------------------------
-- 7. Trade Records
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS trade_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venue_id TEXT NOT NULL,
    ticker TEXT NOT NULL,
    side TEXT NOT NULL,
    size REAL NOT NULL,
    price REAL NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT
);

-- ------------------------------------------------------------
-- 8. Settlement Records
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS settlement_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venue_id TEXT NOT NULL,
    ticker TEXT NOT NULL,
    pnl REAL NOT NULL,
    payout REAL NOT NULL,
    settled_time TEXT NOT NULL,
    trade_id TEXT
);

-- ------------------------------------------------------------
-- 9. Position Records
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS position_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    venue_id TEXT NOT NULL,
    ticker TEXT NOT NULL,
    side TEXT NOT NULL,
    count INTEGER NOT NULL,
    entry_price REAL NOT NULL,
    high_water_mark REAL NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

-- ------------------------------------------------------------
-- 10. PnL Records
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS pnl_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    equity REAL NOT NULL,
    realized REAL NOT NULL,
    unrealized REAL NOT NULL
);

-- ------------------------------------------------------------
-- 11. Metrics Records
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS metrics_record (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    sharpe REAL,
    sortino REAL,
    calmar REAL,
    max_drawdown REAL,
    win_rate REAL,
    avg_win REAL,
    avg_loss REAL,
    slippage REAL,
    liquidity_cost REAL
);

-- ------------------------------------------------------------
-- 12. Health Snapshots
-- ------------------------------------------------------------
CREATE TABLE IF NOT EXISTS health_snapshot (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    component TEXT NOT NULL,
    status TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    metadata TEXT
);

CREATE INDEX IF NOT EXISTS idx_health_snapshot_component_time
ON health_snapshot (component, timestamp DESC);
