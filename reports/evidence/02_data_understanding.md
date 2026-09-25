# T02 Data Understanding Evidence

## Task objective

Create a complete, source-grounded understanding of the weatherAUS dataset's
structure, variables, descriptive statistics, temporal coverage, target basics,
and observed ranges before detailed EDA or data preparation.

## What was analysed

- Dataset dimensions, purpose, date range, location count, and target identity
- Complete 23-column inventory with pandas and logical types, completeness, and cardinality
- Eight thematic feature groups covering every column exactly once
- Descriptive statistics for all 16 numerical columns
- Cardinality, values, modes, frequencies, and missing counts for six categorical/target columns
- Calendar-year counts, raw ordering, and location-level date coverage
- Basic `RainTomorrow` classes and counts
- Observed ranges for temperature, humidity, pressure, wind, rainfall, evaporation,
  sunshine, and cloud variables
- A complete 23-row data dictionary grounded in Rattle and Bureau of Meteorology definitions

## Key dataset characteristics

- 145,460 daily records and 23 columns across 49 locations
- Date range: 2007-11-01 through 2017-06-25, spanning 11 represented calendar years
  (9.6484 elapsed years)
- Target: `RainTomorrow`, with classes `No` and `Yes`; 142,193 labelled rows and
  3,267 missing labels
- Numerical variables: 16; categorical/target variables: 6; temporal variable: 1
- The raw file is not globally date-ordered because records are arranged in
  location blocks, but all 49 locations are internally ordered by date
- Locations do not share identical date coverage: seven start/end patterns occur;
  Canberra has 3,436 records from 2007-11-01, while Katherine, Nhil, and Uluru
  begin in 2013 and each has 1,578 records

## Feature-type classification

- Date/time: `Date`
- Categorical nominal: `Location`, `WindGustDir`, `WindDir9am`, `WindDir3pm`
- Categorical binary: `RainToday`
- Target: `RainTomorrow`
- Numerical discrete: `Cloud9am`, `Cloud3pm`
- Numerical continuous: the remaining 14 temperature, rain, evaporation,
  sunshine, wind-speed, humidity, and pressure variables

The thematic groups are Date/Location, Temperature, Rain/Evaporation/Sunshine,
Wind, Humidity, Pressure, Cloud, and Target. Full mappings are saved in
`reports/tables/02_feature_groups.csv`.

## Important basic observations

- The highest basic missing percentages are Sunshine (48.0098%), Evaporation
  (43.1665%), Cloud3pm (40.8071%), and Cloud9am (38.4216%). Their missingness
  patterns and causes are intentionally not analysed in T02.
- The documented cloud scale is 0–8 oktas, while both cloud columns have an
  observed maximum of 9. This is flagged for later interpretation, not labelled invalid.
- Humidity has observed endpoints of 0% and 100%; the 0% observations are retained
  and flagged for later contextual review.
- Large observed maxima retained for later investigation include Rainfall = 371 mm,
  Evaporation = 145 mm, WindGustSpeed = 135 km/h, and WindSpeed9am = 130 km/h.
- Temperature ranges are -8.5 to 33.9 °C for MinTemp and -4.8 to 48.1 °C for
  MaxTemp; no treatment judgment is made.
- Pressure ranges are 980.5–1041.0 hPa at 9am and 977.1–1039.6 hPa at 3pm.

## Items intentionally deferred to later tasks

- Missingness patterns, mechanisms, and treatment: T03/T07
- Target-feature relationships and deeper class-balance interpretation: T04
- Outlier and suspicious-value investigation or treatment: T05
- Leakage review and chronological splitting: T06
- Preprocessing, encoding, scaling, and imputation: T07
- Feature engineering: T08
- All model training and evaluation: outside T02

No rows were removed, no values were imputed, no features were transformed, and
no plots or models were created.

## Files created/modified

Created:

- `notebooks/01_data_understanding.ipynb`
- `docs/data_dictionary.md`
- `src/fdm_rainfall/understanding.py`
- `tests/test_understanding.py`
- `reports/evidence/02_data_understanding.md`
- `reports/tables/02_dataset_overview.csv`
- `reports/tables/02_column_inventory.csv`
- `reports/tables/02_feature_groups.csv`
- `reports/tables/02_numeric_summary.csv`
- `reports/tables/02_categorical_summary.csv`
- `reports/tables/02_categorical_frequencies.csv`
- `reports/tables/02_date_coverage_summary.csv`
- `reports/tables/02_year_counts.csv`
- `reports/tables/02_location_date_coverage.csv`
- `reports/tables/02_target_summary.csv`
- `reports/tables/02_range_checks.csv`

Modified:

- `README.md`
- `AGENTS.md`
- `PROJECT_STATUS.md`
- `scripts/verify_stage1.py`

## Checks/tests executed

- `python -m unittest discover -s tests -p "test_*.py" -v`: 10 tests passed.
- Full execution of `notebooks/01_data_understanding.ipynb`: succeeded during
  artifact generation; 11 code cells executed with 0 error outputs.
- `python scripts/verify_stage1.py`: T00, T01, and T02 all passed; 8 T00 files,
  14 directories, 12 T01 artifacts, and 16 T02 artifacts verified.

## Unresolved issues

No blocking issue. The meaning of cloud value 9, zero-humidity observations, and
the highlighted high maxima require later T05 investigation and are deliberately
not resolved or altered in T02.

## Final status

DONE
