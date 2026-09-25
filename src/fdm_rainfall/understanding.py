"""Reusable helpers for T02 dataset understanding summaries."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


FEATURE_GROUPS: dict[str, tuple[str, ...]] = {
    "Date / Location": ("Date", "Location"),
    "Temperature": ("MinTemp", "MaxTemp", "Temp9am", "Temp3pm"),
    "Rain / evaporation / sunshine": ("Rainfall", "Evaporation", "Sunshine", "RainToday"),
    "Wind": (
        "WindGustDir",
        "WindGustSpeed",
        "WindDir9am",
        "WindDir3pm",
        "WindSpeed9am",
        "WindSpeed3pm",
    ),
    "Humidity": ("Humidity9am", "Humidity3pm"),
    "Pressure": ("Pressure9am", "Pressure3pm"),
    "Cloud": ("Cloud9am", "Cloud3pm"),
    "Target": ("RainTomorrow",),
}

LOGICAL_TYPES: dict[str, str] = {
    "Date": "date/time",
    "Location": "categorical nominal",
    "MinTemp": "numerical continuous",
    "MaxTemp": "numerical continuous",
    "Rainfall": "numerical continuous",
    "Evaporation": "numerical continuous",
    "Sunshine": "numerical continuous",
    "WindGustDir": "categorical nominal",
    "WindGustSpeed": "numerical continuous",
    "WindDir9am": "categorical nominal",
    "WindDir3pm": "categorical nominal",
    "WindSpeed9am": "numerical continuous",
    "WindSpeed3pm": "numerical continuous",
    "Humidity9am": "numerical continuous",
    "Humidity3pm": "numerical continuous",
    "Pressure9am": "numerical continuous",
    "Pressure3pm": "numerical continuous",
    "Cloud9am": "numerical discrete",
    "Cloud3pm": "numerical discrete",
    "Temp9am": "numerical continuous",
    "Temp3pm": "numerical continuous",
    "RainToday": "categorical binary",
    "RainTomorrow": "target",
}

NUMERICAL_COLUMNS = tuple(
    column
    for column, logical_type in LOGICAL_TYPES.items()
    if logical_type in {"numerical continuous", "numerical discrete"}
)

CATEGORICAL_COLUMNS = tuple(
    column
    for column, logical_type in LOGICAL_TYPES.items()
    if logical_type.startswith("categorical") or logical_type == "target"
)

RANGE_GROUPS = {
    "MinTemp": "Temperature",
    "MaxTemp": "Temperature",
    "Temp9am": "Temperature",
    "Temp3pm": "Temperature",
    "Humidity9am": "Humidity",
    "Humidity3pm": "Humidity",
    "Pressure9am": "Pressure",
    "Pressure3pm": "Pressure",
    "WindGustSpeed": "Wind speed",
    "WindSpeed9am": "Wind speed",
    "WindSpeed3pm": "Wind speed",
    "Rainfall": "Rainfall",
    "Evaporation": "Evaporation",
    "Sunshine": "Sunshine",
    "Cloud9am": "Cloud",
    "Cloud3pm": "Cloud",
}

UNITS = {
    "Date": "YYYY-MM-DD",
    "Location": "Australian weather-station location name",
    "MinTemp": "degrees Celsius (°C)",
    "MaxTemp": "degrees Celsius (°C)",
    "Rainfall": "millimetres (mm)",
    "Evaporation": "millimetres (mm), Class A pan evaporation",
    "Sunshine": "hours",
    "WindGustDir": "compass direction category",
    "WindGustSpeed": "kilometres per hour (km/h)",
    "WindDir9am": "compass direction category",
    "WindDir3pm": "compass direction category",
    "WindSpeed9am": "kilometres per hour (km/h)",
    "WindSpeed3pm": "kilometres per hour (km/h)",
    "Humidity9am": "percent (%)",
    "Humidity3pm": "percent (%)",
    "Pressure9am": "hectopascals (hPa), mean-sea-level pressure",
    "Pressure3pm": "hectopascals (hPa), mean-sea-level pressure",
    "Cloud9am": "oktas (eighths of sky covered; documented scale 0–8)",
    "Cloud3pm": "oktas (eighths of sky covered; documented scale 0–8)",
    "Temp9am": "degrees Celsius (°C)",
    "Temp3pm": "degrees Celsius (°C)",
    "RainToday": "No/Yes category",
    "RainTomorrow": "No/Yes category",
}

DESCRIPTIONS = {
    "Date": "Calendar date of the daily weather observation.",
    "Location": "Common name of the Australian weather-station location.",
    "MinTemp": "Minimum temperature recorded for the day.",
    "MaxTemp": "Maximum temperature recorded for the day.",
    "Rainfall": "Rainfall recorded for the day.",
    "Evaporation": "Class A pan evaporation in the 24 hours to 9am.",
    "Sunshine": "Duration of bright sunshine during the day.",
    "WindGustDir": "Direction of the strongest wind gust in the 24 hours to midnight.",
    "WindGustSpeed": "Speed of the strongest wind gust in the 24 hours to midnight.",
    "WindDir9am": "Wind direction at the 9am observation.",
    "WindDir3pm": "Wind direction at the 3pm observation.",
    "WindSpeed9am": "Wind speed averaged over the 10 minutes before 9am.",
    "WindSpeed3pm": "Wind speed averaged over the 10 minutes before 3pm.",
    "Humidity9am": "Relative humidity at 9am.",
    "Humidity3pm": "Relative humidity at 3pm.",
    "Pressure9am": "Atmospheric pressure reduced to mean sea level at 9am.",
    "Pressure3pm": "Atmospheric pressure reduced to mean sea level at 3pm.",
    "Cloud9am": "Fraction of the sky obscured by cloud at 9am.",
    "Cloud3pm": "Fraction of the sky obscured by cloud at 3pm.",
    "Temp9am": "Temperature at 9am.",
    "Temp3pm": "Temperature at 3pm.",
    "RainToday": "Binary indicator of whether the source definition's daily rainfall threshold was exceeded.",
    "RainTomorrow": "Target indicating whether rain was recorded on the following day.",
}

ROLES = {
    "Date": "temporal",
    "Location": "location",
    **{column: "predictor" for column in LOGICAL_TYPES if column not in {"Date", "Location", "RainTomorrow"}},
    "RainTomorrow": "target",
}


@dataclass(frozen=True)
class DateUnderstanding:
    """Structured date summaries for T02."""

    overview: pd.DataFrame
    year_counts: pd.DataFrame
    location_coverage: pd.DataFrame


def _require_known_columns(frame: pd.DataFrame) -> None:
    missing = [column for column in LOGICAL_TYPES if column not in frame.columns]
    if missing:
        raise ValueError(f"Data-understanding columns are missing: {', '.join(missing)}")


def dataset_overview(frame: pd.DataFrame) -> pd.DataFrame:
    """Return high-level characteristics for the daily observation dataset."""

    _require_known_columns(frame)
    parsed_dates = pd.to_datetime(frame["Date"], format="%Y-%m-%d", errors="coerce")
    rows: list[tuple[str, Any]] = [
        ("Dataset purpose", "Daily Australian weather observations for next-day rain prediction"),
        ("Rows", int(frame.shape[0])),
        ("Columns", int(frame.shape[1])),
        ("Minimum date", parsed_dates.min().date().isoformat()),
        ("Maximum date", parsed_dates.max().date().isoformat()),
        ("Locations", int(frame["Location"].nunique(dropna=True))),
        ("Target variable", "RainTomorrow"),
    ]
    return pd.DataFrame(rows, columns=["Characteristic", "Value"])


def column_inventory(frame: pd.DataFrame) -> pd.DataFrame:
    """Return required per-column type, completeness, and cardinality metrics."""

    _require_known_columns(frame)
    row_count = len(frame)
    rows = []
    for column in frame.columns:
        missing = int(frame[column].isna().sum())
        rows.append(
            {
                "Column": column,
                "Pandas dtype": str(frame[column].dtype),
                "Logical variable type": LOGICAL_TYPES[column],
                "Non-null values": int(frame[column].notna().sum()),
                "Missing values": missing,
                "Missing percentage": round((missing / row_count * 100) if row_count else 0.0, 4),
                "Unique non-null values": int(frame[column].nunique(dropna=True)),
            }
        )
    return pd.DataFrame(rows)


def feature_group_table() -> pd.DataFrame:
    """Return the documented thematic feature grouping."""

    return pd.DataFrame(
        [
            {"Feature group": group, "Feature": feature}
            for group, features in FEATURE_GROUPS.items()
            for feature in features
        ]
    )


def numerical_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Return descriptive statistics for all numerical variables."""

    _require_known_columns(frame)
    summary = frame.loc[:, NUMERICAL_COLUMNS].describe(percentiles=[0.25, 0.5, 0.75]).T
    summary = summary.rename(
        columns={
            "count": "Count",
            "mean": "Mean",
            "std": "Standard deviation",
            "min": "Minimum",
            "25%": "25th percentile",
            "50%": "Median",
            "75%": "75th percentile",
            "max": "Maximum",
        }
    )
    summary.index.name = "Feature"
    return summary.reset_index()


def categorical_frequencies(frame: pd.DataFrame) -> pd.DataFrame:
    """Return readable long-form frequencies for categorical variables."""

    _require_known_columns(frame)
    rows = []
    for column in CATEGORICAL_COLUMNS:
        counts = frame[column].value_counts(dropna=True)
        non_null = int(counts.sum())
        for category, count in counts.items():
            rows.append(
                {
                    "Feature": column,
                    "Category": str(category),
                    "Count": int(count),
                    "Percentage of non-null": round((count / non_null * 100) if non_null else 0.0, 4),
                }
            )
    return pd.DataFrame(rows)


def categorical_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Return compact categorical cardinality, mode, and missingness details."""

    _require_known_columns(frame)
    rows = []
    for column in CATEGORICAL_COLUMNS:
        counts = frame[column].value_counts(dropna=True)
        categories = sorted(str(value) for value in counts.index)
        category_display = (
            "See 02_categorical_frequencies.csv for 49 location values"
            if column == "Location"
            else " | ".join(categories)
        )
        rows.append(
            {
                "Feature": column,
                "Number of categories": len(categories),
                "Category values": category_display,
                "Most frequent category": str(counts.index[0]) if not counts.empty else "",
                "Most frequent count": int(counts.iloc[0]) if not counts.empty else 0,
                "Missing count": int(frame[column].isna().sum()),
            }
        )
    return pd.DataFrame(rows)


def date_understanding(frame: pd.DataFrame) -> DateUnderstanding:
    """Return safe date coverage and ordering summaries without splitting data."""

    _require_known_columns(frame)
    dates = pd.to_datetime(frame["Date"], format="%Y-%m-%d", errors="coerce")
    valid_dates = dates.dropna()
    if valid_dates.empty:
        raise ValueError("Date contains no valid YYYY-MM-DD values")

    dated = pd.DataFrame({"Location": frame["Location"], "ParsedDate": dates})
    within_location_ordered = dated.groupby("Location", sort=False)["ParsedDate"].apply(
        lambda values: values.is_monotonic_increasing
    )
    location_coverage = (
        dated.groupby("Location", dropna=False)["ParsedDate"]
        .agg(Start_date="min", End_date="max", Record_count="size", Unique_dates="nunique")
        .reset_index()
    )
    location_coverage.columns = ["Location", "Start date", "End date", "Record count", "Unique dates"]
    location_coverage["Start date"] = location_coverage["Start date"].dt.date.astype(str)
    location_coverage["End date"] = location_coverage["End date"].dt.date.astype(str)

    coverage_patterns = location_coverage[["Start date", "End date"]].drop_duplicates()
    all_same_coverage = len(coverage_patterns) == 1

    year_counts = (
        valid_dates.dt.year.value_counts().sort_index().rename_axis("Year").reset_index(name="Record count")
    )
    minimum = valid_dates.min()
    maximum = valid_dates.max()
    overview_rows: list[tuple[str, Any]] = [
        ("Minimum date", minimum.date().isoformat()),
        ("Maximum date", maximum.date().isoformat()),
        ("Calendar years represented", int(valid_dates.dt.year.nunique())),
        ("Elapsed coverage in years", round((maximum - minimum).days / 365.2425, 4)),
        ("Invalid or missing dates", int(dates.isna().sum())),
        ("Raw file globally date-ordered", bool(dates.is_monotonic_increasing)),
        (
            "Locations internally date-ordered",
            f"{int(within_location_ordered.sum())} of {len(within_location_ordered)}",
        ),
        ("All locations have the same start/end coverage", bool(all_same_coverage)),
        ("Distinct location coverage patterns", int(len(coverage_patterns))),
    ]
    return DateUnderstanding(
        overview=pd.DataFrame(overview_rows, columns=["Date characteristic", "Value"]),
        year_counts=year_counts,
        location_coverage=location_coverage,
    )


def target_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Return basic RainTomorrow type, classes, and completeness details."""

    _require_known_columns(frame)
    target = frame["RainTomorrow"]
    counts = target.value_counts(dropna=True)
    rows: list[tuple[str, Any]] = [
        ("Pandas dtype", str(target.dtype)),
        ("Classes", " | ".join(sorted(str(value) for value in counts.index))),
        ("No count", int(counts.get("No", 0))),
        ("Yes count", int(counts.get("Yes", 0))),
        ("Missing count", int(target.isna().sum())),
        ("Labelled count", int(target.notna().sum())),
    ]
    return pd.DataFrame(rows, columns=["Target characteristic", "Value"])


def _range_flag(column: str, minimum: float, maximum: float) -> str:
    if column.startswith("Cloud") and maximum > 8:
        return "Maximum exceeds the documented 0–8 clear-to-overcast scale; investigate meaning in T05."
    if column.startswith("Humidity") and minimum == 0:
        return "A 0% boundary observation occurs; verify context and frequency in later EDA/T05."
    if column == "Rainfall" and maximum >= 300:
        return "Very high daily maximum; retain and investigate distribution/context later."
    if column == "Evaporation" and maximum >= 100:
        return "Very high recorded maximum; retain and investigate distribution/context later."
    if column in {"WindGustSpeed", "WindSpeed9am", "WindSpeed3pm"} and maximum >= 100:
        return "High wind-speed maximum; retain and investigate distribution/context later."
    return "No basic range flag at T02; detailed assessment deferred."


def basic_range_checks(frame: pd.DataFrame) -> pd.DataFrame:
    """Return observed ranges with conservative later-investigation flags."""

    _require_known_columns(frame)
    rows = []
    for column, group in RANGE_GROUPS.items():
        values = frame[column].dropna()
        minimum = float(values.min())
        maximum = float(values.max())
        rows.append(
            {
                "Feature group": group,
                "Feature": column,
                "Unit / scale": UNITS[column],
                "Non-null count": int(values.size),
                "Missing count": int(frame[column].isna().sum()),
                "Observed minimum": minimum,
                "Observed maximum": maximum,
                "Later-investigation flag": _range_flag(column, minimum, maximum),
            }
        )
    return pd.DataFrame(rows)


def data_dictionary(frame: pd.DataFrame) -> pd.DataFrame:
    """Return a complete source-grounded dictionary for all dataset columns."""

    inventory = column_inventory(frame).set_index("Column")
    rows = []
    for column in frame.columns:
        info = inventory.loc[column]
        missing_note = (
            f"{int(info['Missing values']):,} missing "
            f"({float(info['Missing percentage']):.4f}%); "
            f"{int(info['Unique non-null values']):,} unique non-null values."
        )
        if column.startswith("Cloud") and frame[column].max(skipna=True) > 8:
            missing_note += " Observed maximum is 9, above the documented 0–8 scale; meaning is deferred."

        logical_type = LOGICAL_TYPES[column]
        if column == "Date":
            consideration = "Parse safely as datetime; preserve chronology for a later split strategy."
        elif column == "Location":
            consideration = "Treat as nominal; encoding and location-aware validation decisions are deferred."
        elif column == "RainTomorrow":
            consideration = "Keep as the target; handling of missing labels is deferred to preprocessing."
        elif logical_type.startswith("categorical"):
            consideration = "Preserve categories; missing-value handling and encoding are deferred."
        else:
            consideration = "Retain numeric values; missing-value and scaling decisions are deferred."

        rows.append(
            {
                "Feature name": column,
                "Description": DESCRIPTIONS[column],
                "Data type": str(info["Pandas dtype"]),
                "Logical type": logical_type,
                "Unit / category meaning": UNITS[column],
                "Role": ROLES[column],
                "Basic data-quality note": missing_note,
                "Possible preprocessing consideration": consideration,
            }
        )
    return pd.DataFrame(rows)


def render_data_dictionary_markdown(frame: pd.DataFrame) -> str:
    """Render the complete dictionary as an academic Markdown document."""

    dictionary = data_dictionary(frame)
    lines = [
        "# weatherAUS Data Dictionary",
        "",
        "This dictionary describes the 23 columns in `data/raw/weatherAUS.csv`.",
        "Observed data types and quality notes come from the local project file; feature",
        "definitions and units are grounded in the Rattle weatherAUS documentation and",
        "Australian Bureau of Meteorology Daily Weather Observations documentation.",
        "",
        "| " + " | ".join(dictionary.columns) + " |",
        "|" + "|".join(["---"] * len(dictionary.columns)) + "|",
    ]
    for row in dictionary.itertuples(index=False, name=None):
        cleaned = [str(value).replace("|", "\\|").replace("\n", " ") for value in row]
        lines.append("| " + " | ".join(cleaned) + " |")
    lines.extend(
        [
            "",
            "## Interpretation notes",
            "",
            "- Missingness is recorded descriptively only; analysis and treatment belong to T03/T07.",
            "- Observed extremes are retained. Any outlier or suspicious-value decisions belong to T05.",
            "- The source documentation describes cloud cover on a 0–8 okta scale; the local",
            "  file contains a maximum value of 9 in both cloud columns, which is flagged for",
            "  later investigation rather than labelled invalid here.",
            "- `RISK_MM` is absent from this project dataset, as verified in T01.",
            "",
            "## Definition sources",
            "",
            "- Rattle `weatherAUS` documentation: https://search.r-project.org/CRAN/refmans/rattle/html/weatherAUS.html",
            "- Australian Bureau of Meteorology Daily Weather Observations: https://www.bom.gov.au/climate/dwo/",
            "",
        ]
    )
    return "\n".join(lines)


def write_data_dictionary(path: str | Path, frame: pd.DataFrame) -> None:
    """Write the rendered data dictionary to a UTF-8 Markdown file."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_data_dictionary_markdown(frame), encoding="utf-8")
