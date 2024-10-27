SHELL := /bin/bash

## help: print this help message
.PHONY: help
help:
	@echo 'Usage:'
	@sed -n 's/^##//p' ${MAKEFILE_LIST} | column -t -s ':' |  sed -e 's/^/ /'


## init: setup a virtual environment
.PHONY: init
init:
	python -m venv .venv
	. .venv/bin/activate
	pip install --upgrade pip
	pip install pre-commit

## install: install project with optional dependencies
.PHONY: install
install:
	poetry install --with=test --with=pydantic --with=requests --with=aiohttp --with=httpx

## install: install pydantic v1
.PHONY: install/pydantic/v1
install/pydantic/v1:
	pip install pydantic===1.10.0

## install: install pydantic v2
.PHONY: install/pydantic/v2
install/pydantic/v2:
	poetry install --with=pydantic

## clean: remove virtual environment
.PHONY: clean
clean:
	.venv/bin/deactivate
	rm -Rf .venv

## test: run tests
.PHONY: test
test:
	poetry run pytest

.PHONY: test/cover
test/cover:
	poetry run coverage run -m pytest

## audit: run static analysis tools
.PHONY: audit
audit:
	pre-commit run --all && poetry run mypy --install-types --non-interactive src/**
