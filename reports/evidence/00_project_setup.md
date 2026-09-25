# T00 Project Setup Evidence

## Task objective

Create the initial repository structure and a repeatable verification script for
the IT3051 mini project without starting dataset or modelling work.

## Files created

- `README.md`
- `AGENTS.md`
- `PROJECT_STATUS.md`
- `requirements.txt`
- `.gitignore`
- `src/fdm_rainfall/__init__.py`
- `scripts/verify_stage1.py`
- Empty-directory placeholder files (`.gitkeep`) in the requested directories

## Verification performed

Command: `python scripts/verify_stage1.py`

The verifier checks that all required T00 files and directories exist and that
all requested tasks and allowed status values appear in `PROJECT_STATUS.md`.

## Verification result

`PASS: T00 Project Setup`

The successful run verified 8 required files and 14 required directories. An
initial run exposed an overly strict task-table text check in the verifier; the
check was corrected to recognize Markdown table columns, and the rerun exited
successfully with status code `0`.

## Unresolved issues

None identified during setup.

## Final status

DONE
