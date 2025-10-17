# TEQUILA v1.3.0

**AI-Powered Latin A Curriculum Generator**

> *Not the quantum TEQUILA project. This is an educational AI system for classical Latin instruction.*

Generate a complete 35-week Latin A curriculum with AI-powered pedagogy, automatic spiral review, and integrated virtue formation. Built for classical educators who need high-quality, coherent lesson plans.

---

## What It Does

TEQUILA automatically generates:
- **35 weeks** of Latin A instruction (140 lessons total)
- **4 days per week** following a Discovery → Practice → Review → Quiz pattern
- **7 structured fields per day** including class materials, teacher support documents, and Sparky (AI tutor) content
- **Integrated virtue & faith** connections throughout
- **Automatic spiral review** ensuring ≥25% retention from prior weeks

Each week is pedagogically sound, follows classical Latin teaching methods, and maintains a consistent "tutor voice" through an AI persona named Sparky.

---

## Quick Start

### 1. Install
```bash
git clone https://github.com/ejresearch/TEQUILA.git
cd TEQUILA
make install
```

### 2. Configure
```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 3. Generate Your First Week
```bash
make gen WEEKS=1
```

### 4. View the Results
```bash
make view WEEK=1
```

That's it! Week 1 is now in `curriculum/LatinA/Week01/` with all 4 days, internal planning documents, and exportable ZIP.

---

## Commands

### Generate Curriculum

```bash
# Single week
make gen WEEKS=3

# Multiple specific weeks
make gen WEEKS=3,5,7

# Range of weeks
make gen WEEKS=3-10

# Mixed notation
make gen WEEKS=1-5,11-15
```

### View Generated Content

```bash
# View full week
make view WEEK=1

# View specific day
make view WEEK=7.2

# View internal planning docs
make view WEEK=7 SCOPE=internal

# View assets (quiz packets, etc.)
make view WEEK=8 SCOPE=assets

# View classroom content only
make view WEEK=19 SCOPE=class
```

### Other Commands

```bash
make help        # Show all available commands
make clean       # Clean build artifacts
make validate WEEK=11    # Validate week structure
```

See [GEN_COMMAND.md](GEN_COMMAND.md) and [VIEW_COMMAND.md](VIEW_COMMAND.md) for detailed documentation.

---

## How It Works

### Two-Phase Architecture

**Phase 1: Week Planning**
1. Reads master curriculum outline (`curriculum_outline.json`)
2. Generates comprehensive planning documents:
   - `week_spec.json` - Complete week specification
   - `week_summary.md` - Human-readable overview
   - `role_context.json` - AI tutor persona for the week
3. Saves to `internal_documents/` folder

**Phase 2: Day Generation**
1. Reads planning documents from Phase 1
2. Generates 4 days (Discovery, Practice, Review, Quiz)
3. Each day includes 7 structured fields:
   - Class name, summary, grade level
   - Role context, guidelines for Sparky
   - 6 teacher support documents (vocabulary, chants, spiral review, etc.)
   - Sparky's greeting
4. Validates content (Pydantic schemas + pedagogical rules)
5. Exports to ZIP with manifest and SHA-256 hashes

### Quality Assurance

- **Automatic validation**: Pydantic schemas ensure structural correctness
- **Spiral review enforcement**: Day 4 must include ≥25% prior content
- **Grammar focus consistency**: v1.3.0 fix ensures all 4 days stay on topic
- **Prerequisite checking**: Can't generate Week N without Weeks 1-N-1
- **Up to 10 retries**: With automatic correction attempts
- **Gold standard weeks**: Weeks 1, 11-15 serve as quality benchmarks

---

## Project Structure

```
TEQUILA/
├── curriculum/
│   └── LatinA/
│       ├── Week01/                    # Gold standard (tracked in git)
│       ├── Week02-10/                 # Generated locally (gitignored)
│       ├── Week11-15/                 # Gold standards (tracked in git)
│       └── Week16-35/                 # Generated locally (gitignored)
├── curriculum_outline.json            # Master 35-week scope & sequence
├── src/
│   ├── cli/
│   │   ├── gen.py                     # NEW: Flexible week generator
│   │   ├── view.py                    # NEW: Content viewer
│   │   ├── generate_all_weeks.py     # Core generator
│   │   ├── create_internal_documents.py
│   │   └── import_sample_weeks.py
│   ├── services/
│   │   ├── curriculum_outline.py      # Outline service
│   │   ├── generator_week.py          # Phase 1: Week planning
│   │   ├── generator_day.py           # Phase 2: Day generation
│   │   ├── prompts/
│   │   │   └── kit_tasks.py           # v1.3.0: Universal metadata extraction
│   │   ├── validator.py
│   │   ├── exporter.py
│   │   └── storage.py
│   └── models/
│       └── schemas_day_week.py        # Pydantic validation
├── bin/
│   ├── gen                            # Shell wrapper for gen command
│   └── view                           # Shell wrapper for view command
├── logs/                              # Generation logs (gitignored)
├── Makefile
├── README.md
├── GEN_COMMAND.md
├── VIEW_COMMAND.md
└── ARCHITECTURE.md
```

---

## Week Structure

Each generated week follows this structure:

```
Week01/
├── internal_documents/
│   ├── week_spec.json           # Complete week specification
│   ├── week_summary.md          # Human-readable overview
│   ├── role_context.json        # AI tutor persona
│   └── generation_log.json      # Provenance tracking
├── Day1_1.1/
│   ├── 01_class_name.txt
│   ├── 02_summary.md
│   ├── 03_grade_level.txt
│   ├── 04_role_context.json
│   ├── 05_guidelines_for_sparky.md
│   ├── 06_document_for_sparky/  # Directory with 6 teacher support files
│   │   ├── vocabulary_key_document.txt
│   │   ├── chant_chart_document.txt
│   │   ├── spiral_review_document.txt
│   │   ├── teacher_voice_tips_document.txt
│   │   ├── virtue_and_faith_document.txt
│   │   └── weekly_topics_document.txt
│   └── 07_sparkys_greeting.txt
├── Day2_1.2/
├── Day3_1.3/
├── Day4_1.4/
└── assets/
    ├── QuizPacket.txt
    └── TeacherKey.txt
```

---

## Key Features

### v1.3.0 (Latest)
- **Universal metadata extraction** with format-agnostic helper function
- Fixes topic drift bug where Days 2-4 went off-topic
- Supports v1.0, v1.1, and custom week spec structures
- `gen` command for flexible week generation
- `view` command for inspecting generated content

### v1.1
- Two-phase architecture (planning → generation)
- Master curriculum outline with 35-week scope & sequence
- Dynamic session duration (30min → 12-15min → 20-25min)
- Prerequisite validation

### Core Features
- **Pedagogically sound**: Follows classical Latin teaching methods
- **Spiral review**: Automatic integration of prior weeks (≥25%)
- **Virtue & faith**: Deep integration throughout curriculum
- **Consistent voice**: Single AI tutor persona (Sparky)
- **Quality benchmarks**: Gold standard weeks establish expected quality
- **Proper Latin**: Macrons, pronunciation, derivatives
- **Export-ready**: ZIP archives with manifests and SHA-256 hashes

---

## Costs & Performance

- **Cost per week**: ~$1-2 in OpenAI API calls
- **Time per week**: ~3-5 minutes for Phase 1 + Phase 2
- **Model**: OpenAI GPT-4o (only supported provider currently)
- **Total for 35 weeks**: ~$35-70 in API costs

---

## Gold Standard Weeks

The following weeks are tracked in git as quality benchmarks:
- **Week 1**: Introduction to Latin & Pronunciation
- **Week 11**: First Conjugation Verbs (-āre family)
- **Week 12**: First Conjugation Practice
- **Week 13**: First Conjugation Review
- **Week 14**: First Conjugation Assessment
- **Week 15**: First Conjugation Integration

All other weeks are generated locally and gitignored.

---

## Validation Rules

1. **Schema validation**: Pydantic models ensure correct structure
2. **Prerequisite check**: Week N requires Weeks 1 through N-1
3. **Spiral review**: Day 4 must include ≥25% prior content
4. **Grammar focus**: All 4 days must stay on the week's grammar topic (v1.3.0 fix)
5. **Field completeness**: All 7 fields must be present per day
6. **Retry logic**: Up to 10 attempts with automatic corrections

---

## Advanced Usage

### Generate Multiple Weeks in Sequence
```bash
# Generate Weeks 1-10 in order
make gen WEEKS=1-10

# This will take ~30-50 minutes and cost ~$10-20
```

### Inspect Internal Planning
```bash
# View the week spec before days are generated
make view WEEK=5 SCOPE=internal
```

### Export to ZIP
```bash
# ZIPs are automatically created in curriculum/LatinA/exports/
ls curriculum/LatinA/exports/
```

### Compare Weeks
```bash
# View two different weeks side-by-side
make view WEEK=1 > week1.txt
make view WEEK=2 > week2.txt
diff week1.txt week2.txt
```

---

## Development

### Run Tests
```bash
make test
```

### Clean Artifacts
```bash
make clean
```

### Validate Specific Week
```bash
make validate WEEK=11
```

### CI/CD
GitHub Actions runs automatically on push:
- Linting (ruff/black)
- Schema validation
- Test suite

---

## Roadmap

- [ ] Human editing UI with diff/accept-reject workflow
- [ ] Multi-subject support (Greek A, Bible A)
- [ ] Dashboard & analytics
- [ ] Anthropic Claude support (in addition to OpenAI)
- [ ] Ollama local LLM integration
- [ ] Teacher feedback loop → model fine-tuning
- [ ] Automated quality scoring against gold standards

---

## Contributing

This is a private research project. Contact ejresearch for collaboration inquiries.

---

## License

MIT License - See [LICENSE](LICENSE) for details.

© 2025 ejresearch

---

## Links

- **Documentation**: See [ARCHITECTURE.md](ARCHITECTURE.md) for technical details
- **Commands**: See [GEN_COMMAND.md](GEN_COMMAND.md) and [VIEW_COMMAND.md](VIEW_COMMAND.md)
- **Changelog**: See [CHANGELOG.md](CHANGELOG.md)
- **Issues**: https://github.com/ejresearch/TEQUILA/issues

---

**Built with Claude Code**
