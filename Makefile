# UPI Analytics Platform — Developer Workflow
.PHONY: ingest transform model analyze all test clean app lint docker-build docker-run docker-stop help

help: ## Show this help
	@findstr /R "^[a-zA-Z_-]*:.*##" Makefile

ingest: ## Run ingestion pipeline (Bronze layer)
	python -m src.pipeline.run_pipeline --stage ingest

transform: ## Run transformation pipeline (Silver layer)
	python -m src.pipeline.run_pipeline --stage transform

model: ## Run modeling pipeline (Gold layer)
	python -m src.pipeline.run_pipeline --stage model

analyze: ## Run all analytics modules
	python -m src.pipeline.run_pipeline --stage analyze

all: ## Run full end-to-end pipeline
	python -m src.pipeline.run_pipeline --stage all

test: ## Run pytest test suite
	pytest tests/ -v --tb=short

clean: ## Remove generated data and logs
	if exist data\bronze\npci\*.parquet del /Q data\bronze\npci\*.parquet
	if exist data\bronze\phonepe_pulse\*.parquet del /Q data\bronze\phonepe_pulse\*.parquet
	if exist data\bronze\rbi\*.parquet del /Q data\bronze\rbi\*.parquet
	if exist data\silver\*.parquet del /Q data\silver\*.parquet
	if exist data\gold\*.duckdb del /Q data\gold\*.duckdb
	if exist logs\*.log del /Q logs\*.log

app: ## Launch Streamlit dashboard locally
	streamlit run src/visualization/app.py

lint: ## Run ruff linter and formatter
	ruff check src/ tests/
	ruff format src/ tests/

docker-build: ## Build Docker image for Streamlit app
	docker build -t upi-analytics-platform:latest .

docker-run: ## Run Docker container locally on port 8501
	docker run -d --name upi-analytics-app -p 8501:8501 upi-analytics-platform:latest

docker-stop: ## Stop and remove local Docker container
	-docker rm -f upi-analytics-app
