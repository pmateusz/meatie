.PHONY: init install install-pydantic-v1 install-pydantic-v2 clean test-cover check
SHELL := /bin/bash

init:
	python -m venv .venv
	. .venv/bin/activate
	pip install --upgrade pip
	pip install pre-commit

install:
	poetry install --with=test --with=pydantic --all-extras

install-pydantic-v1:
	pip install pydantic[dotenv]===1.10.0

install-pydantic-v2:
	poetry install --with=pydantic

clean:
	.venv/bin/deactivate
	rm -Rf .venv

test-cover:
	poetry run coverage run -m pytest

check:
	pre-commit run --all && poetry run mypy --install-types --non-interactive src/**
