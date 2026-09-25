"""Verify the completed T00 and T01 stage requirements."""

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


def _check_notebook_execution(failures: list[str]) -> None:
    notebook_path = PROJECT_ROOT / "notebooks/00_dataset_verification.ipynb"
    if not notebook_path.is_file():
        return

    try:
        notebook = json.loads(notebook_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        failures.append(f"could not read notebook: {exc}")
        return

    code_cells = [cell for cell in notebook.get("cells", []) if cell.get("cell_type") == "code"]
    if not code_cells:
        failures.append("verification notebook contains no code cells")
        return
    if any(cell.get("execution_count") is None for cell in code_cells):
        failures.append("verification notebook has unexecuted code cells")
    if any(
        output.get("output_type") == "error"
        for cell in code_cells
        for output in cell.get("outputs", [])
    ):
        failures.append("verification notebook contains error output")


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
    _check_notebook_execution(failures)
    _check_proposal_table(failures)
    _check_evidence(failures)
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
    """Print T00 and T01 verification results and return a process exit code."""

    t00_failures = run_t00_checks()
    t01_failures = run_t01_checks()
    _print_result("T00 Project Setup", t00_failures)
    _print_result("T01 Dataset Verification", t01_failures)

    if t00_failures or t01_failures:
        return 1

    print(
        f"Verified {len(T00_REQUIRED_FILES)} T00 files, "
        f"{len(T00_REQUIRED_DIRECTORIES)} directories, and "
        f"{len(T01_REQUIRED_FILES)} T01 artifacts."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
