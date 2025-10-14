# Latin A Curriculum System

A 36-week Latin A curriculum generation and management system built with FastAPI and Python 3.11. This platform provides structured week-by-week lesson planning, daily activity templates, virtue integration, faith phrases, and exportable lesson kits for classical Latin instruction.

## Features

- **LLM-Powered Generation**: Automatically generate complete curriculum content using OpenAI or Anthropic
- **Provider-Agnostic**: Support for multiple LLM providers (OpenAI, Anthropic)
- **Spiral Learning**: Built-in enforcement of spiral curriculum principles with vocabulary/grammar recycling
- **Schema Validation**: Full Pydantic v2 schema enforcement with validation reporting
- **RESTful API**: FastAPI endpoints for generation, validation, and export
- **CLI Tools**: Command-line utilities for batch generation and management
- **Atomic File Structure**: Per-field file storage for granular version control

## Quick Start

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd steel

# Install dependencies
make install

# Copy environment template and configure
cp .env.example .env
# Edit .env with your API keys
```

### Configuration

Configure your LLM provider in `.env`:

```bash
# Choose provider: "openai" or "anthropic"
PROVIDER=openai

# Add your API key
OPENAI_API_KEY=sk-...
# OR
ANTHROPIC_API_KEY=sk-ant-...

# Model configuration
MODEL_NAME=gpt-4o
GEN_TEMP=0.25
GEN_MAX_TOKENS=3000
```

### Generate Curriculum Content

**Generate a single week:**
```bash
make gen-week WEEK=11
# Or directly:
python -m src.cli.hydrate_week_from_llm 11
```

**Generate a single day:**
```bash
make gen-day WEEK=11 DAY=1
# Or directly:
python -m src.cli.hydrate_day_from_llm 11 1
```

**Generate all 36 weeks:**
```bash
make gen-all
# Or directly:
python -m src.cli.hydrate_all_from_llm
```

### Run the API Server

```bash
make run
# API available at http://localhost:8000
# Docs at http://localhost:8000/docs
```

### API Endpoints

**Generation Endpoints:**
- `POST /api/v1/gen/weeks/{week}/spec` - Generate week specification
- `POST /api/v1/gen/weeks/{week}/role-context` - Generate Sparky role context
- `POST /api/v1/gen/weeks/{week}/assets` - Generate week assets
- `POST /api/v1/gen/weeks/{week}/days/{day}/fields` - Generate day fields
- `POST /api/v1/gen/weeks/{week}/days/{day}/document` - Generate day document
- `POST /api/v1/gen/weeks/{week}/hydrate` - Generate complete week (all components)

**Example:**
```bash
curl -X POST http://localhost:8000/api/v1/gen/weeks/11/spec
curl -X POST http://localhost:8000/api/v1/gen/weeks/11/hydrate
```

## Architecture

### Directory Structure

```
curriculum/LatinA/
├── Week01/
│   ├── Week_Spec/          # 12 part files + compiled JSON
│   ├── Role_Context/       # 7 part files + compiled JSON
│   ├── activities/         # Day1-Day4 subdirectories
│   │   └── Day1/          # 6 Flint field files
│   └── assets/            # Text files (chants, glossary, etc.)
└── exports/               # Generated ZIP files
```

### LLM Generation Pipeline

1. **Week Spec**: Generate structured lesson plan from curriculum outline
2. **Role Context**: Generate Sparky's pedagogical personality and approach
3. **Assets**: Generate supplementary materials (chants, glossaries, quizzes)
4. **Day Fields**: Generate per-day metadata and teaching notes
5. **Day Documents**: Generate detailed lesson plans with spiral enforcement
6. **Validation**: Validate all content against Pydantic schemas

### Spiral Learning Enforcement

The system automatically enforces spiral curriculum principles:
- Vocabulary/grammar recycling from prior weeks
- First 2 lesson steps must recall prior knowledge
- ≥25% of assessment items test prior content
- Explicit `spiral_links` tracking dependencies
- `misconception_watchlist` for common errors

## Development

### Run Tests

```bash
make test
# Or:
pytest tests/ -v
```

### Project Structure

```
src/
├── app.py                  # FastAPI application
├── config.py              # Settings and LLM client factory
├── cli/                   # CLI tools
│   ├── hydrate_day_from_llm.py
│   ├── hydrate_week_from_llm.py
│   └── hydrate_all_from_llm.py
├── models/                # Pydantic schemas
│   ├── schemas_week.py
│   ├── schemas_day.py
│   ├── schemas_flint.py
│   └── schemas_role.py
├── services/              # Business logic
│   ├── llm_client.py     # LLM abstraction layer
│   ├── generator_week.py # Week generation
│   ├── generator_day.py  # Day generation
│   ├── validator.py      # Schema validation
│   ├── exporter.py       # ZIP export
│   └── prompts/          # Prompt library
│       ├── week_system.txt
│       ├── day_system.txt
│       └── kit_tasks.py
└── templates/             # File templates
```

## Contributing

This system maintains strict schema validation and spiral learning enforcement. When contributing:
- Ensure all generated content validates against Pydantic schemas
- Maintain spiral learning links and vocabulary recycling
- Write tests for new generators using `FakeLLMClient`
- Keep prompts focused on pedagogical quality
