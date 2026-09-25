"""Tests for T06 chronological splitting and leakage validation."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from fdm_rainfall.data import (  # noqa: E402
    chronological_train_validation_test_split,
    load_weather_data,
    location_split_tables,
)
from fdm_rainfall.validation import (  # noqa: E402
    leakage_risk_register,
    validate_chronological_split,
)


def sample_frame() -> pd.DataFrame:
    """Return shuffled station-days with one unlabelled row."""

    rows: list[dict[str, object]] = []
    source_index = 100
    for day in range(1, 13):
        for location in ("A", "B"):
            rows.append(
                {
                    "Date": f"2020-01-{day:02d}",
                    "Location": location,
                    "Feature": float(day),
                    "RainTomorrow": None if day == 6 and location == "B" else ("Yes" if day % 4 == 0 else "No"),
                }
            )
            source_index += 1
    frame = pd.DataFrame(rows, index=range(100, 124))
    return frame.sample(frac=1, random_state=42)


class ChronologicalSplitTests(unittest.TestCase):
    def setUp(self) -> None:
        self.frame = sample_frame()

    def test_split_preserves_input_and_filters_target_in_memory(self) -> None:
        before = self.frame.copy(deep=True)

        split = chronological_train_validation_test_split(self.frame)

        pd.testing.assert_frame_equal(self.frame, before)
        self.assertEqual(sum(len(part) for part in split.frames.values()), 23)
        self.assertTrue(all(part["RainTomorrow"].notna().all() for part in split.frames.values()))
        self.assertTrue(all(pd.api.types.is_datetime64_any_dtype(part["Date"]) for part in split.frames.values()))

    def test_split_keeps_dates_whole_and_boundaries_ordered(self) -> None:
        split = chronological_train_validation_test_split(self.frame)
        date_sets = {name: set(part["Date"]) for name, part in split.frames.items()}

        self.assertFalse(date_sets["Train"] & date_sets["Validation"])
        self.assertFalse(date_sets["Train"] & date_sets["Test"])
        self.assertFalse(date_sets["Validation"] & date_sets["Test"])
        self.assertLess(split.train["Date"].max(), split.validation["Date"].min())
        self.assertLess(split.validation["Date"].max(), split.test["Date"].min())

    def test_split_validation_reports_all_checks_passed(self) -> None:
        split = chronological_train_validation_test_split(self.frame)
        result = validate_chronological_split(
            split.train,
            split.validation,
            split.test,
            labelled_population_size=23,
        )

        self.assertEqual(len(result), 9)
        self.assertEqual(set(result["Result"]), {"PASS"})

    def test_split_validation_detects_source_index_overlap(self) -> None:
        split = chronological_train_validation_test_split(self.frame)
        validation = split.validation.copy()
        validation.index = [split.train.index[0], *list(validation.index[1:])]

        result = validate_chronological_split(
            split.train,
            validation,
            split.test,
            labelled_population_size=23,
        ).set_index("Check")

        self.assertEqual(result.loc["No source-row index overlap", "Result"], "FAIL")

    def test_invalid_dates_and_duplicate_indices_are_rejected(self) -> None:
        invalid_date = self.frame.copy()
        invalid_date.iloc[0, invalid_date.columns.get_loc("Date")] = "not-a-date"
        with self.assertRaisesRegex(ValueError, "invalid or missing"):
            chronological_train_validation_test_split(invalid_date)

        duplicate_index = self.frame.copy()
        duplicate_index.index = [0] * len(duplicate_index)
        with self.assertRaisesRegex(ValueError, "index must be unique"):
            chronological_train_validation_test_split(duplicate_index)

    def test_location_tables_report_subset_presence_and_counts(self) -> None:
        split = chronological_train_validation_test_split(self.frame)
        coverage, counts = location_split_tables(split)

        self.assertEqual(set(coverage["Location"]), {"A", "B"})
        self.assertEqual(set(counts["Location"]), {"A", "B"})
        self.assertEqual(int(counts[["Train", "Validation", "Test"]].to_numpy().sum()), 23)

    def test_leakage_register_contains_required_risks_and_future_controls(self) -> None:
        register = leakage_risk_register()

        self.assertEqual(len(register), 10)
        self.assertIn("Temporal leakage", set(register["Risk"]))
        self.assertIn("Test-set reuse / tuning leakage", set(register["Risk"]))
        self.assertEqual(
            register.loc[register["Risk"] == "Imputation leakage", "Status"].item(),
            "Planned",
        )

    def test_actual_dataset_split_reconciles_to_expected_labelled_population(self) -> None:
        frame = load_weather_data(PROJECT_ROOT / "data" / "raw" / "weatherAUS.csv")
        split = chronological_train_validation_test_split(frame)
        result = validate_chronological_split(
            split.train,
            split.validation,
            split.test,
            labelled_population_size=142_193,
        )

        self.assertEqual(set(result["Result"]), {"PASS"})
        self.assertEqual(split.summary["Rows"].tolist(), [99_546, 21_342, 21_305])
        self.assertEqual(split.summary["Last date"].tolist()[:2], ["2015-01-12", "2016-04-08"])


if __name__ == "__main__":
    unittest.main()
