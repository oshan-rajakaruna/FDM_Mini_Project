# T01 Dataset Verification Evidence

## Task objective

Verify the actual structure, target availability, date coverage, duplicate state,
and supplied proposal claims for the rainfall dataset without changing the raw
file or performing EDA, preprocessing, feature engineering, or modelling.

## Dataset path

`data/raw/weatherAUS.csv`

The file loaded successfully in read-only use. Its recorded size is 14,094,055
bytes, and its last-modified timestamp remained 25 September 2026 at 7:09:03 PM
during verification.

## Verification items performed

1. Successful CSV load
2. Total rows and columns
3. Exact ordered column names
4. pandas-inferred data types
5. Minimum and maximum valid dates
6. Unique non-missing `Location` count
7. `RainTomorrow` existence, values, class counts, missing count, and labelled count
8. Exact duplicate rows
9. Duplicate `Date` + `Location` combinations and participating rows
10. `RISK_MM` existence
11. Unexpected and missing columns relative to the expected weatherAUS schema
12. Direct comparison of every supplied proposal claim with the actual dataset

## Actual dataset findings

- Shape: 145,460 rows and 23 columns.
- Exact ordered columns: `Date`, `Location`, `MinTemp`, `MaxTemp`, `Rainfall`,
  `Evaporation`, `Sunshine`, `WindGustDir`, `WindGustSpeed`, `WindDir9am`,
  `WindDir3pm`, `WindSpeed9am`, `WindSpeed3pm`, `Humidity9am`, `Humidity3pm`,
  `Pressure9am`, `Pressure3pm`, `Cloud9am`, `Cloud3pm`, `Temp9am`, `Temp3pm`,
  `RainToday`, `RainTomorrow`.
- pandas-inferred string columns: `Date`, `Location`, `WindGustDir`,
  `WindDir9am`, `WindDir3pm`, `RainToday`, and `RainTomorrow` (`str`).
- pandas-inferred numeric columns: all other 16 columns (`float64`).
- Date range: 2007-11-01 through 2017-06-25; 0 invalid or missing dates.
- Unique non-missing Locations: 49.
- `RainTomorrow` exists with non-missing values `No` and `Yes`.
- `RainTomorrow` counts: `No` = 110,316; `Yes` = 31,877; missing = 3,267;
  labelled = 142,193.
- Exact duplicate rows (excluding the first occurrence): 0.
- Duplicate `Date` + `Location` combinations: 0; participating rows: 0.
- `RISK_MM` exists: No.
- Unexpected extra columns: None. Missing expected columns: None.

Detailed machine-readable findings are saved in the T01 tables under
`reports/tables/`.

## Proposal comparison results

All seven supplied proposal claims match the actual dataset:

| Claim | Expected value | Actual dataset value | Match / Mismatch | Comment |
|---|---:|---:|---|---|
| Total rows | 145,460 | 145,460 | Match | All loaded observations. |
| Total columns | 23 | 23 | Match | Complete CSV header width. |
| Unique locations | 49 | 49 | Match | Distinct non-missing values. |
| Labelled RainTomorrow rows | 142,193 | 142,193 | Match | Non-missing target values. |
| Missing RainTomorrow rows | 3,267 | 3,267 | Match | Missing target values. |
| Date range | 2007-11-01 to 2017-06-25 | 2007-11-01 to 2017-06-25 | Match | Inclusive valid-date endpoints. |
| RISK_MM exists | False | False | Match | The column is absent as expected. |

Proposal mismatches: None.

## Files created/modified

Created:

- `notebooks/00_dataset_verification.ipynb`
- `src/fdm_rainfall/data.py`
- `src/fdm_rainfall/validation.py`
- `tests/test_validation.py`
- `reports/evidence/01_dataset_verification.md`
- `reports/tables/01_dataset_summary.csv`
- `reports/tables/01_column_names.csv`
- `reports/tables/01_column_schema.csv`
- `reports/tables/01_target_counts.csv`
- `reports/tables/01_duplicate_summary.csv`
- `reports/tables/01_proposal_verification.csv`

Modified:

- `requirements.txt`
- `.gitignore`
- `README.md`
- `scripts/verify_stage1.py`
- `PROJECT_STATUS.md`

## Checks/tests executed

- `python -m unittest discover -s tests -p "test_*.py" -v`: 4 tests passed.
- `python -m nbconvert --to notebook --execute --inplace notebooks/00_dataset_verification.ipynb --ExecutePreprocessor.timeout=120`: completed successfully using a workspace-local Jupyter runtime; 7 of 7 code cells executed and 0 error outputs were saved.
- `python scripts/verify_stage1.py`: `PASS: T00 Project Setup` and
  `PASS: T01 Dataset Verification`; 8 T00 files, 14 directories, and 12 T01
  artifacts verified.

## Unresolved issues

None identified. The direct `jupyter nbconvert` launcher was unavailable and the
managed sandbox required a workspace-local runtime plus Jupyter's documented
insecure-write fallback; invoking the installed `nbconvert` module completed the
notebook successfully. This is an execution-environment limitation, not a
dataset or notebook error.

## Final status

DONE
