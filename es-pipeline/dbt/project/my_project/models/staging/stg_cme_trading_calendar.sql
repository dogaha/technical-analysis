SELECT DISTINCT
    bar_date::DATE as bar_date
FROM {{ ref('cme_trading_calendar') }}
WHERE bar_date IS NOT NULL