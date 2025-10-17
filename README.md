TEQUILA: AI-Powered Latin A Curriculum Generator (v1.3.0)

Not the quantum TEQUILA project.
This is an AI curriculum system for Latin A, not related to quantum computing.

⸻

Overview

TEQUILA (or Steel) is a provider-agnostic curriculum engine that auto-generates a full 35-week Latin A course (4 lessons per week, 7 fields per lesson). It enforces pedagogical rules (spiral review, ≥ 25% recall, virtue alignment, single tutor voice) and produces exportable teaching materials with provenance metadata.

**New in v1.3.0**: Universal metadata extraction fix ensures all 4 days stay focused on the week's grammar topic. Added format-agnostic helper function supporting v1.0, v1.1, and custom week spec structures. Successfully tested with Weeks 2-3 generation.

**New in v1.1**: Two-phase generation architecture with master curriculum outline integration. Weeks are now planned first (internal_documents/), then days are generated from those planning documents, ensuring consistent scope & sequence across all 35 weeks.

⸻

Architecture & Flow

flowchart TD
  CurriculumOutline[curriculum_outline.json] --> Phase1[Phase 1: Week Planning]
  Phase1 --> InternalDocs[internal_documents/]
  InternalDocs --> Phase2[Phase 2: Day Generation]
  Phase2 --> GeneratorDay
  GeneratorDay --> Validator
  Validator -- valid --> Exporter
  Validator -- invalid --> RetryLoop
  RetryLoop --> Validator
  Exporter --> ZIPArchive
  ZIPArchive --> exports/WeekXX.zip

**Two-Phase Generation (v1.1)**:

**Phase 1 - Week Planning**:
1. **curriculum_outline.json**: Master 35-week scope & sequence (2 bullets per week)
   - Session duration per week (30min → 12-15min → 20-25min)
   - Grammar focus, vocabulary domains, prerequisites
2. **GeneratorWeek**: Creates week planning documents in `internal_documents/`:
   - `week_spec.json` - Complete week specification from outline
   - `week_summary.md` - Human-readable overview
   - `role_context.json` - AI tutor persona
   - `generation_log.json` - Provenance tracking

**Phase 2 - Day Generation**:
3. **GeneratorDay**: Reads from internal_documents/ to generate 4 days (7 fields each)
4. **Validator**: Pydantic schema + pedagogical checks (≥ 25% prior content on Day 4)
5. **RetryLoop**: Up to 10 attempts if validation fails
6. **Exporter**: Packages each week into a zip with manifest + metadata

⸻

Directory Layout

TEQUILA/
├── curriculum/
│   └── LatinA/
│       ├── Week01/
│       │   ├── internal_documents/          # ← NEW in v1.1
│       │   │   ├── week_spec.json           # Week planning from outline
│       │   │   ├── week_summary.md          # Human-readable overview
│       │   │   ├── role_context.json        # AI tutor persona
│       │   │   └── generation_log.json      # Provenance tracking
│       │   ├── Day1_1.1/                    # ← NEW naming: Day{N}_{W}.{N}
│       │   │   ├── 01_class_name.txt
│       │   │   ├── 02_summary.md
│       │   │   ├── 03_grade_level.txt
│       │   │   ├── 04_role_context.json
│       │   │   ├── 05_guidelines_for_sparky.json
│       │   │   ├── 06_document_for_sparky/  # ← NEW: directory with 6 .txt files
│       │   │   │   ├── spiral_review_document.txt
│       │   │   │   ├── weekly_topics_document.txt
│       │   │   │   ├── virtue_and_faith_document.txt
│       │   │   │   ├── vocabulary_key_document.txt
│       │   │   │   ├── chant_chart_document.txt
│       │   │   │   └── teacher_voice_tips_document.txt
│       │   │   └── 07_sparkys_greeting.txt
│       │   ├── Day2_1.2/
│       │   ├── Day3_1.3/
│       │   ├── Day4_1.4/
│       │   └── assets/
│       └── … up to Week35/
├── curriculum_outline.json          # ← NEW: Master 35-week outline
├── exports/
│   ├── Week01.zip
│   ├── Week02.zip
│   └── … Week35.zip
├── logs/
│   ├── generation.log
│   └── validation_failures/
├── src/
│   ├── cli/
│   │   └── generate_all_weeks.py
│   ├── services/
│   │   ├── curriculum_outline.py    # ← NEW: Outline service
│   │   ├── generator_week.py        # Rewritten for two-phase
│   │   ├── generator_day.py         # Reads from internal_documents/
│   │   ├── validator.py
│   │   ├── exporter.py
│   │   ├── storage.py               # Updated with internal_documents support
│   │   └── llm_client.py  (OpenAI only)
│   └── models/
│       └── schemas_day_week.py
├── .github/
│   └── workflows/ci.yml
├── .env.example
├── README.md
├── CHANGELOG.md                     # ← NEW
├── ARCHITECTURE.md
└── LICENSE


⸻

Quickstart Guide

**1. Clone the repository**

```bash
git clone https://github.com/ejresearch/TEQUILA.git
cd TEQUILA
```

**2. Environment setup**

Copy `.env.example` to `.env` and fill in:

```bash
OPENAI_API_KEY=your_openai_key
MODEL_NAME=gpt-4o
```

**3. Install dependencies**

```bash
make install
# OR
pip install -e .
```

**4. Generate a single week** (recommended for testing)

```bash
# Generate Week 1 (no prerequisites)
make gen-week WEEK=1

# Generate Week 2 (requires Week 1)
make gen-week WEEK=2
```

**5. Generate multiple weeks**

```bash
# Generate Weeks 1-5
python -m src.cli.generate_all_weeks --from 1 --to 5

# Generate single week with flag
python -m src.cli.generate_all_weeks --week 11
```

**6. Inspect output**

```bash
# View week structure
tree curriculum/LatinA/Week01/

# Check internal planning documents
cat curriculum/LatinA/Week01/internal_documents/week_spec.json
cat curriculum/LatinA/Week01/internal_documents/week_summary.md

# View exported zip
unzip -l exports/Week01.zip
```

**What Gets Generated**:
- **Phase 1**: `internal_documents/` with week planning (week_spec.json, week_summary.md, role_context.json)
- **Phase 2**: 4 days with 7 fields each (28 files total per week)
- **Export**: `exports/WeekXX.zip` with manifest and SHA-256 hashes

⸻

Validation & Retry Behavior

- Each lesson must pass the Pydantic schemas in `src/models/schemas_day_week.py`
- **Prerequisite validation**: Week N cannot be generated without Weeks 1 through N-1 existing
- **Spiral review check**: Day 4 must include ≥25% content from prior weeks
- **Retry logic**: Up to 10 attempts per field if validation fails
- **User confirmation**: After 10 failures, system pauses for manual intervention
- **Version suffixes**: Successful regeneration appends `_v2`, `_v3` rather than overwriting

⸻

Export Format & Metadata

Each week's ZIP archive (`exports/WeekXX.zip`) includes:
- **internal_documents/**: Week planning documents (Phase 1 output)
- **Day folders**: 4 days with 7 fields each (Phase 2 output)
- **assets/**: ChantChart, Copywork, Glossary, QuizPacket, TeacherKey, VirtueEntry
- **manifest.json**: File paths and SHA-256 hashes for integrity verification
- **Provenance metadata**: Model used, timestamp, tokens consumed, git commit hash

Logs of failures, retries, and generation status are stored in `logs/`.

⸻

CI / Testing
	•	A GitHub Actions workflow (.github/workflows/ci.yml) runs on each push:
	•	Linting (e.g. ruff / black)
	•	Schema validation tests with a sample week (Week11)
	•	A small pytest suite ensures no regressions in schema definitions or directory structure.

⸻

Key Features (v1.3.0)

**Universal Metadata Extraction**:
- Format-agnostic `_extract_from_week_spec()` helper function
- Supports v1.0 (flat keys), v1.1 (nested generated_files array), and custom formats
- Ensures all 4 days stay focused on week's grammar topic
- Prevents topic drift that occurred when metadata extraction failed

**Two-Phase Architecture**:
- Phase 1 generates week planning documents from master curriculum outline
- Phase 2 generates 4 days using planning documents as single source of truth
- Reduces redundant LLM calls and ensures consistency

**Master Curriculum Outline**:
- 35-week scope & sequence with prerequisite chains
- Dynamic session duration (30min Week 1 → 12-15min Week 11 → 20-25min Week 16)
- Tracks what each week introduces for the first time
- Sequential validation prevents generating Week N without Weeks 1-N-1

**Enhanced Day Structure**:
- Field 06 as directory with 6 teacher support documents
- Day naming convention includes week context (`Day1_11.1`)
- Spiral review automatically populated from prerequisite weeks

**Quality Standards**:
- Gold standard reference weeks (1, 11-15) establish expected quality
- Proper Latin macrons (amō not amo)
- Minute-by-minute timing precision
- Deep virtue and faith integration

Future & Roadmap (post-v1.1)
- Add human editing overlays with diff / accept-reject UI
- Expand to multi-subject curricula (e.g. Greek A, Bible A)
- Add dashboards & usage analytics
- Ollama local LLM integration (gpt-oss:120b)
- Incorporate educational feedback loops (teacher edits → model fine-tuning)
- Automated quality validation against reference weeks

⸻

License & Attribution

This project is licensed under the MIT License.
© 2025 ejresearch
