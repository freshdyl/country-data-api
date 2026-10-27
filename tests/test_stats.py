from app.service import filter_countries
from app.stats import compute_stats


def test_stats_totals(countries):
    stats = compute_stats(countries)
    assert stats.country_count == len(countries)
    assert stats.total_population == sum(c.population for c in countries)
    assert stats.most_populous[0].name == "India"
    assert stats.densest[0].name == "Singapore"
    assert stats.countries_by_region["Europe"] == 4


def test_top_languages_counts(countries):
    stats = compute_stats(countries)
    assert stats.top_languages[0].language == "English"


def test_stats_for_empty_list():
    stats = compute_stats([])
    assert stats.country_count == 0
    assert stats.average_population is None
    assert stats.median_population is None
    assert stats.most_populous == []


def test_stats_region_is_echoed(countries):
    europe = filter_countries(countries, region="Europe")
    stats = compute_stats(europe, region="Europe")
    assert stats.region == "Europe"
    assert stats.country_count == 4
    assert set(stats.countries_by_region) == {"Europe"}


def test_median_of_even_count(countries):
    europe = filter_countries(countries, region="Europe")
    stats = compute_stats(europe)
    pops = sorted(c.population for c in europe)
    assert stats.median_population == (pops[1] + pops[2]) / 2
