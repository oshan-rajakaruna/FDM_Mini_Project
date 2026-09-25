"""Tests for T07 leakage-safe preprocessing."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fdm_rainfall.data import (  # noqa: E402
    chronological_train_validation_test_split,
    load_weather_data,
)
from fdm_rainfall.preprocessing import (  # noqa: E402
    CATEGORICAL_PREDICTORS,
    MISSING_CATEGORY,
    NUMERICAL_PREDICTORS,
    STRUCTURAL_NUMERICAL_PREDICTORS,
    RainfallPreprocessor,
    fit_transform_chronological_splits,
    predictor_columns,
    separate_supervised_components,
)


def sample_frame() -> pd.DataFrame:
    rows = 6
    data: dict[str, list[object]] = {
        "Date": [f"2020-01-{day:02d}" for day in range(1, rows + 1)],
        "Location": ["A", "A", "B", "B", "A", "C"],
        "WindGustDir": ["N", None, "S", "S", "N", "UNSEEN"],
        "WindDir9am": ["E", "E", None, "W", "E", "UNSEEN"],
        "WindDir3pm": ["E", "W", "W", None, "E", "UNSEEN"],
        "RainToday": ["No", "Yes", None, "No", "Yes", "UNSEEN"],
        "RainTomorrow": ["No", "Yes", "No", "No", "Yes", "No"],
    }
    for position, feature in enumerate(NUMERICAL_PREDICTORS):
        data[feature] = [float(position + value) for value in range(1, rows + 1)]

    data["MinTemp"] = [10.0, None, 30.0, 40.0, None, 1000.0]
    data["Sunshine"] = [1.0, 3.0, None, None, None, None]
    data["Evaporation"] = [2.0, 4.0, None, None, None, None]
    data["Cloud9am"] = [1.0, 7.0, None, None, None, None]
    data["Cloud3pm"] = [2.0, 6.0, None, None, None, None]
    return pd.DataFrame(data, index=[10, 11, 12, 13, 14, 15])


class RainfallPreprocessingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.frame = sample_frame()
        self.train = self.frame.iloc[:4].copy()
        self.later = self.frame.iloc[4:].copy()
        self.X_train = separate_supervised_components(self.train).X
        self.X_later = separate_supervised_components(self.later).X

    def test_feature_roles_and_supervised_separation(self) -> None:
        components = separate_supervised_components(self.train)

        self.assertEqual(tuple(components.X.columns), predictor_columns())
        self.assertEqual(len(NUMERICAL_PREDICTORS), 16)
        self.assertEqual(len(CATEGORICAL_PREDICTORS), 5)
        self.assertNotIn("Date", components.X)
        self.assertNotIn("RainTomorrow", components.X)
        self.assertTrue(components.X.index.equals(components.y.index))
        self.assertTrue(components.X.index.equals(components.dates.index))

    def test_target_missing_and_risk_mm_are_rejected(self) -> None:
        missing_target = self.train.copy()
        missing_target.loc[missing_target.index[0], "RainTomorrow"] = None
        with self.assertRaisesRegex(ValueError, "non-missing RainTomorrow"):
            separate_supervised_components(missing_target)

        risk = self.train.assign(RISK_MM=0.0)
        with self.assertRaisesRegex(ValueError, "RISK_MM"):
            separate_supervised_components(risk)

    def test_fit_and_transform_do_not_mutate_inputs(self) -> None:
        train_before = self.X_train.copy(deep=True)
        later_before = self.X_later.copy(deep=True)

        transformer = RainfallPreprocessor().fit(self.X_train)
        transformer.transform(self.X_later)

        pd.testing.assert_frame_equal(self.X_train, train_before)
        pd.testing.assert_frame_equal(self.X_later, later_before)

    def test_structural_location_median_and_global_fallback(self) -> None:
        transformer = RainfallPreprocessor().fit(self.X_train)
        numeric, indicators = transformer.impute_numeric(self.X_later)

        self.assertEqual(numeric.loc[14, "Sunshine"], 2.0)
        self.assertEqual(numeric.loc[15, "Sunshine"], 2.0)
        self.assertEqual(indicators.loc[14, "Sunshine_missing"], 1.0)
        self.assertEqual(indicators.loc[15, "Sunshine_missing"], 1.0)
        self.assertTrue(pd.isna(transformer.structural_location_medians_["Sunshine"].loc["B"]))

    def test_non_structural_numeric_uses_train_median(self) -> None:
        transformer = RainfallPreprocessor().fit(self.X_train)
        numeric, _ = transformer.impute_numeric(self.X_later)

        self.assertEqual(transformer.numeric_medians_["MinTemp"], 30.0)
        self.assertEqual(numeric.loc[14, "MinTemp"], 30.0)
        self.assertEqual(numeric.loc[15, "MinTemp"], 1000.0)

    def test_categorical_missing_and_unknown_values_are_safe(self) -> None:
        transformer = RainfallPreprocessor().fit(self.X_train)
        transformed = transformer.transform(self.X_later)
        unknown = transformer.unknown_category_counts(self.X_later)

        for categories in transformer.categorical_categories_:
            self.assertIn(MISSING_CATEGORY, set(categories))
        self.assertEqual(int(unknown.loc["Location"]), 1)
        self.assertEqual(int(unknown.loc["WindGustDir"]), 1)
        self.assertFalse(transformed.isna().any().any())

    def test_target_date_and_risk_are_never_output_features(self) -> None:
        transformer = RainfallPreprocessor().fit(self.X_train)
        names = set(transformer.get_feature_names_out())

        self.assertNotIn("RainTomorrow", names)
        self.assertNotIn("Date", names)
        self.assertNotIn("RISK_MM", names)
        self.assertIn("Rainfall", names)
        self.assertTrue(any(name.startswith("RainToday_") for name in names))

        for forbidden in ("RainTomorrow", "Date", "RISK_MM", "Year"):
            with self.assertRaisesRegex(ValueError, "original T07 predictors"):
                transformer.transform(self.X_later.assign(**{forbidden: 1}))

    def test_scaler_is_fitted_from_imputed_train_only(self) -> None:
        transformer = RainfallPreprocessor(scale_numeric=True).fit(self.X_train)
        imputed, _ = transformer.impute_numeric(self.X_train)

        np.testing.assert_allclose(
            transformer.scaler_.mean_,
            imputed.loc[:, NUMERICAL_PREDICTORS].mean().to_numpy(),
        )
        self.assertEqual(transformer.fit_row_count_, len(self.X_train))
        transformed_later = transformer.transform(self.X_later)
        self.assertGreater(abs(transformed_later.loc[15, "MinTemp"]), 1.0)

    def test_scaled_and_unscaled_paths_share_schema(self) -> None:
        unscaled = RainfallPreprocessor(scale_numeric=False).fit(self.X_train)
        scaled = RainfallPreprocessor(scale_numeric=True).fit(self.X_train)

        self.assertEqual(
            unscaled.get_feature_names_out().tolist(),
            scaled.get_feature_names_out().tolist(),
        )
        self.assertIsNone(unscaled.scaler_)
        self.assertIsNotNone(scaled.scaler_)

    def test_output_is_deterministic(self) -> None:
        first = RainfallPreprocessor().fit_transform(self.X_train)
        second = RainfallPreprocessor().fit_transform(self.X_train)

        pd.testing.assert_frame_equal(first, second)

    def test_actual_split_rows_alignment_missingness_and_boundaries(self) -> None:
        frame = load_weather_data(PROJECT_ROOT / "data" / "raw" / "weatherAUS.csv")
        split = chronological_train_validation_test_split(frame)
        processed = fit_transform_chronological_splits(split, scale_numeric=False)

        self.assertEqual(
            [len(processed.X_train), len(processed.X_validation), len(processed.X_test)],
            [99_546, 21_342, 21_305],
        )
        self.assertEqual(
            [split.train["Date"].min().date().isoformat(), split.train["Date"].max().date().isoformat()],
            ["2007-11-01", "2015-01-12"],
        )
        self.assertEqual(
            [split.validation["Date"].min().date().isoformat(), split.validation["Date"].max().date().isoformat()],
            ["2015-01-13", "2016-04-08"],
        )
        self.assertEqual(
            [split.test["Date"].min().date().isoformat(), split.test["Date"].max().date().isoformat()],
            ["2016-04-09", "2017-06-25"],
        )
        for X, y in (
            (processed.X_train, processed.y_train),
            (processed.X_validation, processed.y_validation),
            (processed.X_test, processed.y_test),
        ):
            self.assertTrue(X.index.equals(y.index))
            self.assertFalse(X.isna().any().any())


if __name__ == "__main__":
    unittest.main()
