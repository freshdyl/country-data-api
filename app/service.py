"""Query logic: filtering, searching, sorting and pagination. All pure functions."""

from __future__ import annotations

from typing import Literal

from .models import Country

SortField = Literal["name", "population", "area_km2", "population_density"]
SortOrder = Literal["asc", "desc"]


def filter_countries(
    countries: list[Country],
    *,
    region: str | None = None,
    subregion: str | None = None,
    language: str | None = None,
    currency: str | None = None,
    min_population: int | None = None,
    max_population: int | None = None,
) -> list[Country]:
    """Apply optional filters. String filters are case-insensitive exact matches."""
    result = countries

    if region:
        r = region.casefold()
        result = [c for c in result if c.region and c.region.casefold() == r]
    if subregion:
        s = subregion.casefold()
        result = [c for c in result if c.subregion and c.subregion.casefold() == s]
    if language:
        lang = language.casefold()
        result = [c for c in result if any(lang == name.casefold() for name in c.languages)]
    if currency:
        code = currency.upper()
        result = [c for c in result if code in c.currencies]
    if min_population is not None:
        result = [c for c in result if c.population >= min_population]
    if max_population is not None:
        result = [c for c in result if c.population <= max_population]

    return list(result)


def search_countries(countries: list[Country], query: str) -> list[Country]:
    """Substring search across name, official name and capital, best matches first.

    Ranking (lower is better): exact name, name prefix, name substring,
    capital match, official-name match.
    """
    q = query.strip().casefold()
    if not q:
        return []

    scored: list[tuple[int, str, Country]] = []
    for country in countries:
        name = country.name.casefold()
        official = (country.official_name or "").casefold()
        capital = (country.capital or "").casefold()

        if name == q:
            rank = 0
        elif name.startswith(q):
            rank = 1
        elif q in name:
            rank = 2
        elif q in capital:
            rank = 3
        elif q in official:
            rank = 4
        else:
            continue
        scored.append((rank, name, country))

    scored.sort(key=lambda item: (item[0], item[1]))
    return [country for _, _, country in scored]


def sort_countries(
    countries: list[Country], sort_by: SortField = "name", order: SortOrder = "asc"
) -> list[Country]:
    """Sort by a field. Countries with a missing value (None) always sort last."""
    reverse = order == "desc"

    if sort_by == "name":
        return sorted(countries, key=lambda c: c.name.casefold(), reverse=reverse)

    with_value = [c for c in countries if getattr(c, sort_by) is not None]
    without_value = [c for c in countries if getattr(c, sort_by) is None]
    with_value.sort(key=lambda c: (getattr(c, sort_by), c.name.casefold()), reverse=reverse)
    return with_value + without_value


def paginate(items: list[Country], limit: int, offset: int) -> list[Country]:
    """Return ``items[offset:offset+limit]``."""
    return items[offset : offset + limit]


def find_by_code(countries: list[Country], code: str) -> Country | None:
    """Look up a country by ISO alpha-2 or alpha-3 code (case-insensitive)."""
    code = code.strip().upper()
    if len(code) == 2:
        return next((c for c in countries if c.code2 == code), None)
    if len(code) == 3:
        return next((c for c in countries if c.code3 == code), None)
    return None
