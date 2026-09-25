"""Reusable, non-mutating checks for the weatherAUS dataset."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd


EXPECTED_COLUMNS = (
    "Date",
    "Location",
    "MinTemp",
    "MaxTemp",
    "Rainfall",
    "Evaporation",
    "Sunshine",
    "WindGustDir",
    "WindGustSpeed",
    "WindDir9am",
    "WindDir3pm",
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
    "RainToday",
    "RainTomorrow",
)

PROPOSAL_CLAIMS = (
    ("Total rows", 145_460),
    ("Total columns", 23),
    ("Unique locations", 49),
    ("Labelled RainTomorrow rows", 142_193),
    ("Missing RainTomorrow rows", 3_267),
    ("Date range", "2007-11-01 to 2017-06-25"),
    ("RISK_MM exists", False),
)


@dataclass(frozen=True)
class DatasetVerification:
    """Structured results from the required T01 dataset checks."""

    row_count: int
    column_count: int
    column_names: tuple[str, ...]
    data_types: dict[str, str]
    date_min: str
    date_max: str
    invalid_date_count: int
    unique_location_count: int
    rain_tomorrow_exists: bool
    rain_tomorrow_values: tuple[str, ...]
    rain_tomorrow_class_counts: dict[str, int]
    rain_tomorrow_missing_count: int
    rain_tomorrow_labelled_count: int
    exact_duplicate_rows: int
    duplicate_date_location_combinations: int
    duplicate_date_location_rows: int
    risk_mm_exists: bool
    unexpected_columns: tuple[str, ...]
    missing_expected_columns: tuple[str, ...]

    @property
    def date_range(self) -> str:
        """Return the observed inclusive date range."""

        return f"{self.date_min} to {self.date_max}"

    def proposal_comparison(self) -> pd.DataFrame:
        """Return a transparent expected-versus-actual proposal comparison."""

        actual_values: dict[str, Any] = {
            "Total rows": self.row_count,
            "Total columns": self.column_count,
            "Unique locations": self.unique_location_count,
            "Labelled RainTomorrow rows": self.rain_tomorrow_labelled_count,
            "Missing RainTomorrow rows": self.rain_tomorrow_missing_count,
            "Date range": self.date_range,
            "RISK_MM exists": self.risk_mm_exists,
        }

        comments = {
            "Total rows": "Compares all loaded observations.",
            "Total columns": "Compares the complete CSV header width.",
            "Unique locations": "Counts distinct non-missing Location values.",
            "Labelled RainTomorrow rows": "Counts non-missing target values.",
            "Missing RainTomorrow rows": "Counts missing target values.",
            "Date range": "Uses parsed valid dates and inclusive endpoints.",
            "RISK_MM exists": "Leakage-prone RISK_MM is expected to be absent.",
        }

        rows = []
        for claim, expected in PROPOSAL_CLAIMS:
            actual = actual_values[claim]
            matches = actual == expected
            rows.append(
                {
                    "Claim": claim,
                    "Expected value": expected,
                    "Actual dataset value": actual,
                    "Match / Mismatch": "Match" if matches else "Mismatch",
                    "Comment": comments[claim],
                }
            )
        return pd.DataFrame(rows)

    def summary_table(self) -> pd.DataFrame:
        """Return the required dataset findings as a two-column table."""

        findings: list[tuple[str, Any]] = [
            ("Dataset loaded successfully", True),
            ("Total rows", self.row_count),
            ("Total columns", self.column_count),
            ("Date minimum", self.date_min),
            ("Date maximum", self.date_max),
            ("Invalid or missing dates", self.invalid_date_count),
            ("Unique Locations", self.unique_location_count),
            ("RainTomorrow exists", self.rain_tomorrow_exists),
            ("RainTomorrow unique non-missing values", ", ".join(self.rain_tomorrow_values)),
            ("RainTomorrow missing count", self.rain_tomorrow_missing_count),
            ("Labelled RainTomorrow rows", self.rain_tomorrow_labelled_count),
            ("Exact duplicate rows", self.exact_duplicate_rows),
            ("Duplicate Date + Location combinations", self.duplicate_date_location_combinations),
            ("Rows in duplicate Date + Location combinations", self.duplicate_date_location_rows),
            ("RISK_MM exists", self.risk_mm_exists),
            ("Unexpected extra columns", ", ".join(self.unexpected_columns) or "None"),
            ("Missing expected columns", ", ".join(self.missing_expected_columns) or "None"),
        ]
        return pd.DataFrame(findings, columns=["Verification item", "Actual dataset value"])

    def column_schema_table(self) -> pd.DataFrame:
        """Return exact column order and pandas-inferred data types."""

        return pd.DataFrame(
            {
                "Position": range(1, len(self.column_names) + 1),
                "Column": self.column_names,
                "Pandas dtype": [self.data_types[column] for column in self.column_names],
            }
        )

    def target_counts_table(self) -> pd.DataFrame:
        """Return RainTomorrow class and missing counts."""

        rows = [
            {"RainTomorrow value": value, "Count": count}
            for value, count in self.rain_tomorrow_class_counts.items()
        ]
        rows.append({"RainTomorrow value": "<MISSING>", "Count": self.rain_tomorrow_missing_count})
        return pd.DataFrame(rows)


def _require_columns(frame: pd.DataFrame, columns: tuple[str, ...]) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"Required verification columns are missing: {', '.join(missing)}")


def verify_weather_dataset(frame: pd.DataFrame) -> DatasetVerification:
    """Run the T01 checks without mutating the supplied DataFrame."""

    _require_columns(frame, ("Date", "Location", "RainTomorrow"))

    parsed_dates = pd.to_datetime(frame["Date"], format="%Y-%m-%d", errors="coerce")
    valid_dates = parsed_dates.dropna()
    if valid_dates.empty:
        raise ValueError("Date contains no valid YYYY-MM-DD values")

    target = frame["RainTomorrow"]
    target_counts = target.value_counts(dropna=True)

    duplicate_key_mask = frame.duplicated(subset=["Date", "Location"], keep=False)
    duplicate_keys = frame.loc[duplicate_key_mask, ["Date", "Location"]].drop_duplicates()

    actual_columns = tuple(str(column) for column in frame.columns)
    expected_set = set(EXPECTED_COLUMNS)
    actual_set = set(actual_columns)

    return DatasetVerification(
        row_count=int(frame.shape[0]),
        column_count=int(frame.shape[1]),
        column_names=actual_columns,
        data_types={str(column): str(dtype) for column, dtype in frame.dtypes.items()},
        date_min=valid_dates.min().date().isoformat(),
        date_max=valid_dates.max().date().isoformat(),
        invalid_date_count=int(parsed_dates.isna().sum()),
        unique_location_count=int(frame["Location"].nunique(dropna=True)),
        rain_tomorrow_exists="RainTomorrow" in frame.columns,
        rain_tomorrow_values=tuple(sorted(str(value) for value in target.dropna().unique())),
        rain_tomorrow_class_counts={str(value): int(count) for value, count in target_counts.items()},
        rain_tomorrow_missing_count=int(target.isna().sum()),
        rain_tomorrow_labelled_count=int(target.notna().sum()),
        exact_duplicate_rows=int(frame.duplicated(keep="first").sum()),
        duplicate_date_location_combinations=int(len(duplicate_keys)),
        duplicate_date_location_rows=int(duplicate_key_mask.sum()),
        risk_mm_exists="RISK_MM" in frame.columns,
        unexpected_columns=tuple(column for column in actual_columns if column not in expected_set),
        missing_expected_columns=tuple(column for column in EXPECTED_COLUMNS if column not in actual_set),
    )
