# Next-Day Rainfall Prediction and Weather-Risk Decision Support System

Mini project for **IT3051 Fundamentals of Data Mining**.

The project provides a reproducible workflow and local web application for
predicting next-day rainfall and presenting weather-risk information for
decision support.

## Current scope

T00 Project Setup through T12 Final Model Selection and Final Holdout Test
Evaluation have been completed. T12 ranked the four T11-selected candidates by
full-precision Validation PR-AUC before Test access and selected Random Forest
with the V0 default representation. The frozen pipeline was refitted on 120,888
Train+Validation rows and evaluated once on the 21,305-row chronological Test
period. Final Test PR-AUC was 0.729349 and ROC-AUC was 0.875865. No model,
representation, hyperparameter, resampling, or threshold decision changed
after Test evaluation.

The fitted pipeline is persisted at `models/final_rainfall_model.joblib`, with
its Train+Validation-fitted preprocessing state, ordered feature schema,
positive-class and threshold definitions, and inference metadata. A React/Vite
frontend and FastAPI backend provide local model inference and browser-local
prediction history without changing the frozen model pipeline.

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
comparison, and verification record. See
`reports/evidence/12_final_model_selection.md` for the pre-Test final selection,
one-time holdout evaluation, serialization verification, and completion record.

## RainToday threshold clarification

The proposal describes `RainToday = Yes` as rainfall of "1 mm or more". T04
found that the usable dataset pairs follow the strict convention
`Rainfall > 1.0 mm`: values exactly equal to 1.0 mm are labelled `RainToday = No`.

## Project structure

```text
docs/                 Project documentation
backend/              FastAPI application and Python dependencies
frontend/             React/Vite user interface
data/
  raw/                Original, immutable input data
  interim/            Intermediate data artifacts
  processed/          Analysis-ready data artifacts
notebooks/            Executed analysis and modeling notebooks
models/                Persisted trained model artifacts
src/fdm_rainfall/     Python package source
tests/                Automated tests
reports/
  figures/            Generated figures
  tables/             Generated tables
  evidence/           Task verification evidence
scripts/              Project utility and verification scripts
```

## Run RainWise locally

Run the backend and frontend in separate terminals from the repository root.

Install the API dependencies, copy the safe environment template, and add your
MongoDB Atlas connection details to the untracked `backend/.env` file:

```powershell
python -m pip install -r backend/requirements.txt
Copy-Item backend/.env.example backend/.env
```

`MONGODB_URI` is required. `MONGODB_DATABASE` defaults to `rainwise` when it is
not set. Never commit `backend/.env` or place credentials in source files.

Start the API after configuration:

```powershell
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000
```

Install and start the frontend:

```powershell
Set-Location frontend
npm.cmd install
npm.cmd run dev -- --host 127.0.0.1 --port 5173
```

Open `http://127.0.0.1:5173`. The API health endpoint is available at
`http://127.0.0.1:8000/health`, and interactive API documentation is available
at `http://127.0.0.1:8000/docs`. Both local services must be running to request
a prediction. Successful predictions are stored by the backend in the
configured MongoDB database and can be reviewed or deleted from the History
page.

To verify the frontend production build, run:

```powershell
Set-Location frontend
npm.cmd run build
```

## Verify the completed stage

From the repository root, run:

```bash
python scripts/verify_stage1.py
```

The command exits with status code `0`, prints PASS results for T00 through T08,
and reports completion of the Progress Evaluation 1 implementation stage. T12
verification additionally uses the focused and full unit-test suites, the
executed final-model notebook, artifact round-trip checks, and the evidence
record above.
