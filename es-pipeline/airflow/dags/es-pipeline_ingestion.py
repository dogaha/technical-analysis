from airflow import DAG
from airflow.sensors.filesystem import FileSensor
from airflow.operators.bash import BashOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
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
        timeout=60*5
    )
    run_load = BashOperator(
        task_id="run_load",
        bash_command="python /opt/airflow/load.py"
    )

    trigger_self = TriggerDagRunOperator(
        task_id="trigger_self",
        trigger_dag_id="es_pipeline_ingest",  # same DAG id
        wait_for_completion=False
    )
    
    wait_for_file >> run_load>> trigger_self