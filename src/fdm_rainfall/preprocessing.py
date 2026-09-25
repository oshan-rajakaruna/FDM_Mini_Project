"""Leakage-safe preprocessing fitted only on chronological training data."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib

import numpy as np
import pandas as pd
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from fdm_rainfall.data import ChronologicalSplit


NUMERICAL_PREDICTORS = (
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

CATEGORICAL_PREDICTORS = (
    "Location",
    "WindGustDir",
    "WindDir9am",
    "WindDir3pm",
    "RainToday",
)

STRUCTURAL_NUMERICAL_PREDICTORS = (
    "Sunshine",
    "Evaporation",
    "Cloud9am",
    "Cloud3pm",
)

DATE_COLUMN = "Date"
TARGET_COLUMN = "RainTomorrow"
MISSING_CATEGORY = "Missing"


@dataclass(frozen=True)
class SupervisedComponents:
    """Predictors, target, and dates retained as separate aligned objects."""

    X: pd.DataFrame
    y: pd.Series
    dates: pd.Series


@dataclass(frozen=True)
class PreprocessedSplits:
    """Transformed chronological subsets and their aligned target/date data."""

    preprocessor: "RainfallPreprocessor"
    X_train: pd.DataFrame
    X_validation: pd.DataFrame
    X_test: pd.DataFrame
    y_train: pd.Series
    y_validation: pd.Series
    y_test: pd.Series
    dates_train: pd.Series
    dates_validation: pd.Series
    dates_test: pd.Series


def predictor_columns() -> tuple[str, ...]:
    """Return the 21 original non-temporal predictor names grouped by role."""

    return NUMERICAL_PREDICTORS + CATEGORICAL_PREDICTORS


def separate_supervised_components(frame: pd.DataFrame) -> SupervisedComponents:
    """Separate X, y, and Date without mutating or engineering the input data."""

    required = set(predictor_columns()) | {DATE_COLUMN, TARGET_COLUMN}
    missing = sorted(required.difference(frame.columns))
    if missing:
        raise ValueError(f"Required supervised columns are missing: {', '.join(missing)}")
    if "RISK_MM" in frame.columns:
        raise ValueError("RISK_MM must not enter supervised preprocessing")
    if frame[TARGET_COLUMN].isna().any():
        raise ValueError("Supervised components require non-missing RainTomorrow labels")

    return SupervisedComponents(
        X=frame.loc[:, predictor_columns()].copy(deep=True),
        y=frame[TARGET_COLUMN].copy(deep=True),
        dates=frame[DATE_COLUMN].copy(deep=True),
    )


def _index_fingerprint(index: pd.Index) -> str:
    """Return a deterministic record of which source rows fitted the transformer."""

    hashed = pd.util.hash_pandas_object(index, index=False).to_numpy().tobytes()
    return hashlib.sha256(hashed).hexdigest()


class RainfallPreprocessor:
    """Train-fitted imputation, one-hot encoding, and optional scaling.

    Structural numerical features use training-location medians with a global
    training median fallback and receive missingness indicators. Other numeric
    features use global training medians. Categorical missing values become an
    explicit ``Missing`` category before one-hot encoding. Unknown categories
    are ignored safely. When requested, only the 16 imputed continuous numeric
    columns are standardised; binary indicators and one-hot columns remain
    unchanged.
    """

    def __init__(self, scale_numeric: bool = False) -> None:
        self.scale_numeric = bool(scale_numeric)
        self.is_fitted_ = False

    def _validate_predictors(self, frame: pd.DataFrame) -> None:
        missing = sorted(set(predictor_columns()).difference(frame.columns))
        if missing:
            raise ValueError(f"Required predictor columns are missing: {', '.join(missing)}")
        unexpected = sorted(set(frame.columns).difference(predictor_columns()))
        if unexpected:
            raise ValueError(
                "Only original T07 predictors may enter preprocessing; separate or reject: "
                + ", ".join(unexpected)
            )

    def fit(self, X_train: pd.DataFrame) -> "RainfallPreprocessor":
        """Fit every learned parameter from training predictors only."""

        self._validate_predictors(X_train)
        train = X_train.loc[:, predictor_columns()].copy(deep=True)
        self.fit_row_count_ = int(len(train))
        self.fit_index_fingerprint_ = _index_fingerprint(train.index)

        self.numeric_medians_ = train.loc[:, NUMERICAL_PREDICTORS].median()
        if self.numeric_medians_.isna().any():
            affected = self.numeric_medians_.index[self.numeric_medians_.isna()].tolist()
            raise ValueError(f"Training data has no observed values for: {', '.join(affected)}")

        self.structural_location_medians_: dict[str, pd.Series] = {}
        for feature in STRUCTURAL_NUMERICAL_PREDICTORS:
            self.structural_location_medians_[feature] = train.groupby(
                "Location", dropna=False
            )[feature].median()

        categorical_train = self._prepare_categorical(train)
        self.categorical_categories_ = [
            np.asarray(sorted(set(categorical_train[feature]) | {MISSING_CATEGORY}), dtype=object)
            for feature in CATEGORICAL_PREDICTORS
        ]
        self.encoder_ = OneHotEncoder(
            categories=self.categorical_categories_,
            handle_unknown="ignore",
            sparse_output=False,
            dtype=np.float64,
        )
        self.encoder_.fit(categorical_train.loc[:, CATEGORICAL_PREDICTORS])

        imputed_numeric, _ = self._impute_numeric(train)
        self.scaler_ = StandardScaler() if self.scale_numeric else None
        if self.scaler_ is not None:
            self.scaler_.fit(imputed_numeric.loc[:, NUMERICAL_PREDICTORS])

        self.numeric_feature_names_ = list(NUMERICAL_PREDICTORS)
        self.indicator_feature_names_ = [
            f"{feature}_missing" for feature in STRUCTURAL_NUMERICAL_PREDICTORS
        ]
        self.encoded_feature_names_ = list(
            self.encoder_.get_feature_names_out(CATEGORICAL_PREDICTORS)
        )
        self.feature_names_out_ = (
            self.numeric_feature_names_
            + self.indicator_feature_names_
            + self.encoded_feature_names_
        )
        self.is_fitted_ = True
        return self

    def _check_fitted(self) -> None:
        if not self.is_fitted_:
            raise RuntimeError("RainfallPreprocessor must be fitted before transformation")

    @staticmethod
    def _prepare_categorical(frame: pd.DataFrame) -> pd.DataFrame:
        categorical = frame.loc[:, CATEGORICAL_PREDICTORS].copy(deep=True)
        return categorical.fillna(MISSING_CATEGORY).astype(str)

    def _impute_numeric(self, frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        numeric = frame.loc[:, NUMERICAL_PREDICTORS].copy(deep=True)
        indicators = pd.DataFrame(index=frame.index)

        for feature in STRUCTURAL_NUMERICAL_PREDICTORS:
            missing_mask = numeric[feature].isna()
            indicators[f"{feature}_missing"] = missing_mask.astype(np.float64)
            location_fill = frame["Location"].map(self.structural_location_medians_[feature])
            numeric[feature] = numeric[feature].fillna(location_fill)
            numeric[feature] = numeric[feature].fillna(self.numeric_medians_[feature])

        non_structural = [
            feature
            for feature in NUMERICAL_PREDICTORS
            if feature not in STRUCTURAL_NUMERICAL_PREDICTORS
        ]
        numeric.loc[:, non_structural] = numeric.loc[:, non_structural].fillna(
            self.numeric_medians_.loc[non_structural]
        )
        return numeric, indicators

    def impute_numeric(self, X: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Return imputed numerics and structural missing indicators."""

        self._check_fitted()
        self._validate_predictors(X)
        return self._impute_numeric(X.loc[:, predictor_columns()].copy(deep=True))

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transform predictors using only parameters learned during ``fit``."""

        self._check_fitted()
        self._validate_predictors(X)
        source = X.loc[:, predictor_columns()].copy(deep=True)
        numeric, indicators = self._impute_numeric(source)

        if self.scaler_ is not None:
            numeric_values = self.scaler_.transform(numeric.loc[:, NUMERICAL_PREDICTORS])
            numeric = pd.DataFrame(
                numeric_values,
                index=source.index,
                columns=NUMERICAL_PREDICTORS,
            )

        categorical = self._prepare_categorical(source)
        encoded_values = self.encoder_.transform(categorical.loc[:, CATEGORICAL_PREDICTORS])
        encoded = pd.DataFrame(
            encoded_values,
            index=source.index,
            columns=self.encoded_feature_names_,
        )
        transformed = pd.concat([numeric, indicators, encoded], axis=1)
        transformed = transformed.loc[:, self.feature_names_out_]
        if transformed.isna().any().any():
            raise ValueError("Preprocessing left unexpected missing predictor values")
        return transformed

    def fit_transform(self, X_train: pd.DataFrame) -> pd.DataFrame:
        """Fit on and transform the training predictors."""

        return self.fit(X_train).transform(X_train)

    def get_feature_names_out(self) -> np.ndarray:
        """Return deterministic processed feature names."""

        self._check_fitted()
        return np.asarray(self.feature_names_out_, dtype=object)

    def unknown_category_counts(self, X: pd.DataFrame) -> pd.Series:
        """Count values not in the train-fitted categorical vocabulary."""

        self._check_fitted()
        self._validate_predictors(X)
        categorical = self._prepare_categorical(X)
        counts = {
            feature: int(
                (~categorical[feature].isin(set(self.categorical_categories_[position]))).sum()
            )
            for position, feature in enumerate(CATEGORICAL_PREDICTORS)
        }
        return pd.Series(counts, name="Unknown category rows")

    def structural_imputation_sources(self, X: pd.DataFrame) -> pd.DataFrame:
        """Summarise observed, location-median, and global-fallback usage."""

        self._check_fitted()
        self._validate_predictors(X)
        rows: list[dict[str, object]] = []
        for feature in STRUCTURAL_NUMERICAL_PREDICTORS:
            missing = X[feature].isna()
            location_available = X["Location"].map(
                self.structural_location_medians_[feature]
            ).notna()
            rows.append(
                {
                    "Feature": feature,
                    "Rows": int(len(X)),
                    "Observed rows": int((~missing).sum()),
                    "Missing rows": int(missing.sum()),
                    "Location-median imputations": int((missing & location_available).sum()),
                    "Global-fallback imputations": int((missing & ~location_available).sum()),
                    "Train global median": float(self.numeric_medians_[feature]),
                }
            )
        return pd.DataFrame(rows)


def fit_transform_chronological_splits(
    split: ChronologicalSplit,
    scale_numeric: bool = False,
) -> PreprocessedSplits:
    """Fit on Train and transform Validation/Test without refitting."""

    train = separate_supervised_components(split.train)
    validation = separate_supervised_components(split.validation)
    test = separate_supervised_components(split.test)

    preprocessor = RainfallPreprocessor(scale_numeric=scale_numeric)
    X_train = preprocessor.fit_transform(train.X)
    X_validation = preprocessor.transform(validation.X)
    X_test = preprocessor.transform(test.X)
    return PreprocessedSplits(
        preprocessor=preprocessor,
        X_train=X_train,
        X_validation=X_validation,
        X_test=X_test,
        y_train=train.y,
        y_validation=validation.y,
        y_test=test.y,
        dates_train=train.dates,
        dates_validation=validation.dates,
        dates_test=test.dates,
    )
