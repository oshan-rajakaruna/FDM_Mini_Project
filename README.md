# Next-Day Rainfall Prediction and Weather-Risk Decision Support System

Mini project for **IT3051 Fundamentals of Data Mining**.

The project will develop a reproducible workflow for predicting next-day
rainfall and presenting weather-risk information for decision support.

## Current scope

T00 Project Setup through T07 Data Preprocessing have been completed. Feature
engineering and model development have not started.

## RainToday threshold clarification

The proposal describes `RainToday = Yes` as rainfall of "1 mm or more". T04
found that the usable dataset pairs follow the strict convention
`Rainfall > 1.0 mm`: values exactly equal to 1.0 mm are labelled `RainToday = No`.

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
T07 when the completed-stage requirements are satisfied.
