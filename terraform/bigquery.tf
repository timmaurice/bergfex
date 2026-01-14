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
  },
  {
    "name": "lat",
    "type": "FLOAT64",
    "mode": "NULLABLE",
    "description": "Latitude coordinate of the resort"
  },
  {
    "name": "lon",
    "type": "FLOAT64",
    "mode": "NULLABLE",
    "description": "Longitude coordinate of the resort"
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

resource "google_bigquery_table" "vw_resort_metrics_history" {
  dataset_id = google_bigquery_dataset.dataset.dataset_id
  table_id   = "vw_resort_metrics_history"
  deletion_protection = false

  view {
    query = <<EOF
WITH measurements AS (
  SELECT
    resort_id,
    date AS measurement_date,
    timestamp AS scraped_at,
    
    -- Schneewerte als numerische Werte (NULL-safe)
    SAFE_CAST(snow_mountain AS FLOAT64) AS snow_mountain_cm,
    SAFE_CAST(snow_valley AS FLOAT64) AS snow_valley_cm,
    SAFE_CAST(new_snow AS FLOAT64) AS new_snow_cm,
    
    -- Lifte als numerische Werte
    SAFE_CAST(lifts_open AS INT64) AS lifts_open_count,
    SAFE_CAST(lifts_total AS INT64) AS lifts_total_count,
    
    -- Pisten als numerische Werte
    SAFE_CAST(slopes_open_km AS FLOAT64) AS slopes_open_km,
    SAFE_CAST(slopes_total_km AS FLOAT64) AS slopes_total_km,
    
    -- Textfelder für Score-Berechnung
    snow_condition,
    slope_condition,
    avalanche_warning,
    
    last_update
  FROM `${var.project_id}.${var.dataset_id}.fct_snow_measurements`
),
components AS (
  SELECT
    *,
    -- Lawinenwarnstufe extrahieren
    CASE
      WHEN avalanche_warning IS NULL OR avalanche_warning LIKE '%keine%' THEN NULL
      WHEN avalanche_warning LIKE '%I %' OR avalanche_warning LIKE '%1 %' THEN 1
      WHEN avalanche_warning LIKE '%II %' OR avalanche_warning LIKE '%2 %' THEN 2
      WHEN avalanche_warning LIKE '%III %' OR avalanche_warning LIKE '%3 %' THEN 3
      WHEN avalanche_warning LIKE '%IV %' OR avalanche_warning LIKE '%4 %' THEN 4
      WHEN avalanche_warning LIKE '%V %' OR avalanche_warning LIKE '%5 %' THEN 5
      ELSE NULL
    END AS avalanche_warning_level,
    
    -- Core Score-Komponenten (jetzt mit _cm Suffix!)
    LEAST(1.2, SQRT(IFNULL(new_snow_cm, 0) / 30)) AS freshness,
    SAFE_DIVIDE(
      LOG(1 + IFNULL(snow_mountain_cm, 0) / 40),
      LOG(1 + 120 / 40)
    ) AS base_snow,
    LEAST(1.0, SQRT(IFNULL(slopes_open_km, 0) / 150)) AS terrain,
    
    -- Schneebedingungen-Faktor
    CASE
      WHEN snow_condition IS NULL THEN 0.78
      WHEN LOWER(snow_condition) LIKE '%nass%' OR LOWER(snow_condition) LIKE '%sulz%' THEN 0.65
      WHEN LOWER(snow_condition) LIKE '%aper%' THEN 0.50
      WHEN LOWER(snow_condition) LIKE '%pulver%' THEN 1.00
      WHEN LOWER(snow_condition) LIKE '%sehr gut%' THEN 0.95
      WHEN LOWER(snow_condition) LIKE '%gut%' THEN 0.90
      WHEN LOWER(snow_condition) LIKE '%griffig%' THEN 0.85
      WHEN LOWER(snow_condition) LIKE '%hart%' OR LOWER(snow_condition) LIKE '%eis%' THEN 0.70
      WHEN LOWER(snow_condition) LIKE '%altschnee%' THEN 0.75
      WHEN LOWER(snow_condition) LIKE '%keine meldung%' THEN 0.78
      ELSE 0.78
    END AS snow_factor,
    
    -- Pistenbedingungen-Faktor
    CASE
      WHEN slope_condition IS NULL THEN 0.78
      WHEN LOWER(slope_condition) LIKE '%saisonschluss%' OR LOWER(slope_condition) LIKE '%geschlossen%' THEN 0.10
      WHEN LOWER(slope_condition) LIKE '%sehr gut%' THEN 1.00
      WHEN LOWER(slope_condition) LIKE '%gut%' THEN 0.90
      WHEN LOWER(slope_condition) LIKE '%fahrbar%' THEN 0.75
      WHEN LOWER(slope_condition) LIKE '%keine meldung%' THEN 0.78
      ELSE 0.78
    END AS slope_factor
  FROM measurements
),
scored AS (
  SELECT
    *,
    -- Lawinenfaktor
    CASE
      WHEN avalanche_warning_level IS NULL OR avalanche_warning_level <= 2 THEN 1.00
      WHEN avalanche_warning_level = 3 THEN 0.90
      WHEN avalanche_warning_level = 4 THEN 0.80
      WHEN avalanche_warning_level = 5 THEN 0.75
      ELSE 1.00
    END AS avalanche_penalty,
    
    -- Kombinierter Bedingungsfaktor
    (0.55 * slope_factor + 0.45 * snow_factor) AS conditions_factor
  FROM components
),
final AS (
  SELECT
    *,
    -- Raw Score
    (
      (0.35 * freshness + 0.30 * base_snow + 0.25 * terrain) 
      * conditions_factor 
      * avalanche_penalty
    ) AS raw_score
  FROM scored
)
SELECT
  resort_id,
  measurement_date,
  scraped_at,
  
  -- Numerische Messwerte
  snow_mountain_cm,
  snow_valley_cm,
  new_snow_cm,
  lifts_open_count,
  lifts_total_count,
  slopes_open_km,
  slopes_total_km,
  
  -- Shred Score (auf Skala 1-10)
  LEAST(10, GREATEST(1, 1 + 9 * raw_score)) AS shred_coefficient,
  
  -- Score-Komponenten für Detailanalyse
  raw_score,
  freshness,
  base_snow,
  terrain,
  conditions_factor,
  avalanche_penalty,
  
  -- Zusätzliche Infos (optional, für Debugging)
  snow_factor,
  slope_factor,
  avalanche_warning_level,
  last_update
FROM final
EOF
    use_legacy_sql = false
  }
}
