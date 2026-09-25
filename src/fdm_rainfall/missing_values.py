"""Reusable descriptive helpers for T03 missing-value analysis."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any

import pandas as pd


IMPORTANT_LOCATION_FEATURES = (
    "Sunshine",
    "Evaporation",
    "Cloud9am",
    "Cloud3pm",
    "Pressure9am",
    "Pressure3pm",
    "WindDir9am",
    "WindGustDir",
    "WindGustSpeed",
)

MAJOR_STRUCTURAL_FEATURES = ("Sunshine", "Evaporation", "Cloud9am", "Cloud3pm")

WIND_FEATURES = (
    "WindGustDir",
    "WindGustSpeed",
    "WindDir9am",
    "WindDir3pm",
    "WindSpeed9am",
    "WindSpeed3pm",
)

PROPOSAL_MISSING_COUNTS = {
    "Sunshine": 69_835,
    "Evaporation": 62_790,
    "Cloud3pm": 59_358,
    "Cloud9am": 55_888,
    "Pressure9am": 15_065,
    "Pressure3pm": 15_028,
    "WindDir9am": 10_566,
    "WindGustDir": 10_326,
    "WindGustSpeed": 10_263,
}


@dataclass(frozen=True)
class RowMissingnessAnalysis:
    """Row-level missingness overview and distribution."""

    overview: pd.DataFrame
    distribution: pd.DataFrame


@dataclass(frozen=True)
class TargetMissingnessAnalysis:
    """Target missingness overview, location pattern, and yearly pattern."""

    overview: pd.DataFrame
    by_location: pd.DataFrame
    by_year: pd.DataFrame


def _severity(percentage: float) -> str:
    if percentage == 0:
        return "No missingness"
    if percentage < 5:
        return "Low missingness"
    if percentage < 20:
        return "Moderate missingness"
    return "High missingness"


def missing_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Return per-column missingness sorted from highest to lowest."""

    row_count = len(frame)
    rows = []
    for column in frame.columns:
        missing = int(frame[column].isna().sum())
        percentage = (missing / row_count * 100) if row_count else 0.0
        rows.append(
            {
                "Feature": str(column),
                "Missing count": missing,
                "Missing percentage": round(percentage, 4),
                "Non-missing count": int(frame[column].notna().sum()),
                "Descriptive severity": _severity(percentage),
            }
        )
    return (
        pd.DataFrame(rows)
        .sort_values(["Missing percentage", "Feature"], ascending=[False, True])
        .reset_index(drop=True)
    )


def row_missingness(frame: pd.DataFrame, very_high_threshold: int = 10) -> RowMissingnessAnalysis:
    """Summarize missing-field counts per row without dropping observations."""

    if very_high_threshold < 1 or very_high_threshold > frame.shape[1]:
        raise ValueError("very_high_threshold must be between 1 and the column count")

    missing_per_row = frame.isna().sum(axis=1)
    distribution = (
        missing_per_row.value_counts()
        .sort_index()
        .rename_axis("Missing fields per row")
        .reset_index(name="Row count")
    )
    distribution["Row percentage"] = (
        distribution["Row count"] / len(frame) * 100 if len(frame) else 0.0
    ).round(4)
    any_missing = int((missing_per_row > 0).sum())
    very_high = int((missing_per_row >= very_high_threshold).sum())
    overview_rows: list[tuple[str, Any]] = [
        ("Total rows", int(len(frame))),
        ("Rows with at least one missing value", any_missing),
        ("Rows with at least one missing value (%)", round(any_missing / len(frame) * 100, 4) if len(frame) else 0.0),
        ("Maximum missing fields in one row", int(missing_per_row.max()) if len(frame) else 0),
        ("Very-high threshold (missing fields)", very_high_threshold),
        ("Rows meeting very-high threshold", very_high),
        ("Rows meeting very-high threshold (%)", round(very_high / len(frame) * 100, 4) if len(frame) else 0.0),
    ]
    return RowMissingnessAnalysis(
        overview=pd.DataFrame(overview_rows, columns=["Row-missingness metric", "Value"]),
        distribution=distribution,
    )


def location_missingness(
    frame: pd.DataFrame,
    features: tuple[str, ...] = IMPORTANT_LOCATION_FEATURES,
) -> pd.DataFrame:
    """Return long-form missingness by Location for important features."""

    required = {"Location", *features}
    missing_columns = required - set(frame.columns)
    if missing_columns:
        raise ValueError(f"Missing location-analysis columns: {', '.join(sorted(missing_columns))}")

    rows = []
    for location, group in frame.groupby("Location", sort=True, dropna=False):
        total = len(group)
        for feature in features:
            missing = int(group[feature].isna().sum())
            percentage = missing / total * 100 if total else 0.0
            if percentage == 100:
                coverage = "Complete absence"
            elif percentage <= 5:
                coverage = "Good coverage"
            else:
                coverage = "Partial missingness"
            rows.append(
                {
                    "Location": str(location),
                    "Feature": feature,
                    "Record count": int(total),
                    "Missing count": missing,
                    "Missing percentage": round(percentage, 4),
                    "Non-missing count": int(total - missing),
                    "Coverage classification": coverage,
                }
            )
    return pd.DataFrame(rows)


def temporal_missingness(
    frame: pd.DataFrame,
    features: tuple[str, ...] = IMPORTANT_LOCATION_FEATURES,
) -> pd.DataFrame:
    """Return missingness by calendar year and month-of-year."""

    required = {"Date", *features}
    missing_columns = required - set(frame.columns)
    if missing_columns:
        raise ValueError(f"Missing temporal-analysis columns: {', '.join(sorted(missing_columns))}")

    dates = pd.to_datetime(frame["Date"], format="%Y-%m-%d", errors="coerce")
    working = frame.loc[dates.notna(), list(features)].copy()
    working["Year"] = dates.loc[dates.notna()].dt.year.to_numpy()
    working["Month"] = dates.loc[dates.notna()].dt.month.to_numpy()

    rows = []
    for period_type, period_column in (("Year", "Year"), ("Month of year", "Month")):
        for period, group in working.groupby(period_column, sort=True):
            total = len(group)
            for feature in features:
                missing = int(group[feature].isna().sum())
                rows.append(
                    {
                        "Period type": period_type,
                        "Period": int(period),
                        "Feature": feature,
                        "Record count": int(total),
                        "Missing count": missing,
                        "Missing percentage": round(missing / total * 100 if total else 0.0, 4),
                        "Non-missing count": int(total - missing),
                    }
                )
    return pd.DataFrame(rows)


def location_year_missingness(
    frame: pd.DataFrame,
    features: tuple[str, ...] = IMPORTANT_LOCATION_FEATURES,
) -> pd.DataFrame:
    """Return within-location yearly missingness to separate time from station mix."""

    required = {"Date", "Location", *features}
    missing_columns = required - set(frame.columns)
    if missing_columns:
        raise ValueError(f"Missing location-year columns: {', '.join(sorted(missing_columns))}")

    dates = pd.to_datetime(frame["Date"], format="%Y-%m-%d", errors="coerce")
    working = frame.loc[dates.notna(), ["Location", *features]].copy()
    working["Year"] = dates.loc[dates.notna()].dt.year.to_numpy()
    rows = []
    for (location, year), group in working.groupby(["Location", "Year"], sort=True):
        total = len(group)
        for feature in features:
            missing = int(group[feature].isna().sum())
            rows.append(
                {
                    "Location": str(location),
                    "Year": int(year),
                    "Feature": feature,
                    "Record count": int(total),
                    "Missing count": missing,
                    "Missing percentage": round(missing / total * 100 if total else 0.0, 4),
                }
            )
    return pd.DataFrame(rows)


def structural_missingness_summary(
    frame: pd.DataFrame,
    location_table: pd.DataFrame | None = None,
    temporal_table: pd.DataFrame | None = None,
    location_year_table: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Return evidence and a cautious provisional pattern label by feature."""

    location_table = location_table if location_table is not None else location_missingness(frame)
    temporal_table = temporal_table if temporal_table is not None else temporal_missingness(frame)
    location_year_table = (
        location_year_table
        if location_year_table is not None
        else location_year_missingness(frame)
    )
    overall = missing_summary(frame).set_index("Feature")
    yearly = temporal_table.query("`Period type` == 'Year'")

    rows = []
    for feature in IMPORTANT_LOCATION_FEATURES:
        station = location_table[location_table["Feature"] == feature]
        feature_years = yearly[yearly["Feature"] == feature]
        feature_location_years = location_year_table[location_year_table["Feature"] == feature]
        complete_absence = int((station["Coverage classification"] == "Complete absence").sum())
        partial = int((station["Coverage classification"] == "Partial missingness").sum())
        good = int((station["Coverage classification"] == "Good coverage").sum())
        full = int((station["Missing count"] == 0).sum())
        station_spread = float(station["Missing percentage"].max() - station["Missing percentage"].min())
        year_spread = float(feature_years["Missing percentage"].max() - feature_years["Missing percentage"].min())
        within_station_spreads = feature_location_years.groupby("Location")["Missing percentage"].agg(
            lambda values: float(values.max() - values.min())
        )
        changing_locations = int((within_station_spreads >= 10).sum())

        station_dependent = complete_absence > 0 or station_spread >= 50
        time_dependent = changing_locations >= 5
        if station_dependent and time_dependent:
            provisional = "Likely both station and time dependent"
        elif station_dependent:
            provisional = "Likely structural / station dependent"
        elif time_dependent:
            provisional = "Likely temporal"
        elif float(overall.loc[feature, "Missing percentage"]) < 5 and station_spread < 20 and year_spread < 5:
            provisional = "Likely sporadic"
        else:
            provisional = "Unclear"

        rows.append(
            {
                "Feature": feature,
                "Overall missing percentage": float(overall.loc[feature, "Missing percentage"]),
                "Complete-absence locations": complete_absence,
                "Partial-missingness locations": partial,
                "Good-coverage locations": good,
                "Fully complete locations": full,
                "Minimum station missing percentage": round(float(station["Missing percentage"].min()), 4),
                "Maximum station missing percentage": round(float(station["Missing percentage"].max()), 4),
                "Station percentage spread": round(station_spread, 4),
                "Minimum yearly missing percentage": round(float(feature_years["Missing percentage"].min()), 4),
                "Maximum yearly missing percentage": round(float(feature_years["Missing percentage"].max()), 4),
                "Yearly percentage spread": round(year_spread, 4),
                "Locations with >=10pp within-station yearly spread": changing_locations,
                "Median within-station yearly spread": round(float(within_station_spreads.median()), 4),
                "Maximum within-station yearly spread": round(float(within_station_spreads.max()), 4),
                "Provisional pattern": provisional,
                "Mechanism caveat": "Annual aggregates may reflect station mix; observed patterns do not establish MCAR, MAR, or MNAR.",
            }
        )
    return pd.DataFrame(rows)


def comissingness_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Return interpretable co-missingness metrics for required feature pairs."""

    named_pairs = [
        ("Rainfall / RainToday", "Rainfall", "RainToday"),
        ("Pressure", "Pressure9am", "Pressure3pm"),
        ("Cloud", "Cloud9am", "Cloud3pm"),
        ("Sunshine / Evaporation", "Sunshine", "Evaporation"),
    ]
    named_pairs.extend(("Wind", first, second) for first, second in combinations(WIND_FEATURES, 2))

    rows = []
    total = len(frame)
    for group, first, second in named_pairs:
        first_missing = frame[first].isna()
        second_missing = frame[second].isna()
        both = int((first_missing & second_missing).sum())
        first_only = int((first_missing & ~second_missing).sum())
        second_only = int((~first_missing & second_missing).sum())
        union = int((first_missing | second_missing).sum())
        rows.append(
            {
                "Group": group,
                "Feature A": first,
                "Feature B": second,
                "A missing": int(first_missing.sum()),
                "B missing": int(second_missing.sum()),
                "Both missing": both,
                "A only missing": first_only,
                "B only missing": second_only,
                "Missing union": union,
                "Both missing percentage of rows": round(both / total * 100 if total else 0.0, 4),
                "Jaccard co-missingness percentage": round(both / union * 100 if union else 0.0, 4),
                "Identical missingness masks": bool(first_missing.equals(second_missing)),
            }
        )
    return pd.DataFrame(rows)


def target_missingness(frame: pd.DataFrame) -> TargetMissingnessAnalysis:
    """Describe RainTomorrow missingness by date, location, and station endpoints."""

    required = {"Date", "Location", "RainTomorrow"}
    missing_columns = required - set(frame.columns)
    if missing_columns:
        raise ValueError(f"Missing target-analysis columns: {', '.join(sorted(missing_columns))}")

    dates = pd.to_datetime(frame["Date"], format="%Y-%m-%d", errors="coerce")
    target_missing = frame["RainTomorrow"].isna()
    station_start = dates.groupby(frame["Location"]).transform("min")
    station_end = dates.groupby(frame["Location"]).transform("max")

    overview_rows: list[tuple[str, Any]] = [
        ("Total rows", int(len(frame))),
        ("Missing RainTomorrow count", int(target_missing.sum())),
        ("Missing RainTomorrow percentage", round(float(target_missing.mean() * 100), 4)),
        ("Labelled RainTomorrow count", int((~target_missing).sum())),
        ("Earliest missing-target date", dates[target_missing].min().date().isoformat()),
        ("Latest missing-target date", dates[target_missing].max().date().isoformat()),
    ]
    for window_days in (0, 7, 30):
        endpoint_mask = (
            ((dates - station_start).dt.days <= window_days)
            | ((station_end - dates).dt.days <= window_days)
        )
        missing_at_endpoint = int((target_missing & endpoint_mask).sum())
        missing_share = missing_at_endpoint / int(target_missing.sum()) * 100 if target_missing.any() else 0.0
        baseline_share = float(endpoint_mask.mean() * 100)
        ratio = missing_share / baseline_share if baseline_share else 0.0
        label = "exact station endpoints" if window_days == 0 else f"within {window_days} days of station endpoints"
        overview_rows.extend(
            [
                (f"Missing targets {label} (count)", missing_at_endpoint),
                (f"Missing targets {label} (%)", round(missing_share, 4)),
                (f"All rows {label} (%)", round(baseline_share, 4)),
                (f"Endpoint concentration ratio ({window_days} days)", round(ratio, 4)),
            ]
        )

    working = pd.DataFrame(
        {
            "Location": frame["Location"],
            "Date": dates,
            "TargetMissing": target_missing,
            "StationStart": station_start,
            "StationEnd": station_end,
        }
    )
    location_rows = []
    for location, group in working.groupby("Location", sort=True):
        missing_dates = group.loc[group["TargetMissing"], "Date"]
        location_rows.append(
            {
                "Location": str(location),
                "Record count": int(len(group)),
                "Missing target count": int(group["TargetMissing"].sum()),
                "Missing target percentage": round(float(group["TargetMissing"].mean() * 100), 4),
                "First missing-target date": missing_dates.min().date().isoformat() if not missing_dates.empty else "",
                "Last missing-target date": missing_dates.max().date().isoformat() if not missing_dates.empty else "",
                "Missing at station start": int((group["TargetMissing"] & (group["Date"] == group["StationStart"])).sum()),
                "Missing at station end": int((group["TargetMissing"] & (group["Date"] == group["StationEnd"])).sum()),
            }
        )

    by_year = (
        pd.DataFrame({"Year": dates.dt.year, "TargetMissing": target_missing})
        .dropna(subset=["Year"])
        .groupby("Year")["TargetMissing"]
        .agg(**{"Record count": "size", "Missing target count": "sum"})
        .reset_index()
    )
    by_year["Year"] = by_year["Year"].astype(int)
    by_year["Missing target percentage"] = (
        by_year["Missing target count"] / by_year["Record count"] * 100
    ).round(4)

    return TargetMissingnessAnalysis(
        overview=pd.DataFrame(overview_rows, columns=["Target-missingness metric", "Value"]),
        by_location=pd.DataFrame(location_rows),
        by_year=by_year,
    )


def rainfall_raintoday_relationship(frame: pd.DataFrame) -> pd.DataFrame:
    """Verify whether Rainfall and RainToday missingness coincide."""

    rainfall_missing = frame["Rainfall"].isna()
    rain_today_missing = frame["RainToday"].isna()
    both = rainfall_missing & rain_today_missing
    rows: list[tuple[str, Any]] = [
        ("Rainfall missing count", int(rainfall_missing.sum())),
        ("RainToday missing count", int(rain_today_missing.sum())),
        ("Both missing count", int(both.sum())),
        ("Rainfall-only missing count", int((rainfall_missing & ~rain_today_missing).sum())),
        ("RainToday-only missing count", int((~rainfall_missing & rain_today_missing).sum())),
        ("Missingness fully coincides", bool(rainfall_missing.equals(rain_today_missing))),
    ]
    return pd.DataFrame(rows, columns=["Relationship metric", "Value"])


def proposal_missingness_comparison(
    frame: pd.DataFrame,
    structural_table: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Compare proposal-level missing-count and station-absence claims."""

    structural_table = (
        structural_table if structural_table is not None else structural_missingness_summary(frame)
    )
    structural_lookup = structural_table.set_index("Feature")["Complete-absence locations"]
    rows = []
    for feature, expected in PROPOSAL_MISSING_COUNTS.items():
        actual = int(frame[feature].isna().sum())
        rows.append(
            {
                "Claim": f"{feature} missing count",
                "Expected value": expected,
                "Actual dataset value": actual,
                "Match / Mismatch": "Match" if actual == expected else "Mismatch",
                "Comment": "Direct count of missing values in the raw dataset.",
            }
        )
    for feature in MAJOR_STRUCTURAL_FEATURES:
        affected = int(structural_lookup.loc[feature])
        rows.append(
            {
                "Claim": f"{feature} is entirely absent at some stations",
                "Expected value": "At least 1 station",
                "Actual dataset value": f"{affected} stations",
                "Match / Mismatch": "Match" if affected > 0 else "Mismatch",
                "Comment": "A station is counted only when every row for that feature is missing.",
            }
        )
    return pd.DataFrame(rows)
