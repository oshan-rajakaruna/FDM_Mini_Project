"""Verify the completed T00 through T08 Progress Evaluation 1 requirements."""

from __future__ import annotations

import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

T00_REQUIRED_FILES = (
    "README.md",
    "AGENTS.md",
    "PROJECT_STATUS.md",
    "requirements.txt",
    ".gitignore",
    "src/fdm_rainfall/__init__.py",
    "scripts/verify_stage1.py",
    "reports/evidence/00_project_setup.md",
)

T00_REQUIRED_DIRECTORIES = (
    "docs",
    "data",
    "data/raw",
    "data/interim",
    "data/processed",
    "notebooks",
    "src",
    "src/fdm_rainfall",
    "tests",
    "reports",
    "reports/figures",
    "reports/tables",
    "reports/evidence",
    "scripts",
)

T01_REQUIRED_FILES = (
    "data/raw/weatherAUS.csv",
    "notebooks/00_dataset_verification.ipynb",
    "src/fdm_rainfall/data.py",
    "src/fdm_rainfall/validation.py",
    "tests/test_validation.py",
    "reports/evidence/01_dataset_verification.md",
    "reports/tables/01_dataset_summary.csv",
    "reports/tables/01_column_names.csv",
    "reports/tables/01_column_schema.csv",
    "reports/tables/01_target_counts.csv",
    "reports/tables/01_duplicate_summary.csv",
    "reports/tables/01_proposal_verification.csv",
)

T02_REQUIRED_FILES = (
    "notebooks/01_data_understanding.ipynb",
    "docs/data_dictionary.md",
    "src/fdm_rainfall/understanding.py",
    "tests/test_understanding.py",
    "reports/evidence/02_data_understanding.md",
    "reports/tables/02_dataset_overview.csv",
    "reports/tables/02_column_inventory.csv",
    "reports/tables/02_feature_groups.csv",
    "reports/tables/02_numeric_summary.csv",
    "reports/tables/02_categorical_summary.csv",
    "reports/tables/02_categorical_frequencies.csv",
    "reports/tables/02_date_coverage_summary.csv",
    "reports/tables/02_year_counts.csv",
    "reports/tables/02_location_date_coverage.csv",
    "reports/tables/02_target_summary.csv",
    "reports/tables/02_range_checks.csv",
)

T03_REQUIRED_FILES = (
    "notebooks/02_eda_missing_values.ipynb",
    "src/fdm_rainfall/missing_values.py",
    "tests/test_missing_values.py",
    "reports/evidence/03_missing_values.md",
    "reports/tables/03_missing_summary.csv",
    "reports/tables/03_row_missing_overview.csv",
    "reports/tables/03_row_missing_distribution.csv",
    "reports/tables/03_location_missing_summary.csv",
    "reports/tables/03_complete_absence_locations.csv",
    "reports/tables/03_structural_missingness.csv",
    "reports/tables/03_temporal_missingness_summary.csv",
    "reports/tables/03_location_year_missingness.csv",
    "reports/tables/03_comissingness_summary.csv",
    "reports/tables/03_target_missingness_summary.csv",
    "reports/tables/03_target_missingness_by_location.csv",
    "reports/tables/03_target_missingness_by_year.csv",
    "reports/tables/03_rainfall_raintoday_missingness.csv",
    "reports/tables/03_proposal_missingness_comparison.csv",
    "reports/tables/03_interpretation_framework.csv",
    "reports/figures/missing_values/03_missing_percentage_by_feature.png",
    "reports/figures/missing_values/03_missingness_matrix_sample.png",
    "reports/figures/missing_values/03_station_missingness_major_features.png",
    "reports/figures/missing_values/03_temporal_missingness_major_features.png",
)

T04_REQUIRED_FILES = (
    "notebooks/03_eda_target_relationships.ipynb",
    "src/fdm_rainfall/relationships.py",
    "tests/test_relationships.py",
    "reports/evidence/04_target_relationships.md",
    "reports/tables/04_target_distribution.csv",
    "reports/tables/04_target_by_month.csv",
    "reports/tables/04_target_by_year.csv",
    "reports/tables/04_target_by_season.csv",
    "reports/tables/04_target_by_location.csv",
    "reports/tables/04_numeric_target_summary.csv",
    "reports/tables/04_categorical_target_summary.csv",
    "reports/tables/04_correlation_matrix.csv",
    "reports/tables/04_correlation_pairs.csv",
    "reports/tables/04_raintoday_rainfall_relationship.csv",
    "reports/tables/04_target_association_summary.csv",
    "reports/tables/04_relationship_interpretations.csv",
    "reports/figures/target_analysis/04_target_distribution.png",
    "reports/figures/target_analysis/04_temporal_target_patterns.png",
    "reports/figures/target_analysis/04_location_rain_rates.png",
    "reports/figures/relationships/04_numeric_target_boxplots.png",
    "reports/figures/relationships/04_categorical_target_rates.png",
    "reports/figures/relationships/04_numeric_correlation_heatmap.png",
)

T05_REQUIRED_FILES = (
    "notebooks/04_outlier_analysis.ipynb",
    "src/fdm_rainfall/outliers.py",
    "tests/test_outliers.py",
    "reports/evidence/05_outliers.md",
    "reports/tables/05_percentile_summary.csv",
    "reports/tables/05_outlier_summary.csv",
    "reports/tables/05_cloud9_investigation.csv",
    "reports/tables/05_humidity_boundary_summary.csv",
    "reports/tables/05_rainfall_skewness.csv",
    "reports/tables/05_extreme_pattern_summary.csv",
    "reports/tables/05_extreme_weather_context.csv",
    "reports/tables/05_suspicious_values.csv",
    "reports/tables/05_extreme_target_context.csv",
    "reports/tables/05_outlier_decision_summary.csv",
    "reports/tables/05_proposal_consistency.csv",
    "reports/figures/outliers/05_iqr_flagged_percentages.png",
    "reports/figures/outliers/05_numeric_boxplots.png",
    "reports/figures/outliers/05_rainfall_distribution_tail.png",
    "reports/figures/outliers/05_cloud9_occurrences.png",
    "reports/figures/outliers/05_evaporation_extremes.png",
    "reports/figures/outliers/05_wind_extremes.png",
)

T06_REQUIRED_FILES = (
    "notebooks/05_leakage_and_split_strategy.ipynb",
    "src/fdm_rainfall/data.py",
    "src/fdm_rainfall/validation.py",
    "tests/test_splitting.py",
    "docs/decisions/preprocessing_decisions.md",
    "reports/evidence/06_leakage_and_split.md",
    "reports/tables/06_split_summary.csv",
    "reports/tables/06_split_target_distribution.csv",
    "reports/tables/06_location_split_coverage.csv",
    "reports/tables/06_location_split_counts.csv",
    "reports/tables/06_leakage_risk_register.csv",
    "reports/tables/06_split_validation.csv",
    "reports/figures/leakage_split/06_chronological_split_timeline.png",
    "reports/figures/leakage_split/06_split_target_yes_rate.png",
)

T07_REQUIRED_FILES = (
    "notebooks/06_preprocessing.ipynb",
    "src/fdm_rainfall/preprocessing.py",
    "tests/test_preprocessing.py",
    "docs/decisions/preprocessing_decisions.md",
    "reports/evidence/07_preprocessing.md",
    "reports/tables/07_preprocessing_decisions.csv",
    "reports/tables/07_numeric_imputation_strategy.csv",
    "reports/tables/07_structural_imputation_summary.csv",
    "reports/tables/07_categorical_preprocessing_summary.csv",
    "reports/tables/07_missing_before_after.csv",
    "reports/tables/07_encoding_summary.csv",
    "reports/tables/07_scaling_summary.csv",
    "reports/tables/07_leakage_preprocessing_checks.csv",
    "reports/tables/07_processed_schema_summary.csv",
    "reports/figures/preprocessing/07_missingness_before_after.png",
    "reports/figures/preprocessing/07_structural_imputation_sources.png",
)

T08_REQUIRED_FILES = (
    "notebooks/07_feature_engineering.ipynb",
    "src/fdm_rainfall/features.py",
    "tests/test_features.py",
    "docs/decisions/feature_engineering_decisions.md",
    "reports/evidence/08_feature_engineering.md",
    "reports/tables/08_engineered_feature_inventory.csv",
    "reports/tables/08_feature_decisions.csv",
    "reports/tables/08_engineered_missingness.csv",
    "reports/tables/08_train_engineered_target_summary.csv",
    "reports/tables/08_feature_redundancy_summary.csv",
    "reports/tables/08_cyclical_wind_mapping.csv",
    "reports/tables/08_date_feature_summary.csv",
    "reports/tables/08_rainfall_transform_summary.csv",
    "reports/tables/08_engineered_schema_summary.csv",
    "reports/tables/08_feature_engineering_leakage_checks.csv",
    "reports/tables/08_final_feature_counts.csv",
    "reports/figures/feature_engineering/08_weather_difference_target_distributions.png",
    "reports/figures/feature_engineering/08_rainfall_raw_vs_log1p.png",
    "reports/figures/feature_engineering/08_cyclical_encodings.png",
)

EXPECTED_TASKS = (
    ("T00", "Project Setup"),
    ("T01", "Dataset Verification"),
    ("T02", "Data Understanding"),
    ("T03", "Missing-Value Analysis"),
    ("T04", "Target and Feature Relationship EDA"),
    ("T05", "Outlier and Suspicious-Value Analysis"),
    ("T06", "Leakage and Chronological Split Strategy"),
    ("T07", "Data Preprocessing"),
    ("T08", "Feature Engineering"),
)

ALLOWED_STATUSES = ("TODO", "IN PROGRESS", "BLOCKED", "DONE")
EXPECTED_PROPOSAL_CLAIMS = {
    "Total rows",
    "Total columns",
    "Unique locations",
    "Labelled RainTomorrow rows",
    "Missing RainTomorrow rows",
    "Date range",
    "RISK_MM exists",
}
REQUIRED_EVIDENCE_HEADINGS = (
    "## Task objective",
    "## Dataset path",
    "## Verification items performed",
    "## Actual dataset findings",
    "## Proposal comparison results",
    "## Files created/modified",
    "## Checks/tests executed",
    "## Unresolved issues",
    "## Final status",
)

T02_EVIDENCE_HEADINGS = (
    "## Task objective",
    "## What was analysed",
    "## Key dataset characteristics",
    "## Feature-type classification",
    "## Important basic observations",
    "## Items intentionally deferred to later tasks",
    "## Files created/modified",
    "## Checks/tests executed",
    "## Unresolved issues",
    "## Final status",
)

T03_EVIDENCE_HEADINGS = (
    "## Task objective",
    "## Analyses performed",
    "## Key missing-data findings",
    "## Structural missingness findings",
    "## Temporal findings",
    "## Co-missingness findings",
    "## Target missingness findings",
    "## Proposal comparison",
    "## Future preprocessing considerations",
    "## Files created/modified",
    "## Tests/checks executed",
    "## Unresolved questions",
    "## Final status",
)

T04_EVIDENCE_HEADINGS = (
    "## Task objective",
    "## Analyses performed",
    "## Target distribution findings",
    "## Temporal findings",
    "## Location findings",
    "## Major numerical relationships",
    "## Major categorical relationships",
    "## Correlation/redundancy findings",
    "## RainToday/Rainfall verification",
    "## Class-imbalance findings",
    "## Limitations caused by missingness",
    "## Future considerations",
    "## Files created/modified",
    "## Checks/tests executed",
    "## Unresolved questions",
    "## Final status",
)

T05_EVIDENCE_HEADINGS = (
    "## Task objective",
    "## Analyses performed",
    "## IQR findings",
    "## Skewness findings",
    "## Suspicious-value findings",
    "## Cloud value 9 investigation",
    "## Humidity boundary findings",
    "## Rainfall/evaporation/wind findings",
    "## Proposal consistency result",
    "## Classification of unusual values",
    "## Future preprocessing considerations",
    "## Files created/modified",
    "## Tests/checks executed",
    "## Unresolved questions",
    "## Final status",
)

T06_EVIDENCE_HEADINGS = (
    "## Task objective",
    "## Labelled analysis population",
    "## Leakage risks identified",
    "## Why chronological splitting was chosen",
    "## Split method",
    "## Exact split boundaries",
    "## Actual row proportions",
    "## Target distribution by split",
    "## Location coverage findings",
    "## Split validation results",
    "## Limitations",
    "## Controls planned for later preprocessing/modelling",
    "## Files created/modified",
    "## Tests/checks executed",
    "## Unresolved issues",
    "## Final status",
)

T07_EVIDENCE_HEADINGS = (
    "## Task objective",
    "## Input split sizes",
    "## Preprocessing decisions",
    "## Numerical missing-value strategy",
    "## Structural missingness strategy",
    "## Categorical strategy",
    "## Encoding strategy",
    "## Outlier decision",
    "## Scaling strategy",
    "## Leakage controls",
    "## Before/after missingness results",
    "## Processed feature counts",
    "## Tests/checks executed",
    "## Limitations",
    "## Items deferred to T08",
    "## Files created/modified",
    "## Unresolved issues",
    "## Final status",
)

T08_EVIDENCE_HEADINGS = (
    "## Task objective",
    "## Input split sizes",
    "## Features considered",
    "## Features implemented",
    "## Formulas",
    "## Train-only descriptive evidence",
    "## Retained features",
    "## Optional/deferred/rejected features",
    "## Redundancy discussion",
    "## Leakage controls",
    "## Integration with preprocessing",
    "## Processed feature counts",
    "## Missingness verification",
    "## Row/target integrity",
    "## Tests/checks executed",
    "## Limitations",
    "## Future modelling considerations",
    "## Files created/modified",
    "## Unresolved issues",
    "## Final status",
)


def _missing_files(relative_paths: tuple[str, ...]) -> list[str]:
    return [
        f"missing file: {relative_path}"
        for relative_path in relative_paths
        if not (PROJECT_ROOT / relative_path).is_file()
    ]


def run_t00_checks() -> list[str]:
    """Return descriptions of failed T00 checks."""

    failures = _missing_files(T00_REQUIRED_FILES)
    failures.extend(
        f"missing directory: {relative_path}/"
        for relative_path in T00_REQUIRED_DIRECTORIES
        if not (PROJECT_ROOT / relative_path).is_dir()
    )

    status_path = PROJECT_ROOT / "PROJECT_STATUS.md"
    if status_path.is_file():
        status_text = status_path.read_text(encoding="utf-8")
        for task_id, task_name in EXPECTED_TASKS:
            if f"| {task_id} | {task_name} |" not in status_text:
                failures.append(f"missing status task: {task_id} {task_name}")
        for status in ALLOWED_STATUSES:
            if status not in status_text:
                failures.append(f"missing allowed status declaration: {status}")

    return failures


def _check_notebook_execution(
    relative_path: str, task_label: str, failures: list[str]
) -> None:
    notebook_path = PROJECT_ROOT / relative_path
    if not notebook_path.is_file():
        return

    try:
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"could not read {task_label} notebook: {exc}")
        return

    code_cells = [cell for cell in notebook.get("cells", []) if cell.get("cell_type") == "code"]
    if not code_cells:
        failures.append(f"{task_label} notebook contains no code cells")
        return
    if any(cell.get("execution_count") is None for cell in code_cells):
        failures.append(f"{task_label} notebook has unexecuted code cells")
    if any(
        output.get("output_type") == "error"
        for cell in code_cells
        for output in cell.get("outputs", [])
    ):
        failures.append(f"{task_label} notebook contains error output")


def _check_proposal_table(failures: list[str]) -> None:
    table_path = PROJECT_ROOT / "reports/tables/01_proposal_verification.csv"
    if not table_path.is_file():
        return

    try:
        with table_path.open(encoding="utf-8", newline="") as table_file:
            rows = list(csv.DictReader(table_file))
    except OSError as exc:
        failures.append(f"could not read proposal comparison table: {exc}")
        return

    required_columns = {
        "Claim",
        "Expected value",
        "Actual dataset value",
        "Match / Mismatch",
        "Comment",
    }
    if not rows:
        failures.append("proposal comparison table is empty")
        return
    if not required_columns.issubset(rows[0]):
        failures.append("proposal comparison table is missing required columns")
    observed_claims = {row.get("Claim", "") for row in rows}
    missing_claims = EXPECTED_PROPOSAL_CLAIMS - observed_claims
    if missing_claims:
        failures.append(f"proposal table missing claims: {', '.join(sorted(missing_claims))}")
    if any(row.get("Match / Mismatch") not in {"Match", "Mismatch"} for row in rows):
        failures.append("proposal table contains an invalid comparison result")


def _check_evidence(failures: list[str]) -> None:
    evidence_path = PROJECT_ROOT / "reports/evidence/01_dataset_verification.md"
    if not evidence_path.is_file():
        return
    evidence_text = evidence_path.read_text(encoding="utf-8")
    for heading in REQUIRED_EVIDENCE_HEADINGS:
        if heading not in evidence_text:
            failures.append(f"T01 evidence missing heading: {heading}")


def _check_dataset_load_and_metrics(failures: list[str]) -> None:
    try:
        from fdm_rainfall.data import load_weather_data
        from fdm_rainfall.validation import verify_weather_dataset

        frame = load_weather_data(PROJECT_ROOT / "data/raw/weatherAUS.csv")
        result = verify_weather_dataset(frame)
    except Exception as exc:
        failures.append(f"dataset verification logic failed: {exc}")
        return

    if not result.rain_tomorrow_exists:
        failures.append("RainTomorrow column does not exist")
    if result.column_count != len(result.column_names):
        failures.append("column count does not match captured column names")
    if result.rain_tomorrow_labelled_count + result.rain_tomorrow_missing_count != result.row_count:
        failures.append("RainTomorrow labelled and missing counts do not reconcile to total rows")
    if result.invalid_date_count:
        failures.append(f"Date contains {result.invalid_date_count} invalid or missing values")


def _check_unit_tests(failures: list[str]) -> None:
    completed = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if completed.returncode != 0:
        details = (completed.stderr or completed.stdout).strip().splitlines()
        failures.append(f"unit tests failed: {details[-1] if details else 'unknown failure'}")


def run_t01_checks() -> list[str]:
    """Return descriptions of failed T01 checks."""

    failures = _missing_files(T01_REQUIRED_FILES)
    _check_dataset_load_and_metrics(failures)
    _check_notebook_execution(
        "notebooks/00_dataset_verification.ipynb", "T01", failures
    )
    _check_proposal_table(failures)
    _check_evidence(failures)
    _check_unit_tests(failures)
    return failures


def _read_csv_rows(relative_path: str, failures: list[str]) -> list[dict[str, str]]:
    table_path = PROJECT_ROOT / relative_path
    if not table_path.is_file():
        return []
    try:
        with table_path.open(encoding="utf-8", newline="") as table_file:
            return list(csv.DictReader(table_file))
    except OSError as exc:
        failures.append(f"could not read {relative_path}: {exc}")
        return []


def _check_t02_table_structures(failures: list[str]) -> None:
    expectations: dict[str, tuple[set[str], int | None]] = {
        "reports/tables/02_dataset_overview.csv": (
            {"Characteristic", "Value"},
            7,
        ),
        "reports/tables/02_column_inventory.csv": (
            {
                "Column",
                "Pandas dtype",
                "Logical variable type",
                "Non-null values",
                "Missing values",
                "Missing percentage",
                "Unique non-null values",
            },
            23,
        ),
        "reports/tables/02_feature_groups.csv": (
            {"Feature group", "Feature"},
            23,
        ),
        "reports/tables/02_numeric_summary.csv": (
            {
                "Feature",
                "Count",
                "Mean",
                "Standard deviation",
                "Minimum",
                "25th percentile",
                "Median",
                "75th percentile",
                "Maximum",
            },
            16,
        ),
        "reports/tables/02_categorical_summary.csv": (
            {
                "Feature",
                "Number of categories",
                "Category values",
                "Most frequent category",
                "Most frequent count",
                "Missing count",
            },
            6,
        ),
        "reports/tables/02_categorical_frequencies.csv": (
            {"Feature", "Category", "Count", "Percentage of non-null"},
            None,
        ),
        "reports/tables/02_date_coverage_summary.csv": (
            {"Date characteristic", "Value"},
            9,
        ),
        "reports/tables/02_year_counts.csv": ({"Year", "Record count"}, 11),
        "reports/tables/02_location_date_coverage.csv": (
            {"Location", "Start date", "End date", "Record count", "Unique dates"},
            49,
        ),
        "reports/tables/02_target_summary.csv": (
            {"Target characteristic", "Value"},
            6,
        ),
        "reports/tables/02_range_checks.csv": (
            {
                "Feature group",
                "Feature",
                "Unit / scale",
                "Non-null count",
                "Missing count",
                "Observed minimum",
                "Observed maximum",
                "Later-investigation flag",
            },
            16,
        ),
    }

    for relative_path, (required_columns, expected_rows) in expectations.items():
        rows = _read_csv_rows(relative_path, failures)
        if not rows:
            if (PROJECT_ROOT / relative_path).is_file():
                failures.append(f"T02 table is empty: {relative_path}")
            continue
        if not required_columns.issubset(rows[0]):
            failures.append(f"T02 table missing required columns: {relative_path}")
        if expected_rows is not None and len(rows) != expected_rows:
            failures.append(
                f"T02 table {relative_path} has {len(rows)} rows; expected {expected_rows}"
            )


def _check_t02_dictionary(failures: list[str]) -> None:
    dictionary_path = PROJECT_ROOT / "docs/data_dictionary.md"
    if not dictionary_path.is_file():
        return

    dictionary_text = dictionary_path.read_text(encoding="utf-8")
    required_headers = (
        "Feature name",
        "Description",
        "Data type",
        "Logical type",
        "Unit / category meaning",
        "Role",
        "Basic data-quality note",
        "Possible preprocessing consideration",
    )
    for header in required_headers:
        if header not in dictionary_text:
            failures.append(f"data dictionary missing field: {header}")

    try:
        from fdm_rainfall.understanding import LOGICAL_TYPES
    except Exception as exc:
        failures.append(f"could not import T02 dictionary schema: {exc}")
        return
    for column in LOGICAL_TYPES:
        if f"| {column} |" not in dictionary_text:
            failures.append(f"data dictionary missing feature: {column}")


def _check_t02_helper_outputs(failures: list[str]) -> None:
    try:
        from fdm_rainfall.data import load_weather_data
        from fdm_rainfall.understanding import (
            basic_range_checks,
            categorical_summary,
            column_inventory,
            data_dictionary,
            date_understanding,
            feature_group_table,
            numerical_summary,
            target_summary,
        )

        frame = load_weather_data(PROJECT_ROOT / "data/raw/weatherAUS.csv")
        inventory = column_inventory(frame)
        groups = feature_group_table()
        numeric = numerical_summary(frame)
        categorical = categorical_summary(frame)
        dates = date_understanding(frame)
        target = target_summary(frame)
        ranges = basic_range_checks(frame)
        dictionary = data_dictionary(frame)
    except Exception as exc:
        failures.append(f"T02 reusable analysis failed: {exc}")
        return

    expected_counts = {
        "column inventory": (len(inventory), 23),
        "feature grouping": (len(groups), 23),
        "numerical summary": (len(numeric), 16),
        "categorical summary": (len(categorical), 6),
        "year coverage": (len(dates.year_counts), 11),
        "location coverage": (len(dates.location_coverage), 49),
        "target summary": (len(target), 6),
        "range checks": (len(ranges), 16),
        "data dictionary": (len(dictionary), 23),
    }
    for label, (actual, expected) in expected_counts.items():
        if actual != expected:
            failures.append(f"T02 {label} has {actual} rows; expected {expected}")

    if set(groups["Feature"]) != set(frame.columns) or groups["Feature"].duplicated().any():
        failures.append("T02 feature groups do not cover every column exactly once")
    if not (
        inventory["Non-null values"] + inventory["Missing values"] == len(frame)
    ).all():
        failures.append("T02 column inventory counts do not reconcile to dataset rows")


def _check_t02_evidence(failures: list[str]) -> None:
    evidence_path = PROJECT_ROOT / "reports/evidence/02_data_understanding.md"
    if not evidence_path.is_file():
        return
    evidence_text = evidence_path.read_text(encoding="utf-8")
    for heading in T02_EVIDENCE_HEADINGS:
        if heading not in evidence_text:
            failures.append(f"T02 evidence missing heading: {heading}")


def run_t02_checks() -> list[str]:
    """Return descriptions of failed T02 checks."""

    failures = _missing_files(T02_REQUIRED_FILES)
    _check_notebook_execution("notebooks/01_data_understanding.ipynb", "T02", failures)
    _check_t02_table_structures(failures)
    _check_t02_dictionary(failures)
    _check_t02_helper_outputs(failures)
    _check_t02_evidence(failures)
    return failures


def _check_t03_table_structures(failures: list[str]) -> None:
    expectations: dict[str, tuple[set[str], int | None]] = {
        "reports/tables/03_missing_summary.csv": (
            {"Feature", "Missing count", "Missing percentage", "Non-missing count", "Descriptive severity"},
            23,
        ),
        "reports/tables/03_row_missing_overview.csv": (
            {"Row-missingness metric", "Value"},
            7,
        ),
        "reports/tables/03_row_missing_distribution.csv": (
            {"Missing fields per row", "Row count", "Row percentage"},
            None,
        ),
        "reports/tables/03_location_missing_summary.csv": (
            {"Location", "Feature", "Record count", "Missing count", "Missing percentage", "Non-missing count", "Coverage classification"},
            441,
        ),
        "reports/tables/03_complete_absence_locations.csv": (
            {"Location", "Feature", "Missing percentage", "Coverage classification"},
            71,
        ),
        "reports/tables/03_structural_missingness.csv": (
            {"Feature", "Complete-absence locations", "Provisional pattern", "Mechanism caveat"},
            9,
        ),
        "reports/tables/03_temporal_missingness_summary.csv": (
            {"Period type", "Period", "Feature", "Missing count", "Missing percentage"},
            207,
        ),
        "reports/tables/03_location_year_missingness.csv": (
            {"Location", "Year", "Feature", "Record count", "Missing count", "Missing percentage"},
            4077,
        ),
        "reports/tables/03_comissingness_summary.csv": (
            {"Group", "Feature A", "Feature B", "Both missing", "Jaccard co-missingness percentage", "Identical missingness masks"},
            19,
        ),
        "reports/tables/03_target_missingness_summary.csv": (
            {"Target-missingness metric", "Value"},
            18,
        ),
        "reports/tables/03_target_missingness_by_location.csv": (
            {"Location", "Missing target count", "Missing target percentage", "Missing at station end"},
            49,
        ),
        "reports/tables/03_target_missingness_by_year.csv": (
            {"Year", "Record count", "Missing target count", "Missing target percentage"},
            11,
        ),
        "reports/tables/03_rainfall_raintoday_missingness.csv": (
            {"Relationship metric", "Value"},
            6,
        ),
        "reports/tables/03_proposal_missingness_comparison.csv": (
            {"Claim", "Expected value", "Actual dataset value", "Match / Mismatch", "Comment"},
            13,
        ),
        "reports/tables/03_interpretation_framework.csv": (
            {"Finding", "Observation", "Interpretation", "Future preprocessing consideration"},
            5,
        ),
    }
    for relative_path, (required_columns, expected_rows) in expectations.items():
        rows = _read_csv_rows(relative_path, failures)
        if not rows:
            if (PROJECT_ROOT / relative_path).is_file():
                failures.append(f"T03 table is empty: {relative_path}")
            continue
        if not required_columns.issubset(rows[0]):
            failures.append(f"T03 table missing required columns: {relative_path}")
        if expected_rows is not None and len(rows) != expected_rows:
            failures.append(
                f"T03 table {relative_path} has {len(rows)} rows; expected {expected_rows}"
            )

    proposal_rows = _read_csv_rows(
        "reports/tables/03_proposal_missingness_comparison.csv", failures
    )
    if any(row.get("Match / Mismatch") not in {"Match", "Mismatch"} for row in proposal_rows):
        failures.append("T03 proposal table contains an invalid comparison result")


def _check_t03_figures(failures: list[str]) -> None:
    figure_paths = [path for path in T03_REQUIRED_FILES if path.endswith(".png")]
    for relative_path in figure_paths:
        path = PROJECT_ROOT / relative_path
        if path.is_file() and path.stat().st_size < 10_000:
            failures.append(f"T03 figure appears empty or incomplete: {relative_path}")


def _check_t03_helper_outputs(failures: list[str]) -> None:
    try:
        from fdm_rainfall.data import load_weather_data
        from fdm_rainfall.missing_values import (
            comissingness_summary,
            location_missingness,
            location_year_missingness,
            missing_summary,
            proposal_missingness_comparison,
            rainfall_raintoday_relationship,
            row_missingness,
            structural_missingness_summary,
            target_missingness,
            temporal_missingness,
        )

        frame = load_weather_data(PROJECT_ROOT / "data/raw/weatherAUS.csv")
        overall = missing_summary(frame)
        rows = row_missingness(frame)
        location = location_missingness(frame)
        temporal = temporal_missingness(frame)
        location_year = location_year_missingness(frame)
        structural = structural_missingness_summary(frame, location, temporal, location_year)
        comissing = comissingness_summary(frame)
        target = target_missingness(frame)
        rain_pair = rainfall_raintoday_relationship(frame)
        proposal = proposal_missingness_comparison(frame, structural)
    except Exception as exc:
        failures.append(f"T03 reusable analysis failed: {exc}")
        return

    expected_counts = {
        "overall missingness": (len(overall), 23),
        "location missingness": (len(location), 441),
        "temporal missingness": (len(temporal), 207),
        "location-year missingness": (len(location_year), 4077),
        "structural summary": (len(structural), 9),
        "co-missingness summary": (len(comissing), 19),
        "target location summary": (len(target.by_location), 49),
        "target year summary": (len(target.by_year), 11),
        "rain relationship": (len(rain_pair), 6),
        "proposal comparison": (len(proposal), 13),
    }
    for label, (actual, expected) in expected_counts.items():
        if actual != expected:
            failures.append(f"T03 {label} has {actual} rows; expected {expected}")

    if int(rows.distribution["Row count"].sum()) != len(frame):
        failures.append("T03 row-level missingness does not reconcile to dataset rows")
    if not (
        overall["Missing count"] + overall["Non-missing count"] == len(frame)
    ).all():
        failures.append("T03 feature missingness does not reconcile to dataset rows")


def _check_t03_evidence(failures: list[str]) -> None:
    evidence_path = PROJECT_ROOT / "reports/evidence/03_missing_values.md"
    if not evidence_path.is_file():
        return
    evidence_text = evidence_path.read_text(encoding="utf-8")
    for heading in T03_EVIDENCE_HEADINGS:
        if heading not in evidence_text:
            failures.append(f"T03 evidence missing heading: {heading}")


def run_t03_checks() -> list[str]:
    """Return descriptions of failed T03 checks."""

    failures = _missing_files(T03_REQUIRED_FILES)
    _check_notebook_execution("notebooks/02_eda_missing_values.ipynb", "T03", failures)
    _check_t03_table_structures(failures)
    _check_t03_figures(failures)
    _check_t03_helper_outputs(failures)
    _check_t03_evidence(failures)
    return failures


def _check_t04_table_structures(failures: list[str]) -> None:
    expectations: dict[str, tuple[set[str], int]] = {
        "reports/tables/04_target_distribution.csv": (
            {"Metric", "Value", "Context"},
            8,
        ),
        "reports/tables/04_target_by_month.csv": (
            {"Month number", "Month", "Labelled record count", "Yes count", "No count", "Rain rate (Yes percentage)"},
            12,
        ),
        "reports/tables/04_target_by_year.csv": (
            {"Year", "Labelled record count", "Yes count", "No count", "Rain rate (Yes percentage)"},
            11,
        ),
        "reports/tables/04_target_by_season.csv": (
            {"Season", "Labelled record count", "Rain rate (Yes percentage)", "EDA-only derivation note"},
            4,
        ),
        "reports/tables/04_target_by_location.csv": (
            {"Location", "Labelled record count", "Yes count", "No count", "Rain rate (Yes percentage)", "Observation-count flag", "Rain-rate position"},
            49,
        ),
        "reports/tables/04_numeric_target_summary.csv": (
            {"Feature", "RainTomorrow", "Available count", "Missing within class", "Mean", "Standard deviation", "25th percentile", "Median", "75th percentile"},
            32,
        ),
        "reports/tables/04_categorical_target_summary.csv": (
            {"Feature", "Category", "Category frequency among labelled rows", "Yes count", "No count", "RainTomorrow Yes rate"},
            103,
        ),
        "reports/tables/04_correlation_matrix.csv": (
            {"Feature", "MinTemp", "MaxTemp", "Humidity9am", "Humidity3pm", "Pressure9am", "Pressure3pm"},
            16,
        ),
        "reports/tables/04_correlation_pairs.csv": (
            {"Feature A", "Feature B", "Pearson correlation", "Absolute correlation", "Pairwise available count", "Descriptive strength"},
            120,
        ),
        "reports/tables/04_raintoday_rainfall_relationship.csv": (
            {"Metric", "Value", "Context"},
            15,
        ),
        "reports/tables/04_target_association_summary.csv": (
            {"Feature", "Feature type", "Observed relationship with RainTomorrow", "Descriptive association assessment", "Missingness concern", "Redundancy concern", "Future consideration"},
            21,
        ),
        "reports/tables/04_relationship_interpretations.csv": (
            {"Feature", "Observation", "Interpretation", "Future consideration"},
            10,
        ),
    }
    for relative_path, (required_columns, expected_rows) in expectations.items():
        rows = _read_csv_rows(relative_path, failures)
        if not rows:
            if (PROJECT_ROOT / relative_path).is_file():
                failures.append(f"T04 table is empty: {relative_path}")
            continue
        if not required_columns.issubset(rows[0]):
            failures.append(f"T04 table missing required columns: {relative_path}")
        if len(rows) != expected_rows:
            failures.append(
                f"T04 table {relative_path} has {len(rows)} rows; expected {expected_rows}"
            )


def _check_t04_figures(failures: list[str]) -> None:
    for relative_path in [path for path in T04_REQUIRED_FILES if path.endswith(".png")]:
        path = PROJECT_ROOT / relative_path
        if path.is_file() and path.stat().st_size < 10_000:
            failures.append(f"T04 figure appears empty or incomplete: {relative_path}")


def _check_t04_helper_outputs(failures: list[str]) -> None:
    try:
        from fdm_rainfall.data import load_weather_data
        from fdm_rainfall.relationships import (
            categorical_target_summary,
            correlation_analysis,
            location_target_rates,
            numeric_target_summary,
            raintoday_rainfall_relationship,
            relationship_interpretations,
            target_association_summary,
            target_distribution,
            temporal_target_rates,
        )

        frame = load_weather_data(PROJECT_ROOT / "data/raw/weatherAUS.csv")
        target = target_distribution(frame)
        temporal = temporal_target_rates(frame)
        location = location_target_rates(frame)
        numeric = numeric_target_summary(frame)
        categorical = categorical_target_summary(frame)
        correlations = correlation_analysis(frame)
        rain_pair = raintoday_rainfall_relationship(frame)
        associations = target_association_summary(frame, numeric, categorical)
        interpretations = relationship_interpretations(associations)
    except Exception as exc:
        failures.append(f"T04 reusable analysis failed: {exc}")
        return

    expected_counts = {
        "target distribution": (len(target), 8),
        "monthly target summary": (len(temporal.by_month), 12),
        "yearly target summary": (len(temporal.by_year), 11),
        "season target summary": (len(temporal.by_season), 4),
        "location target summary": (len(location), 49),
        "numerical target summary": (len(numeric), 32),
        "categorical target summary": (len(categorical), 103),
        "correlation matrix": (len(correlations.matrix), 16),
        "correlation pairs": (len(correlations.pairs), 120),
        "RainToday/Rainfall comparison": (len(rain_pair), 15),
        "target association summary": (len(associations), 21),
        "important relationship interpretations": (len(interpretations), 10),
    }
    for label, (actual, expected) in expected_counts.items():
        if actual != expected:
            failures.append(f"T04 {label} has {actual} rows; expected {expected}")

    metrics = target.set_index("Metric")["Value"]
    if int(float(metrics["Labelled total"])) + int(float(metrics["Missing target count"])) != len(frame):
        failures.append("T04 labelled and missing target counts do not reconcile to dataset rows")
    if int(location["Labelled record count"].sum()) != int(float(metrics["Labelled total"])):
        failures.append("T04 location-labelled counts do not reconcile to labelled target rows")
    rain_metrics = rain_pair.set_index("Metric")["Value"]
    if rain_metrics["Proposal claim (approximately 98.8%)"] not in {"Match", "Mismatch"}:
        failures.append("T04 RainToday/Rainfall proposal comparison is invalid")
    if rain_metrics["Proposal threshold definition"] != "Minor mismatch / boundary clarification":
        failures.append("T04 proposal threshold boundary clarification is missing or invalid")


def _check_t04_evidence(failures: list[str]) -> None:
    evidence_path = PROJECT_ROOT / "reports/evidence/04_target_relationships.md"
    if not evidence_path.is_file():
        return
    evidence_text = evidence_path.read_text(encoding="utf-8")
    for heading in T04_EVIDENCE_HEADINGS:
        if heading not in evidence_text:
            failures.append(f"T04 evidence missing heading: {heading}")


def run_t04_checks() -> list[str]:
    """Return descriptions of failed T04 checks."""

    failures = _missing_files(T04_REQUIRED_FILES)
    _check_notebook_execution("notebooks/03_eda_target_relationships.ipynb", "T04", failures)
    _check_t04_table_structures(failures)
    _check_t04_figures(failures)
    _check_t04_helper_outputs(failures)
    _check_t04_evidence(failures)
    return failures


def _check_t05_table_structures(failures: list[str]) -> None:
    expectations: dict[str, tuple[set[str], int]] = {
        "reports/tables/05_percentile_summary.csv": (
            {"Feature", "Non-missing count", "Minimum", "1st percentile", "5th percentile", "25th percentile", "Median", "75th percentile", "95th percentile", "99th percentile", "Maximum", "IQR", "Skewness"},
            16,
        ),
        "reports/tables/05_outlier_summary.csv": (
            {"Feature", "Q1", "Q3", "IQR", "Lower fence", "Upper fence", "Count below lower fence", "Count above upper fence", "Total IQR-flagged", "Percentage IQR-flagged"},
            16,
        ),
        "reports/tables/05_cloud9_investigation.csv": (
            {"Feature", "Value", "Date", "Location", "Year", "Month", "Pattern assessment"},
            3,
        ),
        "reports/tables/05_humidity_boundary_summary.csv": (
            {"Feature", "Minimum", "Maximum", "Count below 0", "Count equal to 0", "Count equal to 100", "Count above 100", "Outside 0–100 range"},
            2,
        ),
        "reports/tables/05_rainfall_skewness.csv": (
            {"Rainfall metric", "Value", "Context"},
            13,
        ),
        "reports/tables/05_extreme_pattern_summary.csv": (
            {"Feature", "99th-percentile threshold", "Count at/above threshold", "Locations represented", "Years represented", "Observed maximum", "Maximum occurrence count", "Pattern assessment"},
            4,
        ),
        "reports/tables/05_extreme_weather_context.csv": (
            {"Selected feature", "Selected rule", "Selected value", "Date", "Location", "RainTomorrow"},
            6,
        ),
        "reports/tables/05_suspicious_values.csv": (
            {"Feature", "Trigger", "Value", "Date", "Location", "RainTomorrow", "Classification"},
            14,
        ),
        "reports/tables/05_extreme_target_context.csv": (
            {"Feature", "Trigger", "Selected_record_count", "Labelled_target_count", "Yes_count", "No_count", "Yes percentage among labelled"},
            8,
        ),
        "reports/tables/05_outlier_decision_summary.csv": (
            {"Feature", "Observed unusual value / rule", "Number affected", "Percentage affected", "Statistical outlier?", "Domain-plausible?", "Classification", "Recommended future handling", "Reason"},
            18,
        ),
        "reports/tables/05_proposal_consistency.csv": (
            {"Claim", "Expected", "Actual", "Match / Mismatch", "Comment"},
            6,
        ),
    }
    for relative_path, (required_columns, expected_rows) in expectations.items():
        rows = _read_csv_rows(relative_path, failures)
        if not rows:
            if (PROJECT_ROOT / relative_path).is_file():
                failures.append(f"T05 table is empty: {relative_path}")
            continue
        if not required_columns.issubset(rows[0]):
            failures.append(f"T05 table missing required columns: {relative_path}")
        if len(rows) != expected_rows:
            failures.append(
                f"T05 table {relative_path} has {len(rows)} rows; expected {expected_rows}"
            )

    decisions = _read_csv_rows("reports/tables/05_outlier_decision_summary.csv", failures)
    allowed = {
        "likely valid extreme",
        "suspicious / investigate later",
        "likely invalid",
        "unresolved",
    }
    if any(row.get("Classification") not in allowed for row in decisions):
        failures.append("T05 decision table contains an invalid classification")
    proposal = _read_csv_rows("reports/tables/05_proposal_consistency.csv", failures)
    if any(row.get("Match / Mismatch") not in {"Match", "Mismatch"} for row in proposal):
        failures.append("T05 proposal table contains an invalid comparison result")


def _check_t05_figures(failures: list[str]) -> None:
    for relative_path in [path for path in T05_REQUIRED_FILES if path.endswith(".png")]:
        path = PROJECT_ROOT / relative_path
        if path.is_file() and path.stat().st_size < 10_000:
            failures.append(f"T05 figure appears empty or incomplete: {relative_path}")


def _check_t05_helper_outputs(failures: list[str]) -> None:
    try:
        from fdm_rainfall.data import load_weather_data
        from fdm_rainfall.outliers import (
            ALLOWED_CLASSIFICATIONS,
            cloud_nine_investigation,
            extreme_pattern_summary,
            extreme_weather_context,
            humidity_boundary_summary,
            iqr_outlier_summary,
            outlier_decision_summary,
            percentile_summary,
            proposal_consistency,
            rainfall_skewness_summary,
            suspicious_value_details,
        )

        frame = load_weather_data(PROJECT_ROOT / "data/raw/weatherAUS.csv")
        percentiles = percentile_summary(frame)
        iqr = iqr_outlier_summary(frame)
        cloud = cloud_nine_investigation(frame)
        humidity = humidity_boundary_summary(frame)
        rainfall = rainfall_skewness_summary(frame)
        patterns = extreme_pattern_summary(frame)
        context = extreme_weather_context(frame)
        suspicious = suspicious_value_details(frame)
        decisions = outlier_decision_summary(frame)
        proposal = proposal_consistency(frame)
    except Exception as exc:
        failures.append(f"T05 reusable analysis failed: {exc}")
        return

    expected_counts = {
        "percentile summary": (len(percentiles), 16),
        "IQR summary": (len(iqr), 16),
        "cloud value-9 details": (len(cloud), 3),
        "humidity boundary summary": (len(humidity), 2),
        "rainfall summary": (len(rainfall), 13),
        "extreme pattern summary": (len(patterns), 4),
        "specific extreme context": (len(context), 6),
        "suspicious-value details": (len(suspicious), 14),
        "decision summary": (len(decisions), 18),
        "proposal comparison": (len(proposal), 6),
    }
    for label, (actual, expected) in expected_counts.items():
        if actual != expected:
            failures.append(f"T05 {label} has {actual} rows; expected {expected}")

    if frame.shape != (145_460, 23):
        failures.append(f"T05 raw dataset shape changed unexpectedly: {frame.shape}")
    if int(humidity["Outside 0–100 range"].sum()) != 0:
        failures.append("T05 humidity boundary result unexpectedly contains out-of-range values")
    if int((cloud["Feature"] == "Cloud9am").sum()) != 2 or int((cloud["Feature"] == "Cloud3pm").sum()) != 1:
        failures.append("T05 cloud value-9 counts do not match the dataset")
    if not set(decisions["Classification"]).issubset(ALLOWED_CLASSIFICATIONS):
        failures.append("T05 helper returned an invalid unusual-value classification")
    if decisions["Classification"].eq("likely invalid").any():
        failures.append("T05 classified a value as likely invalid without the documented evidence threshold")


def _check_t05_evidence(failures: list[str]) -> None:
    evidence_path = PROJECT_ROOT / "reports/evidence/05_outliers.md"
    if not evidence_path.is_file():
        return
    evidence_text = evidence_path.read_text(encoding="utf-8")
    for heading in T05_EVIDENCE_HEADINGS:
        if heading not in evidence_text:
            failures.append(f"T05 evidence missing heading: {heading}")


def run_t05_checks() -> list[str]:
    """Return descriptions of failed T05 checks."""

    failures = _missing_files(T05_REQUIRED_FILES)
    _check_notebook_execution("notebooks/04_outlier_analysis.ipynb", "T05", failures)
    _check_t05_table_structures(failures)
    _check_t05_figures(failures)
    _check_t05_helper_outputs(failures)
    _check_t05_evidence(failures)
    return failures


def _check_t06_table_structures(failures: list[str]) -> None:
    expectations: dict[str, tuple[set[str], int]] = {
        "reports/tables/06_split_summary.csv": (
            {
                "Split",
                "First date",
                "Last date",
                "Rows",
                "Percentage of labelled rows",
                "Unique dates",
                "Locations",
                "RainTomorrow No count",
                "RainTomorrow Yes count",
                "Yes percentage",
                "Missing target count",
            },
            3,
        ),
        "reports/tables/06_split_target_distribution.csv": (
            {
                "Split",
                "Rows",
                "RainTomorrow No count",
                "RainTomorrow Yes count",
                "Yes percentage",
                "Missing target count",
            },
            3,
        ),
        "reports/tables/06_location_split_coverage.csv": (
            {
                "Location",
                "First labelled date",
                "Last labelled date",
                "Present in Train",
                "Present in Validation",
                "Present in Test",
                "Present in all three",
            },
            49,
        ),
        "reports/tables/06_location_split_counts.csv": (
            {"Location", "Train", "Validation", "Test"},
            49,
        ),
        "reports/tables/06_leakage_risk_register.csv": (
            {
                "Risk",
                "Example in this project",
                "Potential consequence",
                "Control / prevention",
                "Stage where controlled",
                "Status",
            },
            10,
        ),
        "reports/tables/06_split_validation.csv": (
            {"Check", "Result", "Details"},
            9,
        ),
    }
    for relative_path, (required_columns, expected_rows) in expectations.items():
        rows = _read_csv_rows(relative_path, failures)
        if not rows:
            if (PROJECT_ROOT / relative_path).is_file():
                failures.append(f"T06 table is empty: {relative_path}")
            continue
        if not required_columns.issubset(rows[0]):
            failures.append(f"T06 table missing required columns: {relative_path}")
        if len(rows) != expected_rows:
            failures.append(
                f"T06 table {relative_path} has {len(rows)} rows; expected {expected_rows}"
            )

    validation_rows = _read_csv_rows("reports/tables/06_split_validation.csv", failures)
    if any(row.get("Result") != "PASS" for row in validation_rows):
        failures.append("T06 saved split validation contains a failed check")

    risk_rows = _read_csv_rows("reports/tables/06_leakage_risk_register.csv", failures)
    required_risks = {
        "Target leakage",
        "RISK_MM leakage",
        "Imputation leakage",
        "Encoding leakage",
        "Scaling leakage",
        "Feature-selection leakage",
        "Resampling leakage",
        "Temporal leakage",
        "Future-derived feature leakage",
        "Test-set reuse / tuning leakage",
    }
    if {row.get("Risk") for row in risk_rows} != required_risks:
        failures.append("T06 leakage register does not contain the required risks")


def _check_t06_figures(failures: list[str]) -> None:
    for relative_path in [path for path in T06_REQUIRED_FILES if path.endswith(".png")]:
        path = PROJECT_ROOT / relative_path
        if path.is_file() and path.stat().st_size < 10_000:
            failures.append(f"T06 figure appears empty or incomplete: {relative_path}")


def _check_t06_helper_outputs(failures: list[str]) -> None:
    try:
        from fdm_rainfall.data import (
            chronological_train_validation_test_split,
            load_weather_data,
            location_split_tables,
        )
        from fdm_rainfall.validation import (
            leakage_risk_register,
            validate_chronological_split,
            verify_weather_dataset,
        )

        frame = load_weather_data(PROJECT_ROOT / "data/raw/weatherAUS.csv")
        dataset_check = verify_weather_dataset(frame)
        split = chronological_train_validation_test_split(frame)
        split_validation = validate_chronological_split(
            split.train,
            split.validation,
            split.test,
            labelled_population_size=dataset_check.rain_tomorrow_labelled_count,
        )
        location_coverage, location_counts = location_split_tables(split)
        risks = leakage_risk_register()
    except Exception as exc:
        failures.append(f"T06 reusable split analysis failed: {exc}")
        return

    if frame.shape != (145_460, 23):
        failures.append(f"T06 raw dataset shape changed unexpectedly: {frame.shape}")
    if dataset_check.rain_tomorrow_labelled_count != 142_193:
        failures.append(
            "T06 labelled population is "
            f"{dataset_check.rain_tomorrow_labelled_count}; expected 142193"
        )
    if int(split.summary["Rows"].sum()) != dataset_check.rain_tomorrow_labelled_count:
        failures.append("T06 split rows do not sum to the labelled population")
    if split.summary["Split"].tolist() != ["Train", "Validation", "Test"]:
        failures.append("T06 split summary is not in chronological subset order")
    if split.summary["Last date"].tolist()[:2] != ["2015-01-12", "2016-04-08"]:
        failures.append("T06 split boundaries differ from the verified whole-date boundaries")
    if not split_validation["Result"].eq("PASS").all():
        failures.append("T06 reusable split validation returned a failed check")
    if len(location_coverage) != 49 or len(location_counts) != 49:
        failures.append("T06 location coverage does not include all 49 locations")
    if int(location_coverage["Present in all three"].sum()) != 48:
        failures.append("T06 all-three-split location count differs from the verified value 48")
    if len(risks) != 10:
        failures.append("T06 leakage register does not contain 10 required risks")


def _check_t06_documentation(failures: list[str]) -> None:
    evidence_path = PROJECT_ROOT / "reports/evidence/06_leakage_and_split.md"
    if evidence_path.is_file():
        evidence_text = evidence_path.read_text(encoding="utf-8")
        for heading in T06_EVIDENCE_HEADINGS:
            if heading not in evidence_text:
                failures.append(f"T06 evidence missing heading: {heading}")

    decision_path = PROJECT_ROOT / "docs/decisions/preprocessing_decisions.md"
    if decision_path.is_file():
        decision_text = decision_path.read_text(encoding="utf-8")
        if "## Chronological Split and Leakage Prevention" not in decision_text:
            failures.append("T06 decision document is missing the required section")


def run_t06_checks() -> list[str]:
    """Return descriptions of failed T06 checks."""

    failures = _missing_files(T06_REQUIRED_FILES)
    _check_notebook_execution("notebooks/05_leakage_and_split_strategy.ipynb", "T06", failures)
    _check_t06_table_structures(failures)
    _check_t06_figures(failures)
    _check_t06_helper_outputs(failures)
    _check_t06_documentation(failures)
    _check_unit_tests(failures)
    return failures


def _check_t07_table_structures(failures: list[str]) -> None:
    expectations: dict[str, tuple[set[str], int]] = {
        "reports/tables/07_preprocessing_decisions.csv": (
            {
                "Feature / Feature group",
                "Issue",
                "Evidence",
                "Options considered",
                "Chosen preprocessing",
                "Why chosen",
                "Train-only fitted?",
                "Future consideration",
            },
            10,
        ),
        "reports/tables/07_numeric_imputation_strategy.csv": (
            {
                "Feature",
                "Raw missing %",
                "Train missing %",
                "Missingness pattern",
                "Chosen strategy",
                "Statistic/grouping used",
                "Train-only fitted?",
                "Missing indicator added?",
                "Reason",
            },
            16,
        ),
        "reports/tables/07_structural_imputation_summary.csv": (
            {
                "Split",
                "Feature",
                "Missing rows",
                "Location-median imputations",
                "Global-fallback imputations",
                "Train global median",
            },
            12,
        ),
        "reports/tables/07_categorical_preprocessing_summary.csv": (
            {
                "Feature",
                "Missing-value treatment",
                "Encoder",
                "Encoded columns",
                "Validation unknown rows",
                "Test unknown rows",
                "Train-only fitted?",
            },
            5,
        ),
        "reports/tables/07_missing_before_after.csv": (
            {
                "Split",
                "Rows before",
                "Rows after",
                "Predictor missing cells before",
                "Unscaled missing cells after",
                "Scaled missing cells after",
                "Target rows aligned",
            },
            3,
        ),
        "reports/tables/07_encoding_summary.csv": (
            {"Feature", "Encoded columns", "Validation unknown rows", "Test unknown rows"},
            5,
        ),
        "reports/tables/07_scaling_summary.csv": (
            {
                "Feature",
                "Train-fitted mean",
                "Train-fitted scale",
                "Fit rows",
                "Validation/Test used in fit?",
                "Scaled path",
                "Unscaled path available?",
            },
            16,
        ),
        "reports/tables/07_leakage_preprocessing_checks.csv": (
            {"Check", "Passed", "Evidence", "Result"},
            13,
        ),
        "reports/tables/07_processed_schema_summary.csv": (
            {
                "Processed feature",
                "Role",
                "Present in unscaled path",
                "Present in scaled path",
                "Scaled in scaled path",
            },
            124,
        ),
    }
    for relative_path, (required_columns, expected_rows) in expectations.items():
        rows = _read_csv_rows(relative_path, failures)
        if not rows:
            if (PROJECT_ROOT / relative_path).is_file():
                failures.append(f"T07 table is empty: {relative_path}")
            continue
        if not required_columns.issubset(rows[0]):
            failures.append(f"T07 table missing required columns: {relative_path}")
        if len(rows) != expected_rows:
            failures.append(
                f"T07 table {relative_path} has {len(rows)} rows; expected {expected_rows}"
            )

    leakage_rows = _read_csv_rows(
        "reports/tables/07_leakage_preprocessing_checks.csv", failures
    )
    if any(row.get("Result") != "PASS" for row in leakage_rows):
        failures.append("T07 saved leakage table contains a failed check")

    missing_rows = _read_csv_rows("reports/tables/07_missing_before_after.csv", failures)
    for row in missing_rows:
        if row.get("Rows before") != row.get("Rows after"):
            failures.append("T07 preprocessing changed a split row count")
        if row.get("Unscaled missing cells after") != "0":
            failures.append("T07 unscaled output contains missing values")
        if row.get("Scaled missing cells after") != "0":
            failures.append("T07 scaled output contains missing values")


def _check_t07_figures(failures: list[str]) -> None:
    for relative_path in [path for path in T07_REQUIRED_FILES if path.endswith(".png")]:
        path = PROJECT_ROOT / relative_path
        if path.is_file() and path.stat().st_size < 10_000:
            failures.append(f"T07 figure appears empty or incomplete: {relative_path}")


def _check_t07_helper_outputs(failures: list[str]) -> None:
    try:
        import numpy as np

        from fdm_rainfall.data import (
            chronological_train_validation_test_split,
            load_weather_data,
        )
        from fdm_rainfall.preprocessing import (
            CATEGORICAL_PREDICTORS,
            NUMERICAL_PREDICTORS,
            STRUCTURAL_NUMERICAL_PREDICTORS,
            RainfallPreprocessor,
            separate_supervised_components,
        )

        frame = load_weather_data(PROJECT_ROOT / "data/raw/weatherAUS.csv")
        split = chronological_train_validation_test_split(frame)
        components = {
            name: separate_supervised_components(part)
            for name, part in split.frames.items()
        }
        unscaled = RainfallPreprocessor(scale_numeric=False).fit(components["Train"].X)
        scaled = RainfallPreprocessor(scale_numeric=True).fit(components["Train"].X)
    except Exception as exc:
        failures.append(f"T07 reusable preprocessing failed: {exc}")
        return

    expected_rows = {"Train": 99_546, "Validation": 21_342, "Test": 21_305}
    for name, part in components.items():
        try:
            unscaled_output = unscaled.transform(part.X)
            scaled_output = scaled.transform(part.X)
        except Exception as exc:
            failures.append(f"T07 {name} transformation failed: {exc}")
            continue
        if len(unscaled_output) != expected_rows[name] or len(scaled_output) != expected_rows[name]:
            failures.append(f"T07 {name} transformation changed row count")
        if not unscaled_output.index.equals(part.y.index):
            failures.append(f"T07 {name} target alignment changed")
        if unscaled_output.isna().any().any() or scaled_output.isna().any().any():
            failures.append(f"T07 {name} output contains missing values")
        if {"RainTomorrow", "Date", "RISK_MM"}.intersection(unscaled_output.columns):
            failures.append(f"T07 {name} output contains a leakage/temporal column")

    if split.summary["Last date"].tolist()[:2] != ["2015-01-12", "2016-04-08"]:
        failures.append("T07 changed the verified T06 split boundaries")
    if unscaled.fit_row_count_ != 99_546 or scaled.fit_row_count_ != 99_546:
        failures.append("T07 preprocessors were not fitted on exactly the Train rows")
    if len(unscaled.get_feature_names_out()) != 124:
        failures.append("T07 processed schema does not contain 124 features")
    if len(unscaled.encoded_feature_names_) != 104:
        failures.append("T07 one-hot encoding does not contain 104 columns")
    if len(unscaled.indicator_feature_names_) != 4:
        failures.append("T07 structural preprocessing does not contain four indicators")

    train_medians = components["Train"].X.loc[:, NUMERICAL_PREDICTORS].median()
    if not unscaled.numeric_medians_.equals(train_medians):
        failures.append("T07 numeric medians differ from independent Train calculations")
    for feature in STRUCTURAL_NUMERICAL_PREDICTORS:
        expected = components["Train"].X.groupby("Location", dropna=False)[feature].median()
        if not unscaled.structural_location_medians_[feature].equals(expected):
            failures.append(f"T07 {feature} Location medians differ from Train calculations")

    imputed_train, _ = scaled.impute_numeric(components["Train"].X)
    expected_mean = imputed_train.loc[:, NUMERICAL_PREDICTORS].mean().to_numpy()
    if not np.allclose(scaled.scaler_.mean_, expected_mean):
        failures.append("T07 scaler mean differs from the imputed Train mean")

    encoded_counts = {
        feature: sum(name.startswith(f"{feature}_") for name in unscaled.encoded_feature_names_)
        for feature in CATEGORICAL_PREDICTORS
    }
    if encoded_counts != {
        "Location": 50,
        "WindGustDir": 17,
        "WindDir9am": 17,
        "WindDir3pm": 17,
        "RainToday": 3,
    }:
        failures.append(f"T07 encoded category counts are unexpected: {encoded_counts}")

    unseen = components["Validation"].X.iloc[[0]].copy()
    unseen["Location"] = "UNSEEN_VALIDATION_LOCATION"
    try:
        unscaled.transform(unseen)
    except Exception as exc:
        failures.append(f"T07 unknown-category handling failed: {exc}")

    raw_hash = hashlib.sha256((PROJECT_ROOT / "data/raw/weatherAUS.csv").read_bytes()).hexdigest().upper()
    expected_hash = "573FD715CD69FCACC4DF32024D823B450AE3EDAAE7E8FF2EEB623ADBED424014"
    if raw_hash != expected_hash:
        failures.append(f"T07 raw dataset checksum changed: {raw_hash}")


def _check_t07_documentation(failures: list[str]) -> None:
    evidence_path = PROJECT_ROOT / "reports/evidence/07_preprocessing.md"
    if evidence_path.is_file():
        evidence_text = evidence_path.read_text(encoding="utf-8")
        for heading in T07_EVIDENCE_HEADINGS:
            if heading not in evidence_text:
                failures.append(f"T07 evidence missing heading: {heading}")

    decision_path = PROJECT_ROOT / "docs/decisions/preprocessing_decisions.md"
    if decision_path.is_file():
        decision_text = decision_path.read_text(encoding="utf-8")
        required_sections = (
            "## Chronological Split and Leakage Prevention",
            "## T07 Data Preprocessing Decisions",
            "### Target handling",
            "### Duplicate handling",
            "### Missing numerical data",
            "### Structural missingness",
            "### Categorical missing data",
            "### Categorical encoding",
            "### Outlier handling",
            "### Scaling strategy",
            "### Leakage prevention",
            "### RainToday/Rainfall redundancy",
            "### Limitations and decisions deferred to T08 or modelling",
        )
        for section in required_sections:
            if section not in decision_text:
                failures.append(f"T07 decision document missing section: {section}")


def run_t07_checks() -> list[str]:
    """Return descriptions of failed T07 checks."""

    failures = _missing_files(T07_REQUIRED_FILES)
    _check_notebook_execution("notebooks/06_preprocessing.ipynb", "T07", failures)
    _check_t07_table_structures(failures)
    _check_t07_figures(failures)
    _check_t07_helper_outputs(failures)
    _check_t07_documentation(failures)
    _check_unit_tests(failures)
    return failures


def _check_t08_table_structures(failures: list[str]) -> None:
    expectations: dict[str, tuple[set[str], int]] = {
        "reports/tables/08_engineered_feature_inventory.csv": (
            {
                "Feature", "Source columns", "Type", "Formula / mapping",
                "Missing-value behavior", "Rationale", "Train-only descriptive finding",
                "Redundancy concern", "Leakage concern", "Decision", "Reason",
                "Preprocessing requirement", "Retained in default engineered schema?",
            },
            25,
        ),
        "reports/tables/08_feature_decisions.csv": (
            {"Feature", "Decision", "Retained in default engineered schema?", "Reason"},
            25,
        ),
        "reports/tables/08_engineered_missingness.csv": (
            {"Split", "Feature", "Rows", "Missing count", "Missing percentage", "Handling"},
            60,
        ),
        "reports/tables/08_train_engineered_target_summary.csv": (
            {"Feature", "RainTomorrow", "Observed count", "Missing count", "Mean", "Median", "Q1", "Q3"},
            38,
        ),
        "reports/tables/08_feature_redundancy_summary.csv": (
            {"Engineered feature", "Compared with", "Train Pearson correlation", "Decision", "Reason"},
            13,
        ),
        "reports/tables/08_cyclical_wind_mapping.csv": (
            {"Direction", "Degrees", "Radians", "Sine", "Cosine"},
            16,
        ),
        "reports/tables/08_date_feature_summary.csv": (
            {"Feature", "Train minimum", "Train maximum", "Unique values", "Decision", "Reason"},
            5,
        ),
        "reports/tables/08_rainfall_transform_summary.csv": (
            {"Representation", "Observed Train rows", "Missing Train rows", "Skewness", "Q99", "Maximum", "Decision"},
            2,
        ),
        "reports/tables/08_engineered_schema_summary.csv": (
            {"Processed feature", "Source", "Role", "Data type", "Missing-value behavior", "Leakage risk", "Preprocessing requirement"},
            89,
        ),
        "reports/tables/08_feature_engineering_leakage_checks.csv": (
            {"Check", "Passed", "Evidence", "Result"},
            12,
        ),
        "reports/tables/08_final_feature_counts.csv": (
            {"Stage", "Measure", "Count", "Explanation"},
            12,
        ),
    }
    for relative_path, (required_columns, expected_rows) in expectations.items():
        rows = _read_csv_rows(relative_path, failures)
        if not rows:
            if (PROJECT_ROOT / relative_path).is_file():
                failures.append(f"T08 table is empty: {relative_path}")
            continue
        if not required_columns.issubset(rows[0]):
            failures.append(f"T08 table missing required columns: {relative_path}")
        if len(rows) != expected_rows:
            failures.append(
                f"T08 table {relative_path} has {len(rows)} rows; expected {expected_rows}"
            )

    decisions = _read_csv_rows("reports/tables/08_feature_decisions.csv", failures)
    allowed = {"KEEP", "OPTIONAL", "DROP", "DEFERRED"}
    if any(row.get("Decision") not in allowed for row in decisions):
        failures.append("T08 decision table contains a decision outside the allowed vocabulary")
    expected_features = {
        "Year", "Month", "Season", "Month_sin", "Month_cos", "TempRange",
        "TempChange", "HumidityChange", "PressureChange", "WindSpeedChange",
        "WindGustDir_sin", "WindGustDir_cos", "WindDir9am_sin", "WindDir9am_cos",
        "WindDir3pm_sin", "WindDir3pm_cos", "WindGustDir_missing",
        "WindDir9am_missing", "WindDir3pm_missing", "Sunshine_missing",
        "Evaporation_missing", "Cloud9am_missing", "Cloud3pm_missing",
        "Rainfall_log1p", "ClimateZone",
    }
    if {row.get("Feature") for row in decisions} != expected_features:
        failures.append("T08 decision table does not contain the exact required feature inventory")

    leakage = _read_csv_rows(
        "reports/tables/08_feature_engineering_leakage_checks.csv", failures
    )
    if any(row.get("Result") != "PASS" for row in leakage):
        failures.append("T08 saved leakage table contains a failed check")


def _check_t08_figures(failures: list[str]) -> None:
    for relative_path in [path for path in T08_REQUIRED_FILES if path.endswith(".png")]:
        path = PROJECT_ROOT / relative_path
        if path.is_file() and path.stat().st_size < 10_000:
            failures.append(f"T08 figure appears empty or incomplete: {relative_path}")


def _check_t08_helper_outputs(failures: list[str]) -> None:
    try:
        import numpy as np

        from fdm_rainfall.data import (
            chronological_train_validation_test_split,
            load_weather_data,
        )
        from fdm_rainfall.features import (
            DEFAULT_ENGINEERED_PREDICTORS,
            WeatherFeatureEngineer,
        )
        from fdm_rainfall.preprocessing import (
            RainfallPreprocessor,
            fit_transform_engineered_chronological_splits,
            fit_transform_chronological_splits,
        )

        frame = load_weather_data(PROJECT_ROOT / "data/raw/weatherAUS.csv")
        split = chronological_train_validation_test_split(frame)
        engineered = fit_transform_engineered_chronological_splits(split)
        engineered_scaled = fit_transform_engineered_chronological_splits(
            split, scale_numeric=True
        )
        original = fit_transform_chronological_splits(split)
    except Exception as exc:
        failures.append(f"T08 reusable feature-engineering pipeline failed: {exc}")
        return

    expected_rows = {"Train": 99_546, "Validation": 21_342, "Test": 21_305}
    expected_dates = {
        "Train": ("2007-11-01", "2015-01-12"),
        "Validation": ("2015-01-13", "2016-04-08"),
        "Test": ("2016-04-09", "2017-06-25"),
    }
    for name, part in split.frames.items():
        actual_dates = (
            part["Date"].min().date().isoformat(),
            part["Date"].max().date().isoformat(),
        )
        if len(part) != expected_rows[name] or actual_dates != expected_dates[name]:
            failures.append(f"T08 changed the verified T06 {name} split")

    outputs = {
        "Train": (engineered.X_train, engineered_scaled.X_train, engineered.y_train, engineered.dates_train),
        "Validation": (engineered.X_validation, engineered_scaled.X_validation, engineered.y_validation, engineered.dates_validation),
        "Test": (engineered.X_test, engineered_scaled.X_test, engineered.y_test, engineered.dates_test),
    }
    for name, (unscaled, scaled, target, dates) in outputs.items():
        if len(unscaled) != expected_rows[name] or len(scaled) != expected_rows[name]:
            failures.append(f"T08 {name} feature engineering changed row count")
        if not unscaled.index.equals(target.index) or not unscaled.index.equals(dates.index):
            failures.append(f"T08 {name} target/date alignment changed")
        if unscaled.isna().any().any() or scaled.isna().any().any():
            failures.append(f"T08 {name} processed output contains missing values")
        if np.isinf(unscaled.to_numpy(dtype=float)).any() or np.isinf(scaled.to_numpy(dtype=float)).any():
            failures.append(f"T08 {name} processed output contains infinite values")
        if {"RainTomorrow", "Date", "RISK_MM"}.intersection(unscaled.columns):
            failures.append(f"T08 {name} processed output contains leakage/temporal columns")

    if engineered.preprocessor.fit_row_count_ != 99_546:
        failures.append("T08 engineered preprocessor was not fitted on exactly Train")
    if len(engineered.feature_engineer.get_feature_names_out()) != 34:
        failures.append("T08 default raw engineered schema does not contain 34 features")
    if tuple(engineered.feature_engineer.get_feature_names_out()) != DEFAULT_ENGINEERED_PREDICTORS:
        failures.append("T08 default engineered feature order is not deterministic")
    if len(engineered.preprocessor.get_feature_names_out()) != 89:
        failures.append("T08 final processed engineered schema does not contain 89 features")
    if len(set(engineered.preprocessor.get_feature_names_out())) != 89:
        failures.append("T08 final processed schema contains duplicate feature names")
    if len(original.preprocessor.get_feature_names_out()) != 124:
        failures.append("T08 broke the original 124-feature T07 configuration")

    raw_input = split.train.drop(columns=["RainTomorrow"])
    changed_target = split.train.copy()
    changed_target["RainTomorrow"] = changed_target["RainTomorrow"].map({"No": "Yes", "Yes": "No"})
    target_free = WeatherFeatureEngineer().fit_transform(raw_input)
    target_present = WeatherFeatureEngineer().fit_transform(changed_target)
    if not target_free.equals(target_present):
        failures.append("T08 engineered predictors depend on RainTomorrow values")

    raw_hash = hashlib.sha256((PROJECT_ROOT / "data/raw/weatherAUS.csv").read_bytes()).hexdigest().upper()
    expected_hash = "573FD715CD69FCACC4DF32024D823B450AE3EDAAE7E8FF2EEB623ADBED424014"
    if raw_hash != expected_hash:
        failures.append(f"T08 raw dataset checksum changed: {raw_hash}")


def _check_t08_documentation(failures: list[str]) -> None:
    evidence_path = PROJECT_ROOT / "reports/evidence/08_feature_engineering.md"
    if evidence_path.is_file():
        evidence_text = evidence_path.read_text(encoding="utf-8")
        for heading in T08_EVIDENCE_HEADINGS:
            if heading not in evidence_text:
                failures.append(f"T08 evidence missing heading: {heading}")

    decision_path = PROJECT_ROOT / "docs/decisions/feature_engineering_decisions.md"
    if decision_path.is_file():
        decision_text = decision_path.read_text(encoding="utf-8")
        required_sections = (
            "## Feature-engineering principles", "## Date features",
            "## Weather difference features", "## Wind cyclical representation",
            "## Missing indicators", "## Rainfall transformation", "## Year caution",
            "## Month/Season redundancy", "## Climate-zone decision",
            "## Retained, optional, dropped, and deferred features",
            "## Leakage prevention", "## Limitations and future model-stage evaluation",
        )
        for section in required_sections:
            if section not in decision_text:
                failures.append(f"T08 decision document missing section: {section}")

    status_path = PROJECT_ROOT / "PROJECT_STATUS.md"
    if status_path.is_file() and "| T08 | Feature Engineering | DONE |" not in status_path.read_text(encoding="utf-8"):
        failures.append("T08 is not marked DONE with verification evidence in PROJECT_STATUS.md")


def _check_t08_scope(failures: list[str]) -> None:
    notebook_path = PROJECT_ROOT / "notebooks/07_feature_engineering.ipynb"
    executable_texts = [
        (PROJECT_ROOT / "src/fdm_rainfall/features.py").read_text(encoding="utf-8"),
        (PROJECT_ROOT / "src/fdm_rainfall/preprocessing.py").read_text(encoding="utf-8"),
        (PROJECT_ROOT / "tests/test_features.py").read_text(encoding="utf-8"),
    ]
    if notebook_path.is_file():
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
        executable_texts.append(
            "\n".join(
                "".join(cell.get("source", []))
                for cell in notebook.get("cells", [])
                if cell.get("cell_type") == "code"
            )
        )
    forbidden_calls = (
        "DummyClassifier(", "LogisticRegression(", "DecisionTreeClassifier(",
        "RandomForestClassifier(", "GradientBoostingClassifier(", "XGBClassifier(",
        "LGBMClassifier(", "GridSearchCV(", "RandomizedSearchCV(", "SMOTE(",
    )
    for token in forbidden_calls:
        if any(token in text for text in executable_texts):
            failures.append(f"T08 executable code contains out-of-scope operation: {token}")

    forbidden_path_parts = {"backend", "frontend", "models", "modeling"}
    for path in PROJECT_ROOT.rglob("*"):
        if ".git" in path.parts:
            continue
        if forbidden_path_parts.intersection(part.lower() for part in path.parts):
            failures.append(f"T08 found an out-of-scope project path: {path.relative_to(PROJECT_ROOT)}")
            break


def run_t08_checks() -> list[str]:
    """Return descriptions of failed T08 checks."""

    failures = _missing_files(T08_REQUIRED_FILES)
    _check_notebook_execution("notebooks/07_feature_engineering.ipynb", "T08", failures)
    _check_t08_table_structures(failures)
    _check_t08_figures(failures)
    _check_t08_helper_outputs(failures)
    _check_t08_documentation(failures)
    _check_t08_scope(failures)
    _check_unit_tests(failures)
    return failures


def _print_result(task: str, failures: list[str]) -> None:
    if failures:
        print(f"FAIL: {task}")
        for failure in failures:
            print(f"- {failure}")
    else:
        print(f"PASS: {task}")


def main() -> int:
    """Print T00 through T08 verification results and return an exit code."""

    t00_failures = run_t00_checks()
    t01_failures = run_t01_checks()
    t02_failures = run_t02_checks()
    t03_failures = run_t03_checks()
    t04_failures = run_t04_checks()
    t05_failures = run_t05_checks()
    t06_failures = run_t06_checks()
    t07_failures = run_t07_checks()
    t08_failures = run_t08_checks()
    _print_result("T00 Project Setup", t00_failures)
    _print_result("T01 Dataset Verification", t01_failures)
    _print_result("T02 Data Understanding", t02_failures)
    _print_result("T03 Missing-Value Analysis", t03_failures)
    _print_result("T04 Target and Feature Relationship EDA", t04_failures)
    _print_result("T05 Outlier and Suspicious-Value Analysis", t05_failures)
    _print_result("T06 Leakage and Chronological Split Strategy", t06_failures)
    _print_result("T07 Data Preprocessing", t07_failures)
    _print_result("T08 Feature Engineering", t08_failures)

    if (
        t00_failures
        or t01_failures
        or t02_failures
        or t03_failures
        or t04_failures
        or t05_failures
        or t06_failures
        or t07_failures
        or t08_failures
    ):
        return 1

    print(
        f"Verified {len(T00_REQUIRED_FILES)} T00 files, "
        f"{len(T00_REQUIRED_DIRECTORIES)} directories, and "
        f"{len(T01_REQUIRED_FILES)} T01 artifacts, and "
        f"{len(T02_REQUIRED_FILES)} T02 artifacts, and "
        f"{len(T03_REQUIRED_FILES)} T03 artifacts, and "
        f"{len(T04_REQUIRED_FILES)} T04 artifacts, and "
        f"{len(T05_REQUIRED_FILES)} T05 artifacts, and "
        f"{len(T06_REQUIRED_FILES)} T06 artifacts, and "
        f"{len(T07_REQUIRED_FILES)} T07 artifacts, and "
        f"{len(T08_REQUIRED_FILES)} T08 artifacts.\n"
        "PROGRESS EVALUATION 1 IMPLEMENTATION STAGE COMPLETE"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
