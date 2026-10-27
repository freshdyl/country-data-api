"""Data access: fetch upstream data, clean it, cache it, fall back to a sample file."""

from __future__ import annotations

import json
import logging
import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx

from .cleaning import clean_countries
from .config import Settings
from .models import Country

logger = logging.getLogger(__name__)

SAMPLE_DATA_PATH = Path(__file__).parent / "data" / "sample_countries.json"

Fetcher = Callable[[str, float], list[Any]]


def fetch_raw_countries(url: str, timeout: float) -> list[Any]:
    """Download the raw JSON list from the upstream API."""
    response = httpx.get(url, timeout=timeout, follow_redirects=True)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, list):
        raise ValueError("Upstream response was not a JSON list")
    return data


def load_sample_countries() -> list[Any]:
    """Load the bundled sample dataset (used when the upstream API is unreachable)."""
    with SAMPLE_DATA_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


class CountryRepository:
    """Provides cleaned countries with a simple time-based in-memory cache.

    Args:
        settings: Application settings.
        fetcher: Callable ``(url, timeout) -> raw records``. Injectable for tests.
        clock: Monotonic clock. Injectable for tests.
    """

    def __init__(
        self,
        settings: Settings,
        fetcher: Fetcher = fetch_raw_countries,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self._settings = settings
        self._fetcher = fetcher
        self._clock = clock
        self._lock = threading.Lock()
        self._countries: list[Country] = []
        self._loaded_at: float | None = None
        self._source = "none"

    @property
    def source(self) -> str:
        """'live' if the last load came from upstream, 'sample' if it fell back."""
        return self._source

    def _is_fresh(self) -> bool:
        if self._loaded_at is None:
            return False
        return (self._clock() - self._loaded_at) < self._settings.cache_ttl_seconds

    def _load(self) -> None:
        raw: list[Any] | None = None
        source = "sample"

        if not self._settings.use_sample_data_only:
            try:
                raw = self._fetcher(self._settings.api_url, self._settings.request_timeout)
                source = "live"
            except (httpx.HTTPError, ValueError) as exc:
                logger.warning("Upstream fetch failed (%s); using sample data", exc)

        if raw is None:
            raw = load_sample_countries()

        countries, report = clean_countries(raw)
        logger.info(
            "Loaded %d countries from %s (rejected=%d, duplicates=%d)",
            report.kept,
            source,
            report.rejected,
            report.duplicates,
        )

        # If live data cleaned down to nothing, prefer the sample over an empty API.
        if not countries and source == "live":
            countries, _ = clean_countries(load_sample_countries())
            source = "sample"

        self._countries = countries
        self._source = source
        self._loaded_at = self._clock()

    def get_all(self) -> list[Country]:
        """Return all cleaned countries, refreshing the cache when it has expired."""
        with self._lock:
            if not self._is_fresh():
                self._load()
            return list(self._countries)
