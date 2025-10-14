.PHONY: install run test clean gen-week gen-day gen-all help

help:
	@echo "Latin A Curriculum System - Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  install     - Install dependencies"
	@echo "  run         - Run FastAPI server"
	@echo "  test        - Run test suite"
	@echo "  clean       - Clean build artifacts"
	@echo "  gen-week    - Generate single week using LLM (WEEK=N)"
	@echo "  gen-day     - Generate single day using LLM (WEEK=N DAY=D)"
	@echo "  gen-all     - Generate all 36 weeks using LLM"

install:
	pip install -e .
	pip install tenacity httpx orjson openai anthropic

run:
	uvicorn src.app:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true

gen-week:
	@if [ -z "$(WEEK)" ]; then \
		echo "Usage: make gen-week WEEK=11"; \
		exit 1; \
	fi
	python -m src.cli.hydrate_week_from_llm $(WEEK)

gen-day:
	@if [ -z "$(WEEK)" ] || [ -z "$(DAY)" ]; then \
		echo "Usage: make gen-day WEEK=11 DAY=1"; \
		exit 1; \
	fi
	python -m src.cli.hydrate_day_from_llm $(WEEK) $(DAY)

gen-all:
	python -m src.cli.hydrate_all_from_llm
