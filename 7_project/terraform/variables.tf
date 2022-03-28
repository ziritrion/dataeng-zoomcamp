locals {
  data_lake_bucket = "data_lake"
}

variable "project" {
  description = "Your GCP Project ID"
}

variable "region" {
  description = "Region for GCP resources. Choose as per your location: https://cloud.google.com/about/locations"
  default = "europe-west1"
  type = string
}

variable "storage_class" {
  description = "Storage class type for your bucket. Check official docs for more info."
  default = "STANDARD"
}

variable "BQ_DATASET" {
  description = "BigQuery Dataset that raw data (from GCS) will be written to"
  type = string
  default = "gh_archive_all"
}

/* variable "composer_name" {
  description = "Name for the Cloud Composer / Airflow service in GCP"
  type = string
  default = "gh-airflow"
}

variable "composer_image" {
  description = "Image to be used for Composer/Airflow"
  type = string
  default = "composer-2.0.7-airflow-2.2.3"
}

variable "service_account" {
  description = "Service account to use for setting up GCP"
  type = string
  default = "gh-archive-user@gh-archive-345218.iam.gserviceaccount.com"
} */
# Transfer service
# variable "access_key_id" {
#   description = "AWS access key"
#   type = string
# }

# variable "aws_secret_key" {
#   description = "AWS secret key"
#   type = string
# }