# Contributing

Thanks for your interest in improving Country Data API.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
```

## Workflow

1. Create a branch: `git checkout -b feature/short-description`
2. Make your change, and add or update tests for it.
3. Run the checks locally:
   ```bash
   ruff format .
   ruff check .
   pytest --cov=app
   ```
4. Commit with a clear message and open a pull request describing *what* changed and *why*.

CI runs the same lint and test steps on Python 3.10 to 3.13, and a pull request needs them to pass.

## Guidelines

- **Keep logic pure.** Filtering, sorting, cleaning and stats take data in and return data out.
  Put I/O in `repository.py` only.
- **Tests must not use the network.** Use the `client` and `countries` fixtures in
  `tests/conftest.py`, or inject a fake fetcher into `CountryRepository`.
- **Add type hints** to new functions and keep docstrings short and useful.
- **Validate input** at the edge (in `main.py`) and return clear `4xx` errors.
- **Update docs.** If you add or change an endpoint or setting, update the README tables.

## Reporting bugs

Open an issue with the request you made, the response you expected, and what you got instead.
Including the `/health` output helps, since it shows whether live or sample data was in use.
