"""Tests for reusable T04 target-and-feature relationship helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fdm_rainfall.relationships import (  # noqa: E402
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    categorical_target_summary,
    correlation_analysis,
    location_target_rates,
    numeric_target_summary,
    raintoday_rainfall_relationship,
    target_association_summary,
    target_distribution,
    temporal_target_rates,
)


def sample_frame() -> pd.DataFrame:
    rows = 6
    data: dict[str, list[object]] = {
        "Date": ["2020-01-01", "2020-03-01", "2020-06-01", "2021-09-01", "2021-12-01", "2021-12-02"],
        "Location": ["A", "A", "A", "B", "B", "B"],
        "RainTomorrow": ["No", "Yes", "No", "Yes", None, "No"],
        "Rainfall": [0.0, 2.0, 1.0, None, 4.0, 0.0],
        "RainToday": ["No", "Yes", "No", None, "Yes", "No"],
        "WindGustDir": ["N", "S", "N", "S", None, "N"],
        "WindDir9am": ["N", "S", "N", "S", None, "N"],
        "WindDir3pm": ["N", "S", "N", "S", None, "N"],
    }
    for index, feature in enumerate(NUMERIC_FEATURES):
        if feature not in data:
            data[feature] = [float(index + value) for value in range(rows)]
    return pd.DataFrame(data)


class RelationshipTests(unittest.TestCase):
    def setUp(self) -> None:
        self.frame = sample_frame()

    def test_target_distribution_reconciles_labelled_and_missing_rows(self) -> None:
        metrics = target_distribution(self.frame).set_index("Metric")["Value"]
        self.assertEqual(metrics["No count"], 3)
        self.assertEqual(metrics["Yes count"], 2)
        self.assertEqual(metrics["Labelled total"], 5)
        self.assertEqual(metrics["Missing target count"], 1)

    def test_temporal_tables_use_all_months_and_eda_only_seasons(self) -> None:
        result = temporal_target_rates(self.frame)
        self.assertEqual(len(result.by_month), 12)
        self.assertEqual(set(result.by_season["Season"]), {"Summer", "Autumn", "Winter", "Spring"})
        self.assertTrue(result.by_season["EDA-only derivation note"].str.contains("T04").all())

    def test_location_counts_reconcile_to_labelled_target(self) -> None:
        result = location_target_rates(self.frame)
        self.assertEqual(int(result["Labelled record count"].sum()), 5)
        self.assertEqual(set(result["Location"]), {"A", "B"})

    def test_numeric_summary_uses_available_values_within_each_class(self) -> None:
        result = numeric_target_summary(self.frame)
        self.assertEqual(len(result), 2 * len(NUMERIC_FEATURES))
        rain_yes = result.query("Feature == 'Rainfall' and RainTomorrow == 'Yes'").iloc[0]
        self.assertEqual(rain_yes["Available count"], 1)
        self.assertEqual(rain_yes["Missing within class"], 1)

    def test_categorical_summary_keeps_missing_as_an_explicit_category(self) -> None:
        result = categorical_target_summary(self.frame)
        self.assertEqual(set(result["Feature"]), set(CATEGORICAL_FEATURES))
        self.assertIn("<Missing>", set(result.loc[result["Feature"] == "RainToday", "Category"]))

    def test_correlation_pairs_are_unique_and_pairwise_complete(self) -> None:
        result = correlation_analysis(self.frame)
        expected_pairs = len(NUMERIC_FEATURES) * (len(NUMERIC_FEATURES) - 1) // 2
        self.assertEqual(len(result.pairs), expected_pairs)
        self.assertEqual(result.matrix.shape, (len(NUMERIC_FEATURES), len(NUMERIC_FEATURES) + 1))

    def test_rain_threshold_comparison_reports_boundary_disagreement(self) -> None:
        metrics = raintoday_rainfall_relationship(self.frame).set_index("Metric")["Value"]
        self.assertEqual(metrics["Usable Rainfall/RainToday comparisons"], 5)
        self.assertEqual(metrics["Disagreement count using Rainfall >= 1 mm"], 1)
        self.assertEqual(metrics["Disagreements at exactly 1.0 mm"], 1)
        self.assertEqual(metrics["Agreement percentage using Rainfall > 1 mm"], 100.0)
        self.assertEqual(
            metrics["Proposal threshold definition"],
            "Minor mismatch / boundary clarification",
        )

    def test_association_summary_covers_every_original_predictor(self) -> None:
        result = target_association_summary(self.frame)
        self.assertEqual(set(result["Feature"]), set(NUMERIC_FEATURES + CATEGORICAL_FEATURES))
        self.assertEqual(len(result), len(NUMERIC_FEATURES) + len(CATEGORICAL_FEATURES))


if __name__ == "__main__":
    unittest.main()
