"""Dataset loading and leakage-safe splitting utilities for the project."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TypeAlias

import pandas as pd


PathLike: TypeAlias = str | Path


class DatasetLoadError(RuntimeError):
    """Raised when the weather dataset cannot be loaded as a CSV file."""


@dataclass(frozen=True)
class ChronologicalSplit:
    """Three non-overlapping date-based subsets and their boundary summary."""

    train: pd.DataFrame
    validation: pd.DataFrame
    test: pd.DataFrame
    summary: pd.DataFrame

    @property
    def frames(self) -> dict[str, pd.DataFrame]:
        """Return the subsets in chronological order."""

        return {
            "Train": self.train,
            "Validation": self.validation,
            "Test": self.test,
        }


def load_weather_data(dataset_path: PathLike) -> pd.DataFrame:
    """Load the weather CSV without changing or cleaning its observations.

    The literal marker ``NA`` is interpreted as missing, consistent with
    pandas' default CSV missing-value handling. No rows or columns are removed,
    and the source file is opened read-only.
    """

    path = Path(dataset_path)
    if not path.is_file():
        raise FileNotFoundError(f"Weather dataset not found: {path}")

    try:
        return pd.read_csv(path, low_memory=False)
    except Exception as exc:  # pragma: no cover - depends on parser/IO failures
        raise DatasetLoadError(f"Could not load weather dataset: {path}") from exc


def _nearest_boundary_position(
    cumulative_rows: pd.Series,
    target_rows: float,
    minimum_position: int,
    maximum_position: int,
) -> int:
    """Return the valid unique-date position nearest a cumulative row target."""

    candidates = cumulative_rows.iloc[minimum_position : maximum_position + 1]
    return int((candidates - target_rows).abs().to_numpy().argmin() + minimum_position)


def _split_summary(
    frames: dict[str, pd.DataFrame],
    date_column: str,
    target_column: str,
) -> pd.DataFrame:
    """Build a compact boundary and target-distribution summary."""

    total_rows = sum(len(part) for part in frames.values())
    rows: list[dict[str, object]] = []
    for split_name, part in frames.items():
        target_counts = part[target_column].value_counts()
        yes_count = int(target_counts.get("Yes", 0))
        no_count = int(target_counts.get("No", 0))
        rows.append(
            {
                "Split": split_name,
                "First date": part[date_column].min().date().isoformat(),
                "Last date": part[date_column].max().date().isoformat(),
                "Rows": int(len(part)),
                "Percentage of labelled rows": round(len(part) / total_rows * 100, 6),
                "Unique dates": int(part[date_column].nunique()),
                "Locations": int(part["Location"].nunique()) if "Location" in part else 0,
                f"{target_column} No count": no_count,
                f"{target_column} Yes count": yes_count,
                "Yes percentage": round(yes_count / len(part) * 100, 6),
                "Missing target count": int(part[target_column].isna().sum()),
            }
        )
    return pd.DataFrame(rows)


def chronological_train_validation_test_split(
    frame: pd.DataFrame,
    date_column: str = "Date",
    target_column: str = "RainTomorrow",
    require_non_missing_target: bool = True,
    train_fraction: float = 0.70,
    validation_fraction: float = 0.15,
) -> ChronologicalSplit:
    """Split rows by whole calendar dates without modifying ``frame``.

    Boundaries are selected from ordered unique dates. The first boundary is
    nearest to the requested cumulative training-row proportion, and the
    second is nearest to the requested cumulative train-plus-validation
    proportion. Consequently, identical dates are never divided between
    subsets and the realised percentages may differ slightly from the targets.

    When ``require_non_missing_target`` is true, an in-memory labelled view is
    created before choosing boundaries. The original frame and raw CSV remain
    unchanged.
    """

    required_columns = {date_column, target_column}
    missing_columns = sorted(required_columns.difference(frame.columns))
    if missing_columns:
        raise ValueError(f"Required split columns are missing: {', '.join(missing_columns)}")
    if not frame.index.is_unique:
        raise ValueError("Input index must be unique so row-overlap checks remain reliable")
    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction must be between 0 and 1")
    if not 0 < validation_fraction < 1:
        raise ValueError("validation_fraction must be between 0 and 1")
    if train_fraction + validation_fraction >= 1:
        raise ValueError("train_fraction + validation_fraction must be less than 1")

    working = frame.copy(deep=True)
    if require_non_missing_target:
        working = working.loc[working[target_column].notna()].copy()
    if working.empty:
        raise ValueError("No rows remain for chronological splitting")

    parsed_dates = pd.to_datetime(working[date_column], format="%Y-%m-%d", errors="coerce")
    invalid_date_count = int(parsed_dates.isna().sum())
    if invalid_date_count:
        raise ValueError(
            f"{date_column} contains {invalid_date_count} invalid or missing values in the split population"
        )

    working[date_column] = parsed_dates
    working = working.sort_values(date_column, kind="mergesort")
    rows_per_date = working.groupby(date_column, sort=True).size()
    if len(rows_per_date) < 3:
        raise ValueError("At least three unique dates are required for three chronological subsets")

    cumulative_rows = rows_per_date.cumsum()
    total_rows = len(working)
    train_position = _nearest_boundary_position(
        cumulative_rows,
        total_rows * train_fraction,
        minimum_position=0,
        maximum_position=len(rows_per_date) - 3,
    )
    validation_position = _nearest_boundary_position(
        cumulative_rows,
        total_rows * (train_fraction + validation_fraction),
        minimum_position=train_position + 1,
        maximum_position=len(rows_per_date) - 2,
    )

    train_end = rows_per_date.index[train_position]
    validation_end = rows_per_date.index[validation_position]
    train = working.loc[working[date_column] <= train_end].copy()
    validation = working.loc[
        (working[date_column] > train_end) & (working[date_column] <= validation_end)
    ].copy()
    test = working.loc[working[date_column] > validation_end].copy()
    frames = {"Train": train, "Validation": validation, "Test": test}

    return ChronologicalSplit(
        train=train,
        validation=validation,
        test=test,
        summary=_split_summary(frames, date_column, target_column),
    )


def location_split_tables(
    split: ChronologicalSplit,
    location_column: str = "Location",
    date_column: str = "Date",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return location coverage flags and per-split observation counts."""

    for part in split.frames.values():
        missing = {location_column, date_column}.difference(part.columns)
        if missing:
            raise ValueError(f"Location coverage columns are missing: {', '.join(sorted(missing))}")

    combined = pd.concat(split.frames.values(), axis=0)
    date_coverage = combined.groupby(location_column)[date_column].agg(["min", "max"])
    counts = pd.DataFrame(
        {
            split_name: part.groupby(location_column).size()
            for split_name, part in split.frames.items()
        }
    ).fillna(0).astype(int)
    counts.index.name = location_column
    counts = counts.reset_index()

    coverage = date_coverage.rename(columns={"min": "First labelled date", "max": "Last labelled date"})
    for split_name in split.frames:
        coverage[f"Present in {split_name}"] = coverage.index.isin(
            split.frames[split_name][location_column].dropna().unique()
        )
    coverage["Present in all three"] = coverage[
        ["Present in Train", "Present in Validation", "Present in Test"]
    ].all(axis=1)
    coverage["Begins after labelled population starts"] = (
        coverage["First labelled date"] > combined[date_column].min()
    )
    coverage["Ends before labelled population ends"] = (
        coverage["Last labelled date"] < combined[date_column].max()
    )
    coverage["First labelled date"] = coverage["First labelled date"].dt.date.astype(str)
    coverage["Last labelled date"] = coverage["Last labelled date"].dt.date.astype(str)
    coverage = coverage.reset_index()
    return coverage, counts
