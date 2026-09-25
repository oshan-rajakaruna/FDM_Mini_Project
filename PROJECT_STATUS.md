# Project Status

Allowed statuses: `TODO`, `IN PROGRESS`, `BLOCKED`, `DONE`.

## Definition of DONE

A task may be marked `DONE` only if:

1. Required files exist.
2. Required code executes successfully.
3. Relevant checks/tests pass.
4. Required evidence/output exists.
5. `PROJECT_STATUS.md` contains verification evidence.

## Task tracker

| ID | Task | Status | Verification evidence |
|---|---|---|---|
| T00 | Project Setup | DONE | `python scripts/verify_stage1.py` passed (8 files and 14 directories verified); see `reports/evidence/00_project_setup.md`. |
| T01 | Dataset Verification | DONE | Dataset loaded; all required checks completed; notebook executed without errors; 4 unit tests and `python scripts/verify_stage1.py` passed. See `reports/evidence/01_dataset_verification.md`. |
| T02 | Data Understanding | DONE | Complete 23-column inventory, feature groups, numerical/categorical/date/target/range summaries, and data dictionary created; notebook executed without errors; 10 tests and `python scripts/verify_stage1.py` passed. See `reports/evidence/02_data_understanding.md`. |
| T03 | Missing-Value Analysis | DONE | Missingness notebook executed without errors; 15 tables and 4 figures created and checked; 16 tests and `python scripts/verify_stage1.py` passed (23 T03 artifacts verified). See `reports/evidence/03_missing_values.md`. |
| T04 | Target and Feature Relationship EDA | DONE | Target, temporal, location, numerical, categorical, correlation, and RainToday/Rainfall analyses completed; notebook executed without errors; 12 tables and 6 figures created and checked; 24 tests and `python scripts/verify_stage1.py` passed (22 T04 artifacts verified). See `reports/evidence/04_target_relationships.md`. |
| T05 | Outlier and Suspicious-Value Analysis | DONE | Percentile/IQR screening, domain plausibility, flagged-value context, Cloud 9, humidity boundaries, rainfall skewness, and cautious classifications completed; notebook executed without errors; 11 tables and 6 figures created and checked; 32 tests and `python scripts/verify_stage1.py` passed (21 T05 artifacts verified). See `reports/evidence/05_outliers.md`. |
| T06 | Leakage and Chronological Split Strategy | DONE | Leakage inventory, 142,193-row labelled population, whole-date chronological 70.007666%/15.009178%/14.983157% split, target/location distribution checks, and nine split validations completed; notebook executed without errors; 6 tables and 2 figures created and checked; 40 tests and `python scripts/verify_stage1.py` passed (14 T06 artifacts verified). See `reports/evidence/06_leakage_and_split.md`. |
| T07 | Data Preprocessing | DONE | Train-only structural/global median imputation, explicit categorical missing handling, safe one-hot encoding, configurable scaled/unscaled paths, row/target alignment, and leakage controls completed; 124-feature schema verified with zero remaining predictor missingness; notebook executed without errors; 9 tables and 2 figures created and checked; 51 tests and `python scripts/verify_stage1.py` passed (16 T07 artifacts verified). See `reports/evidence/07_preprocessing.md`. |
| T08 | Feature Engineering | DONE | Deterministic date, weather-difference, and cyclical-wind features integrated before Train-only preprocessing; 34 raw engineered inputs produce 89 finite processed features with rows/targets/dates preserved; 65 tests, executed notebook, raw checksum, and `python scripts/verify_stage1.py` passed (19 T08 artifacts verified). See `reports/evidence/08_feature_engineering.md`. |
