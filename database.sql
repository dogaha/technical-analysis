-- initalization of database for es pipeline
-- database name is es_data

CREATE SCHEMA IF NOT EXISTS bronze;
CREATE SCHEMA IF NOT EXISTS silver;
CREATE SCHEMA IF NOT EXISTS gold;

-- Bronze: raw bars, minimal validation, mirrors NinjaTrader CSV columns
CREATE TABLE IF NOT EXISTS bronze.es_bars (
    id            BIGSERIAL PRIMARY KEY,
    bar_timestamp TEXT NOT NULL,   -- raw string, e.g. '20241213 060100'
    open_price    NUMERIC,
    high_price    NUMERIC,
    low_price     NUMERIC,
    close_price   NUMERIC,
    volume        NUMERIC,
    source_file   TEXT NOT NULL,
    loaded_at     TIMESTAMP NOT NULL DEFAULT now()
);
 
-- Tracks which files have already been ingested, so Airflow doesn't reload them
CREATE TABLE IF NOT EXISTS bronze.ingested_files (
    id           BIGSERIAL PRIMARY KEY,
    file_name    TEXT NOT NULL UNIQUE,
    ingested_at  TIMESTAMP NOT NULL DEFAULT now(),
    row_count    INTEGER
);

--Silver 
