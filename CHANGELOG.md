# Changelog

All notable changes to TEQUILA: Latin A Curriculum Generator will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-10-16

### Added

#### Two-Phase Generation Architecture
- **Phase 1 (Week Planning)**: Generate week-level planning documents before day content
  - `internal_documents/week_spec.json` - Complete week specification from curriculum outline
  - `internal_documents/week_summary.md` - Human-readable week overview
  - `internal_documents/role_context.json` - AI tutor persona and teaching style
  - `internal_documents/generation_log.json` - Provenance tracking (timestamp, git commit, model)
- **Phase 2 (Day Generation)**: Generate 4 days reading from internal_documents/ as single source of truth

#### Master Curriculum Outline Integration
- `curriculum_outline.json` - 35-week master scope & sequence (70 bullets, 2 per week)
  - Session duration per week (30min → 12-15min → 20-25min progression)
  - Grammar focus and vocabulary domains
  - Prerequisite chains (Week 16 requires Weeks 1-15)
  - "Introduces" tracking (what concepts debut each week)
- `src/services/curriculum_outline.py` - Service module with functions:
  - `get_week_outline(week_num)` - Extract week constraints
  - `validate_week_prerequisites(week_num)` - Block generation if prereqs missing
  - `format_week_constraints_for_prompt(week_num)` - Inject constraints into LLM prompts
  - `get_session_duration(week_num)` - Dynamic duration by week

#### Enhanced Day Structure
- **Field 06 as Directory**: Changed from single JSON to `06_document_for_sparky/` containing 6 .txt files:
  - `spiral_review_document.txt` - Specific prior week content to review
  - `weekly_topics_document.txt` - Week overview for teacher
  - `virtue_and_faith_document.txt` - Theological integration guide
  - `vocabulary_key_document.txt` - Pronunciation and meaning reference
  - `chant_chart_document.txt` - Memory chant with motions
  - `teacher_voice_tips_document.txt` - Pedagogical coaching
- **Day Naming Convention**: `Day{N}_{W}.{N}` format (e.g., `Day1_11.1`, `Day4_16.4`)

#### Sample Week Import System
- `import_sample_weeks.py` - Imports perfect reference weeks from Desktop to curriculum structure
- `create_internal_documents.py` - Reverse-engineers internal_documents/ from existing weeks
- Successfully imported Weeks 1, 11, 12, 13, 14, 15 as gold standard references

#### Storage Layer Enhancements
- `storage.py` updated with internal_documents support:
  - `internal_documents_dir(week_number)` - Get internal_documents path
  - `internal_doc_path(week_number, doc_name)` - Get specific document path
  - `INTERNAL_DOCUMENTS` constant - List of 4 planning documents
  - `DOCUMENT_FOR_SPARKY_FILES` constant - List of 6 teacher support files
  - Updated `day_dir()` for new naming convention

### Changed

#### Generator Workflow
- `generator_week.py` - **Complete rewrite** for two-phase architecture:
  - `scaffold_week()` - Creates internal_documents/ + 4 day folders upfront
  - `generate_week_planning()` - Phase 1 orchestration
  - `generate_week_spec_from_outline()` - Uses curriculum_outline.json
  - `generate_week_summary()` - Reads from week_spec.json
  - `generate_week_role_context()` - Reads from week_spec.json
  - Removed Week_Spec and Role_Context legacy folders
- `generator_day.py` - Updated to read from internal_documents/:
  - `generate_day_fields()` - Reads week_spec.json from internal_documents/
  - `generate_day_document()` - Creates 6 .txt files in 06_document_for_sparky/
  - Fallback support for legacy Week_Spec format (backward compatibility)

#### CLI Scripts
- `generate_all_weeks.py` - Two-phase flow:
  - Calls `scaffold_week()` to create structure
  - Phase 1: Generate week planning documents
  - Phase 2: Generate 4 days using planning documents
  - Updated progress output to show phases
- `hydrate_week_from_llm.py` - Reads from internal_documents/
- `hydrate_all_from_llm.py` - Sequential validation with prerequisite checking

#### Curriculum Scope
- **Total weeks changed from 36 to 35** to match original specification
- Session duration now varies by week (stored in curriculum_outline.json)
- Week structure enforces sequential dependencies

### Documentation

- `SYSTEM_CHANGES.md` - Comprehensive architectural documentation
- `MIGRATION_PLAN.md` - Detailed migration guide from v1.0 to v1.1
- Updated inline documentation in all modified modules

### Technical Details

#### Prompt Chain Integration
- Week-level prompts inject curriculum outline constraints via `format_week_constraints_for_prompt()`
- Day-level prompts read from internal_documents/ (no direct outline access)
- Constraint injection happens once at week planning, then flows through internal_documents/
- Automatic spiral review population from prerequisite week specs

#### Backward Compatibility
- `generator_day.py` includes fallback to legacy `Week_Spec/99_compiled_week_spec.json`
- Existing v1.0 weeks can coexist with v1.1 weeks
- Import scripts handle both old and new formats

#### Quality Standards
- Gold standard weeks (1, 11-15) establish expected quality:
  - Macron usage (amō not amo)
  - Proper terminology (First Conjugation not "first verb type")
  - Minute-by-minute timing precision
  - Virtue integration depth
  - Spiral review specificity

### Performance

- Reduced redundant LLM calls by generating week planning once, reusing for 4 days
- Prerequisite validation prevents wasted generation attempts
- Provenance tracking enables debugging and audit trails

### Migration Notes

**From v1.0 to v1.1**:
1. Existing Week_Spec folders remain functional (backward compatibility)
2. New weeks use internal_documents/ architecture
3. Run `import_sample_weeks.py` to add reference weeks
4. Run `create_internal_documents.py` to retrofit existing weeks (optional)
5. Use curriculum_outline.json for all new week generation

**Breaking Changes**:
- CLI output format changed (shows Phase 1 and Phase 2 separately)
- Week directory structure includes internal_documents/ folder
- Day directories use new naming convention (Day{N}_{W}.{N})
- Field 06 is now a directory, not a single JSON file

## [1.0.0] - 2025-10-15

### Initial Release

- 35-week Latin A curriculum (140 lessons)
- 7-field day architecture with role_context
- OpenAI GPT-4o integration (exclusive)
- 10-retry validation with user confirmation
- Comprehensive logging and error handling
- ≥25% spiral content enforcement (Day 4)
- Schema validation (Pydantic)
- SHA256-verified exports with manifest.json
- CLI: generate_all_weeks.py with --from/--to/--week flags
- FastAPI REST API with authentication
- Cost tracking and budget controls
- Makefile targets for common operations
- GitHub Actions CI (lint + test + validate)
- Comprehensive README with quickstart
- ARCHITECTURE.md with module documentation
- MIT License

---

**Legend**:
- **Added**: New features
- **Changed**: Changes to existing functionality
- **Deprecated**: Soon-to-be removed features
- **Removed**: Removed features
- **Fixed**: Bug fixes
- **Security**: Security improvements
