"""FastAPI application: routes and dependency wiring."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query

from . import __version__
from .config import Settings
from .models import Country, CountryPage, Health, Stats
from .repository import CountryRepository
from .service import (
    SortField,
    SortOrder,
    filter_countries,
    find_by_code,
    paginate,
    search_countries,
    sort_countries,
)
from .stats import compute_stats

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

app = FastAPI(
    title="Country Data API",
    version=__version__,
    description=(
        "Pulls public country data from the REST Countries API, cleans it, and "
        "exposes filtering, search and summary-statistics endpoints."
    ),
)


@lru_cache
def get_repository() -> CountryRepository:
    """Process-wide repository. Overridden in tests via ``app.dependency_overrides``."""
    return CountryRepository(Settings.from_env())


Repo = Annotated[CountryRepository, Depends(get_repository)]


@app.get("/health", response_model=Health, tags=["meta"])
def health(repo: Repo) -> Health:
    """Liveness check that also reports which data source is in use."""
    countries = repo.get_all()
    return Health(
        status="ok",
        version=__version__,
        data_source=repo.source,
        country_count=len(countries),
    )


@app.get("/countries", response_model=CountryPage, tags=["countries"])
def list_countries(
    repo: Repo,
    region: Annotated[str | None, Query(description="e.g. Europe, Asia")] = None,
    subregion: Annotated[str | None, Query(description="e.g. Western Europe")] = None,
    language: Annotated[str | None, Query(description="Language name, e.g. French")] = None,
    currency: Annotated[str | None, Query(description="ISO 4217 code, e.g. EUR")] = None,
    min_population: Annotated[int | None, Query(ge=0)] = None,
    max_population: Annotated[int | None, Query(ge=0)] = None,
    sort_by: SortField = "name",
    order: SortOrder = "asc",
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> CountryPage:
    """List countries with optional filters, sorting and pagination."""
    if (
        min_population is not None
        and max_population is not None
        and min_population > max_population
    ):
        raise HTTPException(
            status_code=422, detail="min_population must not be greater than max_population"
        )

    matches = filter_countries(
        repo.get_all(),
        region=region,
        subregion=subregion,
        language=language,
        currency=currency,
        min_population=min_population,
        max_population=max_population,
    )
    ordered = sort_countries(matches, sort_by, order)
    return CountryPage(
        total=len(ordered),
        limit=limit,
        offset=offset,
        items=paginate(ordered, limit, offset),
    )


@app.get("/countries/search", response_model=list[Country], tags=["countries"])
def search(
    repo: Repo,
    q: Annotated[str, Query(min_length=2, max_length=100, description="Name or capital")],
    limit: Annotated[int, Query(ge=1, le=100)] = 10,
) -> list[Country]:
    """Search by country name, official name or capital. Best matches come first."""
    return search_countries(repo.get_all(), q)[:limit]


@app.get("/countries/{code}", response_model=Country, tags=["countries"])
def get_country(code: str, repo: Repo) -> Country:
    """Get one country by ISO alpha-2 (``CA``) or alpha-3 (``CAN``) code."""
    country = find_by_code(repo.get_all(), code)
    if country is None:
        raise HTTPException(status_code=404, detail=f"No country with code '{code}'")
    return country


@app.get("/regions", response_model=list[str], tags=["countries"])
def list_regions(repo: Repo) -> list[str]:
    """List the distinct regions present in the data."""
    return sorted({c.region for c in repo.get_all() if c.region})


@app.get("/stats", response_model=Stats, tags=["stats"])
def stats(
    repo: Repo,
    region: Annotated[str | None, Query(description="Restrict stats to one region")] = None,
) -> Stats:
    """Summary statistics: totals, averages, rankings, region and language breakdowns."""
    countries = filter_countries(repo.get_all(), region=region)
    if region and not countries:
        raise HTTPException(status_code=404, detail=f"No countries found in region '{region}'")
    return compute_stats(countries, region=region)
