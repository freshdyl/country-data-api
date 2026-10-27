import httpx
import pytest

from app.config import Settings
from app.repository import CountryRepository

GOOD_RECORD = {
    "name": {"common": "Livonia", "official": "Republic of Livonia"},
    "cca2": "LV",
    "cca3": "LVN",
    "population": 10,
    "area": 5,
}


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def test_uses_live_data_when_fetch_succeeds():
    repo = CountryRepository(Settings(), fetcher=lambda url, timeout: [GOOD_RECORD])
    assert [c.name for c in repo.get_all()] == ["Livonia"]
    assert repo.source == "live"


def test_falls_back_to_sample_on_http_error():
    def failing(url, timeout):
        raise httpx.ConnectError("no network")

    repo = CountryRepository(Settings(), fetcher=failing)
    assert len(repo.get_all()) > 5
    assert repo.source == "sample"


def test_falls_back_to_sample_when_live_data_is_all_invalid():
    repo = CountryRepository(Settings(), fetcher=lambda url, timeout: [{"junk": True}])
    assert len(repo.get_all()) > 5
    assert repo.source == "sample"


def test_sample_only_mode_never_calls_fetcher():
    def boom(url, timeout):
        pytest.fail("fetcher should not be called")

    repo = CountryRepository(Settings(use_sample_data_only=True), fetcher=boom)
    assert repo.get_all()
    assert repo.source == "sample"


def test_cache_is_reused_until_ttl_expires():
    calls = []
    clock = FakeClock()

    def fetcher(url, timeout):
        calls.append(1)
        return [GOOD_RECORD]

    repo = CountryRepository(Settings(cache_ttl_seconds=60), fetcher=fetcher, clock=clock)
    repo.get_all()
    clock.now = 30
    repo.get_all()
    assert len(calls) == 1  # still fresh

    clock.now = 61
    repo.get_all()
    assert len(calls) == 2  # expired -> refetched
