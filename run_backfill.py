from google.cloud import bigquery
import os
from dotenv import load_dotenv

def run_backfill():
    load_dotenv()
    project_id = os.getenv('GCP_PROJECT_ID')
    
    client = bigquery.Client(project=project_id)
    
    with open('backfill.sql', 'r') as f:
        sql = f.read()
        
    # Split by semicolon to run multiple statements if needed, 
    # but BigQuery client might support script execution.
    # Let's try running as a script (all at once) first.
    
    print("Running backfill SQL...")
    query_job = client.query(sql)
    
    try:
        results = query_job.result()
        print("Backfill completed successfully.")
    except Exception as e:
        print(f"Backfill failed: {e}")

if __name__ == "__main__":
    run_backfill()
