SHELL := /bin/bash

.PHONY: init
init:
	python -m venv .venv
	. .venv/bin/activate
	pip install --upgrade pip
	pip install pre-commit

.PHONY: install
install:
	poetry install --with=test --with=pydantic --all-extras

.PHONY: install/pydantic/v1
install/pydantic/v1:
	pip install pydantic[dotenv]===1.10.0

.PHONY: install/pydantic/v2
install/pydantic/v2:
	poetry install --with=pydantic

.PHONY: clean
clean:
	.venv/bin/deactivate
	rm -Rf .venv

.PHONY: test
test:
	poetry run pytest

.PHONY: test/cover
test/cover:
	poetry run coverage run -m pytest

.PHONY: audit
audit:
	pre-commit run --all && poetry run mypy --install-types --non-interactive src/**
