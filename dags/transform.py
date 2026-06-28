from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.sensors.external_task import ExternalTaskSensor

DBT_DIR = "/opt/airflow/dbt_project"
DBT_CMD = f"cd {DBT_DIR} && dbt {{}} --profiles-dir ."

default_args = {
    "owner": "creatorradar",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="transform",
    description="dbt staging → intermediate → marts, triggered after youtube_ingest succeeds.",
    schedule="0 8 * * *",  # 08:00 UTC = 11:00 Turkey — 2h after youtube_ingest
    start_date=datetime(2026, 6, 29),
    catchup=True,
    max_active_runs=1,
    default_args=default_args,
    tags=["dbt", "transform"],
) as dag:

    wait_for_ingest = ExternalTaskSensor(
        task_id="wait_for_ingest",
        external_dag_id="youtube_ingest",
        external_task_id=None,  # wait for the whole DAG
        allowed_states=["success"],
        execution_delta=timedelta(hours=2),  # ingest runs at 06:00, transform at 08:00
        timeout=3600,
        poke_interval=60,
        mode="reschedule",
    )

    dbt_run_staging = BashOperator(
        task_id="dbt_run_staging",
        bash_command=DBT_CMD.format("run --select staging"),
    )

    dbt_test_staging = BashOperator(
        task_id="dbt_test_staging",
        bash_command=DBT_CMD.format("test --select staging"),
    )

    dbt_run_intermediate = BashOperator(
        task_id="dbt_run_intermediate",
        bash_command=DBT_CMD.format("run --select intermediate"),
    )

    dbt_run_marts = BashOperator(
        task_id="dbt_run_marts",
        bash_command=DBT_CMD.format("run --select marts"),
    )

    dbt_test_marts = BashOperator(
        task_id="dbt_test_marts",
        bash_command=DBT_CMD.format("test --select marts"),
    )

    (
        wait_for_ingest
        >> dbt_run_staging
        >> dbt_test_staging
        >> dbt_run_intermediate
        >> dbt_run_marts
        >> dbt_test_marts
    )
