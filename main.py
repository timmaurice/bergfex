"""
Main entry point for Bergfex ETL job.
Fetches data from Bergfex and exports to CSV.
"""
import csv
import logging
import os
import sys
from datetime import datetime
import hashlib
import time
import tempfile
import concurrent.futures
from urllib.parse import urljoin

import requests
from dotenv import load_dotenv
from google.cloud import bigquery
from google.cloud import bigquery
from google.cloud import storage
import functions_framework

load_dotenv()

from etl_utils.const import BASE_URL, COUNTRIES
from etl_utils.geo import extract_coords
from etl_utils.parser import parse_overview_data, parse_resort_page

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
_LOGGER = logging.getLogger(__name__)

import time


def fetch_resort_detail(area_url: str) -> dict:
    """Fetch and parse detail page for a single resort to get avalanche data."""
    if "schneebericht" in area_url:
        path = area_url
    else:
        path = urljoin(area_url, "schneebericht/")
    
    url = urljoin(BASE_URL, path)
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        data = parse_resort_page(response.text, area_url)

        # Coordinate Extraction
        # 1. Try from current URL/HTML (schneebericht)
        coords = extract_coords(url, response.text)
        
        # 2. Fallback: Try Base URL if no coords found
        if not coords and "schneebericht" in url:
            base_resort_url = url.replace("schneebericht/", "")
            _LOGGER.debug(f"Coords missing, trying base URL: {base_resort_url}")
            try:
                base_resp = requests.get(base_resort_url, timeout=30)
                if base_resp.ok:
                    coords = extract_coords(base_resort_url, base_resp.text)
            except Exception as e:
                _LOGGER.debug(f"Error fetching base URL {base_resort_url}: {e}")

        if coords:
            data["lat"] = coords[0]
            data["lon"] = coords[1]
            
        return data
    except requests.RequestException as e:
        _LOGGER.debug(f"Error fetching detail for {area_url}: {e}")
        return {}
    except Exception as e:
        _LOGGER.debug(f"Error parsing detail for {area_url}: {e}")
        return {}


def fetch_country_overview(country_name: str, path: str, fetch_details: bool = True, limit: int | None = None) -> list[dict]:
    """Fetch and parse overview data for a country."""
    url = urljoin(BASE_URL, path)
    _LOGGER.info(f"Fetching data for {country_name} from {url}")

    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        data = parse_overview_data(response.text)
        
        # Transform dict to list and add metadata
        entries = []
        for area_url, area_data in data.items():
            if limit and len(entries) >= limit:
                break
            
            entry = {
                "country": country_name,
                "resort_name": None,
                "status": None,
                "scraped_at": datetime.now().isoformat(),
                "area_url": area_url,
                "lat": None,
                "lon": None,
                "lifts_open_count": None,
                "lifts_total_count": None,
                "new_snow": None,
                "snow_mountain": None,
                "snow_valley": None,
                "avalanche_warning": None,
                "snow_condition": None,
                "last_snowfall": None,
                "slopes_open_km": None,
                "slopes_total_km": None,
                "slopes_open_count": None,
                "slopes_total_count": None,
                "slope_condition": None,
                "last_update": None,
            }
            entry.update(area_data)
            entries.append(entry)

        if not fetch_details:
            return entries

        _LOGGER.info(f"Fetching details for {len(entries)} resorts in {country_name}...")
        
        def fetch_detail_and_merge(entry):
            detail_data = fetch_resort_detail(entry["area_url"])
            for field in [
                "avalanche_warning", "snow_condition", "last_snowfall",
                "slopes_open_km", "slopes_total_km", "slopes_open_count",
                "slopes_total_count", "slope_condition", "last_update",
                "elevation_valley", "elevation_mountain", "region_path",
                "lat", "lon"
            ]:
                if field in detail_data:
                    entry[field] = detail_data[field]
            return entry

        # Parallelize fetching
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            # We use a list to consume the iterator
            results = list(executor.map(fetch_detail_and_merge, entries))
            
        return results

    except requests.RequestException as e:
        _LOGGER.error(f"Error fetching data for {country_name}: {e}")
        return []
    except Exception as e:
        _LOGGER.error(f"Error parsing data for {country_name}: {e}")
        return []


def save_to_csv(data: list[dict], filename: str = "bergfex_data.csv"):
    """Save the collected data to a CSV file."""
    if not data:
        _LOGGER.warning("No data to save.")
        return

    # Determine fieldnames dynamically from the first record
    fieldnames = list(data[0].keys())

    try:
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
        _LOGGER.info(f"Successfully saved {len(data)} records to {filename}")
    except IOError as e:
        _LOGGER.error(f"Error saving to CSV: {e}")


def upload_to_gcs(
    bucket_name: str,
    source_file_name: str,
    destination_blob_name: str,
    project_id: str | None = None,
):
    """Uploads a file to the bucket."""
    try:
        storage_client = storage.Client(project=project_id)
        bucket = storage_client.bucket(bucket_name)
        blob = bucket.blob(destination_blob_name)

        blob.upload_from_filename(source_file_name)

        _LOGGER.info(
            f"File {source_file_name} uploaded to {destination_blob_name} in {bucket_name}."
        )
    except Exception as e:
        _LOGGER.error(f"Error uploading to GCS: {e}")


def load_csv_to_bq(
    dataset_id: str,
    table_id: str,
    uri: str,
    project_id: str | None = None,
    write_disposition: str = bigquery.WriteDisposition.WRITE_APPEND,
):
    """Loads a CSV file from GCS to BigQuery."""
    try:
        bigquery_client = bigquery.Client(project=project_id)

        dataset_ref = bigquery.DatasetReference(project_id, dataset_id)
        table_ref = dataset_ref.table(table_id)

        job_config = bigquery.LoadJobConfig(
            source_format=bigquery.SourceFormat.CSV,
            skip_leading_rows=1,
            write_disposition=write_disposition,
            allow_quoted_newlines=True,
        )

        load_job = bigquery_client.load_table_from_uri(
            uri, table_ref, job_config=job_config
        )

        _LOGGER.info(f"Starting job {load_job.job_id}")

        load_job.result()  # Waits for table load to complete.

        _LOGGER.info("Job finished.")

        destination_table = bigquery_client.get_table(table_ref)
        _LOGGER.info(f"Loaded {destination_table.num_rows} rows.")
    except Exception as e:
        _LOGGER.error(f"Error loading to BigQuery: {e}")


def run_scraper(smoke_test: bool = False, force: bool = False):
    """
    Core ETL logic.
    :param smoke_test: If True, runs a quick verification.
    :param force: If True, ignores local file presence and scrapes fresh.
    """
    load_dotenv()
    _LOGGER.info("Starting Bergfex ETL job")
    
    today = datetime.now().date()
    # Use /tmp for all files in Cloud Functions
    base_path = tempfile.gettempdir()
    csv_filename = os.path.join(base_path, "bergfex_data.csv")
    
    if smoke_test:
        _LOGGER.info("🚀 Running smoke test...")
        # Just test Österreich with 2 resorts
        test_data = fetch_country_overview("Österreich", COUNTRIES["Österreich"], fetch_details=True, limit=2)
        
        if not test_data:
            _LOGGER.error("❌ Smoke test failed: No data fetched")
            # In a function, we shouldn't exit the process, but raise error
            raise RuntimeError("Smoke test failed: No data fetched")
            
        _LOGGER.info(f"✅ Smoke test fetched {len(test_data)} resorts")
        # Verify a few key fields exist in the output dictionary keys
        sample = test_data[0]
        required_keys = ["slopes_open_km", "snow_mountain", "avalanche_warning", "snow_condition", "lat", "lon"]
        missing = [k for k in required_keys if k not in sample]
        
        if missing:
            _LOGGER.error(f"❌ Smoke test failed: Missing keys {missing}")
            raise RuntimeError(f"Smoke test failed: Missing keys {missing}")
            
        _LOGGER.info("✅ Smoke test passed!")
        return

    # Check if we already have today's data and not forcing
    if os.path.exists(csv_filename) and not force:
        # Check if the file was modified today
        file_time = datetime.fromtimestamp(os.path.getmtime(csv_filename)).date()
        if file_time == today:
            _LOGGER.info(f"📅 Data for {today} already exists in {csv_filename}. Skipping scrape. Use --force to overwrite.")
            return # Exit early if data is fresh and not forced
        else:
            # File is old, proceed with scrape
            force = True 

    if force or not os.path.exists(csv_filename):
        # Always scrape if not a smoke test
        all_data = []
        for country, path in COUNTRIES.items():
            country_data = fetch_country_overview(country, path, fetch_details=True)
            all_data.extend(country_data)
            _LOGGER.info(f"Found {len(country_data)} areas for {country}")

        # Process for DIM/FCT tables
        dim_rows = []
        fct_rows = []
        seen_resorts = set()
        
        for entry in all_data:
            # Generate ID
            url = entry.get('area_url', '')
            if not url:
                continue
            resort_id = hashlib.md5(url.encode('utf-8')).hexdigest()
            
            # Region cleaning
            region = None
            if entry.get('region_path'):
                region = entry['region_path'].strip('/').split('/')[0].capitalize()
            
            # DIM Resort
            if resort_id not in seen_resorts:
                dim_rows.append({
                    "resort_id": resort_id,
                    "resort_name": entry.get('resort_name'),
                    "country": entry.get('country'),
                    "region": region,
                    "area_url": url,
                    "elevation_valley": entry.get('elevation_valley'),
                    "elevation_mountain": entry.get('elevation_mountain'),
                    "lat": entry.get('lat'),
                    "lon": entry.get('lon')
                })
                seen_resorts.add(resort_id)
            
            # FCT Measurement
            # Extract date from scraped_at ISO string
            scraped_at = entry.get('scraped_at')
            date_str = scraped_at.split('T')[0] if scraped_at else str(today)
            
            measurement_id = f"{resort_id}_{date_str}"
            
            fct_rows.append({
                "measurement_id": measurement_id,
                "resort_id": resort_id,
                "date": date_str,
                "timestamp": scraped_at,
                "snow_valley": entry.get('snow_valley'),
                "snow_mountain": entry.get('snow_mountain'),
                "new_snow": entry.get('new_snow'),
                "lifts_open": entry.get('lifts_open_count'),
                "lifts_total": entry.get('lifts_total_count'),
                "slopes_open_km": entry.get('slopes_open_km'),
                "slopes_total_km": entry.get('slopes_total_km'),
                "status": entry.get('status'),
                "avalanche_warning": entry.get('avalanche_warning'),
                "snow_condition": entry.get('snow_condition'),
                "slope_condition": entry.get('slope_condition'),
                "last_snowfall": entry.get('last_snowfall'),
                "last_update": entry.get('last_update').isoformat() if entry.get('last_update') else None,
            })

        # Save new CSVs
        dim_csv = os.path.join(base_path, "dim_resorts.csv")
        fct_csv = os.path.join(base_path, "fct_snow_measurements.csv")
        save_to_csv(dim_rows, dim_csv)
        save_to_csv(fct_rows, fct_csv)
        
        # Cloud Integration
        bucket_name = os.environ.get("GCP_BUCKET_NAME")
        dataset_id = os.environ.get("BQ_DATASET_ID")
        project_id = os.environ.get("GCP_PROJECT_ID")
        
        if bucket_name:
            # New Tables Upload & Load
            files_config = [
                (dim_csv, "dim_resorts", "WRITE_TRUNCATE"),
                (fct_csv, "fct_snow_measurements", "WRITE_APPEND")
            ]
            
            for fpath, tid, disposition in files_config:
                if os.path.exists(fpath):
                    fname = os.path.basename(fpath)
                    blob_name = f"{fname.replace('.csv', '')}_{today}.csv" # Timestamped backup
                    
                    upload_to_gcs(bucket_name, fpath, blob_name, project_id)
                    
                    if dataset_id:
                        gcs_uri = f"gs://{bucket_name}/{blob_name}"
                        load_csv_to_bq(
                            dataset_id, 
                            tid, 
                            gcs_uri, 
                            project_id,
                            write_disposition=disposition
                        )
        else:
            _LOGGER.info("GCP_BUCKET_NAME not set. Skipping cloud upload.")

        # Refresh Shred Score Mart via Stored Procedure
        if dataset_id and project_id:
            try:
                _LOGGER.info("Refreshing Shred Score Mart...")
                bq_client = bigquery.Client(project=project_id)
                # Ensure fully qualified name if not already provided in env vars, 
                # but assuming dataset_id is just the name 'bergfex_data'
                procedure_ref = f"{project_id}.{dataset_id}.sp_refresh_resort_shred_score_latest"
                query = f"CALL `{procedure_ref}`();"
                
                job = bq_client.query(query)
                job.result() # Wait for completion
                _LOGGER.info(f"Shred Score Mart refreshed successfully via {procedure_ref}.")
            except Exception as e:
                _LOGGER.error(f"Error refreshing Shred Score Mart: {e}")

        _LOGGER.info("ETL job finished")


@functions_framework.http
def scrape_job(request):
    """
    Cloud Function entry point.
    """
    try:
        # Run full scraper
        run_scraper(force=True)
        return "OK", 200
    except Exception as e:
        _LOGGER.exception("Job failed")
        return f"Error: {e}", 500


def main():
    """Main execution function."""
    import argparse
    parser = argparse.ArgumentParser(description="Bergfex ETL scraper")
    parser.add_argument("--smoke-test", action="store_true", help="Run a quick verification on a few resorts")
    parser.add_argument("--force", action="store_true", help="Force scrape even if today's file exists")
    args = parser.parse_args()

    try:
        run_scraper(smoke_test=args.smoke_test, force=args.force)
    except RuntimeError as e:
        _LOGGER.error(e)
        sys.exit(1)

if __name__ == "__main__":
    main()
