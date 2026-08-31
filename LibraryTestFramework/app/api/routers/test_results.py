"""
Admin-only endpoints for viewing and triggering test runs.

GET  /tests/results  — return the latest test results summary
POST /tests/run      — trigger a test run and return results
"""
import json
import os
import subprocess
import sys

from fastapi import APIRouter, Depends

from app.api.deps import require_roles
from app.models import UserRole

router = APIRouter(prefix="/tests", tags=["test-results"])

# Project root is three levels up from this file
# (app/api/routers/test_results.py -> app/api -> app -> LibraryTestFramework)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
REPORTS_DIR = os.path.join(PROJECT_ROOT, "tests", "reports")
RESULTS_JSON = os.path.join(REPORTS_DIR, "results.json")
COVERAGE_JSON = os.path.join(REPORTS_DIR, "coverage.json")

# Hardcoded pytest command — never accepts user input
PYTEST_CMD = [
    sys.executable, "-m", "pytest",
    "tests/unit", "tests/integration",
    "--json-report",
    f"--json-report-file={RESULTS_JSON}",
    "--cov=app",
    "--cov-report=json",
    "--cov-report=term:skip-covered",
    "--tb=short",
    "-q",
]


def _read_report() -> dict:
    """Parse the latest results.json and coverage.json into a summary dict."""
    summary = {
        "last_run": None,
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "total": 0,
        "duration": 0.0,
        "coverage_percent": None,
        "report_path": "/static/reports/report.html",
    }

    if os.path.isfile(RESULTS_JSON):
        try:
            with open(RESULTS_JSON, "r") as f:
                data = json.load(f)
            s = data.get("summary", {})
            summary["passed"] = s.get("passed", 0)
            summary["failed"] = s.get("failed", 0)
            summary["skipped"] = s.get("skipped", 0)
            summary["total"] = s.get("total", 0)
            summary["duration"] = data.get("duration", 0.0)
            # Try to determine when the report was last generated
            summary["last_run"] = os.path.getmtime(RESULTS_JSON)
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

    if os.path.isfile(COVERAGE_JSON):
        try:
            with open(COVERAGE_JSON, "r") as f:
                cov = json.load(f)
            totals = cov.get("totals", {})
            summary["coverage_percent"] = round(totals.get("percent_covered", 0.0), 2)
        except (json.JSONDecodeError, KeyError, TypeError):
            pass

    return summary


@router.get("/results")
def get_test_results(_user=Depends(require_roles(UserRole.ADMIN))):
    """Return the latest test results summary.

    If no report files exist yet, return 200 with null/zero values.
    """
    return _read_report()


@router.post("/run")
def run_tests(_user=Depends(require_roles(UserRole.ADMIN))):
    """Trigger a test run via subprocess and return the results summary.

    Uses a hardcoded pytest command.  If the process fails or times out,
    still returns 200 with whatever partial results can be gathered.
    """
    os.makedirs(REPORTS_DIR, exist_ok=True)

    try:
        result = subprocess.run(
            PYTEST_CMD,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except subprocess.TimeoutExpired:
        # Timeout — return whatever we had before
        return _read_report()
    except Exception:
        return _read_report()

    # After the run, read the (potentially updated) report
    return _read_report()
