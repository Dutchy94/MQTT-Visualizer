PYTHON ?= python3
VENV ?= .venv
VENV_BIN := $(VENV)/bin

.PHONY: venv install setup run test-publish

venv:
	$(PYTHON) -m venv $(VENV)

install: venv
	$(VENV_BIN)/pip install -r requirements.txt

setup: install

run: setup
	$(VENV_BIN)/$(PYTHON) app.py

test-publish: setup
	$(VENV_BIN)/$(PYTHON) test_publisher.py
