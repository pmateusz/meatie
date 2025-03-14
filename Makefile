SHELL := /bin/bash

## help: print this help message
.PHONY: help
help:
	@echo 'Usage:'
	@sed -n 's/^##//p' ${MAKEFILE_LIST} | column -t -s ':' |  sed -e 's/^/ /'


## init: setup a virtual environment
.PHONY: init
init:
	uv venv
	. .venv/bin/activate

## install: install project with optional dependencies
.PHONY: install
install:
	uv sync --all-extras --group mypy --group test

## install: install pydantic v1
.PHONY: install/pydantic/v1
install/pydantic/v1:
	uv pip install pydantic===1.13.0

## install: install pydantic v2
.PHONY: install/pydantic/v2
install/pydantic/v2:
	uv pip install -r pyproject.toml install --with=pydantic

## clean: remove virtual environment
.PHONY: clean
clean:
	.venv/bin/deactivate
	rm -Rf .venv

## test: run tests
.PHONY: test
test:
	uv run pytest

.PHONY: test/cover
test/cover:
	uv run pytest --cov=src --cov-report=term-missing

## audit: run static analysis tools
.PHONY: audit
audit:
	pre-commit run --all && uv run mypy --install-types --non-interactive src/**

## docs/serve: run mkdocs server in development mode
.PHONY: docs/serve
docs/serve:
	uv run mkdocs serve
