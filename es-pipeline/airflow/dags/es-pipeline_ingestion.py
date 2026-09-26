from airflow import DAG
from airflow.sensors.filesystem import FileSensor
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator

import os
import logging
import io
import re
import calendar
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta
from dotenv import load_dotenv
from sqlalchemy import create_engine, text, inspect

import sys
sys.path.insert(0, '/opt/airflow')
import utils

 
def load_bars():            
    load_dotenv()
    logger = utils.get_logger()
    landingPath = "/opt/airflow/data/landing"
    archivePath = "/opt/airflow/data/archive"
    errorsPath = "/opt/airflow/data/errors"

    # f"postgres+psycopg2://{[user]}:{[pass]}@{[host}:{[port]}/{[dbname]}"
    engine = create_engine(
        f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
        f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    )

    inspector = inspect(engine)
    
    with engine.connect() as conn:
        if not inspector.has_table('es_bars', schema='bronze'):
            logger.error(f"Table 'es_bars' does not exist within schema 'bronze'")
            raise utils.PostgresTableError()
        conn.execute(
            text("SELECT DISTINCT source_file FROM bronze.es_bars")
        )
        ingested_contracts = set(conn.execute(text("SELECT DISTINCT source_file FROM bronze.es_bars")).scalars())
            

    for instance in os.listdir(landingPath):
        if instance.endswith(".txt"):
            instancePath = os.path.join(landingPath,instance)
            if os.path.isfile(instancePath):
                conn = engine.raw_connection()
                cur = conn.cursor()
                try:
                    filename = os.path.splitext(os.path.basename(instancePath))[0]
                    utils.validate_filename(filename)
                    if filename in ingested_contracts:
                        raise utils.DuplicateContractError(f"Contract already added, skipping {filename}")
                    
                    buffer = io.StringIO()
                    first_line = None
                    last_line = None
                    row_count = 0
                    with open(instancePath,"r",encoding="utf-8") as file:
                        first_line = file.readline()
                        buffer.write(first_line.strip() + f";{filename}\n")
                        for line in file:
                            last_line = line
                            buffer.write(line.strip()+f";{filename}\n")
                            row_count += 1
                    buffer.seek(0)
                    
                    # Ingestion
                    cur.copy_expert(
                        "COPY bronze.es_bars (bar_timestamp, open_price, high_price, low_price, close_price, volume, source_file) FROM STDIN WITH(FORMAT csv, DELIMITER ';')",
                        buffer
                    )

                    start, end = utils.get_daterange(filename)
                    cur.execute(
                        "INSERT INTO bronze.loaded_files (source_file, row_count, start_date, end_date) VALUES (%s, %s, %s, %s)",
                        (filename, row_count,start,end)
                    )

                    cur.execute(
                        """
                        UPDATE bronze.loaded_files
                        SET loaded_bronze_bars_at = NOW()
                        WHERE source_file = %s
                        """,
                        (filename,)
                    )
                    conn.commit()
                    
                    os.replace(instancePath, os.path.join(archivePath, instance))
                    logger.info(f"Successfully Ingested {filename}")
                    
                except utils.DuplicateContractError as e:
                    logger.error(f"Duplicate Contract Error: {e}")
                    os.remove(instancePath)
                    continue
                except utils.ContractNameError as e:
                    logger.error(f"Contract Name Error: {e}")
                    os.replace(instancePath, os.path.join(errorsPath, instance))
                    continue
                except utils.ContractDateRangeError as e:
                    logger.error(f"Contract Date Range Error: {e}")
                    os.replace(instancePath, os.path.join(errorsPath, instance))
                    continue
                except Exception as e:
                    logger.error(f"Failed To Load {filename}: {e}")
                    os.replace(instancePath, os.path.join(errorsPath, instance))
                    if conn:
                        conn.rollback()
                    continue
                finally:
                    if cur:
                        cur.close()
                    if conn:
                        conn.close()

def update_silver_bars_load_timestamp():
    engine = create_engine(
        f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
        f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    )

    with engine.connect() as conn:
        conn.execute(
            text("""
                UPDATE bronze.loaded_files
                SET loaded_silver_bars_at = NOW()
                WHERE loaded_silver_bars_at IS NULL
            """)
        )
        conn.commit()

def load_legs():
    load_dotenv()
    logger = utils.get_logger()
    # f"postgres+psycopg2://{[user]}:{[pass]}@{[host}:{[port]}/{[dbname]}"
    engine = create_engine(
        f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
        f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    )

    df_all = pd.read_sql(
        """
        SELECT b.* FROM silver.es_bars b
        INNER JOIN bronze.loaded_files f ON b.contract = f.source_file
        WHERE f.loaded_silver_legs_at IS NULL
        ORDER BY contract, bar_date, bar_time
        """,
        engine
    )

    for contract, df in df_all.groupby('contract'):
        try:
            df_legs = utils.get_legs(df)            
            df_legs.to_sql(
                'es_legs',
                engine,
                schema='gold',
                if_exists='append',
                index=False
            )
    
            with engine.connect() as conn:
                conn.execute(
                    text("""
                        UPDATE bronze.loaded_files
                        SET loaded_gold_legs_at = :timestamp
                        WHERE source_file = :contract
                    """),
                    {"timestamp": pd.Timestamp.now(), "contract":contract}
                    
                )
                conn.commit()
            logger.info(f"Successfully Loaded {contract}")
        except Exception as e:
            logger.error(f"Failed To Load {contract}: {e}")
   
with DAG(
    dag_id="es_pipeline_ingest",
    start_date=datetime(2026,6,20),
    schedule=None,
    catchup=False
) as dag:

    wait_task = FileSensor(
        task_id="wait_for_file",
        fs_conn_id="fs_default",
        filepath="/opt/airflow/data/landing/*.txt",
        poke_interval=15,
        timeout=60*2
    )
    bronze_task = PythonOperator(
        task_id='load_bronze',
        python_callable=load_bars
    )

    dbt_task = BashOperator(
        task_id="run_dbt_models",
        bash_command="docker exec dbt_container dbt run --select silver"
    )

    timestamp_task = PythonOperator(
        task_id="update_silver_bars_timestamp",
        python_callable=update_silver_bars_load_timestamp
    )

    leg_task = PythonOperator(
        task_id='load_legs',
        python_callable=load_legs
    )
    
    wait_task >> bronze_task >> dbt_task >> timestamp_task >> leg_task