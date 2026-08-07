{{
    config(
        pre_hook="SET timezone = 'UTC';",
        materialized='incremental',
        unique_key=['contract', 'bar_date', 'bar_time'],
        alias='es_bars'
    )
}}

WITH timezone AS(
    SELECT 
        source_file as contract,
        (TO_TIMESTAMP(bar_timestamp,'YYYYMMDD HH24MISS') AT TIME ZONE 'America/Chicago')::DATE as bar_date,
        (TO_TIMESTAMP(bar_timestamp,'YYYYMMDD HH24MISS') AT TIME ZONE 'America/Chicago')::TIME as bar_time,
        high_price::numeric as high,
        open_price::numeric as open,
        close_price::numeric as close,
        low_price::numeric as low,
        volume::numeric
    FROM {{ source('bronze','es_bars')}}
)

SELECT 
    b.contract,
    b.bar_date,
    b.bar_time,
    b.high,
    b.open,
    b.close,
    b.low,
    b.volume
FROM timezone as b
INNER JOIN bronze.loaded_files as f
    ON b.contract = f.source_file
    AND b.bar_date BETWEEN f.start_date and f.end_date
    AND f.loaded_silver_bars_at IS NULL
INNER JOIN bronze.nyse_calendar AS c
    ON b.bar_date = c.date 
    AND c.is_half_day IS FALSE
