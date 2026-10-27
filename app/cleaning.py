"""Turn raw upstream country records into clean, validated ``Country`` objects.

Upstream data is messy: fields go missing, populations arrive as strings or
negative numbers, capitals are lists, and duplicates occasionally appear.
Everything in this module is a pure function so it is trivial to unit test.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .models import Country


@dataclass(frozen=True)
class CleaningReport:
    """Summary of what happened while cleaning a batch of raw records."""

    kept: int
    rejected: int
    duplicates: int


def _clean_str(value: Any) -> str | None:
    """Return a stripped string, or None for empty / non-string input."""
    if not isinstance(value, str):
        return None
    value = " ".join(value.split())
    return value or None


def _clean_population(value: Any) -> int:
    """Coerce to a non-negative int; anything unusable becomes 0."""
    try:
        number = int(float(value))
    except (TypeError, ValueError):
        return 0
    return max(number, 0)


def _clean_area(value: Any) -> float | None:
    """Coerce to a positive float; zero, negative or invalid becomes None."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if number > 0 else None


def _first_capital(value: Any) -> str | None:
    """Capitals arrive as a list (some countries have several); keep the first."""
    if isinstance(value, list):
        for item in value:
            cleaned = _clean_str(item)
            if cleaned:
                return cleaned
        return None
    return _clean_str(value)


def _languages(value: Any) -> list[str]:
    """``{"eng": "English"}`` -> ``["English"]`` (sorted, de-duplicated)."""
    if not isinstance(value, dict):
        return []
    names = {_clean_str(v) for v in value.values()}
    return sorted(n for n in names if n)


def _currencies(value: Any) -> list[str]:
    """``{"CAD": {...}}`` -> ``["CAD"]`` (upper-cased, sorted)."""
    if not isinstance(value, dict):
        return []
    codes = {str(k).strip().upper() for k in value if str(k).strip()}
    return sorted(codes)


def clean_country(raw: Any) -> Country | None:
    """Clean one raw record. Returns None if it lacks a name or valid codes."""
    if not isinstance(raw, dict):
        return None

    name_block = raw.get("name")
    if isinstance(name_block, dict):
        name = _clean_str(name_block.get("common"))
        official = _clean_str(name_block.get("official"))
    else:
        name, official = _clean_str(name_block), None

    code2 = _clean_str(raw.get("cca2"))
    code3 = _clean_str(raw.get("cca3"))
    if not name or not code2 or not code3:
        return None
    code2, code3 = code2.upper(), code3.upper()
    if len(code2) != 2 or len(code3) != 3:
        return None

    population = _clean_population(raw.get("population"))
    area = _clean_area(raw.get("area"))
    density = round(population / area, 2) if area else None

    return Country(
        name=name,
        official_name=official,
        code2=code2,
        code3=code3,
        capital=_first_capital(raw.get("capital")),
        region=_clean_str(raw.get("region")),
        subregion=_clean_str(raw.get("subregion")),
        population=population,
        area_km2=area,
        population_density=density,
        languages=_languages(raw.get("languages")),
        currencies=_currencies(raw.get("currencies")),
    )


def clean_countries(raw_records: list[Any]) -> tuple[list[Country], CleaningReport]:
    """Clean a batch, dropping invalid records and duplicate codes.

    The result is sorted by country name so output order is deterministic.
    """
    seen: set[str] = set()
    cleaned: list[Country] = []
    rejected = duplicates = 0

    for raw in raw_records:
        country = clean_country(raw)
        if country is None:
            rejected += 1
            continue
        if country.code3 in seen:
            duplicates += 1
            continue
        seen.add(country.code3)
        cleaned.append(country)

    cleaned.sort(key=lambda c: c.name.casefold())
    return cleaned, CleaningReport(kept=len(cleaned), rejected=rejected, duplicates=duplicates)
