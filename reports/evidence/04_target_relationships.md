# T04 Target and Feature Relationship EDA Evidence

## Task objective

Describe the `RainTomorrow` class balance and its unadjusted relationships with
the original weather predictors in `data/raw/weatherAUS.csv`, without performing
preprocessing, feature engineering, splitting, outlier treatment, or modelling.

## Analyses performed

- Target counts, percentages, missing labels, imbalance ratio, and descriptive
  majority-class accuracy
- Target rates by month, year, temporary EDA-only Southern Hemisphere season,
  and all 49 locations
- Pairwise-available summaries for all 16 original numerical predictors by target class
- Frequencies and target rates for RainToday, three wind-direction fields, and Location
- Observation/interpretation/future-consideration records for 10 domain relationships
- Pairwise-complete Pearson correlations for all 120 unique numerical predictor pairs
- Explicit RainToday agreement checks that distinguish the proposal wording
  `Rainfall >= 1.0 mm` from the dataset-observed `Rainfall > 1.0 mm` convention
- Six focused figures, all visually inspected for readable titles, axes, units,
  category labels, legends, and layout

## Target distribution findings

- Labelled rows: 142,193; missing targets: 3,267.
- `No`: 110,316 (77.5819% of labelled rows).
- `Yes`: 31,877 (22.4181% of labelled rows).
- The majority/minority ratio is 3.4607 to 1.
- Always describing the majority class would yield 77.5819% accuracy, but no
  DummyClassifier or other model was trained.

## Temporal findings

- Monthly Yes rates range from 19.3329% in January to 26.9208% in July.
- The temporary EDA-only seasonal summary is highest in winter (26.1202%) and
  lowest in summer (20.3030%). Season was not added to the dataset or approved
  as a model feature.
- Yearly rates vary. The 31.1475% value for 2007 is based on only 61 records and
  is not directly comparable with full years; among larger yearly samples, the
  rates still vary without supporting a causal claim.

## Location findings

- Observed Yes rates span 6.7559% to 36.5487% across locations.
- Relatively high observed rates include Portland (36.5487%), Walpole
  (33.6644%), and Cairns (31.7938%). Relatively low observed rates include
  Woomera (6.7559%), Uluru (7.6266%), and AliceSprings (8.0501%). These are
  descriptions of target frequency, not rankings of location quality.
- Uluru (1,521), Katherine (1,559), and Nhil (1,569) have the lowest labelled
  record counts, so their percentages are less stable. Melbourne and
  Williamtown also have reduced labelled counts because of concentrated missing targets.

## Major numerical relationships

- Humidity3pm shows strong separation: median 70% for Yes versus 47% for No.
- Sunshine shows strong separation where recorded: median 4.3 hours for Yes
  versus 9.4 for No, but 48.01% overall missingness limits coverage.
- Cloud9am and Cloud3pm both have medians of 7 oktas for Yes versus 4 for No;
  their 38.42% and 40.81% missingness requires caution.
- Humidity9am has median 80% for Yes versus 67% for No.
- Pressure9am and Pressure3pm are lower for Yes (medians 1014.3 and 1012.2 hPa)
  than No (1018.5 and 1016.0 hPa).
- WindGustSpeed is higher for Yes (median 44 km/h) than No (37 km/h).
- Rainfall has median 0.8 mm for Yes versus 0 mm for No. Its skew and extreme
  values were retained and not treated in T04.

These are descriptive class differences, not causal effects or trained-model importance.

## Major categorical relationships

- RainTomorrow Yes rates are 15.1868% when RainToday is No and 46.4060% when
  RainToday is Yes. The 1,406 labelled rows with missing RainToday have a
  48.0797% Yes rate; this subgroup is retained as a missing-category description.
- Wind-direction Yes rates vary by compass category. For example, WindGustDir
  ranges from 14.8826% for E to 28.5393% for NW, and WindDir9am ranges from
  14.5723% for E to 30.9949% for NNW.
- Compass categories were preserved; no ordinal or one-hot encoding was performed.
- Location differences are summarized separately because there are 49 categories.

## Correlation/redundancy findings

- MaxTemp/Temp3pm: `r = 0.984562`.
- Pressure9am/Pressure3pm: `r = 0.961348`.
- MinTemp/Temp9am: `r = 0.901813`.
- MaxTemp/Temp9am: `r = 0.887020`; Temp9am/Temp3pm: `r = 0.860574`.
- MinTemp/MaxTemp: `r = 0.736267`; MinTemp/Temp3pm: `r = 0.708865`.
- Sunshine/Cloud3pm: `r = -0.704202`, based on only 64,893 pairwise-available
  labelled rows because of substantial missingness.
- Humidity9am/Humidity3pm (`r = 0.667388`) and
  WindSpeed9am/WindSpeed3pm (`r = 0.519971`) show related but non-identical
  morning/afternoon measurements.

No correlated predictor was removed. The results are evidence for later
redundancy and feature-selection discussion only.

## RainToday/Rainfall verification

- Both values are available for 142,199 rows; 140,787 of these also have a
  labelled target. Both fields are jointly missing in 3,261 rows, with no
  one-sided missingness.
- The proposal wording "1 mm or more" means `Rainfall >= 1.0 mm`. Under that
  definition, 140,440 usable pairs agree
  and 1,759 disagree: 98.7630% agreement, which rounds to the proposal's 98.8%.
- Every disagreement occurs at exactly 1.0 mm and has `RainToday = No`.
- A strict `Rainfall > 1 mm` rule agrees with RainToday for all 142,199 usable pairs.
- The proposal's approximate 98.8% agreement figure matches, but its threshold
  definition has a **minor proposal-definition mismatch / boundary clarification**:
  "1 mm or more" includes exactly 1.0 mm, while the observed dataset convention
  is strictly `Rainfall > 1.0 mm`.
- Neither feature was dropped.

## Class-imbalance findings

The Yes class comprises 22.4181% and the No class 77.5819% of labelled rows.
Overall accuracy alone could reward majority-class predictions while hiding poor
Yes detection. Later evaluation should inspect Yes-class precision, recall, F1,
and PR-AUC. T04 applies no weighting, resampling, SMOTE, or threshold tuning.

## Limitations caused by missingness

- All summaries use available non-missing values pairwise; no imputation occurred.
- Numerical summaries report class-specific available and missing counts, and
  correlation pairs report pairwise sample sizes.
- Sunshine, Evaporation, Cloud9am, and Cloud3pm have high, structurally patterned
  missingness from T03. Their relationships describe the observed subset and may
  not generalize uniformly across locations or dates.
- Missing categorical values are reported explicitly where present rather than encoded.

## Future considerations

- Evaluate non-linear forms and interactions only after the chronological split
  and leakage controls are established.
- Later compare Rainfall and RainToday for incremental value rather than removing
  either based only on definitional overlap.
- Consider correlated morning/afternoon variables during later redundancy work,
  without assuming that correlation makes one automatically disposable.
- Compare missingness-aware and station-aware approaches for structurally sparse
  variables during preprocessing; no strategy is approved here.
- Season remains an EDA helper unless a later feature-engineering task evaluates it.

## Files created/modified

Created:

- `notebooks/03_eda_target_relationships.ipynb`
- `src/fdm_rainfall/relationships.py`
- `tests/test_relationships.py`
- `reports/evidence/04_target_relationships.md`
- 12 `04_*.csv` tables under `reports/tables/`
- 3 figures under `reports/figures/target_analysis/`
- 3 figures under `reports/figures/relationships/`

Modified:

- `.gitignore`
- `docs/data_dictionary.md`
- `README.md`
- `AGENTS.md`
- `PROJECT_STATUS.md`
- `src/fdm_rainfall/understanding.py`
- `scripts/verify_stage1.py`

## Checks/tests executed

- Full notebook execution: completed successfully after source correction; final
  execution has no errors and generated all 12 tables and 6 figures.
- Visual QA: all six figures inspected; one overlapping location-chart annotation
  was replaced with a readable legend and the notebook was rerun successfully.
- `python -m unittest discover -s tests -p "test_*.py" -v`: 24 tests passed.
- `python scripts/verify_stage1.py`: passed T00 through T04 and verified all 22
  required T04 artifacts.

## Unresolved questions

- Unadjusted associations cannot separate location, season, and correlated-weather effects.
- High missingness prevents assuming that Sunshine, Evaporation, and cloud results
  represent every station equally.
- The stability of class rates across future time periods remains untested because
  chronological splitting belongs to T06.
- Extreme-value validity remains unresolved and belongs to T05.

These limitations do not block completion of the requested descriptive T04 scope.

## Final status

DONE — the notebook executed successfully, all required analyses and outputs
exist, all 24 tests passed, and the stage verifier passed T04.
