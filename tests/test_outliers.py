"""Tests for reusable T05 outlier and suspicious-value helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fdm_rainfall.outliers import (  # noqa: E402
    ALLOWED_CLASSIFICATIONS,
    NUMERICAL_FEATURES,
    cloud_nine_investigation,
    humidity_boundary_summary,
    iqr_outlier_summary,
    outlier_decision_summary,
    percentile_summary,
    proposal_consistency,
    rainfall_skewness_summary,
    suspicious_value_details,
)


def sample_frame() -> pd.DataFrame:
    rows = 8
    data: dict[str, list[object]] = {
        "Date": [f"2020-01-{day:02d}" for day in range(1, rows + 1)],
        "Location": ["A"] * 4 + ["B"] * 4,
        "RainTomorrow": ["No", "No", "Yes", "Yes", "No", "Yes", None, "No"],
        "RainToday": ["No", "No", "Yes", "Yes", "No", "Yes", None, "No"],
        "Rainfall": [0.0, 0.0, 1.0, 2.0, 3.0, 100.0, 200.0, 371.0],
        "Evaporation": [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 145.0],
        "WindGustSpeed": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 135.0],
        "WindSpeed9am": [0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 130.0],
        "WindSpeed3pm": [0.0, 10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 87.0],
        "Humidity9am": [0.0, 25.0, 50.0, 75.0, 100.0, 50.0, 60.0, 70.0],
        "Humidity3pm": [0.0, 25.0, 50.0, 75.0, 100.0, 50.0, 60.0, 70.0],
        "Cloud9am": [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 8.0, 9.0],
        "Cloud3pm": [0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 8.0, 9.0],
    }
    for index, feature in enumerate(NUMERICAL_FEATURES):
        if feature not in data:
            data[feature] = [float(index + value) for value in range(rows)]
    return pd.DataFrame(data)


class OutlierTests(unittest.TestCase):
    def setUp(self) -> None:
        self.frame = sample_frame()

    def test_percentile_summary_covers_all_numerical_features(self) -> None:
        result = percentile_summary(self.frame)
        self.assertEqual(set(result["Feature"]), set(NUMERICAL_FEATURES))
        self.assertEqual(len(result), len(NUMERICAL_FEATURES))
        self.assertIn("99th percentile", result.columns)
        self.assertIn("Skewness", result.columns)

    def test_iqr_screening_flags_tail_without_modifying_input(self) -> None:
        before = self.frame.copy(deep=True)
        result = iqr_outlier_summary(self.frame).set_index("Feature")
        self.assertGreater(result.loc["Rainfall", "Total IQR-flagged"], 0)
        pd.testing.assert_frame_equal(self.frame, before)

    def test_cloud_nine_rows_retain_date_and_location_context(self) -> None:
        result = cloud_nine_investigation(self.frame)
        self.assertEqual(len(result), 2)
        self.assertEqual(set(result["Feature"]), {"Cloud9am", "Cloud3pm"})
        self.assertEqual(set(result["Value"]), {9})

    def test_humidity_boundaries_distinguish_boundary_from_violation(self) -> None:
        result = humidity_boundary_summary(self.frame).set_index("Feature")
        self.assertEqual(int(result["Outside 0–100 range"].sum()), 0)
        self.assertEqual(result.loc["Humidity9am", "Count equal to 0"], 1)
        self.assertEqual(result.loc["Humidity3pm", "Count equal to 100"], 1)

    def test_rainfall_summary_reconciles_zero_and_positive_counts(self) -> None:
        result = rainfall_skewness_summary(self.frame).set_index("Rainfall metric")["Value"]
        self.assertEqual(result["Zero-rain count"] + result["Positive-rain count"], result["Non-missing Rainfall count"])
        self.assertEqual(result["Maximum"], 371.0)

    def test_suspicious_details_include_requested_exact_values(self) -> None:
        result = suspicious_value_details(self.frame)
        self.assertIn("Evaporation maximum = 145 mm", set(result["Trigger"]))
        self.assertIn("WindSpeed9am maximum = 130 km/h", set(result["Trigger"]))
        self.assertTrue(set(result["Classification"]).issubset(ALLOWED_CLASSIFICATIONS))

    def test_decision_summary_uses_only_allowed_classifications(self) -> None:
        result = outlier_decision_summary(self.frame)
        self.assertTrue(set(result["Classification"]).issubset(ALLOWED_CLASSIFICATIONS))
        self.assertEqual(set(result["Feature"]), set(NUMERICAL_FEATURES))

    def test_proposal_comparison_has_valid_results(self) -> None:
        result = proposal_consistency(self.frame)
        self.assertEqual(len(result), 6)
        self.assertTrue(set(result["Match / Mismatch"]).issubset({"Match", "Mismatch"}))


if __name__ == "__main__":
    unittest.main()
