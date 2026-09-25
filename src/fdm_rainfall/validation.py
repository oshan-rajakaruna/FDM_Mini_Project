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


def validate_chronological_split(
    train: pd.DataFrame,
    validation: pd.DataFrame,
    test: pd.DataFrame,
    labelled_population_size: int,
    date_column: str = "Date",
    target_column: str = "RainTomorrow",
) -> pd.DataFrame:
    """Return explicit PASS/FAIL checks for a supervised chronological split."""

    frames = {"Train": train, "Validation": validation, "Test": test}
    required_present = all(
        date_column in part.columns and target_column in part.columns for part in frames.values()
    )
    non_empty = all(not part.empty for part in frames.values())

    index_sets = {name: set(part.index) for name, part in frames.items()}
    no_index_overlap = (
        all(part.index.is_unique for part in frames.values())
        and not index_sets["Train"].intersection(index_sets["Validation"])
        and not index_sets["Train"].intersection(index_sets["Test"])
        and not index_sets["Validation"].intersection(index_sets["Test"])
    )

    parsed_dates: dict[str, pd.Series] = {}
    valid_dates = required_present
    if required_present:
        for name, part in frames.items():
            parsed = pd.to_datetime(part[date_column], errors="coerce")
            parsed_dates[name] = parsed
            valid_dates = valid_dates and bool(parsed.notna().all())

    no_date_overlap = False
    ordered_boundaries = False
    if valid_dates and non_empty:
        date_sets = {name: set(values) for name, values in parsed_dates.items()}
        no_date_overlap = bool(
            not date_sets["Train"].intersection(date_sets["Validation"])
            and not date_sets["Train"].intersection(date_sets["Test"])
            and not date_sets["Validation"].intersection(date_sets["Test"])
        )
        ordered_boundaries = bool(
            parsed_dates["Train"].max() < parsed_dates["Validation"].min()
            and parsed_dates["Validation"].max() < parsed_dates["Test"].min()
        )

    split_rows = sum(len(part) for part in frames.values())
    target_missing = (
        sum(int(part[target_column].isna().sum()) for part in frames.values())
        if required_present
        else -1
    )
    risk_mm_absent = all("RISK_MM" not in part.columns for part in frames.values())

    checks = [
        (
            "Train, validation and test are non-empty",
            non_empty,
            ", ".join(f"{name}={len(part)}" for name, part in frames.items()),
        ),
        (
            "Date values parse successfully",
            valid_dates,
            "All split dates must be valid before temporal comparisons.",
        ),
        (
            "No source-row index overlap",
            no_index_overlap,
            "Each labelled source index must occur in exactly one subset.",
        ),
        (
            "No calendar-date overlap",
            no_date_overlap,
            "A calendar date must not occur in more than one subset.",
        ),
        (
            "Chronological boundaries are strictly ordered",
            ordered_boundaries,
            "max(Train) < min(Validation) and max(Validation) < min(Test).",
        ),
        (
            "Split rows equal labelled population",
            split_rows == labelled_population_size,
            f"Split rows={split_rows}; labelled population={labelled_population_size}.",
        ),
        (
            "RainTomorrow exists in every split",
            required_present,
            "The target is retained for later supervised modelling.",
        ),
        (
            "RainTomorrow has no missing values in supervised splits",
            target_missing == 0,
            f"Missing target values across splits={target_missing}.",
        ),
        (
            "RISK_MM is absent from every split",
            risk_mm_absent,
            "RISK_MM would directly reveal next-day rainfall and cause target leakage.",
        ),
    ]
    return pd.DataFrame(
        [
            {
                "Check": check,
                "Result": "PASS" if passed else "FAIL",
                "Details": details,
            }
            for check, passed, details in checks
        ]
    )


def leakage_risk_register() -> pd.DataFrame:
    """Return T06 leakage controls, separating current and future safeguards."""

    rows = [
        (
            "Target leakage",
            "RainTomorrow included among predictors",
            "The model would be given the answer it is meant to predict.",
            "Explicitly exclude RainTomorrow from the future predictor matrix.",
            "T07/later",
            "Planned",
        ),
        (
            "RISK_MM leakage",
            "RISK_MM contains next-day rainfall amount",
            "Near-direct target disclosure would produce unrealistically strong results.",
            "Verify RISK_MM is absent and reject it if encountered.",
            "T01 and T06",
            "Implemented now",
        ),
        (
            "Imputation leakage",
            "Means, medians, modes, or categorical rules learned from all dates",
            "Validation/test information would influence training inputs.",
            "Fit numerical and categorical imputation rules on Train only.",
            "T07",
            "Planned",
        ),
        (
            "Encoding leakage",
            "Categories or encoders learned from validation/test rows",
            "Future category information would shape the training representation.",
            "Fit encoders on Train only; define unknown-category handling.",
            "T07",
            "Planned",
        ),
        (
            "Scaling leakage",
            "Scaling statistics calculated across all three subsets",
            "Future distributions would influence transformed training values.",
            "Fit scalers on Train only and apply unchanged to later subsets.",
            "T07",
            "Planned",
        ),
        (
            "Feature-selection leakage",
            "Selecting predictors using validation/test outcomes",
            "Reported performance would be optimistically biased.",
            "Select features within Train/development procedures only.",
            "T07/later",
            "Planned",
        ),
        (
            "Resampling leakage",
            "Class balancing before the split or across validation/test rows",
            "Synthetic or duplicated information could cross subset boundaries.",
            "Apply any class balancing to Train only after splitting.",
            "Later modelling",
            "Planned",
        ),
        (
            "Temporal leakage",
            "Random rows place later weather in development data and nearby station-days across subsets",
            "Evaluation would not represent prediction on unseen future dates.",
            "Use whole-date chronological Train/Validation/Test boundaries.",
            "T06",
            "Implemented now",
        ),
        (
            "Future-derived feature leakage",
            "Tomorrow's measurements, future rainfall/stations, or future-inclusive aggregates",
            "Predictors would contain information unavailable on the observation date.",
            "Require every engineered feature to use observation-date-or-earlier information only.",
            "T08",
            "Planned",
        ),
        (
            "Test-set reuse / tuning leakage",
            "Repeatedly choosing models or probability thresholds from Test results",
            "The Test set would cease to represent an independent final assessment.",
            "Fit thresholds within a training-only development procedure; never tune on Test.",
            "Later modelling",
            "Planned",
        ),
    ]
    return pd.DataFrame(
        rows,
        columns=[
            "Risk",
            "Example in this project",
            "Potential consequence",
            "Control / prevention",
            "Stage where controlled",
            "Status",
        ],
    )
