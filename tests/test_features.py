"""Tests for T08 deterministic, leakage-safe feature engineering."""

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
from fdm_rainfall.features import (  # noqa: E402
    ALL_CANDIDATE_FEATURES,
    AUSTRALIAN_SEASONS,
    COMPASS_DEGREES,
    DEFAULT_ENGINEERED_PREDICTORS,
    WeatherFeatureEngineer,
)
from fdm_rainfall.preprocessing import (  # noqa: E402
    fit_transform_engineered_chronological_splits,
)


def sample_feature_frame() -> pd.DataFrame:
    """Return a complete small raw frame with controlled feature values."""

    return pd.DataFrame(
        {
            "Date": ["2020-01-15", "2020-06-15", "2020-12-15"],
            "Location": ["A", "B", "C"],
            "MinTemp": [10.0, 5.0, np.nan],
            "MaxTemp": [25.0, 15.0, 30.0],
            "Rainfall": [0.0, 9.0, np.nan],
            "Evaporation": [2.0, 3.0, 4.0],
            "Sunshine": [8.0, 4.0, np.nan],
            "WindGustDir": ["N", "E", None],
            "WindGustSpeed": [40.0, 50.0, 30.0],
            "WindDir9am": ["S", "W", "NNE"],
            "WindDir3pm": ["NE", None, "SW"],
            "WindSpeed9am": [10.0, 20.0, 12.0],
            "WindSpeed3pm": [15.0, 12.0, 12.0],
            "Humidity9am": [70.0, 80.0, 50.0],
            "Humidity3pm": [50.0, 90.0, 50.0],
            "Pressure9am": [1015.0, 1020.0, 1000.0],
            "Pressure3pm": [1012.0, 1022.0, 999.0],
            "Cloud9am": [2.0, 7.0, np.nan],
            "Cloud3pm": [4.0, 8.0, np.nan],
            "Temp9am": [12.0, 8.0, 20.0],
            "Temp3pm": [23.0, 14.0, 18.0],
            "RainToday": ["No", "Yes", None],
            "RainTomorrow": ["No", "Yes", "No"],
        },
        index=[10, 20, 30],
    )


class WeatherFeatureEngineeringTests(unittest.TestCase):
    def setUp(self) -> None:
        self.frame = sample_feature_frame()
        self.candidates = WeatherFeatureEngineer(output="candidates").fit_transform(self.frame)

    def test_input_row_count_and_index_are_preserved_without_mutation(self) -> None:
        before = self.frame.copy(deep=True)
        default = WeatherFeatureEngineer().fit_transform(self.frame)

        pd.testing.assert_frame_equal(self.frame, before)
        self.assertEqual(len(default), len(self.frame))
        self.assertTrue(default.index.equals(self.frame.index))

    def test_temp_range_formula(self) -> None:
        expected = self.frame["MaxTemp"] - self.frame["MinTemp"]
        pd.testing.assert_series_equal(self.candidates["TempRange"], expected, check_names=False)

    def test_temp_change_formula_and_sign(self) -> None:
        expected = self.frame["Temp3pm"] - self.frame["Temp9am"]
        pd.testing.assert_series_equal(self.candidates["TempChange"], expected, check_names=False)
        self.assertGreater(self.candidates.loc[10, "TempChange"], 0)

    def test_humidity_change_formula(self) -> None:
        expected = self.frame["Humidity3pm"] - self.frame["Humidity9am"]
        pd.testing.assert_series_equal(
            self.candidates["HumidityChange"], expected, check_names=False
        )

    def test_pressure_change_formula(self) -> None:
        expected = self.frame["Pressure3pm"] - self.frame["Pressure9am"]
        pd.testing.assert_series_equal(
            self.candidates["PressureChange"], expected, check_names=False
        )

    def test_wind_speed_change_formula(self) -> None:
        expected = self.frame["WindSpeed3pm"] - self.frame["WindSpeed9am"]
        pd.testing.assert_series_equal(
            self.candidates["WindSpeedChange"], expected, check_names=False
        )

    def test_australian_season_mapping_and_month_cycle(self) -> None:
        self.assertEqual(AUSTRALIAN_SEASONS[1], "Summer")
        self.assertEqual(AUSTRALIAN_SEASONS[6], "Winter")
        self.assertEqual(AUSTRALIAN_SEASONS[12], "Summer")
        self.assertEqual(self.candidates["Season"].tolist(), ["Summer", "Winter", "Summer"])
        self.assertAlmostEqual(self.candidates.loc[10, "Month_sin"], 0.0, places=12)
        self.assertAlmostEqual(self.candidates.loc[10, "Month_cos"], 1.0, places=12)
        self.assertAlmostEqual(self.candidates.loc[30, "Month_sin"], -0.5, places=12)
        self.assertAlmostEqual(self.candidates.loc[30, "Month_cos"], np.sqrt(3) / 2, places=12)

    def test_compass_mapping_and_cyclical_values(self) -> None:
        self.assertEqual(COMPASS_DEGREES["N"], 0.0)
        self.assertEqual(COMPASS_DEGREES["E"], 90.0)
        self.assertEqual(COMPASS_DEGREES["NNW"], 337.5)
        self.assertAlmostEqual(self.candidates.loc[10, "WindGustDir_sin"], 0.0, places=12)
        self.assertAlmostEqual(self.candidates.loc[10, "WindGustDir_cos"], 1.0, places=12)
        self.assertAlmostEqual(self.candidates.loc[20, "WindGustDir_sin"], 1.0, places=12)
        self.assertAlmostEqual(self.candidates.loc[20, "WindGustDir_cos"], 0.0, places=12)

    def test_missing_wind_direction_uses_neutral_pair_and_indicator(self) -> None:
        self.assertEqual(self.candidates.loc[30, "WindGustDir_sin"], 0.0)
        self.assertEqual(self.candidates.loc[30, "WindGustDir_cos"], 0.0)
        self.assertEqual(self.candidates.loc[30, "WindGustDir_missing"], 1.0)
        self.assertEqual(self.candidates.loc[10, "WindGustDir_missing"], 0.0)
        self.assertEqual(self.candidates.loc[20, "WindDir3pm_missing"], 1.0)

    def test_structural_missing_indicators_are_not_duplicated(self) -> None:
        default = WeatherFeatureEngineer().fit_transform(self.frame)
        for feature in ("Sunshine_missing", "Evaporation_missing", "Cloud9am_missing", "Cloud3pm_missing"):
            self.assertNotIn(feature, default.columns)

    def test_rainfall_log1p_is_valid_but_optional(self) -> None:
        self.assertAlmostEqual(self.candidates.loc[10, "Rainfall_log1p"], 0.0)
        self.assertAlmostEqual(self.candidates.loc[20, "Rainfall_log1p"], np.log(10.0))
        self.assertTrue(pd.isna(self.candidates.loc[30, "Rainfall_log1p"]))
        self.assertNotIn("Rainfall_log1p", DEFAULT_ENGINEERED_PREDICTORS)

    def test_target_is_not_used_and_future_columns_are_rejected(self) -> None:
        changed_target = self.frame.copy()
        changed_target["RainTomorrow"] = ["Yes", "No", "Yes"]
        first = WeatherFeatureEngineer().fit_transform(self.frame)
        second = WeatherFeatureEngineer().fit_transform(changed_target)
        pd.testing.assert_frame_equal(first, second)
        self.assertNotIn("RainTomorrow", first.columns)

        with self.assertRaisesRegex(ValueError, "future columns"):
            WeatherFeatureEngineer().fit(self.frame.assign(TomorrowHumidity=80))
        with self.assertRaisesRegex(ValueError, "RISK_MM"):
            WeatherFeatureEngineer().fit(self.frame.assign(RISK_MM=1.0))

    def test_deterministic_default_and_candidate_schemas(self) -> None:
        first = WeatherFeatureEngineer().fit_transform(self.frame)
        second = WeatherFeatureEngineer().fit_transform(self.frame)
        pd.testing.assert_frame_equal(first, second)
        self.assertEqual(tuple(first.columns), DEFAULT_ENGINEERED_PREDICTORS)
        self.assertEqual(tuple(self.candidates.columns), ALL_CANDIDATE_FEATURES)
        self.assertEqual(len(first.columns), 34)
        self.assertEqual(len(set(first.columns)), 34)

    def test_actual_split_preprocessing_integration(self) -> None:
        raw = load_weather_data(PROJECT_ROOT / "data" / "raw" / "weatherAUS.csv")
        raw_before = raw.copy(deep=True)
        split = chronological_train_validation_test_split(raw)
        split_before = {name: part.copy(deep=True) for name, part in split.frames.items()}
        processed = fit_transform_engineered_chronological_splits(split)

        expected_rows = [99_546, 21_342, 21_305]
        self.assertEqual(
            [len(processed.X_train), len(processed.X_validation), len(processed.X_test)],
            expected_rows,
        )
        self.assertEqual(len(processed.preprocessor.get_feature_names_out()), 89)
        self.assertEqual(processed.preprocessor.fit_row_count_, 99_546)
        for X, y, dates in (
            (processed.X_train, processed.y_train, processed.dates_train),
            (processed.X_validation, processed.y_validation, processed.dates_validation),
            (processed.X_test, processed.y_test, processed.dates_test),
        ):
            self.assertTrue(X.index.equals(y.index))
            self.assertTrue(X.index.equals(dates.index))
            self.assertFalse(X.isna().any().any())
            self.assertFalse(np.isinf(X.to_numpy(dtype=float)).any())
        pd.testing.assert_frame_equal(raw, raw_before)
        for name, part in split.frames.items():
            pd.testing.assert_frame_equal(part, split_before[name])


if __name__ == "__main__":
    unittest.main()
