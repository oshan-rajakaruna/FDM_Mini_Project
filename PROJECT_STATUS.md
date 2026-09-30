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
| T09 | Baseline Model Development | DONE | Exactly four untuned baselines fitted on 99,546 Train rows and evaluated only on 21,342 Validation rows using the 89-column T08 representation; comparison, four figure groups, executed notebook (8/8 code cells, zero errors), 77 tests, T00-T08 verifier, and raw checksum passed. Test was not evaluated. See `reports/evidence/09_baseline_models.md`. |
| T10 | Leakage-Safe Hyperparameter Tuning | DONE | Three whole-date expanding Train-CV folds, fold-local preprocessing, and PR-AUC-only performance ranking evaluated 34 configurations across 102 fits for the four T09 families; neutral candidate order resolves exact PR-AUC ties, and no winner required it. Selected configurations were refitted on complete Train and evaluated once on Validation only. Focused tests (11/11), full suite (88/88), executed notebook (11/11 code cells, zero errors, four inline figures), T00-T08 verifier, T09 baseline-preservation check, Test-isolation review, and raw checksum passed. See `reports/evidence/10_hyperparameter_tuning.md`. |
| T11 | Controlled Feature / Representation Optimization | DONE | Exactly four pre-declared representations were evaluated for all four fixed T10 model families using three whole-date Train-CV folds (48 fits) with fold-local preprocessing and PR-AUC-only selection. Selected representations were refitted on complete Train and evaluated once on Validation; no final model was selected and Test remained untouched. Focused tests (12/12), full suite (100/100), executed notebook (10/10 code cells, zero errors, four inline figures), T00-T08 verifier, T09/T10 preservation checks, and raw checksum passed. See `reports/evidence/11_feature_optimization.md`. |
| T12 | Final Model Selection and Final Holdout Test Evaluation | DONE | Full-precision T11 Validation PR-AUC selected Random Forest with V0 before Test access; the frozen 0.5-threshold pipeline was refitted on 120,888 Train+Validation rows and evaluated once on 21,305 Test rows (PR-AUC 0.729349, ROC-AUC 0.875865). The compressed final bundle and round trip passed; focused tests (22/22), full suite (123/123), executed notebook (8/8 code cells, zero errors, four inline figures), T00-T08 verifier, prior-result preservation, and raw checksum passed. No post-Test change occurred. See `reports/evidence/12_final_model_selection.md`. |
