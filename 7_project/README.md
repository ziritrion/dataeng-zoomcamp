_[Back to the repo index](https://github.com/ziritrion/dataeng-zoomcamp)_

# Data Engineering Zoomcamp Project

This folder contains my project for the [Data Engineering Zoomcamp](https://github.com/DataTalksClub/data-engineering-zoomcamp) by [DataTalks.Club](https://datatalks.club).

## Index
- [Data Engineering Zoomcamp Project](#data-engineering-zoomcamp-project)
  - [Index](#index)
- [Problem](#problem)
- [Dataset](#dataset)
- [Dashboard](#dashboard)
- [Project details and implementation](#project-details-and-implementation)
- [Reproduce the project](#reproduce-the-project)
  - [Prerequisites](#prerequisites)
  - [Create a Google Cloud Project](#create-a-google-cloud-project)
  - [Creating an environment variable for the credentials](#creating-an-environment-variable-for-the-credentials)
  - [Install and setup Google Cloud SDK](#install-and-setup-google-cloud-sdk)
  - [Create a VM instance](#create-a-vm-instance)
    - [Using the GCP dashboard](#using-the-gcp-dashboard)
    - [Using the SDK](#using-the-sdk)
  - [Set up SSH access to the VM](#set-up-ssh-access-to-the-vm)
  - [Starting and stopping your instance with gcloud sdk after you shut it down](#starting-and-stopping-your-instance-with-gcloud-sdk-after-you-shut-it-down)
  - [Installing the required software in the VM](#installing-the-required-software-in-the-vm)
    - [Docker:](#docker)
    - [Docker compose:](#docker-compose)
    - [Terraform:](#terraform)
    - [Google credentials](#google-credentials)
  - [Upload/download files to/from your instance](#uploaddownload-files-tofrom-your-instance)
  - [Clone the repo in the VM](#clone-the-repo-in-the-vm)
  - [Set up project infrastructure with Terraform](#set-up-project-infrastructure-with-terraform)
  - [Set up data ingestion with Airflow](#set-up-data-ingestion-with-airflow)
  - [Perform the data ingestion](#perform-the-data-ingestion)
  - [Setting up dbt Cloud](#setting-up-dbt-cloud)
  - [Deploying models in dbt Cloud with a Production environment](#deploying-models-in-dbt-cloud-with-a-production-environment)
  - [Creating a dashboard](#creating-a-dashboard)

# Problem

This is a simple project which takes data from the GitHub Archive and transforms it in order to visualize the top GitHub contributors as well as the amount of commits per day.

# Dataset

The chosen dataset for this project is the [GitHub Archive](https://www.gharchive.org/). The dataset contains every single public event made by GitHub users, from basic repo activity such as commits, forks and pull requests to comments, actions and all other events.

# Dashboard

You may access the dashboard with the visualizations [in this link](https://datastudio.google.com/reporting/fe0713dd-c5f1-4e26-b8e1-ca2a64cec745).

# Project details and implementation

This project makes use of Google Cloud Platform, particularly Cloud Storage and BigQuery.

Cloud infrastructure is mostly managed with Terraform, except for Airflow and dbt instances (detailed below in the _Reproduce the project_ section).

Data ingestion is carried out by an Airflow DAG. The DAG downloads new data hourly and ingests it to a Cloud Storage bucket which behaves as the Data Lake for the project. The dataset is in JSON format; the DAG transforms it in order to get rid of any payload objects and parquetizes the data before uploading it. The DAG also creates an external table in BigQuery for querying the parquet files.

The Data Warehouse is defined with dbt. It creates a table with all the info in the parquet files. The table is partitioned by day and clustered on actor ID's.

dbt is also used for creating the transformations needed for the visualizations. A view is created in a staging phase containing only the _PushEvents_ (a Push Event contains one or more commits), and a final table containing the commit count per user is materialized in the deployment phase.

The visualization dashboard is a simple Google Data Studio report with 2 widgets.

# Reproduce the project

## Prerequisites

The following requirements are needed to reproduce the project:

1. A [Google Cloud Platform](https://cloud.google.com/) account.
1. (Optional) The [Google Cloud SDK](https://cloud.google.com/sdk). Instructions for installing it are below.
    * Most instructions below will assume that you are using the SDK for simplicity.
1. (Optional) A SSH client.
    * All the instructions listed below assume that you are using a Terminal and SSH.
1. (Optional) VSCode with the Remote-SSH extension.
    * Any other IDE should work, but VSCode makes it very convenient to forward ports in remote VM's.

Development and testing were carried out using a Google Cloud Compute VM instance. I strongly recommend that a VM instance is used for reproducing the project as well. All the instructions below will assume that a VM is used.

## Create a Google Cloud Project

Access the [Google Cloud dashboard](https://console.cloud.google.com/) and create a new project from the dropdown menu on the top left of the screen, to the right of the _Google Cloud Platform_ text.

After you create the project, you will need to create a _Service Account_ with the following roles:
* `BigQuery Admin`
* `Storage Admin`
* `Storage Object Admin`
* `Viewer`

Download the Service Account credentials file, rename it to `google_credentials.json` and store it in your home folder, in `$HOME/.google/credentials/` .
> ***IMPORTANT***: if you're using a VM as recommended, you will have to upload this credentials file to the VM.

You will also need to activate the following APIs:
* https://console.cloud.google.com/apis/library/iam.googleapis.com
* https://console.cloud.google.com/apis/library/iamcredentials.googleapis.com

If all of these steps are unfamiliar to you, please review [Lesson 1.3.1 - Introduction to Terraform Concepts & GCP Pre-Requisites (YouTube)](https://youtu.be/Hajwnmj0xfQ?t=198), or check out my notes [here](https://github.com/ziritrion/dataeng-zoomcamp/blob/main/notes/1_intro.md#gcp-initial-setup).

## Creating an environment variable for the credentials

Create an environment variable called `GOOGLE_APPLICATION_CREDENTIALS` and assign it to the path of your json credentials file, which should be `$HOME/.google/credentials/` . Assuming you're running bash:

1. Open `.bashrc`:
    ```sh
    nano ~/.bashrc
    ```
1. At the end of the file, add the following line:
    ```sh
    export GOOGLE_APPLICATION_CREDENTIALS="<path/to/authkeys>.json"
    ```
1. Exit nano with `Ctrl+X`. Follow the on-screen instructions to save the file and exit.
1. Log out of your current terminal session and log back in, or run `source ~/.bashrc` to activate the environment variable.
1. Refresh the token and verify the authentication with the GCP SDK:
    ```sh
    gcloud auth application-default login
    ```

## Install and setup Google Cloud SDK

1. Download Gcloud SDK [from this link](https://cloud.google.com/sdk/docs/install) and install it according to the instructions for your OS.
1. Initialize the SDK [following these instructions](https://cloud.google.com/sdk/docs/quickstart).
    1. Run `gcloud init` from a terminal and follow the instructions.
    1. Make sure that your project is selected with the command `gcloud config list`

## Create a VM instance

### Using the GCP dashboard

1. From your project's dashboard, go to _Cloud Compute_ > _VM instance_
1. Create a new instance:
    * Any name of your choosing
    * Pick your favourite region. You can check out the regions [in this link](https://cloud.google.com/about/locations).
        > ***IMPORTANT***: make sure that you use the same region for all of your Google Cloud components.
    * Pick a _E2 series_ instance. A _e2-standard-4_ instance is recommended (4 vCPUs, 16GB RAM)
    * Change the boot disk to _Ubuntu_. The _Ubuntu 20.04 LTS_ version is recommended. Also pick at least 30GB of storage.
    * Leave all other settings on their default value and click on _Create_.

### Using the SDK

The following command will create a VM using the recommended settings from above. Make sure that the region matches your choice:

```sh
gcloud compute instances create <name-of-the-vm> --zone=<google-cloud-zone> --image-family=ubuntu-2004-lts --image-project=ubuntu-os-cloud --machine-type=e2-standard-4 --boot-disk-size=30GB
```

## Set up SSH access to the VM

1. Start your instance from the _VM instances_ dashboard in Google Cloud.
1. In your local terminal, make sure that the gcloud SDK is configured for your project. Use `gcloud config list` to list your current config's details.
    1. If you have multiple google accounts but the current config does not match the account you want:
        1. Use `gcloud config configurations list` to see all of the available configs and their associated accounts.
        1. Change to the config you want with `gcloud config configurations activate my-project`
    1. If the config matches your account but points to a different project:
        1. Use `gcloud projects list` to list the projects available to your account (it can take a while to load).
        1. use `gcloud config set project my-project` to change your current config to your project.
3. Set up the SSH connection to your VM instances with `gcloud compute config-ssh`
    * Inside `~/ssh/` a new `config` file should appear with the necessary info to connect.
    * If you did not have a SSH key, a pair of public and private SSH keys will be generated for you.
    * The output of this command will give you the _host name_ of your instance in this format: `instance.zone.project` ; write it down.
4. You should now be able to open a terminal and SSH to your VM instance like this:
   * `ssh instance.zone.project`
5. In VSCode, with the Remote SSH extension, if you run the [command palette](https://code.visualstudio.com/docs/getstarted/userinterface#_command-palette) and look for _Remote-SSH: Connect to Host_ (or alternatively you click on the Remote SSH icon on the bottom left corner and click on _Connect to Host_), your instance should now be listed. Select it to connect to it and work remotely.

## Starting and stopping your instance with gcloud sdk after you shut it down

1. List your available instances.
    ```sh
    gcloud compute instances list
    ```
1. Start your instance.
    ```sh
    gcloud compute instances start <instance_name>
    ```
1. Set up ssh so that you don't have to manually change the IP in your config files.
    ```sh
    gcloud compute config-ssh
    ```
1. Once you're done working with the VM, you may shut it down to avoid consuming credit.
    ```sh
    gcloud compute instances stop <instance_name>
    ```

## Installing the required software in the VM

1. Run this first in your SSH session: `sudo apt update && sudo apt -y upgrade`
    * It's a good idea to run this command often, once per day or every few days, to keep your VM up to date.
### Docker:
1. Run `sudo apt install docker.io` to install it.
1. Change your settings so that you can run Docker without `sudo`:
    1. Run `sudo groupadd docker`
    1. Run `sudo gpasswd -a $USER docker`
    1. Log out of your SSH session and log back in.
    1. Run `sudo service docker restart`
    1. Test that Docker can run successfully with `docker run hello-world`
### Docker compose:
1. Go to https://github.com/docker/compose/releases and copy the URL for the  `docker-compose-linux-x86_64` binary for its latest version.
    * At the time of writing, the last available version is `v2.2.3` and the URL for it is https://github.com/docker/compose/releases/download/v2.2.3/docker-compose-linux-x86_64
1. Create a folder for binary files for your Linux user:
    1. Create a subfolder `bin` in your home account with `mkdir ~/bin`
    1. Go to the folder with `cd ~/bin`
1. Download the binary file with `wget <compose_url> -O docker-compose`
    * If you forget to add the `-O` option, you can rename the file with `mv <long_filename> docker-compose`
    * Make sure that the `docker-compose` file is in the folder with `ls`
1. Make the binary executable with `chmod +x docker-compose`
    * Check the file with `ls` again; it should now be colored green. You should now be able to run it with `./docker-compose version`
1. Go back to the home folder with `cd ~`
1. Run `nano .bashrc` to modify your path environment variable:
    1. Scroll to the end of the file
    1. Add this line at the end:
       ```bash
        export PATH="${HOME}/bin:${PATH}"
        ```
    1. Press `CTRL` + `o` in your keyboard and press Enter afterwards to save the file.
    1. Press `CTRL` + `x` in your keyboard to exit the Nano editor.
1. Reload the path environment variable with `source .bashrc`
1. You should now be able to run Docker compose from anywhere; test it with `docker-compose version`
### Terraform:
1. Run `curl -fsSL https://apt.releases.hashicorp.com/gpg | sudo apt-key add -`
1. Run `sudo apt-add-repository "deb [arch=amd64] https://apt.releases.hashicorp.com $(lsb_release -cs) main"`
1. Run `sudo apt-get update && sudo apt-get install terraform`

### Google credentials

Make sure that you upload the `google_credentials.json` to `$HOME/.google/credentials/` and you create the `GOOGLE_APPLICATION_CREDENTIALS` as specified in the _Creating an environment variable for the credentials_ section.

## Upload/download files to/from your instance

1. Download a file.
    ```sh
    # From your local machine
    scp <instance_name>:path/to/remote/file path/to/local/file
    ```

1. Upload a file.
    ```sh
    # From your local machine
    scp path/to/local/file <instance_name>:path/to/remote/file
    ```

1. You can also drag & drop stuff in VSCode with the remote extension.

1. If you use a client like Cyberduck, you can connect with SFTP to your instance using the `instance.zone.project` name as server, and adding the generated private ssh key.

## Clone the repo in the VM

Log in to your VM instance and run the following from your `$HOME` folder:

```sh
git clone https://github.com/ziritrion/dataeng-zoomcamp.git
```

The contents of the project can be found in the `dataeng-zoomcamp/7_project` folder.

>***IMPORTANT***: I strongly suggest that you fork my project and clone your copy so that you can easily perform changes on the code, because you will need to customize a few variables in order to make it run with your own infrastructure.

## Set up project infrastructure with Terraform

Make sure that the credentials are updated and the environment variable is set up.

1. Go to the `dataeng-zoomcamp/7_project/terraform` folder.

1. Open `variables.tf` and edit line 11 under the `variable "region"` block so that it matches your preferred region.

1. Initialize Terraform:
    ```sh
    terraform init
    ```
1. Plan the infrastructure and make sure that you're creating a bucket in Cloud Storage as well as a dataset in BigQuery
    ```sh
    terraform plan
    ```
1. If the plan details are as expected, apply the changes.
    ```sh
    terraform apply
    ```

You should now have a bucket called `data_lake` and a dataset called `gh-archive-all` in BigQuery.

## Set up data ingestion with Airflow

1. Go to the `dataeng-zoomcamp/7_project/airflow` folder.
1. Run the following command and write down the output:
    ```sh
    echo -e "AIRFLOW_UID=$(id -u)"
    ```
1. Open the `.env` file and change the value of `AIRFLOW_UID` for the value of the previous command.
1. Change the value of `GCP_PROJECT_ID` for the name of your project id in Google Cloud and also change the value of `GCP_GCS_BUCKET` for the name of your bucket.
1. Build the custom Airflow Docker image:
    ```sh
    docker-compose build
    ```
1. Initialize the Airflow configs:
    ```sh
    docker-compose up airflow-init
    ```
1. Run Airflow
    ```sh
    docker-compose up
    ```

You may now access the Airflow GUI by browsing to `localhost:8080`. Username and password are both `airflow` .
>***IMPORTANT***: this is ***NOT*** a production-ready setup! The username and password for Airflow have not been modified in any way; you can find them by searching for `_AIRFLOW_WWW_USER_USERNAME` and `_AIRFLOW_WWW_USER_PASSWORD` inside the `docker-compose.yaml` file.

## Perform the data ingestion

If you performed all the steps of the previous section, you should now have a web browser with the Airflow dashboard.

The DAG is set up to download all data starting from April 1st 2022. You may change this date by modifying line 202 of `dataeng-zoomcamp/7_project/airflow/dags/data_ingestion.py` . It is not recommended to retrieve data earlier than January 1st 2015, because the data was retrieved with a different API and it has not been tested to work with this pipeline. Should you change the DAG date, you will have to delete the DAG in the Airflow UI and wait a couple of minutes so that Airflow can pick up the changes in the DAG.

To trigger the DAG, simply click on the switch icon next to the DAG name. The DAG will retrieve all data from the starting date to the latest available hour and then perform hourly checks on every 30 minute mark.

After the data ingestion, you may shut down Airflow by pressing `Ctrl+C` on the terminal running Airflow and then running `docker-compose down`, or you may keep Airflow running if you want to update the dataset every hour. If you shut down Airflow, you may also shut down the VM instance because it won't be needed for the following steps.

## Setting up dbt Cloud

1. Create a [dbt CLoud account](https://www.getdbt.com/).
1. Create a new project.
    1. Give it a name (`gh-archive` is recommended), and under _Advanced settings_, input `7_project/dbt` as the _Project subdirectory_.
    1. Choose _BigQuery_ as a database connection.
    1. Choose the following settings:
        * You may leave the default connection name.
        * Upload a Service Account JSON file > choose the `google_credentials.json` we created previously.
        * Under _BigQuery Optional Settings_, make sure that you put your Google Cloud location under _Location_.
        * Under _Development credentials_, choose any name for the dataset. This name will be added as a prefix to the schemas. In this project the name `dbt` was used.
        * Test the connection and click on _Continue_ once the connection is tested successfully.
    1. In the _Add repository from_ form, click on Github and choose your fork from your user account. Alternatively, you may provide a URL and clone the repo.
1. Once the project has been created, you should now be able to click on the hamburger menu on the top left and click on _Develop_ to load the dbt Cloud IDE.

You may now run the `dbt run` command in the bottom prompt to run all models; this will generate 3 different datasets in BigQuery:
* `<prefix>_dwh` hosts the data warehouse materialized table with all of the ingested data.
* `<prefix>_staging` hosts the staging views for generating the final end-user tables.
* `<prefix>_core` hosts the end-user tables.

## Deploying models in dbt Cloud with a Production environment

1. Click on the hamburger menu on the top left and click on _Environments_.
1. Click on the _New Environment_ button on the top right.
1. Give the environment a name (`Production` is recommended), make sure that the environment is of type _Deployment_ and in the _Credentials_ section, you may input a name in the _Dataset_ field; this will add a prefix to the schemas, similarly to what we did in when setting up the development environment (`production` is the recommended prefix but any prefix will do, or you may leave it blank).
1. Create a new job with the following settings:
    * Give it any name; `dbt run` is recommended.
    * Choose the environment you created in the previous step.
    * Optionally, you may click on the _Generate docs?_ checkbox.
    * In the _Commands_ section, add the command `dbt run`
    * In the _Triggers_ section, inside the _Schedule_ tab, make sure that the _Run on schedule?_ checkbox is checked. Select _custom cron schedule_ and input the string `40 * * * *`; this will run the models every hour on the 40th minute (the DAG runs on the 30th minute, the 10 minute delay is to make sure that the DAG is run successfully).
1. Save the job.

You may now trigger the job manually or you may wait until the scheduled trigger to run it. The first time you run it, 3 new datasets will be added to BigQuery following the same pattern as in the development environment.

## Creating a dashboard

The dashboard used in this project was generated with [Google Data Studio](https://datastudio.google.com/) (GDS from now on). Dashboards in GDS are called _reports_. Reports grab data from _data sources_. We will need to generate 2 data sources and a report:

1. Generate the data sources.
    1. Click on the _Create_ button and choose _Data source_.
    1. Click on the _BigQuery_ connector.
    1. Choose your Google Cloud project, choose your _production core_ dataset and click on the `users` table. Click on the _Connect_ button at the top.
    1. You may rename the data source by clicking on the name at the top left of the screen. The default name will be the name of the chosen table.
    1. Click on the GDS icon on the top left to go back to the GDS front page and repeat all of the previous steps but choose the _production staging_ dataset and the `stg_commits` table.
1. Generate the report.
    1. Click on the _Create_ button and choose _Report_.
    1. If the _Add data to report_ pop-up appears, choose the `My data sources` tab and choose one of the data sources. Click on the _Add to report_ button on the confirmation pop-up.
    1. Once you're in the report page, click on the _Add data_ button on the top bar and choose the other data source you created.
    1.  You may delete any default widgets created by GDS.
1. Add the _Top Github Contributors_ widget.
    1. Click on the _Add a chart_ button on the top bar and select _Table_.
    1. On the left bar, in _Data source_ choose the dats source with the `users` table.
    1. In _Dimension_, choose `actor_login` as the only dimension.
    1. In _Metric_, choose `commit_count` as the only metric.
    1. In _Sort_, choose `commit_count` and click on _Descending_.
1. Add the _Commits per day_ widget.
    1. Click on the _Add a chart_ button on the top bar and select _Time series chart_.
    1. On the left bar, in _Data source_ choose the dats source with the `stg_commits` table.
    1. In _Dimension_, choose `created_at` as the only dimension.
    1. In _Metric_, choose `Record Count` as the only metric.

You should now have a functioning dashboard.

_[Back to the repo index](https://github.com/ziritrion/dataeng-zoomcamp)_