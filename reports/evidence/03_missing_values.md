# T03 Missing-Value Analysis Evidence

## Task objective

Investigate the amount, distribution, location dependence, temporal variation,
co-occurrence, and target implications of missing data in `weatherAUS.csv`
without changing the raw data or making preprocessing decisions.

## Analyses performed

- Missing count, percentage, non-missing count, and descriptive severity for all 23 columns
- Row-level missing-field distribution and a stated very-high threshold of 10 fields
- Location-level coverage for nine important features across all 49 locations
- Complete station-level absence, partial missingness, and good coverage counts
- Year, month-of-year, and Location×Year missingness summaries
- Co-missingness for the required rain, pressure, cloud, sunshine/evaporation,
  and all 15 wind-feature pairs
- `RainTomorrow` missingness by date, year, location, and station endpoint proximity
- Direct `Rainfall`/`RainToday` mask comparison
- Provisional structural, temporal, sporadic, or unclear pattern classification
- Comparison of all supplied proposal counts and station-level absence claims
- Four focused figures, visually inspected for readability

## Key missing-data findings

- 89,040 rows (61.2127%) contain at least one missing value; 56,420 rows
  (38.7873%) are complete across all 23 fields.
- The maximum missing fields in one row is 21. Using the stated ≥10-field
  threshold, 3,117 rows (2.1429%) have very high row-level missingness.
- High descriptive missingness: Sunshine 48.0098%, Evaporation 43.1665%,
  Cloud3pm 40.8071%, and Cloud9am 38.4216%.
- Moderate descriptive missingness: Pressure9am 10.3568%, Pressure3pm 10.3314%,
  WindDir9am 7.2639%, WindGustDir 7.0989%, and WindGustSpeed 7.0555%.
- Date and Location have no missing values; all other columns have some missingness.

Severity bands are descriptive only: 0% = none, >0–<5% = low, 5–<20% =
moderate, and ≥20% = high.

## Structural missingness findings

- Sunshine is completely absent at 19 locations.
- Evaporation is completely absent at 16 locations.
- Cloud9am and Cloud3pm are each completely absent at 12 locations.
- Pressure9am and Pressure3pm are each completely absent at 4 locations.
- WindGustDir and WindGustSpeed are each completely absent at 2 locations.
- WindDir9am has no fully absent station, but station missing percentages range
  from 0.2659% to 46.7588%.

The major features have large between-station spreads. Within-station yearly
spreads of at least 10 percentage points occur at 19 locations for Sunshine, 22
for Evaporation, 27 for Cloud9am, and 30 for Cloud3pm. These observations are
consistent with both station dependence and time variation, but do not establish
a causal missingness mechanism.

## Temporal findings

- Aggregate yearly missingness varies substantially for the four major features:
  Sunshine 0–74.1273%, Evaporation 0–66.7169%, Cloud9am 0–46.7703%, and
  Cloud3pm 0–54.6793% across represented years.
- Location×Year results confirm material within-station changes for multiple
  locations, rather than relying only on changing station composition.
- WindDir9am has 14 locations with a within-station yearly spread of at least 10
  percentage points and is provisionally described as likely temporal.
- Calendar-month summaries are saved, but no seasonal cause is claimed.
- Annual aggregates still combine changing station coverage with time effects;
  therefore all classifications remain provisional.

## Co-missingness findings

- Rainfall and RainToday have identical missingness masks: 3,261 rows are missing
  for both, with no one-sided exceptions.
- Pressure9am/Pressure3pm: 14,804 jointly missing rows and 96.8278% Jaccard overlap.
- Cloud9am/Cloud3pm: 51,744 jointly missing rows and 81.4840% Jaccard overlap.
- Sunshine/Evaporation: 58,547 jointly missing rows and 79.0343% Jaccard overlap.
- WindGustDir/WindGustSpeed: 10,263 jointly missing rows and 99.3899% Jaccard overlap.
- Other wind-pair overlaps vary, so wind missingness is not represented by one
  universal mask.

## Target missingness findings

- RainTomorrow is missing in 3,267 rows (2.2460%); 142,193 rows are labelled.
- Missing-target dates range from 2008-07-05 through 2017-06-25.
- Location concentration is strong: Melbourne has 758 missing targets (23.7394%)
  and Williamtown has 456 (15.1545%), substantially above the overall rate.
- The highest yearly missing-target percentage is 3.6567% in 2015.
- Only 10 missing targets (0.3061%) fall exactly on station endpoints; 78 (2.3875%)
  fall within 30 days of an endpoint versus 2.0885% of all rows. Thus missing
  targets are not predominantly concentrated at station endpoints.
- Missing target rows must later be excluded from supervised-learning data, but
  no rows are removed in T03.

## Proposal comparison

All nine supplied feature-level missing counts match the actual dataset exactly.
The four station-level claims also match: Sunshine, Evaporation, Cloud9am, and
Cloud3pm are each entirely absent at one or more stations. No proposal mismatch
was found. The full 13-row comparison is saved as
`reports/tables/03_proposal_missingness_comparison.csv`.

## Future preprocessing considerations

- Do not assume global mean/mode imputation is suitable for station-dependent fields.
- Later compare station-aware strategies, missing indicators, native missing-value
  handling, and justified feature exclusion after the split strategy is fixed.
- Treat strongly co-missing pairs consistently and avoid redundant indicators
  without evaluation.
- Exclude missing target labels only when supervised-learning datasets are
  constructed in a later preprocessing task.
- Preserve chronology and prevent future information from entering any fitted
  imputation procedure.

No imputation, deletion, encoding, scaling, or feature creation was performed.

## Files created/modified

Created:

- `notebooks/02_eda_missing_values.ipynb`
- `src/fdm_rainfall/missing_values.py`
- `tests/test_missing_values.py`
- `reports/evidence/03_missing_values.md`
- 15 `03_*.csv` analysis tables under `reports/tables/`
- 4 final figures under `reports/figures/missing_values/`

Modified:

- `requirements.txt`
- `.gitignore`
- `README.md`
- `AGENTS.md`
- `PROJECT_STATUS.md`
- `scripts/verify_stage1.py`

## Tests/checks executed

- Full notebook execution: completed successfully; 12 of 12 code cells executed
  with 0 error outputs.
- Visual QA: all four figures inspected; titles, labels, axes, legends, and
  location names are readable without clipping.
- `python -m unittest discover -s tests -p "test_*.py" -v`: 16 tests passed.
- `python scripts/verify_stage1.py`: passed T00 through T03 and verified all 23
  required T03 artifacts.

## Unresolved questions

- The observed masks alone cannot establish MCAR, MAR, or MNAR.
- External station instrumentation/collection metadata would be needed to confirm
  why particular stations lack entire features.
- Exact causes of within-station temporal changes remain unknown.

These are analytical uncertainties, not blockers for completing the descriptive T03 scope.

## Final status

DONE — the notebook executed successfully, all required outputs exist, all 16
tests passed, and the stage verifier passed T03.
