from google.cloud import bigquery
import os
from dotenv import load_dotenv

load_dotenv()
project_id = os.getenv('GCP_PROJECT_ID')
dataset_id = os.getenv('BQ_DATASET_ID')
table_id = os.getenv('BQ_TABLE_ID')

client = bigquery.Client(project=project_id)
table_ref = f"{project_id}.{dataset_id}.{table_id}"

print(f"Checking table: {table_ref}")

try:
    # 1. Row count
    query_count = f"SELECT count(*) as row_count FROM `{table_ref}`"
    results = list(client.query(query_count))
    print(f"Total rows in BigQuery: {results[0].row_count}")

    # 2. Latest scraped_at
    query_latest_time = f"SELECT max(scraped_at) as last_scrape FROM `{table_ref}`"
    results = list(client.query(query_latest_time))
    print(f"Latest scrape timestamp in DB: {results[0].last_scrape}")

    # 3. Check for last_snowfall
    query_snow = f"""
        SELECT resort_name, last_snowfall, slopes_open_km, scraped_at 
        FROM `{table_ref}`
        WHERE last_snowfall IS NOT NULL
        ORDER BY scraped_at DESC
        LIMIT 5
    """
    results = list(client.query(query_snow))
    print("\nLatest records with last_snowfall:")
    if not results:
        print("NO RECORDS FOUND with last_snowfall != NULL")
    else:
        for row in results:
            print(f"Resort: {row.resort_name}, Snowfall: {row.last_snowfall}, Slopes: {row.slopes_open_km}, Scraped: {row.scraped_at}")

except Exception as e:
    print(f"Error: {e}")
