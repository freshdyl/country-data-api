"""Pydantic models used for both internal data and API responses."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Country(BaseModel):
    """A cleaned, normalized country record."""

    name: str
    official_name: str | None = None
    code2: str = Field(description="ISO 3166-1 alpha-2 code, e.g. 'CA'")
    code3: str = Field(description="ISO 3166-1 alpha-3 code, e.g. 'CAN'")
    capital: str | None = None
    region: str | None = None
    subregion: str | None = None
    population: int = 0
    area_km2: float | None = None
    population_density: float | None = Field(
        default=None, description="People per square kilometre (None if area is unknown)"
    )
    languages: list[str] = Field(default_factory=list)
    currencies: list[str] = Field(default_factory=list, description="ISO 4217 codes")


class CountryPage(BaseModel):
    """A paginated list of countries."""

    total: int = Field(description="Number of countries matching the filters")
    limit: int
    offset: int
    items: list[Country]


class RankedCountry(BaseModel):
    name: str
    code3: str
    value: float


class LanguageCount(BaseModel):
    language: str
    countries: int


class Stats(BaseModel):
    """Summary statistics over a (possibly region-filtered) set of countries."""

    region: str | None = None
    country_count: int
    total_population: int
    average_population: float | None = None
    median_population: float | None = None
    total_area_km2: float
    most_populous: list[RankedCountry]
    densest: list[RankedCountry]
    countries_by_region: dict[str, int]
    top_languages: list[LanguageCount]


class Health(BaseModel):
    status: str
    version: str
    data_source: str = Field(description="'live' if upstream data loaded, else 'sample'")
    country_count: int
