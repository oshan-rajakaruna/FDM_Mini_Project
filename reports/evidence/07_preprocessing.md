# T07 Data Preprocessing Evidence

## Task objective

Implement a reproducible, leakage-safe preprocessing workflow for the original
predictors using the T06 chronological split. Every learned statistic is fitted
on Train only, Validation and Test are transform-only, the raw dataset remains
unchanged, and no feature engineering or model training is performed.

## Input split sizes

The existing T06 splitter was reused without reimplementation or randomisation.

| Split | Date range | Rows |
|---|---|---:|
| Train | 2007-11-01 to 2015-01-12 | 99,546 |
| Validation | 2015-01-13 to 2016-04-08 | 21,342 |
| Test | 2016-04-09 to 2017-06-25 | 21,305 |

The raw dataset contains 145,460 rows. The 142,193 supervised rows have known
`RainTomorrow`; 3,267 missing-target rows are excluded only from the in-memory
supervised population. The target is not imputed.

## Preprocessing decisions

- Separate `RainTomorrow` into y and preserve Date separately for T08.
- Process the 16 original numerical and five original categorical predictors.
- Remove no duplicate rows because exact and `Date + Location` duplicate counts
  are both zero.
- Retain all extreme and suspicious values because T05 identified no
  likely-invalid value.
- Provide unscaled and scaled paths with the same schema.
- Keep both RainToday and Rainfall; redundancy remains a later consideration.

The detailed eight-column viva decision register is saved as
`reports/tables/07_preprocessing_decisions.csv`.

## Numerical missing-value strategy

The twelve non-structural numerical features use global Train medians. This
robust choice retains all rows and avoids sensitivity of means to skew and valid
extremes. Each feature's raw/train missingness, pattern, statistic, indicator
decision, and rationale is recorded in
`reports/tables/07_numeric_imputation_strategy.csv`.

## Structural missingness strategy

For Sunshine, Evaporation, Cloud9am, and Cloud3pm:

1. use the feature's Location median fitted on Train;
2. if that Train Location median is unavailable, use the global Train median;
3. add a binary indicator recording whether the original value was missing.

Train-global fallbacks are Sunshine 8.4, Evaporation 4.6, Cloud9am 5.0, and
Cloud3pm 5.0. Locations with complete Train absence therefore never obtain a
fallback statistic from Validation or Test. The 12 split-feature source counts
are saved in `reports/tables/07_structural_imputation_summary.csv`.

## Categorical strategy

Missing Location, wind-direction, and RainToday observations become the
explicit category `Missing`. This preserves source absence rather than
pretending a mode was observed. Location is currently complete, but the
reserved category makes the transformer robust to future missing Location
values.

## Encoding strategy

One-hot encoding is fitted on Train with `handle_unknown="ignore"`. Each
vocabulary contains Train-observed categories plus the reserved `Missing`
category. Validation and Test contain zero observed unknown-category rows for
all five inputs; automated tests inject unseen values and confirm safe
transformation.

Encoded counts are Location 50, WindGustDir 17, WindDir9am 17, WindDir3pm 17,
and RainToday 3, for 104 one-hot columns. Raw Date is not encoded, target
encoding is not used, and cyclical wind encoding is deferred to T08.

## Outlier decision

No row is deleted, capped, winsorised, or converted to missing because of an
extreme value. Rainfall 371 mm and WindGustSpeed 135 km/h remain plausible
extremes; Evaporation 145 mm, WindSpeed9am 130 km/h, cloud value 9, and 0%
humidity remain unresolved but unproven errors. Statistical outlier status alone
does not justify destructive treatment.

## Scaling strategy

- Unscaled path: imputed numerical values, four missing indicators, and one-hot
  columns remain on their produced scales for future tree-based algorithms.
- Scaled path: `StandardScaler` is fitted on the 16 imputed Train numerical
  columns, then applied unchanged to Validation and Test. Indicators and one-hot
  columns are not scaled.

Both paths contain 124 output columns. Scaling is configurable rather than
claimed to be universally required; no model was trained to choose a path.

## Leakage controls

All 13 saved controls pass:

- RainTomorrow, Date, and `RISK_MM` are excluded from X;
- the transformer accepts only the 21 declared original predictors;
- numerical and Location medians match independent Train calculations;
- categorical vocabulary equals Train categories plus reserved `Missing`;
- StandardScaler means equal the imputed Train means;
- both preprocessors record exactly 99,546 fit rows;
- Validation and Test are transformed without refitting;
- row counts and target indices remain aligned;
- T06 split boundaries are unchanged;
- no processed predictor missingness remains; and
- no T08 feature is created.

`reports/tables/07_leakage_preprocessing_checks.csv` contains the machine-readable
PASS evidence. The API also records a deterministic Train-index fingerprint.

## Before/after missingness results

| Split | Predictor missing cells before | Missing cells after, unscaled | Missing cells after, scaled | Rows preserved |
|---|---:|---:|---:|---:|
| Train | 202,214 | 0 | 0 | 99,546 |
| Validation | 51,352 | 0 | 0 | 21,342 |
| Test | 62,993 | 0 | 0 | 21,305 |

Targets remain aligned by source index in every split.

## Processed feature counts

- Original non-temporal predictors: 21.
- Imputed numerical output columns: 16.
- Structural missingness indicators: 4.
- One-hot encoded columns: 104.
- Total processed output columns: 124.
- Location columns: 50.
- All wind-direction columns: 51.
- RainToday columns: 3 (`Missing`, `No`, and `Yes`).

The expanded encoded columns are preprocessing representations of original
categories, not engineered domain features.

## Tests/checks executed

- Notebook: 6 of 6 code cells executed with zero errors.
- `python -B -m unittest discover -s tests -p "test_*.py" -v`: 51 tests passed.
- `python -B scripts/verify_stage1.py`: T00 through T07 passed; 16 T07
  artifacts verified.
- Raw SHA-256 before and after:
  `573FD715CD69FCACC4DF32024D823B450AE3EDAAE7E8FF2EEB623ADBED424014`.

## Limitations

- Location medians do not model time-varying station practices.
- Global fallback is frequent for stations with complete Train absence, though
  missing indicators preserve the fact of imputation.
- Standard scaling does not correct skewness and is only a future
  algorithm-compatible option.
- Melbourne remains absent from labelled Validation; the Train-fitted Location
  vocabulary still transforms its Test rows safely.
- Observed later categories are known, but injected-unknown tests are still
  required to protect against future data changes.

## Items deferred to T08

Date-derived Year/Month/Season/DayOfYear fields, cyclical wind representation,
temperature/humidity/pressure differences, and other engineered predictors are
deferred to T08. Model-based feature selection, class balancing, algorithm
training, tuning, and probability-threshold selection are deferred to modelling.

## Files created/modified

Created:

- `notebooks/06_preprocessing.ipynb`
- `src/fdm_rainfall/preprocessing.py`
- `tests/test_preprocessing.py`
- `reports/evidence/07_preprocessing.md`
- nine `07_*.csv` tables under `reports/tables/`
- two figures under `reports/figures/preprocessing/`

Modified:

- `docs/decisions/preprocessing_decisions.md`
- `scripts/verify_stage1.py`
- `requirements.txt`
- `.gitignore`
- `README.md`
- `AGENTS.md`
- `PROJECT_STATUS.md`

## Unresolved issues

- The relative value of RainToday versus Rainfall remains a future
  feature-selection question; the documented >1.0 mm dataset convention is
  unchanged from T04.
- Alternative structural imputation or robust scaling may be evaluated later
  without using Test to select a method.
- No blocking issue remains for T07.

## Final status

**DONE** — Train-only preprocessing is implemented and verified for both paths;
rows and target alignment are preserved; processed predictors contain no
missing values or leakage columns; tests, notebook, verifier, evidence, and
decision documentation pass; the raw dataset remains unchanged.
