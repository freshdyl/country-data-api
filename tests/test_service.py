from app.service import (
    filter_countries,
    find_by_code,
    paginate,
    search_countries,
    sort_countries,
)


def names(items):
    return [c.name for c in items]


def test_filter_by_region_is_case_insensitive(countries):
    result = filter_countries(countries, region="europe")
    assert set(names(result)) == {"France", "Germany", "Italy", "Switzerland"}


def test_filter_by_language_and_currency(countries):
    assert "Canada" in names(filter_countries(countries, language="french"))
    assert set(names(filter_countries(countries, currency="eur"))) == {"France", "Germany", "Italy"}


def test_filter_by_population_range(countries):
    result = filter_countries(countries, min_population=50_000_000, max_population=100_000_000)
    assert set(names(result)) == {"France", "Germany", "Italy"}


def test_filters_combine(countries):
    result = filter_countries(countries, region="Asia", language="English", min_population=10**9)
    assert names(result) == ["India"]


def test_no_filters_returns_everything(countries):
    assert len(filter_countries(countries)) == len(countries)


def test_search_ranks_exact_then_prefix_then_substring(countries):
    # "an" -> prefix none; substring in several names
    result = names(search_countries(countries, "ni"))
    assert result[0] == "Nigeria"  # prefix match outranks substring matches
    assert "United States" in result


def test_search_matches_capital(countries):
    assert names(search_countries(countries, "tokyo")) == ["Japan"]


def test_search_blank_returns_empty(countries):
    assert search_countries(countries, "   ") == []


def test_sort_by_population_desc(countries):
    top = sort_countries(countries, "population", "desc")[:2]
    assert names(top) == ["India", "United States"]


def test_sort_puts_missing_values_last(countries):
    from app.models import Country

    no_area = Country(name="Nowhere", code2="NW", code3="NWH", population=5)
    mixed = sort_countries([no_area, *countries], "area_km2", "asc")
    assert mixed[-1].name == "Nowhere"
    mixed_desc = sort_countries([no_area, *countries], "area_km2", "desc")
    assert mixed_desc[-1].name == "Nowhere"


def test_paginate(countries):
    page = paginate(countries, limit=3, offset=2)
    assert page == countries[2:5]
    assert paginate(countries, limit=5, offset=10_000) == []


def test_find_by_code(countries):
    assert find_by_code(countries, "ca").name == "Canada"
    assert find_by_code(countries, "CAN").name == "Canada"
    assert find_by_code(countries, "XX") is None
    assert find_by_code(countries, "TOOLONG") is None
