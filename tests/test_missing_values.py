"""Tests for reusable T03 missing-value analysis helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fdm_rainfall.missing_values import (  # noqa: E402
    IMPORTANT_LOCATION_FEATURES,
    comissingness_summary,
    location_missingness,
    location_year_missingness,
    missing_summary,
    rainfall_raintoday_relationship,
    row_missingness,
    target_missingness,
    temporal_missingness,
)


def sample_frame() -> pd.DataFrame:
    rows = 4
    data: dict[str, list[object]] = {
        "Date": ["2020-01-01", "2020-01-02", "2021-01-01", "2021-01-02"],
        "Location": ["A", "A", "B", "B"],
        "Rainfall": [1.0, None, 0.0, None],
        "RainToday": ["Yes", None, "No", None],
        "RainTomorrow": ["Yes", None, "No", None],
    }
    for feature in IMPORTANT_LOCATION_FEATURES:
        data[feature] = [None, None, 1.0, 2.0]
    for feature in ("WindDir3pm", "WindSpeed9am", "WindSpeed3pm"):
        if feature not in data:
            data[feature] = [None, None, 1.0, 2.0]
    frame = pd.DataFrame(data)
    self_check = len(frame) == rows
    assert self_check
    return frame


class MissingValueTests(unittest.TestCase):
    def setUp(self) -> None:
        self.frame = sample_frame()

    def test_missing_summary_is_sorted_and_classified(self) -> None:
        summary = missing_summary(self.frame)
        self.assertTrue(summary["Missing percentage"].is_monotonic_decreasing)
        rainfall = summary.set_index("Feature").loc["Rainfall"]
        self.assertEqual(rainfall["Missing count"], 2)
        self.assertEqual(rainfall["Descriptive severity"], "High missingness")

    def test_row_missingness_reconciles_to_all_rows(self) -> None:
        result = row_missingness(self.frame, very_high_threshold=2)
        self.assertEqual(int(result.distribution["Row count"].sum()), len(self.frame))
        metrics = result.overview.set_index("Row-missingness metric")["Value"]
        self.assertGreater(metrics["Rows with at least one missing value"], 0)

    def test_location_and_temporal_tables_cover_requested_features(self) -> None:
        locations = location_missingness(self.frame)
        temporal = temporal_missingness(self.frame)
        location_year = location_year_missingness(self.frame)
        self.assertEqual(len(locations), 2 * len(IMPORTANT_LOCATION_FEATURES))
        self.assertEqual(
            set(locations.query("Location == 'A'")["Coverage classification"]),
            {"Complete absence"},
        )
        self.assertEqual(set(temporal["Period type"]), {"Year", "Month of year"})
        self.assertEqual(set(location_year["Feature"]), set(IMPORTANT_LOCATION_FEATURES))

    def test_comissingness_reports_identical_rain_masks(self) -> None:
        comparison = comissingness_summary(self.frame)
        rain_pair = comparison.query("`Feature A` == 'Rainfall' and `Feature B` == 'RainToday'").iloc[0]
        self.assertTrue(rain_pair["Identical missingness masks"])
        self.assertEqual(rain_pair["Both missing"], 2)

    def test_rainfall_raintoday_relationship_has_no_exceptions(self) -> None:
        relationship = rainfall_raintoday_relationship(self.frame).set_index("Relationship metric")["Value"]
        self.assertTrue(relationship["Missingness fully coincides"])
        self.assertEqual(relationship["Rainfall-only missing count"], 0)
        self.assertEqual(relationship["RainToday-only missing count"], 0)

    def test_target_endpoint_analysis_reconciles_counts(self) -> None:
        result = target_missingness(self.frame)
        metrics = result.overview.set_index("Target-missingness metric")["Value"]
        self.assertEqual(metrics["Missing RainTomorrow count"], 2)
        self.assertEqual(int(result.by_location["Missing target count"].sum()), 2)
        self.assertEqual(int(result.by_year["Missing target count"].sum()), 2)


if __name__ == "__main__":
    unittest.main()
