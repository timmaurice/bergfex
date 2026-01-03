.PHONY: help setup terraform scrape run test clean

help:
	@echo "Bergfex ETL Pipeline"
	@echo "===================="
	@echo "make setup      - Create venv and install dependencies"
	@echo "make terraform  - Apply Terraform infrastructure"
	@echo "make scrape     - Run the scraper (includes cloud upload)"
	@echo "make run        - Run both terraform + scrape"
	@echo "make test       - Run tests"
	@echo "make clean      - Remove generated files"

setup:
	uv venv .venv
	uv pip install -r requirements.txt
	@echo "✅ Setup complete. Activate with: source .venv/bin/activate"

terraform:
	cd terraform && terraform init -input=false && terraform apply -auto-approve

scrape:
	source .venv/bin/activate && python main.py

run: terraform scrape
	@echo "✅ Full pipeline complete!"

test:
	source .venv/bin/activate && pytest

clean:
	rm -f bergfex_data.csv
	rm -rf __pycache__ .pytest_cache
