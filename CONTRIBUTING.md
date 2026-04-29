# Contributing to pyverity

Thank you for your interest in contributing!

## Development setup

```bash
git clone https://github.com/DelcioKelson/pyverity.git
cd pyverity
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Running tests

```bash
pytest tests/
```

With coverage:

```bash
pytest tests/ --cov=pyverity --cov-report=term-missing
```

## Linting and formatting

```bash
ruff check pyverity/
ruff format pyverity/
```

## Type checking

```bash
mypy pyverity/
```

## Pull request guidelines

- Keep changes focused — one feature or fix per PR.
- Add or update tests for any changed behaviour.
- All CI checks must pass before merging.
- Update `CHANGELOG.md` under `[Unreleased]` with a short description of the change.

## Reporting issues

Please open an issue on [GitHub](https://github.com/DelcioKelson/pyverity/issues) with:

- A minimal reproducible example
- The Python version and pyverity version (`python -c "import pyverity; print(pyverity.__version__)"`)
- The full traceback if applicable
