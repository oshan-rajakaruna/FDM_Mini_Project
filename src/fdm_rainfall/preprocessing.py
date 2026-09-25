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

ENGINEERED_NUMERICAL_PREDICTORS = (
    *NUMERICAL_PREDICTORS,
    "Month_sin",
    "Month_cos",
    "TempRange",
    "TempChange",
    "HumidityChange",
    "PressureChange",
    "WindSpeedChange",
    "WindGustDir_sin",
    "WindGustDir_cos",
    "WindDir9am_sin",
    "WindDir9am_cos",
    "WindDir3pm_sin",
    "WindDir3pm_cos",
)

ENGINEERED_CATEGORICAL_PREDICTORS = ("Location", "RainToday")
ENGINEERED_PASSTHROUGH_INDICATORS = (
    "WindGustDir_missing",
    "WindDir9am_missing",
    "WindDir3pm_missing",
)
ENGINEERED_PREDICTORS = (
    *ENGINEERED_NUMERICAL_PREDICTORS,
    *ENGINEERED_CATEGORICAL_PREDICTORS,
    *ENGINEERED_PASSTHROUGH_INDICATORS,
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


@dataclass(frozen=True)
class EngineeredPreprocessedSplits:
    """Feature-engineered and preprocessed chronological subsets."""

    feature_engineer: object
    preprocessor: "RainfallPreprocessor"
    engineered_train: pd.DataFrame
    engineered_validation: pd.DataFrame
    engineered_test: pd.DataFrame
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
    unchanged. The original configuration scales 16 numerical columns. The
    engineered configuration scales its 29 continuous/circular numerical
    columns while leaving missing indicators and one-hot columns unchanged.
    """

    def __init__(self, scale_numeric: bool = False, configuration: str = "original") -> None:
        self.scale_numeric = bool(scale_numeric)
        if configuration not in {"original", "engineered"}:
            raise ValueError("configuration must be 'original' or 'engineered'")
        self.configuration = configuration
        if configuration == "original":
            self.numerical_predictors_ = NUMERICAL_PREDICTORS
            self.categorical_predictors_ = CATEGORICAL_PREDICTORS
            self.passthrough_indicators_ = ()
            self.predictor_columns_ = predictor_columns()
        else:
            self.numerical_predictors_ = ENGINEERED_NUMERICAL_PREDICTORS
            self.categorical_predictors_ = ENGINEERED_CATEGORICAL_PREDICTORS
            self.passthrough_indicators_ = ENGINEERED_PASSTHROUGH_INDICATORS
            self.predictor_columns_ = ENGINEERED_PREDICTORS
        self.is_fitted_ = False

    def _validate_predictors(self, frame: pd.DataFrame) -> None:
        missing = sorted(set(self.predictor_columns_).difference(frame.columns))
        if missing:
            raise ValueError(f"Required predictor columns are missing: {', '.join(missing)}")
        unexpected = sorted(set(frame.columns).difference(self.predictor_columns_))
        if unexpected:
            scope = (
                "original T07 predictors"
                if self.configuration == "original"
                else "T08 engineered predictors"
            )
            raise ValueError(
                f"Only {scope} may enter preprocessing; separate or reject: "
                + ", ".join(unexpected)
            )

    def fit(self, X_train: pd.DataFrame) -> "RainfallPreprocessor":
        """Fit every learned parameter from training predictors only."""

        self._validate_predictors(X_train)
        train = X_train.loc[:, self.predictor_columns_].copy(deep=True)
        self.fit_row_count_ = int(len(train))
        self.fit_index_fingerprint_ = _index_fingerprint(train.index)

        self.numeric_medians_ = train.loc[:, self.numerical_predictors_].median()
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
            for feature in self.categorical_predictors_
        ]
        self.encoder_ = OneHotEncoder(
            categories=self.categorical_categories_,
            handle_unknown="ignore",
            sparse_output=False,
            dtype=np.float64,
        )
        self.encoder_.fit(categorical_train.loc[:, self.categorical_predictors_])

        imputed_numeric, _ = self._impute_numeric(train)
        self.scaler_ = StandardScaler() if self.scale_numeric else None
        if self.scaler_ is not None:
            self.scaler_.fit(imputed_numeric.loc[:, self.numerical_predictors_])

        self.numeric_feature_names_ = list(self.numerical_predictors_)
        self.indicator_feature_names_ = [
            f"{feature}_missing" for feature in STRUCTURAL_NUMERICAL_PREDICTORS
        ] + list(self.passthrough_indicators_)
        self.encoded_feature_names_ = list(
            self.encoder_.get_feature_names_out(self.categorical_predictors_)
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

    def _prepare_categorical(self, frame: pd.DataFrame) -> pd.DataFrame:
        categorical = frame.loc[:, self.categorical_predictors_].copy(deep=True)
        return categorical.fillna(MISSING_CATEGORY).astype(str)

    def _impute_numeric(self, frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        numeric = frame.loc[:, self.numerical_predictors_].copy(deep=True)
        indicators = pd.DataFrame(index=frame.index)

        for feature in STRUCTURAL_NUMERICAL_PREDICTORS:
            missing_mask = numeric[feature].isna()
            indicators[f"{feature}_missing"] = missing_mask.astype(np.float64)
            location_fill = frame["Location"].map(self.structural_location_medians_[feature])
            numeric[feature] = numeric[feature].fillna(location_fill)
            numeric[feature] = numeric[feature].fillna(self.numeric_medians_[feature])

        non_structural = [
            feature
            for feature in self.numerical_predictors_
            if feature not in STRUCTURAL_NUMERICAL_PREDICTORS
        ]
        numeric.loc[:, non_structural] = numeric.loc[:, non_structural].fillna(
            self.numeric_medians_.loc[non_structural]
        )
        for feature in self.passthrough_indicators_:
            values = frame[feature]
            if values.isna().any() or not values.isin([0, 1, 0.0, 1.0]).all():
                raise ValueError(f"{feature} must contain only non-missing binary values")
            indicators[feature] = values.astype(np.float64)
        return numeric, indicators

    def impute_numeric(self, X: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Return imputed numerics and structural missing indicators."""

        self._check_fitted()
        self._validate_predictors(X)
        return self._impute_numeric(X.loc[:, self.predictor_columns_].copy(deep=True))

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Transform predictors using only parameters learned during ``fit``."""

        self._check_fitted()
        self._validate_predictors(X)
        source = X.loc[:, self.predictor_columns_].copy(deep=True)
        numeric, indicators = self._impute_numeric(source)

        if self.scaler_ is not None:
            numeric_values = self.scaler_.transform(numeric.loc[:, self.numerical_predictors_])
            numeric = pd.DataFrame(
                numeric_values,
                index=source.index,
                columns=self.numerical_predictors_,
            )

        categorical = self._prepare_categorical(source)
        encoded_values = self.encoder_.transform(categorical.loc[:, self.categorical_predictors_])
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
            for position, feature in enumerate(self.categorical_predictors_)
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


def fit_transform_engineered_chronological_splits(
    split: ChronologicalSplit,
    scale_numeric: bool = False,
) -> EngineeredPreprocessedSplits:
    """Engineer raw observation-date features, then fit preprocessing on Train.

    The feature engineer is deterministic and target-independent. All learned
    imputation, encoding, and scaling parameters are fitted by the downstream
    preprocessor using the chronological Train subset only.
    """

    from fdm_rainfall.features import WeatherFeatureEngineer

    train = separate_supervised_components(split.train)
    validation = separate_supervised_components(split.validation)
    test = separate_supervised_components(split.test)

    raw_inputs = {
        "Train": pd.concat([train.dates.rename(DATE_COLUMN), train.X], axis=1),
        "Validation": pd.concat(
            [validation.dates.rename(DATE_COLUMN), validation.X], axis=1
        ),
        "Test": pd.concat([test.dates.rename(DATE_COLUMN), test.X], axis=1),
    }
    engineer = WeatherFeatureEngineer(output="default").fit(raw_inputs["Train"])
    engineered_train = engineer.transform(raw_inputs["Train"])
    engineered_validation = engineer.transform(raw_inputs["Validation"])
    engineered_test = engineer.transform(raw_inputs["Test"])

    preprocessor = RainfallPreprocessor(
        scale_numeric=scale_numeric,
        configuration="engineered",
    )
    X_train = preprocessor.fit_transform(engineered_train)
    X_validation = preprocessor.transform(engineered_validation)
    X_test = preprocessor.transform(engineered_test)
    return EngineeredPreprocessedSplits(
        feature_engineer=engineer,
        preprocessor=preprocessor,
        engineered_train=engineered_train,
        engineered_validation=engineered_validation,
        engineered_test=engineered_test,
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
