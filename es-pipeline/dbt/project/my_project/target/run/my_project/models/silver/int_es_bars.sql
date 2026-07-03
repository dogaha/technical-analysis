
  
    

  create  table "futures_data"."silver"."int_es_bars__dbt_tmp"
  
  
    as
  
  (
    /*
silver layer
    bar_date
    bar_time
    high
    open
    close
    low
    volume
    rn --this is the duplication checker
*/
WITH silver as (
    SELECT 
        contract,
        TO_TIMESTAMP(bar_timestamp,'YYYYMMDD HH24MISS')::DATE AT TIME ZONE 'UTC' AT TIME ZONE 'America/Chicago' as bar_date,
        TO_TIMESTAMP(bar_timestamp,'YYYYMMDD HH24MISS')::TIME AT TIME ZONE 'UTC' AT TIME ZONE 'America/Chicago' as bar_time,
        high::numeric,
        open::numeric,
        close::numeric,
        low::numeric,
        volume::numeric,
        row_number() OVER(PARTITION BY contract, bar_timestamp ORDER BY contract, bar_timestamp) as rn
    FROM "futures_data"."staging"."stg_es_bars"
)

SELECT * FROM silver
WHERE rn = 1
  );
  