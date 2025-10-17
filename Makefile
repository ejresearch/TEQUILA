.PHONY: install run test clean gen view gen-week gen-all validate help

help:
	@echo "TEQUILA: AI Latin A Curriculum Generator (v1.2.0)"
	@echo ""
	@echo "Available targets:"
	@echo "  install     - Install dependencies (OpenAI GPT-4o only)"
	@echo "  run         - Run FastAPI server"
	@echo "  test        - Run test suite"
	@echo "  clean       - Clean build artifacts and logs"
	@echo ""
	@echo "Generation commands:"
	@echo "  gen         - Flexible week generator"
	@echo "  view        - View generated curriculum content"
	@echo "  gen-week    - Generate single week (WEEK=11)"
	@echo "  gen-all     - Generate all 35 weeks (EXPENSIVE!)"
	@echo "  validate    - Validate a week structure (WEEK=11)"
	@echo ""
	@echo "Generation Examples:"
	@echo "  make gen WEEKS=3              # Generate Week 3"
	@echo "  make gen WEEKS=3,5,7          # Generate Weeks 3, 5, and 7"
	@echo "  make gen WEEKS=3-10           # Generate Weeks 3 through 10"
	@echo "  make gen WEEKS=1-5,11-15      # Generate Weeks 1-5 and 11-15"
	@echo ""
	@echo "View Examples:"
	@echo "  make view WEEK=1                     # View all Week 1 content"
	@echo "  make view WEEK=7.2                   # View Week 7 Day 2 only"
	@echo "  make view WEEK=7 SCOPE=internal      # View Week 7 internal docs"
	@echo "  make view WEEK=8 SCOPE=assets        # View Week 8 assets"
	@echo "  make view WEEK=19 SCOPE=class        # View Week 19 class material"
	@echo "  make view WEEK=22.2 SCOPE=class      # View Week 22 Day 2 class"

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

gen:
	@if [ -z "$(WEEKS)" ]; then \
		echo "Usage: make gen WEEKS=<spec>"; \
		echo ""; \
		echo "Examples:"; \
		echo "  make gen WEEKS=3              # Generate Week 3"; \
		echo "  make gen WEEKS=3,5,7          # Generate Weeks 3, 5, and 7"; \
		echo "  make gen WEEKS=3-10           # Generate Weeks 3 through 10"; \
		echo "  make gen WEEKS=1-5,11-15      # Generate Weeks 1-5 and 11-15"; \
		exit 1; \
	fi
	python -m src.cli.gen $(WEEKS)

view:
	@if [ -z "$(WEEK)" ]; then \
		echo "Usage: make view WEEK=<spec> [SCOPE=<scope>]"; \
		echo ""; \
		echo "Examples:"; \
		echo "  make view WEEK=1                    # View all Week 1 content"; \
		echo "  make view WEEK=7.2                  # View Week 7 Day 2 only"; \
		echo "  make view WEEK=7 SCOPE=internal     # View Week 7 internal docs"; \
		echo "  make view WEEK=8 SCOPE=assets       # View Week 8 assets"; \
		echo "  make view WEEK=19 SCOPE=class       # View Week 19 class material"; \
		echo "  make view WEEK=22.2 SCOPE=class     # View Week 22 Day 2 class material"; \
		exit 1; \
	fi
	python -m src.cli.view $(WEEK) $(SCOPE)

gen-all:
	@echo "⚠️  WARNING: This will generate all 35 weeks and may cost $$$"
	@echo "Press Ctrl+C to cancel, or wait 5 seconds to continue..."
	@sleep 5
	python -m src.cli.generate_all_weeks --from 1 --to 35

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
