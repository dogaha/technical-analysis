/*
#stg_es_bars
    nar

*/

SELECT
    source_file as contract,
    bar_timestamp,
    open_price as open,
    high_price as high,
    low_price as low,
    close_price as close,
    volume
FROM {{ source('futures_data','es_bars')}}