-- IVSURF storage schema (PostgreSQL)

CREATE TABLE IF NOT EXISTS bars (
    id SERIAL PRIMARY KEY,
    ticker TEXT NOT NULL,
    timeframe TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    open DOUBLE PRECISION NOT NULL,
    high DOUBLE PRECISION NOT NULL,
    low DOUBLE PRECISION NOT NULL,
    close DOUBLE PRECISION NOT NULL,
    volume DOUBLE PRECISION NOT NULL,
    source TEXT NOT NULL DEFAULT 'yfinance',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (ticker, timeframe, timestamp)
);

CREATE INDEX IF NOT EXISTS idx_bars_ticker_ts ON bars (ticker, timestamp);

CREATE TABLE IF NOT EXISTS signals (
    id SERIAL PRIMARY KEY,
    ticker TEXT NOT NULL,
    signal_type TEXT NOT NULL,
    score DOUBLE PRECISION,
    payload TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_signals_ticker_created ON signals (ticker, created_at);

CREATE TABLE IF NOT EXISTS outcomes (
    id SERIAL PRIMARY KEY,
    signal_id INTEGER NOT NULL REFERENCES signals (id),
    horizon TEXT NOT NULL,
    realized_return DOUBLE PRECISION,
    label TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_outcomes_signal ON outcomes (signal_id);
