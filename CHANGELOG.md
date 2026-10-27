# Changelog

All notable changes to this project are documented here.
The format follows [Keep a Changelog](https://keepachangelog.com/).

## [1.0.0] - 2026-10-26

### Added
- FastAPI service with `/countries`, `/countries/search`, `/countries/{code}`, `/regions`,
  `/stats` and `/health` endpoints.
- Data cleaning for missing fields, bad numbers, malformed codes and duplicates.
- Filtering, sorting and pagination.
- In-memory TTL cache with automatic fallback to bundled sample data.
- Test suite, CI workflow, Dockerfile and documentation.
