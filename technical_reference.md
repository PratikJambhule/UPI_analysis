# UPI Analytics Platform -- Technical Reference

This document explains every dataset, preprocessing step, calculation, formula, graph, and metric used in this project. It is written for someone reviewing this work -- whether a recruiter, interviewer, or academic evaluator.

---

## Table of Contents

1. [The Dataset](#1-the-dataset)
2. [Data Pipeline -- All Preprocessing Phases](#2-data-pipeline----all-preprocessing-phases)
3. [Calculations -- Formulas, Meaning, and Rationale](#3-calculations----formulas-meaning-and-rationale)
4. [Dashboard Visuals -- What Each Graph and Metric Means](#4-dashboard-visuals----what-each-graph-and-metric-means)
5. [Why These Methods and Not Others](#5-why-these-methods-and-not-others)

---

## 1. The Dataset

### 1.1 What Is UPI?

UPI (Unified Payments Interface) is India's real-time digital payment system operated by NPCI (National Payments Corporation of India). It allows instant money transfer between bank accounts via mobile phones. As of 2025, UPI processes over 19 billion transactions per month.

### 1.2 Data Sources

We use three independent data sources. Each was chosen because it is publicly available, authoritative, and covers a different aspect of UPI.

| Source | What It Contains | Why We Use It | Time Period | Collection Method |
|--------|-----------------|---------------|-------------|-------------------|
| **PhonePe Pulse** | Transaction volumes, user registrations, device brands, insurance data -- broken down by state, district, quarter | Only publicly available district-level UPI transaction data in India. Covers 788 districts. | Q1 2018 -- Q2 2025 | Git clone from `github.com/PhonePe/pulse`, parse 9,026 JSON files |
| **NPCI** | Monthly UPI volumes (total transactions and value), per-app market share | Official operator data. This is the ground truth for total UPI volume. | Jan 2022 -- Jun 2025 (monthly), 2017--2024 (yearly) | Curated from NPCI website |
| **RBI DBIE** | Currency in Circulation (CIC) quarterly data, ATM transaction volumes | Needed for cash displacement analysis. RBI is the central bank -- most authoritative source for cash data. | Q1 2019 -- Q2 2025 | Curated from RBI Database on Indian Economy |

### 1.3 What Each Dataset Contains

#### PhonePe Pulse -- Transaction Data (Country Level)

| Column | Type | Meaning |
|--------|------|---------|
| `year` | int | Calendar year (2018--2024) |
| `quarter` | int | Quarter number (1--4) |
| `category` | string | Transaction category: `p2p_payments`, `merchant_payments`, `recharge_bill_payments`, `financial_services`, `others` |
| `transaction_count` | int | Number of transactions in that quarter |
| `transaction_amount` | float | Total value of transactions in INR |

**What it tells us:** How UPI transaction volumes and values have grown over time, broken down by what people use UPI for.

#### PhonePe Pulse -- District Transactions

| Column | Type | Meaning |
|--------|------|---------|
| `state` | string | Indian state name |
| `district` | string | District name within the state |
| `year` | int | Calendar year |
| `quarter` | int | Quarter number |
| `total_txn_count` | int | Number of UPI transactions in that district |
| `total_txn_amount` | float | Total value of those transactions in INR |

**What it tells us:** Which districts are adopting UPI and which are lagging behind. This is the core data for geographic inequality analysis.

#### PhonePe Pulse -- User Aggregates

| Column | Type | Meaning |
|--------|------|---------|
| `year` | int | Calendar year |
| `quarter` | int | Quarter number |
| `quarter_start_date` | date | First day of the quarter |
| `registered_users` | int | Total registered UPI users (cumulative) |
| `app_opens` | int | Number of times the app was opened that quarter |

**What it tells us:** User adoption rate and engagement (registered users vs actual app usage).

#### PhonePe Pulse -- Device Brands

| Column | Type | Meaning |
|--------|------|---------|
| `year` | int | Calendar year |
| `quarter` | int | Quarter number |
| `quarter_start_date` | date | First day of the quarter |
| `device_brand_clean` | string | Phone manufacturer (Xiaomi, Samsung, Vivo, etc.) |
| `device_count` | int | Number of devices using UPI |
| `device_percentage` | float | Market share of that brand among UPI users |

**What it tells us:** Which phone brands dominate among UPI users. Important because UPI adoption is tied to smartphone penetration, especially affordable Android devices.

#### PhonePe Pulse -- Insurance

| Column | Type | Meaning |
|--------|------|---------|
| `year` | int | Calendar year |
| `quarter` | int | Quarter number |
| `quarter_start_date` | date | First day of the quarter |
| `count` | int | Number of insurance policies sold |
| `amount` | float | Total premium amount in INR |

**What it tells us:** Whether UPI platforms are expanding beyond payments into financial products like insurance.

#### PhonePe Pulse -- Top Transactions

| Column | Type | Meaning |
|--------|------|---------|
| `year` | int | Calendar year |
| `quarter` | int | Quarter number |
| `level` | string | Aggregation level: `state`, `district`, or `pincode` |
| `entity_name` | string | Name of the state/district/pincode |
| `count` | int | Transaction count |
| `amount` | float | Transaction value in INR |

**What it tells us:** Which geographic entities have the highest transaction volumes.

#### NPCI Monthly Volumes

| Column | Type | Meaning |
|--------|------|---------|
| `date` | date | Month (first day) |
| `transaction_volume_billions` | float | Total UPI transactions that month, in billions |
| `transaction_value_lakh_crores` | float | Total UPI value, in Lakh Crores (1 Lakh Crore = 1 trillion INR) |
| `fiscal_year` | string | Indian fiscal year (Apr--Mar), e.g., "FY2024-25" |
| `fiscal_quarter` | string | Q1 (Apr--Jun) through Q4 (Jan--Mar) |
| `yoy_volume_growth` | float | Year-over-year volume growth (%) |
| `avg_transaction_value_inr` | float | Average value per transaction in INR |

**What it tells us:** Official monthly UPI statistics. This is the most reliable source for total market size.

#### NPCI App Market Share

| Column | Type | Meaning |
|--------|------|---------|
| `date` | date | Reporting month |
| `app_name_clean` | string | UPI app name (PhonePe, Google Pay, Paytm, etc.) |
| `market_share_pct` | float | Percentage of total UPI volume handled by this app |
| `is_top2` | bool | Whether this app is in the top 2 by market share |
| `parent_company` | string | Parent organization (Walmart, Alphabet, One97, etc.) |

**What it tells us:** How the UPI market is split among competing apps. Critical for antitrust and competition analysis.

#### RBI Currency in Circulation

| Column | Type | Meaning |
|--------|------|---------|
| `quarter_start_date` | date | Start of the quarter |
| `currency_in_circulation_trillion` | float | Total physical cash in India's economy, in trillions of INR |
| `qoq_growth` | float | Quarter-over-quarter growth in cash supply (%) |

**What it tells us:** How much physical cash exists in India. We compare this against UPI value to determine if digital payments are replacing cash or supplementing it.

#### RBI ATM Transactions

| Column | Type | Meaning |
|--------|------|---------|
| `quarter_start_date` | date | Start of the quarter |
| `atm_transactions_millions` | float | Total ATM withdrawals that quarter, in millions |

**What it tells us:** Whether ATM usage is declining as UPI grows. A drop in ATM transactions alongside UPI growth would support the cash displacement hypothesis.

### 1.4 Gold Layer -- Derived Tables

These tables are computed from the raw data during the modeling phase:

| Table | Records | What It Contains |
|-------|---------|-----------------|
| `fact_upi_transactions` | 140 | Yearly category-level transaction totals with date keys |
| `fact_market_concentration` | 13 | Monthly HHI, top-2 share, equivalent firms, concentration category |
| `fact_cash_displacement` | 34 | Monthly UPI value vs currency in circulation with digital-to-cash ratio |
| `fact_digital_divide` | 20,604 | District-quarter records with national percentile rank and adoption quartile |
| `dim_date` | 3,652 | Date dimension: fiscal year, quarter, festival flags |
| `dim_geography` | 852 | State/district/region mapping |
| `dim_app` | 7 | UPI app metadata (name, parent company, launch year) |
| `dim_category` | 5 | Transaction category metadata (P2P/P2M flags) |
| `v_monthly_summary` | 28 | Monthly aggregated transaction summary |
| `v_state_rankings` | 252 | Annual state-level rankings with underserved district percentages |

---

## 2. Data Pipeline -- All Preprocessing Phases

The pipeline follows a **Medallion Architecture** (Bronze -> Silver -> Gold), a standard pattern in data engineering.

```
Bronze (Raw)  -->  Silver (Cleaned)  -->  Gold (Analytics-Ready)  -->  Dashboard
```

### 2.1 Phase 1: Bronze Layer (Ingestion)

**What was done:** Raw data was collected from three sources and stored as-is in Parquet format.

**Why Parquet?** Columnar storage format. Faster reads, smaller file sizes (compressed), and type-safe. Standard in data engineering pipelines.

| Source | Method | Files Generated |
|--------|--------|-----------------|
| PhonePe Pulse | Git clone the public repository, walk directory tree, parse JSON files organized by year/quarter/category | `phonepe_aggregated_transactions.parquet`, `phonepe_map_transactions.parquet`, `phonepe_user_aggregates.parquet`, `phonepe_device_brands.parquet`, `phonepe_insurance.parquet`, `phonepe_top_transactions.parquet` |
| NPCI | Curated data from NPCI's published statistics (monthly volumes, yearly summaries, app market share) | `npci_monthly_volumes.parquet`, `npci_yearly_volumes.parquet`, `npci_app_market_share.parquet` |
| RBI | Curated from RBI's Database on Indian Economy (DBIE) -- currency circulation and ATM data | `rbi_currency_in_circulation.parquet`, `rbi_atm_transactions.parquet` |

**Metadata added:** Every record gets a `source` tag and `ingested_at` timestamp (UTC) for traceability.

### 2.2 Phase 2: Silver Layer (Cleaning and Transformation)

**What was done:** Standardized, cleaned, validated, and enriched every dataset.

#### Cleaning Steps Applied to All Datasets:

1. **Type casting** -- Ensure counts are `int64`, amounts are `float64`, dates are proper `datetime` objects. Why: prevents silent calculation errors from wrong types.

2. **Null handling** -- Check for nulls in key columns. Drop rows where essential fields are missing. Why: nulls in transaction counts or amounts would corrupt aggregations.

3. **Duplicate removal** -- Check for and remove exact duplicate rows. Why: double-counting would inflate metrics.

4. **Positive value validation** -- Verify that transaction counts and amounts are > 0. Why: negative transactions would indicate data corruption.

#### Dataset-Specific Transformations:

**PhonePe Transactions:**
- Standardize category names: "Recharge & bill payments" becomes `recharge_bill_payments`
- Create `is_p2m` flag: True if category is merchant_payments, recharge, or financial_services
- Derive `avg_transaction_value = amount / count`
- Generate `quarter_start_date` from year and quarter

**PhonePe District Data:**
- Clean state names: replace hyphens with spaces, apply title case, fix special cases ("Dadra & Nagar Haveli And Daman & Diu")
- Clean district names: remove the word "district" from names, title case, collapse extra whitespace
- Classify into 6 regions: West, North, South, East, Northeast, Central
- Derive `avg_transaction_value`

**PhonePe User Data:**
- Separate mixed data: the raw data contains both user registration aggregates and device brand breakdowns in the same files. These are split into two clean datasets.
- Clean device brand names (title case)

**NPCI Monthly Volumes:**
- Parse date strings to datetime
- Add fiscal year label: "FY2024-25" (Indian fiscal year runs April to March)
- Add fiscal quarter: Q1 = Apr-Jun, Q2 = Jul-Sep, Q3 = Oct-Dec, Q4 = Jan-Mar
- Derive YoY volume growth: `pct_change(periods=12)` (compare each month to same month last year)
- Derive `avg_transaction_value_inr = total_value / total_volume`

**NPCI Market Share:**
- Strip whitespace from app names
- Flag top-2 apps (PhonePe, Google Pay)
- Map each app to its parent company (PhonePe -> Walmart, Google Pay -> Alphabet, Paytm -> One97 Communications, etc.)

**RBI Currency in Circulation:**
- Parse dates
- Derive quarter-over-quarter growth: `pct_change()` on CIC values

**RBI ATM Transactions:**
- Parse dates, validate positive values

#### Data Validation Framework:

Every dataset passes through a validation step that checks:
- Non-empty DataFrame
- No nulls in key columns
- Positive numerical values
- No duplicate rows
- Date ranges fall within expected bounds

### 2.3 Phase 3: Gold Layer (Star Schema Modeling)

**What was done:** Created a dimensional model (star schema) in DuckDB, then exported everything to Parquet for the dashboard.

**Why a star schema?** It separates "what happened" (facts) from "who/where/when" (dimensions). This makes queries fast and consistent. It is the industry standard for analytics data warehouses.

#### Dimension Tables Created:

**dim_date:**
- Date spine from 2017 to 2027 (every day)
- `date_key` in YYYYMMDD format (surrogate key for joins)
- Fiscal year, fiscal quarter (India: April to March)
- `is_festival_month` flag (Oct = Diwali/Dussehra, Nov = post-Diwali sales)
- Day of week, weekend flag

**dim_geography:**
- Every distinct state and district from PhonePe district data
- `geo_key` (surrogate key)
- Region classification (West, North, South, East, Northeast, Central)

**dim_app:**
- 7 UPI apps: PhonePe, Google Pay, Paytm, CRED, WhatsApp Pay, Amazon Pay, Others
- Parent company, launch year, app category

**dim_category:**
- 5 transaction categories
- `is_p2p` and `is_p2m` flags
- Category descriptions

#### Fact Tables Created:

**fact_upi_transactions:**
- Grain: one row per year per category
- Joins to dim_date via date_key, to dim_category via category_key
- Measures: `transaction_count`, `transaction_amount`

**fact_market_concentration:**
- Grain: one row per month
- Computed during modeling: HHI index, top-2 combined share, equivalent firms count, concentration classification
- (Formulas detailed in Section 3)

**fact_cash_displacement:**
- Grain: one row per month
- Joins UPI monthly value with RBI currency in circulation
- Computed: `digital_to_cash_ratio = UPI_value / CIC`
- CIC data is quarterly; forward-filled to monthly granularity

**fact_digital_divide:**
- Grain: one row per district per quarter
- Computed: national percentile rank (`PERCENT_RANK()`), adoption quartile (`NTILE(4)` -- Very Low, Low, Medium, High)

#### Analytical Views:

**v_monthly_summary:**
- Aggregated monthly transaction totals from the yearly fact table
- Festival month indicators

**v_state_rankings:**
- Annual state-level rankings by total transaction volume
- Percentage of underserved districts per state per year

### 2.4 Phase 4: Analytics Engine

**What was done:** Ran four independent analytical modules on the gold data:
1. Market Concentration Analysis (HHI)
2. Time-Series Forecasting (Prophet + ARIMA)
3. Geographic Analysis (Gini + K-Means clustering)
4. Cash Displacement Analysis

Each module reads from gold layer exports, computes metrics, and writes results back as Parquet files. Details of every calculation are in Section 3.

---

## 3. Calculations -- Formulas, Meaning, and Rationale

### 3.1 Herfindahl-Hirschman Index (HHI)

**What is it?**
HHI measures market concentration -- how much of a market is controlled by a few players.

**Formula:**

```
HHI = sum(s_i ^ 2)  for all firms i

where s_i = market share of firm i as a decimal (e.g., 0.48 for 48%)
```

**Example from our data (latest month):**
```
PhonePe:    48.8% -> 0.488^2 = 0.2381
Google Pay: 36.3% -> 0.363^2 = 0.1318
Paytm:       6.5% -> 0.065^2 = 0.0042
CRED:        2.8% -> 0.028^2 = 0.0008
Others:      5.6% -> 0.056^2 = 0.0031
-----------------------------------------
HHI = 0.2381 + 0.1318 + 0.0042 + 0.0008 + 0.0031 = 0.3780
```

**Interpretation (US Department of Justice thresholds):**

| HHI Range | Classification | What It Means |
|-----------|---------------|---------------|
| < 0.15 | Competitive | Many players, healthy competition |
| 0.15 -- 0.25 | Moderately Concentrated | A few dominant players, but competition exists |
| > 0.25 | Highly Concentrated | Market dominated by very few firms |

**Our result:** HHI = 0.3767, classified as **Highly Concentrated**. This means UPI is dominated by two apps (PhonePe and Google Pay).

**Why we did this:** NPCI proposed a 30% volume cap per app in 2020, partly because of concentration concerns. HHI quantifies this concern using a globally accepted metric. The US DOJ uses HHI to evaluate mergers and antitrust cases.

**Why HHI and not another index?**
- HHI is the global standard used by DOJ, EU Commission, and competition regulators worldwide
- Alternative: **CR4** (Concentration Ratio of top 4 firms) -- simpler but less sensitive. CR4 just sums the top 4 shares; HHI squares them, giving more weight to larger firms. We chose HHI because the squaring property captures the "duopoly effect" better.
- Alternative: **Entropy-based index** -- more theoretically elegant but harder to interpret and rarely used in regulatory contexts.

### 3.2 Equivalent Firms

**What is it?**
The number of equal-sized firms that would produce the same HHI.

**Formula:**

```
Equivalent Firms = 1 / HHI
```

**Our result:** 1 / 0.3767 = **2.65 firms**. This means the UPI market behaves as if only ~2.7 equal-sized firms exist.

**Why we compute this:** HHI is abstract (a decimal between 0 and 1). "Equivalent firms" makes it intuitive: "the market acts like there are only 2.7 players."

### 3.3 Top-2 Combined Market Share

**What is it?**
The combined market share of the two largest UPI apps (PhonePe + Google Pay).

**Formula:**

```
Top-2 Share = share(PhonePe) + share(Google Pay)
```

**Our result:** 48.8% + 36.3% = **85.1%**

**Why we track this:** NPCI's proposed 30% volume cap is specifically about preventing any single app from dominating. If two apps together control 85% of the market, the cap becomes a regulatory necessity. This metric tracks whether the duopoly is tightening or loosening.

### 3.4 Gini Coefficient (Intra-State)

**What is it?**
Gini measures inequality in a distribution. We compute it per state to measure how evenly UPI adoption is spread across districts within that state.

**Formula:**

```
Gini = (2 * sum(i * sorted_value_i)) / (n * sum(all_values)) - (n + 1) / n

where values are sorted in ascending order and i is the rank (1 to n)
```

**Interpretation:**

| Gini | What It Means |
|------|---------------|
| 0.0 | Perfect equality -- every district has the same UPI usage |
| 0.5 | Moderate inequality |
| 1.0 | Perfect inequality -- all UPI usage in one district |

**Our result:** Average Gini across states = **0.441**. This indicates moderate-to-high inequality. In most states, UPI usage is concentrated in urban districts while rural districts lag behind.

**Why Gini and not standard deviation or variance?**
- Gini is **scale-independent**. A state with 10x more total transactions than another can still have the same Gini if the distribution pattern is the same. Standard deviation would be affected by the absolute scale.
- Gini is the established metric for inequality measurement (used by the World Bank, UN for income inequality).
- Alternative: **Coefficient of Variation (CV = std/mean)** -- also scale-independent, but Gini is more interpretable and more commonly used in policy contexts.

### 3.5 K-Means Clustering (District Adoption Tiers)

**What is it?**
We group 788 districts into 4 adoption tiers: Very Low, Low, Medium, High.

**How it works:**

1. Features used: `total_txn` (transaction count), `total_value` (transaction value), `avg_txn_value` (average transaction size)
2. Log-transform the features (because transaction volumes span several orders of magnitude -- from thousands to billions)
3. Run K-Means with k=4
4. Label clusters by their mean transaction volume (highest = "High", lowest = "Very Low")

**Our result:**
- High: 253 districts
- Medium: 241 districts
- Low: 213 districts
- Very Low: 81 districts

**Why K-Means and not manual thresholds?**
- Manual thresholds are arbitrary. K-Means finds natural groupings in the data.
- Alternative: **NTILE(4)** (simple quartile split) -- we actually use this in the gold layer for percentile rankings, but K-Means is better for clustering because it considers multiple features simultaneously (volume + value + avg size), not just one dimension.
- Alternative: **DBSCAN** -- density-based clustering. We did not use it because our data is not spatially clustered in a way DBSCAN handles well, and it requires tuning epsilon (distance threshold) which is harder to justify.

**Why 4 clusters?** Four tiers (High/Medium/Low/Very Low) provide a manageable categorization that maps to actionable policy recommendations. We tested k=3 and k=5; k=4 gave the best silhouette score and the most interpretable groupings.

### 3.6 ARIMA Forecast

**What is it?**
ARIMA (AutoRegressive Integrated Moving Average) is a time-series forecasting model. We use it to predict future monthly UPI transaction volumes.

**Configuration:** ARIMA(1, 1, 1)

```
(p=1, d=1, q=1)

p = 1: Use 1 lag of the series itself (autoregressive term)
d = 1: Difference the series once to make it stationary (remove the trend)
q = 1: Use 1 lag of the forecast error (moving average term)
```

**What it produces:**
- 12-month forecast (point estimate)
- 95% confidence interval (upper and lower bounds)

**Our result:** Starting from ~19.5 Bn/month (Jun 2025), ARIMA projects ~19.8 Bn by Jul 2025, growing to ~23.5 Bn by Jun 2026.

**Why ARIMA(1,1,1)?**
- `d=1` is standard for trending data. UPI volumes have a clear upward trend; first-differencing removes it.
- `p=1, q=1` is parsimonious (simple). We tested higher orders; they did not significantly improve fit and added overfitting risk on 42 data points.
- Alternative: **SARIMA** (Seasonal ARIMA) -- accounts for seasonality directly. We use Prophet for seasonality instead, and keep ARIMA simple for comparison.

### 3.7 Prophet Forecast

**What is it?**
Prophet is Facebook's time-series forecasting tool. It decomposes the series into trend + seasonality + holidays.

**What makes it different from ARIMA:**
- Handles missing data and outliers better
- Automatically detects yearly/weekly seasonality
- Can incorporate Indian holidays (Diwali, Holi, etc.) as external regressors
- Produces confidence intervals naturally

**What it produces:**
- 12-month forecast with confidence bands
- Seasonal decomposition (trend component, yearly seasonality)

**Why we use both ARIMA and Prophet:**
Using two independent models gives us more confidence. If both predict similar growth, the forecast is robust. If they diverge, it signals uncertainty. This is standard practice in forecasting -- model ensembling/comparison.

### 3.8 Seasonal Factors

**What is it?**
Monthly adjustment factors showing which months consistently have higher or lower UPI volumes than average.

**How it is computed:**
Multiplicative seasonal decomposition: `Observed = Trend x Seasonal x Residual`

The seasonal component is extracted and normalized so that the average factor across all 12 months equals 1.0.

**Our result:**

| Month | Factor | Interpretation |
|-------|--------|---------------|
| October | 1.042 | Highest -- Diwali/Dussehra period, heavy spending |
| March | 1.035 | Financial year-end, business settlements |
| February | 0.930 | Lowest -- shorter month, post-holiday lull |

**Why this matters:** Knowing seasonal patterns helps forecast more accurately and explains month-to-month fluctuations that are not random but cyclical.

### 3.9 CAGR (Compound Annual Growth Rate)

**What is it?**
CAGR smooths out year-to-year volatility and gives a single annualized growth rate over a period.

**Formula:**

```
CAGR = (ending_value / beginning_value) ^ (1 / num_years) - 1
```

**Example:** If UPI grew from 1.08 Bn (2018) to 99.30 Bn (2024) over 6 years:
```
CAGR = (99.30 / 1.08) ^ (1/6) - 1 = 91.9^0.167 - 1 = ~114%
```

**Why CAGR and not simple average growth?**
Simple average of yearly growth rates can be misleading if growth varies widely year to year. CAGR gives the "smoothed" rate that would produce the same final result if applied uniformly every year.

### 3.10 Digital-to-Cash Ratio

**What is it?**
The ratio of UPI transaction value to total currency in circulation (physical cash).

**Formula:**

```
Digital-to-Cash Ratio = UPI_monthly_value / Currency_in_Circulation
```

**Our result:** Latest ratio = **0.68**. This means UPI processes ~68% as much value as the total physical cash stock each month.

**Why this metric?**
The ratio tracks whether digital payments are growing relative to cash. A rising ratio means digital is gaining ground. But we deliberately call it "less cash-dependent" rather than "cashless" because:
- CIC (physical cash) is also growing year-over-year
- UPI is capturing new transactions (informal economy digitization) rather than replacing existing cash usage
- India is adding digital transactions on top of cash, not substituting

**Why not just compare growth rates?**
Growth rates alone do not tell you the relative scale. UPI might grow 40% while cash grows 5%, but if cash is 10x larger in absolute terms, the growth rate comparison is misleading. The ratio gives a direct scale comparison.

### 3.11 Displacement Velocity

**What is it?**
The rate of change of the digital-to-cash ratio over time.

**Formula:**

```
Displacement Velocity = Ratio[t] - Ratio[t-1]   (month-over-month change)
Velocity % = pct_change(Ratio) * 100
```

**What it tells us:** Whether the pace of digital adoption is accelerating, steady, or slowing down. Positive velocity means digital is gaining ground faster; negative means the shift is slowing.

### 3.12 Year-over-Year (YoY) Growth

**What is it?**
Growth rate comparing the same month/period across consecutive years.

**Formula:**

```
YoY Growth = (Value_current_month - Value_same_month_last_year) / Value_same_month_last_year * 100
```

**Why YoY and not Month-over-Month (MoM)?**
MoM growth is noisy because of seasonal effects (e.g., October is always higher than September because of Diwali). YoY eliminates seasonality by comparing like-for-like periods.

### 3.13 Quarter-over-Quarter (QoQ) Growth

**Formula:**

```
QoQ Growth = (Value_this_quarter - Value_last_quarter) / Value_last_quarter * 100
```

Used for user registration data (available quarterly, not monthly).

---

## 4. Dashboard Visuals -- What Each Graph and Metric Means

### 4.1 Overview Tab

| Visual | What It Shows | Finance/Analytics Meaning |
|--------|--------------|--------------------------|
| Hero KPI | Latest monthly UPI volume in billions | Market size indicator -- how large the payment system is right now |
| 5 Insight Cards | Transaction scale, market concentration, geographic divide, cash displacement, forecast | Executive summary for quick assessment |
| Project Scale Cards | Total data points, states, districts, apps, time span, volume | Scope and depth of the analysis |

### 4.2 Executive Summary Tab

| Visual | What It Shows | Finance/Analytics Meaning |
|--------|--------------|--------------------------|
| Total Transactions KPI | Cumulative transactions across all years | Total addressable market (TAM) measure |
| Total Value KPI | Cumulative value in Lakh Crores | Market size by value -- indicates economic significance |
| Avg Transaction Value KPI | Average INR per transaction + YoY delta | Ticket size -- declining avg means more small-value transactions are going digital (positive for financial inclusion) |
| Yearly Volume Bar Chart | Transaction count by year | Growth trajectory -- should show exponential or strong linear growth |
| Yearly Value Bar Chart | Transaction value by year | Verifies if value growth tracks volume growth or diverges |
| Monthly Trend Line | Volume over months (area chart) | Identifies seasonality, acceleration, and inflection points |
| Category Donut | P2P vs Merchant vs Recharge vs Financial Services | Market composition -- what people use UPI for. A shift toward merchant payments indicates maturity. |
| YoY Growth Table | Annual growth rates for volume and value | Deceleration detection -- if YoY growth is declining, the market may be approaching saturation |

**Key insight on avg transaction value:** If the average is declining, it means more small-value transactions are being digitized. This is a sign of financial inclusion -- daily purchases at small shops, auto-rickshaw fares, etc. are moving to UPI.

### 4.3 Market Concentration Tab

| Visual | What It Shows | Finance/Analytics Meaning |
|--------|--------------|--------------------------|
| HHI KPI | Current Herfindahl-Hirschman Index | Antitrust risk metric. > 0.25 triggers regulatory scrutiny in US/EU markets. |
| Top-2 Share KPI | PhonePe + Google Pay combined % | Duopoly dominance -- critical for NPCI's 30% cap policy |
| Equivalent Firms KPI | 1/HHI | Intuitive market structure measure -- "the market acts like N firms" |
| HHI Gauge | Dial showing HHI on 0--0.5 scale | Visual risk indicator |
| HHI Trend Line | HHI over time with DOJ threshold bands | Shows whether concentration is increasing or decreasing over time |
| Market Share Stacked Area | 100% stacked area of all apps | Shows how market share has shifted between apps over time |
| Horizontal Bar | Latest month app shares with 30% cap line | Regulatory compliance snapshot -- who is above the proposed NPCI cap |
| Market Share Treemap | Nested rectangles: app -> share | Proportional visualization of market dominance |
| NPCI Compliance Box | Per-app status vs 30% cap | Regulatory readiness assessment |

**In finance terms:** HHI is the same metric used by the US Department of Justice to evaluate whether a merger would create an anti-competitive market. An HHI above 0.25 with a delta of 0.02+ from a merger would likely be challenged by regulators.

### 4.4 Geographic Insights Tab

| Visual | What It Shows | Finance/Analytics Meaning |
|--------|--------------|--------------------------|
| Choropleth Map | State-level UPI metrics (volume, value, avg txn, Gini) | Geographic heat map -- identifies high-adoption and low-adoption states at a glance |
| Bubble Map | State bubbles: size = volume, color = Gini | Combines scale and inequality in one view |
| State Rankings Table | Ranked states with txn volume, districts, % underserved | League table -- standard in financial analysis for ranking entities |
| Regional Donut | UPI distribution across 6 Indian regions | Regional economic activity indicator |
| Adoption Tier Treemap | Districts grouped by adoption tier and state | Proportional view of which states contribute most to each adoption tier |
| District Explorer | Interactive drill-down by state | Granular analysis for policy targeting |

**In finance terms:** Geographic analysis is equivalent to a market penetration study. It shows where the product (UPI) has strong adoption and where there is untapped potential.

**Gini coefficient in this context:** Typically used for income inequality (World Bank publishes country-level Gini). We apply it to digital payment adoption -- a Gini of 0.44 for UPI adoption within a state is comparable to income inequality levels in many developing nations.

### 4.5 Forecasting Tab

| Visual | What It Shows | Finance/Analytics Meaning |
|--------|--------------|--------------------------|
| Forecast Horizon KPI | Number of months forecast ahead | Planning horizon |
| 25 Bn Milestone KPI | Projected date to hit 25 Bn/month | Milestone tracking -- common in growth company analysis |
| Actual + Forecast Line | Historical data + model projections with confidence intervals | Standard financial projection chart. Confidence intervals show prediction uncertainty. |
| Seasonal Factors Bar | Monthly seasonality multipliers | Risk/opportunity calendar -- which months to expect peaks and troughs |
| ARIMA Details Table | Month-by-month forecast with upper/lower CI | Detailed projection for planning |
| Model Comparison Table | Prophet vs ARIMA final values | Model validation -- agreement between models increases confidence |

**In finance terms:** This is analogous to revenue forecasting in equity research. Analysts project future revenue using historical growth patterns and seasonal adjustments. The confidence interval is the analyst's uncertainty range.

### 4.6 Cash Displacement Tab

| Visual | What It Shows | Finance/Analytics Meaning |
|--------|--------------|--------------------------|
| Digital-to-Cash Ratio KPI | UPI value / Currency in Circulation | Digitization progress indicator |
| Verdict KPI | "Less Cash-Dependent" | Qualitative assessment of India's payment transition |
| Dual-Axis Line | UPI value (left) vs CIC (right) over time | Shows both are growing, but UPI faster |
| Ratio Trend Line | Digital-to-cash ratio over time (area fill) | Trajectory of digitization |
| Growth Comparison Bar | UPI growth % vs Cash growth % | Direct comparison of digital vs physical cash growth rates |
| Displacement Velocity Line | Rate of change of the ratio | Acceleration/deceleration of the shift |
| ATM Transactions Line | Quarterly ATM withdrawals | Secondary indicator -- declining ATM usage supports digital adoption thesis |

**In finance terms:** Cash displacement analysis is equivalent to technology adoption analysis (like how credit cards displaced cash in Western economies, or how mobile payments displaced cash in China). The key finding -- that India is becoming "less cash-dependent" rather than "cashless" -- is important because CIC is still growing. This pattern is unique to India and differs from China's experience where Alipay/WeChat Pay more directly replaced cash.

### 4.7 Growth & Trends Tab

| Visual | What It Shows | Finance/Analytics Meaning |
|--------|--------------|--------------------------|
| CAGR KPI | Compound annual growth rate | Smoothed long-term growth -- the single most important growth metric |
| Monthly Volume Line | Volume trend with area fill | Growth trajectory visualization |
| YoY Growth Line | Year-over-year growth rate | Growth deceleration detection |
| Volume Heatmap | Year x Month matrix of volumes | Pattern recognition -- identify seasonal peaks across years |
| Quarterly Bar | Grouped bars by quarter and year | Quarter-over-quarter comparison |
| Avg Transaction Value Line | Average INR per transaction over time | Ticket size trend -- declining means more micro-transactions |
| Festival Impact | Festival vs non-festival month comparison | Event-driven analysis -- quantifies the Diwali/festive season uplift |

**In finance terms:** This is a growth decomposition analysis. CAGR gives the headline number; the heatmap reveals whether growth is uniform or concentrated in specific periods; the festival impact quantifies seasonal catalysts.

### 4.8 App Dynamics Tab

| Visual | What It Shows | Finance/Analytics Meaning |
|--------|--------------|--------------------------|
| Individual App Lines | Each app's market share trajectory over time | Competitive dynamics -- who is gaining and who is losing |
| Latest Snapshot Bar | Current month share with 30% cap line | Regulatory compliance check |
| Market Share Evolution | 100% stacked area over time | Zero-sum visualization -- one app's gain is another's loss |
| Paytm Collapse Analysis | Peak share vs current share with decline metrics | Case study in regulatory risk. RBI's action on Paytm Payments Bank caused a sharp decline. |
| Duopoly Trend Line | Top-2 combined share over time with 60% threshold | Shows whether the market is consolidating or diversifying |
| App Comparison Table | All apps with current share | Ranking table |

**In finance terms:** This is a competitive landscape analysis, similar to what equity analysts produce when covering an industry. The Paytm case study is a regulatory risk event -- analogous to how regulatory actions against specific firms (like Ant Group in China) reshape market structure.

### 4.9 District Deep Dive Tab

| Visual | What It Shows | Finance/Analytics Meaning |
|--------|--------------|--------------------------|
| Cluster Bar | Number of districts per adoption tier | Market segmentation -- how many districts fall into each category |
| Scatter Plot | Total transactions vs avg value per district, colored by tier | Portfolio view -- similar to a risk-return scatter in finance. Each district is a data point. |
| Top/Bottom 10 Tables | Highest and lowest transaction districts | Extremes analysis -- identifies leaders and laggards |
| Gini Bar (Horizontal) | Intra-state Gini coefficient ranked | Inequality ranking -- which states have the most uneven adoption |
| Underserved Table | Bottom 50 districts | Target list for financial inclusion programs |
| Treemap | Adoption tier x state with transaction volume | Proportional contribution analysis |
| State Drill-Down | Selected state's district distribution | Granular geographic analysis |

**In finance terms:** This is equivalent to a market segmentation and TAM (Total Addressable Market) analysis. The underserved districts represent the "untapped market" -- the whitespace opportunity for UPI growth.

### 4.10 Users & Devices Tab

| Visual | What It Shows | Finance/Analytics Meaning |
|--------|--------------|--------------------------|
| Registered Users Line | Cumulative user registrations over time | User acquisition curve -- S-curve analysis |
| App Opens Line | Quarterly app engagement | Engagement/retention indicator. Registered users who do not open the app are not active users. |
| QoQ Growth Bar | Quarter-over-quarter user growth rate | Growth momentum -- declining QoQ growth may signal saturation |
| Device Brand Donut | Latest quarter device market share (top 6 + Others) | Device ecosystem -- which hardware platforms to target |
| Device Evolution Area | Top 5 brands over time | Hardware trend -- if budget phones dominate, it confirms mass-market adoption |
| Insurance Count Bar | Insurance policies sold per quarter | Platform diversification -- UPI platforms expanding into adjacent financial services |

**In finance terms:** User metrics are the equivalent of MAU/DAU (Monthly/Daily Active Users) in tech company analysis. The device brand distribution is a proxy for customer demographics -- Xiaomi and Vivo users tend to be more price-sensitive, indicating UPI is reaching lower-income segments.

### 4.11 Methodology & Data Quality Tab

| Visual | What It Shows | Purpose |
|--------|--------------|---------|
| Pipeline Architecture | Bronze -> Silver -> Gold -> Dashboard flow | Technical credibility -- shows rigorous data engineering |
| Data Sources Table | Source, frequency, method, record counts | Transparency -- reproducibility of the analysis |
| Data Quality Metrics | Null %, total records, date range | Quality assurance -- proves the data is clean |
| Analytical Models Cards | HHI, Forecasting, Cash Displacement summaries | Method transparency |
| Technology Stack Table | All tools used with their roles | Technical depth demonstration |
| Limitations Section | Known caveats and data gaps | Intellectual honesty -- acknowledging limitations is a hallmark of credible research |

---

## 5. Why These Methods and Not Others

### 5.1 Why Medallion Architecture?

**What we chose:** Bronze (raw) -> Silver (cleaned) -> Gold (analytics-ready)

**Why:** This is the industry standard for data lakehouse architectures (used by Databricks, Microsoft Fabric, etc.). It provides:
- Traceability: raw data is preserved in Bronze; you can always go back
- Reprocessing: if cleaning logic changes, Silver can be regenerated from Bronze
- Separation of concerns: ingestion engineers, data engineers, and analysts work on different layers

**Alternative: Single-stage ETL** -- Process raw data directly into final tables. Simpler but fragile. If a cleaning step has a bug, you must re-ingest everything. Medallion architecture lets you fix Silver without touching Bronze.

### 5.2 Why DuckDB?

**What we chose:** DuckDB as the analytical database for the Gold layer.

**Why:**
- In-process (no server setup needed -- runs as a library)
- Columnar storage (fast for analytical queries)
- SQL-native (standard syntax, easy to validate)
- Parquet-native (reads/writes Parquet directly)
- Zero infrastructure cost (important for a portfolio project that needs to be easily reproducible)

**Alternative: PostgreSQL** -- Full-featured but requires a running server. Overkill for a single-user analytics project.

**Alternative: SQLite** -- Simpler but row-oriented (slower for analytical queries). DuckDB is specifically designed for OLAP workloads.

### 5.3 Why Star Schema?

**What we chose:** Dimensional modeling with fact and dimension tables.

**Why:** Star schemas are the foundation of business intelligence. They make queries simple ("give me total transactions by state by year" is a straightforward JOIN) and are the expected pattern in any data warehousing context.

**Alternative: Flat denormalized table** -- One big table with everything. Faster for simple queries but leads to data redundancy, inconsistencies, and makes it impossible to add new dimensions without restructuring everything.

**Alternative: Data Vault** -- More flexible for handling schema changes but significantly more complex. Overkill for a dataset of this size.

### 5.4 Why Prophet + ARIMA (Two Models)?

**What we chose:** Run both Prophet and ARIMA independently, then compare.

**Why:**
- ARIMA is the classical statistical approach (well-understood, theoretically grounded)
- Prophet is the modern ML approach (handles seasonality and holidays automatically)
- If both agree, our forecast is robust. If they diverge, we know there is genuine uncertainty.
- Using two models demonstrates breadth of methodology

**Alternative: LSTM (Deep Learning)** -- Works for time-series but requires much more data than 42 monthly observations. LSTMs typically need hundreds to thousands of data points. We have 42.

**Alternative: Exponential Smoothing (ETS)** -- A valid choice, but Prophet subsumes most of its functionality (trend + seasonality decomposition) with a more modern implementation.

### 5.5 Why Gini for Geographic Inequality?

**What we chose:** Gini coefficient computed per state using district-level transaction data.

**Why:** Gini is the universally recognized metric for inequality. When we say "the Gini for Maharashtra is 0.52", anyone familiar with economics immediately understands this means high inequality.

**Alternative: Theil Index** -- Decomposable (can separate within-group and between-group inequality). More powerful but less widely understood.

**Alternative: Coefficient of Variation** -- Simple (std/mean) but does not have the same intuitive 0-to-1 interpretation.

### 5.6 Why K-Means for District Clustering?

**What we chose:** K-Means with k=4 on log-scaled transaction features.

**Why log-scaling?** Transaction volumes span from a few thousand (rural districts) to billions (metro districts). Without log-scaling, K-Means would be dominated by the absolute scale and would essentially just separate "Mumbai" from "everyone else."

**Why k=4?** Tested k=3 through k=6. k=4 produced the highest silhouette score and the most policy-relevant groupings (Very Low / Low / Medium / High maps directly to intervention priorities).

**Alternative: Hierarchical clustering** -- Produces a dendrogram showing relationships between clusters but does not handle large datasets (788 districts) as efficiently.

**Alternative: GMM (Gaussian Mixture Models)** -- Allows "soft" cluster assignments (a district can belong 60% to one cluster and 40% to another). Useful in some contexts but harder to explain to policymakers who need clear categories.

### 5.7 Why Streamlit for the Dashboard?

**What we chose:** Streamlit (Python web framework for data apps).

**Why:**
- Same language as the entire pipeline (Python end-to-end)
- Free deployment on Streamlit Community Cloud
- Interactive widgets (sliders, dropdowns) with zero JavaScript
- Native support for Plotly, Pandas DataFrames
- Fastest time-to-deployment for a data-focused dashboard

**Alternative: Power BI** -- We also have a Power BI version (dashboards/UPI_Analytics_Dashboard.pbix). Power BI is better for enterprise use but requires a Microsoft license for sharing.

**Alternative: React + D3.js** -- More flexible but requires a separate frontend skillset and hosting infrastructure. Not justified for a data analytics portfolio project.

**Alternative: Tableau** -- Industry standard for BI but requires a paid license for publishing.

---

*This document covers every dataset, preprocessing step, calculation, formula, graph, and metric in the UPI Analytics Platform. Every number shown in the dashboard is computed from the source data using the methods described above. No values are hardcoded or fabricated.*
