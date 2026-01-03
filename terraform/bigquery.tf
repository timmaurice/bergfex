resource "google_bigquery_dataset" "dataset" {
  dataset_id                  = var.dataset_id
  friendly_name               = "Bergfex Snow Reports"
  description                 = "Dataset containing scraped snow reports from Bergfex"
  location                    = "EU"
  default_table_expiration_ms = null
}

resource "google_bigquery_table" "snow_reports_view" {
  dataset_id = google_bigquery_dataset.dataset.dataset_id
  table_id   = var.table_id
  deletion_protection = false

  view {
    query = <<EOF
SELECT
  d.country,
  d.resort_name,
  f.status,
  f.timestamp as scraped_at,
  d.area_url,
  f.lifts_open as lifts_open_count,
  f.lifts_total as lifts_total_count,
  CAST(f.new_snow AS STRING) as new_snow,
  CAST(f.snow_mountain AS STRING) as snow_mountain,
  CAST(f.snow_valley AS STRING) as snow_valley,
  CAST(f.avalanche_warning AS STRING) as avalanche_warning,
  f.snow_condition,
  f.last_snowfall,
  f.slopes_open_km,
  f.slopes_total_km,
  CAST(NULL AS INTEGER) as slopes_open_count,
  CAST(NULL AS INTEGER) as slopes_total_count,
  f.slope_condition,
  f.last_update
FROM `${var.project_id}.${var.dataset_id}.fct_snow_measurements` f
JOIN `${var.project_id}.${var.dataset_id}.dim_resorts` d ON f.resort_id = d.resort_id
EOF
    use_legacy_sql = false
  }
}

resource "google_bigquery_table" "dim_resorts" {
  dataset_id = google_bigquery_dataset.dataset.dataset_id
  table_id   = "dim_resorts"
  deletion_protection = false
  
  schema = <<EOF
[
  {
    "name": "resort_id",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "Unique identifier for the resort (MD5 of area_url)"
  },
  {
    "name": "resort_name",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "Name of the ski resort"
  },
  {
    "name": "country",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "Country name"
  },
  {
    "name": "region",
    "type": "STRING",
    "mode": "NULLABLE",
    "description": "Region name (e.g., Tirol)"
  },
  {
    "name": "area_url",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "URL to the resort page"
  },
  {
    "name": "elevation_valley",
    "type": "INTEGER",
    "mode": "NULLABLE",
    "description": "Valley elevation in meters"
  },
  {
    "name": "elevation_mountain",
    "type": "INTEGER",
    "mode": "NULLABLE",
    "description": "Mountain elevation in meters"
  }
]
EOF
}

resource "google_bigquery_table" "fct_snow_measurements" {
  dataset_id = google_bigquery_dataset.dataset.dataset_id
  table_id   = "fct_snow_measurements"
  deletion_protection = false
  
  time_partitioning {
    type  = "DAY"
    field = "date"
  }

  schema = <<EOF
[
  {
    "name": "measurement_id",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "Unique identifier for the measurement"
  },
  {
    "name": "resort_id",
    "type": "STRING",
    "mode": "REQUIRED",
    "description": "Foreign key to dim_resorts"
  },
  {
    "name": "date",
    "type": "DATE",
    "mode": "REQUIRED",
    "description": "Date of the measurement"
  },
  {
    "name": "timestamp",
    "type": "TIMESTAMP",
    "mode": "REQUIRED",
    "description": "Exact time of data extraction"
  },
  {
    "name": "snow_valley",
    "type": "STRING",
    "mode": "NULLABLE",
    "description": "Snow depth in valley (cm)"
  },
  {
    "name": "snow_mountain",
    "type": "STRING",
    "mode": "NULLABLE",
    "description": "Snow depth on mountain (cm)"
  },
  {
    "name": "new_snow",
    "type": "STRING",
    "mode": "NULLABLE",
    "description": "New snow amount (cm)"
  },
  {
    "name": "lifts_open",
    "type": "STRING",
    "mode": "NULLABLE",
    "description": "Number of open lifts"
  },
  {
    "name": "lifts_total",
    "type": "STRING",
    "mode": "NULLABLE",
    "description": "Total number of lifts"
  },
  {
    "name": "slopes_open_km",
    "type": "STRING",
    "mode": "NULLABLE",
    "description": "Kilometers of open slopes"
  },
  {
    "name": "slopes_total_km",
    "type": "STRING",
    "mode": "NULLABLE",
    "description": "Total kilometers of slopes"
  },
  {
    "name": "status",
    "type": "STRING",
    "mode": "NULLABLE",
    "description": "Open or Closed status"
  },
  {
    "name": "avalanche_warning",
    "type": "STRING",
    "mode": "NULLABLE",
    "description": "Avalanche warning level (1-5)"
  },
  {
    "name": "snow_condition",
    "type": "STRING",
    "mode": "NULLABLE",
    "description": "Condition of the snow"
  },
  {
    "name": "slope_condition",
    "type": "STRING",
    "mode": "NULLABLE",
    "description": "Condition of the pistes (e.g., gut, sehr gut)"
  },
  {
    "name": "last_snowfall",
    "type": "STRING",
    "mode": "NULLABLE",
    "description": "Date/info about last snowfall in the region"
  },
  {
    "name": "last_update",
    "type": "TIMESTAMP",
    "mode": "NULLABLE",
    "description": "Timestamp of the last update from the resort"
  }
]
EOF
}
