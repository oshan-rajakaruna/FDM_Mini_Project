"""Deterministic, leakage-safe weather feature engineering for T08."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin


DATE_COLUMN = "Date"
TARGET_COLUMN = "RainTomorrow"

RAW_NUMERICAL_PREDICTORS = (
    "MinTemp",
    "MaxTemp",
    "Rainfall",
    "Evaporation",
    "Sunshine",
    "WindGustSpeed",
    "WindSpeed9am",
    "WindSpeed3pm",
    "Humidity9am",
    "Humidity3pm",
    "Pressure9am",
    "Pressure3pm",
    "Cloud9am",
    "Cloud3pm",
    "Temp9am",
    "Temp3pm",
)

WIND_DIRECTION_COLUMNS = ("WindGustDir", "WindDir9am", "WindDir3pm")
RAW_CATEGORICAL_PREDICTORS = (
    "Location",
    *WIND_DIRECTION_COLUMNS,
    "RainToday",
)
RAW_PREDICTOR_COLUMNS = RAW_NUMERICAL_PREDICTORS + RAW_CATEGORICAL_PREDICTORS

COMPASS_DEGREES = {
    "N": 0.0,
    "NNE": 22.5,
    "NE": 45.0,
    "ENE": 67.5,
    "E": 90.0,
    "ESE": 112.5,
    "SE": 135.0,
    "SSE": 157.5,
    "S": 180.0,
    "SSW": 202.5,
    "SW": 225.0,
    "WSW": 247.5,
    "W": 270.0,
    "WNW": 292.5,
    "NW": 315.0,
    "NNW": 337.5,
}

AUSTRALIAN_SEASONS = {
    1: "Summer",
    2: "Summer",
    3: "Autumn",
    4: "Autumn",
    5: "Autumn",
    6: "Winter",
    7: "Winter",
    8: "Winter",
    9: "Spring",
    10: "Spring",
    11: "Spring",
    12: "Summer",
}

DATE_CANDIDATE_FEATURES = ("Year", "Month", "Season", "Month_sin", "Month_cos")
DIFFERENCE_FEATURES = (
    "TempRange",
    "TempChange",
    "HumidityChange",
    "PressureChange",
    "WindSpeedChange",
)
WIND_CYCLICAL_FEATURES = tuple(
    name for source in WIND_DIRECTION_COLUMNS for name in (f"{source}_sin", f"{source}_cos")
)
WIND_MISSING_INDICATORS = tuple(f"{source}_missing" for source in WIND_DIRECTION_COLUMNS)
OPTIONAL_FEATURES = ("Year", "Rainfall_log1p")
REPORTING_ONLY_FEATURES = ("Month", "Season")

# The default deliberately replaces raw wind-direction categories and omits
# redundant/algorithm-dependent date and rainfall candidates.
DEFAULT_ENGINEERED_PREDICTORS = (
    *RAW_NUMERICAL_PREDICTORS,
    "Location",
    "RainToday",
    "Month_sin",
    "Month_cos",
    *DIFFERENCE_FEATURES,
    *WIND_CYCLICAL_FEATURES,
    *WIND_MISSING_INDICATORS,
)

ALL_CANDIDATE_FEATURES = (
    *RAW_PREDICTOR_COLUMNS,
    *DATE_CANDIDATE_FEATURES,
    *DIFFERENCE_FEATURES,
    *WIND_CYCLICAL_FEATURES,
    *WIND_MISSING_INDICATORS,
    "Rainfall_log1p",
)


def australian_season(month: pd.Series) -> pd.Series:
    """Map month numbers to Australian meteorological seasons."""

    mapped = month.map(AUSTRALIAN_SEASONS)
    if mapped.isna().any():
        raise ValueError("Month values must be integers from 1 through 12")
    return mapped.astype(str)


def cyclical_month(month: pd.Series) -> tuple[pd.Series, pd.Series]:
    """Encode month on a circle with January at zero radians."""

    if not month.dropna().between(1, 12).all():
        raise ValueError("Month values must be between 1 and 12")
    angle = 2.0 * np.pi * (month.astype(float) - 1.0) / 12.0
    return np.sin(angle), np.cos(angle)


def cyclical_wind_direction(direction: pd.Series) -> tuple[pd.Series, pd.Series, pd.Series]:
    """Return sine, cosine and original-missing flag for compass directions.

    Missing directions receive the neutral coordinate (0, 0), which is not a
    real point on the unit circle, plus a missing flag of one. This avoids
    silently treating missing direction as a valid compass bearing.
    """

    observed = direction.dropna().astype(str)
    invalid = sorted(set(observed).difference(COMPASS_DEGREES))
    if invalid:
        raise ValueError(f"Unknown wind directions: {', '.join(invalid)}")

    degrees = direction.map(COMPASS_DEGREES)
    radians = np.deg2rad(degrees.astype(float))
    missing = direction.isna()
    sine = pd.Series(np.sin(radians), index=direction.index).mask(missing, 0.0)
    cosine = pd.Series(np.cos(radians), index=direction.index).mask(missing, 0.0)
    return sine.astype(float), cosine.astype(float), missing.astype(float)


class WeatherFeatureEngineer(BaseEstimator, TransformerMixin):
    """Create deterministic observation-date features without learning targets.

    Parameters
    ----------
    output:
        ``"default"`` returns the modelling default described in the T08
        decision record. ``"candidates"`` returns all original predictors and
        all implemented candidates for descriptive assessment.
    """

    def __init__(self, output: str = "default") -> None:
        self.output = output

    def _validate(self, frame: pd.DataFrame) -> None:
        if self.output not in {"default", "candidates"}:
            raise ValueError("output must be 'default' or 'candidates'")
        required = {DATE_COLUMN, *RAW_PREDICTOR_COLUMNS}
        missing = sorted(required.difference(frame.columns))
        if missing:
            raise ValueError(f"Required feature-engineering columns are missing: {', '.join(missing)}")
        if "RISK_MM" in frame.columns:
            raise ValueError("RISK_MM must never enter feature engineering")
        allowed = required | {TARGET_COLUMN}
        unexpected = sorted(set(frame.columns).difference(allowed))
        if unexpected:
            raise ValueError(
                "Unexpected or future columns must be removed before feature engineering: "
                + ", ".join(unexpected)
            )

    def fit(self, X: pd.DataFrame, y: object = None) -> "WeatherFeatureEngineer":
        """Validate schema; no data- or target-derived parameters are learned."""

        self._validate(X)
        self.feature_names_out_ = list(
            DEFAULT_ENGINEERED_PREDICTORS if self.output == "default" else ALL_CANDIDATE_FEATURES
        )
        self.is_fitted_ = True
        return self

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Derive features while preserving row count, index, and input data."""

        if not getattr(self, "is_fitted_", False):
            raise RuntimeError("WeatherFeatureEngineer must be fitted before transformation")
        self._validate(X)
        source = X.loc[:, [DATE_COLUMN, *RAW_PREDICTOR_COLUMNS]].copy(deep=True)
        dates = pd.to_datetime(source[DATE_COLUMN], format="%Y-%m-%d", errors="coerce")
        if dates.isna().any():
            raise ValueError("Date contains invalid or missing YYYY-MM-DD values")

        engineered = source.loc[:, RAW_PREDICTOR_COLUMNS].copy(deep=True)
        engineered["Year"] = dates.dt.year.astype(float)
        engineered["Month"] = dates.dt.month.astype(float)
        engineered["Season"] = australian_season(dates.dt.month)
        engineered["Month_sin"], engineered["Month_cos"] = cyclical_month(dates.dt.month)

        engineered["TempRange"] = source["MaxTemp"] - source["MinTemp"]
        engineered["TempChange"] = source["Temp3pm"] - source["Temp9am"]
        engineered["HumidityChange"] = source["Humidity3pm"] - source["Humidity9am"]
        engineered["PressureChange"] = source["Pressure3pm"] - source["Pressure9am"]
        engineered["WindSpeedChange"] = source["WindSpeed3pm"] - source["WindSpeed9am"]

        for wind_feature in WIND_DIRECTION_COLUMNS:
            sine, cosine, missing = cyclical_wind_direction(source[wind_feature])
            engineered[f"{wind_feature}_sin"] = sine
            engineered[f"{wind_feature}_cos"] = cosine
            engineered[f"{wind_feature}_missing"] = missing

        observed_rainfall = source["Rainfall"].dropna()
        if (observed_rainfall < 0).any():
            raise ValueError("Rainfall_log1p requires non-negative observed Rainfall")
        engineered["Rainfall_log1p"] = np.log1p(source["Rainfall"])

        output_columns = (
            DEFAULT_ENGINEERED_PREDICTORS if self.output == "default" else ALL_CANDIDATE_FEATURES
        )
        transformed = engineered.loc[:, output_columns].copy(deep=True)
        if len(transformed) != len(X) or not transformed.index.equals(X.index):
            raise RuntimeError("Feature engineering changed row count or index")
        return transformed

    def fit_transform(self, X: pd.DataFrame, y: object = None, **fit_params: object) -> pd.DataFrame:
        """Fit the schema-only transformer and return deterministic features."""

        return self.fit(X, y).transform(X)

    def get_feature_names_out(self, input_features: Iterable[str] | None = None) -> np.ndarray:
        """Return output feature names in deterministic order."""

        if not getattr(self, "is_fitted_", False):
            raise RuntimeError("WeatherFeatureEngineer must be fitted before requesting names")
        return np.asarray(self.feature_names_out_, dtype=object)


def compass_mapping_table() -> pd.DataFrame:
    """Return the documented compass-to-angle and circular-coordinate mapping."""

    rows = []
    for direction, degrees in COMPASS_DEGREES.items():
        radians = np.deg2rad(degrees)
        rows.append(
            {
                "Direction": direction,
                "Degrees": degrees,
                "Radians": radians,
                "Sine": np.sin(radians),
                "Cosine": np.cos(radians),
            }
        )
    return pd.DataFrame(rows)


def engineered_missingness(frame: pd.DataFrame) -> pd.DataFrame:
    """Summarise missingness in implemented candidates before preprocessing."""

    engineer = WeatherFeatureEngineer(output="candidates")
    candidates = engineer.fit_transform(frame)
    created = [
        *DATE_CANDIDATE_FEATURES,
        *DIFFERENCE_FEATURES,
        *WIND_CYCLICAL_FEATURES,
        *WIND_MISSING_INDICATORS,
        "Rainfall_log1p",
    ]
    return pd.DataFrame(
        {
            "Feature": created,
            "Missing count": [int(candidates[name].isna().sum()) for name in created],
            "Missing percentage": [float(candidates[name].isna().mean() * 100) for name in created],
        }
    )
