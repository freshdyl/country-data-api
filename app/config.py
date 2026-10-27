"""Runtime configuration, read from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_API_URL = (
    "https://restcountries.com/v3.1/all"
    "?fields=name,cca2,cca3,capital,region,subregion,population,area,languages,currencies"
)


def _env_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.getenv(name, default))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    """Application settings.

    Attributes:
        api_url: Upstream endpoint returning a JSON list of country records.
        cache_ttl_seconds: How long fetched data is reused before refetching.
        request_timeout: Upstream HTTP timeout in seconds.
        use_sample_data_only: Skip the network and serve the bundled sample file.
    """

    api_url: str = DEFAULT_API_URL
    cache_ttl_seconds: float = 3600.0
    request_timeout: float = 10.0
    use_sample_data_only: bool = False

    @classmethod
    def from_env(cls) -> Settings:
        return cls(
            api_url=os.getenv("COUNTRIES_API_URL", DEFAULT_API_URL),
            cache_ttl_seconds=_env_float("CACHE_TTL_SECONDS", 3600.0),
            request_timeout=_env_float("REQUEST_TIMEOUT", 10.0),
            use_sample_data_only=_env_bool("USE_SAMPLE_DATA_ONLY", False),
        )
