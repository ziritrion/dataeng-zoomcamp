>Previous: [Introduction to Data Engineering](1_intro.md)

>[Back to index](README.md)

>Next: (Coming soon)

### Table of contents

# Data Ingestion

This lesson will cover the topics of _Data Lake_ and _pipelines orchestration with Airflow_.

_[Back to the top](#table-of-contents)_

# Data Lake

## What is a Data Lake?

A ***Data Lake*** is a _central repository_ that holds _big data_ from many sources.

The _data_ in a Data Lake could either be structured, unstructured or a mix of both.

The main goal behind a Data Lake is being able to ingest data as quickly as possible and making it available to the other team members.

A Data Lake should be:
* Secure
* Scalable
* Able to run on inexpensive hardware

## Data Lake vs Data Warehouse

A Data Lake (DL) is not to be confused with a Data Warehouse (DW). There are several differences:

* Data Processing:
  * DL: The data is **raw** and has undergone minimal processing. The data is generally unstructured.
  * DW: the data is **refined**; it has been cleaned, pre-processed and structured for specific use cases.
* Size:
  * DL: Data Lakes are **large** and contains vast amounts of data, in the order of petabytes. Data is transformed when in use only and can be stored indefinitely.
  * DW: Data Warehouses are **small** in comparison with DLs. Data is always preprocessed before ingestion and may be purged periodically.
* Nature:
  * DL: data is **undefined** and can be used for a wide variety of purposes.
  * DW: data is historic and **relational**, such as transaction systems, etc.
* Users:
  * DL: Data scientists, data analysts.
  * DW: Business analysts.
* Use cases:
  * DL: Stream processing, machine learning, real-time analytics...
  * DW: Batch processing, business intelligence, reporting.

Data Lakes came into existence because as companies started to realize the importance of data, they soon found out that they couldn't ingest data right away into their DWs but they didn't want to waste uncollected data when their devs hadn't yet finished developing the necessary relationships for a DW, so the Data Lake was born to collect any potentially useful data that could later be used in later steps from the very start of any new projects.

## ETL vs ELT

When ingesting data, DLs use the ***Export, Transform and Load*** (ETL) model whereas DWs use ***Export, Load and Transform*** (ELT).

The main difference between them is the order of steps. In DWs, ELT (Schema on Write) means the data is _transformed_ (preprocessed, etc) before arriving to its final destination, whereas in DLs, ETL (Schema on read) the data is directly stored without any transformations and any schemas are derived when reading the data from the DL.

## Data Swamp - Data Lakes gone wrong

Data Lakes are only useful if data can be easily processed from it. Techniques such as versioning and metadata are very helpful in helping manage a Data Lake. A Data Lake risks degenerating into a ***Data Swamp*** if no such measures are taken, which can lead to:
* No versioning of the data
* Incompatible schemes for the same data
* No metadata associated
* Joins between different datasets are not possible

## Data Lake Cloud Providers

* Google Cloud Platform > [Cloud Storage](https://cloud.google.com/storage)
* Amazon Web Services > [Amazon S3](https://aws.amazon.com/s3/)
* Microsoft Azure > [Azure Blob Storage](https://azure.microsoft.com/en-us/services/storage/blobs/)

_[Back to the top](#table-of-contents)_

# Orchestration with Airflow

## Introduction to Workflow Orchestration

In the previous lesson we saw the definition of [data pipeline](1_intro.md#data-pipelines) and we created a [pipeline script](../1_intro/ingest_data.py) that downloaded a CSV and processed it so that we could ingest it to Postgres.

The script we created is an example of how **NOT** to create a pipeline, because it contains 2 steps which could otherwise be separated (downloading and processing). The reason is that if our internet connection is slow or if we're simply testing the script, it will have to download the CSV file every single time that we run the script, which is less than ideal.

Ideally, each of these steps would be contained as separate entities, like for example 2 separate scripts. For our pipeline, that would look like this:

```
(web) → DOWNLOAD → (csv) → INGEST → (Postgres)
```

We have now separated our pipeline into a `DOWNLOAD` script and a `INGEST` script.

In this lesson we will create a more complex pipeline:

```
(web)
  ↓
DOWNLOAD
  ↓
(csv)
  ↓
PARQUETIZE
  ↓
(parquet) ------→ UPLOAD TO S3
  ↓
UPLOAD TO GCS
  ↓
(parquet in GCS)
  ↓
UPLOAD TO BIGQUERY
  ↓
(table in BQ)
```
_Parquet_ is a [columnar storage datafile format](https://parquet.apache.org/) which is more efficient than CSV.

This ***Data Workflow*** has more steps and even branches. This type of workflow is often called a ***Directed Acyclic Graph*** (DAG) because it lacks any loops and the data flow is well defined.

The steps in capital letters are our ***jobs*** and the objects in between are the jobs' outputs, which behave as ***dependencies*** for other jobs. Each job may have its own set of ***parameters*** and there may also be global parameters which are the same for all of the jobs.

A ***Workflow Orchestration Tool*** allows us to define data workflows and parametrize them; it also provides additional tools such as history and logging.

The tool we will focus on in this course is **[Apache Airflow](https://airflow.apache.org/)**, but there are many others such as Luigi, Prefect, Argo, etc.

## Airflow architecture

A typical Airflow installation consists of the following components:

![airflow architecture](https://airflow.apache.org/docs/apache-airflow/stable/_images/arch-diag-basic.png)

* The **scheduler** handles both triggering scheduled workflows as well as submitting _tasks_ to the executor to run. The scheduler is the main "core" of Airflow.
* The **executor** handles running tasks. In a default installation, the executor runs everything inside the scheduler but most production-suitable executors push task execution out to _workers_.
* A **worker** simply executes tasks given by the scheduler.
* A **webserver** which seves as the GUI.
* A **DAG directory**; a folder with _DAG files_ which is read by the scheduler and the executor (an by extension by any worker the executor might have)
* A **metadata database** (Postgres) used by the scheduler, the executor and the web server to store state. The backend of Airflow.
* Additional components (not shown in the diagram):
  * `redis`: a _message broker_ that forwards messages from the scheduler to workers.
  * `flower`: app for monitoring the environment, available at port `5555` by default.
  * `airflow-init`: initialization service which we will customize for our needs.

Airflow will create a folder structure when running:
* `./dags` - `DAG_FOLDER` for DAG files
* `./logs` - contains logs from task execution and scheduler.
* `./plugins` - for custom plugins

Additional definitions:
* ***DAG***: Directed acyclic graph, specifies the dependencies between a set of tasks with explicit execution order, and has a beginning as well as an end. (Hence, “acyclic”). A _DAG's Structure_ is as follows:
  * DAG Definition
  * Tasks (eg. Operators)
  * Task Dependencies (control flow: `>>` or `<<` )  
* ***Task***: a defined unit of work. The Tasks themselves describe what to do, be it fetching data, running analysis, triggering other systems, or more. Common Types of tasks are:
  * ***Operators*** (used in this workshop) are predefined tasks. They're the most common.
  * ***Sensors*** are a subclass of operator which wait for external events to happen.
  * ***TaskFlow decorators*** (subclasses of Airflow's BaseOperator) are custom Python functions packaged as tasks.
* ***DAG Run***: individual execution/run of a DAG. A run may be scheduled or triggered.
* ***Task Instance***: an individual run of a single task. Task instances also have an indicative state, which could be `running`, `success`, `failed`, `skipped`, `up for retry`, etc.
    * Ideally, a task should flow from `none`, to `scheduled`, to `queued`, to `running`, and finally to `success`.

## Setting up Airflow with Docker

### Pre-requisites

1. This tutorial assumes that the [service account credentials JSON file](1_intro.md#gcp-initial-setup) is named `google_credentials.json` and stored in `$HOME/.google/credentials/`. Copy and rename your credentials file to the required path.
2. `docker-compose` should be at least version v2.x+ and Docker Engine should have at least 5GB of RAM available, ideally 8GB. On Docker Desktop this can be changed in _Preferences_ > _Resources_.

### Setup

1. Create a new `airflow` subdirectory in your work directory.
1. Download the official Docker-compose YAML file for the latest Airflow version.
    ```bash
    curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.2.3/docker-compose.yaml'
    ```
    * The official `docker-compose.yaml` file is quite complex and contains [several service definitions](https://airflow.apache.org/docs/apache-airflow/stable/start/docker.html#docker-compose-yaml).
    * If you want a less overwhelming file that only runs the webserver, you may take a look at [this simplified YAML file](../2_data_ingestion/airflow/extras/docker-compose-nofrills.yml).
    * For a refresher on how `docker-compose` works, you can [check out this lesson from the ML Zoomcamp](https://github.com/ziritrion/ml-zoomcamp/blob/main/notes/10_kubernetes.md#connecting-docker-containers-with-docker-compose).
1. We now need to [set up the Airflow user](https://airflow.apache.org/docs/apache-airflow/stable/start/docker.html#setting-the-right-airflow-user). For MacOS, create a new `.env` in the same folder as the `docker-compose.yaml` file with the content below:
    ```bash
    AIRFLOW_UID=50000
    ```
1. The base Airflow Docker image won't work with GCP, so we need to [customize it](https://airflow.apache.org/docs/docker-stack/build.html) to suit our needs. You may download a GCP-ready Airflow Dockerfile [from this link](../2_data_ingestion/airflow/Dockerfile). A few things of note:
    * We use the base Apache Airflow image as the base.
    * We install the GCP SDK CLI tool so that Airflow can communicate with our GCP project.
    * We also need to provide a [`requirements.txt` file](../2_data_ingestion/airflow/requirements.txt) to install Python dependencies. The dependencies are:
      * `apache-airflow-providers-google` so that Airflow can use the GCP SDK.
      * `pyarrow` , a library to work with parquet files.
1. Alter the `x-airflow-common` service definition inside the `docker-compose.yaml` file as follows:
   * We need to point to our custom Docker image. At the beginning, comment or delete the `image` field and uncomment the `build` line, or arternatively, use the following (make sure you respect YAML indentation):
      ```yaml
        build:
          context: .
          dockerfile: ./Dockerfile
      ```
    * Add a volume and point it to the folder where you stored the credentials json file. Assuming you complied with the pre-requisites and moved and renamed your credentials, add the following line after all the other volumes:
      ```yaml
      - ~/.google/credentials/:/.google/credentials:ro
      ```
    * Add 2 new environment variables right after the others: `GOOGLE_APPLICATION_CREDENTIALS` and `AIRFLOW_CONN_GOOGLE_CLOUD_DEFAULT`:
      ```yaml
      GOOGLE_APPLICATION_CREDENTIALS: /.google/credentials/google_credentials.json
      AIRFLOW_CONN_GOOGLE_CLOUD_DEFAULT: 'google-cloud-platform://?extra__google_cloud_platform__key_path=/.google/credentials/google_credentials.json'
      ```
    * Change the `AIRFLOW__CORE__LOAD_EXAMPLES` value to `'false'`. This will prevent Airflow from populating its interface with DAG examples.
1. You may find a modified `docker-compose.yaml` file [in this link](../2_data_ingestion/airflow/docker-compose.yaml).

### Execution
1. Build the image. It may take several minutes You only need to do this the first time you run Airflow or if you modified the Dockerfile or the `requirements.txt` file.
    ```bash
    docker-compose build
    ```
2. Initialize configs:
    ```bash
    docker-compose up airflow-init
    ```
3. Run Airflow
    ```bash
    docker-compose up
    ```
1. You may now access the Airflow GUI by browsing to `localhost:8080`. Username and password are both `airflow` .
>***IMPORTANT***: this is ***NOT*** a production-ready setup! The username and password for Airflow have not been modified in any way; you can find them by searching for `_AIRFLOW_WWW_USER_USERNAME` and `_AIRFLOW_WWW_USER_PASSWORD` inside the `docker-compose.yaml` file.

## Creating a DAG

_For reference, check out [Airflow's docs](https://airflow.apache.org/docs/apache-airflow/stable/concepts/dags.html)._

A DAG is created as a Python script which imports a series of libraries from Airflow.

There are [3 different ways of declaring a DAG](https://airflow.apache.org/docs/apache-airflow/stable/concepts/dags.html#declaring-a-dag). Here's an example definition using a _[context manager](https://book.pythontips.com/en/latest/context_managers.html)_:

```python
with DAG(dag_id="my_dag_name") as dag:
    op1 = DummyOperator(task_id="task1")
    op2 = DummyOperator(task_id="task2")
    op1 >> op2
```
* When declaring a DAG we must provide at least a `dag_id` parameter. There are many additional parameters available.
* The content of the DAG is composed of _tasks_. This example contains 2 _operators_, which are predefined tasks provided by Airflow's libraries and plugins.
  * An operator only has to be declared with any parameters that it may require. There is no need to define anything inside them.
  * All operators must have at least a `task_id` parameter.
* Finally, at the end of the definition we define the _task dependencies_, which is what ties the tasks together and defines the actual structure of the DAG.
  * Task dependencies are primarily defined with the `>>` (downstream) and `<<` (upstream) control flow operators.
  * Additional functions are available for more complex control flow definitions.
* A single Python script may contain multiple DAGs.

Many operators inside a DAG may have common arguments with the same values (such as `start_date`). We can define a `default_args` dict which all tasks within the DAG will inherit:

```python
default_args = {
    'start_date': datetime(2016, 1, 1),
    'owner': 'airflow'
}

with DAG('my_dag', default_args=default_args) as dag:
    op = DummyOperator(task_id='dummy')
    print(op.owner)  # "airflow"
```

_[Back to the top](#table-of-contents)_