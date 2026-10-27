"""Summary statistics over a list of countries."""

from __future__ import annotations

import statistics
from collections import Counter

from .models import Country, LanguageCount, RankedCountry, Stats


def compute_stats(countries: list[Country], region: str | None = None, top_n: int = 5) -> Stats:
    """Compute aggregate statistics.

    Args:
        countries: Countries to summarise (already filtered by the caller).
        region: Echoed back in the response when the caller filtered by region.
        top_n: Length of the "top" lists.
    """
    populations = [c.population for c in countries]

    most_populous = sorted(countries, key=lambda c: (-c.population, c.name.casefold()))[:top_n]
    with_density = [c for c in countries if c.population_density is not None]
    densest = sorted(with_density, key=lambda c: (-c.population_density, c.name.casefold()))[:top_n]

    region_counts = Counter(c.region or "Unknown" for c in countries)
    language_counts = Counter(lang for c in countries for lang in c.languages)
    top_languages = sorted(language_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:top_n]

    return Stats(
        region=region,
        country_count=len(countries),
        total_population=sum(populations),
        average_population=round(statistics.fmean(populations), 2) if populations else None,
        median_population=float(statistics.median(populations)) if populations else None,
        total_area_km2=round(sum(c.area_km2 or 0 for c in countries), 2),
        most_populous=[
            RankedCountry(name=c.name, code3=c.code3, value=float(c.population))
            for c in most_populous
        ],
        densest=[
            RankedCountry(name=c.name, code3=c.code3, value=c.population_density) for c in densest
        ],
        countries_by_region=dict(sorted(region_counts.items())),
        top_languages=[LanguageCount(language=lang, countries=n) for lang, n in top_languages],
    )
