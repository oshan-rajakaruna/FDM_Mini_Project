"""Reusable descriptive helpers for T04 target-and-feature relationship EDA."""

from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations

import pandas as pd


TARGET = "RainTomorrow"

NUMERIC_FEATURES = (
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

CATEGORICAL_FEATURES = (
    "RainToday",
    "WindGustDir",
    "WindDir9am",
    "WindDir3pm",
    "Location",
)

IMPORTANT_RELATIONSHIPS = (
    "Humidity3pm",
    "Humidity9am",
    "Pressure3pm",
    "Pressure9am",
    "Sunshine",
    "Cloud3pm",
    "Cloud9am",
    "Rainfall",
    "RainToday",
    "WindGustSpeed",
)

MONTH_NAMES = (
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
)

SEASON_BY_MONTH = {
    12: "Summer",
    1: "Summer",
    2: "Summer",
    3: "Autumn",
    4: "Autumn",
    5: "Autumn",
    6: "Winter",
    7: "Winter",
    8: "Winter",
    9: "Spring",
    10: "Spring",
    11: "Spring",
}


@dataclass(frozen=True)
class TemporalTargetAnalysis:
    """Target-rate summaries for temporary EDA time groupings."""

    by_month: pd.DataFrame
    by_year: pd.DataFrame
    by_season: pd.DataFrame


@dataclass(frozen=True)
class CorrelationAnalysis:
    """Pairwise-complete Pearson correlations and unique predictor pairs."""

    matrix: pd.DataFrame
    pairs: pd.DataFrame


def _require_columns(frame: pd.DataFrame, columns: tuple[str, ...]) -> None:
    missing = [column for column in columns if column not in frame.columns]
    if missing:
        raise ValueError(f"Required relationship-analysis columns are missing: {', '.join(missing)}")


def _rain_rate_rows(
    frame: pd.DataFrame,
    group_column: str,
    group_values: list[object] | None = None,
) -> pd.DataFrame:
    rows = []
    values = group_values if group_values is not None else list(frame[group_column].drop_duplicates())
    for value in values:
        group = frame.loc[frame[group_column] == value]
        labelled = group.loc[group[TARGET].notna(), TARGET]
        yes_count = int((labelled == "Yes").sum())
        no_count = int((labelled == "No").sum())
        rows.append(
            {
                group_column: value,
                "Total record count": int(len(group)),
                "Labelled record count": int(len(labelled)),
                "Yes count": yes_count,
                "No count": no_count,
                "Missing target count": int(group[TARGET].isna().sum()),
                "Rain rate (Yes percentage)": round(
                    yes_count / len(labelled) * 100 if len(labelled) else 0.0, 4
                ),
            }
        )
    return pd.DataFrame(rows)


def target_distribution(frame: pd.DataFrame) -> pd.DataFrame:
    """Return class counts, imbalance metrics, and the descriptive baseline."""

    _require_columns(frame, (TARGET,))
    counts = frame[TARGET].value_counts(dropna=True)
    no_count = int(counts.get("No", 0))
    yes_count = int(counts.get("Yes", 0))
    labelled = no_count + yes_count
    missing = int(frame[TARGET].isna().sum())
    majority = max(no_count, yes_count)
    minority = min(no_count, yes_count)
    rows = [
        ("No count", no_count, "rows"),
        ("Yes count", yes_count, "rows"),
        ("No percentage", round(no_count / labelled * 100, 4), "percentage of labelled rows"),
        ("Yes percentage", round(yes_count / labelled * 100, 4), "percentage of labelled rows"),
        ("Missing target count", missing, "rows"),
        ("Labelled total", labelled, "rows"),
        (
            "Majority/minority ratio",
            round(majority / minority, 4) if minority else float("inf"),
            "majority rows per minority row",
        ),
        (
            "Baseline majority-class accuracy",
            round(majority / labelled * 100, 4) if labelled else 0.0,
            "descriptive percentage; no model trained",
        ),
    ]
    return pd.DataFrame(rows, columns=["Metric", "Value", "Context"])


def temporal_target_rates(frame: pd.DataFrame) -> TemporalTargetAnalysis:
    """Summarize target rates by month, year, and EDA-only Southern seasons."""

    _require_columns(frame, ("Date", TARGET))
    dates = pd.to_datetime(frame["Date"], format="%Y-%m-%d", errors="coerce")
    if dates.notna().sum() == 0:
        raise ValueError("Date contains no valid YYYY-MM-DD values")
    work = pd.DataFrame({TARGET: frame[TARGET], "Month number": dates.dt.month, "Year": dates.dt.year})
    work["Season"] = work["Month number"].map(SEASON_BY_MONTH)

    month = _rain_rate_rows(work, "Month number", list(range(1, 13)))
    month.insert(1, "Month", [MONTH_NAMES[number - 1] for number in month["Month number"]])
    years = sorted(int(value) for value in work["Year"].dropna().unique())
    year = _rain_rate_rows(work, "Year", years)
    year["Year"] = year["Year"].astype(int)
    season = _rain_rate_rows(work, "Season", ["Summer", "Autumn", "Winter", "Spring"])
    season["EDA-only derivation note"] = (
        "Southern Hemisphere season derived from Date for T04 description only; not an approved model feature."
    )
    return TemporalTargetAnalysis(by_month=month, by_year=year, by_season=season)


def location_target_rates(frame: pd.DataFrame) -> pd.DataFrame:
    """Return per-location class counts and descriptive rain-rate positions."""

    _require_columns(frame, ("Location", TARGET))
    result = _rain_rate_rows(frame, "Location").sort_values("Location").reset_index(drop=True)
    q1_count = float(result["Labelled record count"].quantile(0.25))
    q1_rate = float(result["Rain rate (Yes percentage)"].quantile(0.25))
    q3_rate = float(result["Rain rate (Yes percentage)"].quantile(0.75))
    result["Observation-count flag"] = result["Labelled record count"].map(
        lambda count: "Lower-quartile count; percentage may be less stable" if count <= q1_count else "Typical/higher count"
    )
    result["Rain-rate position"] = result["Rain rate (Yes percentage)"].map(
        lambda rate: (
            "Relatively low (lower quartile)"
            if rate <= q1_rate
            else "Relatively high (upper quartile)"
            if rate >= q3_rate
            else "Middle half"
        )
    )
    return result


def numeric_target_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Return pairwise-available numerical summaries for labelled target rows."""

    _require_columns(frame, NUMERIC_FEATURES + (TARGET,))
    labelled = frame.loc[frame[TARGET].isin(["No", "Yes"])]
    rows = []
    for feature in NUMERIC_FEATURES:
        for target_value in ("No", "Yes"):
            group = labelled.loc[labelled[TARGET] == target_value, feature]
            values = group.dropna()
            rows.append(
                {
                    "Feature": feature,
                    "RainTomorrow": target_value,
                    "Labelled class count": int(len(group)),
                    "Available count": int(values.size),
                    "Missing within class": int(group.isna().sum()),
                    "Mean": round(float(values.mean()), 4),
                    "Standard deviation": round(float(values.std()), 4),
                    "25th percentile": round(float(values.quantile(0.25)), 4),
                    "Median": round(float(values.median()), 4),
                    "75th percentile": round(float(values.quantile(0.75)), 4),
                }
            )
    return pd.DataFrame(rows)


def categorical_target_summary(frame: pd.DataFrame) -> pd.DataFrame:
    """Return frequency and target-rate summaries, retaining missing categories."""

    _require_columns(frame, CATEGORICAL_FEATURES + (TARGET,))
    labelled = frame.loc[frame[TARGET].isin(["No", "Yes"])]
    rows = []
    for feature in CATEGORICAL_FEATURES:
        categories = labelled[feature].astype("string").fillna("<Missing>")
        for category in sorted(categories.unique(), key=lambda value: (value == "<Missing>", str(value))):
            mask = categories == category
            targets = labelled.loc[mask, TARGET]
            yes_count = int((targets == "Yes").sum())
            no_count = int((targets == "No").sum())
            count = int(mask.sum())
            rows.append(
                {
                    "Feature": feature,
                    "Category": str(category),
                    "Category frequency among labelled rows": count,
                    "Category percentage among labelled rows": round(count / len(labelled) * 100, 4),
                    "Yes count": yes_count,
                    "No count": no_count,
                    "RainTomorrow Yes rate": round(yes_count / count * 100 if count else 0.0, 4),
                }
            )
    return pd.DataFrame(rows)


def correlation_analysis(frame: pd.DataFrame) -> CorrelationAnalysis:
    """Return labelled-row Pearson correlations using pairwise available values."""

    _require_columns(frame, NUMERIC_FEATURES + (TARGET,))
    labelled = frame.loc[frame[TARGET].isin(["No", "Yes"]), NUMERIC_FEATURES]
    matrix = labelled.corr(method="pearson")
    matrix.index.name = "Feature"
    matrix_table = matrix.reset_index()
    rows = []
    for first, second in combinations(NUMERIC_FEATURES, 2):
        correlation = float(matrix.loc[first, second])
        absolute = abs(correlation)
        common = int(labelled[[first, second]].dropna().shape[0])
        strength = (
            "Very strong"
            if absolute >= 0.9
            else "Strong"
            if absolute >= 0.7
            else "Moderate"
            if absolute >= 0.5
            else "Weak"
        )
        rows.append(
            {
                "Feature A": first,
                "Feature B": second,
                "Pearson correlation": round(correlation, 6),
                "Absolute correlation": round(absolute, 6),
                "Pairwise available count": common,
                "Descriptive strength": strength,
            }
        )
    pairs = pd.DataFrame(rows).sort_values(
        ["Absolute correlation", "Feature A", "Feature B"], ascending=[False, True, True]
    ).reset_index(drop=True)
    return CorrelationAnalysis(matrix=matrix_table, pairs=pairs)


def raintoday_rainfall_relationship(frame: pd.DataFrame) -> pd.DataFrame:
    """Verify RainToday against explicit >=1 mm and >1 mm Rainfall rules."""

    _require_columns(frame, ("Rainfall", "RainToday", TARGET))
    rainfall_present = frame["Rainfall"].notna()
    raintoday_present = frame["RainToday"].notna()
    usable_mask = rainfall_present & raintoday_present
    usable = frame.loc[usable_mask, ["Rainfall", "RainToday", TARGET]]

    prediction_ge = usable["Rainfall"].ge(1.0).map({True: "Yes", False: "No"})
    prediction_gt = usable["Rainfall"].gt(1.0).map({True: "Yes", False: "No"})
    agreement_ge = prediction_ge.eq(usable["RainToday"])
    agreement_gt = prediction_gt.eq(usable["RainToday"])
    disagreement_ge = ~agreement_ge
    agreement_percentage = float(agreement_ge.mean() * 100)
    proposal_result = "Match" if round(agreement_percentage, 1) == 98.8 else "Mismatch"

    rows = [
        ("Total dataset rows", int(len(frame)), "All records"),
        ("Usable Rainfall/RainToday comparisons", int(usable_mask.sum()), "Both fields available"),
        (
            "Target-labelled usable comparisons",
            int((usable_mask & frame[TARGET].notna()).sum()),
            "Both fields and RainTomorrow available",
        ),
        ("Rows with one or both fields missing", int((~usable_mask).sum()), "Excluded pairwise, not removed"),
        ("Both fields missing", int((~rainfall_present & ~raintoday_present).sum()), "Missing-value effect"),
        ("Rainfall-only missing", int((~rainfall_present & raintoday_present).sum()), "Missing-value effect"),
        ("RainToday-only missing", int((rainfall_present & ~raintoday_present).sum()), "Missing-value effect"),
        ("Agreement count using Rainfall >= 1 mm", int(agreement_ge.sum()), "Proposal threshold convention"),
        ("Agreement percentage using Rainfall >= 1 mm", round(agreement_percentage, 4), "Percentage of usable pairs"),
        ("Disagreement count using Rainfall >= 1 mm", int(disagreement_ge.sum()), "Usable pairs"),
        (
            "Disagreements at exactly 1.0 mm",
            int((disagreement_ge & usable["Rainfall"].eq(1.0)).sum()),
            "All such records are RainToday=No in this dataset",
        ),
        ("Agreement count using Rainfall > 1 mm", int(agreement_gt.sum()), "Alternative strict-threshold check"),
        ("Agreement percentage using Rainfall > 1 mm", round(float(agreement_gt.mean() * 100), 4), "Percentage of usable pairs"),
        ("Proposal claim (approximately 98.8%)", proposal_result, "Compared after rounding actual agreement to one decimal place"),
        (
            "Proposal threshold definition",
            "Minor mismatch / boundary clarification",
            "Proposal says 1 mm or more (>= 1.0 mm); usable dataset pairs match RainToday when Rainfall > 1.0 mm.",
        ),
    ]
    return pd.DataFrame(rows, columns=["Metric", "Value", "Context"])


def _missingness_concern(missing_percentage: float) -> str:
    if missing_percentage >= 20:
        return f"High ({missing_percentage:.2f}%)"
    if missing_percentage >= 5:
        return f"Moderate ({missing_percentage:.2f}%)"
    return f"Low ({missing_percentage:.2f}%)"


def _numeric_strength(effect: float) -> str:
    absolute = abs(effect)
    if absolute >= 0.8:
        return "Strong observed separation"
    if absolute >= 0.5:
        return "Moderate observed association"
    if absolute >= 0.2:
        return "Weak observed separation"
    return "Minimal observed separation"


def target_association_summary(
    frame: pd.DataFrame,
    numeric_summary: pd.DataFrame | None = None,
    categorical_summary: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """Summarize descriptive associations without claiming model importance."""

    _require_columns(frame, NUMERIC_FEATURES + CATEGORICAL_FEATURES + (TARGET,))
    numeric = numeric_summary if numeric_summary is not None else numeric_target_summary(frame)
    categorical = categorical_summary if categorical_summary is not None else categorical_target_summary(frame)
    rows = []
    redundancy = {
        "MinTemp": "Correlated with Temp9am, Temp3pm, and MaxTemp",
        "MaxTemp": "Very strongly correlated with Temp3pm; correlated with morning temperatures",
        "Temp9am": "Strongly correlated with MinTemp and MaxTemp",
        "Temp3pm": "Very strongly correlated with MaxTemp",
        "Humidity9am": "Related morning/afternoon measure; correlation should be considered later",
        "Humidity3pm": "Related morning/afternoon measure; correlation should be considered later",
        "Pressure9am": "Very strongly correlated with Pressure3pm",
        "Pressure3pm": "Very strongly correlated with Pressure9am",
        "WindSpeed9am": "Related morning/afternoon wind-speed measure",
        "WindSpeed3pm": "Related morning/afternoon wind-speed measure",
        "Rainfall": "Strong definitional overlap with RainToday threshold indicator",
        "RainToday": "Strong definitional overlap with Rainfall",
    }
    for feature in NUMERIC_FEATURES:
        feature_rows = numeric.loc[numeric["Feature"] == feature].set_index("RainTomorrow")
        no_mean = float(feature_rows.loc["No", "Mean"])
        yes_mean = float(feature_rows.loc["Yes", "Mean"])
        no_std = float(feature_rows.loc["No", "Standard deviation"])
        yes_std = float(feature_rows.loc["Yes", "Standard deviation"])
        pooled = ((no_std**2 + yes_std**2) / 2) ** 0.5
        effect = (yes_mean - no_mean) / pooled if pooled else 0.0
        no_median = float(feature_rows.loc["No", "Median"])
        yes_median = float(feature_rows.loc["Yes", "Median"])
        missing_percentage = float(frame[feature].isna().mean() * 100)
        rows.append(
            {
                "Feature": feature,
                "Feature type": "Numerical",
                "Observed relationship with RainTomorrow": (
                    f"Median Yes={yes_median:g} versus No={no_median:g}; standardized mean difference={effect:.3f}."
                ),
                "Descriptive association assessment": _numeric_strength(effect),
                "Missingness concern": _missingness_concern(missing_percentage),
                "Redundancy concern": redundancy.get(feature, "No specific high-correlation concern identified at T04"),
                "Future consideration": "Retain for now; evaluate robustness and predictive contribution after leakage-safe splitting.",
            }
        )

    for feature in CATEGORICAL_FEATURES:
        feature_rows = categorical.loc[
            (categorical["Feature"] == feature) & (categorical["Category"] != "<Missing>")
        ]
        minimum = float(feature_rows["RainTomorrow Yes rate"].min())
        maximum = float(feature_rows["RainTomorrow Yes rate"].max())
        spread = maximum - minimum
        strength = (
            "Strong observed separation"
            if spread >= 20
            else "Moderate observed association"
            if spread >= 10
            else "Weak observed separation"
            if spread >= 5
            else "Minimal observed separation"
        )
        missing_percentage = float(frame[feature].isna().mean() * 100)
        rows.append(
            {
                "Feature": feature,
                "Feature type": "Categorical",
                "Observed relationship with RainTomorrow": (
                    f"Observed category Yes rates span {minimum:.2f}% to {maximum:.2f}% (range {spread:.2f} percentage points)."
                ),
                "Descriptive association assessment": strength,
                "Missingness concern": _missingness_concern(missing_percentage),
                "Redundancy concern": redundancy.get(feature, "No direct numerical redundancy conclusion; preserve category meaning"),
                "Future consideration": "Preserve original categories; encoding and contribution assessment are deferred.",
            }
        )
    return pd.DataFrame(rows)


def relationship_interpretations(association_summary: pd.DataFrame) -> pd.DataFrame:
    """Return cautious observation/interpretation/future notes for key relationships."""

    lookup = association_summary.set_index("Feature")
    interpretations = {
        "Humidity3pm": "Higher afternoon humidity is consistent with wetter atmospheric conditions, but this is association, not causation.",
        "Humidity9am": "Morning humidity also differs by target class, with weaker separation than afternoon humidity.",
        "Pressure3pm": "Lower afternoon pressure is associated with next-day rain in this sample; weather systems and location may confound it.",
        "Pressure9am": "Lower morning pressure is associated with next-day rain, without establishing an independent causal effect.",
        "Sunshine": "Lower recorded sunshine accompanies more Yes labels where sunshine is observed; structural station missingness limits coverage.",
        "Cloud3pm": "Greater afternoon cloud cover accompanies more Yes labels, subject to substantial station-dependent missingness.",
        "Cloud9am": "Greater morning cloud cover accompanies more Yes labels, subject to substantial station-dependent missingness.",
        "Rainfall": "Recent rainfall is associated with next-day rain, consistent with persistence in wet conditions; skew and threshold overlap matter.",
        "RainToday": "RainToday separates target rates and reflects recent rainfall status, but it substantially overlaps with Rainfall by definition.",
        "WindGustSpeed": "Higher gust speeds are associated with Yes labels, but the distributions overlap and extremes remain untreated.",
    }
    future = {
        "Rainfall": "Later assess transformation/non-linearity and redundancy with RainToday after the chronological split is fixed.",
        "RainToday": "Retain for now; later compare its incremental value against Rainfall without leakage.",
        "Sunshine": "Later compare missingness-aware handling and coverage-sensitive usefulness; do not impute globally by default.",
        "Cloud3pm": "Later assess missing indicators or station-aware handling and possible non-linear effects.",
        "Cloud9am": "Later assess missing indicators or station-aware handling and possible non-linear effects.",
    }
    rows = []
    for feature in IMPORTANT_RELATIONSHIPS:
        rows.append(
            {
                "Feature": feature,
                "Observation": str(lookup.loc[feature, "Observed relationship with RainTomorrow"]),
                "Interpretation": interpretations[feature],
                "Future consideration": future.get(
                    feature,
                    "Retain unchanged in T04; later evaluate non-linearity, redundancy, and predictive contribution using leakage-safe data.",
                ),
            }
        )
    return pd.DataFrame(rows)
