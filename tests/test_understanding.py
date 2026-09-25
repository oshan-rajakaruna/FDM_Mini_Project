"""Tests for reusable T02 data-understanding helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fdm_rainfall.understanding import (  # noqa: E402
    LOGICAL_TYPES,
    basic_range_checks,
    categorical_summary,
    column_inventory,
    data_dictionary,
    date_understanding,
    feature_group_table,
    numerical_summary,
    target_summary,
)


def sample_frame() -> pd.DataFrame:
    data: dict[str, list[object]] = {}
    for column, logical_type in LOGICAL_TYPES.items():
        if column == "Date":
            data[column] = ["2020-01-01", "2020-01-02", "2021-02-01"]
        elif column == "Location":
            data[column] = ["A", "A", "B"]
        elif column in {"WindGustDir", "WindDir9am", "WindDir3pm"}:
            data[column] = ["N", "S", None]
        elif column == "RainToday":
            data[column] = ["No", "Yes", None]
        elif column == "RainTomorrow":
            data[column] = ["No", "Yes", None]
        elif column.startswith("Cloud"):
            data[column] = [0.0, 8.0, 9.0]
        elif logical_type.startswith("numerical"):
            data[column] = [1.0, 2.0, None]
    return pd.DataFrame(data, columns=LOGICAL_TYPES)


class UnderstandingTests(unittest.TestCase):
    def setUp(self) -> None:
        self.frame = sample_frame()

    def test_inventory_covers_every_column_and_reconciles_counts(self) -> None:
        inventory = column_inventory(self.frame)
        self.assertEqual(list(inventory["Column"]), list(self.frame.columns))
        self.assertTrue(
            (
                inventory["Non-null values"] + inventory["Missing values"]
                == len(self.frame)
            ).all()
        )

    def test_feature_groups_cover_each_column_once(self) -> None:
        groups = feature_group_table()
        self.assertEqual(set(groups["Feature"]), set(self.frame.columns))
        self.assertEqual(len(groups), len(self.frame.columns))

    def test_numerical_and_categorical_summaries_have_required_fields(self) -> None:
        numeric = numerical_summary(self.frame)
        categorical = categorical_summary(self.frame)
        self.assertIn("Median", numeric.columns)
        self.assertIn("Standard deviation", numeric.columns)
        self.assertIn("Most frequent category", categorical.columns)
        self.assertIn("Missing count", categorical.columns)

    def test_date_and_target_summaries_capture_basic_structure(self) -> None:
        date_result = date_understanding(self.frame)
        target = target_summary(self.frame).set_index("Target characteristic")["Value"]
        self.assertEqual(len(date_result.year_counts), 2)
        self.assertEqual(len(date_result.location_coverage), 2)
        self.assertEqual(target["Missing count"], 1)
        self.assertEqual(target["Labelled count"], 2)

    def test_range_checks_flag_cloud_value_above_documented_scale(self) -> None:
        ranges = basic_range_checks(self.frame).set_index("Feature")
        self.assertIn("documented 0–8", ranges.loc["Cloud9am", "Later-investigation flag"])

    def test_data_dictionary_is_complete(self) -> None:
        dictionary = data_dictionary(self.frame)
        self.assertEqual(list(dictionary["Feature name"]), list(self.frame.columns))
        self.assertEqual(
            set(dictionary.columns),
            {
                "Feature name",
                "Description",
                "Data type",
                "Logical type",
                "Unit / category meaning",
                "Role",
                "Basic data-quality note",
                "Possible preprocessing consideration",
            },
        )


if __name__ == "__main__":
    unittest.main()
