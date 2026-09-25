# T05 Outlier and Suspicious-Value Analysis Evidence

## Task objective

Identify, quantify, visualize, and cautiously classify unusual/extreme values in
the original `data/raw/weatherAUS.csv` dataset while distinguishing statistical
outliers from credible domain errors. No source value is changed or removed.

## Analyses performed

- Percentile, IQR, and skewness summaries for all 16 original numerical predictors
- 1.5-IQR lower/upper fences and below/above-fence counts
- Temperature, humidity, pressure, cloud, rainfall, evaporation, sunshine, and
  wind plausibility reviews
- Exact row-level investigation of all values specifically flagged in T02
- Rainfall zero mass, positive distribution, skewness, and upper-tail review
- Evaporation/wind 99th-percentile station, time, co-weather, and target context
- Detailed Cloud9am/Cloud3pm value-9 location/date/year/month investigation
- Humidity 0%, 100%, and outside-0–100% boundary checks
- Cautious final classification with future handling options only
- Proposal consistency comparison and six visually inspected figures

## IQR findings

The IQR rule is used only as statistical screening. It does not establish invalidity.

- Rainfall: 25,578 flagged (17.9875% of non-missing values), the largest rate.
- Evaporation: 1,995 (2.4132%).
- WindGustSpeed: 3,092 (2.2870%).
- WindSpeed3pm: 2,523 (1.7718%); WindSpeed9am: 1,817 (1.2645%).
- Humidity9am: 1,425 (0.9979%); Humidity3pm: none.
- Pressure9am: 1,191 (0.9134%); Pressure3pm: 919 (0.7046%).
- MaxTemp, Temp9am, Temp3pm, and MinTemp have smaller flagged fractions.
- Sunshine and both cloud fields have no IQR-flagged values, illustrating that
  a domain-suspicious code can exist without being an IQR outlier.

## Skewness findings

- Rainfall skewness is 9.836225 across all non-missing values and 6.387431 among
  positive rainfall values only.
- Of 142,199 non-missing Rainfall values, 91,080 (64.0511%) are zero and 51,119
  are positive.
- The 99th percentile is 37.4 mm, the 99.9th is 102 mm, and the maximum is 371 mm.
- There are 151 records at or above 100 mm and 14 at or above 200 mm.
- The zero mass plus long positive tail naturally causes the symmetric IQR rule
  to flag many rainy days. No transformation is applied in T05.

## Suspicious-value findings

- No value has sufficient evidence to be classified `likely invalid`.
- `Evaporation = 145 mm` is a single Williamtown record on 2016-12-19, far above
  the next-highest measurements and paired with 58.2 mm rainfall. It is
  `suspicious / investigate later` rather than automatically invalid.
- `WindSpeed9am = 130 km/h` is a single Newcastle record on 2017-01-18 with
  missing gust, afternoon-wind, humidity3pm, and pressure confirmation. It is
  `suspicious / investigate later`.
- Rare exact 0% humidity values are within the physical boundary but remain
  `unresolved` because all occur at Woomera and may need station metadata.
- Cloud value 9 is `suspicious / investigate later` because it conflicts with
  the documented 0–8 scale but could be a source-specific code.

## Cloud value 9 investigation

- Cloud9am equals 9 twice: Sydney on 2009-09-23 and Canberra on 2012-05-27.
- Cloud3pm equals 9 once: Woomera on 2012-11-02.
- The three observations occur in 2009/2012 and months 5, 9, and 11 across three
  locations. They are sporadic, not a repeated station/time pattern.
- Value 9 is not IQR-flagged because the broad cloud distributions place it
  inside the calculated fences. It remains outside the documented 0–8 scale.
- No value is replaced with 8 or missing.

## Humidity boundary findings

- Humidity9am: one 0% value, 2,863 values at 100%, and no values below 0 or above 100.
- Humidity3pm: four 0% values, 400 values at 100%, and no values below 0 or above 100.
- All five 0% observations occur at Woomera; the dates span 2013-10-20 to 2015-10-15.
- The proposal's 0–100% range claim matches. Boundary observations are retained.

## Rainfall/evaporation/wind findings

- Rainfall 371 mm occurs once at CoffsHarbour on 2009-11-07, with 93%/81%
  morning/afternoon humidity and `RainTomorrow = Yes`. It is classified as a
  likely valid extreme, not a confirmed error.
- Evaporation's upper 1% begins at 18.4 mm and contains 841 records across 26
  locations and 10 years. The broader upper tail repeats, but the isolated
  145 mm maximum remains suspicious.
- WindGustSpeed 135 km/h occurs three times at NorahHead, Townsville, and Woomera.
  The strongest records include wet/high-humidity context; the maximum is a
  likely valid extreme.
- Wind upper tails repeat widely: the gust upper 1% covers 47 locations and all
  11 represented years; WindSpeed9am covers 42 locations and WindSpeed3pm 45.
  The broader tails appear systematic, while the isolated 130 km/h 9am record
  has insufficient corroboration.
- Temperature endpoints, pressure endpoints, Sunshine 0–14.5 hours, and the
  WindSpeed3pm 87 km/h maximum were not found to violate a documented constraint.

## Proposal consistency result

All six supplied proposal statements match the actual dataset:

- Rainfall is strongly right-skewed with many IQR flags.
- Maximum Rainfall is 371 mm.
- Evaporation and wind contain extreme values.
- Statistical extremes may be genuine events rather than errors.
- Humidity remains within 0–100%.
- Cloud data contain value 9 despite the documented 0–8 scale.

There are no proposal mismatches. The classification remains mixed and cautious:
some extremes have supporting context, while evaporation 145 mm and 9am wind
130 km/h require later investigation.

## Classification of unusual values

- `likely valid extreme`: temperature endpoints, humidity 100%, pressure
  endpoints, Rainfall 371 mm, WindGustSpeed 135 km/h, WindSpeed3pm 87 km/h,
  and Sunshine endpoints.
- `suspicious / investigate later`: Cloud9am/Cloud3pm value 9, Evaporation
  145 mm, and WindSpeed9am 130 km/h.
- `unresolved`: exact 0% humidity values.
- `likely invalid`: none; no credible constraint violation was established with
  enough source information.

## Future preprocessing considerations

- Retain all values until a later task evaluates handling under a leakage-safe split.
- Consider robust scaling for heavy-tailed wind, pressure, and other predictors.
- Consider a rainfall transformation only during later preprocessing/feature engineering.
- Verify source metadata before any cloud-9 recoding or conversion to missing.
- Verify the isolated evaporation and 9am-wind records before considering
  winsorization, capping, or missing-value conversion.
- Feature removal would require separate evidence and is not justified here.

No option was implemented in T05.

## Files created/modified

Created:

- `notebooks/04_outlier_analysis.ipynb`
- `src/fdm_rainfall/outliers.py`
- `tests/test_outliers.py`
- `reports/evidence/05_outliers.md`
- 11 `05_*.csv` analysis tables under `reports/tables/`
- 6 figures under `reports/figures/outliers/`

Modified:

- `.gitignore`
- `README.md`
- `AGENTS.md`
- `PROJECT_STATUS.md`
- `scripts/verify_stage1.py`

## Tests/checks executed

- Full notebook execution: completed successfully; final code cells executed
  without error and produced all 11 tables and 6 figures.
- Visual QA: all six figures inspected. Crowded date labels on the cloud figure
  were corrected to yearly ticks, and the notebook was rerun successfully.
- `python -m unittest discover -s tests -p "test_*.py" -v`: 32 tests passed.
- `python scripts/verify_stage1.py`: passed T00 through T05 and verified all 21
  required T05 artifacts.

## Unresolved questions

- Source/station metadata is needed to interpret cloud code 9 conclusively.
- The isolated Evaporation 145 mm and WindSpeed9am 130 km/h records need source
  verification before any later corrective action.
- Exact 0% humidity readings at Woomera could be rare physical measurements or
  station/sensor artefacts; the dataset alone cannot decide.
- T05 does not test how future models respond to retaining or transforming
  statistical outliers; that belongs to later stages.

These uncertainties do not block completion of the descriptive T05 scope.

## Final status

DONE — the notebook executed successfully, all required analyses and outputs
exist, all 32 tests passed, and the stage verifier passed T05.
