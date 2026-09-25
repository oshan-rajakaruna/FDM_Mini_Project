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
