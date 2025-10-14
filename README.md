# TEQUILA: AI Latin A Curriculum Generator (v1.0 Pilot)

**NOT the quantum TEQUILA project** - This is an AI-powered educational content generator for Latin curriculum.

[![CI](https://github.com/ejresearch/TEQUILA/actions/workflows/ci.yml/badge.svg)](https://github.com/ejresearch/TEQUILA/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Overview

TEQUILA (Teaching Enhancement through Query-based Instructional Learning Automation) automatically generates a complete 35-week Latin A curriculum using **OpenAI GPT-4o**. Instead of months of manual lesson planning, generate validated, structured lessons in hours.

### Key Features

- **35 weeks × 4 days = 140 complete lessons**
- **7-field lesson architecture** with role context, guidelines, and Sparky AI tutor personality
- **10-retry validation** with automatic schema checking
- **25% spiral content enforcement** (Day 4 must review prior weeks)
- **SHA256-verified exports** with manifest.json for integrity
- **Cost tracking** and budget controls
- **Comprehensive logging** for retry attempts and validation failures

## Quick Start

### 1. Installation

```bash
# Clone repository
git clone https://github.com/ejresearch/TEQUILA.git
cd TEQUILA

# Install dependencies
make install

# Configure OpenAI API key
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=your_key_here
```

### 2. Generate Curriculum

```bash
# Generate a single week (Week 11 for testing)
make gen-week WEEK=11

# Generate a range of weeks
make gen-range FROM=1 TO=5

# Generate all 35 weeks (EXPENSIVE!)
make gen-all
```

### 3. Validate and Export

```bash
# Validate a week's structure
make validate WEEK=11

# Exports are automatically created in curriculum/exports/
ls curriculum/exports/Week11.zip
```

## Architecture Overview

```
Outline → Week Spec → Day Generation → Validation → ZIP Export
                ↓                ↓
          Role Context    7-Field Structure
                              ↓
                    01_class_name.txt
                    02_summary.md
                    03_grade_level.txt
                    04_role_context.json  ← NEW
                    05_guidelines_for_sparky.md
                    06_document_for_sparky.json
                    07_sparkys_greeting.txt
```

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed module documentation.

## Project Structure

```
TEQUILA/
├── src/
│   ├── cli/                  # Command-line tools
│   │   └── generate_all_weeks.py  # Main generation entrypoint
│   ├── models/               # Pydantic schemas (week, day, role)
│   ├── services/
│   │   ├── llm_client.py     # OpenAI GPT-4o client with retries
│   │   ├── generator_day.py  # Day generation with 10-retry logic
│   │   ├── generator_week.py # Week-level orchestration
│   │   ├── validator.py      # Schema & 25% spiral validation
│   │   ├── exporter.py       # ZIP export with SHA256 manifests
│   │   └── prompts/          # Prompt templates (111KB+)
│   └── app.py                # FastAPI REST API
├── curriculum/LatinA/        # Generated content (35 weeks)
├── logs/                     # Retry logs and invalid responses
└── tests/                    # pytest test suite
```

## Pedagogical Rules (Enforced)

1. **Spiral Learning**: ≥25% of quiz questions must review prior weeks (automated validation)
2. **7-Field Structure**: All days must include role_context.json for Sparky personality
3. **Virtue Integration**: Each week tagged with classical virtue (temperance, fortitude, etc.)
4. **4-Day Pattern**:
   - Day 1: Introduction and exploration
   - Day 2: Practice and reinforcement
   - Day 3: Application and extension
   - Day 4: Review and spiral (≥25% prior content)

## API Endpoints

Start the FastAPI server:

```bash
make run
# Visit http://localhost:8000/docs for interactive API documentation
```

**Public Endpoints** (no auth):
- `GET /api/v1/usage` - Cost tracking
- `GET /api/v1/weeks/{week}/spec/compiled` - Read week spec
- `POST /api/v1/weeks/{week}/validate` - Validate week

**Protected Endpoints** (require `X-API-Key` header):
- `POST /api/v1/gen/weeks/{week}/hydrate` - Generate complete week
- `POST /api/v1/gen/weeks/{week}/days/{day}/document` - Generate single day

## Cost Management

```bash
# Set budget cap in .env (optional, tracking only)
BUDGET_USD=100.00

# Check current spending
curl http://localhost:8000/api/v1/usage

# Use dry-run mode to test without API calls
DRY_RUN=true make gen-week WEEK=1
```

## Troubleshooting

### Generation Failures

Check `logs/Week{XX}_Day{Y}_retries.log` for retry attempts.

Invalid responses saved to `logs/invalid_responses/`.

### Validation Errors

Run explicit validation:
```bash
python -m src.cli.validate_week_and_kit 11
```

### Cost Exceeded

Budget tracking is **disabled by default** in v1.0 Pilot. Enable with `BUDGET_USD` in `.env`.

## Development

```bash
# Run tests
make test

# Lint code
black src/ tests/
ruff check src/ tests/

# Clean build artifacts
make clean
```

## License

MIT License - See [LICENSE](LICENSE) file.

**Note**: This project is NOT affiliated with the quantum computing framework "TEQUILA".

## Contributing

This is a v1.0 Pilot release. Contributions welcome via GitHub issues and pull requests.

## Citation

If you use TEQUILA in research or educational settings:

```bibtex
@software{tequila_latin_2025,
  title={TEQUILA: AI Latin A Curriculum Generator},
  author={TEQUILA Project Contributors},
  year={2025},
  version={1.0.0},
  url={https://github.com/ejresearch/TEQUILA}
}
```

---

**Generated with OpenAI GPT-4o** | **Human Review Required**
