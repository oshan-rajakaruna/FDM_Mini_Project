# T08 Feature Engineering Evidence

## Task objective

Design, implement, justify, and validate reproducible observation-date feature
engineering for next-day rainfall prediction, using the exact T06 chronological
split and the T07 leakage-safe preprocessing architecture. No model, balancing,
tuning, threshold selection, backend, or frontend work was performed.

## Input split sizes

| Split | Date range | Rows |
|---|---|---:|
| Train | 2007-11-01 to 2015-01-12 | 99,546 |
| Validation | 2015-01-13 to 2016-04-08 | 21,342 |
| Test | 2016-04-09 to 2017-06-25 | 21,305 |

The total supervised population remains 142,193 labelled rows. No date or
source-row index crosses a split boundary.

## Features considered

The review covered Year, Month, Australian Season, cyclical month, five
same-day weather differences, circular encodings and missing indicators for all
three wind directions, the four existing T07 structural-missingness indicators,
`Rainfall_log1p`, and the proposal's possible ClimateZone feature. The complete
25-row inventory is saved in `08_engineered_feature_inventory.csv`.

## Features implemented

Twenty T08 candidate columns are reproducibly implemented: five date
candidates, five weather differences, six wind circular coordinates, three wind
missing indicators, and `Rainfall_log1p`. Sixteen are retained in the default
engineered raw schema: Month_sin, Month_cos, five differences, six wind
coordinates, and three wind missing indicators.

The default transformer returns 34 inputs for preprocessing: 18 retained
original predictors plus 16 new T08 features. Raw wind-direction categories are
replaced only in this engineered configuration; the original T07 configuration
remains available.

## Formulas

- `Month_sin = sin(2*pi*(Month-1)/12)`
- `Month_cos = cos(2*pi*(Month-1)/12)`
- `TempRange = MaxTemp - MinTemp`
- `TempChange = Temp3pm - Temp9am`
- `HumidityChange = Humidity3pm - Humidity9am`
- `PressureChange = Pressure3pm - Pressure9am`
- `WindSpeedChange = WindSpeed3pm - WindSpeed9am`
- Wind coordinates use sine/cosine of the documented N=0 degrees clockwise
  16-direction mapping.
- Missing wind directions use `(sin, cos) = (0, 0)` plus an explicit indicator.
- `Rainfall_log1p = log1p(Rainfall)` for non-negative observed rainfall.

Positive change values always mean the 3pm measurement is higher than the 9am
measurement. Negative PressureChange means lower afternoon pressure.

## Train-only descriptive evidence

All target-conditioned evidence uses Train only. The main mean comparisons
(`RainTomorrow` No / Yes) are:

| Feature | No mean | Yes mean |
|---|---:|---:|
| TempRange | 11.921 | 7.869 |
| TempChange | 5.348 | 2.552 |
| HumidityChange | -19.555 | -9.080 |
| PressureChange | -2.475 | -2.068 |
| WindSpeedChange | 4.710 | 4.515 |
| Rainfall_log1p | 0.319 | 1.085 |

The difference ranges are TempRange 0.0–31.2, TempChange -12.6–23.0,
HumidityChange -91–91, PressureChange -16.7–10.8, and WindSpeedChange -57–78.
These are descriptive associations, not causal claims or model importance.

Train Rainfall skewness falls from 9.967964 to 2.033358 after `log1p`; the
maximum changes from 371 mm to 5.918894 on the transformed scale. The raw and
transformed 99th percentiles are 38.0 and 3.663562.

## Retained features

The default keeps Month_sin, Month_cos, TempRange, TempChange, HumidityChange,
PressureChange, WindSpeedChange, six wind sine/cosine coordinates, and three
wind missing indicators. The four structural indicators from T07 remain in the
processed output and are not duplicated. Original numerical measurements,
Location, and RainToday are retained.

## Optional/deferred/rejected features

- OPTIONAL: Year, because it may proxy temporal/station/measurement drift.
- OPTIONAL: Rainfall_log1p, because its value is algorithm-dependent; raw
  Rainfall remains default.
- DROP from default: Month and Season, because they duplicate the retained
  month-cycle representation. They remain available for reporting.
- DEFERRED / NOT IMPLEMENTED: ClimateZone, because no authoritative documented
  mapping is incorporated.

The decision counts across the comprehensive inventory are KEEP 20, OPTIONAL
2, DROP 2, and DEFERRED 1. KEEP includes four T07-origin indicators.

## Redundancy discussion

Train-only correlations confirm the differences are related to, but not exact
copies of, their source levels. TempRange correlates -0.252 with MinTemp and
0.477 with MaxTemp; HumidityChange correlates -0.320 with Humidity9am and 0.496
with Humidity3pm; PressureChange correlates -0.176 with Pressure9am and 0.103
with Pressure3pm. Source values remain pending model-stage evaluation.

Month/Season are excluded from the default to avoid redundant annual
representations. Circular wind replaces direction one-hot in the engineered
default, while original one-hot remains a separate T07 baseline alternative.
Rainfall_log1p correlates 0.762 with Rainfall and remains optional.

## Leakage controls

The 12 saved leakage checks all pass:

- `RainTomorrow` is separated and never used in a predictor formula.
- `RISK_MM` is absent and rejected if supplied.
- raw Date is neither encoded nor scaled; month features use observation date.
- no tomorrow/future measurement, future station row, rolling aggregate, or
  future-inclusive statistic is used.
- the feature transformer learns no target or data-derived parameter.
- preprocessing learns imputation, encoding, and scaling from Train only.
- Validation/Test targets are not used for feature decisions.
- both original and engineered schemas remain explicit and deterministic.

## Integration with preprocessing

`fit_transform_engineered_chronological_splits` implements the required order:
raw labelled split -> deterministic feature engineering -> fit preprocessing on
Train -> transform Validation/Test. The existing original T07 preprocessing
configuration still produces its verified 124-column output. The engineered
configuration supports unscaled and scaled paths with identical 89-column
schemas.

## Processed feature counts

Before T08 there are 21 original non-Date predictors and 124 T07 processed
columns. T08 implements 20 raw candidates and retains 16 new features in the
default. After replacing the three wind-direction categories, 34 raw engineered
inputs enter preprocessing.

The final 89 columns comprise 29 numerical/circular columns, seven indicators
(four T07 structural plus three T08 wind), and 53 one-hot columns (50 Location
plus three RainToday). All names are unique.

## Missingness verification

Before preprocessing, difference missingness is expected when either source is
missing. Counts for Train / Validation / Test are:

| Feature | Train | Validation | Test |
|---|---:|---:|---:|
| TempRange | 565 | 110 | 196 |
| TempChange | 1,198 | 781 | 1,298 |
| HumidityChange | 1,812 | 989 | 1,485 |
| PressureChange | 9,572 | 2,428 | 2,204 |
| WindSpeedChange | 1,563 | 605 | 929 |
| Rainfall_log1p | 1,007 | 188 | 211 |

Wind coordinates contain no NaN because missing direction uses the documented
neutral pair and indicator. After Train-fitted preprocessing, each split has
zero NaN, zero None, and zero infinite numerical values in both unscaled and
scaled paths.

## Row/target integrity

Feature engineering and preprocessing preserve 99,546 / 21,342 / 21,305 rows,
unique source indices, target index/order, date index/order, and exact T06 date
boundaries. No row is added, removed, or duplicated. Input raw and split
DataFrames remain unchanged after transformation.

## Tests/checks executed

- `python -m unittest discover -s tests -v`: 65 tests passed.
- `notebooks/07_feature_engineering.ipynb`: 7/7 code cells executed; zero error
  outputs.
- `python scripts/verify_stage1.py`: T00-T08 passed; 19 T08 artifacts verified.
- Raw SHA-256 check passed:
  `573FD715CD69FCACC4DF32024D823B450AE3EDAAE7E8FF2EEB623ADBED424014`.
- Three generated figures were visually checked for readability and consistency.

## Limitations

Descriptive Train differences do not establish causation or future model
utility. Difference features can remain redundant for some algorithms. Missing
source measurements still require Train-fitted T07 imputation. Year may be
unstable under drift, Rainfall_log1p is algorithm-dependent, and ClimateZone
cannot be justified without an authoritative mapping.

## Future modelling considerations

Later work may compare the engineered circular-wind configuration with the T07
one-hot baseline, assess Year and Rainfall_log1p inside a time-aware development
procedure, and evaluate source-versus-difference redundancy. These are not
implemented here. No model, class balancing, feature selection, tuning, or
probability-threshold optimisation was performed.

## Files created/modified

Created:

- `notebooks/07_feature_engineering.ipynb`
- `src/fdm_rainfall/features.py`
- `tests/test_features.py`
- `docs/decisions/feature_engineering_decisions.md`
- `reports/evidence/08_feature_engineering.md`
- eleven `reports/tables/08_*.csv` tables
- three figures under `reports/figures/feature_engineering/`

Modified:

- `src/fdm_rainfall/preprocessing.py`
- `scripts/verify_stage1.py`
- `.gitignore`
- `README.md`
- `AGENTS.md`
- `PROJECT_STATUS.md`

The raw dataset was not modified.

## Unresolved issues

Year and Rainfall_log1p remain optional pending model-stage evaluation.
ClimateZone remains deferred pending an authoritative mapping. These are
documented future decisions, not blockers for T08.

## Final status

**DONE** — T08 feature engineering is implemented, documented, executed, and
verified without beginning modelling. Progress Evaluation 1 implementation is
complete through T08.
