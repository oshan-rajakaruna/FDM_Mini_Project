# Preprocessing Decisions

## Chronological Split and Leakage Prevention

### Decision

Use a whole-date chronological Train/Validation/Test split for the supervised
`RainTomorrow` population. A random row split is rejected because the combined
CSV is grouped by location rather than globally ordered, nearby days from the
same station could enter different subsets, and later-period conditions could
influence development choices. Chronological evaluation more closely represents
prediction on future, unseen dates.

### Analysis population

The raw dataset remains unchanged at 145,460 rows. Split design uses an
in-memory view containing the 142,193 rows with non-missing `RainTomorrow`.
Removing unlabelled rows from this supervised analysis view is not treated as
final preprocessing and no split CSVs are saved.

### Boundary selection

Dates are safely converted in memory and rows are stably sorted by date. Row
counts are accumulated over ordered unique dates. The Train boundary is the
eligible whole-date boundary nearest 70% of labelled rows; the Validation
boundary is the eligible whole-date boundary nearest 85% cumulatively. This
keeps every calendar date in exactly one subset, so exact 70/15/15 proportions
are not forced.

| Split | Date range | Rows | Actual percentage |
|---|---|---:|---:|
| Train | 2007-11-01 to 2015-01-12 | 99,546 | 70.007666% |
| Validation | 2015-01-13 to 2016-04-08 | 21,342 | 15.009178% |
| Test | 2016-04-09 to 2017-06-25 | 21,305 | 14.983157% |

### Leakage controls implemented in T06

- The split is chronological and no calendar date overlaps subsets.
- Source-row indices do not overlap and split rows reconcile to all 142,193
  labelled observations.
- `RainTomorrow` remains available as the supervised target but is identified
  as excluded from future predictors.
- `RISK_MM` is absent; if encountered later it must be rejected because it
  would reveal next-day rainfall amount and cause severe target leakage.
- Exact duplicate rows and duplicate `Date + Location` combinations are both
  zero.
- Reusable validation checks confirm non-empty subsets, valid dates, strict
  boundary ordering, zero missing targets, target retention, and `RISK_MM`
  absence.

### Controls planned for T07 or later

Numerical and categorical imputation rules, encoders, scalers, learned
outlier-treatment parameters, and feature selection must be fitted using Train
only. Any class balancing must be applied only to Train after splitting. Future
engineered features must use observation-date-or-earlier information only.
Probability thresholds must be fitted within a training-only development
procedure. Validation may support later model comparison without fitting
preprocessing to it, and Test must remain an independent final evaluation set.

These are planned controls, not preprocessing or modelling implemented in T06.

### Limitations

- Chronological splitting does not remove serial or spatial dependence within
  each subset.
- Weather and target prevalence can drift over time: observed Yes-rates are
  22.561429% in Train, 20.391716% in Validation, and 23.778456% in Test.
- Station coverage varies. Forty-eight locations occur in all three subsets;
  Melbourne is absent from Validation because its labelled record has a long
  gap, while every location occurs in Test.
- Only Canberra starts at the overall labelled-population start date, and nine
  locations end before its final date. These coverage differences are retained
  rather than corrected.
- Chronological splitting cannot prevent leakage from a future feature that is
  constructed incorrectly; feature availability must be checked again in T08.

## T07 Data Preprocessing Decisions

The decisions below implement the T07 controls without changing the T06 split,
engineering features, balancing classes, selecting predictors from model
performance, or training a model.

### Target handling

`RainTomorrow` is separated from predictors before any preprocessing. The
3,267 rows with missing targets remain in the immutable raw dataset but are not
part of the 142,193-row supervised population. The target is never imputed.
The Train, Validation, and Test target indices remain aligned with their
transformed predictor rows.

### Duplicate handling

No row is removed for duplication because the verified dataset contains zero
exact duplicate rows and zero duplicate `Date + Location` combinations.

### Missing numerical data

The twelve numerical predictors outside the high-structural-missingness group
use global medians fitted on the 99,546 Train rows. Medians were chosen over
means because several weather variables are skewed or contain valid extremes.
Validation and Test values never contribute to these statistics.

### Structural missingness

`Sunshine`, `Evaporation`, `Cloud9am`, and `Cloud3pm` use a two-level rule:

1. fill a missing value with its Location median learned from Train; and
2. use the global Train median when that Location has no observed Train value.

The Train-global fallbacks are 8.4 hours for Sunshine, 4.6 mm for Evaporation,
and 5.0 oktas for both cloud variables. Four binary missing indicators preserve
whether the original measurement was absent. This strategy retains the
variables and all supervised rows while reflecting the strong station-dependent
missingness found in T03.

### Categorical missing data

Missing `Location`, wind-direction, and `RainToday` values are represented by
the explicit category `Missing`. This avoids substituting a modal category that
was not observed. Location is complete in the current data, but reserving the
category makes the preprocessing contract robust to future missing Location
values.

### Categorical encoding

The five original categorical variables use one-hot encoding fitted on Train.
The vocabulary contains Train-observed categories plus the reserved `Missing`
category, and unknown later categories are ignored safely. Validation and Test
contain no observed unknown categories, while automated tests confirm that
injected unseen values transform without failure. Raw Date is not encoded and
wind directions are not converted to cyclical components in T07.

### Outlier handling

All statistically extreme and suspicious observations are retained unchanged.
This includes Rainfall 371 mm, WindGustSpeed 135 km/h, Evaporation 145 mm,
WindSpeed9am 130 km/h, cloud value 9, and the rare 0% humidity readings. T05
found no value with sufficient evidence to classify as invalid. Blanket IQR
deletion, capping, winsorisation, or conversion to missing would risk removing
genuine severe-weather information.

### Scaling strategy

Two reusable paths expose the same 124-column schema:

- an unscaled path for future tree-based algorithms; and
- a scaled path that applies a Train-fitted `StandardScaler` to the 16 imputed
  continuous numerical predictors for future scale-sensitive algorithms.

The four missing indicators and 104 one-hot columns are not scaled. Scaling is
not claimed to be universally required, and no model was trained to select a
path.

### Leakage prevention

- `RainTomorrow`, Date, and `RISK_MM` cannot enter the T07 transformer.
- The API accepts only the 21 declared original predictors.
- Global and Location medians are calculated from Train only.
- Categorical vocabulary and one-hot encoding are fitted from Train only.
- StandardScaler means and scales are fitted from imputed Train predictors only.
- Validation and Test call `transform` without refitting.
- The T06 chronological boundaries and row membership are unchanged.
- No processed split files are persisted; the raw CSV checksum remains
  `573FD715CD69FCACC4DF32024D823B450AE3EDAAE7E8FF2EEB623ADBED424014`.

### RainToday/Rainfall redundancy

Both variables remain predictors. T04 showed that the dataset-observed
`RainToday` convention corresponds to `Rainfall > 1.0 mm`, making the pair
highly redundant, but model-based feature selection is outside T07. Their
relative value remains a later modelling decision.

### Limitations and decisions deferred to T08 or modelling

- Location medians cannot capture changing station practices through time.
- Global fallback is necessary for stations with a feature entirely absent in
  Train; the missing indicators preserve that an imputation occurred.
- Standard scaling does not remove rainfall skewness or guarantee better model
  performance.
- T08 will consider Date-derived variables, cyclical wind representation,
  temperature/humidity/pressure differences, and other engineered predictors.
- Modelling will determine algorithm-specific preprocessing, feature selection,
  class-imbalance treatment, hyperparameters, and probability thresholds
  without using Test for iterative decisions.
