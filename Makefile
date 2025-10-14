.PHONY: install run test clean gen-week gen-day gen-all validate help

help:
	@echo "TEQUILA: AI Latin A Curriculum Generator (v1.0 Pilot)"
	@echo ""
	@echo "Available targets:"
	@echo "  install     - Install dependencies (OpenAI GPT-4o only)"
	@echo "  run         - Run FastAPI server"
	@echo "  test        - Run test suite"
	@echo "  clean       - Clean build artifacts and logs"
	@echo "  gen-all     - Generate all 35 weeks (EXPENSIVE!)"
	@echo "  gen-range   - Generate week range (FROM=1 TO=5)"
	@echo "  gen-week    - Generate single week (WEEK=11)"
	@echo "  validate    - Validate a week structure (WEEK=11)"

install:
	pip install -e .
	@echo "✓ TEQUILA v1.0 Pilot installed (OpenAI GPT-4o only)"

run:
	uvicorn src.app:app --reload --host 0.0.0.0 --port 8000

test:
	pytest tests/ -v

clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	rm -rf logs/*.log logs/invalid_responses/ 2>/dev/null || true
	@echo "✓ Cleaned build artifacts and logs"

gen-all:
	@echo "⚠️  WARNING: This will generate all 35 weeks and may cost \$\$\$"
	@echo "Press Ctrl+C to cancel, or wait 5 seconds to continue..."
	@sleep 5
	python -m src.cli.generate_all_weeks --from 1 --to 35

gen-range:
	@if [ -z "$(FROM)" ] || [ -z "$(TO)" ]; then \
		echo "Usage: make gen-range FROM=1 TO=5"; \
		exit 1; \
	fi
	python -m src.cli.generate_all_weeks --from $(FROM) --to $(TO)

gen-week:
	@if [ -z "$(WEEK)" ]; then \
		echo "Usage: make gen-week WEEK=11"; \
		exit 1; \
	fi
	python -m src.cli.generate_all_weeks --week $(WEEK)

validate:
	@if [ -z "$(WEEK)" ]; then \
		echo "Usage: make validate WEEK=11"; \
		exit 1; \
	fi
	python -m src.cli.validate_week_and_kit $(WEEK)
