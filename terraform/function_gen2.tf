resource "google_service_account" "scraper_sa" {
  account_id   = "bergfex-scraper-sa"
  display_name = "Bergfex Scraper Service Account"
}

resource "google_project_iam_member" "scraper_bq_data_editor" {
  project = var.project_id
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.scraper_sa.email}"
}

resource "google_project_iam_member" "scraper_bq_job_user" {
  project = var.project_id
  role    = "roles/bigquery.jobUser"
  member  = "serviceAccount:${google_service_account.scraper_sa.email}"
}

resource "google_project_iam_member" "scraper_storage_admin" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.scraper_sa.email}"
}

# Get project number
data "google_project" "project" {
}

# Grant GCF Service Agent access to source bucket
resource "google_storage_bucket_iam_member" "gcf_sa_source_access" {
  bucket = google_storage_bucket.static_site.name
  role   = "roles/storage.objectViewer"
  member = "serviceAccount:service-${data.google_project.project.number}@gcf-admin-robot.iam.gserviceaccount.com"
}

# Zip Source Code
data "archive_file" "function_source" {
  type        = "zip"
  output_path = "/tmp/function-source.zip"
  source_dir  = "${path.module}/.."
  excludes    = [
    ".git",
    ".github",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "terraform",
    "tests",
    "venv",
    ".env",
    ".DS_Store",
    "bergfex_data.csv",
    "*.pyc"
  ]
}

resource "google_storage_bucket_object" "function_zip" {
  name   = "function-source-${data.archive_file.function_source.output_md5}.zip"
  bucket = google_storage_bucket.static_site.name
  source = data.archive_file.function_source.output_path
}

# Cloud Function Gen 2
resource "google_cloudfunctions2_function" "scraper" {
  name        = "bergfex-scraper-job"
  location    = var.region
  description = "Scrapes Bergfex snow reports"

  build_config {
    runtime     = "python312"
    entry_point = "scrape_job" 
    source {
      storage_source {
        bucket = google_storage_bucket.static_site.name
        object = google_storage_bucket_object.function_zip.name
      }
    }
  }

  service_config {
    max_instance_count = 1
    available_memory   = "512Mi"
    timeout_seconds    = 600
    service_account_email = google_service_account.scraper_sa.email
    environment_variables = {
        GCP_PROJECT_ID = var.project_id
        BQ_DATASET_ID = var.dataset_id
        GCP_BUCKET_NAME = google_storage_bucket.static_site.name
    }
  }
}

# Cloud Scheduler
resource "google_cloud_scheduler_job" "scraper_trigger" {
  name        = "bergfex-scraper-trigger"
  description = "Triggers the Bergfex scraper daily at 6am and 6pm"
  schedule    = "0 6,18 * * *"
  time_zone   = "Europe/Vienna"
  region      = "europe-west3"

  http_target {
    http_method = "POST"
    uri         = google_cloudfunctions2_function.scraper.service_config[0].uri
    
    oidc_token {
      service_account_email = google_service_account.scraper_sa.email
    }
  }

  attempt_deadline = "600s"
}

# Grant Invoker Permission
resource "google_cloud_run_service_iam_member" "invoker" {
  project  = var.project_id
  location = var.region
  service  = google_cloudfunctions2_function.scraper.name
  role     = "roles/run.invoker"
  member   = "serviceAccount:${google_service_account.scraper_sa.email}"
}
