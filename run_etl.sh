#!/bin/bash
set -e

# Bergfex ETL Pipeline Runner
# Usage: ./run_etl.sh [--skip-terraform] [--skip-detail-pages] [--force] [--skip-smoke] [--smoke-only]

SKIP_TERRAFORM=false
SKIP_DETAILS=false
FORCE=false
SKIP_SMOKE=false
SMOKE_ONLY=false

# Parse arguments
while [[ "$#" -gt 0 ]]; do
    case $1 in
        --skip-terraform) SKIP_TERRAFORM=true ;;
        --skip-detail-pages) SKIP_DETAILS=true ;;
        --force) FORCE=true ;;
        --skip-smoke) SKIP_SMOKE=true ;;
        --smoke-only) SMOKE_ONLY=true ;;
        *) echo "Unknown parameter: $1"; exit 1 ;;
    esac
    shift
done

if [ "$SMOKE_ONLY" = true ]; then
    SKIP_TERRAFORM=true
fi

echo "🏔️ Bergfex ETL Pipeline"
echo "========================"

# Change to script directory
cd "$(dirname "$0")"

# 0. Setup Venv
source .venv/bin/activate

# 1. Terraform (only if schema changed)
if [ "$SKIP_TERRAFORM" = false ]; then
    echo ""
    echo "📦 1. Applying Terraform..."
    cd terraform
    terraform init -input=false
    terraform apply -auto-approve
    cd ..
    echo "✅ Terraform complete"
else
    echo "⏭️ Skipping Terraform (--skip-terraform)"
fi

# 2. Smoke Test (verification before full run)
if [ "$SKIP_SMOKE" = false ]; then
    echo ""
    echo "🧪 2. Running Smoke Test Verification..."
    python main.py --smoke-test
    if [ $? -ne 0 ]; then
        echo "❌ Smoke test failed! Aborting ETL."
        exit 1
    fi
    echo "✅ Smoke test passed"
else
    echo "⏭️ Skipping Smoke Test (--skip-smoke)"
fi

# Exit early if only smoke test was requested
if [ "$SMOKE_ONLY" = true ]; then
    echo ""
    echo "🏁 Smoke test only run complete."
    exit 0
fi

# 3. Scrape and Ingest
echo ""
echo "🕷️ 3. Running full scraper..."

PYTHON_ARGS=""
if [ "$FORCE" = true ]; then
    PYTHON_ARGS="--force"
fi

python main.py $PYTHON_ARGS

echo ""
echo "✅ ETL Pipeline Complete!"
echo "📊 Data uploaded to BigQuery"
