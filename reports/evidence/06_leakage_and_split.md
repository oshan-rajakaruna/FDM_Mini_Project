# T06 Data Leakage and Chronological Split Strategy Evidence

## Task objective

Identify project-specific leakage risks and implement and verify a defensible
whole-date chronological Train/Validation/Test strategy before any preprocessing,
feature engineering, resampling, or modelling is performed.

## Labelled analysis population

- Raw dataset: 145,460 rows and 23 columns.
- Missing `RainTomorrow`: 3,267 rows.
- Supervised labelled analysis population: 142,193 rows.
- The labelled population exists only as an in-memory view. The raw CSV was not
  overwritten and no split CSV datasets were saved.
- Exact duplicate rows: 0.
- Duplicate `Date + Location` combinations: 0.
- `RISK_MM`: absent.

## Leakage risks identified

The risk register documents target leakage, `RISK_MM` leakage, imputation
leakage, encoding leakage, scaling leakage, feature-selection leakage,
resampling leakage, temporal leakage, future-derived feature leakage, and
test-set reuse/tuning leakage.

`RainTomorrow` must be excluded from the future predictor matrix. `RISK_MM`
would be severe target leakage because next-day rainfall amount would nearly
disclose whether next-day rain occurred. Any future feature must use only
information available on or before the observation date.

## Why chronological splitting was chosen

The raw file is not globally ordered by date: it contains 48 adjacent backward
date transitions because location blocks restart their date sequences. All 49
locations are internally date ordered. Of 3,436 unique dates, 3,344 occur for
multiple locations, with as many as 49 locations on a date.

A random row split could therefore place nearby days from the same station in
different subsets and allow later-period conditions to influence development
choices. Whole-date chronological evaluation more closely represents
prediction on unseen future days. It does not eliminate every form of temporal,
serial, spatial, or distribution dependence.

## Split method

The reusable splitter:

1. Copies the input frame and optionally keeps non-missing target rows in memory.
2. Parses the date column safely and rejects invalid dates.
3. Stable-sorts rows chronologically without changing the input frame.
4. Counts labelled rows over ordered unique dates.
5. Chooses the eligible date nearest 70% cumulative rows for the Train end.
6. Chooses the eligible date nearest 85% cumulative rows for the Validation end.
7. Returns Train, Validation, Test, and boundary metadata while keeping each
   calendar date wholly within one subset.

The realised percentages are allowed to differ slightly from 70/15/15 rather
than splitting a calendar date. No random split was created.

## Exact split boundaries

| Split | First date | Last date | Unique dates | Locations |
|---|---|---|---:|---:|
| Train | 2007-11-01 | 2015-01-12 | 2,541 | 49 |
| Validation | 2015-01-13 | 2016-04-08 | 452 | 48 |
| Test | 2016-04-09 | 2017-06-25 | 443 | 49 |

The validated inequalities are `max(Train Date) < min(Validation Date)` and
`max(Validation Date) < min(Test Date)`. No calendar date overlaps subsets.

## Actual row proportions

| Split | Rows | Percentage of labelled rows |
|---|---:|---:|
| Train | 99,546 | 70.007666% |
| Validation | 21,342 | 15.009178% |
| Test | 21,305 | 14.983157% |

The three row counts sum exactly to 142,193. The proposal's labelled-row claim
matches the dataset; there is no proposal inconsistency. The target proportions
were approximate by design, and the small deviations are the consequence of
retaining whole dates.

## Target distribution by split

| Split | No | Yes | Yes percentage | Missing target |
|---|---:|---:|---:|---:|
| Train | 77,087 | 22,459 | 22.561429% | 0 |
| Validation | 16,990 | 4,352 | 20.391716% | 0 |
| Test | 16,239 | 5,066 | 23.778456% | 0 |

The Validation Yes-rate is lower and the Test Yes-rate is higher than Train.
This is documented as temporal distribution shift; no rebalancing was applied.

## Location coverage findings

- 48 of 49 locations occur in all three subsets.
- Melbourne is absent from Validation but occurs in Train and Test. Its labelled
  observations have a long gap from 2015-01-05 to 2016-04-30.
- No location is absent from Test.
- Canberra is the only location beginning on the overall labelled-population
  start date; the other 48 begin later.
- Nine locations end before the overall labelled-population end date: Adelaide,
  AliceSprings, Darwin, Katherine, MountGambier, Newcastle, Nuriootpa, Uluru,
  and Woomera.
- All locations are retained. Varying station coverage can change the location
  mix and should be considered when interpreting later performance.

## Split validation results

All nine saved validation checks pass:

- all three subsets are non-empty;
- all dates parse successfully;
- source-row indices do not overlap;
- calendar dates do not overlap;
- temporal boundaries are strictly ordered;
- split rows equal the labelled population;
- `RainTomorrow` exists in every subset;
- supervised targets contain no missing values; and
- `RISK_MM` is absent from every subset.

## Limitations

- Chronological splitting does not remove serial or spatial dependence within a
  subset.
- Target prevalence, observation volume, and station coverage change over time.
- Validation lacks labelled Melbourne observations.
- Climate drift and station data gaps may affect future evaluation.
- The split cannot prevent leakage from incorrectly constructed future features
  or from reusing Test during later tuning; those practices require continued
  controls.

## Controls planned for later preprocessing/modelling

The following controls are planned and are **not implemented in T06**:

- fit numerical and categorical imputation rules using Train only;
- fit encoding and scaling using Train only;
- learn feature-selection and data-dependent outlier parameters without using
  Validation or Test outcomes;
- apply any class balancing to Train only after splitting;
- build features only from observation-date-or-earlier information; and
- fit probability thresholds within a training-only development procedure;
  preserve Validation for later development assessment and Test for one
  independent final evaluation.

## Files created/modified

Created:

- `notebooks/05_leakage_and_split_strategy.ipynb`
- `tests/test_splitting.py`
- `docs/decisions/preprocessing_decisions.md`
- `reports/evidence/06_leakage_and_split.md`
- six `06_*.csv` tables under `reports/tables/`
- two figures under `reports/figures/leakage_split/`

Modified:

- `src/fdm_rainfall/data.py`
- `src/fdm_rainfall/validation.py`
- `scripts/verify_stage1.py`
- `.gitignore`
- `README.md`
- `AGENTS.md`
- `PROJECT_STATUS.md`

## Tests/checks executed

- `python -B -m unittest discover -s tests -p "test_*.py" -v`: 40 tests passed.
- `python -B scripts/verify_stage1.py`: T00 through T06 passed; 14 T06
  artifacts verified.
- Notebook execution: 7 of 7 code cells executed with no errors.
- Raw-file SHA-256 before and after analysis:
  `573FD715CD69FCACC4DF32024D823B450AE3EDAAE7E8FF2EEB623ADBED424014`.

## Unresolved issues

- Melbourne's Validation-period absence and other station-coverage differences
  should be considered during later evaluation; no location is removed here.
- Later stages must enforce the planned train-only transformations and protect
  the Test set from iterative tuning.
- No blocking issue remains for T06.

## Final status

**DONE** — leakage risks are documented, the labelled population is verified,
the reusable whole-date chronological split and validation checks pass, the
notebook executes without errors, outputs and decision documentation exist, and
the raw dataset is unchanged.
