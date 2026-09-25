# Next-Day Rainfall Prediction and Weather-Risk Decision Support System

Mini project for **IT3051 Fundamentals of Data Mining**.

The project will develop a reproducible workflow for predicting next-day
rainfall and presenting weather-risk information for decision support.

## Current scope

T00 Project Setup, T01 Dataset Verification, and T02 Data Understanding have
been completed. Detailed missing-value and relationship EDA, outlier analysis,
data preparation, feature engineering, and model development have not started.

## Project structure

```text
docs/                 Project documentation
data/
  raw/                Original, immutable input data
  interim/            Intermediate data artifacts
  processed/          Analysis-ready data artifacts
notebooks/            Future analysis notebooks
src/fdm_rainfall/     Python package source
tests/                Automated tests
reports/
  figures/            Generated figures
  tables/             Generated tables
  evidence/           Task verification evidence
scripts/              Project utility and verification scripts
```

## Verify the completed stage

From the repository root, run:

```bash
python scripts/verify_stage1.py
```

The command exits with status code `0` and prints PASS results for T00 through
T02 when the completed-stage requirements are satisfied.
