import os
import logging

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

from airflow.providers.google.cloud.operators.bigquery import BigQueryCreateExternalTableOperator, BigQueryInsertJobOperator

from datetime import datetime

from google.cloud import storage

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
BUCKET = os.environ.get("GCP_GCS_BUCKET")
DATASET = "gh"
BIGQUERY_DATASET = os.environ.get("BIGQUERY_DATASET", 'gh_archive_all')

url_prefix = 'https://data.gharchive.org/'
file_template = '{{ execution_date.strftime(\'%Y-%m-%d-%-H\') }}.json.gz'
url = url_prefix + file_template
path_to_local_home = os.environ.get("AIRFLOW_HOME", "/opt/airflow/")

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
}

def upload_to_gcs(bucket, object_name, local_file):
    """
    Ref: https://cloud.google.com/storage/docs/uploading-objects#storage-upload-object-python
    :param bucket: GCS bucket name
    :param object_name: target path & file-name
    :param local_file: source path & file-name
    :return:
    """
    # WORKAROUND to prevent timeout for files > 6 MB on 800 kbps upload speed.
    # (Ref: https://github.com/googleapis/python-storage/issues/74)
    storage.blob._MAX_MULTIPART_SIZE = 5 * 1024 * 1024  # 5 MB
    storage.blob._DEFAULT_CHUNKSIZE = 5 * 1024 * 1024  # 5 MB
    # End of Workaround

    client = storage.Client()
    bucket = client.bucket(bucket)

    blob = bucket.blob(object_name)
    blob.upload_from_filename(local_file)

with DAG(
    dag_id="gh_data_ingestion",
    schedule_interval="30 * * * *",
    start_date=datetime(2022, 3, 25),
    default_args=default_args,
    catchup=True,
    max_active_runs=3,
    tags=['dtc-de-project'],
) as dag:

    download_dataset_task = BashOperator(
        task_id="download_dataset_task",
        bash_command=f'curl -sSLf {url} > {path_to_local_home}/{file_template}'
    )

    local_to_gcs_task = PythonOperator(
        task_id="local_to_gcs_task",
        python_callable=upload_to_gcs,
        op_kwargs={
            "bucket": BUCKET,
            "object_name": f"raw/{file_template}",
            "local_file": f"{path_to_local_home}/{file_template}",
        },
    )

    gcs_2_bq_ext_task = BigQueryCreateExternalTableOperator(
        task_id=f"bq_{DATASET}_external_table_task",
        table_resource={
            "tableReference": {
                "projectId": PROJECT_ID,
                "datasetId": BIGQUERY_DATASET,
                "tableId": f"{DATASET}_external_table",
            },
            "schema": {
                "fields": [
                    {
                        "name": "type",
                        "type": "STRING",
                        "description": "https://developer.github.com/v3/activity/events/types/"
                    },
                    {
                        "name": "public",
                        "type": "BOOLEAN",
                        "description": "Always true for this dataset since only public activity is recorded."
                    },
                    {
                        "name": "payload",
                        "type": "STRING",
                        "description": "Event payload in JSON format"
                    },
                    {
                        "name": "repo",
                        "type": "RECORD",
                        "description": "Repository associated with the event",
                        "fields": [
                            {
                                "name": "id",
                                "type": "INTEGER",
                                "description": "Numeric ID of the GitHub repository"
                            },
                            {
                                "name": "name",
                                "type": "STRING",
                                "description": "Repository name"
                            },
                            {
                                "name": "url",
                                "type": "STRING",
                                "description": "Repository URL"
                            }
                        ]
                    },
                    {
                        "name": "actor",
                        "type": "RECORD",
                        "description": "Actor generating the event",
                        "fields": [
                            {
                                "name": "id",
                                "type": "INTEGER",
                                "description": "Numeric ID of the GitHub actor"
                            },
                            {
                                "name": "login",
                                "type": "STRING",
                                "description": "Actor's GitHub login"
                            },
                            {
                                "name": "gravatar_id",
                                "type": "STRING",
                                "description": "Actor's Gravatar ID"
                            },
                            {
                            "name": "avatar_url",
                            "type": "STRING",
                            "description": "Actor's Gravatar URL"
                            },
                            {
                            "name": "url",
                            "type": "STRING",
                            "description": "Actor's profile URL"
                            }
                        ]
                    },
                    {
                        "name": "org",
                        "type": "RECORD",
                        "description": "GitHub org of the associated repo",
                        "fields": [
                            {
                                "name": "id",
                                "type": "INTEGER",
                                "description": "Numeric ID of the GitHub org"
                            },
                            {
                                "name": "login",
                                "type": "STRING",
                                "description": "Org's GitHub login"
                            },
                            {
                                "name": "gravatar_id",
                                "type": "STRING",
                                "description": "Org's Gravatar ID"
                            },
                            {
                                "name": "avatar_url",
                                "type": "STRING",
                                "description": "Org's Gravatar URL"
                            },
                            {
                                "name": "url",
                                "type": "STRING",
                                "description": "Org's profile URL"
                            }
                        ]
                    },
                    {
                        "name": "created_at",
                        "type": "TIMESTAMP",
                        "description": "Timestamp of associated event"
                    },
                    {
                        "name": "id",
                        "type": "STRING",
                        "description": "Unique event ID"
                    },
                    {
                        "name": "other",
                        "type": "STRING",
                        "description": "Unknown fields in JSON format"
                    }
                ]
            },
            "externalDataConfiguration": {
                "autodetect": "True",
                "sourceFormat": "NEWLINE_DELIMITED_JSON",
                "compression": "GZIP",
                "sourceUris": [f"gs://{BUCKET}/raw/*"],
            },
        },
    )

    remove_files_task = BashOperator(
        task_id="remove_files_task",
        bash_command=f"rm {path_to_local_home}/{file_template}"
    )

    download_dataset_task >> local_to_gcs_task >> gcs_2_bq_ext_task  >> remove_files_task