# TEQUILA Architecture Documentation

## System Overview

TEQUILA is a curriculum generation platform that uses OpenAI GPT-4o to create structured, validated Latin lessons. The system enforces pedagogical rules (spiral learning, virtue integration) through code, not just prompts.

## Core Modules

### 1. `src/config.py` - Configuration Management

**Purpose**: Centralized settings for all system parameters.

**Key Settings**:
- `total_weeks = 35` - Latin A v1.0 Pilot scope
- `max_retries = 10` - Retry attempts before user confirmation
- `prior_content_min_percentage = 25.0` - Spiral learning enforcement
- `logs_path` - Directory for retry and validation logs

**Usage**:
```python
from src.config import settings, get_llm_client

client = get_llm_client()  # Returns configured OpenAI client
```

### 2. `src/services/llm_client.py` - OpenAI GPT-4o Client

**Purpose**: Abstraction layer for OpenAI API with retry logic.

**Features**:
- Automatic retries (3 attempts via tenacity)
- Token usage tracking
- Budget checking (optional enforcement)
- Dry-run mode for testing

**Key Functions**:
- `OpenAIClient.generate(prompt, system, json_schema)` - Generate with structured output
- `get_client(provider="openai")` - Factory function

### 3. `src/services/generator_day.py` - Day Generation with Retries

**Purpose**: Generate complete daily lessons with 10-retry validation logic.

**Key Functions**:
- `scaffold_day(week, day)` - Create 7-field file structure
- `generate_day_document(week, day, client)` - Generate with retries
- `hydrate_day_from_llm(week, day, client)` - Complete day generation

**Retry Logic**:
1. Generate content via LLM
2. Validate required fields
3. If invalid, log attempt and retry (up to 10 times)
4. After MAX_RETRIES, prompt user for confirmation
5. Save invalid responses to `logs/invalid_responses/`

**7-Field Structure**:
```
Day{X}/
├── 01_class_name.txt           # Student-facing title
├── 02_summary.md               # Lesson overview
├── 03_grade_level.txt          # Grade level (3-5)
├── 04_role_context.json        # Sparky personality config
├── 05_guidelines_for_sparky.md # Teaching guidelines
├── 06_document_for_sparky.json # Complete lesson plan
└── 07_sparkys_greeting.txt     # Opening greeting
```

### 4. `src/services/generator_week.py` - Week Orchestration

**Purpose**: Coordinate generation of all week components (spec, role context, assets, days).

**Key Functions**:
- `scaffold_week(week)` - Create week directory structure
- `generate_week_spec_from_outline(week, client)` - Generate 12-part week spec
- `generate_role_context(week, client)` - Generate Sparky personality context
- `generate_assets(week, client)` - Generate chant charts, glossaries, quiz packets

**Week Structure**:
```
WeekXX/
├── Week_Spec/              # 12 JSON/markdown parts
│   ├── 01_metadata.json
│   ├── 03_vocabulary.json
│   ├── 07_assessment.json
│   └── 99_compiled_week_spec.json
├── Role_Context/           # 7-part Sparky personality
├── activities/             # Day1-Day4 (7 fields each)
└── assets/                 # ChantChart, Glossary, QuizPacket
```

### 5. `src/services/validator.py` - Schema and Rule Validation

**Purpose**: Enforce pedagogical rules and validate structure.

**Key Functions**:
- `validate_day_fields(week, day)` - Check all 7 fields exist
- `validate_day_4_spiral_content(week)` - Enforce ≥25% prior content
- `validate_week(week)` - Complete week validation

**Validation Rules**:
1. **7-Field Requirement**: Days must have all 7 fields (6-field is legacy)
2. **25% Spiral Rule**: Assessment `prior_content_percentage ≥ 25.0`
3. **JSON Validity**: All `.json` files must parse correctly
4. **Non-Empty Files**: Warn on empty fields
5. **role_context Structure**: Check for `sparky_role`, `focus_mode`, `hints_enabled`

### 6. `src/services/exporter.py` - ZIP Export with Manifests

**Purpose**: Package weeks into distributable ZIP files with integrity verification.

**Key Functions**:
- `export_week_to_zip(week)` - Create ZIP with manifest.json
- `export_all_weeks(num_weeks=35)` - Batch export

**Manifest Structure**:
```json
{
  "week": 11,
  "export_date": "2025-10-14T16:00:00",
  "version": "1.0.0",
  "pilot": "Latin A v1.0 Pilot (35 weeks)",
  "files": [
    {
      "path": "Week11/activities/Day1/01_class_name.txt",
      "size_bytes": 42,
      "sha256": "a1b2c3d4..."
    }
  ],
  "file_count": 147,
  "total_size_bytes": 284932
}
```

### 7. `src/services/usage_tracker.py` - Cost Tracking

**Purpose**: Monitor OpenAI API token usage and cost estimates.

**Key Functions**:
- `get_tracker()` - Singleton tracker instance
- `tracker.get_summary()` - Return usage stats

**Tracking Data**:
- Total tokens (prompt + completion)
- Estimated cost in USD
- Per-request breakdowns

### 8. `src/services/prompts/` - Prompt Templates

**Purpose**: Structured prompts with examples and validation rubrics.

**Key Files**:
- `kit_tasks.py` - Prompt assembly functions
- `day_system.txt` - System prompts for day generation
- `week_system.txt` - System prompts for week generation
- `system/` - Project manifests and overviews

**Prompt Engineering Approach**:
- Self-check rubrics embedded in prompts
- Example skeletons for anchoring
- Role context references for behavioral alignment
- Repair logic for missing dependencies

### 9. `src/cli/generate_all_weeks.py` - Main CLI Entrypoint

**Purpose**: User-facing command-line tool for generation.

**Usage**:
```bash
python -m src.cli.generate_all_weeks --from 1 --to 35
python -m src.cli.generate_all_weeks --week 11
```

**Features**:
- Week range generation (`--from`, `--to`)
- Single week generation (`--week`)
- Progress display with retry status
- Cost estimation per week
- Automatic validation and export
- User prompts on failures

## Data Flow

```
┌─────────────────┐
│  User Command   │
│ (CLI or API)    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ generate_week() │
│   (orchestrate) │
└────────┬────────┘
         │
         ├──► scaffold_week()
         │
         ├──► generate_week_spec()
         │        │
         │        └──► OpenAI GPT-4o
         │
         ├──► generate_role_context()
         │
         ├──► generate_assets()
         │
         ├──► For each day (1-4):
         │        │
         │        ├──► generate_day_fields()
         │        │        │
         │        │        └──► Retry loop (max 10)
         │        │                 │
         │        │                 ├──► OpenAI GPT-4o
         │        │                 ├──► Validate fields
         │        │                 └──► Log if invalid
         │        │
         │        └──► generate_day_document()
         │                 │
         │                 └──► Retry loop (max 10)
         │
         ├──► validate_week()
         │        │
         │        ├──► Check 7 fields
         │        ├──► Check 25% spiral
         │        └──► Check JSON validity
         │
         └──► export_week_to_zip()
                  │
                  ├──► Calculate SHA256 hashes
                  ├──► Generate manifest.json
                  └──► Create Week{XX}.zip
```

## Error Handling Strategy

### Retry Levels

1. **Transient API Errors** (Level 1):
   - Handled by `tenacity` in `llm_client.py`
   - 3 attempts with exponential backoff

2. **Validation Failures** (Level 2):
   - Handled by retry loop in `generator_day.py`
   - 10 attempts with 2-second pause
   - Logs each attempt to `logs/Week{XX}_Day{Y}_retries.log`
   - Saves invalid responses to `logs/invalid_responses/`

3. **User Confirmation** (Level 3):
   - After MAX_RETRIES exhausted
   - Prompt user: Continue (y) or Abort (n)
   - If abort, raise `ValueError` with "aborted by user"

### Logging Strategy

**Retry Logs** (`logs/Week{XX}_Day{Y}_retries.log`):
```
[2025-10-14T16:30:45] Attempt 1/10: Missing required fields: ['objectives']
[2025-10-14T16:30:50] Attempt 2/10: Invalid JSON response: JSONDecodeError
```

**Invalid Responses** (`logs/invalid_responses/`):
```
Week11_Day1_document_v3_20251014_163050_INVALID.json
```

## Testing Strategy

### Unit Tests
- `tests/test_schemas.py` - Pydantic schema validation
- `tests/test_validator.py` - Validation logic
- `tests/test_llm_client.py` - LLM client behavior

### Integration Tests
- `tests/test_generation_pipeline.py` - End-to-end generation
- `tests/test_7field_migration.py` - Legacy migration

### Validation Tests
- `tests/test_prompts.py` - Prompt output validation
- Week11 structure validation (used in CI)

## Deployment Considerations

### OpenAI API Limits
- Rate limits: 10,000 RPM for GPT-4o (tier-based)
- Token limits: 30M TPM (tier 2)
- Cost: ~$0.10-0.20 per day (estimate)

### Scaling
- **Parallel Generation**: Days within a week can be parallelized
- **Batch Processing**: Weeks must be sequential (spiral dependencies)
- **Caching**: Week specs can be cached for regeneration

### Security
- **API Key**: Store in `.env`, never commit
- **Authentication**: Enable `API_AUTH_KEY` for production FastAPI
- **Budget Caps**: Set `BUDGET_USD` to prevent runaway costs

## Extension Points

### Adding New Subjects
1. Create new schemas in `src/models/schemas_{subject}.py`
2. Update prompts in `src/services/prompts/`
3. Modify `generator_week.py` for subject-specific rules

### Customizing Validation
1. Edit `src/services/validator.py`
2. Add new `ValidationResult` checks
3. Update `validate_week()` orchestration

### Alternative LLM Providers
Currently locked to OpenAI GPT-4o for consistency. To add providers:
1. Implement `LLMClient` interface in `llm_client.py`
2. Update `get_client()` factory
3. Test prompt compatibility thoroughly

---

**Last Updated**: 2025-10-14 (v1.0.0)
