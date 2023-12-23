.PHONY: init install install-pydantic-v1 install-pydantic-v2 clean check
SHELL := /bin/bash

init:
	python -m venv .venv
	. .venv/bin/activate
	pip install --upgrade pip
	pip install poetry pre-commit

install:
	poetry install --with=dev

install-pydantic-v1:
	pip install pydantic[dotenv]===1.10.0

install-pydantic-v2:
	poetry install --with=pydantic

clean:
	.venv/bin/deactivate
	rm -Rf .venv

check:
	pre-commit run --all
