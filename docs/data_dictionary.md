# weatherAUS Data Dictionary

This dictionary describes the 23 columns in `data/raw/weatherAUS.csv`.
Observed data types and quality notes come from the local project file; feature
definitions and units are grounded in the Rattle weatherAUS documentation and
Australian Bureau of Meteorology Daily Weather Observations documentation.

| Feature name | Description | Data type | Logical type | Unit / category meaning | Role | Basic data-quality note | Possible preprocessing consideration |
|---|---|---|---|---|---|---|---|
| Date | Calendar date of the daily weather observation. | str | date/time | YYYY-MM-DD | temporal | 0 missing (0.0000%); 3,436 unique non-null values. | Parse safely as datetime; preserve chronology for a later split strategy. |
| Location | Common name of the Australian weather-station location. | str | categorical nominal | Australian weather-station location name | location | 0 missing (0.0000%); 49 unique non-null values. | Treat as nominal; encoding and location-aware validation decisions are deferred. |
| MinTemp | Minimum temperature recorded for the day. | float64 | numerical continuous | degrees Celsius (°C) | predictor | 1,485 missing (1.0209%); 389 unique non-null values. | Retain numeric values; missing-value and scaling decisions are deferred. |
| MaxTemp | Maximum temperature recorded for the day. | float64 | numerical continuous | degrees Celsius (°C) | predictor | 1,261 missing (0.8669%); 505 unique non-null values. | Retain numeric values; missing-value and scaling decisions are deferred. |
| Rainfall | Rainfall recorded for the day. | float64 | numerical continuous | millimetres (mm) | predictor | 3,261 missing (2.2419%); 681 unique non-null values. | Retain numeric values; missing-value and scaling decisions are deferred. |
| Evaporation | Class A pan evaporation in the 24 hours to 9am. | float64 | numerical continuous | millimetres (mm), Class A pan evaporation | predictor | 62,790 missing (43.1665%); 358 unique non-null values. | Retain numeric values; missing-value and scaling decisions are deferred. |
| Sunshine | Duration of bright sunshine during the day. | float64 | numerical continuous | hours | predictor | 69,835 missing (48.0098%); 145 unique non-null values. | Retain numeric values; missing-value and scaling decisions are deferred. |
| WindGustDir | Direction of the strongest wind gust in the 24 hours to midnight. | str | categorical nominal | compass direction category | predictor | 10,326 missing (7.0989%); 16 unique non-null values. | Preserve categories; missing-value handling and encoding are deferred. |
| WindGustSpeed | Speed of the strongest wind gust in the 24 hours to midnight. | float64 | numerical continuous | kilometres per hour (km/h) | predictor | 10,263 missing (7.0555%); 67 unique non-null values. | Retain numeric values; missing-value and scaling decisions are deferred. |
| WindDir9am | Wind direction at the 9am observation. | str | categorical nominal | compass direction category | predictor | 10,566 missing (7.2639%); 16 unique non-null values. | Preserve categories; missing-value handling and encoding are deferred. |
| WindDir3pm | Wind direction at the 3pm observation. | str | categorical nominal | compass direction category | predictor | 4,228 missing (2.9066%); 16 unique non-null values. | Preserve categories; missing-value handling and encoding are deferred. |
| WindSpeed9am | Wind speed averaged over the 10 minutes before 9am. | float64 | numerical continuous | kilometres per hour (km/h) | predictor | 1,767 missing (1.2148%); 43 unique non-null values. | Retain numeric values; missing-value and scaling decisions are deferred. |
| WindSpeed3pm | Wind speed averaged over the 10 minutes before 3pm. | float64 | numerical continuous | kilometres per hour (km/h) | predictor | 3,062 missing (2.1050%); 44 unique non-null values. | Retain numeric values; missing-value and scaling decisions are deferred. |
| Humidity9am | Relative humidity at 9am. | float64 | numerical continuous | percent (%) | predictor | 2,654 missing (1.8246%); 101 unique non-null values. | Retain numeric values; missing-value and scaling decisions are deferred. |
| Humidity3pm | Relative humidity at 3pm. | float64 | numerical continuous | percent (%) | predictor | 4,507 missing (3.0984%); 101 unique non-null values. | Retain numeric values; missing-value and scaling decisions are deferred. |
| Pressure9am | Atmospheric pressure reduced to mean sea level at 9am. | float64 | numerical continuous | hectopascals (hPa), mean-sea-level pressure | predictor | 15,065 missing (10.3568%); 546 unique non-null values. | Retain numeric values; missing-value and scaling decisions are deferred. |
| Pressure3pm | Atmospheric pressure reduced to mean sea level at 3pm. | float64 | numerical continuous | hectopascals (hPa), mean-sea-level pressure | predictor | 15,028 missing (10.3314%); 549 unique non-null values. | Retain numeric values; missing-value and scaling decisions are deferred. |
| Cloud9am | Fraction of the sky obscured by cloud at 9am. | float64 | numerical discrete | oktas (eighths of sky covered; documented scale 0–8) | predictor | 55,888 missing (38.4216%); 10 unique non-null values. Observed maximum is 9, above the documented 0–8 scale; meaning is deferred. | Retain numeric values; missing-value and scaling decisions are deferred. |
| Cloud3pm | Fraction of the sky obscured by cloud at 3pm. | float64 | numerical discrete | oktas (eighths of sky covered; documented scale 0–8) | predictor | 59,358 missing (40.8071%); 10 unique non-null values. Observed maximum is 9, above the documented 0–8 scale; meaning is deferred. | Retain numeric values; missing-value and scaling decisions are deferred. |
| Temp9am | Temperature at 9am. | float64 | numerical continuous | degrees Celsius (°C) | predictor | 1,767 missing (1.2148%); 441 unique non-null values. | Retain numeric values; missing-value and scaling decisions are deferred. |
| Temp3pm | Temperature at 3pm. | float64 | numerical continuous | degrees Celsius (°C) | predictor | 3,609 missing (2.4811%); 502 unique non-null values. | Retain numeric values; missing-value and scaling decisions are deferred. |
| RainToday | Binary indicator of whether the source definition's daily rainfall threshold was exceeded. | str | categorical binary | No/Yes category | predictor | 3,261 missing (2.2419%); 2 unique non-null values. | Preserve categories; missing-value handling and encoding are deferred. |
| RainTomorrow | Target indicating whether rain was recorded on the following day. | str | target | No/Yes category | target | 3,267 missing (2.2460%); 2 unique non-null values. | Keep as the target; handling of missing labels is deferred to preprocessing. |

## Interpretation notes

- Missingness is recorded descriptively only; analysis and treatment belong to T03/T07.
- Observed extremes are retained. Any outlier or suspicious-value decisions belong to T05.
- The source documentation describes cloud cover on a 0–8 okta scale; the local
  file contains a maximum value of 9 in both cloud columns, which is flagged for
  later investigation rather than labelled invalid here.
- `RISK_MM` is absent from this project dataset, as verified in T01.

## Definition sources

- Rattle `weatherAUS` documentation: https://search.r-project.org/CRAN/refmans/rattle/html/weatherAUS.html
- Australian Bureau of Meteorology Daily Weather Observations: https://www.bom.gov.au/climate/dwo/
