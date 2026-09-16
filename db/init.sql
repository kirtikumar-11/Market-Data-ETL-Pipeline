-- Market Data Ingestion & Tick Store Schema Initialization

CREATE TABLE IF NOT EXISTS marketdata (
    id             BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    instrument_id  VARCHAR(20) NOT NULL,
    price          NUMERIC(18, 4) NOT NULL,
    volume         BIGINT NOT NULL,
    timestamp      TIMESTAMPTZ NOT NULL,
    vwap           NUMERIC(18, 4),
    is_outlier     BOOLEAN DEFAULT FALSE NOT NULL,
    ingested_at    TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT uq_marketdata_instrument_timestamp
        UNIQUE (instrument_id, timestamp)
);

-- Performance Indexes for time-series & VWAP analytics
CREATE INDEX IF NOT EXISTS idx_marketdata_instrument_timestamp 
    ON market_data (instrument_id, timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_marketdata_timestamp 
    ON market_data (timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_marketdataa_outlier 
    ON market_data (is_outlier) 
    WHERE is_outlier = TRUE;