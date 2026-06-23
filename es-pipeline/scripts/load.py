# bronze.es_bars
#   id            BIGSERIAL PRIMARY KEY,
#   bar_timestamp TEXT NOT NULL,   -- raw string, e.g. '20241213 060100'
#   open_price    NUMERIC,
#   high_price    NUMERIC,
#   low_price     NUMERIC,
#   close_price   NUMERIC,
#   volume        NUMERIC,
#   source_file   TEXT NOT NULL,
#   loaded_at     TIMESTAMP NOT NULL DEFAULT now()


try:
    # Logging
    import os
    import logging
    import psycopg2
    import io
    from dotenv import load_dotenv

    load_dotenv()
    logger = logging.getLogger("es_pipeline")
    logger.setLevel(logging.INFO)
    handler = logging.FileHandler("/opt/airflow/logs/pipeline.log")
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
    logger.addHandler(handler)

    # logging.basicConfig(
    #     filename="/opt/airflow/logs/pipeline.log",
    #     level=logging.INFO,
    #     format="%(asctime)s %(levelname)s %(message)s"
    # )

    # Ingestion
    conn = psycopg2.connect(
        host="host.docker.internal",
        port="5432",
        dbname=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD")
    )
    cur = conn.cursor()

    landingPath = "opt/airflow/data/landing"
    archivePath = "opt/airflow/data/archive"

    for instance in os.listdir(landingPath):
        if instance.endswith(".txt"):
            instancePath = os.path.join(landingPath,instance)
            if os.path.isfile(instancePath):
                try:
                    filename=os.path.basename(instancePath)
                    buffer = io.StringIO()
                    with open(instancePath,"r",encoding="utf-8") as file:
                        for line in file:
                            buffer.write(line.strip()+f";{filename}\n")
                    buffer.seek(0)

                    cur.copy_expert(
                        "COPY bronze.es_bars (bar_timestamp, open_price, high_price, low_price, close_price, volume, source_file) FROM STDIN WITH(FORMAT csv, DELIMITER ';')",
                        buffer
                    )

                    logger.info(f"Successfully Ingested {filename}")
                except Exception as e:
                    logger.exception(f"Parse Error: {filename}")
    conn.commit()
except Exception as e:
    logger.exception("Unexpected Error")
finally:
    cur.close()
    conn.close()

