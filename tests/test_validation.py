"""Tests for reusable T01 dataset loading and validation logic."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fdm_rainfall.data import load_weather_data  # noqa: E402
from fdm_rainfall.validation import verify_weather_dataset  # noqa: E402


class LoadWeatherDataTests(unittest.TestCase):
    def test_missing_file_raises_file_not_found(self) -> None:
        with self.assertRaises(FileNotFoundError):
            load_weather_data(PROJECT_ROOT / "data" / "raw" / "does_not_exist.csv")

    @patch("fdm_rainfall.data.pd.read_csv")
    @patch("fdm_rainfall.data.Path.is_file", return_value=True)
    def test_loader_returns_parser_output_unchanged(self, _is_file, read_csv) -> None:
        expected = pd.DataFrame(
            {
                "Date": ["2020-01-01", "2020-01-02"],
                "Location": ["A", "A"],
                "RainTomorrow": ["Yes", None],
            }
        )
        read_csv.return_value = expected

        actual = load_weather_data("sample.csv")

        self.assertIs(actual, expected)
        read_csv.assert_called_once_with(Path("sample.csv"), low_memory=False)


class VerifyWeatherDatasetTests(unittest.TestCase):
    def test_required_metrics_and_duplicates(self) -> None:
        frame = pd.DataFrame(
            {
                "Date": ["2020-01-01", "2020-01-01", "2020-01-02"],
                "Location": ["A", "A", "B"],
                "RainTomorrow": ["Yes", "Yes", None],
                "RISK_MM": [1.0, 1.0, 0.0],
                "Extra": [5, 5, 7],
            }
        )

        result = verify_weather_dataset(frame)

        self.assertEqual(result.row_count, 3)
        self.assertEqual(result.column_count, 5)
        self.assertEqual(result.date_min, "2020-01-01")
        self.assertEqual(result.date_max, "2020-01-02")
        self.assertEqual(result.unique_location_count, 2)
        self.assertEqual(result.rain_tomorrow_values, ("Yes",))
        self.assertEqual(result.rain_tomorrow_class_counts, {"Yes": 2})
        self.assertEqual(result.rain_tomorrow_missing_count, 1)
        self.assertEqual(result.rain_tomorrow_labelled_count, 2)
        self.assertEqual(result.exact_duplicate_rows, 1)
        self.assertEqual(result.duplicate_date_location_combinations, 1)
        self.assertEqual(result.duplicate_date_location_rows, 2)
        self.assertTrue(result.risk_mm_exists)
        self.assertEqual(result.unexpected_columns, ("RISK_MM", "Extra"))

    def test_proposal_comparison_reports_mismatches(self) -> None:
        frame = pd.DataFrame(
            {
                "Date": ["2020-01-01"],
                "Location": ["A"],
                "RainTomorrow": ["No"],
            }
        )

        comparison = verify_weather_dataset(frame).proposal_comparison()

        self.assertEqual(
            list(comparison.columns),
            ["Claim", "Expected value", "Actual dataset value", "Match / Mismatch", "Comment"],
        )
        self.assertTrue((comparison["Match / Mismatch"] == "Mismatch").any())


if __name__ == "__main__":
    unittest.main()
