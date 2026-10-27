from app.cleaning import clean_countries, clean_country


def raw(**overrides):
    record = {
        "name": {"common": "Testland", "official": "Republic of Testland"},
        "cca2": "tl",
        "cca3": "tst",
        "capital": ["Testville", "Second City"],
        "region": " Europe ",
        "subregion": "Western Europe",
        "population": 1000,
        "area": 500.0,
        "languages": {"eng": "English", "fra": "French"},
        "currencies": {"eur": {"name": "Euro"}},
    }
    record.update(overrides)
    return record


def test_clean_country_normalizes_fields():
    country = clean_country(raw())
    assert country is not None
    assert country.name == "Testland"
    assert (country.code2, country.code3) == ("TL", "TST")
    assert country.capital == "Testville"
    assert country.region == "Europe"
    assert country.languages == ["English", "French"]
    assert country.currencies == ["EUR"]
    assert country.population_density == 2.0


def test_missing_name_or_codes_are_rejected():
    assert clean_country(raw(name={})) is None
    assert clean_country(raw(cca2=None)) is None
    assert clean_country(raw(cca3="TOOLONG")) is None
    assert clean_country("not a dict") is None


def test_bad_population_becomes_zero():
    assert clean_country(raw(population="abc")).population == 0
    assert clean_country(raw(population=-5)).population == 0
    assert clean_country(raw(population="1234")).population == 1234


def test_bad_area_gives_no_density():
    for bad in (0, -1, None, "n/a"):
        country = clean_country(raw(area=bad))
        assert country.area_km2 is None
        assert country.population_density is None


def test_empty_capital_list_is_none():
    assert clean_country(raw(capital=[])).capital is None


def test_clean_countries_drops_invalid_and_duplicates_and_sorts():
    records = [
        raw(name={"common": "Zeta"}, cca2="ZZ", cca3="ZZZ"),
        raw(name={"common": "Alpha"}, cca2="AA", cca3="AAA"),
        raw(name={"common": "Alpha again"}, cca2="AB", cca3="AAA"),  # duplicate code3
        {"name": {}},  # invalid
    ]
    cleaned, report = clean_countries(records)
    assert [c.name for c in cleaned] == ["Alpha", "Zeta"]
    assert (report.kept, report.rejected, report.duplicates) == (2, 1, 1)
