terraform {
  required_version = ">= 1.0"
  backend "local" {} 
  required_providers {
    google = {
      source = "hashicorp/google"
    }
  }
}

provider "google" {
  project = var.project
  region = var.region
  // credentials = file(var.credentials)  # Use this if you do not want to set env-var GOOGLE_APPLICATION_CREDENTIALS
}

# Data Lake Bucket
# Ref: https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/storage_bucket
resource "google_storage_bucket" "data-lake-bucket" {
  name          = "${local.data_lake_bucket}_${var.project}" # Concatenating DL bucket & Project name for unique naming
  location      = var.region

  # Optional, but recommended settings:
  storage_class = var.storage_class
  uniform_bucket_level_access = true

  versioning {
    enabled     = true
  }

  lifecycle_rule {
    action {
      type = "Delete"
    }
    condition {
      age = 30  // days
    }
  }

  force_destroy = true
}

/* # DWH
# Ref: https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/bigquery_dataset
resource "google_bigquery_dataset" "dataset" {
  dataset_id = var.BQ_DATASET
  project    = var.project
  location   = var.region
}

# Airflow
# Ref: https://cloud.google.com/composer/docs/composer-2/create-environments#terraform_5
resource "google_composer_environment" "airflow" {
  name = var.composer_name
  region = var.region

  config {
    software_config {
      image_version = var.composer_image
    }

    node_config {
      service_account = var.service_account
    }

    # Environment scale is optional, the default small setup should suffice

    # Networking on public IP environment is the default

    # web server network access should also be public

    # maintenance window should be the default

    # Data encryption should also be the default

    # Environment labels aren't needed
  }
} */