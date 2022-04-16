import os
import logging

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

from airflow.providers.google.cloud.operators.bigquery import BigQueryCreateExternalTableOperator, BigQueryInsertJobOperator

from datetime import datetime

from google.cloud import storage

import pandas as pd
from glom import glom
import json
import gzip

PROJECT_ID = os.environ.get("GCP_PROJECT_ID")
BUCKET = os.environ.get("GCP_GCS_BUCKET")
DATASET = "gh"
BIGQUERY_DATASET = os.environ.get("BIGQUERY_DATASET", 'gh_archive_all')

url_prefix = 'https://data.gharchive.org/'
file_template = '{{ execution_date.strftime(\'%Y-%m-%d-%-H\') }}.json.gz'
parquet_file = file_template.replace('.json.gz', '.parquet')
url = url_prefix + file_template
path_to_local_home = os.environ.get("AIRFLOW_HOME", "/opt/airflow/")

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
}

spec = {
    'id':'id',
    'type':'type',
    'actor_id':'actor.id',
    'actor_login':'actor.login',
    'actor_gravatar_id':'actor.gravatar_id',
    'actor_url':'actor.url',
    'actor_avatar_url':'actor.avatar_url',
    'repo_id':'repo.id',
    'repo_name':'repo.name',
    'repo_url':'repo.url',
    #'payload':'payload',
    'public':'public',
    'created_at':'created_at'
}

spec_org = {
    'id':'id',
    'type':'type',
    'actor_id':'actor.id',
    'actor_login':'actor.login',
    'actor_gravatar_id':'actor.gravatar_id',
    'actor_url':'actor.url',
    'actor_avatar_url':'actor.avatar_url',
    'repo_id':'repo.id',
    'repo_name':'repo.name',
    'repo_url':'repo.url',
    #'payload':'payload',
    'public':'public',
    'created_at':'created_at',
    'org_id':'org.id',
    'org_login':'org.login',
    'org_gravatar_id':'org.gravatar_id',
    'org_avatar_url':'org.avatar_url',
    'org_url':'org.url'
}

schema = [
    {
        "name": "id",
        "type": "STRING",
        "description": "Unique event ID"
    },
    {
        "name": "type",
        "type": "STRING",
        "description": "https://developer.github.com/v3/activity/events/types/"
    },
    {
        "name":"actor_id",
        "type": "INTEGER",
        "description": "Numeric ID of the GitHub actor"
    },
    {
        "name": "actor_login",
        "type": "STRING",
        "description": "Actor's GitHub login"
    },
    {
        "name": "actor_gravatar_id",
        "type": "STRING",
        "description": "Actor's Gravatar ID"
    },
    {
        "name": "actor_url",
        "type": "STRING",
        "description": "Actor's profile URL"
    },
    {
        "name": "actor_avatar_url",
        "type": "STRING",
        "description": "Actor's Gravatar URL"
    },
    {
        "name": "repo_id",
        "type": "INTEGER",
        "description": "Numeric ID of the GitHub repository"
    },
    {
        "name": "repo_name",
        "type": "STRING",
        "description": "Repository name"
    },
    {
        "name": "repo_url",
        "type": "STRING",
        "description": "Repository URL"
    },
    {
        "name": "public",
        "type": "BOOLEAN",
        "description": "Always true for this dataset since only public activity is recorded."
    },
    {
        "name": "created_at",
        "type": "TIMESTAMP",
        "description": "Timestamp of associated event"
    },
    {
        "name": "org_id",
        "type": "INTEGER",
        "description": "Numeric ID of the GitHub org"
    },
    {
        "name": "org_login",
        "type": "STRING",
        "description": "Org's GitHub login"
    },
    {
        "name": "org_gravatar_id",
        "type": "STRING",
        "description": "Org's Gravatar ID"
    },
    {
        "name": "org_avatar_url",
        "type": "STRING",
        "description": "Org's Gravatar URL"
    },
    {
        "name": "org_url",
        "type": "STRING",
        "description": "Org's profile URL"
    }
]

def format_to_parquet(src_file):
    if not src_file.endswith('.json.gz'):
        logging.error("Can only accept source files in json.gz format, for the moment")
        return
    data = []
    with gzip.open(src_file, 'rt', encoding='UTF-8') as f:
        for line in f:
            j_content = json.loads(line)
            if j_content.get('org') is None:
                d_line = glom(j_content, spec)
            else:
                d_line = glom(j_content, spec_org)
            data.append(d_line)
    pd.DataFrame(data).to_parquet(src_file.replace('.json.gz', '.parquet'))

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
    start_date=datetime(2022, 4, 1),
    default_args=default_args,
    catchup=True,
    max_active_runs=3,
    tags=['dtc-de-project'],
) as dag:

    download_dataset_task = BashOperator(
        task_id="download_dataset_task",
        bash_command=f'curl -sSLf {url} > {path_to_local_home}/{file_template}'
    )

    format_to_parquet_task = PythonOperator(
        task_id = "format_to_parquet_task",
        python_callable=format_to_parquet,
        op_kwargs={
            "src_file": f"{path_to_local_home}/{file_template}",
        },
    )

    local_to_gcs_task = PythonOperator(
        task_id="local_to_gcs_task",
        python_callable=upload_to_gcs,
        op_kwargs={
            "bucket": BUCKET,
            "object_name": f"raw/{file_template}",
            "local_file": f"{path_to_local_home}/{parquet_file}",
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
                "fields": schema
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
        bash_command=f"rm {path_to_local_home}/{file_template} {path_to_local_home}/{parquet_file}"
    )

    download_dataset_task >> format_to_parquet_task >> local_to_gcs_task >> gcs_2_bq_ext_task  >> remove_files_task