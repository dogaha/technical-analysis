from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime
import pandas_market_calendars as mcal
import pandas as pd
import logging
import os
from dotenv import load_dotenv, find_dotenv
from sqlalchemy import create_engine, text

logger = logging.getLogger("calendar_pipeline")
logger.setLevel(logging.INFO)
handler = logging.FileHandler("/opt/airflow/logs/pipeline.log")
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)

START_YEAR= str(2006)
END_YEAR= str(datetime.now().year)

def load_calendar():
    load_dotenv()

    engine = create_engine(
        f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
        f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT')}/{os.getenv('POSTGRES_DB')}"
    )

    cme = mcal.get_calendar('NYSE')
    schedule = cme.schedule(start_date=START_YEAR+'-01-01', end_date=END_YEAR+'-12-31')

    local_close = schedule['market_close'].dt.tz_convert('America/Chicago')
    regular_close = local_close.dt.time.mode()[0]
    # full_days = schedule[schedule['market_close'].dt.time.eq(regular_close)]
    trading_days = pd.DataFrame({
        'date': schedule.index.normalize().date,
        'is_half_day': local_close.dt.time.ne(regular_close)
    })

    trading_days.to_sql(
        'nyse_calendar',
        engine,
        schema='bronze',
        if_exists='replace',
        index=False
    )

with DAG(
    dag_id='refresh_nyse_calendar',
    schedule='@yearly',   
    start_date=datetime(2025, 1, 1),
    catchup=False,
) as dag:
    calendar_task = PythonOperator(
        task_id='refresh_nyse_calendar',
        python_callable=load_calendar,
    )

    calendar_task