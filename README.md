# Country Data API

[![CI](https://github.com/YOUR-USERNAME/country-data-api/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR-USERNAME/country-data-api/actions/workflows/ci.yml)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

A small REST API built with **FastAPI** that pulls public country data from the
[REST Countries](https://restcountries.com) API, cleans it, and exposes endpoints for
filtering, searching and summary statistics.

It is intentionally compact, but it covers the things real backend code needs:
input validation, error handling, caching with a graceful fallback, pure and
well-tested business logic, and automated CI.

## Features

- **Data cleaning**: handles missing fields, bad numbers, empty capitals, malformed
  codes and duplicate records (see [`app/cleaning.py`](app/cleaning.py)).
- **Filtering** by region, subregion, language, currency and population range.
- **Sorting and pagination** on name, population, area and population density.
- **Search** by country name, official name or capital, with best matches first.
- **Statistics**: totals, average/median population, rankings, region and language breakdowns.
- **Resilient**: results are cached in memory, and if the upstream API is unreachable the
  service falls back to a bundled sample dataset instead of failing.
- **Validated input**: bad query parameters return clear `422` responses.
- **Tested**: 40+ tests, none of which touch the network.

## Quick start

```bash
git clone https://github.com/YOUR-USERNAME/country-data-api.git
cd country-data-api

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt

uvicorn app.main:app --reload
```

Open **http://127.0.0.1:8000/docs** for interactive Swagger documentation.

### With Docker

```bash
docker build -t country-data-api .
docker run -p 8000:8000 country-data-api
```

## API reference

| Method | Path                 | Description                                         |
| ------ | -------------------- | --------------------------------------------------- |
| GET    | `/health`            | Liveness check; reports data source (`live`/`sample`) |
| GET    | `/countries`         | List countries with filters, sorting and pagination |
| GET    | `/countries/search`  | Search by name or capital                           |
| GET    | `/countries/{code}`  | One country by ISO alpha-2 or alpha-3 code          |
| GET    | `/regions`           | Distinct regions in the data                        |
| GET    | `/stats`             | Summary statistics, optionally for one region       |

### `GET /countries` query parameters

| Parameter        | Type    | Default | Notes                                              |
| ---------------- | ------- | ------- | -------------------------------------------------- |
| `region`         | string  | -       | Case-insensitive, e.g. `Europe`                    |
| `subregion`      | string  | -       | e.g. `Western Europe`                              |
| `language`       | string  | -       | Language name, e.g. `French`                       |
| `currency`       | string  | -       | ISO 4217 code, e.g. `EUR`                          |
| `min_population` | int     | -       | `>= 0`                                             |
| `max_population` | int     | -       | `>= 0`, must not be below `min_population`         |
| `sort_by`        | string  | `name`  | `name`, `population`, `area_km2`, `population_density` |
| `order`          | string  | `asc`   | `asc` or `desc`                                    |
| `limit`          | int     | `25`    | 1 to 100                                           |
| `offset`         | int     | `0`     | `>= 0`                                             |

### Examples

```bash
# The three most populous European countries
curl "http://127.0.0.1:8000/countries?region=Europe&sort_by=population&order=desc&limit=3"

# Countries that use the euro and have more than 10 million people
curl "http://127.0.0.1:8000/countries?currency=EUR&min_population=10000000"

# Search by capital
curl "http://127.0.0.1:8000/countries/search?q=accra"

# One country by code
curl "http://127.0.0.1:8000/countries/CAN"

# Statistics for Africa
curl "http://127.0.0.1:8000/stats?region=Africa"
```

Example response from `/countries/CAN`:

```json
{
  "name": "Canada",
  "official_name": "Canada",
  "code2": "CA",
  "code3": "CAN",
  "capital": "Ottawa",
  "region": "Americas",
  "subregion": "North America",
  "population": 38250000,
  "area_km2": 9984670.0,
  "population_density": 3.83,
  "languages": ["English", "French"],
  "currencies": ["CAD"]
}
```

### Errors

| Status | When                                                                    |
| ------ | ----------------------------------------------------------------------- |
| `404`  | Unknown country code, or `/stats` for a region with no countries        |
| `422`  | Invalid query parameter (out-of-range `limit`, unknown `sort_by`, `min_population > max_population`, too-short search `q`) |

## Configuration

Settings are read from environment variables (see [`.env.example`](.env.example)):

| Variable              | Default             | Description                                    |
| --------------------- | ------------------- | ---------------------------------------------- |
| `COUNTRIES_API_URL`   | REST Countries v3.1 | Upstream endpoint returning a JSON list        |
| `CACHE_TTL_SECONDS`   | `3600`              | How long fetched data is reused                |
| `REQUEST_TIMEOUT`     | `10`                | Upstream HTTP timeout, in seconds              |
| `USE_SAMPLE_DATA_ONLY`| `false`             | Skip the network and serve the bundled sample  |

## Project structure

```
country-data-api/
├── app/
│   ├── main.py          # FastAPI routes and dependency wiring
│   ├── service.py       # Filter / search / sort / paginate (pure functions)
│   ├── stats.py         # Summary statistics (pure functions)
│   ├── cleaning.py      # Raw record -> validated Country (pure functions)
│   ├── repository.py    # Fetch, cache, and fall back to sample data
│   ├── models.py        # Pydantic models
│   ├── config.py        # Environment-based settings
│   └── data/            # Bundled sample dataset (offline fallback)
├── tests/               # pytest suite (no network access needed)
├── docs/DESIGN.md       # Design decisions and trade-offs
├── .github/workflows/   # CI: lint + tests on Python 3.10-3.13
├── Dockerfile
└── pyproject.toml
```

## Development

```bash
pytest                              # run the tests
pytest --cov=app --cov-report=term-missing   # with coverage
ruff check .                        # lint
ruff format .                       # auto-format
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the workflow and [docs/DESIGN.md](docs/DESIGN.md)
for why the code is structured the way it is.

## Data source

Country data comes from [REST Countries](https://restcountries.com). The bundled
`app/data/sample_countries.json` is a small hand-made subset used for offline
development, tests and as a fallback. It is illustrative, not authoritative.

## License

[MIT](LICENSE)
