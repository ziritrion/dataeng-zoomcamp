import os
import logging

from airflow import DAG
from airflow.utils.dates import days_ago

from airflow.providers.google.cloud.operators.bigquery import BigQueryCreateExternalTableOperator, BigQueryInsertJobOperator
from airflow.providers.google.cloud.transfers.gcs_to_gcs import GCSToGCSOperator

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
BUCKET = os.environ.get("GCP_GCS_BUCKET")
path_to_local_home = os.environ.get("AIRFLOW_HOME", "/opt/airflow/")
BIGQUERY_DATASET = os.environ.get("BIGQUERY_DATASET", 'trips_data_all')

DATASET = "tripdata"
TAXI_TYPES = {'yellow': 'tpep_pickup_datetime', 'fhv': 'Pickup_datetime', 'green': 'lpep_pickup_datetime'}
#TAXI_TYPES = {'yellow': 'tpep_pickup_datetime'}
INPUT_PART = "raw"
#INPUT_FILETYPE = "parquet"

default_args = {
    "owner": "airflow",
    "start_date": days_ago(1),
    "depends_on_past": False,
    "retries": 1,
}

# NOTE: DAG declaration - using a Context Manager (an implicit way)
with DAG(
    dag_id="gcs_2_bq_dag",
    schedule_interval="@daily",
    default_args=default_args,
    catchup=False,
    max_active_runs=1,
    tags=['dtc-de'],
) as dag:

    for taxi_type, ds_col in TAXI_TYPES.items():

        gcs_2_gcs_task = GCSToGCSOperator(
            task_id=f'move_{taxi_type}_{DATASET}_files_task',
            source_bucket=BUCKET,
            #source_object=f'{INPUT_PART}/{taxi_type}_*.{INPUT_FILETYPE}',
            source_object=f'{INPUT_PART}/{taxi_type}_*',
            destination_bucket=BUCKET,
            #destination_object=f'{taxi_type}/{taxi_type}_{DATASET}*.{INPUT_FILETYPE}',
            destination_object=f'{taxi_type}/{taxi_type}_',
            move_object=False
        )

        gcs_2_bq_ext_task = BigQueryCreateExternalTableOperator(
            task_id=f"bq_{taxi_type}_{DATASET}_external_table_task",
            table_resource={
                "tableReference": {
                    "projectId": PROJECT_ID,
                    "datasetId": BIGQUERY_DATASET,
                    "tableId": f"{taxi_type}_{DATASET}_external_table",
                },
                "externalDataConfiguration": {
                    "autodetect": "True",
                    "sourceFormat": "PARQUET",
                    "sourceUris": [f"gs://{BUCKET}/{taxi_type}/*"],
                },
            },
        )

        CREATE_BQ_TBL_QUERY = (
            f"CREATE OR REPLACE TABLE {BIGQUERY_DATASET}.{taxi_type}_{DATASET} \
            PARTITION BY DATE({ds_col}) \
            AS \
            SELECT * FROM {BIGQUERY_DATASET}.{taxi_type}_{DATASET}_external_table;"
        )

        bq_ext_2_part_task = BigQueryInsertJobOperator(
            task_id=f"bq_create_{taxi_type}_{DATASET}_partitioned_table_task",
            configuration={
                "query": {
                    "query": CREATE_BQ_TBL_QUERY,
                    "useLegacySql": False,
                }
            }
        )

        gcs_2_gcs_task >> gcs_2_bq_ext_task >> bq_ext_2_part_task