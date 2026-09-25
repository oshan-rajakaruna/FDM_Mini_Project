# T08 Feature Engineering Decisions

## Feature-engineering principles

Feature engineering occurs after the whole-date chronological split and before
preprocessing:

`raw labelled data -> chronological split -> feature engineering -> Train-fitted preprocessing -> transform Validation/Test`

Every formula uses only values available on the observation date. The
transformer is deterministic and target-independent. Any descriptive
association with `RainTomorrow` was calculated on the 99,546-row Train subset
only; Validation and Test targets were not used to select features. Original
measurements remain available unless a representation is explicitly replaced.

## Date features

The implemented candidates are Year, Month, Australian Season, Month_sin, and
Month_cos. Australian seasons use Summer = December-February, Autumn =
March-May, Winter = June-August, and Spring = September-November.

The default matrix keeps `Month_sin = sin(2*pi*(Month-1)/12)` and
`Month_cos = cos(2*pi*(Month-1)/12)`. This preserves the closeness of December
and January. Raw Month and Season remain useful reporting labels but are
dropped from the default matrix to avoid three simultaneous representations of
the same annual cycle. The raw Date string is never one-hot encoded or scaled.

## Weather difference features

The default keeps five same-day differences while retaining their source
measurements:

| Feature | Formula | Sign convention | Train range | Train mean, No / Yes |
|---|---|---|---:|---:|
| TempRange | MaxTemp - MinTemp | Non-negative daily thermal range | 0.0 to 31.2 | 11.921 / 7.869 |
| TempChange | Temp3pm - Temp9am | Positive means warmer at 3pm | -12.6 to 23.0 | 5.348 / 2.552 |
| HumidityChange | Humidity3pm - Humidity9am | Positive means more humid at 3pm | -91 to 91 | -19.555 / -9.080 |
| PressureChange | Pressure3pm - Pressure9am | Negative means lower pressure at 3pm | -16.7 to 10.8 | -2.475 / -2.068 |
| WindSpeedChange | WindSpeed3pm - WindSpeed9am | Positive means stronger wind at 3pm | -57 to 78 | 4.710 / 4.515 |

The group differences are descriptive, not causal and not feature importance.
They justify retaining interpretable within-day movement without claiming that
all five will improve every later model.

## Wind cyclical representation

The 16 compass directions are mapped clockwise from N = 0 degrees in 22.5
degree increments, then represented as sine and cosine. Each of WindGustDir,
WindDir9am, and WindDir3pm produces two coordinates and an original-missing
indicator.

Missing direction maps to the neutral pair `(0, 0)`, which is not a valid unit
circle direction, and its indicator is set to one. It is never assigned a real
bearing. The engineered default replaces the 51 wind-direction one-hot columns
with six circular coordinates and three indicators. The original T07 one-hot
configuration remains intact as a baseline alternative for later modelling;
both representations are not duplicated in the same default matrix.

## Missing indicators

T08 adds exactly three wind-direction indicators. The four structural
indicators (`Sunshine_missing`, `Evaporation_missing`, `Cloud9am_missing`, and
`Cloud3pm_missing`) continue to be created exactly once by T07 preprocessing.
They are included in the final inventory because T03 found strong
station-dependent missingness, but the feature engineer does not duplicate
them.

## Rainfall transformation

Train Rainfall skewness is 9.967964; `log1p(Rainfall)` reduces it to 2.033358
and compresses the maximum from 371 mm to 5.918894 on the transformed scale.
The raw and transformed Train 99th percentiles are 38.0 and 3.663562.

Raw Rainfall remains in the default. `Rainfall_log1p` is implemented but marked
OPTIONAL / ALGORITHM-DEPENDENT: it may help scale-sensitive or linear methods,
while tree-based models generally do not need a monotonic duplicate. No model
result was used to make this decision.

## Year caution

Year is known at prediction time and is not direct leakage. It is OPTIONAL,
not default, because it may proxy temporal drift, station coverage, measurement
practice, or longer-term climate variation. Train target groups have nearly
identical mean years (No 2011.470; Yes 2011.395), which supplies no descriptive
reason to force it into the default matrix. Its stability must be evaluated in
future time-aware modelling.

## Month/Season redundancy

Keeping Month, Season, Month_sin, and Month_cos together would repeat annual
seasonality and make the representation unnecessarily model-dependent. The
cyclical pair is the default; Month and Season are reporting-only DROP decisions
for the default matrix. This is a schema decision, not deletion from source
data.

## Climate-zone decision

Status: **DEFERRED / NOT IMPLEMENTED**.

No authoritative, documented mapping from the 49 Locations to climate zones is
incorporated in the project. Inventing groups would introduce unsupported
assumptions. The proposal idea remains recorded for reconsideration only after
a defensible external mapping and provenance are available.

## Retained, optional, dropped, and deferred features

- KEEP: Month_sin, Month_cos; five weather differences; six wind circular
  coordinates; three wind missing indicators; and the four existing structural
  missing indicators.
- OPTIONAL: Year and Rainfall_log1p.
- DROP from the default matrix: Month and Season; both remain available for
  reporting.
- DEFERRED: ClimateZone.

Original numerical weather measurements, Location, and RainToday are retained.
Only the original three wind-direction categories are replaced in the
engineered default; their T07 one-hot alternative remains supported.

## Redundancy and correlation

Train-only Pearson checks show that differences are related to, but not copies
of, their source levels. Examples include TempRange with MinTemp (-0.252) and
MaxTemp (0.477), HumidityChange with Humidity9am (-0.320) and Humidity3pm
(0.496), and PressureChange with Pressure9am (-0.176) and Pressure3pm (0.103).
Rainfall_log1p correlates 0.762 with raw Rainfall, reinforcing its optional
status. Source variables are retained pending model-stage evaluation.

## Preprocessing integration and counts

The existing `RainfallPreprocessor` keeps its original T07 configuration and
adds an explicit engineered configuration. The engineered configuration uses:

- 29 numerical columns: 16 original, two month-cycle, five differences, and
  six wind circular coordinates;
- seven unscaled indicators: four structural and three wind-direction;
- 53 one-hot columns: 50 Location and three RainToday.

The resulting processed schema has 89 unique columns. Both unscaled and scaled
paths use Train-only imputation/encoding/scaling. Validation and Test are
transform-only and contain no missing or infinite processed values.

## Leakage prevention

- `RainTomorrow` is separated before feature engineering and never used in a
  formula.
- `RISK_MM` is rejected and remains absent.
- No tomorrow/future weather value, future station observation, rolling
  aggregate, or future-inclusive statistic is used.
- Date features use only the observation date.
- The transformer learns no target or data-derived parameter.
- T07 imputation, encoding, and optional scaling are fitted on Train only.
- Validation/Test targets are not used for feature decisions.

## Limitations and future model-stage evaluation

Descriptive Train separation does not prove predictive value or causation.
Difference features may still be redundant for some algorithms. Circular wind
and one-hot wind are alternatives that should later be compared inside a
time-aware model-development procedure. Year and Rainfall_log1p remain optional
until that stage. Climate zones need an authoritative source. No feature
selection, balancing, model fitting, tuning, or threshold optimisation was
performed in T08.
