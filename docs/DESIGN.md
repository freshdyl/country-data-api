# Design notes

This document explains the main decisions in the project and the trade-offs behind them.

## Layers

```
HTTP (main.py)  ->  query logic (service.py, stats.py)  ->  data (repository.py, cleaning.py)
```

- **`main.py`** only translates HTTP into function calls: it parses and validates query
  parameters, calls the logic, and shapes the response or error. No business rules live here.
- **`service.py` and `stats.py`** are *pure functions* over a `list[Country]`. They have no
  I/O, so they are fast to test and easy to reason about.
- **`cleaning.py`** is also pure. It is the only place that knows what messy upstream data
  looks like.
- **`repository.py`** is the only module that does I/O (network and file).

The payoff is that nearly all logic can be tested without a server or a network connection.

## Data cleaning rules

| Problem in raw data                    | Handling                                          |
| -------------------------------------- | ------------------------------------------------- |
| Missing name or ISO codes              | Record is rejected                                |
| Codes with wrong length                | Record is rejected                                |
| Duplicate `cca3` code                  | First record wins, later ones are dropped         |
| Population missing, non-numeric, negative | Becomes `0`                                    |
| Area missing, zero, negative           | Becomes `None`; density is then also `None`       |
| `capital` is a list                    | First non-empty entry is kept                     |
| Extra whitespace in strings            | Collapsed and trimmed                             |
| Languages / currencies are dicts       | Flattened to sorted lists of names / ISO codes    |

Rejected and duplicate counts are logged on every load so data problems are visible.

## Caching and fallback

The upstream dataset is about 250 records and changes rarely, so the repository keeps it in
memory for a configurable TTL (default one hour). This keeps responses fast and avoids
hammering a free public API.

If the upstream request fails (network error, HTTP error, invalid JSON shape), or if it
returns data that cleans down to nothing, the repository loads the bundled sample dataset
instead and `/health` reports `data_source: "sample"`. The API stays usable, and the
degraded state is visible rather than silent.

The cache is guarded by a lock so concurrent requests do not trigger duplicate fetches.

## Dependency injection

Routes get the repository via FastAPI's `Depends(get_repository)`. Tests replace it with
`app.dependency_overrides`, so no test ever makes a network call. The repository itself
accepts an injectable `fetcher` and `clock`, which makes the cache and fallback behaviour
testable without sleeping or patching.

## API design choices

- **Offset pagination** (`limit`/`offset`) is simple and fine for a dataset this size. For a
  large or fast-changing dataset, cursor pagination would be safer.
- **`limit` is capped at 100** to bound response size.
- **Missing values sort last** regardless of ascending or descending order, so countries
  without an area do not crowd out real results.
- **Route order matters**: `/countries/search` is declared before `/countries/{code}`,
  otherwise "search" would be read as a country code. A test guards this.
- **Case-insensitive filters** because callers should not need to know the upstream casing.
- **Search ranking**: exact name, then name prefix, then name substring, then capital, then
  official name. Simple, predictable, and enough for this scale.

## Known limitations and ideas for extension

- Search is substring-based; it has no fuzzy matching or accent folding (`Brasilia` will not
  match `Brasília`).
- The cache is per-process. Running several workers means several caches.
- Region names follow REST Countries (for example, "Americas" rather than separate North and
  South America).
- Possible additions: accent-insensitive search, an `/countries/compare` endpoint, response
  caching headers, rate limiting, and a persistent cache (SQLite or Redis).
