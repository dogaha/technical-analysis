SELECT
    contract,
    bar_date,
    ('00:00:00'::time 
        + (EXTRACT(HOUR FROM bar_time)::int || ' hours')::interval 
        + (FLOOR(EXTRACT(MINUTE FROM bar_time)/30)*30 || ' minutes')::interval
    ) AS bar_time_bucket,
    SUM(volume) AS bucket_volume
FROM "futures_data"."silver"."int_es_bars"
GROUP BY contract, bar_date, bar_time_bucket