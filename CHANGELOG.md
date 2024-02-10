# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2024-02-10

### Added

- Support for httpx and requests libraries (synchronous API)
- Added additional configuration options to tune the retry strategy, i.e., wait with jitter, wait fixed, stop after
  attempt, retry on exception cause type, etc.

### Changed

- Revised exceptions thrown by the library to mirror exceptions thrown by supported HTTP client libraries
- Changed options passed to the endpoint decorator, they are now lowercase
- Moved all exported symbols to the `meatie` package
- Moved `aiohttp` client the `meatie_aiohttp` package

### Removed

- Retry action on server-side errors, decisions what a server is debatable and design decisions made in the aiohttp
  library are not present in the httpx and requests libraries
