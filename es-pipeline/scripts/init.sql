-- initalization of database for es pipeline
-- database name is futures_data

DROP SCHEMA IF EXISTS bronze CASCADE;
CREATE SCHEMA bronze;
DROP SCHEMA IF EXISTS silver CASCADE;
CREATE SCHEMA silver;
DROP SCHEMA IF EXISTS gold CASCADE;
CREATE SCHEMA gold;

-- Loaded Files
CREATE TABLE bronze.loaded_files (
    source_file  TEXT PRIMARY KEY,
    row_count    INTEGER,
    start_date   DATE,
    end_date     DATE,
    loaded_bronze_bars_at TIMESTAMP DEFAULT NULL,
    loaded_silver_bars_at TIMESTAMP DEFAULT NULL,
    loaded_silver_legs_at TIMESTAMP DEFAULT NULL,
    loaded_at    TIMESTAMP NOT NULL DEFAULT now()
);

-- Bronze: raw bars, minimal validation, mirrors NinjaTrader CSV columns
CREATE TABLE bronze.es_bars (
    source_file   TEXT NOT NULL,
    bar_timestamp TEXT NOT NULL,
    open_price    NUMERIC,
    high_price    NUMERIC,
    low_price     NUMERIC,
    close_price   NUMERIC,
    volume        NUMERIC,
    UNIQUE (source_file, bar_timestamp)
);

-- NYSE Calendar for holidays / weekends
CREATE TABLE bronze.nyse_calendar (
    date            DATE PRIMARY KEY,
    is_half_day     BOOLEAN
);
