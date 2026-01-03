variable "project_id" {
  description = "The ID of the GCP project"
  type        = string
  default     = "bergfex-481612"
}

variable "region" {
  description = "The region to deploy resources to"
  type        = string
  default     = "europe-west10"
}

variable "bucket_name" {
  description = "The name of the GCS bucket"
  type        = string
  default     = "bergfex"
}

variable "bucket_location" {
  description = "The location of the GCS bucket (e.g. EU, US, europe-west1)"
  type        = string
  default     = "EU"
}

variable "dataset_id" {
  description = "The ID of the BigQuery dataset"
  type        = string
  default     = "bergfex_data"
}

variable "table_id" {
  description = "The ID of the BigQuery table"
  type        = string
  default     = "snow_reports"
}
