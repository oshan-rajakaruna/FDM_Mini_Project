# Project Status

Allowed statuses: `TODO`, `IN PROGRESS`, `BLOCKED`, `DONE`.

## Definition of DONE

A task may be marked `DONE` only if:

1. Required files exist.
2. Required code executes successfully.
3. Relevant checks/tests pass.
4. Required evidence/output exists.
5. `PROJECT_STATUS.md` contains verification evidence.

## Task tracker

| ID | Task | Status | Verification evidence |
|---|---|---|---|
| T00 | Project Setup | DONE | `python scripts/verify_stage1.py` passed (8 files and 14 directories verified); see `reports/evidence/00_project_setup.md`. |
| T01 | Dataset Verification | DONE | Dataset loaded; all required checks completed; notebook executed without errors; 4 unit tests and `python scripts/verify_stage1.py` passed. See `reports/evidence/01_dataset_verification.md`. |
| T02 | Data Understanding | DONE | Complete 23-column inventory, feature groups, numerical/categorical/date/target/range summaries, and data dictionary created; notebook executed without errors; 10 tests and `python scripts/verify_stage1.py` passed. See `reports/evidence/02_data_understanding.md`. |
| T03 | Missing-Value Analysis | TODO | Not started. |
| T04 | Target and Feature Relationship EDA | TODO | Not started. |
| T05 | Outlier and Suspicious-Value Analysis | TODO | Not started. |
| T06 | Leakage and Chronological Split Strategy | TODO | Not started. |
| T07 | Data Preprocessing | TODO | Not started. |
| T08 | Feature Engineering | TODO | Not started. |
