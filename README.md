# Next-Day Rainfall Prediction and Weather-Risk Decision Support System

Mini project for **IT3051 Fundamentals of Data Mining**.

The project will develop a reproducible workflow for predicting next-day
rainfall and presenting weather-risk information for decision support.

## Current scope

T00 Project Setup through T10 Leakage-Safe Hyperparameter Tuning have been
completed. T10 tunes the four T09 classifier families using three whole-date,
expanding Train-only cross-validation folds with fold-local preprocessing and
PR-AUC as the sole performance metric for candidate selection. ROC-AUC, F1,
recall, and balanced accuracy are interpretive only; exact PR-AUC ties use
original candidate order as a neutral deterministic tie-break, and no current
winner required it. Each selected configuration is refitted on complete Train
and evaluated once on Validation. The held-out Test subset remains unevaluated;
no resampling, threshold optimization, feature selection, or final-model
selection has started.

The T08 engineered default uses cyclical month, five within-day weather
differences, and cyclical wind direction with explicit missing indicators. The
original T07 preprocessing option remains available. Year and transformed
rainfall are optional, and climate-zone grouping is deferred until an
authoritative mapping is available.

The T09 baselines are Logistic Regression (scaled engineered inputs), Decision
Tree, Random Forest, and Gradient Boosting (unscaled engineered inputs). See
`reports/evidence/09_baseline_models.md` for the Validation-only results and
verification record. See `reports/evidence/10_hyperparameter_tuning.md` for the
T10 search design, selected configurations, Validation-only comparison, and
verification record.

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

The command exits with status code `0`, prints PASS results for T00 through T08,
and reports completion of the Progress Evaluation 1 implementation stage when
all completed-stage requirements are satisfied.
