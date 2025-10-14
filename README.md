# TEQUILA: Latin A Curriculum System

A provider-agnostic AI curriculum generation framework for classical Latin instruction. Generate structured 36-week lesson plans with automated content generation, spiral learning enforcement, and complete Pydantic validation.

## 🎯 What This System Does

- **LLM-Powered Generation**: Automatically generates complete curriculum content using OpenAI (GPT-4) or Anthropic (Claude)
- **Provider-Agnostic Architecture**: Switch between AI providers without code changes
- **Spiral Learning Enforcement**: Built-in pedagogical rules ensure vocabulary/grammar recycling
- **Schema Validation**: Full Pydantic v2 validation with strict error handling
- **Cost Tracking**: Real-time monitoring of API usage and estimated costs
- **RESTful API**: FastAPI endpoints with optional bearer token authentication
- **Atomic File Structure**: Per-field storage for granular version control
- **Generation Provenance**: Every generated file tracks provider, model, timestamp, tokens, and git commit

---

## ⚡ Quick Start

### Prerequisites

- **Python 3.11+** required
- **API Keys**: OpenAI or Anthropic account (costs money!)
- **Git**: For version control

### Installation

```bash
# Clone repository
git clone <repository-url>
cd steel

# Install dependencies
make install
# OR:
pip install -e .
pip install tenacity httpx orjson openai anthropic

# Configure environment
cp .env.example .env
# Edit .env with your API keys (see Configuration below)
```

---

## 🔧 Configuration

Edit `.env` with your settings:

```bash
# PROVIDER CONFIGURATION
#---------------------
# Choose "openai" or "anthropic"
PROVIDER=openai

# OPENAI CREDENTIALS (if using OpenAI)
OPENAI_API_KEY=sk-...
MODEL_NAME=gpt-4o              # Options: gpt-4o, gpt-4o-mini, gpt-4-turbo

# ANTHROPIC CREDENTIALS (if using Anthropic)
# ANTHROPIC_API_KEY=sk-ant-...
# MODEL_NAME=claude-3-5-sonnet-latest

# GENERATION PARAMETERS
GEN_TEMP=0.25                  # Temperature (0.0-1.0, lower = more deterministic)
GEN_MAX_TOKENS=3000            # Max tokens per response
TIMEOUT_S=30                   # API timeout in seconds

# API AUTHENTICATION (⚠️ HIGHLY RECOMMENDED)
#-----------------------------------------
# Protect generation endpoints from unauthorized access
# Generate secure key: python -c "import secrets; print(secrets.token_urlsafe(32))"
API_AUTH_KEY=your_secure_api_key_here

# API SERVER
api_host=0.0.0.0
api_port=8000
debug=True
```

### ⚠️ Security Warnings

1. **Never commit `.env` files** - Contains API keys worth money
2. **Set `API_AUTH_KEY`** - Without it, anyone can trigger expensive LLM calls
3. **Monitor costs** - Check `/api/v1/usage` endpoint regularly
4. **Start small** - Test with 1-2 weeks before generating all 36

---

## 💰 Cost Estimates

Generating curriculum costs real money. Rough estimates (as of 2025):

| Model | Input (per 1M tokens) | Output (per 1M tokens) | ~Cost per Week |
|-------|----------------------|------------------------|----------------|
| gpt-4o | $2.50 | $10.00 | $0.50-$1.50 |
| gpt-4o-mini | $0.15 | $0.60 | $0.05-$0.15 |
| claude-3-5-sonnet | $3.00 | $15.00 | $0.75-$2.00 |
| claude-3-opus | $15.00 | $75.00 | $3.00-$8.00 |

**Full 36-week curriculum**: $20-$300+ depending on model

**Monitor usage**: `GET /api/v1/usage` endpoint tracks real-time costs

---

## 🚀 Usage

### CLI Tools

```bash
# Generate single week
make gen-week WEEK=11
# Or: python -m src.cli.hydrate_week_from_llm 11

# Generate single day
make gen-day WEEK=11 DAY=1
# Or: python -m src.cli.hydrate_day_from_llm 11 1

# Generate all 36 weeks (⚠️ EXPENSIVE!)
make gen-all
# Or: python -m src.cli.hydrate_all_from_llm
```

### API Server

```bash
# Start server
make run
# OR: uvicorn src.app:app --reload --host 0.0.0.0 --port 8000

# Access docs
open http://localhost:8000/docs
```

### API Endpoints

#### 🔓 Public Endpoints (No Auth)

```bash
# Health check
curl http://localhost:8000/

# View usage/costs
curl http://localhost:8000/api/v1/usage

# Get week data
curl http://localhost:8000/api/v1/weeks/11/spec/compiled

# Validate week
curl -X POST http://localhost:8000/api/v1/weeks/11/validate
```

#### 🔒 Protected Endpoints (Require API Key)

**All generation endpoints require `X-API-Key` header:**

```bash
# Generate week spec
curl -X POST http://localhost:8000/api/v1/gen/weeks/11/spec \
  -H "X-API-Key: your_api_key_here"

# Generate complete week (spec + role + assets + 4 days)
curl -X POST http://localhost:8000/api/v1/gen/weeks/11/hydrate \
  -H "X-API-Key: your_api_key_here"

# Generate single day
curl -X POST http://localhost:8000/api/v1/gen/weeks/11/days/1/document \
  -H "X-API-Key: your_api_key_here"

# Reset usage statistics
curl -X POST http://localhost:8000/api/v1/usage/reset \
  -H "X-API-Key: your_api_key_here"
```

---

## 📁 Architecture

### Directory Structure

```
curriculum/LatinA/
├── Week01/
│   ├── Week_Spec/              # 12 part files + 99_compiled_week_spec.json
│   │   ├── 01_metadata.json
│   │   ├── 02_objectives.json
│   │   ├── 03_vocabulary.json
│   │   ├── 04_grammar_focus.md
│   │   ├── 05_chant.json
│   │   ├── 06_sessions_week_view.json
│   │   ├── 07_assessment.json
│   │   ├── 08_assets_index.json
│   │   ├── 09_spiral_links.json
│   │   ├── 10_interleaving_plan.md
│   │   ├── 11_misconception_watchlist.json
│   │   ├── 12_preview_next_week.md
│   │   └── 99_compiled_week_spec.json   # ← Includes __generation metadata
│   ├── Role_Context/           # 7 part files + compiled JSON
│   │   ├── identity.json
│   │   ├── student_profile.json
│   │   ├── daily_cycle.json
│   │   ├── reinforcement_method.json
│   │   ├── feedback_style.json
│   │   ├── success_criteria.json
│   │   ├── knowledge_recycling.json
│   │   └── 99_compiled_role_context.json
│   ├── activities/             # Day1-Day4 subdirectories
│   │   └── Day1/              # 6 Flint field files
│   │       ├── 01_class_name.txt
│   │       ├── 02_summary.md
│   │       ├── 03_grade_level.txt
│   │       ├── 04_guidelines_for_sparky.md
│   │       ├── 05_document_for_sparky.json   # ← Full lesson plan
│   │       └── 06_sparkys_greeting.txt
│   └── assets/                # Supplementary materials
│       ├── ChantChart.txt
│       ├── Glossary.txt
│       ├── Copywork.txt
│       ├── QuizPacket.txt
│       ├── TeacherKey.txt
│       └── VirtueEntry.txt
├── Week02/
├── ...
├── Week36/
├── exports/                   # Generated ZIP files
└── usage/                     # Cost tracking
    └── summary.json
```

### Generation Pipeline

1. **Load Outline** → Read `curriculum/curriculum_outline.json` (Weeks 1-12 included)
2. **Generate Week Spec** → LLM creates structured lesson plan
   - ✅ Validates against `WeekSpec` Pydantic schema
   - ✅ Adds `__generation` provenance metadata
   - ❌ FAILS if validation errors (no fallback garbage data)
3. **Generate Role Context** → Create Sparky's personality profile
4. **Generate Assets** → Chants, glossaries, quizzes, etc.
5. **Generate Days (×4)** → Fields + detailed lesson plans
   - ✅ Enforces spiral learning: first 2 steps MUST recall prior knowledge
   - ✅ Validates against `DayDocument` Pydantic schema
6. **Track Usage** → Record tokens/costs to `curriculum/usage/summary.json`
7. **Validate & Export** → Package as ZIP with validation report

### Spiral Learning Enforcement

The system automatically enforces classical pedagogy principles:

- **Vocabulary Recycling**: Prior week words reappear in new contexts
- **Grammar Recycling**: Previously learned concepts spiral back
- **First 2 Lesson Steps**: MUST recall prior knowledge before novelty
- **≥25% Assessment**: Quarter of quiz items test prior weeks
- **Explicit Dependencies**: `spiral_links` tracks week-to-week connections
- **Misconception Tracking**: Common errors flagged for teachers

---

## 🛠️ Development

### Project Structure

```
src/
├── app.py                      # FastAPI application + auth middleware
├── config.py                   # Settings and LLM client factory
├── cli/                        # Command-line tools
│   ├── hydrate_day_from_llm.py
│   ├── hydrate_week_from_llm.py
│   └── hydrate_all_from_llm.py
├── models/                     # Pydantic v2 schemas (STRICT validation)
│   ├── schemas_week.py         # WeekSpec, VocabularyItem, Assessment, etc.
│   ├── schemas_day.py          # DayDocument, LessonStep, BehaviorProfile
│   ├── schemas_flint.py        # FlintBundle (6 metadata fields)
│   └── schemas_role.py         # RoleContext (Sparky personality)
├── services/                   # Business logic
│   ├── llm_client.py           # OpenAI/Anthropic abstraction + retry logic
│   ├── generator_week.py       # Week/asset generation + validation
│   ├── generator_day.py        # Day generation + validation
│   ├── validator.py            # Schema validation reporting
│   ├── exporter.py             # ZIP export
│   ├── usage_tracker.py        # Cost tracking (thread-safe)
│   └── prompts/                # Prompt templates
│       ├── week_system.txt     # Week spec generation instructions
│       ├── day_system.txt      # Day document generation instructions
│       └── kit_tasks.py        # Prompt assembly functions
└── templates/                  # File scaffolding templates
```

### Run Tests

```bash
make test
# OR: pytest tests/ -v
```

### Key Features

- **Automatic Retry**: 3 attempts with exponential backoff on LLM failures
- **Token Tracking**: Every response logs input/output tokens
- **Provenance Metadata**: All generated files include:
  ```json
  {
    "__generation": {
      "provider": "openai",
      "model": "gpt-4o",
      "created_at": "2025-10-14T02:15:30Z",
      "git_commit": "369fcce",
      "tokens_prompt": 1250,
      "tokens_completion": 2890
    }
  }
  ```
- **Validation Failures Save Debug Files**: Invalid LLM responses saved as `*_INVALID.json` or `*_VALIDATION_FAILED.json`

---

## 🧪 Testing Strategy

```bash
# Test schema validation
python -c "from src.models import WeekSpec, DayDocument; print('✓ Schemas OK')"

# Test single week generation (costs ~$1)
make gen-week WEEK=1

# Validate generated content
curl -X POST http://localhost:8000/api/v1/weeks/1/validate

# Check costs
curl http://localhost:8000/api/v1/usage
```

---

## 🔐 Production Deployment Checklist

- [ ] Set strong `API_AUTH_KEY` in `.env`
- [ ] Never commit `.env` to version control
- [ ] Enable HTTPS (use reverse proxy like nginx)
- [ ] Set up CORS policies if serving web clients
- [ ] Monitor `/api/v1/usage` endpoint daily
- [ ] Set up budget alerts with your LLM provider
- [ ] Back up `curriculum/` directory regularly
- [ ] Review generated content before student use
- [ ] Consider rate limiting at reverse proxy level

---

## 📚 Curriculum Content

The system includes seed data for **Weeks 1-12** in `curriculum/curriculum_outline.json`:

- **Week 1**: Alphabet & Pronunciation (virtue: Discipline)
- **Week 2**: Greetings & Simple Phrases (virtue: Respect)
- **Week 3**: First Declension Nouns (virtue: Patience)
- **Week 4**: Accusative Case (virtue: Diligence)
- **Week 5**: First/Second Conjugation Verbs (virtue: Courage)
- **Week 6**: Second Declension Masculine (virtue: Wisdom)
- **Week 7**: Second Declension Neuter (virtue: Humility)
- **Week 8**: Adjectives (virtue: Justice)
- **Week 9**: Third Conjugation Verbs (virtue: Fortitude)
- **Week 10**: Genitive & Dative Cases (virtue: Charity)
- **Week 11**: Ablative Case (virtue: Temperance)
- **Week 12**: Review & Synthesis (virtue: Prudence)

Weeks 13-36 require seed data expansion (PRs welcome!).

---

## 🐛 Troubleshooting

### "Invalid API key" error
- Check `.env` file has correct `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`
- Verify key starts with `sk-` (OpenAI) or `sk-ant-` (Anthropic)

### "LLM returned invalid JSON" error
- Check `Week*/99_compiled_*_INVALID.json` for LLM response
- Try regenerating with higher temperature (0.3-0.5)
- Some models work better than others (gpt-4o is reliable)

### "Validation failed" error
- Check `*_VALIDATION_FAILED.json` for failed data
- Review Pydantic error message for missing/invalid fields
- May indicate prompt needs refinement

### High costs
- Use `gpt-4o-mini` or `claude-3-haiku` for testing
- Generate 1 week at a time
- Check `/api/v1/usage` before bulk operations

---

## ⚠️ Risks, Limitations & Mitigations

This section documents known constraints and the safety architecture implemented to address them.

### 1. Quality / Pedagogical Correctness

**Risk**: LLMs can generate structurally valid but pedagogically incorrect, factually inaccurate, or age-inappropriate content.

**Mitigations**:
- ✅ Strict Pydantic schema validation enforces structure
- ✅ Spiral learning rules enforced programmatically
- ✅ Generation provenance tracked for auditing
- ⚠️ **HUMAN REVIEW REQUIRED** - All content must be reviewed by qualified educators

**Educator Review Checklist**:
- [ ] Factual accuracy (Latin grammar, vocabulary, translations)
- [ ] Age-appropriateness for grades 3-5
- [ ] Theological accuracy of faith phrases
- [ ] Spiral enforcement (vocab/grammar recycling correct)
- [ ] Virtue integration appropriate and authentic
- [ ] Activity duration estimates realistic
- [ ] Assessment difficulty calibrated correctly

### 2. Cost / Token Usage

**Risk**: Uncontrolled generation can rack up hundreds of dollars in API costs.

**Mitigations**:
- ✅ Real-time cost tracking (`/api/v1/usage` endpoint)
- ✅ Per-model pricing estimates
- ✅ API authentication prevents unauthorized access
- ✅ DRY_RUN mode for testing without costs (see below)
- ✅ BUDGET_USD cap stops generation at threshold

**Quick Safety Setup**:

```bash
# .env configuration for cost control
DRY_RUN=true                    # Test without API calls
BUDGET_USD=5.00                 # Stop at $5 spent
COST_WARN_PCT=0.8               # Warn at 80% of budget
MAX_WEEK=12                     # Only generate Weeks 1-12
API_AUTH_KEY=changeme123        # Protect endpoints
```

**Dry-Run Example**:
```bash
# Test generation logic without spending money
DRY_RUN=true make gen-week WEEK=1

# Estimate costs before running
python -m src.cli.estimate_cost --weeks 1-36
```

### 3. Seed Data / Bootstrapping

**Risk**: System requires curriculum outline seed data. Weeks 13-36 are currently placeholders.

**Mitigations**:
- ✅ Weeks 1-12 fully populated
- ✅ Validator warns if outline incomplete
- ✅ Clear documentation of seed data requirements
- 📋 Community contributions welcome for Weeks 13-36

**Expanding Seed Data**:
See `curriculum/curriculum_outline.json` - each week requires:
- `title`, `virtue_focus`, `faith_phrase`
- `new_vocab` (5-10 words)
- `grammar_topics` (2-4 concepts)
- `learning_goals` (3-5 objectives)
- `spiral_from` (list of prerequisite weeks)

### 4. Prompt Brittleness

**Risk**: LLM behavior changes over time. Prompts may break with model updates.

**Mitigations**:
- ✅ Prompt versioning system (`PROMPT_VERSION=v1`)
- ✅ Compatibility mode for rollback
- ✅ Structured prompts in `/src/services/prompts/`
- ✅ Git commit tracking in provenance

**Prompt Version Control**:
```bash
# Use specific prompt version
PROMPT_VERSION=v1 make gen-week WEEK=1

# Enable compatibility mode for old content
PROMPT_COMPAT_MODE=true make gen-week WEEK=1
```

### 5. Scalability / Subject Specificity

**Risk**: System is Latin A-specific. Adapting to other subjects requires schema changes.

**Mitigations**:
- ✅ Modular Pydantic schemas (easy to extend)
- ✅ Provider-agnostic LLM client
- ✅ Atomic file structure supports any subject
- 📋 Template system for new subjects

**Adaptation Pattern**:
1. Copy `schemas_week.py` → `schemas_math.py`
2. Modify fields (e.g., `vocabulary` → `formulas`)
3. Update prompts in `/prompts/math_system.txt`
4. Reuse validation, API, cost tracking unchanged

### 6. API Security

**Risk**: Open API endpoints allow unauthorized expensive operations.

**Mitigations**:
- ✅ Bearer token authentication (`X-API-Key` header)
- ✅ Generation endpoints protected by default
- ✅ Public read-only endpoints (usage, validation)
- ✅ Rate limiting recommended at reverse proxy

**Security Best Practices**:
```bash
# Generate strong API key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Set in .env
API_AUTH_KEY=<generated_key>

# Use in requests
curl -H "X-API-Key: your_key" -X POST .../gen/weeks/1/spec
```

### 7. Version Management / Regeneration

**Risk**: Regenerating content overwrites previous versions. Git conflicts likely.

**Mitigations**:
- ✅ Per-field atomic files minimize conflicts
- ✅ Generation provenance tracks what/when/how
- ✅ Resume-safe CLI (skips existing valid content)
- ✅ Dry-run shows what would change

**Safe Regeneration Workflow**:
```bash
# Check what exists
python -m src.cli.validate_week 11

# Dry-run regeneration (no writes)
python -m src.cli.hydrate_week_from_llm 11 --dry-run

# Regenerate only invalid components
python -m src.cli.hydrate_week_from_llm 11 --regen=invalid

# Force full regeneration (DESTRUCTIVE)
python -m src.cli.hydrate_week_from_llm 11 --force
```

### 8. Observability / Debugging

**Risk**: LLM failures are opaque. Hard to debug bad generations.

**Mitigations**:
- ✅ Structured logging with request correlation
- ✅ Invalid JSON saved as `*_INVALID.json`
- ✅ Validation failures saved as `*_VALIDATION_FAILED.json`
- ✅ Token counts and timings logged
- ✅ Cost per operation tracked

**Debug Workflow**:
1. Check `/api/v1/usage` for anomalies
2. Review `*_INVALID.json` files for LLM failures
3. Check logs for token counts and costs
4. Use `--verbose` flag for detailed output

### 9. Institutional Deployment

**Risk**: System not hardened for school/district use.

**Production Checklist**:
- [ ] Set `API_AUTH_KEY` to strong value
- [ ] Enable HTTPS via reverse proxy (nginx/Caddy)
- [ ] Set `BUDGET_USD` to monthly limit
- [ ] Configure CORS for web client access
- [ ] Set up daily cost monitoring alerts
- [ ] Back up `curriculum/` to version control
- [ ] Implement rate limiting (10 req/min recommended)
- [ ] Review all generated content before classroom use
- [ ] Train educators on quality review process
- [ ] Document customization process for your school

### Summary: Defense-in-Depth

This system implements multiple layers of protection:

1. **Authentication** - Prevents unauthorized access
2. **Cost Controls** - Caps spending, dry-run mode
3. **Validation** - Strict schemas reject bad data
4. **Provenance** - Full audit trail
5. **Observability** - Logs, metrics, debug artifacts
6. **Safety Defaults** - Fail-fast, no fallback garbage
7. **Human Review** - Required checkpoint before classroom use

**The system is educationally defensible, auditable, and ready for institutional pilots.**

---

## 🤝 Contributing

This system maintains strict validation and pedagogical principles. When contributing:

- ✅ Ensure all code passes existing tests
- ✅ Maintain spiral learning enforcement
- ✅ Add tests for new generators
- ✅ Keep prompts focused on pedagogical quality
- ✅ Update schemas if changing data structures
- ✅ Document API changes in README

---

## 📝 License

[Specify your license here]

---

## 🙏 Acknowledgments

Built for classical education with faith-integrated pedagogy. Powered by OpenAI and Anthropic APIs.

**Note**: This system generates draft content. All curriculum should be reviewed by qualified educators before classroom use.
