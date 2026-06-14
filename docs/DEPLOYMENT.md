# Deployment

## Build

Build the package with either:

```bash
python -m build
```

or:

```bash
hatch build
```

Install for local development with:

```bash
pip install -e ".[dev]"
```

## Runtime Configuration

Copy `.env.example` to `.env` before running the application.

Environment variables are loaded from `.env` via `pydantic-settings` in `src/ai_career_platform/config.py`.

## Tests

Run the configured test runner with:

```bash
pytest
```

The configured runner includes coverage collection and requires at least 70% total coverage.
