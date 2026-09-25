"""Verify the required T00 Project Setup structure."""

from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "README.md",
    "AGENTS.md",
    "PROJECT_STATUS.md",
    "requirements.txt",
    ".gitignore",
    "src/fdm_rainfall/__init__.py",
    "scripts/verify_stage1.py",
    "reports/evidence/00_project_setup.md",
)

REQUIRED_DIRECTORIES = (
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


def run_checks() -> list[str]:
    """Return descriptions of all failed T00 checks."""
    failures: list[str] = []

    for relative_path in REQUIRED_FILES:
        path = PROJECT_ROOT / relative_path
        if not path.is_file():
            failures.append(f"missing file: {relative_path}")

    for relative_path in REQUIRED_DIRECTORIES:
        path = PROJECT_ROOT / relative_path
        if not path.is_dir():
            failures.append(f"missing directory: {relative_path}/")

    status_path = PROJECT_ROOT / "PROJECT_STATUS.md"
    if status_path.is_file():
        status_text = status_path.read_text(encoding="utf-8")
        for task_id, task_name in EXPECTED_TASKS:
            table_entry = f"| {task_id} | {task_name} |"
            if table_entry not in status_text:
                failures.append(f"missing status task: {task_id} {task_name}")
        for status in ALLOWED_STATUSES:
            if status not in status_text:
                failures.append(f"missing allowed status declaration: {status}")

    return failures


def main() -> int:
    """Print the T00 verification result and return a process exit code."""
    failures = run_checks()
    if failures:
        print("FAIL: T00 Project Setup")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("PASS: T00 Project Setup")
    print(f"Verified {len(REQUIRED_FILES)} files and {len(REQUIRED_DIRECTORIES)} directories.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
