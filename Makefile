PYTHON ?= python3
VENV ?= .venv

.PHONY: venv install run test-publish

venv:
	$(PYTHON) -m venv $(VENV)

install:
	$(VENV)/bin/pip install -r requirements.txt

run:
	$(VENV)/bin/$(PYTHON) app.py

test-publish:
	$(VENV)/bin/$(PYTHON) test_publisher.py
