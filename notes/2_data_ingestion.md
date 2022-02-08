>Previous: [Introduction to Data Engineering](1_intro.md)

>[Back to index](README.md)

>Next: [Data Warehouse](3_data_warehouse.md)

### Table of contents

- [Data Ingestion](#data-ingestion)
- [Data Lake](#data-lake)
  - [What is a Data Lake?](#what-is-a-data-lake)
  - [Data Lake vs Data Warehouse](#data-lake-vs-data-warehouse)
  - [ETL vs ELT](#etl-vs-elt)
  - [Data Swamp - Data Lakes gone wrong](#data-swamp---data-lakes-gone-wrong)
  - [Data Lake Cloud Providers](#data-lake-cloud-providers)
- [Orchestration with Airflow](#orchestration-with-airflow)
  - [Introduction to Workflow Orchestration](#introduction-to-workflow-orchestration)
  - [Airflow architecture](#airflow-architecture)
  - [Setting up Airflow with Docker](#setting-up-airflow-with-docker)
    - [Pre-requisites](#pre-requisites)
    - [Setup (full version)](#setup-full-version)
    - [Setup (lite version)](#setup-lite-version)
    - [Execution](#execution)
  - [Creating a DAG](#creating-a-dag)
  - [Running DAGs](#running-dags)
  - [Airflow and DAG tips and tricks](#airflow-and-dag-tips-and-tricks)
- [Airflow in action](#airflow-in-action)
  - [Ingesting data to local Postgres with Airflow](#ingesting-data-to-local-postgres-with-airflow)
  - [Ingesting data to GCP](#ingesting-data-to-gcp)
- [GCP's Transfer Service](#gcps-transfer-service)
  - [Creating a Transfer Service from GCP's web UI](#creating-a-transfer-service-from-gcps-web-ui)
  - [Creating a Transfer Service with Terraform](#creating-a-transfer-service-with-terraform)

# Data Ingestion

This lesson will cover the topics of _Data Lake_ and _pipelines orchestration with Airflow_.

_[Back to the top](#table-of-contents)_

# Data Lake

_[Video source](https://www.youtube.com/watch?v=W3Zm6rjOq70&list=PL3MmuxUbc_hJed7dXYoJw8DoCuVHhGEQb&index=16)_

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

When ingesting data, DWs use the ***Export, Transform and Load*** (ETL) model whereas DLs use ***Export, Load and Transform*** (ELT).

The main difference between them is the order of steps. In DWs, ETL (Schema on Write) means the data is _transformed_ (preprocessed, etc) before arriving to its final destination, whereas in DLs, ELT (Schema on read) the data is directly stored without any transformations and any schemas are derived when reading the data from the DL.

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

_[Video source](https://www.youtube.com/watch?v=0yK7LXwYeD0&list=PL3MmuxUbc_hJed7dXYoJw8DoCuVHhGEQb&index=17)_

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

_[Video source](https://www.youtube.com/watch?v=lqDMzReAtrw&list=PL3MmuxUbc_hJed7dXYoJw8DoCuVHhGEQb&index=18)_

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

_[Video source](https://www.youtube.com/watch?v=lqDMzReAtrw&list=PL3MmuxUbc_hJed7dXYoJw8DoCuVHhGEQb&index=18)_

### Pre-requisites

1. This tutorial assumes that the [service account credentials JSON file](1_intro.md#gcp-initial-setup) is named `google_credentials.json` and stored in `$HOME/.google/credentials/`. Copy and rename your credentials file to the required path.
2. `docker-compose` should be at least version v2.x+ and Docker Engine should have at least 5GB of RAM available, ideally 8GB. On Docker Desktop this can be changed in _Preferences_ > _Resources_.

### Setup (full version)

Please follow these instructions for deploying the "full" Airflow with Docker. Instructions for a "lite" version are provided in the next section but you must follow these steps first.

1. Create a new `airflow` subdirectory in your work directory.
1. Download the official Docker-compose YAML file for the latest Airflow version.
    ```bash
    curl -LfO 'https://airflow.apache.org/docs/apache-airflow/2.2.3/docker-compose.yaml'
    ```
    * The official `docker-compose.yaml` file is quite complex and contains [several service definitions](https://airflow.apache.org/docs/apache-airflow/stable/start/docker.html#docker-compose-yaml).
    * For a refresher on how `docker-compose` works, you can [check out this lesson from the ML Zoomcamp](https://github.com/ziritrion/ml-zoomcamp/blob/main/notes/10_kubernetes.md#connecting-docker-containers-with-docker-compose).
1. We now need to [set up the Airflow user](https://airflow.apache.org/docs/apache-airflow/stable/start/docker.html#setting-the-right-airflow-user). For MacOS, create a new `.env` in the same folder as the `docker-compose.yaml` file with the content below:
    ```bash
    AIRFLOW_UID=50000
    ```
    * In all other operating systems, you may need to generate a `.env` file with the appropiate UID with the following command:
        ```bash
        echo -e "AIRFLOW_UID=$(id -u)" > .env
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
    * Add 2 new additional environment variables for your GCP project ID and the GCP bucket that Terraform should have created [in the previous lesson](1_intro.md#creating-gcp-infrastructure-with-terraform). You can find this info in your GCP project's dashboard.
      ```yaml
      GCP_PROJECT_ID: '<your_gcp_project_id>'
      GCP_GCS_BUCKET: '<your_bucket_id>'
      ```
    * Change the `AIRFLOW__CORE__LOAD_EXAMPLES` value to `'false'`. This will prevent Airflow from populating its interface with DAG examples.
1. You may find a modified `docker-compose.yaml` file [in this link](../2_data_ingestion/airflow/docker-compose.yaml).
1. Additional notes:
    * The YAML file uses [`CeleryExecutor`](https://airflow.apache.org/docs/apache-airflow/stable/executor/celery.html) as its executor type, which means that tasks will be pushed to workers (external Docker containers) rather than running them locally (as regular processes). You can change this setting by modifying the `AIRFLOW__CORE__EXECUTOR` environment variable under the `x-airflow-common` environment definition.

You may now skip to the [Execution section](#execution) to deploy Airflow, or continue reading to modify your `docker-compose.yaml` file further for a less resource-intensive Airflow deployment.

### Setup (lite version)

_[Video source](https://www.youtube.com/watch?v=A1p5LQ0zzaQ&list=PL3MmuxUbc_hJed7dXYoJw8DoCuVHhGEQb&index=23)_

The current `docker-compose.yaml` file we've generated will deploy multiple containers which will require lots of resources. This is the correct approach for running multiple DAGs accross multiple nodes in a Kubernetes deployment but it's very taxing on a regular local computer such as a laptop.

If you want a less overwhelming YAML that only runs the webserver and the scheduler and runs the DAGs in the scheduler rather than running them in external workers, please modify the `docker-compose.yaml` file following these steps:

1. Remove the `redis`, `airflow-worker`, `airflow-triggerer` and `flower` services.
1. Change the `AIRFLOW__CORE__EXECUTOR` environment variable from `CeleryExecutor` to `LocalExecutor` .
1. At the end of the `x-airflow-common` definition, within the `depends-on` block, remove these 2 lines:
    ```yaml
    redis:
      condition: service_healthy
    ```
1. Comment out the `AIRFLOW__CELERY__RESULT_BACKEND` and `AIRFLOW__CELERY__BROKER_URL` environment variables.

You should now have a simplified Airflow "lite" YAML file ready for deployment and may continue to the next section.

For convenience, a simplified YAML version is available [in this link](../2_data_ingestion/airflow/extras/docker-compose-nofrills.yml).

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
    docker-compose up -d
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

For this lesson we will focus mostly on operator tasks. Here are some examples:

```python
download_dataset_task = BashOperator(
    task_id="download_dataset_task",
    bash_command=f"curl -sS {dataset_url} > {path_to_local_home}/{dataset_file}"
)
```
* A `BashOperator` is a simple bash command which is passed on the `bash_command` parameter. In this example, we're doenloading some file.

```python
  format_to_parquet_task = PythonOperator(
      task_id="format_to_parquet_task",
      python_callable=format_to_parquet,
      op_kwargs={
          "src_file": f"{path_to_local_home}/{dataset_file}",
      },
  )
```
* A `PythonOperator` calls a Python method rather than a bash command.
* In this example, the `python_callable` argument receives a function that we've defined before in the DAG file, which receives a file name as a parameter then opens that file and saves it in parquet format.
* the `op_kwargs` parameter is a dict with all necessary parameters for the function we're calling. This example contains a single argument with a file name.

A list of operators is available on [Airflow's Operators docs](https://airflow.apache.org/docs/apache-airflow/stable/concepts/operators.html). A list of GCP-specific operators [is also available](https://airflow.apache.org/docs/apache-airflow-providers-google/stable/operators/cloud/index.html).

As mentioned before, DAGs can be scheduled. We can define a schedule in the DAG definition by including the `start_date` and `schedule_interval` parameters, like this:

```python
from datetime import datetime

with DAG(
    dag_id="my_dag_name",
    schedule_interval="0 6 2 * *",
    start_date=datetime(2021, 1, 1)
  ) as dag:
    op1 = DummyOperator(task_id="task1")
    op2 = DummyOperator(task_id="task2")
    op1 >> op2
```
* The scheduler will run a job ***AFTER*** the start date, at the ***END*** of the interval
* The interval is defined as a [cron job](https://www.wikiwand.com/en/Cron) expression. You can use [crontab guru](https://www.wikiwand.com/en/Cron) to define your own.
  * In this example, `0 6 2 * *` means that the job will run at 6:00 AM on the second day of the month each month.
* The starting date is what it sounds like: defines when the jobs will start.
  * The jobs will start ***AFTER*** the start date. In this example, the starting date is January 1st, which means that the job won't run until January 2nd.

## Running DAGs

DAG management is carried out via Airflow's web UI.

![airflow ui](images/02_01.png)

There are 2 main ways to run DAGs:
* Triggering them manually via the web UI or programatically via API
* Scheduling them

When you trigger or schedule a DAG, a DAG instance is created, called a ***DAG run***. DAG runs can run in **parallel for the same DAG** for separate data intervals.

Each task inside a DAG is also instantiated, and a state is given to each task instance. Ideally, a task should flow from `none`, to `scheduled`, to `queued`, to `running`, and finally to `success`.

In the DAGs dashboard, all available DAGs are shown along with their schedule, last and next runs and the status of the DAG's tasks.

You may manually trigger a DAG by clicking on the Play button on the left of each DAG.

A more detailed view and options for each DAG can be accessed by clicking on the DAG's name.

![dag details](images/02_02.png)

The tree view is offered by default, but you can get a graph view of the DAG by clicking on the _Graph_ button.

![dag details](images/02_03.png)

The status of each task can be seen in both views as you trigger a DAG.

## Airflow and DAG tips and tricks

* The default Airflow Docker image does not have `wget` by default. You can either add a line to your custom image to install it or you can use `curl` instead. Here's how to handle file downloading:
  ```python
  import os
  AIRFLOW_HOME = os.environ.get("AIRFLOW_HOME", "/opt/airflow/")
  URL_PREFIX = 'https://s3.amazonaws.com/nyc-tlc/trip+data' 
  URL_TEMPLATE = URL_PREFIX + '/yellow_tripdata_{{ execution_date.strftime(\'%Y-%m\') }}.csv'
  OUTPUT_FILE_TEMPLATE = AIRFLOW_HOME + '/output_{{ execution_date.strftime(\'%Y-%m\') }}.csv'

  with my_worflow as dag:
    download_task = BashOperator(
      task_id = 'download'
      bash_command=f'curl -sSL {URL_TEMPLATE} > {OUTPUT_FILE_TEMPLATE}'
    )
  ```
  * We want to periodically download data each month and the filename changes according to the name and month. We can use _templating_ to parametrize the filename.
    * Airflow uses the [Jinja template engine](https://jinja.palletsprojects.com/en/3.0.x/).
    * Jinja templates make use of `{%...%}` for statements (control structures such as `if` and `for`, macros, etc) and `{{...}}` for expressions (literals, math and logic operators, variables, Python methods, etc). 
    * Airflow offers a series of predefined variables and macros which can be consulted [in this link](https://airflow.apache.org/docs/apache-airflow/stable/templates-ref.html).
    * We use a template to rename the file with the current year and month that the task is running:
      * `execution_date` is an Airflow variable that returns the _execution date_ (or _logical date_ in newer versions of Airflow) of the task, which denotes the current data interval as specified by the `start_date` of the DAG and the number of executions. In this example, this is useful to download past data, since we can trigger this DAG manually and in each execution the execution date will increase by the amount specified in the `schedule_interval`, thus allowing us to download data for multiple months by simply rerunning the DAG.
        * Do not confuse this variable with the actual current date!
      * `strftime()` is a Python function that returns a string representing a date. You can check how to define the format of the string [in this link](https://docs.python.org/3/library/datetime.html#strftime-strptime-behavior). In this example we're outputting the year and month.   
  * `curl` command:
    * Like all other commands, options can be stacked if there aren't additional parameters. In this case, `-sS` is the same as `-s -S`.
    * `-s` is the same as `--silent`; it won't output any progress meters on the console.
    * `-S` is the same as `--show-error`; when combined with silent mode as `-sS`, it will print error messages if any but will not show any progress output.
    * `-L` will follow a link in case the original URL redirects somewhere else.
    * By default, `curl` outputs to console. We could use the `-o` option to print to a file or redirect the output in the shell with `>` as shown here.
* When creating a custom Airflow Docker image, in the Dockerfile, when installing additional packages with `pip`, it's a good idea to disable caching in order to make smaller images:
  ```dockerfile
  RUN pip install --no-cache-dir -r requirements.txt
  ```
* The `.env` file we created during [Airflow setup](#setup) is useful por passing environment variables which can later be reused in multiple places rather than having them hardcoded:
  1. Define your variables inside `.env`. For example:
      ```bash
      PG_HOST=pgdatabase
      PG_USER=root
      PG_PASSWORD=root
      ```
  1. Add the environment variables in `docker-compose.yaml` inside the `x-airflow-common` environment definition:
      ```yaml
      PG_HOST: "${PG_HOST}"
      PG_USER: "${PG_USER}"
      PG_PASSWORD: "${PG_PASSWORD}"
      ```
  1. In your DAG, grab the variables with `os.getenv()`:
      ```python
      PG_HOST = os.getenv('PG_HOST')
      PG_USER = os.getenv('PG_USER')
      PG_PASSWORD = os.getenv('PG_PASSWORD')
      ```
  1. In Python Operator tasks inside a DAG, you can pass arguments as a dict. Instead of `op_kwargs={'key':'value'}`, you can use `op_kwargs=dict(host=PG_HOST, ...)` to define the arguments dictionay in an easier way.
* A key design principle of tasks and DAGs is ***idempotency***. A task is ***idempotent*** if the end result is identical regardless of whether we run the task once or multiple times.
  * For example, if we create a DAG to handle ingestion to our database, the DAG is idempotent if the final table in the database is the same whether we run the DAG once or many times. If it created multiple duplicate tables or multiple records in a single table, then the DAG is NOT idempotent.
  * In our ingestion code, we managed idempotency by dropping any pre-existing databases and recreataing them from scratch.
* You can define multiple DAGs in a single file. Remember that there are [multiple ways of declaring a DAG](https://airflow.apache.org/docs/apache-airflow/stable/concepts/dags.html#declaring-a-dag); we can use this to recycle code for multiple different DAGs:
  * Define a function with all the arguments you may need such as filenames or buckets as well as a `dag` parameter, and inside the function declare the DAG with a context manager with all of your base tasks:
    ```python
    def my_cool_dag_function(dag, param_1, param_2, ...):
      with dag:
        task_1 = BashOperator(task_id=param_1, ...)
        task_2 = PythonOperator(task_id=param_2, ...)
        # ...
        task_1 >> task_2 >> ...
    ```
  * Create as many DAG objects as you need using standard constructors:
    ```python
    first_dag = DAG(
      dag_id='first_dag',
      schedule_interval=@daily,
      ...
    )

    second_dag = DAG(
      dag_id='second_dag',
      ...
    )

    # ...
    ```
  * Call your function as many times as the amount of DAGs you've defined and pass the DAG objects as params to your function.
    ```python
    my_cool_dag_function(
      first_dag,
      param_1=...,
      param_2=...,
      ...
    )

    my_cool_dag_function(
      second_dag,
      param_1=...,
      param_2=...,
      ...
    )

    #...
    ```
  * You can check an example DAG file with 3 DAGs [in this link](https://github.com/DataTalksClub/data-engineering-zoomcamp/raw/main/week_2_data_ingestion/homework/solution.py).

_[Back to the top](#table-of-contents)_

# Airflow in action

We will now learn how to use Airflow to populate a Postgres database locally and in GCP's BigQuery.

## Ingesting data to local Postgres with Airflow

_[Video source](https://www.youtube.com/watch?v=s2U8MWJH5xA&list=PL3MmuxUbc_hJed7dXYoJw8DoCuVHhGEQb&index=20)_

We want to run our Postgres setup from last section locally as well as Airflow, and we will use the `ingest_data.py` script from a DAG to ingest the NYC taxi trip data to our local Postgres.

1. Prepare an ingestion script. We will use [this `ingest_script.py` file](../2_data_ingestion/airflow/dags/ingest_script.py).
    * This script is heavily based on the script from last session, but the code has been wrapped inside a `ingest_callable()` method that will receive parameters from Airflow in order to connect to the database.
    * We originally ran a dockerized version of the script; we could dockerize it again with a special `DockerOperator` task but we will simply run it with `PythonOperator` in our DAG for simplicity.
1. Prepare a DAG. We will use [this `data_ingestion_local.py` DAG file](../2_data_ingestion/airflow/dags/data_ingestion_local.py). The DAG will have the following tasks:
    1. A download `BashOperator` task that will download the NYC taxi data.
    1. A `PythonOperator` task that will call our ingest script in order to fill our database.
    1. All the necessary info for connecting to the database will be defined as environment variables.
1. Modify the `.env` file to include all the necessary environment files. We will use [this `.env` file](../2_data_ingestion/airflow/.env).
1. Modify the Airflow `docker-compose.yaml` file to include the environment variables. We will use [this `docker-compose.yaml` file](../2_data_ingestion/airflow/docker-compose.yaml).
1. Modify the custom Airflow Dockerfile so that we can run our script (this is only for the purposes of this exercise) by installing the additional Python libraries that the `ingest_script.py` file needs. We will use [this Dockerfile](../2_data_ingestion/airflow/Dockerfile).
    * Add this right after installing the `requirements.txt` file: `RUN pip install --no-cache-dir pandas sqlalchemy psycopg2-binary`
1. Rebuild the Airflow image with `docker-compose build` and initialize the Airflow config with `docker-compose up airflow-init`.
1. Start Airflow by using `docker-compose up` and on a separate terminal, find out which virtual network it's running on with `docker network ls`. It most likely will be something like `airflow_default`.
1. Modify the `docker-compose.yaml` file from lesson 1 by adding the network info and commenting away the pgAdmin service in order to reduce the amount of resources we will consume (we can use `pgcli` to check the database). We will use [this `docker-compose-lesson2.yaml` file](../1_intro/docker-compose-lesson2.yaml).
1. Run the updated `docker-compose-lesson2.yaml` with `docker-compose -f docker-compose-lesson2.yaml up` . We need to explicitly call the file because we're using a non-standard name.
1. Optionally, you can login to a worker container and try to access the database from there.
    1. Run `docker ps` and look for a `airflow_airflow-worker` container. Copy the container ID.
    1. Login to the worker container with `docker exec -it <container_id> bash`
    1. Run `python` to start Python's interactive mode. Run the following lines:
        ```python
        from sqlalchemy import create_engine
        engine = create_engine('postgresql://root:root@pgdatabase:5432/ny_taxi')
        engine.connect()
        ```
    1. You should see the output of the `connect()` method. You may now exit both the Python console and logout from the container.
1. Open the Airflow dashboard and trigger the `LocalIngestionDag` DAG by clicking on the Play icon. Inside the detailed DAG view you will find the status of the tasks as they download the files and ingest them to the database. Note that the DAG will run as many times as stated in the drop down menu, which is 25 by default.
    ![DAG in progress](images/02_04.png)
1. Click on any of the colored squares to see the details of the task.
    ![task details](images/02_05.png)
    ![task details](images/02_06.png)
    ![task details](images/02_07.png)
1. As both the download and ingest tasks finish and the squares for both turn dark green, you may use `pgcli -h localhost -p 5432 -u root -d ny_taxi` on a separate terminal to check the tables on your local Postgres database. You should see a new table per run.
1. Once you're finished, remember to use `docker-compose down` on both the Airflow and Postgres terminals.

## Ingesting data to GCP

_[Video source](https://www.youtube.com/watch?v=9ksX9REfL8w&list=PL3MmuxUbc_hJed7dXYoJw8DoCuVHhGEQb&index=19)_

We will now run a slightly more complex DAG that will download the NYC taxi trip data, convert it to parquet, upload it to a GCP bucket and ingest it to GCP's BigQuery.

1. Prepare a DAG for the aforementioned tasks. We will use [this DAG file](../2_data_ingestion/airflow/dags/data_ingestion_gcs_dag.py). Copy it to the `/dags` subdirectory in your work folder.
    * A `BashOperator` is used to download the dataset and then 2 `PythonOperator` tasks are used to format the file to parquet and then upload the file to a GCP bucket.
        * You may find more info on how to programatically upload to a bucket with Python [in this link](https://cloud.google.com/storage/docs/uploading-objects#storage-upload-object-python).
    * A `BigQueryCreateExternalTableOperator` is used for ingesting the data into BigQuery. You may read more about it [in this link](https://airflow.apache.org/docs/apache-airflow/1.10.12/_api/airflow/contrib/operators/bigquery_operator/index.html).
1. If not started, run Airflow with `docker-compose up airflow-init` and then `docker-compose up`.
1. Select the DAG from Airflow's dashboard and trigger it.
1. Once the DAG finishes, you can go to your GCP project's dashboard and search for BigQuery. You should see your project ID; expand it and you should see a new `trips_data_all` database with an `external_table` table.
    ![bigquery](images/02_08.png)
1. Click on the 3 dots next to `external_table` and click on _Open_ to display the table's schema.
    ![bigquery](images/02_09.png)
1. Click on the 3 dots next to `external_table` and click on _Query_. Run the following SQL query to show the top 10 rows in the database:
    ```sql
    SELECT * FROM `animated-surfer-338618.trips_data_all.external_table` LIMIT 10
    ```
    ![bigquery](images/02_10.png)
1. You can also see the uploaded parquet file by searching the _Cloud Storage_ service, selecting your bucket and then clickin on the `raw/` folder. You may click on the filename to access an info panel.
    ![bigquery](images/02_11.png)
    ![bigquery](images/02_12.png)
    ![bigquery](images/02_13.png)
    ![bigquery](images/02_14.png)
1. You may now shutdown Airflow by running `docker-compose down` on the terminal where you run it.

_[Back to the top](#table-of-contents)_

# GCP's Transfer Service

_[Video source](https://www.youtube.com/watch?v=rFOFTfD1uGk&list=PL3MmuxUbc_hJed7dXYoJw8DoCuVHhGEQb&index=22)_

[Transfer Service](https://cloud.google.com/storage-transfer-service) is a GCP service to transfer data from multiple sources to Google's Cloud Storage. This is useful for Data Lake purposes.

Transfer Service _jobs_ can be created via the GCP UI or with Terraform.

## Creating a Transfer Service from GCP's web UI

We will use the _Transfer Service | cloud_ submenu. Creating a job takes 4 steps:

1. Choose a source.
    * For this example we will grab the [NYC taxi trips data](https://www1.nyc.gov/site/tlc/about/tlc-trip-record-data.page) which is stored on Amazon S3, so we will pick _Amazon S3_ as _source type_.
    * Input a bucket name. The URL for the dataset from lesson 1 is `https://s3.amazonaws.com/nyc-tlc/trip+data/yellow_tripdata_2021-01.csv`; the bucket name is the name right after the domain, `nyc-tlc`.
    * Input your [AWS access key and secret key](https://console.aws.amazon.com/iam/home?#/security_credentials).
        * Alternatively, some S3 URLs put the bucket name as the lowest subdomain; this URL is also valid: `https://nyc-tlc.s3.amazonaws.com/trip+data/yellow_tripdata_2021-01.csv`
        ![transfer source](images/02_15.png)
1. Choose a destination bucket.
    * Create a new bucket by clicking on _Browse_ > _Create new bucket_ icon.
        * Choose a unique name
        * Pick single region location type and choose your nearest location.
        * Choose the Standard default storage class.
        * Select Uniform access control
        * Do not select any protection tools.
        * Click on _Create_.
    * Once the bucket has been created, select it in the bucket browser side panel and click on _Select_.
        ![transfer source](images/02_16.png)
1. Choose the settings for the job
    * Type in a description of your choosing.
    * The default _overwrite if different_ and _never delete_ options should work.
        ![transfer source](images/02_17.png)
1. Choose the scheduling options
    * We will only run this job once, with the _Starting now_ option
        ![transfer source](images/02_18.png)

Once you click on the _Create_ button, the job will start transfering data right away. You may click on it to check the progress.

![transfer source](images/02_19.png)
![transfer source](images/02_20.png)

You may now check your Storage dashboard; you should see a new bucket has been created there which contains all the data from the Amazon S3 bucket.

Be aware that Transfer Service charges you per transferred gigabyte. For single use jobs, the Transfer Service UI is preferred to DAGs which take time to create and debug, but costs can add quickly if you're relying on this service to download data periodically.

## Creating a Transfer Service with Terraform

We can use a [Transfer Service Terraform resource](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/storage_transfer_job) as well to recreate what we just did in the web UI in the form of a Terraform config.

The config will contains the following:

* A _data source_ definition using a [`data` block](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/storage_transfer_job) to define our GCP service account.
* A GCP bucket resource that will receive the contents. 
* A IAM rule resource for the Transfer Service that will be assigned to the bucket.
* Finally, the actual transfer service resource in which we can define additional info regarding the transfer specs and schedule.

A finalized `transfer_service.tf` file is available [in this link](../1_intro/terraform/transfer_service.tf), which is based on the example on the [official documentation](https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/storage_transfer_job).
* You will have to modify the file to change the bucket name to something unique.
* You will have to add new variables to the `variables.tf` file: `access_key_id` and `aws_secret_key` for both access and secret keys for AWS.
    * It is ***strongly recommended*** that you ***DO NOT*** write default values for these variables, as both the access and secret keys are highly sensitive data that should be kept secret at all times. If no default value is set, Terraform will ask for the keys when applying the changes.
* You will have to modify the `schedule_start_date` and `schedule_end_date` blocks near the end of the file. Change them to your current date to run the job once.

Copy the `transfer_service.tf` to your Terraform work folder and run `terraform plan` to see the changes that will be deployed.

If you agree with the changes, run `terraform apply` to start the Transfer Service job. You should now be able to see the job in the web UI.

_[Back to the top](#table-of-contents)_

>Previous: [Introduction to Data Engineering](1_intro.md)

>[Back to index](README.md)

>Next: [Data Warehouse](3_data_warehouse.md)