WITH filtered AS (
    SELECT
        contract,
        bar_date,
        bar_time,
        high,
        open,
        close,
        low,
        volume
    FROM {{ ref('int_es_bars') }}
    WHERE EXTRACT(ISODOW FROM bar_date) BETWEEN 1 AND 5
      AND bar_time BETWEEN '08:00:00' AND '14:59:00'
)

SELECT
    f.contract,
    f.bar_date,
    f.bar_time,
    f.high,
    f.open,
    f.close,
    f.low,
    f.volume
FROM {{ ref('stg_cme_trading_calendar') }} cme
INNER JOIN filtered f
    ON f.bar_date = cme.bar_date