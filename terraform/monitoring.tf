resource "google_monitoring_alert_policy" "scraper_failure" {
  display_name = "Bergfex Scraper Failure"
  combiner     = "OR"
  conditions {
    display_name = "Cloud Run Job Failure"
    condition_threshold {
      filter     = "resource.type = \"cloud_run_revision\" AND resource.labels.service_name = \"bergfex-scraper-job\" AND metric.type = \"run.googleapis.com/request_count\" AND metric.label.response_code_class != \"2xx\""
      duration   = "60s"
      comparison = "COMPARISON_GT"
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }

  alert_strategy {
    auto_close = "604800s" # 7 days
  }
}
