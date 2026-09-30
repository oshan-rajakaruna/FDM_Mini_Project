# Next-Day Rainfall Prediction and Weather-Risk Decision Support System

Mini project for **IT3051 Fundamentals of Data Mining**.

The project will develop a reproducible workflow for predicting next-day
rainfall and presenting weather-risk information for decision support.

## Current scope

T00 Project Setup through T11 Controlled Feature / Representation Optimization
have been completed. T11 evaluates exactly four pre-declared T08
representations for the four fixed T10-tuned model families using whole-date,
expanding Train-only cross-validation and fold-local preprocessing. PR-AUC is
the sole representation-selection metric. Logistic Regression selected the
log-Rainfall replacement, Decision Tree and Random Forest retained the default,
and Gradient Boosting selected Year; the observed changes were small and mixed.
The held-out Test subset remains unevaluated, and no final model has been
selected. Final selection and one-time Test evaluation remain reserved for
T12.

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
verification record. See `reports/evidence/11_feature_optimization.md` for the
controlled feature-variant experiment, Train-CV selections, Validation-only
comparison, and verification record.

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
