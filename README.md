Water Quality Intelligence Platform

1. Project Overview

The Water Quality Intelligence Platform is a data engineering application that processes historical water-quality issue records across India.

It ingests raw CSV data, cleans and transforms records, stores the processed dataset in Parquet format, performs analytical queries using DuckDB, and provides results through a FastAPI backend and Streamlit dashboard.

The platform also supports background pipeline execution, job-status monitoring, and a data-quality report.

2. Objectives

Build an end-to-end data engineering pipeline.

Clean and standardize raw CSV data.

Remove duplicate records.

Validate dates and essential fields.

Generate a data-quality report.

Store processed data efficiently in Parquet format.

Generate analytics using DuckDB.

Expose analytical results through REST API endpoints.

Visualize results using an interactive dashboard.

Monitor pipeline execution and identify failures.

Validate API behavior using automated tests.

3. Technology Stack

Technology

Purpose

Python

Core programming language

Pandas

Data processing and cleaning

PyArrow

Parquet support

DuckDB

Analytical SQL queries

FastAPI

REST API backend

Uvicorn

ASGI application server

Streamlit

Interactive dashboard

Plotly

Data visualization

Pytest

Automated testing

HTTPX

HTTP client and test support

4. System Architecture

Raw CSV Dataset
      |
      v
Data Ingestion
      |
      v
Data Cleaning and Validation
      |
      +----> Data Quality Report (CSV)
      |
      v
Processed Parquet Dataset
      |
      v
DuckDB Analytics
      |
      v
Generated Analytics CSV Files
      |
      v
FastAPI REST API
      |
      v
Streamlit Dashboard

Pipeline execution can be triggered through the API and monitored using a unique job ID.

5. Project Structure

DE mini project/
├── backend/
│   ├── main.py
│   └── pipeline_manager.py
├── dashboard/
│   └── app.py
├── data/
│   ├── raw/
│   │   └── IndiaAffectedWaterQualityAreas.csv
│   ├── processed/
│   │   └── water_quality_cleaned.parquet
│   └── analytics/
│       ├── records_by_state.csv
│       ├── records_by_parameter.csv
│       ├── records_by_year.csv
│       ├── top_districts.csv
│       └── data_quality_report.csv
├── src/
│   ├── ingestion.py
│   ├── etl_pipeline.py
│   ├── analytics.py
│   └── verify_data.py
├── tests/
│   └── test_api.py
├── requirements.txt
└── README.md

6. Data Pipeline

Stage 1: Data Ingestion

The ingestion module reads the original CSV dataset and inspects its structure, columns, data types, missing values, and duplicates.

Stage 2: ETL Processing

The ETL module standardizes column names, removes surrounding whitespace, converts date values into year values, removes duplicate records, validates required fields, and writes the cleaned dataset to Parquet format.

It also generates data/analytics/data_quality_report.csv, which records the original record count, invalid dates, duplicates removed, final record count, column count, missing-value statistics, and validation status.

Stage 3: Analytics

The analytics module uses DuckDB to calculate record counts, state-level summaries, parameter distributions, yearly summaries, and district rankings. The results are exported as CSV files.

Stage 4: API Service

FastAPI exposes endpoints for dataset summaries, state statistics, quality parameters, yearly statistics, district statistics, and pipeline execution monitoring.

Stage 5: Dashboard

Streamlit presents dataset statistics, charts, filters, pipeline progress, job details, downloadable analytics, and the data-quality report.

7. Data Quality Report

The current report was generated successfully with the following results:

Metric

Current result

Original records

550,242

Invalid dates

0

Duplicates removed

90

Final records

550,152

Total columns

8

Missing values

0

Missing values by column

{}

Validation status

Passed

These figures describe the current source dataset and the checks performed by the implemented ETL pipeline. A passed status means the implemented validations passed; it does not guarantee that all source values are factually correct or establish current drinking-water safety.

8. API Endpoints

Method

Endpoint

Purpose

GET

/

API home

GET

/api/health

Health check

GET

/api/summary

Dataset summary

GET

/api/states

State-level statistics

GET

/api/parameters

Parameter statistics

GET

/api/years

Yearly statistics

GET

/api/districts

District statistics

POST

/api/pipeline/run

Start a pipeline run

GET

/api/pipeline/status/{job_id}

Check job status

Interactive API documentation is available at /docs while the backend is running.

9. Installation

Prerequisites

Python

Visual Studio Code

The project CSV dataset

Create a virtual environment

Windows PowerShell:

python -m venv .venv

Activate it:

.\.venv\Scripts\Activate.ps1

Install dependencies

python -m pip install -r requirements.txt

10. Running the Application

Run each command from the project root (C:\DE mini project).

Step 1: Run the pipeline

python src/ingestion.py
python src/etl_pipeline.py
python src/analytics.py

Step 2: Start the backend

python -m uvicorn backend.main:app --reload

API documentation:

http://127.0.0.1:8000/docs

Health check:

http://127.0.0.1:8000/api/health

Step 3: Start the dashboard

Open a second terminal and run:

python -m streamlit run dashboard/app.py

Open the local dashboard address printed in the terminal, usually http://localhost:8501.

11. Automated Testing

Run the API tests using:

python -m pytest tests/test_api.py -v

The current test run completed successfully: 8 tests passed. The tests cover the home endpoint, health endpoint, summary, states, parameters, years, districts, and handling of an invalid pipeline job ID.

A Starlette deprecation warning about the current HTTP test-client integration was also shown. It did not cause any test failures.

12. Current Dataset Summary

The processed dataset currently contains:

550,152 records

27 distinct states or regions

493 distinct district names

5 quality parameters

Historical records spanning 2009–2012

These values should be rechecked if the source data changes.

13. Limitations

The dataset contains historical reported water-quality issue records rather than continuous live sensor measurements.

The application does not establish the current safety of drinking water at a location.

Pipeline job history is stored in application memory and is lost when the backend restarts.

The application currently processes a local dataset rather than continuously ingesting data from a live external source.

14. Future Enhancements

Persistent job history using a database.

Scheduled pipeline execution.

External data-source integration.

Improved logging and monitoring.

More advanced geographical visualizations.

Deployment to a cloud platform.

15. Conclusion

The Water Quality Intelligence Platform demonstrates an end-to-end data engineering workflow involving data ingestion, ETL, data-quality reporting, analytical storage, SQL-based analysis, REST APIs, interactive visualization, background execution, and automated testing.