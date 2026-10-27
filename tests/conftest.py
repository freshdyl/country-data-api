"""Shared fixtures. Tests never touch the network: they use the bundled sample data."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.cleaning import clean_countries
from app.config import Settings
from app.main import app, get_repository
from app.models import Country
from app.repository import CountryRepository, load_sample_countries


@pytest.fixture(scope="session")
def countries() -> list[Country]:
    cleaned, _ = clean_countries(load_sample_countries())
    return cleaned


@pytest.fixture()
def client() -> TestClient:
    repo = CountryRepository(Settings(use_sample_data_only=True))
    app.dependency_overrides[get_repository] = lambda: repo
    yield TestClient(app)
    app.dependency_overrides.clear()
