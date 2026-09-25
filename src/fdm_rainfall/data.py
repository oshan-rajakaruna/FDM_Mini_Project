"""Dataset loading utilities for the rainfall project."""

from __future__ import annotations

from pathlib import Path
from typing import TypeAlias

import pandas as pd


PathLike: TypeAlias = str | Path


class DatasetLoadError(RuntimeError):
    """Raised when the weather dataset cannot be loaded as a CSV file."""


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
