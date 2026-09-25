"""Verify the completed T00 through T03 stage requirements."""

from __future__ import annotations

import csv
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


def _print_result(task: str, failures: list[str]) -> None:
    if failures:
        print(f"FAIL: {task}")
        for failure in failures:
            print(f"- {failure}")
    else:
        print(f"PASS: {task}")


def main() -> int:
    """Print T00 through T03 verification results and return an exit code."""

    t00_failures = run_t00_checks()
    t01_failures = run_t01_checks()
    t02_failures = run_t02_checks()
    t03_failures = run_t03_checks()
    _print_result("T00 Project Setup", t00_failures)
    _print_result("T01 Dataset Verification", t01_failures)
    _print_result("T02 Data Understanding", t02_failures)
    _print_result("T03 Missing-Value Analysis", t03_failures)

    if t00_failures or t01_failures or t02_failures or t03_failures:
        return 1

    print(
        f"Verified {len(T00_REQUIRED_FILES)} T00 files, "
        f"{len(T00_REQUIRED_DIRECTORIES)} directories, and "
        f"{len(T01_REQUIRED_FILES)} T01 artifacts, and "
        f"{len(T02_REQUIRED_FILES)} T02 artifacts, and "
        f"{len(T03_REQUIRED_FILES)} T03 artifacts."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
