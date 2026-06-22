# Silver es-data
# id            BIGSERIAL PRIMARY KEY,
# bar_timestamp TEXT NOT NULL,   -- raw string, e.g. '20241213 060100'
# open_price    NUMERIC,
# high_price    NUMERIC,
# low_price     NUMERIC,
# close_price   NUMERIC,
# volume        NUMERIC,
# source_file   TEXT NOT NULL,
# loaded_at     TIMESTAMP NOT NULL DEFAULT now()


try:
    # Logging
    import os
    import logging
    import psycopg2
    from dotenv import load_dotenv

    load_dotenv()
    logging.basicConfig(
        filename="/opt/airflow/logs/pipeline.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s"
    )

    # Ingestion
    conn = psycopg2.connect(
        host="host.docker.internal",
        port="5432",
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )
    

    cur = conn.cursor()
    conn.commit()
    logging.info("Successful Ingestion")
except Exception as e:
    logging.exception("Unexpected Error")
finally:
    cur.close()
    conn.close()

