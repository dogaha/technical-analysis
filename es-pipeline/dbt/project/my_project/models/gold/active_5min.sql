WITH filtered AS (
    SELECT
        contract,
        bar_date,
        bar_time,
        (
            '00:00:00'::TIME + 
            EXTRACT(HOUR FROM bar_time) * INTERVAL '1 hour' + 
            FLOOR(EXTRACT(MINUTE FROM bar_time)/5) * INTERVAL '5 minutes'
        ) AS bar_time_bucket,
        high,
        open,
        close,
        low,
        volume
    FROM {{ ref('int_es_bars') }}
    WHERE EXTRACT(ISODOW FROM bar_date) BETWEEN 1 AND 5
      AND bar_time BETWEEN '08:30:00' AND '15:00:00'
)
SELECT
    contract as contract,
    bar_date as bar_date,
    bar_time_bucket as bar_time,
    MAX(high) as high,
    (ARRAY_AGG(open ORDER BY bar_time ASC))[1] as open,
    (ARRAY_AGG(close ORDER BY bar_time DESC))[1] as close,
    MIN(low) as low,
    SUM(volume) as total_volume,
    ROUND(AVG(volume)) as average_volume
FROM filtered
GROUP BY contract, bar_date, bar_time_bucket