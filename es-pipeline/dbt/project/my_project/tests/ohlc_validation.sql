-- Look for invalid higs and lows
SELECT * FROM {{ ref('int_es_bars') }}
WHERE high < low
    or high < open
    or high < close
    or low > open
    or low > close