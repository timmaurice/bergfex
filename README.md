# Bergfex Snow Report ETL Pipeline

[![Deploy](https://github.com/Alexander-Heinz/bergfex-scraper/actions/workflows/deploy.yml/badge.svg)](https://github.com/Alexander-Heinz/bergfex-scraper/actions/workflows/deploy.yml)
![Python](https://img.shields.io/badge/python-3.12-blue?style=flat-square)
![Terraform](https://img.shields.io/badge/terraform-1.6+-purple?style=flat-square)
![License](https://img.shields.io/github/license/Alexander-Heinz/bergfex-scraper?style=flat-square)

An automated ETL pipeline that scrapes snow reports from [Bergfex](https://www.bergfex.com) ski resorts across multiple countries and loads them into Google BigQuery for analytics and dashboards.

## Architecture

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Cloud Scheduler │────▶│  Cloud Function  │────▶│    BigQuery     │
│   (Daily 7am)   │     │   (Python ETL)   │     │  (Data Warehouse)│
└─────────────────┘     └──────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌──────────────────┐
                        │   bergfex.com    │
                        │   (Web Scraping) │
                        └──────────────────┘
```

## Features

- **Multi-Country Support**: Austria, Germany, Switzerland, Italy, and more
- **Automated Daily Runs**: Cloud Scheduler triggers the scraper at 7am CET
- **Dimensional Model**: Normalized into `dim_resorts` and `fct_snow_measurements` tables
- **CI/CD Pipeline**: GitHub Actions with Workload Identity Federation (keyless auth)
- **Infrastructure as Code**: Full GCP infrastructure managed via Terraform

## Data Schema

### `dim_resorts` (Dimension Table)
| Column | Type | Description |
|--------|------|-------------|
| resort_id | STRING | MD5 hash of area_url |
| resort_name | STRING | Name of the ski resort |
| country | STRING | Country name |
| region | STRING | Region (e.g., Tirol) |
| area_url | STRING | URL path on bergfex.com |
| elevation_valley | INTEGER | Valley elevation (m) |
| elevation_mountain | INTEGER | Mountain elevation (m) |

### `fct_snow_measurements` (Fact Table)
| Column | Type | Description |
|--------|------|-------------|
| measurement_id | STRING | Unique ID (resort_id + date) |
| resort_id | STRING | FK to dim_resorts |
| date | DATE | Measurement date |
| timestamp | TIMESTAMP | Exact scrape time |
| snow_valley | STRING | Snow depth in valley (cm) |
| snow_mountain | STRING | Snow depth on mountain (cm) |
| new_snow | STRING | Fresh snow last 24h (cm) |
| slopes_open_km | FLOAT | Open slopes (km) |
| slopes_total_km | FLOAT | Total slopes (km) |
| slope_condition | STRING | Piste condition (e.g., "gut") |
| last_snowfall | STRING | Last snowfall info |
| last_update | TIMESTAMP | Resort's last update time |
| avalanche_warning | STRING | Avalanche warning level |

## Quick Start

### Prerequisites

- Python 3.12+
- Google Cloud SDK (`gcloud`)
- Terraform 1.6+

### Local Development

```bash
# Clone and setup
git clone https://github.com/Alexander-Heinz/bergfex-scraper.git
cd bergfex-scraper
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Run tests
pytest tests/ -v

# Run scraper locally (smoke test)
python main.py --smoke-test

# Run full scrape
python main.py --force
```

### Deploy Infrastructure

```bash
cd terraform
terraform init
terraform apply
```

## CI/CD Pipeline

The project uses GitHub Actions with Workload Identity Federation for secure, keyless authentication to GCP.

### Workflow

1. **On Push/PR**: Runs `pytest` tests
2. **On Push to main**: Deploys via Terraform

### Required GitHub Secrets

| Secret | Description |
|--------|-------------|
| `GCP_PROJECT_ID` | GCP Project ID |
| `GCP_SERVICE_ACCOUNT` | Service Account email |
| `GCP_WORKLOAD_IDENTITY_PROVIDER` | WIF Provider resource name |

## Project Structure

```
bergfex-scraper/
├── main.py                 # ETL entry point
├── etl_utils/
│   ├── parser.py          # HTML parsing logic
│   └── const.py           # Constants (countries, URLs)
├── terraform/
│   ├── main.tf            # Provider & backend config
│   ├── bigquery.tf        # BQ tables & views
│   ├── function.tf        # Cloud Function
│   └── scheduler.tf       # Cloud Scheduler
├── tests/
│   ├── test_parser_etl.py # Parser unit tests
│   └── fixtures/          # HTML test fixtures
└── .github/workflows/
    └── deploy.yml         # CI/CD pipeline
```

## Related Projects

- **[bergfex-dashboard](https://github.com/Alexander-Heinz/bergfex-dashboard)**: React dashboard consuming this data
- **Original Fork**: Based on [timmaurice/bergfex](https://github.com/timmaurice/bergfex) Home Assistant integration

## License

MIT License - see [LICENSE](LICENSE)
