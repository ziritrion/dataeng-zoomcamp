# Data Engineering Zoomcamp Project

This folder contains my project for the [Data Engineering Zoomcamp](https://github.com/DataTalksClub/data-engineering-zoomcamp) by [DataTalks.Club](https://datatalks.club).

# Dataset

The chosen dataset for this project is the [GitHub Archive](https://www.gharchive.org/).

# GCP APIs

https://console.cloud.google.com/apis/library/iam.googleapis.com
https://console.cloud.google.com/apis/library/iamcredentials.googleapis.com
NOT https://console.cloud.google.com/apis/library/dataproc.googleapis.com
NOT https://console.cloud.google.com/apis/library/composer.googleapis.com

# Airflow

## Create VM

Follow [this gist](https://gist.github.com/ziritrion/3214aa570e15ae09bf72c4587cb9d686)

```sh
gcloud compute instances create gh-airflow --zone=europe-west1-b --image-family=ubuntu-2004-lts --image-project=ubuntu-os-cloud --machine-type=e2-standard-4 --boot-disk-size=30GB
```

Set up Airflow according to [these instructions](https://github.com/ziritrion/dataeng-zoomcamp/blob/main/notes/2_data_ingestion.md#setting-up-airflow-with-docker)

