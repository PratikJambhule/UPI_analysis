# UPI Analytics Platform

**Live App:** https://upi-analytics-pratikjambhule.streamlit.app/

> **Note:** This app is hosted on Streamlit's free tier. If you see a screen saying _"This app has gone to sleep"_, it's not broken — just click the button to wake it up. Free hosting sleeps inactive apps to save resources for the open-source community. It'll be back in ~30 seconds!

> If this URL changes based on your Streamlit app name, update this line to your final deployed URL.

An end-to-end data engineering and analytics platform analyzing India's Unified Payments Interface (UPI) -- the world's largest real-time digital payment system by transaction volume.

---

## What This Project Does

This project ingests raw data from three public sources, processes it through a Medallion Architecture pipeline (Bronze, Silver, Gold), and produces an interactive Streamlit dashboard with 60+ visuals across 11 analytical tabs.

The pipeline processes 235+ billion transactions worth 345+ trillion INR, spanning 7 years (2018--2024), covering 36 states and 788 districts.

---

## The Dataset

Three independent, publicly available data sources are used. Each covers a different aspect of UPI.

The enriched combined dataset is also available on Hugging Face:  
[`PratikJambhule/india-upi-ecosystem-2018-2025`](https://huggingface.co/datasets/PratikJambhule/india-upi-ecosystem-2018-2025)

Hugging Face dataset card content used for publishing is available in this repository at:  
[`DatasetReadme.md`](DatasetReadme.md)

| Source                                                                  | What It Contains                                                                                        | Time Period                    | Why We Use It                                                                                                 |
| ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- | ------------------------------ | ------------------------------------------------------------------------------------------------------------- |
| [PhonePe Pulse](https://github.com/PhonePe/pulse)                       | District-level UPI transactions, user registrations, device brands, insurance data across 788 districts | Q1 2018 -- Q2 2025             | Only publicly available district-level UPI data in India. 9,026 JSON files parsed from their GitHub repo.     |
| [NPCI](https://www.npci.org.in/what-we-do/upi/upi-ecosystem-statistics) | Official monthly UPI volumes, per-app market share                                                      | Jan 2022 -- Jun 2025 (monthly) | Ground truth for total UPI volume. NPCI operates UPI.                                                         |
| [RBI DBIE](https://dbie.rbi.org.in)                                     | Currency in Circulation (quarterly), ATM transaction volumes                                            | Q1 2019 -- Q2 2025             | Central bank data needed for cash displacement analysis. Most authoritative source for physical cash metrics. |

### Key Tables Produced

| Table                       | Records | Description                                                                    |
| --------------------------- | ------- | ------------------------------------------------------------------------------ |
| `fact_upi_transactions`     | 140     | Yearly category-level transaction totals (5 categories x 7 years x 4 quarters) |
| `fact_market_concentration` | 13      | Monthly HHI index, top-2 share, equivalent firms, concentration classification |
| `fact_cash_displacement`    | 34      | Monthly UPI value vs currency in circulation with digital-to-cash ratio        |
| `district_clusters`         | 788     | Every district classified into 4 adoption tiers via K-Means clustering         |
| `state_analysis`            | 36      | Per-state metrics including intra-state Gini coefficient                       |
| `forecast_combined`         | 54      | 42 actual + 12 forecast months (Prophet + ARIMA projections)                   |
| `npci_monthly_volumes`      | 42      | Monthly transaction volumes with YoY growth and fiscal year mapping            |
| `app_market_share`          | 91      | Per-app market share with parent company mapping                               |

See [`technical_reference.md`](technical_reference.md) for complete column definitions and formulas.

---

## Key Findings

These are the main insights extracted from the data. Every number below is computed from the source data, not estimated.

### 1. Market Concentration

UPI is a duopoly. PhonePe holds ~48.8% and Google Pay holds ~36.3% of all transactions. Together, they control ~85% of the market.

- **HHI Index: 0.3767** -- classified as "Highly Concentrated" by US Department of Justice standards (threshold: 0.25)
- **Equivalent firms: 2.7** -- the market behaves as if only ~3 equal-sized firms exist
- NPCI proposed a 30% volume cap per app in 2020. As of 2025, enforcement remains deferred. Both PhonePe and Google Pay exceed this cap.
- Paytm's market share dropped sharply after RBI's regulatory action on Paytm Payments Bank, further consolidating the duopoly.

### 2. Geographic Digital Divide

UPI adoption is concentrated in urban districts. Rural districts lag behind.

- **788 districts analyzed**, classified into 4 adoption tiers (K-Means clustering)
- **50 districts identified as critically underserved** (bottom by transaction volume)
- **Average intra-state Gini coefficient: 0.441** -- moderate-to-high inequality. Within most states, a few urban districts account for the majority of UPI transactions.
- Top states: Maharashtra (3.63 Bn txns), Karnataka (3.46 Bn). Bottom states have transaction volumes 1000x lower.

### 3. Cash Displacement

India is becoming less cash-dependent, not cashless. This is an important distinction.

- **Digital-to-cash ratio: 0.68** -- UPI processes ~68% as much value as total physical cash in circulation each month
- Currency in circulation (physical cash) continues to grow year-over-year despite UPI growth
- UPI is capturing **new transactions** -- street vendors, auto-rickshaws, small shops that previously operated in cash only
- ATM transaction volumes show gradual decline, supporting the digital shift thesis

### 4. Growth Trajectory

UPI transaction volumes have grown from 1.08 Bn (2018) to 99.30 Bn (2024).

- **Latest monthly volume: 19.48 Bn transactions** (Jun 2025)
- **Seasonal peak: October** (Diwali/festive season, factor: 1.042). **Trough: February** (factor: 0.930)
- Prophet and ARIMA models both project volumes reaching ~23 Bn/month by mid-2026
- Average transaction value has been declining -- more small-value payments are being made digitally, indicating deeper financial inclusion

---

## Data Pipeline

```
Bronze (Raw)  -->  Silver (Cleaned)  -->  Gold (Analytics-Ready)  -->  Dashboard
```

| Phase         | What Happens                                                                                                                                                                                                                                 |
| ------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Bronze**    | Raw data ingested from 3 sources. PhonePe Pulse: 9,026 JSON files parsed from GitHub. NPCI: curated from official statistics. RBI: curated from DBIE. All stored as Parquet with source metadata.                                            |
| **Silver**    | Standardized column names, type casting, null handling, duplicate removal. State/district name cleaning. Derived fields: fiscal year, YoY growth, avg transaction value. Validated: no nulls in key columns, positive values, no duplicates. |
| **Gold**      | Star schema in DuckDB. 4 dimension tables (date, geography, app, category) + 4 fact tables + 2 analytical views. Exported to Parquet for dashboard consumption.                                                                              |
| **Analytics** | 4 independent modules: Market concentration (HHI), Forecasting (Prophet + ARIMA), Geographic analysis (Gini + K-Means), Cash displacement (ratio analysis). Each produces Parquet outputs.                                                   |

---

## Analytical Methods

| Method                    | Formula                                                     | What It Measures                                           | Why This Method                                                               |
| ------------------------- | ----------------------------------------------------------- | ---------------------------------------------------------- | ----------------------------------------------------------------------------- |
| **HHI**                   | `sum(market_share^2)`                                       | Market concentration (0 = competitive, 1 = monopoly)       | Global standard used by DOJ and EU for antitrust evaluation                   |
| **Gini Coefficient**      | `(2 * sum(i * sorted_val)) / (n * sum(vals)) - (n+1)/n`     | Inequality of UPI adoption across districts within a state | Scale-independent; used by World Bank for income inequality                   |
| **K-Means Clustering**    | 4 clusters on log-scaled features (volume, value, avg size) | District adoption tiers: Very Low, Low, Medium, High       | Finds natural groupings; log-scaling prevents metro districts from dominating |
| **ARIMA(1,1,1)**          | AR(1) + differencing(1) + MA(1)                             | 12-month transaction volume forecast                       | Classical statistical approach; parsimonious for 42 data points               |
| **Prophet**               | Trend + seasonality + holidays                              | 12-month forecast with confidence intervals                | Handles Indian holidays (Diwali, Holi); robust to missing data                |
| **Digital-to-Cash Ratio** | `UPI_value / Currency_in_Circulation`                       | Digital payment penetration relative to physical cash      | Direct scale comparison; growth rates alone can be misleading                 |

See [`technical_reference.md`](technical_reference.md) for detailed formula explanations, worked examples, and rationale for choosing each method over alternatives.

---

## Why This Project Matters

UPI is not just a payment system. It is the financial infrastructure of a country with 1.4 billion people.

- **Scale**: UPI processes more real-time transactions per month than Visa and Mastercard combined in their respective networks
- **Financial inclusion**: The declining average transaction value (from ~1,800 INR to ~1,300 INR) indicates that small-value everyday purchases are moving to digital -- street vendors, auto-rickshaws, tea shops
- **Policy relevance**: The HHI analysis directly informs the NPCI 30% volume cap debate. A duopoly controlling 85% of a national payment system raises systemic risk questions.
- **Geographic inequality**: A Gini of 0.44 for digital payment adoption within states means the benefits of UPI are not evenly distributed. 50 districts remain critically underserved.
- **Cash paradox**: Despite UPI's growth, physical cash in circulation continues to rise. India is not going cashless -- it is adding a digital layer on top of existing cash usage. This finding contradicts the common "cashless India" narrative.

---

## Tech Stack

| Layer         | Tools                                                              |
| ------------- | ------------------------------------------------------------------ |
| Ingestion     | Python, GitPython (PhonePe Pulse repo clone + JSON parsing)        |
| Processing    | pandas, NumPy, DuckDB (columnar analytical database)               |
| Modeling      | Star schema (4 dimension + 4 fact tables), Parquet exports         |
| Analytics     | Prophet, statsmodels (ARIMA), scikit-learn (K-Means), SciPy (Gini) |
| Visualization | Streamlit (11-tab dashboard), Plotly (60+ interactive charts)      |
| CI/CD         | Jenkins (pipeline), pytest (test gate), Docker (container deploy)  |

---

## Repository Structure

```
UPI_DS_Project/
├── config/               # Pipeline settings and data source definitions
├── dashboards/           # Power BI dashboard (.pbix)
├── data/                 # Bronze / Silver / Gold data layers
├── src/
│   ├── ingestion/        # Data collection from 3 sources
│   ├── transformation/   # Silver layer cleaning and validation
│   ├── modeling/         # Gold layer star schema (DuckDB)
│   ├── analytics/        # HHI, forecasting, geographic, cash displacement
│   ├── visualization/    # Streamlit dashboard (11 pages, 60+ charts)
│   ├── pipeline/         # Orchestrator and CLI runner
│   └── utils/            # Config loader, logger
├── tests/                # Unit and smoke tests
├── technical_reference.md  # Full documentation of datasets, formulas, and methods
├── Makefile              # Developer workflow commands
├── requirements.txt      # Python dependencies
└── UPI_Dashboard.pdf     #Power BI Report Snapshots
```

---

## Running This Project From Scratch

### Prerequisites

| Requirement      | Why                                                | Install                                         |
| ---------------- | -------------------------------------------------- | ----------------------------------------------- |
| **Python 3.10+** | Required by pandas 2.0, Prophet, DuckDB            | [python.org](https://www.python.org/downloads/) |
| **Git**          | PhonePe Pulse ingester clones a public GitHub repo | [git-scm.com](https://git-scm.com/downloads)    |
| **pip**          | Package installer                                  | Ships with Python                               |

No API keys, credentials, or environment variables are needed. All three data sources are public.

### Step 1: Clone the Repository

```bash
git clone https://github.com/YOUR_USERNAME/UPI_DS_Project.git
cd UPI_DS_Project
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

This installs pandas, DuckDB, Plotly, Streamlit, Prophet, statsmodels, scikit-learn, and all other dependencies. Prophet takes the longest to install (~2-3 minutes) because it compiles C++ code.

### Step 3: Run the Data Pipeline

```bash
# Run the full pipeline end-to-end (recommended for first run)
make all
```

This runs four stages in sequence:

| Stage         | Command          | What It Does                                                                                                                                                                                                                                                                                            | Time                                    |
| ------------- | ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------- |
| **Ingest**    | `make ingest`    | Downloads raw data from 3 sources into `data/bronze/`. PhonePe Pulse: clones their [public GitHub repo](https://github.com/PhonePe/pulse) and parses 9,026 JSON files. NPCI: scrapes official statistics (falls back to curated data if site is JS-rendered). RBI: loads curated currency and ATM data. | ~5-10 min (first run, due to git clone) |
| **Transform** | `make transform` | Cleans and validates all datasets. Standardizes column names, handles nulls, removes duplicates, derives fiscal year/quarter fields, computes YoY growth rates. Output in `data/silver/`.                                                                                                               | ~1-2 min                                |
| **Model**     | `make model`     | Builds a star schema in DuckDB (4 dimension tables + 4 fact tables + 2 views). Exports all tables to Parquet in `data/gold/exports/`.                                                                                                                                                                   | ~2-3 min                                |
| **Analyze**   | `make analyze`   | Runs 4 analytical modules: HHI market concentration, Prophet + ARIMA forecasting, Gini + K-Means geographic analysis, cash displacement ratio analysis. Results saved as Parquet.                                                                                                                       | ~3-5 min                                |

Total first-run time: ~15-20 minutes. Subsequent runs are faster because the PhonePe repo is already cloned (git pull instead of clone).

### Step 4: Launch the Dashboard

```bash
make app
```

Opens the Streamlit dashboard at [http://localhost:8501](http://localhost:8501). All 11 tabs should render with data.

### Step 5: Run Tests (Optional)

```bash
make test
```

Runs 28 unit and smoke tests covering chart builders, KPI formatters, and page module imports.

### Step 6: Deploy to Streamlit Cloud (Pratik Account)

1. Push this project to your GitHub repository under your account (`PratikJambhule`).
2. Go to [Streamlit Community Cloud](https://share.streamlit.io/).
3. Click **New app** and select:
	- **Repository**: `PratikJambhule/UPI_DS_Project`
	- **Branch**: `main`
	- **Main file path**: `src/visualization/app.py`
4. Click **Deploy**.
5. After deployment, copy your app URL and update the **Live App** link at the top of this README.

---

## DevOps Setup (Jenkins + pytest + Docker)

This repository now includes a production-style CI/CD flow using 4 technologies:

1. **Streamlit** for the web application
2. **pytest** for automated testing
3. **Jenkins** for CI/CD orchestration
4. **Docker** for packaging and deployment

### Jenkins Pipeline Stages

Pipeline file: `Jenkinsfile`

1. **Checkout**: Pulls latest source from repository
2. **Install Dependencies**: Creates virtual environment and installs `requirements.txt`
3. **Run Tests**: Executes `pytest` and publishes JUnit report (`reports/junit.xml`)
4. **Build Docker Image**: Builds `upi-analytics-platform:latest`
5. **Deploy To Docker**: Runs app container on selected host port (default 8501)

### Running Pipeline in Jenkins

1. Create a Jenkins Pipeline job pointing to this repository.
2. Ensure Jenkins agent has Python, Docker, and Git installed.
3. Set Pipeline script from SCM and use `Jenkinsfile` at repository root.
4. Build with parameters:
	- `DEPLOY_TO_DOCKER=true`
	- `APP_PORT=8501`
5. After success, open `http://localhost:8501` on Jenkins host machine.

### Local Docker Commands

```bash
make docker-build
make docker-run
```

To stop container:

```bash
make docker-stop
```

For submission-ready documentation and screenshot checklist, see `DEVOPS_REPORT.md`.

### How Data Flows Through the Pipeline

```
PhonePe Pulse (GitHub) ──┐
NPCI (website)          ──┼── Bronze (Raw Parquet) ── Silver (Cleaned) ── Gold (Star Schema) ── Dashboard
RBI DBIE (curated)      ──┘
```

Each stage reads from the previous layer and writes to the next. You can re-run any individual stage without re-running earlier stages (e.g., `make analyze` only re-runs analytics on existing gold data).

### Where Data Is Stored

```
data/
├── bronze/           # Raw ingested data (gitignored)
│   ├── npci/         # NPCI monthly volumes, market share
│   ├── phonepe_pulse/# Cloned repo + parsed parquets
│   └── rbi/          # Currency circulation, ATM data
├── silver/           # Cleaned and validated (gitignored)
│   ├── geographic/   # District and state transactions
│   ├── market_share/ # App-level market share
│   ├── transactions/ # NPCI, PhonePe, RBI cleaned data
│   └── users/        # User registrations, device brands
├── gold/
│   ├── exports/      # Analytics-ready parquets (COMMITTED to git)
│   └── upi_analytics.duckdb  # Star schema database (gitignored)
└── geojson/          # India state boundaries (gitignored)
```

Only `data/gold/exports/` is committed to git. Everything else is regenerated by running the pipeline.

### Available Make Commands

```bash
make help       # Show all available commands
make ingest     # Run ingestion only (Bronze layer)
make transform  # Run transformation only (Silver layer)
make model      # Run modeling only (Gold layer)
make analyze    # Run analytics only
make all        # Full end-to-end pipeline
make app        # Launch Streamlit dashboard
make test       # Run test suite
make clean      # Delete all generated data and logs
make lint       # Run ruff linter and formatter
```
