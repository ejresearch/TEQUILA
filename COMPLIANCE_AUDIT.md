# TEQUILA Compliance Audit Report
**Generated:** 2025-10-15
**Status:** NON-COMPLIANT (22% coverage)
**Critical Issues:** 28 unused prompts, inline prompts, missing Day 4 assessment, no spiral enforcement

---

## Executive Summary

TEQUILA has a comprehensive 37-function prompt library but **only 8 functions (22%) are wired to the generation pipeline**. This violates the core directive: "Every file generated must map to a corresponding task_* function."

### Critical Gaps
- ❌ **78% of prompt library unused** (29/37 functions never called)
- ❌ **Inline prompts violate modularity** (`task_role_context`, `task_assets`)
- ❌ **No Day 4 assessment generation** (quiz_packet, teacher_key missing)
- ❌ **No spiral enforcement** before export
- ❌ **Incomplete export provenance** (no prompt hashes)
- ❌ **No CI for prompt coverage**

---

## Prompt Coverage Matrix

### ✅ WIRED (8 functions - 22%)

| Function | Call Site | Output Files | Status |
|----------|-----------|--------------|--------|
| `task_week_spec` | `generator_week.generate_week_spec_from_outline()` | `Week_Spec/*` (12 files) | ✅ ACTIVE |
| `task_role_context` | `generator_week.generate_role_context()` | `Role_Context/*` (7 files) | ⚠️ INLINE PROMPT |
| `task_assets` | `generator_week.generate_assets()` | `assets/*` (6 files) | ⚠️ INLINE PROMPT |
| `task_day_fields` | `generator_day.generate_day_fields()` | `01-03` (class_name, summary, grade_level) | ⚠️ INLINE PROMPT |
| `task_day_role_context` | `generator_day.generate_day_fields()` | `04_role_context.json` | ✅ ACTIVE + SCHEMA |
| `task_day_guidelines` | `generator_day.generate_day_fields()` | `05_guidelines_for_sparky.md` | ✅ LOADS FILE |
| `task_day_document` | `generator_day.generate_day_document()` | `06_document_for_sparky.json` | ✅ LOADS FILE |
| `task_day_greeting` | `generator_day.generate_day_fields()` | `07_sparkys_greeting.txt` | ✅ LOADS FILE |

### ❌ ORPHANED - High Priority (5 functions)

| Function | Intended Use | Output Files | Action Required |
|----------|--------------|--------------|-----------------|
| `task_quiz_packet` | Day 4 assessment | `assets/QuizPacket.txt` or `Day4/08_quiz.md` | **Wire to Day 4 generation** |
| `task_teacher_key` | Day 4 answer key | `assets/TeacherKey.txt` or `Day4/09_key.md` | **Wire to Day 4 generation** |
| `task_spiral_enforcement` | Pre-export validation | `logs/spiral_report.json` | **Add to validator before export** |
| `task_virtue_alignment` | Pre-export validation | `logs/virtue_report.json` | **Add to validator (optional)** |
| `task_export_zip_manifest` | Export metadata | `manifest.json` in ZIP | **Replace current manifest logic** |

### ❌ ORPHANED - Medium Priority (10 functions)

| Function | Intended Use | Call Site | Status |
|----------|--------------|-----------|--------|
| `task_class_name` | Field 01 generation | Should replace inline in `task_day_fields` | Unused - inline instead |
| `task_day_summary` | Field 02 generation | Should replace inline in `task_day_fields` | Unused - inline instead |
| `task_grade_level` | Field 03 generation | Should replace inline in `task_day_fields` | Unused - inline instead |
| `task_prior_knowledge_digest` | Week spec part | Should be in `generate_week_spec_from_outline` | Unused |
| `task_week_summary` | Week metadata | Should be in `generate_week_spec_from_outline` | Unused |
| `task_day_repair` | Validation repair | Should be in `validator.repair_day_field()` | Unused |
| `task_week_refresh` | Admin tool | CLI `cli/repair_week.py` | Not implemented |
| `task_alignment_check` | CI validation | `scripts/ci_alignment.py` | Not implemented |
| `task_legacy_migration` | Migration tool | `cli/migrate_legacy.py` | Exists but limited use |
| `task_chain_context_builder` | Prompt chaining | Meta utility | Experimental |

### ❌ ORPHANED - Low Priority (14 functions)

Support, meta, and validation functions that are utilities or experimental:
- `task_system_overview`, `task_project_manifest`, `task_schema_validation`, `task_week_validation`
- `task_role_context_day`, `task_guidelines`, `task_document_day`, `task_greeting` (aliases/legacy)
- `task_schema_selfcheck`, `task_pedagogical_selfcheck`, `task_llm_repair_cycle`
- `task_cost_explanation`, `task_error_explanation`, `task_api_docstring`

---

## Inline Prompt Violations

These functions return **hardcoded prompts** instead of loading from structured files:

### 🚨 Critical Violations

**1. `task_role_context()` (Lines 567-590)**
```python
# VIOLATION: Inline system prompt
sys = (
    "Generate Sparky Role Context JSON with these fields:\n"
    "- identity (Sparky's character and teaching philosophy)\n"
    ...
)
```
**Fix:** Create `prompts/week/role_context.json` and load via `_load_prompt_json()`

**2. `task_assets()` (Lines 603-628)**
```python
# VIOLATION: Inline system prompt
sys = (
    "Generate plain-text content for these weekly assets:\n"
    "1. ChantChart - formatted chant with Latin and English\n"
    ...
)
```
**Fix:** Create `prompts/week/assets.json` and load via `_load_prompt_json()`

**3. `task_day_fields()` (Lines 1848-1905)**
```python
# VIOLATION: Inline system prompt for fields 01-03
sys = (
    "Generate the THREE metadata fields for a single day lesson:\n"
    "1. class_name - short lesson title\n"
    ...
)
```
**Fix:** Use existing `task_class_name()`, `task_day_summary()`, `task_grade_level()` functions

---

## Missing Pipeline Components

### 1. Day 4 Assessment Generation ❌

**Current State:**
- `task_quiz_packet()` and `task_teacher_key()` exist but are NEVER called
- Day 4 generates same fields as Days 1-3
- `assets/QuizPacket.txt` and `assets/TeacherKey.txt` are empty placeholders

**Required Fix:**
```python
# In generator_day.py, add:
def generate_day4_assessment(week: int, client: LLMClient) -> Dict[str, Path]:
    """Generate Day 4 quiz packet and teacher key."""
    # Load week spec and Day 4 document
    # Call task_quiz_packet()
    # Call task_teacher_key()
    # Write to assets/ or Day4/ directory
    # Return paths
    pass

# In generate_all_weeks.py, modify day 4 generation:
if day == 4:
    assessment_paths = generate_day4_assessment(week_number, client)
```

### 2. Spiral Enforcement Validation ❌

**Current State:**
- `task_spiral_enforcement()` exists but is NEVER called
- Validator checks Day 4 guidelines for keywords but doesn't enforce 25% rule
- No pre-export spiral validation report

**Required Fix:**
```python
# In validator.py, add:
def enforce_spiral_before_export(week: int) -> ValidationResult:
    """Run spiral enforcement check before allowing export."""
    from .prompts.kit_tasks import task_spiral_enforcement

    # Load Day 4 document
    # Load prior knowledge digest
    # Call task_spiral_enforcement()
    # Parse response and validate ≥25% coverage
    # Return ValidationResult with ERRORS if fails
    pass

# In generate_all_weeks.py, before export:
spiral_result = enforce_spiral_before_export(week_number)
if not spiral_result.is_valid():
    print("⚠️ Spiral enforcement FAILED - cannot export")
    # Show errors and prompt user
```

### 3. Enhanced Export Manifest ❌

**Current State:**
- Manifest has SHA-256 hashes and basic metadata
- Missing: prompt hashes, model config, token counts, commit hash

**Required Fix:**
```python
# In exporter.py, use task_export_zip_manifest():
from .prompts.kit_tasks import task_export_zip_manifest

def export_week_to_zip(week: int) -> Path:
    # ... existing code ...

    # Get prompt hashes
    prompt_hashes = _compute_prompt_hashes(week)

    # Use task_export_zip_manifest to generate full manifest
    sys, usr, config = task_export_zip_manifest(
        week_number=week,
        file_hashes=file_hashes,
        prompt_hashes=prompt_hashes,
        model_config=get_model_config(),
        generation_metadata=get_generation_metadata(week)
    )

    # Write enhanced manifest.json
```

---

## Action Plan (Priority Order)

### Phase 1: Critical Fixes (Week 1)
1. ✅ **Wire Day 4 Assessment** - `task_quiz_packet`, `task_teacher_key`
2. ✅ **Add Spiral Enforcement** - Call `task_spiral_enforcement` before export
3. ✅ **Remove Inline Prompts** - Convert `task_role_context`, `task_assets`, `task_day_fields`

### Phase 2: Validation & Provenance (Week 2)
4. ✅ **Enhanced Export Manifest** - Use `task_export_zip_manifest`
5. ✅ **Virtue Alignment** - Optional pre-export check
6. ✅ **Repair Logic** - Wire `task_day_repair` to validator

### Phase 3: CI & Guardrails (Week 3)
7. ✅ **Prompt Coverage CI** - Script to enforce 100% coverage
8. ✅ **Admin Tools** - Implement `task_week_refresh`, `task_alignment_check`
9. ✅ **Documentation** - Update CHANGELOG.md and ARCHITECTURE.md

---

## Acceptance Criteria

### Minimal Done Definition
- ✅ All 8 active functions load from external files (no inline prompts)
- ✅ Day 4 generates quiz_packet + teacher_key
- ✅ Spiral enforcement runs before export and BLOCKS on failure
- ✅ Export manifest contains prompt hashes, model config, tokens, commit
- ✅ CI fails if any task_* function is unused
- ✅ Validators fail (not warn) on empty/placeholder content

### Verification Commands
```bash
# 1. Check prompt coverage
python scripts/check_prompt_coverage.py  # Should return 100%

# 2. Generate Week 1 with full pipeline
python -m src.cli.generate_all_weeks --week 1

# 3. Verify outputs
ls curriculum/LatinA/Week01/assets/QuizPacket.txt  # Non-empty
ls logs/Week01_spiral_report.json  # Exists with PASS status
unzip -l exports/Week01.zip | grep manifest.json  # Contains full provenance

# 4. Run validators
python -m src.cli.validate_export_week 1  # Should pass with 0 errors

# 5. CI checks
make test && make validate  # All green
```

---

## Current Coverage: 22% (8/37 functions)
**Target Coverage: 100% (37/37 functions wired or tagged @experimental)**

---

**Next Step:** Begin Phase 1, Task 1 - Wire Day 4 Assessment Generation
