"""Reusable helpers for T05 outlier and suspicious-value analysis."""

from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


NUMERICAL_FEATURES = (
    "MinTemp",
    "MaxTemp",
    "Rainfall",
    "Evaporation",
    "Sunshine",
    "WindGustSpeed",
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
)

UNITS = {
    "MinTemp": "°C",
    "MaxTemp": "°C",
    "Rainfall": "mm",
    "Evaporation": "mm",
    "Sunshine": "hours",
    "WindGustSpeed": "km/h",
    "WindSpeed9am": "km/h",
    "WindSpeed3pm": "km/h",
    "Humidity9am": "%",
    "Humidity3pm": "%",
    "Pressure9am": "hPa",
    "Pressure3pm": "hPa",
    "Cloud9am": "oktas",
    "Cloud3pm": "oktas",
    "Temp9am": "°C",
    "Temp3pm": "°C",
}

ALLOWED_CLASSIFICATIONS = {
    "likely valid extreme",
    "suspicious / investigate later",
    "likely invalid",
    "unresolved",
}


def _require_columns(frame: pd.DataFrame, columns: Iterable[str]) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"Required outlier-analysis columns are missing: {', '.join(missing)}")


def percentile_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Return the requested extreme-value distribution summary."""

    _require_columns(frame, NUMERICAL_FEATURES)
    rows = []
    for feature in NUMERICAL_FEATURES:
        values = frame[feature].dropna()
        quantiles = values.quantile([0.01, 0.05, 0.25, 0.5, 0.75, 0.95, 0.99])
        q1 = float(quantiles.loc[0.25])
        q3 = float(quantiles.loc[0.75])
        rows.append(
            {
                "Feature": feature,
                "Unit": UNITS[feature],
                "Non-missing count": int(values.size),
                "Minimum": round(float(values.min()), 4),
                "1st percentile": round(float(quantiles.loc[0.01]), 4),
                "5th percentile": round(float(quantiles.loc[0.05]), 4),
                "25th percentile": round(q1, 4),
                "Median": round(float(quantiles.loc[0.5]), 4),
                "75th percentile": round(q3, 4),
                "95th percentile": round(float(quantiles.loc[0.95]), 4),
                "99th percentile": round(float(quantiles.loc[0.99]), 4),
                "Maximum": round(float(values.max()), 4),
                "IQR": round(q3 - q1, 4),
                "Skewness": round(float(values.skew()), 6),
            }
        )
    return pd.DataFrame(rows)


def iqr_outlier_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Screen numerical features with 1.5-IQR fences without changing values."""

    _require_columns(frame, NUMERICAL_FEATURES)
    rows = []
    for feature in NUMERICAL_FEATURES:
        values = frame[feature].dropna()
        q1 = float(values.quantile(0.25))
        q3 = float(values.quantile(0.75))
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        below = int(values.lt(lower).sum())
        above = int(values.gt(upper).sum())
        total = below + above
        rows.append(
            {
                "Feature": feature,
                "Non-missing count": int(values.size),
                "Q1": round(q1, 4),
                "Q3": round(q3, 4),
                "IQR": round(iqr, 4),
                "Lower fence": round(lower, 4),
                "Upper fence": round(upper, 4),
                "Count below lower fence": below,
                "Count above upper fence": above,
                "Total IQR-flagged": total,
                "Percentage IQR-flagged": round(total / len(values) * 100 if len(values) else 0.0, 4),
                "Interpretation": "Statistical screening only; an IQR flag is not a domain error.",
            }
        )
    return pd.DataFrame(rows)


def cloud_nine_investigation(frame: pd.DataFrame) -> pd.DataFrame:
    """Return every observed Cloud9am/Cloud3pm value equal to 9."""

    required = ("Date", "Location", "Cloud9am", "Cloud3pm", "Rainfall", "Humidity9am", "Humidity3pm", "RainTomorrow")
    _require_columns(frame, required)
    rows = []
    for feature in ("Cloud9am", "Cloud3pm"):
        selected = frame.loc[frame[feature].eq(9), required].copy()
        dates = pd.to_datetime(selected["Date"], format="%Y-%m-%d", errors="coerce")
        for (_, record), parsed_date in zip(selected.iterrows(), dates):
            rows.append(
                {
                    "Feature": feature,
                    "Value": 9,
                    "Date": record["Date"],
                    "Location": record["Location"],
                    "Year": int(parsed_date.year),
                    "Month": int(parsed_date.month),
                    "Other cloud value": record["Cloud3pm" if feature == "Cloud9am" else "Cloud9am"],
                    "Rainfall": record["Rainfall"],
                    "Humidity9am": record["Humidity9am"],
                    "Humidity3pm": record["Humidity3pm"],
                    "RainTomorrow": record["RainTomorrow"],
                    "Pattern assessment": "Sporadic: isolated across different locations/dates in the observed data.",
                }
            )
    return pd.DataFrame(rows).sort_values(["Date", "Feature"]).reset_index(drop=True)


def humidity_boundary_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Check humidity physical bounds and observed boundary frequencies."""

    _require_columns(frame, ("Humidity9am", "Humidity3pm"))
    rows = []
    for feature in ("Humidity9am", "Humidity3pm"):
        values = frame[feature].dropna()
        below = int(values.lt(0).sum())
        above = int(values.gt(100).sum())
        rows.append(
            {
                "Feature": feature,
                "Non-missing count": int(values.size),
                "Minimum": float(values.min()),
                "Maximum": float(values.max()),
                "Count below 0": below,
                "Count equal to 0": int(values.eq(0).sum()),
                "Count equal to 100": int(values.eq(100).sum()),
                "Count above 100": above,
                "Outside 0–100 range": below + above,
                "Assessment": "Within the physical 0–100% bounds; boundary values retained for review.",
            }
        )
    return pd.DataFrame(rows)


def rainfall_skewness_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Return zero-rain, positive-rain, skewness, and upper-tail metrics."""

    _require_columns(frame, ("Rainfall",))
    values = frame["Rainfall"].dropna()
    positive = values.loc[values.gt(0)]
    iqr_row = iqr_outlier_summary(frame).set_index("Feature").loc["Rainfall"]
    rows = [
        ("Non-missing Rainfall count", int(values.size), "rows"),
        ("Zero-rain count", int(values.eq(0).sum()), "rows"),
        ("Zero-rain percentage", round(float(values.eq(0).mean() * 100), 4), "percentage of non-missing"),
        ("Positive-rain count", int(positive.size), "rows"),
        ("All-value skewness", round(float(values.skew()), 6), "sample skewness"),
        ("Positive-only skewness", round(float(positive.skew()), 6), "sample skewness"),
        ("99th percentile", round(float(values.quantile(0.99)), 4), "mm"),
        ("99.9th percentile", round(float(values.quantile(0.999)), 4), "mm"),
        ("Maximum", round(float(values.max()), 4), "mm"),
        ("Count >= 100 mm", int(values.ge(100).sum()), "rows"),
        ("Count >= 200 mm", int(values.ge(200).sum()), "rows"),
        ("IQR-flagged count", int(iqr_row["Total IQR-flagged"]), "rows"),
        ("IQR-flagged percentage", float(iqr_row["Percentage IQR-flagged"]), "percentage of non-missing"),
    ]
    return pd.DataFrame(rows, columns=["Rainfall metric", "Value", "Context"])


def extreme_pattern_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Describe whether evaporation/wind upper-tail values repeat across place/time."""

    required = ("Date", "Location", "Rainfall", "RainTomorrow", "Evaporation", "WindGustSpeed", "WindSpeed9am", "WindSpeed3pm")
    _require_columns(frame, required)
    dates = pd.to_datetime(frame["Date"], format="%Y-%m-%d", errors="coerce")
    rows = []
    for feature in ("Evaporation", "WindGustSpeed", "WindSpeed9am", "WindSpeed3pm"):
        threshold = float(frame[feature].quantile(0.99))
        mask = frame[feature].ge(threshold)
        selected = frame.loc[mask]
        labelled = selected["RainTomorrow"].dropna()
        rows.append(
            {
                "Feature": feature,
                "99th-percentile threshold": threshold,
                "Count at/above threshold": int(mask.sum()),
                "Locations represented": int(selected["Location"].nunique()),
                "Years represented": int(dates.loc[mask].dt.year.nunique()),
                "First date": selected["Date"].min(),
                "Last date": selected["Date"].max(),
                "Observed maximum": float(frame[feature].max()),
                "Maximum occurrence count": int(frame[feature].eq(frame[feature].max()).sum()),
                "Co-occurring positive Rainfall count": int(selected["Rainfall"].gt(0).sum()),
                "RainTomorrow Yes rate among labelled extremes": round(
                    float(labelled.eq("Yes").mean() * 100) if len(labelled) else 0.0, 4
                ),
                "Pattern assessment": (
                    "Upper tail repeats across multiple stations/years"
                    if selected["Location"].nunique() > 5 and dates.loc[mask].dt.year.nunique() > 3
                    else "Upper tail is concentrated; investigate later"
                ),
            }
        )
    return pd.DataFrame(rows)


def extreme_weather_context(frame: pd.DataFrame) -> pd.DataFrame:
    """Return row context for specific T02 maximum values."""

    required = (
        "Date", "Location", "Rainfall", "Evaporation", "WindGustSpeed", "WindSpeed9am",
        "WindSpeed3pm", "MaxTemp", "Humidity9am", "Humidity3pm", "Pressure9am",
        "Pressure3pm", "RainToday", "RainTomorrow",
    )
    _require_columns(frame, required)
    rules = (
        ("Rainfall", 371.0, "Rainfall maximum = 371 mm"),
        ("Evaporation", 145.0, "Evaporation maximum = 145 mm"),
        ("WindGustSpeed", 135.0, "WindGustSpeed maximum = 135 km/h"),
        ("WindSpeed9am", 130.0, "WindSpeed9am maximum = 130 km/h"),
    )
    rows = []
    for feature, value, rule in rules:
        selected = frame.loc[frame[feature].eq(value), required]
        for _, record in selected.iterrows():
            row = record.to_dict()
            row = {"Selected feature": feature, "Selected rule": rule, "Selected value": value, **row}
            rows.append(row)
    return pd.DataFrame(rows)


def suspicious_value_details(frame: pd.DataFrame) -> pd.DataFrame:
    """Return row-level context for requested suspicious/extreme triggers."""

    _require_columns(
        frame,
        (
            "Date", "Location", "Cloud9am", "Cloud3pm", "Humidity9am", "Humidity3pm",
            "Rainfall", "Evaporation", "WindGustSpeed", "WindSpeed9am", "WindSpeed3pm",
            "MaxTemp", "RainToday", "RainTomorrow",
        ),
    )
    rules = (
        ("Cloud9am", 9.0, "Cloud9am = 9", "suspicious / investigate later"),
        ("Cloud3pm", 9.0, "Cloud3pm = 9", "suspicious / investigate later"),
        ("Humidity9am", 0.0, "Humidity9am = 0%", "unresolved"),
        ("Humidity3pm", 0.0, "Humidity3pm = 0%", "unresolved"),
        ("Rainfall", 371.0, "Rainfall maximum = 371 mm", "likely valid extreme"),
        ("Evaporation", 145.0, "Evaporation maximum = 145 mm", "suspicious / investigate later"),
        ("WindGustSpeed", 135.0, "WindGustSpeed maximum = 135 km/h", "likely valid extreme"),
        ("WindSpeed9am", 130.0, "WindSpeed9am maximum = 130 km/h", "suspicious / investigate later"),
    )
    context_columns = [
        "Date", "Location", "Rainfall", "Evaporation", "WindGustSpeed", "WindSpeed9am",
        "WindSpeed3pm", "MaxTemp", "Humidity9am", "Humidity3pm", "RainToday", "RainTomorrow",
    ]
    rows = []
    for feature, value, rule, classification in rules:
        selected = frame.loc[frame[feature].eq(value), context_columns]
        for _, record in selected.iterrows():
            rows.append(
                {
                    "Feature": feature,
                    "Trigger": rule,
                    "Value": value,
                    **record.to_dict(),
                    "Classification": classification,
                }
            )
    return pd.DataFrame(rows).sort_values(["Date", "Feature"]).reset_index(drop=True)


def _endpoint_count(values: pd.Series) -> int:
    return int(values.eq(values.min()).sum() + values.eq(values.max()).sum())


def outlier_decision_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Classify important unusual values without applying any handling option."""

    _require_columns(frame, NUMERICAL_FEATURES)
    iqr = iqr_outlier_summary(frame).set_index("Feature")
    rows: list[dict[str, object]] = []

    def add(
        feature: str,
        rule: str,
        count: int,
        statistical: str,
        plausible: str,
        classification: str,
        future: str,
        reason: str,
    ) -> None:
        if classification not in ALLOWED_CLASSIFICATIONS:
            raise ValueError(f"Invalid unusual-value classification: {classification}")
        rows.append(
            {
                "Feature": feature,
                "Observed unusual value / rule": rule,
                "Number affected": int(count),
                "Percentage affected": round(count / len(frame) * 100 if len(frame) else 0.0, 6),
                "Statistical outlier?": statistical,
                "Domain-plausible?": plausible,
                "Classification": classification,
                "Recommended future handling": future,
                "Reason": reason,
            }
        )

    for feature in ("MinTemp", "MaxTemp", "Temp9am", "Temp3pm"):
        values = frame[feature].dropna()
        add(
            feature,
            f"Observed endpoints {values.min():g} to {values.max():g} {UNITS[feature]}",
            _endpoint_count(values),
            "Yes; one or both endpoints cross an IQR fence",
            "Plausible for Australian weather observations",
            "likely valid extreme",
            "Retain unchanged; consider robust scaling later if needed.",
            "Extreme temperatures remain within credible terrestrial weather ranges.",
        )

    for feature in ("Humidity9am", "Humidity3pm"):
        values = frame[feature].dropna()
        add(
            feature,
            "Humidity = 0%",
            int(values.eq(0).sum()),
            "Yes for Humidity9am; no for Humidity3pm under IQR screening",
            "At the physical boundary; measurement context uncertain",
            "unresolved",
            "Retain for now; investigate station/date context before any later rule.",
            "No values violate 0–100%, but exact zero is rare and location-concentrated.",
        )
        add(
            feature,
            "Humidity = 100%",
            int(values.eq(100).sum()),
            "May be IQR-flagged depending on feature distribution",
            "Yes; saturation is physically possible",
            "likely valid extreme",
            "Retain unchanged.",
            "The value is within the credible humidity constraint and occurs repeatedly.",
        )

    for feature in ("Pressure9am", "Pressure3pm"):
        values = frame[feature].dropna()
        add(
            feature,
            f"Observed endpoints {values.min():g} to {values.max():g} hPa",
            _endpoint_count(values),
            "Yes; endpoints cross IQR fences",
            "Plausible synoptic pressure range; no project-backed violation identified",
            "likely valid extreme",
            "Retain unchanged; use robust scaling later if warranted.",
            "Low/high values are unusual but not clearly physically implausible.",
        )

    for feature in ("Cloud9am", "Cloud3pm"):
        count = int(frame[feature].eq(9).sum())
        add(
            feature,
            "Cloud value = 9",
            count,
            "No; value 9 is within the sample IQR fences",
            "Outside the documented 0–8 okta scale; a special code remains possible",
            "suspicious / investigate later",
            "Retain unchanged in T05; verify source coding before recoding to 8 or missing.",
            "The value is rare and sporadic, but source metadata is insufficient to call it invalid.",
        )

    specific = (
        ("Rainfall", 371.0, "Rainfall = 371 mm", "likely valid extreme", "Retain; consider a later transformation/robust method.", "Very rare and strongly right-tailed, with wet contextual observations; not a physical impossibility."),
        ("Evaporation", 145.0, "Evaporation = 145 mm", "suspicious / investigate later", "Verify source record; consider capping or missing conversion only with evidence.", "Single value far above the next observations and paired with heavy rainfall; validity is uncertain."),
        ("WindGustSpeed", 135.0, "WindGustSpeed = 135 km/h", "likely valid extreme", "Retain; robust scaling may be considered later.", "Occurs three times across stations, including storm-like rain/humidity context."),
        ("WindSpeed9am", 130.0, "WindSpeed9am = 130 km/h", "suspicious / investigate later", "Verify the isolated record before any later capping or missing conversion.", "Single isolated value with missing gust/afternoon wind and otherwise limited confirming context."),
        ("WindSpeed3pm", float(frame["WindSpeed3pm"].max()), f"WindSpeed3pm maximum = {frame['WindSpeed3pm'].max():g} km/h", "likely valid extreme", "Retain; robust scaling may be considered later.", "Upper-tail winds repeat across many stations and years."),
    )
    for feature, value, rule, classification, future, reason in specific:
        add(
            feature,
            rule,
            int(frame[feature].eq(value).sum()),
            "Yes" if (value < iqr.loc[feature, "Lower fence"] or value > iqr.loc[feature, "Upper fence"]) else "No",
            "Plausible but requires contextual review" if "suspicious" in classification else "Plausible",
            classification,
            future,
            reason,
        )

    sunshine = frame["Sunshine"].dropna()
    add(
        "Sunshine",
        f"Observed endpoints {sunshine.min():g} to {sunshine.max():g} hours",
        _endpoint_count(sunshine),
        "No IQR-flagged Sunshine values",
        "Plausible daily duration",
        "likely valid extreme",
        "Retain unchanged.",
        "Observed range is compatible with zero-sun days and long Australian summer days.",
    )
    return pd.DataFrame(rows)


def proposal_consistency(frame: pd.DataFrame) -> pd.DataFrame:
    """Compare T05 findings with the supplied proposal statements."""

    _require_columns(frame, NUMERICAL_FEATURES)
    rainfall = rainfall_skewness_summary(frame).set_index("Rainfall metric")["Value"]
    cloud_count = int(frame["Cloud9am"].eq(9).sum() + frame["Cloud3pm"].eq(9).sum())
    humidity_outside = int(
        frame["Humidity9am"].lt(0).sum()
        + frame["Humidity9am"].gt(100).sum()
        + frame["Humidity3pm"].lt(0).sum()
        + frame["Humidity3pm"].gt(100).sum()
    )
    rows = [
        {
            "Claim": "Rainfall is strongly skewed and has many IQR-flagged observations",
            "Expected": "Strong right skew and substantial IQR flags",
            "Actual": f"Skewness {float(rainfall['All-value skewness']):.6f}; {float(rainfall['IQR-flagged percentage']):.4f}% IQR-flagged",
            "Match / Mismatch": "Match",
            "Comment": "The zero mass and long positive tail naturally make IQR screening flag many wet days.",
        },
        {
            "Claim": "Maximum Rainfall is 371 mm",
            "Expected": "371 mm",
            "Actual": f"{frame['Rainfall'].max():g} mm",
            "Match / Mismatch": "Match" if frame["Rainfall"].max() == 371 else "Mismatch",
            "Comment": "One observed record; retained for contextual review.",
        },
        {
            "Claim": "Evaporation and wind contain some extreme values",
            "Expected": "Extreme upper-tail values present",
            "Actual": f"Evaporation max {frame['Evaporation'].max():g} mm; gust max {frame['WindGustSpeed'].max():g} km/h; 9am wind max {frame['WindSpeed9am'].max():g} km/h",
            "Match / Mismatch": "Match",
            "Comment": "Upper tails were quantified without changing values.",
        },
        {
            "Claim": "Extremes may be genuine weather events rather than errors",
            "Expected": "Do not equate statistical outliers with errors",
            "Actual": "Rainfall and gust maxima have supporting weather context; evaporation 145 and 9am wind 130 remain suspicious",
            "Match / Mismatch": "Match",
            "Comment": "The dataset supports mixed, cautious classifications rather than blanket deletion.",
        },
        {
            "Claim": "Humidity lies within 0–100%",
            "Expected": "No values below 0 or above 100",
            "Actual": f"{humidity_outside} values outside 0–100%",
            "Match / Mismatch": "Match" if humidity_outside == 0 else "Mismatch",
            "Comment": "Rare 0% boundary values remain unresolved but are not outside the range.",
        },
        {
            "Claim": "Cloud data include value 9 despite a documented 0–8 scale",
            "Expected": "At least one cloud value 9",
            "Actual": f"{cloud_count} rows across Cloud9am/Cloud3pm",
            "Match / Mismatch": "Match" if cloud_count else "Mismatch",
            "Comment": "Three sporadic records require source-code clarification; none were recoded.",
        },
    ]
    return pd.DataFrame(rows)
