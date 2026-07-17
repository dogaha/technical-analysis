WITH filtered AS (
    SELECT
        contract,
        bar_date,
        bar_time,
        (
            '00:00:00'::TIME + 
            EXTRACT(HOUR FROM bar_time) * INTERVAL '1 hour'
        ) AS bar_time_bucket,
        high,
        open,
        close,
        low,
        volume
    FROM {{ ref('int_es_bars') }}
    WHERE 
        EXTRACT(ISODOW FROM bar_date) BETWEEN 1 AND 5
        AND bar_time BETWEEN '08:00:00' AND '14:59:00'
)

SELECT
    f.contract as contract,
    f.bar_date as bar_date,
    f.bar_time_bucket as bar_time,
    MAX(high) as high,
    (ARRAY_AGG(open ORDER BY f.bar_time ASC))[1] as open,
    (ARRAY_AGG(close ORDER BY f.bar_time DESC))[1] as close,
    MIN(f.low) as low,
    SUM(f.volume) as volume
FROM {{ ref('stg_cme_trading_calendar') }} cme
INNER JOIN filtered f
    ON f.bar_date = cme.bar_date
GROUP BY f.contract, f.bar_date, f.bar_time_bucket