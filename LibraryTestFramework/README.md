# Automated Testing Framework for a Library Management Web Application

[![CI](https://img.shields.io/badge/CI-GitHub_Actions-2088FF?logo=githubactions&logoColor=white)](../.github/workflows/ci.yml) [![Tests](https://img.shields.io/badge/tests-150_passed-brightgreen)](#5-current-test-suite) [![Coverage](https://img.shields.io/badge/coverage-91%25%20%28gate%2085%25%29-brightgreen)](#11-reports-and-coverage) [![Property-based](https://img.shields.io/badge/property--based-Hypothesis-9B5DE5)](#testing-techniques) [![e2e](https://img.shields.io/badge/e2e-Selenium_nightly-FF6B6B)](#continuous-integration)

## 1. Project Overview

This project is a small Library Management web application used as a **System Under Test (SUT)** for a multi-level automated testing framework.

The main focus of the project is not the library application itself, but the design of a maintainable automated testing solution covering:

- Unit testing
- API/database integration testing
- End-to-end browser testing
- Mocking
- Test-data generation
- Test reporting and coverage
- Continuous integration

## 2. Technology Stack

### Application

- FastAPI
- SQLAlchemy
- SQLite
- Next.js frontend

### Testing

- pytest
- FastAPI `TestClient`
- Selenium WebDriver
- Page Object Model (POM)
- `unittest.mock`
- Faker
- Factory Boy
- pytest-html
- pytest-cov
- pytest-json-report
- Hypothesis (property-based testing)
- freezegun (deterministic time)

### CI/CD

- GitHub Actions

## 3. Testing Architecture

```text
                         pytest
                           |
          +----------------+----------------+
          |                |                |
       Unit Tests     Integration Tests   E2E Tests
          |                |                |
     Mocked repos      TestClient       Selenium
          |                |                |
      Services      API + Test DB       Page Objects
                           |
                    SQLAlchemy + SQLite
```

More detailed diagrams are in [`docs/testing-strategy.md`](docs/testing-strategy.md).

### Architecture and UML diagrams

- [Use Case Diagram](docs/diagrams/use-case.svg) — actors and major library workflows
- [Application Architecture](docs/diagrams/architecture.svg) — frontend, API, services, repositories, and database
- [Testing Architecture](docs/diagrams/testing-architecture.svg) — unit, integration, and E2E layers
- PlantUML source files are provided alongside the diagrams for reproducibility.

## 4. Test Organization

```text
tests/
├── unit/
│   ├── test_book_service.py
│   ├── test_borrowing_service.py
│   ├── test_member_service.py
│   ├── test_reservation_service.py
│   ├── test_property_borrowing.py   # Hypothesis + freezegun invariants
│   └── test_factories.py
│
├── integration/
│   ├── conftest.py
│   ├── test_api.py
│   ├── test_auth_security.py        # expired/tampered/forged JWT attacks
│   └── test_concurrency.py          # real-thread race conditions
│
├── e2e/
│   ├── pages/
│   │   ├── base_page.py
│   │   ├── login_page.py
│   │   ├── home_page.py
│   │   ├── book_detail_page.py
│   │   ├── admin_page.py
│   │   └── member_page.py
│   └── test_e2e.py
│
├── conftest.py
├── helpers.py
└── factories.py

Legacy duplicates of the unit/integration/e2e suites are kept at the
repository root (tests/test_borrowing_service.py, tests/test_integration.py,
tests/test_e2e.py) for history; the organized tree above is authoritative.
```

## 5. Current Test Suite

The organized suite contains **119 test functions** (150 execute when legacy
root-level duplicates are included):

| Level | Tests | Purpose |
|---|---:|---|
| Unit | 71 | Business logic, validation, edge cases, fine/due-date property invariants, factories |
| Integration | 35 | HTTP API, auth, RBAC, JWT security attacks, plan changes, concurrency races |
| E2E | 13 | Critical browser/user workflows incl. membership plan switching |
| **Total** | **119** | |

Last full local run: **150 passed, 1 skipped, coverage 91.30%** (gate: 85%).

The counts above are based on the current test source. They are source counts, not a claim that the suite has been executed in this environment. Regenerate execution reports after the final local run.

## 6. Testing Techniques

### Unit Testing

Business services are tested independently of the database using mocked repositories.

Important cases include:

- happy paths
- invalid states
- business-rule violations
- boundary values
- unavailable copies
- borrowing limits
- fine thresholds
- reservation behavior
- regression cases

### Property-Based Testing (Hypothesis + freezegun)

Beyond fixed examples, `tests/unit/test_property_borrowing.py` generates
hundreds of arbitrary clocks, due dates, loan periods, and fine rates, and
asserts the invariants that must hold for every combination:

- a late return is fined exactly `days_late x daily_fine_rate` — never more, never less
- on-time returns are never fined
- fines are never negative and grow monotonically with lateness
- a new loan's due date is exactly `borrow_date + loan_period_days`
- each renewal adds exactly one loan period and increments the counter

`freezegun` pins the service clock to each generated instant, making the
tests deterministic and immune to midnight rollovers.

### Integration Testing

FastAPI `TestClient` exercises the real request path through the application and an isolated in-memory SQLite database.

Examples include:

- registration and login
- authentication failures
- CRUD operations
- borrowing and returning
- membership plan switching (self-service, staff override, downgrade rules)
- role-based access control
- database constraints

### Authentication Security Tests

`tests/integration/test_auth_security.py` attacks the JWT layer the way an
adversary would: expired tokens, tampered signatures, payload escalation
without re-signing, wrong-secret tokens, the classic `alg=none` bypass,
tokens without a subject, and valid tokens for deactivated users — all must
be rejected with 401.

### Concurrency Tests

`tests/integration/test_concurrency.py` reproduces the race where two
members borrow the last copy of a book at the same instant, using real
threads with separate sessions against a shared file-backed SQLite database:

- **Before the fix:** both requests succeeded — the physical copy was double-booked.
- **Fix:** a partial unique index (`uq_active_borrow_per_copy`) lets the
  database itself enforce "one active loan per copy"; the losing commit
  raises `IntegrityError`, which the service translates into the normal
  "no copies available" business rule.
- **After:** exactly one borrower wins, the loser gets a clean 400, and the
  test repeats the race five times to defeat scheduler luck.

### End-to-End Testing

Selenium tests exercise the application through the browser using the Page Object Model.

Critical workflows include:

- authentication
- search and navigation
- member borrowing (including self-service return)
- reservation of an unavailable book
- membership plan switching — the Current badge moves between plan cards
- admin book creation
- role-based navigation

### Test Data

Factory Boy and Faker provide reusable, realistic test data without coupling factories to the application database.

### Mocking

`unittest.mock` isolates unit-level business logic from repositories and infrastructure.

## 7. Testing Strategy

The test pyramid is intentionally weighted toward fast unit and integration tests, with a smaller E2E layer for critical user journeys.

```text
             /\
            /  \
           / E2E\          Small, critical workflows
          /------\
         /        \
        /Integration\       API + database behavior
       /------------\
      /              \
     /      Unit      \      Fast business-rule coverage
    /------------------\
```

See [`docs/testing-strategy.md`](docs/testing-strategy.md) for the detailed matrix and test techniques.

## 8. Installation

Use a supported Python 3.x environment and create a virtual environment:

```bash
python -m venv .venv
```

Activate it and install the pinned dependencies:

```bash
pip install -r requirements.txt
```

## 9. Running the Application

Start the FastAPI application with:

```bash
uvicorn app.main:app --reload
```

The exact frontend startup command depends on the frontend project. For browser tests, both the frontend and backend must be running and the configured test data must be available.

## 10. Running Tests

Run the complete backend test suite (coverage and the 85% gate apply
automatically via `pytest.ini`):

```bash
pytest -m "not e2e and not selenium"
```

Run unit tests only:

```bash
pytest tests/unit
```

Run integration tests only:

```bash
pytest tests/integration
```

Run E2E tests locally after starting the required servers and browser environment:

```bash
pytest tests/e2e -m e2e
```

The E2E suite uses a locally installed ChromeDriver and does not contain a
machine-specific driver path. This avoids Selenium Manager attempting an
internet download in restricted environments.

### ChromeDriver on Windows

The E2E fixture deliberately avoids Selenium Manager downloads because restricted
networks can return HTTP 403 from the Chrome for Testing storage endpoint. A
local ChromeDriver is therefore required. The fixture searches, in order, for:

1. `CHROMEDRIVER_PATH`
2. `tools\chromedriver.exe` in this project
3. `chromedriver.exe` on `PATH`
4. a previously downloaded driver in Selenium's local cache

Make sure the ChromeDriver major version matches your installed Chrome major
version. For example, Chrome 151 requires a ChromeDriver 151 build.

PowerShell example after downloading the matching driver:

```powershell
$env:CHROMEDRIVER_PATH = "C:\tools\chromedriver.exe"
pytest tests/e2e -m e2e
```

You can also put `chromedriver.exe` on your `PATH`, then simply run:

```powershell
pytest tests/e2e -m e2e
```

## 11. Reports and Coverage

Every run measures coverage (terminal + `coverage.json` + `htmlcov/`) and
fails below 85% — the same gate CI enforces. To also produce an HTML test
report:

```bash
pytest -m "not e2e and not selenium" --html=tests/reports/report.html --self-contained-html
```

The generated reports are intentionally not treated as source code and should be regenerated after changes.

## 12. Continuous Integration

GitHub Actions is configured in `.github/workflows/ci.yml` (at the
repository root, next to the frontend project).

**On every push and pull request** the backend job installs the pinned
dependencies and runs the unit + integration suite with the same 85%
coverage gate enforced locally by `pytest.ini`, then uploads the coverage
JSON, HTML coverage, and the pytest-html report as artifacts.

**Nightly (03:00 UTC) and on demand** (`workflow_dispatch`) the e2e job
seeds the database, boots the FastAPI backend and the Next.js frontend,
lets Selenium Manager resolve a matching ChromeDriver, runs the full
browser suite, and uploads the HTML report, failure screenshots, and both
server logs.

## 13. Limitations

This is a focused university-scale testing project, not a production QA platform. It does not attempt to provide:

- load/performance testing
- full accessibility certification
- penetration testing beyond the JWT attack surface
- production deployment infrastructure

Correctness-level concurrency (the double-booking race on the last copy)
*is* covered; what remains out of scope is throughput/load testing.

Those areas are outside the project's intended scope.

## 14. Submission Focus

The strongest part of the project is the testing framework itself. During evaluation, the important points to demonstrate are:

1. Why the tests are divided into unit, integration, and E2E levels.
2. How mocking isolates business logic.
3. How the integration database is isolated.
4. How Page Object Model improves Selenium maintainability.
5. How boundary, negative, and regression tests catch defects.
6. How generated reports and CI provide repeatable feedback.
