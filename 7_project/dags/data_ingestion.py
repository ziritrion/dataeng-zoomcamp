import os
import logging

from airflow import DAG
from airflow.operators.bash import BashOperator

from datetime import datetime

from google.cloud import storage

url_prefix = 'https://data.gharchive.org/'
url = url_prefix + '{{ execution_date.strftime(\'%Y-%m-%d-%H\') }}.json.gz'
output_file = '{{ execution_date.strftime(\'%Y-%m-%d-%H\') }}.json.gz'


default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
}

with DAG(
    dag_id="gh_data_ingestion",
    schedule_interval="0 6 2 * *",
    start_date=datetime(2022, 3, 20),
    default_args=default_args,
    catchup=True,
    max_active_runs=3,
    tags=['dtc-de-project'],
) as dag:

    download_dataset_task = BashOperator(
        task_id="download_dataset_task",
        bash_command=f'curl -sSL {url} > {output_file}'
    )

    download_dataset_task