# Contributing Guide

Thank you for contributing to the Multi-Domain Analytics Dashboard! This guide covers the development workflow, coding standards, and PR process.

## Getting Started

### Prerequisites

- Python 3.10 or 3.12
- Git
- Docker (optional, for containerized development)

### Development Setup

```bash
# Clone the repository
git clone https://github.com/mdespinoza/demo-repo-applicaiton.git
cd demo-repo-applicaiton

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # macOS/Linux
# venv\Scripts\activate   # Windows

# Install all dependencies (production + dev tools)
pip install -r requirements-dev.txt

# Set up pre-commit hooks
pre-commit install

# Copy environment template
cp .env.example .env
```

### Running the App Locally

```bash
# Development server with hot reload
python app/main.py
# Open http://localhost:8050

# Or with Docker Compose
docker-compose up
```

## Development Workflow

### Branch Naming

Create branches from `main` using this convention:

| Prefix | Use Case | Example |
|--------|----------|---------|
| `feature/` | New features | `feature/add-export-csv` |
| `fix/` | Bug fixes | `fix/ecg-label-cast` |
| `docs/` | Documentation | `docs/update-readme` |
| `refactor/` | Code refactoring | `refactor/data-loader` |
| `test/` | Test additions | `test/callback-coverage` |

### Making Changes

1. Create a feature branch:
   ```bash
   git checkout -b feature/your-feature main
   ```

2. Make your changes following the coding standards below.

3. Run tests locally:
   ```bash
   pytest
   ```

4. Commit your changes. Pre-commit hooks will automatically run formatting and linting checks.

5. Push and open a PR targeting `main`.

## Coding Standards

### Formatting

- **Formatter:** Black (v23.12.1)
- **Line length:** 120 characters
- **Target:** Python 3.10+

```bash
# Format code
black --line-length 120 app/ tests/

# Check without modifying
black --check --line-length 120 app/ tests/
```

### Linting

- **Linter:** Flake8 (v6.1.0)
- **Line length:** 120
- **Ignored rules:** E203 (whitespace before `:`, conflicts with Black)

```bash
flake8 app/ tests/ --max-line-length=120 --extend-ignore=E203
```

### Security Scanning

- **Scanner:** Bandit (v1.9.3)
- **Skipped rules:** B101 (`assert` allowed in tests)
- **Scope:** `app/` directory only

```bash
bandit -r app/ --skip=B101 -ll
```

### Configuration Files

| Tool | Config Location |
|------|----------------|
| Black | `pyproject.toml` `[tool.black]` |
| Bandit | `pyproject.toml` `[tool.bandit]` |
| Flake8 | `.pre-commit-config.yaml` (args) |
| Pytest | `pytest.ini` |

## Pre-Commit Hooks

Pre-commit hooks run automatically on every `git commit`. They enforce:

1. **Trailing whitespace removal**
2. **End-of-file newline fix**
3. **YAML/JSON validation**
4. **Large file check** (max 500KB)
5. **Black formatting**
6. **Flake8 linting**
7. **Bandit security scan** (app/ only)

If a hook fails, fix the issue and re-stage your changes:

```bash
# Fix issues (Black often auto-fixes)
git add -u
git commit
```

To run hooks manually on all files:

```bash
pre-commit run --all-files
```

## Testing

### Running Tests

```bash
# Full test suite with coverage
pytest

# Specific test file
pytest tests/test_data_loader.py

# Specific test function
pytest tests/test_callbacks.py::test_equipment_filters

# With verbose output
pytest -vv
```

### Coverage

Coverage is configured in `pytest.ini` and runs automatically:

- **Source:** `app/` directory
- **Excludes:** `app/assets/`, `app/tabs/tab_instructions.py`
- **Reports:** Terminal (with missing lines) + HTML (`htmlcov/index.html`)

```bash
# Generate HTML coverage report
pytest --cov=app --cov-report=html:htmlcov
open htmlcov/index.html
```

### Writing Tests

- Place tests in the `tests/` directory
- Follow the naming pattern `test_*.py` for files and `test_*` for functions
- Use fixtures from `tests/conftest.py` for mock DataFrames and cache isolation
- Available fixtures:
  - `mock_equipment_df` — sample military equipment DataFrame
  - `mock_bases_df` — sample military bases DataFrame
  - `mock_ecg_dict` — sample precomputed ECG data dictionary
  - `mock_healthcare_df` — sample healthcare transcription DataFrame
  - `clear_loader_cache` — isolates tests from the data loader cache

## CI/CD Pipeline

Every push to `main` and every PR triggers the GitHub Actions pipeline (`.github/workflows/ci.yml`):

### Test Job
- Runs on **Python 3.10 and 3.12** (matrix)
- Installs dependencies with pip caching
- Runs `pytest` with coverage
- Uploads coverage report as artifact (Python 3.12 only)

### Lint Job
- Runs on **Python 3.12**
- Black formatting check
- Flake8 linting
- Bandit security scan

Both jobs must pass before a PR can be merged.

## Pull Request Process

1. Ensure all CI checks pass (tests + lint).
2. Write a clear PR title and description summarizing the changes.
3. Reference any related GitHub issues (e.g., `Closes #25`).
4. Keep PRs focused — one feature or fix per PR when possible.
5. Request review if required by branch protection rules.

## Project Structure

```
app/
├── main.py              # Entry point, Dash app initialization
├── config.py            # Paths, colors, constants
├── settings.py          # Environment-based configuration
├── logging_config.py    # Structured logging (JSON/text)
├── error_tracking.py    # Sentry integration
├── health.py            # /health endpoint
├── metrics.py           # /metrics endpoint
├── assets/styles.css    # Custom dark theme
├── components/          # Reusable UI components
│   ├── kpi_card.py
│   └── chart_container.py
├── data/
│   └── loader.py        # Centralized data loading + caching
└── tabs/                # Dashboard tab modules
    ├── tab_instructions.py
    ├── tab_equipment.py
    ├── tab_ecg.py
    ├── tab_bases.py
    ├── tab_healthcare.py
    └── tab_combined.py
```

## Questions?

Open a GitHub issue for questions about the codebase or development workflow.
