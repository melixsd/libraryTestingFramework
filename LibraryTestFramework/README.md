# Automated Testing Framework for a Library Management Web Application

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
│   ├── test_reservation_service.py
│   └── test_factories.py
│
├── integration/
│   ├── conftest.py
│   └── test_api.py
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
```

## 5. Current Test Suite

The current source tree contains **78 test functions**:

| Level | Tests | Purpose |
|---|---:|---|
| Unit | 50 | Business logic, validation, edge cases, factories |
| Integration | 16 | HTTP API, authentication, authorization, database behavior |
| E2E | 12 | Critical browser/user workflows |
| **Total** | **78** | |

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

### Integration Testing

FastAPI `TestClient` exercises the real request path through the application and an isolated in-memory SQLite database.

Examples include:

- registration and login
- authentication failures
- CRUD operations
- borrowing and returning
- role-based access control
- database constraints

### End-to-End Testing

Selenium tests exercise the application through the browser using the Page Object Model.

Critical workflows include:

- authentication
- search and navigation
- member borrowing
- reservation of an unavailable book
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

Run the complete backend test suite:

```bash
pytest tests/unit tests/integration
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

Generate an HTML test report:

```bash
pytest tests/unit tests/integration --html=tests/reports/report.html --self-contained-html
```

Generate coverage:

```bash
pytest tests/unit tests/integration --cov=app --cov-report=term-missing --cov-report=html:tests/reports/coverage
```

The generated reports are intentionally not treated as source code and should be regenerated after changes.

## 12. Continuous Integration

GitHub Actions is configured in `.github/workflows/tests.yml`.

The CI workflow installs dependencies, runs unit and integration tests, generates coverage/report artifacts, and uploads the results.

Browser E2E tests are kept as a local execution step because they require the application servers and browser environment.

## 13. Limitations

This is a focused university-scale testing project, not a production QA platform. It does not attempt to provide:

- load/performance testing
- full accessibility certification
- concurrent/race-condition testing
- penetration testing
- production deployment infrastructure

Those areas are outside the project's intended scope.

## 14. Submission Focus

The strongest part of the project is the testing framework itself. During evaluation, the important points to demonstrate are:

1. Why the tests are divided into unit, integration, and E2E levels.
2. How mocking isolates business logic.
3. How the integration database is isolated.
4. How Page Object Model improves Selenium maintainability.
5. How boundary, negative, and regression tests catch defects.
6. How generated reports and CI provide repeatable feedback.
