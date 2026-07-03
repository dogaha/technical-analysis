-- initalization of database for es pipeline
-- database name is es_data

DROP SCHEMA IF EXISTS staging CASCADE;
CREATE SCHEMA staging;
DROP SCHEMA IF EXISTS bronze CASCADE;
CREATE SCHEMA bronze;
DROP SCHEMA IF EXISTS silver CASCADE;
CREATE SCHEMA silver;
DROP SCHEMA IF EXISTS gold CASCADE;
CREATE SCHEMA gold;

-- Bronze: raw bars, minimal validation, mirrors NinjaTrader CSV columns
DROP TABLE IF EXISTS bronze.es_bars;
CREATE TABLE bronze.es_bars (
    id            BIGSERIAL PRIMARY KEY,
    bar_timestamp TEXT NOT NULL,   -- raw string, e.g. '20241213 060100'
    open_price    NUMERIC,
    high_price    NUMERIC,
    low_price     NUMERIC,
    close_price   NUMERIC,
    volume        NUMERIC,
    source_file   TEXT NOT NULL
);

