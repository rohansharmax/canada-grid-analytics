
# Canada Grid Analytics

ETL pipeline + interactive dashboard for Canadian electricity generation data, sourced live from Statistics Canada.

## What it does

Pulls monthly electricity generation data (2008–present) for every Canadian province and territory, across 9 generation sources (hydraulic, nuclear, wind, solar, combustion, etc.), from the StatCan Web Data Service API. Cleans it, validates it, loads it into a star-schema SQLite database, and serves it through a filterable Streamlit dashboard.

## Pipeline

```
extract.py   → Pull full table from StatCan API (table 25-10-0015-01), cache raw CSV
transform.py → Clean columns, parse dates, remove aggregate/subtotal rows
quality.py   → Automated quality gates (nulls, duplicates, date sanity, anomaly detection)
load.py      → Build star schema (fact_generation + dim_region/source/date) in SQLite
app.py       → Streamlit + Plotly dashboard
```

## Key finding: net-negative generation

Initial quality checks flagged 297 rows with negative generation values. Investigation showed StatCan reports **net** generation — idle plants can legitimately consume more power than they produce, producing small negative values. Rather than dropping these as bad data, the quality gate was redesigned to allow small net-negatives while flagging anything below −150,000 MWh as a genuine anomaly worth investigating.

## Setup

```
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

## Run the pipeline

```
python extract.py
python transform.py
python quality.py
python load.py
```

## Run the dashboard

```
streamlit run app.py
```

## Run tests

```
pytest -v
```

## Stack

Python, pandas, SQLite, Streamlit, Plotly, pytest, requests

## Data source

Statistics Canada, Table 25-10-0015-01 — Electric power generation, monthly, by province/territory and type of electricity generation. Accessed via the StatCan Web Data Service API: https://www.statcan.gc.ca/en/developers/wds
