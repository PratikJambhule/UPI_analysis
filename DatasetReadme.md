---
pretty_name: India UPI Ecosystem (2018-2025)
language:
  - en
license: cdla-permissive-2.0
task_categories:
  - tabular-regression
task_ids:
  - time-series-forecasting
size_categories:
  - 10K<n<100K
source_datasets:
  - original
tags:
  - upi
  - india
  - digital-payments
  - finance
  - analytics
---

# India UPI Ecosystem Dataset (2018-2025)

## Dataset Summary

This dataset analyzes India's UPI transaction ecosystem by combining district-level app and usage data, official NPCI benchmark statistics, and RBI macroeconomic cash indicators.  
It is a merged and enriched analytics dataset designed for market concentration studies, geographic adoption analysis, forecasting, and cash displacement research.

## Data Sources

| Source | What it contains | Why it was used |
| --- | --- | --- |
| [PhonePe Pulse](https://github.com/PhonePe/pulse) | District-level UPI transactions, user registrations, and related app usage fields. Time period: Q1 2018 - Q2 2025. | Provides granular district-level coverage needed for regional adoption and inequality analysis. |
| [NPCI UPI Ecosystem Statistics](https://www.npci.org.in/what-we-do/upi/upi-ecosystem-statistics) | Official monthly UPI transaction volumes and app market-share values. Time period: Jan 2022 - Jun 2025. | Serves as official benchmark and ground-truth reference for national UPI trends and app shares. |
| [RBI DBIE](https://dbie.rbi.org.in) | Currency in circulation and ATM transaction volumes. Time period: Q1 2019 - Q2 2025. | Adds macroeconomic cash indicators required for digital-vs-cash displacement analysis. |

## Data Format & Usage

The final merged dataset is stored in `.parquet` format for efficient loading and analytics workflows.

```python
from datasets import load_dataset

# Load directly from Hugging Face
dataset = load_dataset("PratikJambhule/india-upi-ecosystem-2018-2025")
print(dataset)
```

## Acknowledgements & Attribution

This dataset is derived from:

- PhonePe Pulse
- National Payments Corporation of India (NPCI)
- Reserve Bank of India (RBI DBIE)

PhonePe Pulse data is governed by the **CDLA-Permissive-2.0** open data license, and this combined dataset is released under `cdla-permissive-2.0`.
