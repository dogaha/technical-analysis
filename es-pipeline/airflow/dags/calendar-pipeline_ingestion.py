from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime
import pandas_market_calendars as mcal
import pandas as pd
import logging
import os

logger = logging.getLogger("calendar_pipeline")
logger.setLevel(logging.INFO)
handler = logging.FileHandler("/opt/airflow/logs/pipeline.log")
handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(message)s"))
logger.addHandler(handler)

SEED_PATH = "/dbt_project/seeds/cme_trading_calendar.csv"
START_YEAR= str(2020)
END_YEAR= str(datetime.now().year + 3)

def generate_csv_calendar():
    cme = mcal.get_calendar('NYSE')
    schedule = cme.schedule(start_date=START_YEAR+'-01-01', end_date=END_YEAR+'-12-31')

    trading_days = pd.DataFrame({
        'bar_date': schedule.index.normalize().date
    })

    os.makedirs(os.path.dirname(SEED_PATH),exist_ok=True)
    trading_days.to_csv(SEED_PATH,index=False)
    logger.info('Successfully Wrote CME Calendar CSV')




with DAG(
    dag_id='refresh_cme_calendar',
    schedule='@yearly',   
    start_date=datetime(2025, 1, 1),
    catchup=False,
) as dag:
    gen_csv = PythonOperator(
        task_id='refresh_cme_calendar',
        python_callable=generate_csv_calendar,
    )
    dbt_seed = BashOperator(
        task_id='dbt_seed_calendar',
        bash_command="docker exec dbt_container dbt seed --select cme_trading_calendar",
    )

    gen_csv >> dbt_seed