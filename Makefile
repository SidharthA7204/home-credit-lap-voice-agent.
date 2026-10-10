.PHONY: install run test lint report cli
install:
	pip install -r requirements-dev.txt
run:
	uvicorn app.main:app --reload --port 8000
test:
	pytest -q
lint:
	ruff check .
report:
	python scripts/run_scenarios.py
cli:
	python -m app.cli
