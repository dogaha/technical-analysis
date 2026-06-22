from airflow import DAG
from airflow.sensors.filesystem import FileSensor
from airflow.operators.bash import BashOperator
from datetime import datetime

with DAG(
    dag_id="es_pipeline_ingest",
    start_date=datetime(2026,6,20),
    schedule=None,
    catchup=False
) as dag:

    wait_for_file = FileSensor(
        task_id="wait_for_file",
        fs_conn_id="fs_default",
        filepath="/opt/airflow/data/landing/*.txt",
        poke_interval=30,
        timeout=60*60
    )
    run_load = BashOperator(
        task_id="run_load",
        bash_command="python /opt/airflow/load.py"
    )
    wait_for_file >> run_load