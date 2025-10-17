"""Prompt assembly functions for LLM generation tasks.

PROMPT ENGINEERING ARCHITECTURE (7-field day structure):
- All prompts include self-check rubrics and positive instructions
- Prompts reference role_context (field 04) for behavioral alignment
- Example skeletons embedded for LLM anchoring
- Repair logic and fallbacks for missing dependencies
- Optimized for OpenAI GPT-4o
"""
from pathlib import Path
from typing import Dict, Optional, Tuple, Any, List
import json
import orjson


# ============================================================================
# WEEK SPEC DATA EXTRACTION HELPERS (v1.0 and v1.1 compatible)
# ============================================================================

def _extract_from_week_spec(week_spec: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract data from week_spec in a format-agnostic way.

    Supports both:
    - v1.0 format: flat structure with keys like "01_metadata.json"
    - v1.1 format: nested "week_spec_kit.generated_files" structure
    - Custom formats: root-level metadata/grammar_focus

    Returns:
        Dictionary with standardized keys: metadata, objectives, vocabulary,
        grammar_focus, chant, virtue_focus, faith_phrase, etc.
    """
    result = {
        "metadata": {},
        "objectives": [],
        "vocabulary": [],
        "grammar_focus": "",
        "chant": "",
        "virtue_focus": "",
        "faith_phrase": "",
        "week_number": 0,
        "week_title": "",
    }

    # v1.1 structure: week_spec_kit
    if "week_spec_kit" in week_spec:
        week_info = week_spec["week_spec_kit"].get("week_info", {})
        result["week_number"] = week_info.get("week_number", 0)
        result["week_title"] = week_info.get("title", "")
        result["grammar_focus"] = week_info.get("grammar_focus", "")
        result["chant"] = week_info.get("chant", "")
        result["virtue_focus"] = week_info.get("virtue_focus", "")
        result["faith_phrase"] = week_info.get("faith_phrase", "")

        # Extract from generated_files array
        generated_files = week_spec["week_spec_kit"].get("generated_files", [])
        for file_obj in generated_files:
            file_name = file_obj.get("file_name", "")
            content = file_obj.get("content", {})

            if file_name == "01_metadata.json":
                result["metadata"] = content
                if not result["week_number"]:
                    result["week_number"] = content.get("week_number", 0)
                if not result["week_title"]:
                    result["week_title"] = content.get("week_title", "")
                if not result["grammar_focus"]:
                    result["grammar_focus"] = content.get("grammar_focus", "")

            elif file_name == "02_objectives.json":
                result["objectives"] = content.get("objectives", [])

            elif file_name == "03_vocabulary.json":
                result["vocabulary"] = content.get("vocabulary", [])

    # v1.0 structure: flat keys
    elif "01_metadata.json" in week_spec:
        metadata = week_spec.get("01_metadata.json", {})
        result["metadata"] = metadata
        result["week_number"] = metadata.get("week_number", 0)
        result["week_title"] = metadata.get("week_title", "")
        result["grammar_focus"] = metadata.get("grammar_focus", "")
        result["chant"] = metadata.get("chant", "")
        result["virtue_focus"] = metadata.get("virtue_focus", "")
        result["faith_phrase"] = metadata.get("faith_phrase", "")
        result["objectives"] = week_spec.get("02_objectives.json", [])
        result["vocabulary"] = week_spec.get("03_vocabulary.json", [])

    # Custom format: root-level keys (Week 1 style)
    else:
        metadata = week_spec.get("metadata", {})
        result["metadata"] = metadata
        result["week_number"] = metadata.get("week", 0)
        result["week_title"] = metadata.get("title", "")
        result["grammar_focus"] = week_spec.get("grammar_focus", "")
        result["chant"] = week_spec.get("chant", "")

        faith_integration = week_spec.get("faith_integration", {})
        result["virtue_focus"] = faith_integration.get("virtue", week_spec.get("virtue_focus", ""))
        result["faith_phrase"] = faith_integration.get("faith_phrase", week_spec.get("faith_phrase", ""))

        vocabulary_data = week_spec.get("vocabulary", {})
        if isinstance(vocabulary_data, dict):
            result["vocabulary"] = vocabulary_data.get("core_items", [])
        elif isinstance(vocabulary_data, list):
            result["vocabulary"] = vocabulary_data

        objectives = week_spec.get("objectives", {})
        if isinstance(objectives, dict):
            result["objectives"] = objectives.get("skill_goals", [])
        elif isinstance(objectives, list):
            result["objectives"] = objectives

    return result


def _load_system_prompt(filename: str) -> str:
    """Load a system prompt from the prompts directory."""
    path = Path(__file__).parent / filename
    return path.read_text(encoding="utf-8")


def _load_prompt_json(filename: str) -> Dict[str, Any]:
    """Load a JSON prompt specification from the prompts directory."""
    path = Path(__file__).parent / filename
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


# ============================================================================
# SYSTEM OVERVIEW PROMPT - Establishes TEQUILA/Steel architecture
# ============================================================================

def task_system_overview() -> Tuple[str, str, Dict[str, Any]]:
    """
    Generate TEQUILA system overview manifesto.

    This prompt bootstraps Steel's understanding of the Latin A curriculum
    generation system. It establishes:
    - Course scope (35 weeks × 4 days)
    - 7-field day architecture
    - Pedagogical pillars (spiral, virtue, faith, chant)
    - Open-source policy and originality requirements
    - Budget, provenance, and validation policies

    Returns:
        (system_prompt, user_prompt, config_dict)

    Output:
        Markdown document (~1000 words) saved to docs/SYSTEM_OVERVIEW.md
    """
    prompt_spec = _load_prompt_json("system/system_overview.json")

    # Interpolate template variables
    outline = "\n".join(prompt_spec["inputs"]["latin_a_outline"])

    pillars = "\n".join(f"- {p}" for p in
        prompt_spec["inputs"]["pedagogical_pillars"]
    )

    seven_fields = ", ".join(prompt_spec["inputs"]["seven_field_names"])

    # Build user prompt from template
    user_content = "\n".join(prompt_spec["messages"][1]["content_template"])
    user_content = user_content.replace("{{latin_a_outline}}", outline)
    user_content = user_content.replace("{{pedagogical_pillars}}", pillars)
    user_content = user_content.replace("{{seven_field_names}}", seven_fields)

    system_content = prompt_spec["messages"][0]["content_template"]

    config = {
        "temperature": prompt_spec["model_preferences"]["temperature"],
        "max_tokens": prompt_spec["model_preferences"]["max_tokens"]
    }

    return (system_content, user_content, config)


def task_project_manifest() -> Tuple[str, str, Dict[str, Any]]:
    """
    Generate TEQUILA project manifest for all 35 weeks.

    This prompt produces the authoritative scope-and-sequence JSON that defines:
    - All 35 weeks with titles, grammar focus, chant, vocabulary scope
    - Virtue focus per week (rotating classical virtues)
    - Faith phrases per week (short Latin phrases)
    - 4-day structure pattern (Learn, Practice, Review, Quiz)
    - Open-source policy and originality requirements

    Returns:
        (system_prompt, user_prompt, config_dict)

    Output:
        JSON manifest saved to data/project_manifest.json
    """
    prompt_spec = _load_prompt_json("system/project_manifest.json")

    # Get latin_a_outline from system_overview (or use embedded version)
    try:
        system_overview_spec = _load_prompt_json("system/system_overview.json")
        latin_a_outline = system_overview_spec["inputs"]["latin_a_outline"]
    except (FileNotFoundError, KeyError):
        # Fallback: use outline from this spec (if embedded)
        latin_a_outline = [
            "1. Introduction to Latin & Pronunciation (Ecclesiastical & Classical)",
            "2. First Declension Nouns (Singular)",
            # ... (would be full list in production)
        ]

    # Format outline as numbered list
    outline_text = "\n".join(latin_a_outline)

    # Build user prompt from template
    user_content = "\n".join(prompt_spec["messages"][1]["content_template"])
    user_content = user_content.replace("{{latin_a_outline}}", outline_text)

    system_content = prompt_spec["messages"][0]["content_template"]

    config = {
        "temperature": prompt_spec["model_preferences"]["temperature"],
        "max_tokens": prompt_spec["model_preferences"]["max_tokens"]
    }

    return (system_content, user_content, config)


# ============================================================================
# SCHEMA VALIDATION PROMPT - Validates entire week structure
# ============================================================================

def task_schema_validation(
    week_number: int,
    project_root: str = "curriculum/LatinA",
    week_files: Optional[Dict[str, Any]] = None
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Generate validation report for a complete week.

    This prompt validates all aspects of a week's content:
    - 7-field structure for all 4 days
    - Pydantic schema conformance (WeekSpec, DayDocument, DayRoleContext, FlintBundle)
    - YAML references integrity
    - Spiral learning rules (≥25% for week ≥2)
    - Virtue and faith integration
    - Provenance metadata
    - Originality and licensing (CC BY 4.0)
    - Grade-level calibration (Grade 3 primary)
    - Backward compatibility (6-field legacy support)

    Args:
        week_number: Week number (1-35)
        project_root: Root path for curriculum
        week_files: Optional dict of file contents (if not provided, assumes FS binding)

    Returns:
        (system_prompt, user_prompt, config_dict)

    Output:
        JSON validation report saved to validation_reports/Week{week_number}_validation.json
    """
    prompt_spec = _load_prompt_json("validation/schema_validation.json")

    # Build user prompt with interpolated values
    user_content = "\n".join(prompt_spec["messages"][1]["content_template"])
    user_content = user_content.replace("{{project_root}}", project_root)
    user_content = user_content.replace("{{week_number}}", str(week_number))

    # Interpolate pedagogical rules
    contracts = prompt_spec["inputs"]["contracts"]
    ped_rules = contracts["pedagogical_rules"]
    orig_rules = contracts["originality_rules"]
    grade_rules = contracts["grade_level_rules"]

    user_content = user_content.replace(
        "{{contracts.pedagogical_rules.lesson_total_minutes_min}}",
        str(ped_rules["lesson_total_minutes_min"])
    )
    user_content = user_content.replace(
        "{{contracts.pedagogical_rules.lesson_total_minutes_max}}",
        str(ped_rules["lesson_total_minutes_max"])
    )
    user_content = user_content.replace(
        "{{contracts.originality_rules.n_gram_window}}",
        str(orig_rules["n_gram_window"])
    )
    user_content = user_content.replace(
        "{{contracts.originality_rules.n_gram_similarity_max}}",
        str(orig_rules["n_gram_similarity_max"])
    )
    user_content = user_content.replace(
        "{{contracts.originality_rules.example_overlap_max_pct}}",
        str(orig_rules["example_overlap_max_pct"])
    )
    user_content = user_content.replace(
        "{{contracts.grade_level_rules.english_exposition_target_flesch_kincaid_max}}",
        str(grade_rules["english_exposition_target_flesch_kincaid_max"])
    )
    user_content = user_content.replace(
        "{{contracts.grade_level_rules.english_sentence_length_max}}",
        str(grade_rules["english_sentence_length_max"])
    )
    user_content = user_content.replace(
        "{{contracts.grade_level_rules.latin_sentence_length_max_words}}",
        str(grade_rules["latin_sentence_length_max_words"])
    )

    # If week_files provided, append them to the prompt
    if week_files:
        user_content += "\n\n## Provided File Contents\n"
        for path, content in week_files.items():
            user_content += f"\n### {path}\n```\n{content}\n```\n"

    system_content = prompt_spec["messages"][0]["content_template"]

    config = {
        "temperature": prompt_spec["model_preferences"]["temperature"],
        "max_tokens": prompt_spec["model_preferences"]["max_tokens"]
    }

    return (system_content, user_content, config)


# ============================================================================
# WEEK VALIDATION PROMPT - Final readiness gate for week publication
# ============================================================================

def task_week_validation(
    week_number: int,
    project_root: str = "curriculum/LatinA",
    schema_report: Optional[Dict[str, Any]] = None
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Generate final week validation report - publishability gate.

    This prompt aggregates schema validation, performs cross-file coherence
    checks, verifies assets/assessment coverage, enforces pedagogy thresholds,
    and decides publishability with minimal-diff fix suggestions.

    Validation domains:
    A. Manifest Consistency (title, grammar, chant alignment)
    B. Vocabulary Scope (new vocab count, cross-references)
    C. Prior Knowledge (spiral items referenced in Day1-Day2)
    D. Assessment & Assets (quiz items, chant chart, glossary)
    E. Pedagogy & Timing (lesson minutes, virtue, faith)
    F. License & Originality (frontmatter, attestation)

    Output structure:
    - week: {week_number, path}
    - upstream: {schema_report_gate, errors, warnings}
    - coherence_checks: {manifest_consistency, vocabulary_scope, ...}
    - findings: array of {level, domain, rule, path, detail, anchors}
    - suggested_fixes: array of {for_rule, path, patch_type, patch, notes}
    - metrics: {domains_checked, files_checked, errors, warnings}
    - status: {pass, gate, next_actions}

    Decision logic:
    - upstream fail → gate=fail, pass=false
    - errors>0 → gate=fail, pass=false
    - any coherence fail → gate=fail, pass=false
    - any warn → gate=warn, pass=true
    - else → gate=ok, pass=true

    Args:
        week_number: Week number (1-35)
        project_root: Root path for curriculum
        schema_report: Optional schema validation report from prompt_for_schema_validation

    Returns:
        (system_prompt, user_prompt, config_dict)

    Output:
        JSON validation report with gate status and fix patches
    """
    prompt_spec = _load_prompt_json("validation/week_validation.json")

    # Build user prompt with interpolated values
    user_content = "\n".join(prompt_spec["messages"][1]["content_template"])
    user_content = user_content.replace("{{project_root}}", project_root)
    user_content = user_content.replace("{{week_number}}", str(week_number))

    # Build file paths with zero-padded week number
    week_str = f"Week{week_number:02d}" if week_number < 10 else f"Week{week_number}"

    compiled_week_spec_path = f"{project_root}/{week_str}/Week_Spec/99_compiled_week_spec.json"
    prior_knowledge_digest_path = f"{project_root}/{week_str}/Week_Spec/07_prior_knowledge_digest.json"
    project_manifest_path = f"{project_root}/project_manifest.json"

    user_content = user_content.replace("{{compiled_week_spec_path}}", compiled_week_spec_path)
    user_content = user_content.replace("{{prior_knowledge_digest_path}}", prior_knowledge_digest_path)
    user_content = user_content.replace("{{project_manifest_path}}", project_manifest_path)

    # Replace policy thresholds
    thresholds = prompt_spec["inputs"]["policy_thresholds"]
    user_content = user_content.replace(
        "{{policy_thresholds.min_vocab_new}}",
        str(thresholds["min_vocab_new"])
    )
    user_content = user_content.replace(
        "{{policy_thresholds.max_vocab_new}}",
        str(thresholds["max_vocab_new"])
    )
    user_content = user_content.replace(
        "{{policy_thresholds.min_quiz_items}}",
        str(thresholds["min_quiz_items"])
    )
    user_content = user_content.replace(
        "{{policy_thresholds.lesson_minutes_min}}",
        str(thresholds["lesson_minutes_min"])
    )
    user_content = user_content.replace(
        "{{policy_thresholds.lesson_minutes_max}}",
        str(thresholds["lesson_minutes_max"])
    )
    user_content = user_content.replace(
        "{{policy_thresholds.license_allowed}}",
        str(thresholds["license_allowed"])
    )

    # If schema_report provided, serialize it
    # Otherwise leave as placeholder for file/API reference
    if schema_report:
        schema_json = json.dumps(schema_report, indent=2)
        # Note: In the prompt spec, schema_report is referenced but not templated
        # We could add it to the context if needed
        pass

    system_content = prompt_spec["messages"][0]["content_template"]

    config = {
        "temperature": prompt_spec["model_preferences"]["temperature"],
        "max_tokens": prompt_spec["model_preferences"]["max_tokens"]
    }

    return (system_content, user_content, config)


# ============================================================================
# WEEK SPEC PROMPT - Generates complete 12-file week specification
# ============================================================================

def task_week_spec(
    week_number: int,
    manifest_entry: Dict[str, Any],
    research_plan: Optional[Dict[str, Any]] = None
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Generate complete Week Spec kit (12 files) for a single week.

    NEW: Receives PHASE 0 research findings to inform generation.

    This prompt produces all Week_Spec files:
    - 01_metadata.json
    - 02_objectives.json
    - 03_vocabulary.json
    - 04_grammar_focus.md
    - 05_virtue_focus.md
    - 06_faith_phrase.md
    - 07_prior_knowledge_digest.json
    - 08_chant_chart.txt
    - 09_assessment_overview.json
    - 10_teacher_notes.md
    - 11_weekly_review_questions.md
    - 99_compiled_week_spec.json

    Args:
        week_number: Week number (1-35)
        manifest_entry: Week entry from project_manifest.week_manifest
        research_plan: Optional PHASE 0 research findings (12 outputs)

    Returns:
        (system_prompt, user_prompt, config_dict)

    Output:
        JSON with week_info and generated_files array
    """
    prompt_spec = _load_prompt_json("week/week_spec.json")

    # Build user prompt with interpolated manifest entry
    user_content = "\n".join(prompt_spec["messages"][1]["content_template"])

    # Replace week_number
    user_content = user_content.replace("{{week_number}}", str(week_number))

    # Replace manifest entry fields
    user_content = user_content.replace(
        "{{week_manifest_entry.title}}",
        manifest_entry.get("title", "")
    )
    user_content = user_content.replace(
        "{{week_manifest_entry.grammar_focus}}",
        manifest_entry.get("grammar_focus", "")
    )
    user_content = user_content.replace(
        "{{week_manifest_entry.chant}}",
        manifest_entry.get("chant", "")
    )
    user_content = user_content.replace(
        "{{week_manifest_entry.virtue_focus}}",
        manifest_entry.get("virtue_focus", "")
    )
    user_content = user_content.replace(
        "{{week_manifest_entry.faith_phrase}}",
        manifest_entry.get("faith_phrase", "")
    )

    # Replace vocabulary_scope (array)
    vocab_scope = manifest_entry.get("vocabulary_scope", [])
    vocab_json = json.dumps(vocab_scope)
    user_content = user_content.replace("{{week_manifest_entry.vocabulary_scope}}", vocab_json)

    # INJECT PHASE 0 RESEARCH if available
    if research_plan:
        # Extract all 12 research outputs
        week_entry = research_plan.get("00_week_entry", {})
        backward = research_plan.get("01_backward_analysis", {})
        forward = research_plan.get("02_forward_analysis", {})
        pedagogy = research_plan.get("03_pedagogical_research", {})
        vocab_plan = research_plan.get("04_vocabulary_plan", {})
        duration = research_plan.get("05_session_duration", {})
        virtue = research_plan.get("06_virtue_faith_strategy", {})
        assessment = research_plan.get("07_assessment_plan", {})
        differentiation = research_plan.get("08_differentiation_plan", {})
        materials = research_plan.get("09_materials_list", {})
        masters = research_plan.get("10_master_analysis", {})
        alignment = research_plan.get("11_alignment_guide", {})

        research_injection = f"""

## PHASE 0 RESEARCH FINDINGS - USE ALL OF THIS DATA

You have access to comprehensive pedagogical research conducted before generation.
ALL of these findings MUST inform your week spec generation:

### 1. VERIFIED VOCABULARY (MUST USE EXACTLY)
New Latin Words (verified by reasoning model):
{json.dumps([{'word': w.get('word', ''), 'english': w.get('english', ''), 'rationale': w.get('rationale', '')} for w in vocab_plan.get('new_latin_words', [])], indent=2)}

Recycled Words (for spiral review):
{json.dumps([{'word': w.get('word', ''), 'originally_taught_week': w.get('originally_taught_week', '')} for w in vocab_plan.get('recycled_latin_words', [])], indent=2)}

Alignment Check: {json.dumps(vocab_plan.get('alignment_check', {}), indent=2)}

CRITICAL: Use ONLY these words in 03_vocabulary.json. Do NOT generate different vocabulary.

### 2. PRIOR KNOWLEDGE (for 07_prior_knowledge_digest.json)
Students entering this week already know:
- Vocabulary: {json.dumps([v.get('word', '') for v in backward.get('cumulative_latin_vocabulary', [])[:10]], indent=2)}
- Grammar Concepts: {json.dumps([c.get('concept', '') for c in backward.get('cumulative_grammar_concepts', [])[:5]], indent=2)}
- Student State: {backward.get('student_knowledge_state', '')}
- Spiral Target: {backward.get('spiral_review_target_percentage', 0.25)*100}% prior content

### 3. PEDAGOGICAL APPROACH (for 04_grammar_focus.md and 10_teacher_notes.md)
How classical curricula teach this topic:
- Logos Latin Approach: {pedagogy.get('logos_latin_approach', '')[:200]}...
- Time-Tested Chants: {json.dumps(pedagogy.get('time_tested_chants', []), indent=2)}
- Common Misconceptions: {json.dumps(pedagogy.get('common_misconceptions', []), indent=2)}

### 4. SESSION TIMING (for daily structure)
- Recommended Duration: {duration.get('recommended_duration_minutes', 15)} minutes
- Time Breakdown: {json.dumps(duration.get('time_breakdown', {}), indent=2)}

### 5. VIRTUE & FAITH INTEGRATION (for 05_virtue_focus.md and 06_faith_phrase.md)
- Virtue: {virtue.get('virtue_focus', '')}
- Connection to Learning: {virtue.get('virtue_connection_to_language_learning', '')[:150]}...
- Scripture: {virtue.get('scripture_reference', {}).get('passage', '')} - "{virtue.get('scripture_reference', {}).get('text', '')[:100]}..."
- Faith Phrase: {virtue.get('faith_phrase', '')}
- Explanation: {virtue.get('faith_phrase_explanation', '')[:150]}...

### 6. ASSESSMENT DESIGN (for 09_assessment_overview.json)
Day 4 Quiz Components:
{json.dumps([{'component': c.get('component', ''), 'format': c.get('format', '')} for c in assessment.get('day_4_quiz_components', [])], indent=2)}

### 7. DIFFERENTIATION (for 10_teacher_notes.md)
- Struggling Students: {json.dumps(differentiation.get('struggling_students', {}).get('scaffolds', [])[:3], indent=2)}
- Advanced Students: {json.dumps(differentiation.get('advanced_students', {}).get('extensions', [])[:3], indent=2)}

### 8. MATERIALS NEEDED (for 10_teacher_notes.md)
- Chant Charts: {json.dumps([c.get('title', '') for c in materials.get('chant_charts', [])], indent=2)}
- Flashcard Sets: {json.dumps([s.get('set_name', '') for s in materials.get('flashcard_sets', [])], indent=2)}

### 9. STYLE GUIDE (from gold standard Week 1 & Week 11)
Class Name Pattern: {masters.get('class_name_pattern', '')}
Summary Style: {json.dumps(masters.get('summary_style_guide', {}), indent=2)}
Vocabulary Format: {json.dumps(masters.get('vocabulary_format', {}), indent=2)}

### 10. ALIGNMENT GUIDANCE (how to combine research with style)
{json.dumps(alignment, indent=2)}

---

GENERATION INSTRUCTIONS:
1. Use ONLY the verified vocabulary from section 1
2. Include spiral review from section 2 in 07_prior_knowledge_digest.json
3. Use pedagogical approach from section 3 in grammar explanations
4. Use timing from section 4 to structure daily activities
5. Use virtue/faith from section 5 in 05_virtue_focus.md and 06_faith_phrase.md
6. Use assessment design from section 6 in 09_assessment_overview.json
7. Use differentiation from section 7 in 10_teacher_notes.md
8. Match style patterns from sections 9 & 10
"""
        user_content += research_injection

    system_content = prompt_spec["messages"][0]["content_template"]

    config = {
        "temperature": prompt_spec["model_preferences"]["temperature"],
        "max_tokens": prompt_spec["model_preferences"]["max_tokens"]
    }

    return (system_content, user_content, config)


# ============================================================================
# PRIOR KNOWLEDGE DIGEST PROMPT - Generates spiral learning memory
# ============================================================================

def task_prior_knowledge_digest(
    current_week_number: int,
    project_root: str = "curriculum/LatinA"
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Generate prior_knowledge_digest.json for spiral learning validation.

    This prompt synthesizes all prior weeks' content into a structured digest
    identifying which vocabulary, grammar, chants, and virtue/faith concepts
    are being recycled in the current week.

    Output structure:
    - digest_for_week: integer
    - summary: counts per category
    - vocabulary_recycled: array of recycled vocab items
    - grammar_recycled: array of recycled grammar concepts
    - chant_recycled: array of recycled chants
    - virtue_faith_links: array of virtue/faith connections
    - originality_attestation: true
    - license: "CC BY 4.0"

    Args:
        current_week_number: Week number (1-35)
        project_root: Root path for curriculum

    Returns:
        (system_prompt, user_prompt, config_dict)

    Output:
        JSON digest saved to Week_Spec/07_prior_knowledge_digest.json
    """
    prompt_spec = _load_prompt_json("digest/prior_knowledge_digest.json")

    # Build user prompt with interpolated values
    user_content = "\n".join(prompt_spec["messages"][1]["content_template"])
    user_content = user_content.replace("{{current_week_number}}", str(current_week_number))
    user_content = user_content.replace("{{project_root}}", project_root)

    # Replace dynamic expressions like {{current_week_number - 1}}
    user_content = user_content.replace(
        "{{current_week_number - 1}}",
        str(current_week_number - 1)
    )

    system_content = prompt_spec["messages"][0]["content_template"]

    config = {
        "temperature": prompt_spec["model_preferences"]["temperature"],
        "max_tokens": prompt_spec["model_preferences"]["max_tokens"]
    }

    return (system_content, user_content, config)


# ============================================================================
# WEEK SUMMARY PROMPT - Generates human-readable week overview
# ============================================================================

def task_week_summary(
    week_number: int,
    week_spec: Optional[Dict[str, Any]] = None,
    prior_knowledge_digest: Optional[Dict[str, Any]] = None,
    project_root: str = "curriculum/LatinA"
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Generate 00_week_summary.md - human-readable week overview.

    This prompt synthesizes week data into a coherent markdown summary that
    combines grammar, vocabulary, virtue, faith, chants, and prior knowledge
    for educators, validators, and Sparky.

    Output structure (JSON with markdown content):
    - week_number: integer
    - file_name: "00_week_summary.md"
    - content: markdown string with YAML frontmatter

    Markdown sections:
    1. Week Overview (title, grammar, chant, virtue, faith)
    2. Learning Objectives (3-5 bullets)
    3. Prior Knowledge Connection (recycled content)
    4. New Concepts Introduced (grammar + vocab)
    5. Virtue and Faith Integration
    6. Pedagogical Flow (Days 1-4)
    7. Teacher Notes
    8. YAML frontmatter (license, provenance)

    Args:
        week_number: Week number (1-35)
        week_spec: Optional compiled week spec (99_compiled_week_spec.json)
        prior_knowledge_digest: Optional digest (07_prior_knowledge_digest.json)
        project_root: Root path for curriculum

    Returns:
        (system_prompt, user_prompt, config_dict)

    Output:
        JSON with week_number, file_name, and markdown content string
    """
    prompt_spec = _load_prompt_json("week/week_summary.json")

    # Build user prompt with interpolated values
    user_content = "\n".join(prompt_spec["messages"][1]["content_template"])
    user_content = user_content.replace("{{week_number}}", str(week_number))
    user_content = user_content.replace("{{project_root}}", project_root)

    # If week_spec provided, serialize it for context
    if week_spec:
        week_spec_json = json.dumps(week_spec, indent=2)
        user_content = user_content.replace("{{week_spec}}", week_spec_json)
    else:
        # Placeholder for file reference
        user_content = user_content.replace(
            "{{week_spec}}",
            f"Load from {project_root}/Week{week_number:02d}/Week_Spec/99_compiled_week_spec.json"
        )

    # If prior_knowledge_digest provided, serialize it
    if prior_knowledge_digest:
        digest_json = json.dumps(prior_knowledge_digest, indent=2)
        user_content = user_content.replace("{{prior_knowledge_digest}}", digest_json)
    else:
        # Placeholder for file reference
        user_content = user_content.replace(
            "{{prior_knowledge_digest}}",
            f"Load from {project_root}/Week{week_number:02d}/Week_Spec/07_prior_knowledge_digest.json"
        )

    system_content = prompt_spec["messages"][0]["content_template"]

    config = {
        "temperature": prompt_spec["model_preferences"]["temperature"],
        "max_tokens": prompt_spec["model_preferences"]["max_tokens"]
    }

    return (system_content, user_content, config)


def task_role_context(week_spec: dict, research_plan: Optional[Dict[str, Any]] = None) -> Tuple[str, str, Optional[Dict]]:
    """
    Generate prompts for Sparky role context (week-level).

    NEW: Accepts PHASE 0 research to inform Sparky's behavior based on
    week difficulty, virtue focus, and differentiation needs.

    Args:
        week_spec: The week specification data
        research_plan: Optional PHASE 0 research findings

    Returns:
        (system_prompt, user_prompt, json_schema_hint)
    """
    sys = (
        "Generate Sparky Role Context JSON for a LATIN A curriculum week.\n\n"
        "IMPORTANT: This is Classical Latin instruction (declensions, conjugations, cases).\n"
        "Sparky teaches LATIN vocabulary and grammar, NOT modern languages.\n\n"
        "Fields to generate:\n"
        "- identity (Sparky's character and teaching philosophy)\n"
        "- student_profile (Grade 3 students learning Classical Latin)\n"
        "- daily_cycle (typical Latin lesson structure)\n"
        "- reinforcement_method (how Sparky encourages Latin practice)\n"
        "- feedback_style (how Sparky corrects Latin errors)\n"
        "- success_criteria (what Latin mastery looks like)\n"
        "- knowledge_recycling (spiral learning approach for Latin)\n\n"
        "Return only valid JSON."
    )

    usr = (
        "Base this Sparky role context on the week metadata and spiral links:\n\n"
        + orjson.dumps(
            {
                "metadata": week_spec.get("01_metadata.json", {}),
                "spiral_links": week_spec.get("09_spiral_links.json", {})
            },
            option=orjson.OPT_INDENT_2
        ).decode()
    )

    # Inject PHASE 0 research if available
    if research_plan:
        virtue = research_plan.get("06_virtue_faith_strategy", {})
        differentiation = research_plan.get("08_differentiation_plan", {})
        pedagogy = research_plan.get("03_pedagogical_research", {})

        research_context = f"""

## PHASE 0 RESEARCH - INFORM SPARKY'S BEHAVIOR

Adapt Sparky's role context based on this week's needs:

### Virtue Focus:
- Virtue: {virtue.get('virtue_focus', '')}
- How it connects to learning: {virtue.get('virtue_connection_to_language_learning', '')[:200]}
- Incorporate this virtue into encouragement_triggers and praise language

### Differentiation Needs:
- Struggling Students Scaffolds: {json.dumps(differentiation.get('struggling_students', {}).get('scaffolds', [])[:2], indent=2)}
- Advanced Extensions: {json.dumps(differentiation.get('advanced_students', {}).get('extensions', [])[:2], indent=2)}
- Adjust feedback_style to support both groups

### Common Misconceptions:
{json.dumps(pedagogy.get('common_misconceptions', [])[:3], indent=2)}
- Include these in knowledge_recycling and error correction approaches

Generate a Sparky role context that adapts to this week's virtue, difficulty level, and student needs.
"""
        usr += research_context

    return sys, usr, None


def task_assets(week_spec: dict) -> Tuple[str, str, Optional[Dict]]:
    """
    Generate prompts for week assets (text files).

    Args:
        week_spec: The week specification data

    Returns:
        (system_prompt, user_prompt, json_schema_hint)
    """
    sys = (
        "Generate plain-text content for these weekly assets:\n"
        "1. ChantChart - formatted chant with Latin and English\n"
        "2. Glossary - vocabulary list with definitions\n"
        "3. Copywork - practice sentences for handwriting\n"
        "4. QuizPacket - assessment questions\n"
        "5. TeacherKey - answer key for quiz\n"
        "6. VirtueEntry - reflection prompt on week's virtue\n\n"
        "Keep each asset concise and pedagogically appropriate.\n"
        "Return as JSON object with keys matching asset names."
    )

    usr = (
        "Week information:\n\n"
        + orjson.dumps(
            {
                "title": week_spec.get("01_metadata.json", {}).get("title", ""),
                "vocabulary": week_spec.get("03_vocabulary.json", [])[:5],  # Sample
                "chant": week_spec.get("05_chant.json", {}),
                "virtue_focus": week_spec.get("01_metadata.json", {}).get("virtue_focus", "")
            },
            option=orjson.OPT_INDENT_2
        ).decode()
    )

    return sys, usr, None


# ============================================================================
# CLASS NAME PROMPT (Field 01) - Student-facing lesson title
# ============================================================================

def task_class_name(
    week_number: int,
    day_number: int,
    week_title: str,
    grammar_focus: str,
    chant: str,
    vocabulary_scope: Optional[list] = None
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Generate class_name (field 01) - student-facing lesson title.

    This prompt creates memorable, consistent class names following the pattern:
    "Latin A — Week {N} Day {D}: {Grammar Topic} — {Intent}"

    Naming rules:
    - ≤ 60 characters in descriptive portion
    - Title Case, no trailing punctuation
    - Concrete, kid-friendly (grades 3-5)
    - No trademarked names, colons (except prefix), or emojis
    - Day intent: 1=Learn, 2=Practice, 3=Review, 4=Quiz

    Args:
        week_number: Week number (1-35)
        day_number: Day number (1-4)
        week_title: Week title from manifest
        grammar_focus: Grammar focus from manifest
        chant: Chant description from manifest
        vocabulary_scope: Optional vocabulary list from manifest

    Returns:
        (system_prompt, user_prompt, config_dict)

    Output:
        JSON with single key: {"class_name": "..."}
    """
    prompt_spec = _load_prompt_json("day/class_name.json")

    # Map day number to intent
    day_intents = {1: "Learn", 2: "Practice", 3: "Review", 4: "Quiz"}
    day_intent = day_intents.get(day_number, "Learn")

    # Build user prompt with interpolated values
    user_content = "\n".join(prompt_spec["messages"][1]["content_template"])
    user_content = user_content.replace("{{project_name}}", prompt_spec["inputs"]["project_name"])
    user_content = user_content.replace("{{week_number}}", str(week_number))
    user_content = user_content.replace("{{day_number}}", str(day_number))
    user_content = user_content.replace("{{week_title}}", week_title)
    user_content = user_content.replace("{{grammar_focus}}", grammar_focus)
    user_content = user_content.replace("{{chant}}", chant)
    user_content = user_content.replace("{{day_intent[day_number]}}", day_intent)

    system_content = prompt_spec["messages"][0]["content_template"]

    config = {
        "temperature": prompt_spec["model_preferences"]["temperature"],
        "max_tokens": prompt_spec["model_preferences"]["max_tokens"],
        "model": prompt_spec["model_preferences"]["model"]  # Note: uses gpt-4o-mini
    }

    return (system_content, user_content, config)


# ============================================================================
# DAY SUMMARY PROMPT (Field 02) - Daily lesson overview markdown
# ============================================================================

def task_day_summary(
    week_number: int,
    day_number: int,
    class_name: str,
    week_spec: Optional[Dict[str, Any]] = None,
    prior_knowledge_digest: Optional[Dict[str, Any]] = None
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Generate 02_summary.md - daily lesson summary markdown.

    This prompt creates a 150-250 word structured markdown summary explaining:
    - What the student should learn today (objective)
    - Prior knowledge connections (2-3 items from digest)
    - Focus for today (grammar, chant, vocabulary)
    - Virtue & faith connection
    - Teacher notes (pacing, pronunciation)

    Output structure (JSON with markdown content):
    - day_summary: markdown string with YAML frontmatter

    Markdown sections:
    1. YAML header (week, day, license, provenance)
    2. Objective (1-2 sentences)
    3. Prior Knowledge (2-3 items)
    4. Focus for Today (grammar, chant, vocab list)
    5. Virtue & Faith Connection (1-2 sentences)
    6. Teacher Notes (pacing/pronunciation)

    Args:
        week_number: Week number (1-35)
        day_number: Day number (1-4)
        class_name: Class name from prompt_for_class_name
        week_spec: Optional compiled week spec
        prior_knowledge_digest: Optional prior knowledge digest

    Returns:
        (system_prompt, user_prompt, config_dict)

    Output:
        JSON with single key: {"day_summary": "...markdown..."}
    """
    prompt_spec = _load_prompt_json("day/day_summary.json")

    # Map day number to intent
    day_intents = {
        1: "Learn: introduce new grammar, vocabulary, and chant.",
        2: "Practice: review, translate, and recite.",
        3: "Review: answer questions and reinforce mastery.",
        4: "Quiz: assess learning and reflect on progress."
    }
    day_intent = day_intents.get(day_number, "Learn")

    # Build user prompt with interpolated values
    user_content = "\n".join(prompt_spec["messages"][1]["content_template"])
    user_content = user_content.replace("{{week_number}}", str(week_number))
    user_content = user_content.replace("{{day_number}}", str(day_number))
    user_content = user_content.replace("{{class_name}}", class_name)
    user_content = user_content.replace("{{day_intent[day_number]}}", day_intent)

    # If week_spec provided, interpolate its fields
    if week_spec:
        metadata = week_spec.get("01_metadata.json", {})
        user_content = user_content.replace(
            "{{week_spec.title}}",
            metadata.get("week_title", "")
        )
        user_content = user_content.replace(
            "{{week_spec.grammar_focus}}",
            metadata.get("grammar_focus", "")
        )
        chant_data = week_spec.get("05_chant.json", {})
        chant_text = chant_data.get("text", "") if isinstance(chant_data, dict) else str(chant_data)
        user_content = user_content.replace(
            "{{week_spec.chant}}",
            chant_text
        )
        user_content = user_content.replace(
            "{{week_spec.virtue_focus}}",
            metadata.get("virtue_focus", "")
        )
        user_content = user_content.replace(
            "{{week_spec.faith_phrase}}",
            metadata.get("faith_phrase", "")
        )
    else:
        # Leave placeholders for file/API reference
        user_content = user_content.replace("{{week_spec.title}}", "[Load from week spec]")
        user_content = user_content.replace("{{week_spec.grammar_focus}}", "[Load from week spec]")
        user_content = user_content.replace("{{week_spec.chant}}", "[Load from week spec]")
        user_content = user_content.replace("{{week_spec.virtue_focus}}", "[Load from week spec]")
        user_content = user_content.replace("{{week_spec.faith_phrase}}", "[Load from week spec]")

    system_content = prompt_spec["messages"][0]["content_template"]

    config = {
        "temperature": prompt_spec["model_preferences"]["temperature"],
        "max_tokens": prompt_spec["model_preferences"]["max_tokens"],
        "model": prompt_spec["model_preferences"]["model"]  # gpt-4o-mini
    }

    return (system_content, user_content, config)


# ============================================================================
# GRADE LEVEL PROMPT (Field 03) - Fixed metadata value
# ============================================================================

def task_grade_level(
    week_number: int,
    day_number: int
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Generate 03_grade_level.txt - fixed grade level metadata.

    This prompt outputs a fixed standardized value for all Latin A lessons:
    "Grade 3 (Grammar Stage, U.S.)"

    Since all Latin A lessons target the same grade level, this is a
    deterministic output with zero temperature for consistency.

    Output structure:
    - Single JSON key: {"grade_level": "Grade 3 (Grammar Stage, U.S.)"}

    Args:
        week_number: Week number (1-35)
        day_number: Day number (1-4)

    Returns:
        (system_prompt, user_prompt, config_dict)

    Output:
        JSON with single key: {"grade_level": "Grade 3 (Grammar Stage, U.S.)"}
    """
    prompt_spec = _load_prompt_json("day/grade_level.json")

    # Build user prompt with interpolated values
    user_content = "\n".join(prompt_spec["messages"][1]["content_template"])
    user_content = user_content.replace("{{week_number}}", str(week_number))
    user_content = user_content.replace("{{day_number}}", str(day_number))

    system_content = prompt_spec["messages"][0]["content_template"]

    config = {
        "temperature": prompt_spec["model_preferences"]["temperature"],
        "max_tokens": prompt_spec["model_preferences"]["max_tokens"],
        "model": prompt_spec["model_preferences"]["model"]  # gpt-4o-mini
    }

    return (system_content, user_content, config)


# ============================================================================
# ROLE_CONTEXT PROMPT (Field 04) - Day-level Sparky coaching brief
# ============================================================================

def task_role_context_day(
    week_number: int,
    day_number: int,
    class_name: str,
    week_spec: Optional[Dict[str, Any]] = None,
    prior_knowledge_digest: Optional[Dict[str, Any]] = None,
    day_summary: Optional[Dict[str, Any]] = None
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Generate 04_role_context.json - Day-level coaching brief for Sparky.

    This prompt produces a comprehensive DayRoleContext schema that defines:
    - Identity and audience (Sparky persona, Grade 3 target)
    - Lesson slot (week, day, title)
    - Objectives (2-4 measurable student outcomes)
    - Focus areas (3-5 teaching priorities)
    - Spiral hooks (vocabulary + grammar from prior weeks)
    - Virtue integration (from WeekSpec)
    - Faith integration (from WeekSpec)
    - Coaching cues (4-6 short lines Sparky can say)
    - Common misconceptions (pattern + correction)
    - Checks for understanding (3-5 CFU questions)
    - Success criteria (3-4 observable outcomes)
    - Differentiation (support scaffolds + extensions)
    - Classroom management (2-3 reminders)
    - Constraints (time, tone, no direct translation)

    Output structure (JSON schema):
    - identity: string (e.g., "Sparky the Encourager")
    - audience: "Grade 3 (Grammar Stage, U.S.)" (fixed)
    - lesson_slot: {week, day, title}
    - objectives: array of strings (2-4)
    - focus_areas: array of strings (3-5)
    - spiral_hooks: {vocabulary_spiral, grammar_spiral}
    - virtue_integration: {virtue, prompt ≤40 words}
    - faith_integration: {phrase, usage_note ≤40 words}
    - coaching_cues: array of strings (4-6)
    - common_misconceptions: array of {pattern, correction_cue}
    - checks_for_understanding: array of strings (3-5)
    - success_criteria: array of strings (3-4)
    - differentiation: {support, extension}
    - classroom_management: array of strings (2-3)
    - constraints: {time_window_minutes, tone, no_translation_key}
    - __provenance: {provider, model, generated_at}

    Args:
        week_number: Week number (1-35)
        day_number: Day number (1-4)
        class_name: Class name from prompt_for_class_name
        week_spec: Optional week spec data
        prior_knowledge_digest: Optional prior knowledge digest
        day_summary: Optional day summary

    Returns:
        (system_prompt, user_prompt, config_dict)

    Output:
        JSON with complete DayRoleContext schema
    """
    prompt_spec = _load_prompt_json("day/role_context.json")

    # Build user prompt with interpolated values
    user_content = "\n".join(prompt_spec["messages"][1]["content_template"])
    user_content = user_content.replace("{{project_name}}", prompt_spec["inputs"]["project_name"])
    user_content = user_content.replace("{{week_number}}", str(week_number))
    user_content = user_content.replace("{{day_number}}", str(day_number))
    user_content = user_content.replace("{{class_name}}", class_name)
    user_content = user_content.replace("{{grade_level_fixed}}", prompt_spec["inputs"]["grade_level_fixed"])

    # If week_spec provided, serialize it
    if week_spec:
        week_spec_json = json.dumps(week_spec, indent=2)
        user_content = user_content.replace("{{week_spec}}", week_spec_json)
    else:
        user_content = user_content.replace(
            "{{week_spec}}",
            f"[Load from curriculum/LatinA/Week{week_number:02d}/Week_Spec/99_compiled_week_spec.json]"
        )

    # If prior_knowledge_digest provided, serialize it
    if prior_knowledge_digest:
        digest_json = json.dumps(prior_knowledge_digest, indent=2)
        user_content = user_content.replace("{{prior_knowledge_digest}}", digest_json)
    else:
        user_content = user_content.replace(
            "{{prior_knowledge_digest}}",
            f"[Load from curriculum/LatinA/Week{week_number:02d}/Week_Spec/07_prior_knowledge_digest.json]"
        )

    # If day_summary provided, serialize it
    if day_summary:
        if isinstance(day_summary, dict) and "day_summary" in day_summary:
            summary_content = day_summary["day_summary"]
        elif isinstance(day_summary, str):
            summary_content = day_summary
        else:
            summary_content = json.dumps(day_summary)
        user_content = user_content.replace("{{day_summary}}", summary_content)
    else:
        user_content = user_content.replace(
            "{{day_summary}}",
            f"[Load from curriculum/LatinA/Week{week_number:02d}/Day{day_number:02d}/02_summary.md]"
        )

    system_content = prompt_spec["messages"][0]["content_template"]

    config = {
        "temperature": prompt_spec["model_preferences"]["temperature"],
        "max_tokens": prompt_spec["model_preferences"]["max_tokens"],
        "model": prompt_spec["model_preferences"]["model"]  # gpt-4o
    }

    return (system_content, user_content, config)


# ============================================================================
# GUIDELINES PROMPT (Field 05) - Minute-by-minute teaching script
# ============================================================================

def task_guidelines(
    week_number: int,
    day_number: int,
    class_name: str,
    week_spec: Optional[Dict[str, Any]] = None,
    prior_knowledge_digest: Optional[Dict[str, Any]] = None,
    day_summary: Optional[Dict[str, Any]] = None,
    role_context: Optional[Dict[str, Any]] = None
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Generate 05_guidelines_for_sparky.md - Minute-by-minute teaching script.

    This prompt produces a detailed markdown teaching script that implements
    the role_context (Field 04) with concrete lesson flow, dialogue, and activities.

    Output structure (Markdown with YAML frontmatter):
    - YAML header (week, day, title, time_window_minutes, tone, audience, license, provenance)
    - Objectives & Success Criteria (from role_context)
    - Materials & Setup
    - Minute-by-Minute Flow (5 phases):
      1. Greeting & Spiral Review (5 min)
      2. Chant Introduction/Practice (5-7 min)
      3. Grammar Instruction (8-10 min)
      4. Guided Practice (5-7 min)
      5. Closure & Virtue Tie-In (2-3 min)
    - Coaching Notes (misconceptions, differentiation, classroom management)
    - Assessment Checkpoints

    Pedagogical features:
    - Embeds spiral_hooks from role_context in Phase 1
    - Uses coaching_cues from role_context as dialogue
    - Includes common_misconceptions with correction cues
    - Implements checks_for_understanding throughout
    - Integrates virtue and faith in Phase 5
    - Respects constraints (time_window, tone, no_translation_key)

    Args:
        week_number: Week number (1-35)
        day_number: Day number (1-4)
        class_name: Class name from prompt_for_class_name
        week_spec: Optional week spec data
        prior_knowledge_digest: Optional prior knowledge digest
        day_summary: Optional day summary
        role_context: Optional role context from prompt_for_role_context

    Returns:
        (system_prompt, user_prompt, config_dict)

    Output:
        JSON with single key: {"guidelines_markdown": "...markdown..."}
    """
    prompt_spec = _load_prompt_json("day/guidelines.json")

    # Build user prompt with interpolated values
    user_content = "\n".join(prompt_spec["messages"][1]["content_template"])
    user_content = user_content.replace("{{project_name}}", prompt_spec["inputs"]["project_name"])
    user_content = user_content.replace("{{week_number}}", str(week_number))
    user_content = user_content.replace("{{day_number}}", str(day_number))
    user_content = user_content.replace("{{class_name}}", class_name)
    user_content = user_content.replace("{{grade_level_fixed}}", prompt_spec["inputs"]["grade_level_fixed"])

    # If week_spec provided, serialize it
    if week_spec:
        week_spec_json = json.dumps(week_spec, indent=2)
        user_content = user_content.replace("{{week_spec}}", week_spec_json)
    else:
        user_content = user_content.replace(
            "{{week_spec}}",
            f"[Load from curriculum/LatinA/Week{week_number:02d}/Week_Spec/99_compiled_week_spec.json]"
        )

    # If prior_knowledge_digest provided, serialize it
    if prior_knowledge_digest:
        digest_json = json.dumps(prior_knowledge_digest, indent=2)
        user_content = user_content.replace("{{prior_knowledge_digest}}", digest_json)
    else:
        user_content = user_content.replace(
            "{{prior_knowledge_digest}}",
            f"[Load from curriculum/LatinA/Week{week_number:02d}/Week_Spec/07_prior_knowledge_digest.json]"
        )

    # If day_summary provided, serialize it
    if day_summary:
        if isinstance(day_summary, dict) and "day_summary" in day_summary:
            summary_content = day_summary["day_summary"]
        elif isinstance(day_summary, str):
            summary_content = day_summary
        else:
            summary_content = json.dumps(day_summary)
        user_content = user_content.replace("{{day_summary}}", summary_content)
    else:
        user_content = user_content.replace(
            "{{day_summary}}",
            f"[Load from curriculum/LatinA/Week{week_number:02d}/Day{day_number:02d}/02_summary.md]"
        )

    # If role_context provided, serialize it
    if role_context:
        role_context_json = json.dumps(role_context, indent=2)
        user_content = user_content.replace("{{role_context}}", role_context_json)
    else:
        user_content = user_content.replace(
            "{{role_context}}",
            f"[Load from curriculum/LatinA/Week{week_number:02d}/Day{day_number:02d}/04_role_context.json]"
        )

    system_content = prompt_spec["messages"][0]["content_template"]

    config = {
        "temperature": prompt_spec["model_preferences"]["temperature"],
        "max_tokens": prompt_spec["model_preferences"]["max_tokens"],
        "model": prompt_spec["model_preferences"]["model"]  # gpt-4o
    }

    return (system_content, user_content, config)


# ============================================================================
# DAY DOCUMENT PROMPT (Field 06) - Structured JSON lesson plan
# ============================================================================

def task_document_day(
    week_number: int,
    day_number: int,
    class_name: str,
    week_spec: Optional[Dict[str, Any]] = None,
    prior_knowledge_digest: Optional[Dict[str, Any]] = None,
    role_context: Optional[Dict[str, Any]] = None,
    guidelines: Optional[str] = None
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Generate 06_document_for_sparky.json - Structured JSON lesson plan.

    This prompt produces the core schema-based learning document that drives
    both validation and AI tutoring. It compiles all prior fields into a
    complete DayDocument with lesson steps, vocabulary, grammar, chant,
    virtue/faith integration, and spiral content references.

    Output structure (DayDocument schema):
    - metadata: {week, day, class_name, grade, time_total_minutes, license,
                 validated_by, originality_attestation, provenance}
    - lesson_steps: array of 4-6 steps (each with: step_number, title,
                    duration_minutes, instruction, activity_type, materials,
                    spiral_content, virtue_link, faith_phrase)
    - vocabulary_today: array of strings (≥3 words)
    - grammar_focus: string
    - chant_focus: string
    - checks_for_understanding: array of strings
    - success_criteria: array of strings
    - constraints: {tone, no_translation_key}

    Pedagogical features:
    - Lesson steps sum to 20-25 minutes total
    - At least one step includes spiral_content references
    - Virtue and faith integrated naturally in 1-2 steps
    - Grade 3 appropriate language throughout
    - Activity types: chant, recitation, translation, discussion, reflection

    Args:
        week_number: Week number (1-35)
        day_number: Day number (1-4)
        class_name: Class name from prompt_for_class_name
        week_spec: Optional week spec data
        prior_knowledge_digest: Optional prior knowledge digest
        role_context: Optional role context from prompt_for_role_context
        guidelines: Optional guidelines markdown from prompt_for_guidelines

    Returns:
        (system_prompt, user_prompt, config_dict)

    Output:
        JSON with single key: {"day_document": {...DayDocument schema...}}
    """
    prompt_spec = _load_prompt_json("day/day_document.json")

    # Build user prompt with interpolated values
    user_content = "\n".join(prompt_spec["messages"][1]["content_template"])
    user_content = user_content.replace("{{week_number}}", str(week_number))
    user_content = user_content.replace("{{day_number}}", str(day_number))
    user_content = user_content.replace("{{class_name}}", class_name)
    user_content = user_content.replace("{{grade_level}}", prompt_spec["inputs"]["grade_level"])

    # If week_spec provided, serialize it (excerpt: first 500 chars to save tokens)
    if week_spec:
        week_spec_json = json.dumps(week_spec, indent=2)
        # Truncate if very large
        if len(week_spec_json) > 2000:
            week_spec_excerpt = week_spec_json[:2000] + "\n... (truncated)"
        else:
            week_spec_excerpt = week_spec_json
        user_content = user_content.replace("{{week_spec}}", week_spec_excerpt)
    else:
        user_content = user_content.replace(
            "{{week_spec}}",
            f"[Load from curriculum/LatinA/Week{week_number:02d}/Week_Spec/99_compiled_week_spec.json]"
        )

    # If prior_knowledge_digest provided, serialize it (excerpt)
    if prior_knowledge_digest:
        digest_json = json.dumps(prior_knowledge_digest, indent=2)
        if len(digest_json) > 1000:
            digest_excerpt = digest_json[:1000] + "\n... (truncated)"
        else:
            digest_excerpt = digest_json
        user_content = user_content.replace("{{prior_knowledge_digest}}", digest_excerpt)
    else:
        user_content = user_content.replace(
            "{{prior_knowledge_digest}}",
            f"[Load from curriculum/LatinA/Week{week_number:02d}/Week_Spec/07_prior_knowledge_digest.json]"
        )

    # If role_context provided, serialize it (excerpt)
    if role_context:
        role_context_json = json.dumps(role_context, indent=2)
        if len(role_context_json) > 1500:
            role_context_excerpt = role_context_json[:1500] + "\n... (truncated)"
        else:
            role_context_excerpt = role_context_json
        user_content = user_content.replace("{{role_context}}", role_context_excerpt)
    else:
        user_content = user_content.replace(
            "{{role_context}}",
            f"[Load from curriculum/LatinA/Week{week_number:02d}/Day{day_number:02d}/04_role_context.json]"
        )

    # If guidelines provided, use excerpt (first 1000 chars)
    if guidelines:
        if len(guidelines) > 1000:
            guidelines_excerpt = guidelines[:1000] + "\n... (truncated)"
        else:
            guidelines_excerpt = guidelines
        user_content = user_content.replace("{{guidelines}}", guidelines_excerpt)
    else:
        user_content = user_content.replace(
            "{{guidelines}}",
            f"[Load from curriculum/LatinA/Week{week_number:02d}/Day{day_number:02d}/05_guidelines_for_sparky.md]"
        )

    system_content = prompt_spec["messages"][0]["content_template"]

    config = {
        "temperature": prompt_spec["model_preferences"]["temperature"],
        "max_tokens": prompt_spec["model_preferences"]["max_tokens"],
        "model": prompt_spec["model_preferences"]["model"]  # gpt-4o
    }

    return (system_content, user_content, config)


# ============================================================================
# GREETING PROMPT (Field 07) - Sparky's closing message
# ============================================================================

def task_greeting(
    week_number: int,
    day_number: int,
    class_name: str,
    week_spec: Optional[Dict[str, Any]] = None,
    role_context: Optional[Dict[str, Any]] = None,
    day_document: Optional[Dict[str, Any]] = None
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Generate 07_sparkys_greeting.txt - Cheerful closing message from Sparky.

    This prompt produces a short, warm, faith-grounded farewell message that
    reflects the week's virtue and faith phrase while reinforcing joy in
    learning Latin. The greeting is student-facing and ends each lesson on
    a positive, encouraging note.

    Output structure (JSON with text string):
    - greeting_text: string (40-300 chars)
      * Begins with cheerful tone ("Well done!", "Great work today!")
      * References virtue and/or faith phrase naturally
      * Optionally echoes chant rhythm or Latin vocabulary
      * Encourages curiosity for tomorrow's lesson
      * Ends with warm sign-off ("Valē!", "See you next time!")

    Tone features:
    - Warm, rhythmic, faithful, encouraging
    - Grade 3 appropriate language
    - Reflects Sparky's identity from role_context
    - Integrates virtue and faith without being preachy
    - Natural, conversational, uplifting

    Args:
        week_number: Week number (1-35)
        day_number: Day number (1-4)
        class_name: Class name from prompt_for_class_name
        week_spec: Optional week spec data (for virtue_focus, faith_phrase)
        role_context: Optional role context (for Sparky's identity)
        day_document: Optional day document (for lesson_steps summary)

    Returns:
        (system_prompt, user_prompt, config_dict)

    Output:
        JSON with single key: {"greeting_text": "...cheerful message..."}
    """
    prompt_spec = _load_prompt_json("day/greeting.json")

    # Build user prompt with interpolated values
    user_content = "\n".join(prompt_spec["messages"][1]["content_template"])
    user_content = user_content.replace("{{week_number}}", str(week_number))
    user_content = user_content.replace("{{day_number}}", str(day_number))
    user_content = user_content.replace("{{class_name}}", class_name)
    user_content = user_content.replace("{{grade_level}}", prompt_spec["inputs"]["grade_level"])

    # Extract virtue and faith phrase from week_spec
    if week_spec:
        virtue_focus = week_spec.get("virtue_focus", "diligence")
        faith_phrase = week_spec.get("faith_phrase", "Gloria Deo")
        user_content = user_content.replace("{{week_spec.virtue_focus}}", virtue_focus)
        user_content = user_content.replace("{{week_spec.faith_phrase}}", faith_phrase)
    else:
        user_content = user_content.replace("{{week_spec.virtue_focus}}", "[Load from week spec]")
        user_content = user_content.replace("{{week_spec.faith_phrase}}", "[Load from week spec]")

    # If role_context provided, serialize excerpt
    if role_context:
        # Extract just identity and constraints for brevity
        role_excerpt = {
            "identity": role_context.get("identity", "Sparky the Encourager"),
            "audience": role_context.get("audience", "Grade 3 (Grammar Stage, U.S.)"),
            "constraints": role_context.get("constraints", {})
        }
        role_context_json = json.dumps(role_excerpt, indent=2)
        user_content = user_content.replace("{{role_context}}", role_context_json)
    else:
        user_content = user_content.replace(
            "{{role_context}}",
            f"[Load from curriculum/LatinA/Week{week_number:02d}/Day{day_number:02d}/04_role_context.json]"
        )

    # If day_document provided, extract lesson_steps titles only for brevity
    if day_document:
        lesson_steps = day_document.get("lesson_steps", [])
        if lesson_steps:
            step_titles = [step.get("title", "") for step in lesson_steps]
            lesson_summary = "Lesson steps: " + ", ".join(step_titles)
        else:
            lesson_summary = "No lesson steps found"
        user_content = user_content.replace("{{day_document.lesson_steps}}", lesson_summary)
    else:
        user_content = user_content.replace(
            "{{day_document.lesson_steps}}",
            f"[Load from curriculum/LatinA/Week{week_number:02d}/Day{day_number:02d}/06_document_for_sparky.json]"
        )

    system_content = prompt_spec["messages"][0]["content_template"]

    config = {
        "temperature": prompt_spec["model_preferences"]["temperature"],
        "max_tokens": prompt_spec["model_preferences"]["max_tokens"],
        "model": prompt_spec["model_preferences"]["model"]  # gpt-4o
    }

    return (system_content, user_content, config)


# ============================================================================
# DAY REPAIR PROMPT - Minimal surgical fixes for broken fields
# ============================================================================

def task_day_repair(
    week_number: int,
    day_id: str,
    target_field: str,
    current_content: str,
    validation_report: Dict[str, Any],
    week_spec: Optional[Dict[str, Any]] = None,
    project_root: str = "curriculum/LatinA"
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Generate repair patch for a single day's broken field.

    This prompt produces minimal surgical fixes that satisfy schema, pedagogy,
    and references without creative rewrites. Returns unified-diff patch and
    optional full replacement artifact.

    Args:
        week_number: Week number (1-35)
        day_id: Day identifier (Day1, Day2, Day3, Day4)
        target_field: Field filename to repair
        current_content: Current file content
        validation_report: Validation findings
        week_spec: Optional week spec for alignment
        project_root: Root path for curriculum

    Returns:
        (system_prompt, user_prompt, config_dict)

    Output:
        JSON with patch, repaired_artifact, resolutions, status
    """
    prompt_spec = _load_prompt_json("repair/day_repair.json")

    user_content = "\n".join(prompt_spec["messages"][1]["content_template"])
    user_content = user_content.replace("{{project_root}}", project_root)
    user_content = user_content.replace("{{week_number}}", str(week_number))
    user_content = user_content.replace("{{day_id}}", day_id)
    user_content = user_content.replace("{{target_field}}", target_field)
    user_content = user_content.replace("{{current_content}}", current_content)

    validation_json = json.dumps(validation_report, indent=2)
    user_content = user_content.replace("{{validation_report}}", validation_json)

    if week_spec:
        week_spec_json = json.dumps(week_spec, indent=2)
        user_content = user_content.replace("{{week_spec}}", week_spec_json)
    else:
        user_content = user_content.replace("{{week_spec}}", "[Load from week spec]")

    system_content = prompt_spec["messages"][0]["content_template"]
    system_content = system_content.replace("{{target_field}}", target_field)

    config = {
        "temperature": prompt_spec["model_preferences"]["temperature"],
        "max_tokens": prompt_spec["model_preferences"]["max_tokens"],
        "model": prompt_spec["model_preferences"]["model"]
    }

    return (system_content, user_content, config)


# ============================================================================
# WEEK REFRESH PROMPT - Minimal regeneration after spec changes
# ============================================================================

def task_week_refresh(
    week_number: int,
    old_week_spec: Dict[str, Any],
    new_week_spec: Dict[str, Any],
    project_root: str = "curriculum/LatinA"
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Generate refresh plan for week after spec changes.

    This prompt computes deltas between old and new week specs and produces
    a minimal regeneration plan (keep/patch/regenerate) for each field in
    each of the 4 days.

    Args:
        week_number: Week number (1-35)
        old_week_spec: Compiled spec before change
        new_week_spec: Compiled spec after change
        project_root: Root path for curriculum

    Returns:
        (system_prompt, user_prompt, config_dict)

    Output:
        JSON with week, plan, artifacts, revalidation, cost_notes
    """
    prompt_spec = _load_prompt_json("refresh/week_refresh.json")

    user_content = "\n".join(prompt_spec["messages"][1]["content_template"])

    old_spec_json = json.dumps(old_week_spec, indent=2)
    new_spec_json = json.dumps(new_week_spec, indent=2)

    user_content = user_content.replace("{{old_week_spec}}", old_spec_json)
    user_content = user_content.replace("{{new_week_spec}}", new_spec_json)
    user_content = user_content.replace(
        "{{seven_fields}}",
        json.dumps(prompt_spec["inputs"]["seven_fields"])
    )

    system_content = prompt_spec["messages"][0]["content_template"]

    config = {
        "temperature": prompt_spec["model_preferences"]["temperature"],
        "max_tokens": prompt_spec["model_preferences"]["max_tokens"],
        "model": prompt_spec["model_preferences"]["model"]
    }

    return (system_content, user_content, config)


# ============================================================================
# LEGACY MIGRATION PROMPT - 6-field to 7-field upgrade
# ============================================================================

def task_legacy_migration(
    week_number: int,
    detected_layouts: Dict[str, Any],
    week_level_role_context: Optional[Dict[str, Any]] = None,
    project_root: str = "curriculum/LatinA"
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Generate migration plan for legacy 6-field to 7-field layout.

    This prompt produces mechanical upgrades: creates missing 04_role_context.json,
    adds YAML frontmatter to guidelines, preserves content and provenance.

    Args:
        week_number: Week number (1-35)
        detected_layouts: FS scan summary of present/missing files per day
        week_level_role_context: Optional week-level role context for synthesis
        project_root: Root path for curriculum

    Returns:
        (system_prompt, user_prompt, config_dict)

    Output:
        JSON with week, operations, artifacts, post_checks
    """
    prompt_spec = _load_prompt_json("migration/legacy_migration.json")

    user_content = "\n".join(prompt_spec["messages"][1]["content_template"])
    user_content = user_content.replace("{{week_number}}", str(week_number))

    layouts_json = json.dumps(detected_layouts, indent=2)
    user_content = user_content.replace("{{detected_layouts}}", layouts_json)

    if week_level_role_context:
        role_json = json.dumps(week_level_role_context, indent=2)
        user_content = user_content.replace("{{week_level_role_context}}", role_json)
    else:
        user_content = user_content.replace("{{week_level_role_context}}", "{}")

    system_content = prompt_spec["messages"][0]["content_template"]

    config = {
        "temperature": prompt_spec["model_preferences"]["temperature"],
        "max_tokens": prompt_spec["model_preferences"]["max_tokens"],
        "model": prompt_spec["model_preferences"]["model"]
    }

    return (system_content, user_content, config)


# ============================================================================
# ALIGNMENT CHECK PROMPT - Editorial QA for week bundle
# ============================================================================

def task_alignment_check(
    week_number: int,
    week_spec: Dict[str, Any],
    day_bundles: Dict[str, Dict[str, Any]],
    project_root: str = "curriculum/LatinA"
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Generate alignment QA report for week bundle.

    This prompt audits tone, age-level, virtue, and faith-phrase alignment
    across all 7 fields in Day1-Day4. Produces concise markdown report with
    actionable quick fixes.

    Args:
        week_number: Week number (1-35)
        week_spec: Week specification data
        day_bundles: Dict of Day1-Day4 with their 7 fields
        project_root: Root path for curriculum

    Returns:
        (system_prompt, user_prompt, config_dict)

    Output:
        Markdown report with summary, checklist, findings, next actions
    """
    prompt_spec = _load_prompt_json("qa/alignment_check.json")

    user_content = "\n".join(prompt_spec["messages"][1]["content_template"])
    user_content = user_content.replace("{{week_number}}", str(week_number))

    # Extract virtue and faith from week_spec
    virtue = week_spec.get("virtue_focus", week_spec.get("virtue", "N/A"))
    faith_phrase = week_spec.get("faith_phrase", "N/A")

    user_content = user_content.replace("{{week_spec.virtue}}", virtue)
    user_content = user_content.replace("{{week_spec.faith_phrase}}", faith_phrase)

    style_constraints = prompt_spec["inputs"]["style_constraints"]
    user_content = user_content.replace(
        "{{style_constraints.grade_level}}",
        style_constraints["grade_level"]
    )

    system_content = prompt_spec["messages"][0]["content_template"]

    config = {
        "temperature": prompt_spec["model_preferences"]["temperature"],
        "max_tokens": prompt_spec["model_preferences"]["max_tokens"],
        "model": prompt_spec["model_preferences"]["model"]
    }

    return (system_content, user_content, config)


# ============================================================================
# LEGACY ROLE_CONTEXT PROMPT (Field 04) - Week-level variant
# ============================================================================

def task_day_role_context(week_spec: dict, day: int) -> Tuple[str, str, Optional[Dict]]:
    """
    Generate prompts for day-specific role_context (field 04).

    PROMPT ENGINEERING PRINCIPLES APPLIED:
    - Positive instructions: "Include X" rather than "Don't omit X"
    - Schema skeleton embedded in prompt for anchoring
    - Self-check rubric at end of system prompt
    - Day-specific guidance (Day 1 vs Day 4 have different requirements)
    - Spiral learning references validated against week_spec
    - Output format strictly enforced (JSON only, no markdown)
    - Repair logic hint: prompt suggests fallback if spiral_links missing

    Args:
        week_spec: The week specification data
        day: Day number (1-4)

    Returns:
        (system_prompt, user_prompt, json_schema_hint)
    """
    # Load prompt from JSON library
    prompt_spec = _load_prompt_json("day/role_context.json")

    # Extract system and user prompts from JSON
    system_content = prompt_spec["messages"][0]["content_template"]
    user_template = "\n".join(prompt_spec["messages"][1]["content_template"])

    # Extract metadata for interpolation (using prefixed key from compiled week spec)
    metadata = week_spec.get("01_metadata.json", {})
    week_number = metadata.get("week", metadata.get("week_number", 1))

    # Build user prompt with interpolations (simplified version - we don't have all dependencies yet)
    user_content = user_template.replace("{{project_name}}", "Latin A (Grammar Stage)")
    user_content = user_content.replace("{{week_number}}", str(week_number))
    user_content = user_content.replace("{{day_number}}", str(day))
    user_content = user_content.replace("{{grade_level_fixed}}", "Grade 3 (Grammar Stage, U.S.)")
    user_content = user_content.replace("{{class_name}}", f"Week {week_number} Day {day}")

    # Serialize week_spec for context
    week_spec_json = json.dumps(week_spec, indent=2)
    user_content = user_content.replace("{{week_spec}}", week_spec_json)

    # Placeholders for missing dependencies (will be empty for now)
    user_content = user_content.replace("{{prior_knowledge_digest}}", "{}")
    user_content = user_content.replace("{{day_summary}}", "")

    # Extract JSON schema from output_contract
    schema = prompt_spec["output_contract"]["schema"]

    return (system_content, user_content, schema)


def _get_day_focus(day: int) -> str:
    """Get pedagogical focus label for day number."""
    focuses = {
        1: "introduction_and_exploration",
        2: "practice_and_reinforcement",
        3: "application_and_extension",
        4: "review_and_spiral_25pct"
    }
    return focuses.get(day, "general")


# ============================================================================
# GUIDELINES PROMPT (Field 05) - Markdown teaching notes
# Depends on: role_context (field 04)
# ============================================================================

def task_day_guidelines(
    week_spec: dict,
    day: int,
    role_context: Optional[Dict[str, Any]] = None
) -> Tuple[str, str, Optional[Dict]]:
    """
    Generate prompts for day guidelines (field 05_guidelines_for_sparky.md).

    PROMPT ENGINEERING PRINCIPLES:
    - Consumes role_context from field 04 (if available, else uses fallback)
    - Positive framing: "Include these sections" not "Don't forget"
    - Markdown structure template embedded in prompt
    - YAML references header validation (points to prior_knowledge, vocabulary)
    - Self-check rubric for completeness
    - Repair logic: if role_context missing, prompt generates minimal default

    Args:
        week_spec: Week specification data
        day: Day number (1-4)
        role_context: Optional role_context dict from field 04

    Returns:
        (system_prompt, user_prompt, None) - No JSON schema (output is markdown)
    """
    # Load prompt from JSON library
    prompt_spec = _load_prompt_json("day/guidelines.json")

    # Extract system and user prompts from JSON
    system_content = prompt_spec["messages"][0]["content_template"]
    user_template = "\n".join(prompt_spec["messages"][1]["content_template"])

    # Handle missing role_context (fallback)
    if not role_context:
        role_context = {
            "sparky_role": "encouraging Latin guide",
            "focus_mode": _get_day_focus(day),
            "hints_enabled": True,
            "spiral_emphasis": [],
            "encouragement_triggers": ["first_attempt"],
            "max_hints": 3,
            "wait_time_seconds": 5
        }

    # Extract metadata for interpolation (using prefixed key from compiled week spec)
    metadata = week_spec.get("01_metadata.json", {})
    week_number = metadata.get("week", metadata.get("week_number", 1))

    # Build user prompt with interpolations
    user_content = user_template.replace("{{project_name}}", "Latin A (Grammar Stage)")
    user_content = user_content.replace("{{week_number}}", str(week_number))
    user_content = user_content.replace("{{day_number}}", str(day))
    user_content = user_content.replace("{{grade_level_fixed}}", "Grade 3 (Grammar Stage, U.S.)")
    user_content = user_content.replace("{{class_name}}", f"Week {week_number} Day {day}")

    # Serialize week_spec and role_context for context
    week_spec_json = json.dumps(week_spec, indent=2)
    user_content = user_content.replace("{{week_spec}}", week_spec_json)

    role_context_json = json.dumps(role_context, indent=2)
    user_content = user_content.replace("{{role_context}}", role_context_json)

    # Placeholders for missing dependencies
    user_content = user_content.replace("{{prior_knowledge_digest}}", "{}")
    user_content = user_content.replace("{{day_summary}}", "")
    user_content = user_content.replace("{{week_summary}}", "")

    return (system_content, user_content, None)  # No JSON schema (markdown output)


# ============================================================================
# DAY FIELDS PROMPT (Fields 01-03) - Metadata fields only
# ============================================================================

def task_day_fields(week_spec: dict, day: int) -> Tuple[str, str, Optional[Dict]]:
    """
    Generate prompts for day metadata fields (class_name, summary, grade_level).

    UPDATED FOR 7-FIELD ARCHITECTURE:
    - This function now generates ONLY fields 01-03
    - Field 04 (role_context) generated by task_day_role_context()
    - Field 05 (guidelines) generated by task_day_guidelines()
    - Field 06 (document) generated by task_day_document()
    - Field 07 (greeting) generated by task_day_greeting()

    Args:
        week_spec: The week specification data
        day: Day number (1-4)

    Returns:
        (system_prompt, user_prompt, json_schema_hint)
    """
    # Extract week data using helper function (supports v1.0, v1.1, and custom formats)
    week_data = _extract_from_week_spec(week_spec)
    week_number = week_data["week_number"]
    week_title = week_data["week_title"]
    grammar_focus = week_data["grammar_focus"]

    # Map day number to pedagogical intent (gold standard pattern)
    day_intents = {
        1: "Discovery",  # or "Learn"
        2: "Practice",
        3: "Review",
        4: "Quiz"
    }
    day_intent = day_intents.get(day, "Learn")

    sys = (
        "Generate the THREE metadata fields for a single day lesson in a CLASSICAL LATIN curriculum:\n"
        "1. class_name - engaging, narrative lesson title\n"
        "2. summary - narrative 3-5 sentence overview with italicized Latin terms\n"
        "3. grade_level - target grade range\n"
        "\n"
        "FIELD NUMBERING (7-field architecture):\n"
        "- These are fields 01, 02, 03\n"
        "- Field 04 (role_context) is generated separately\n"
        "- Field 05 (guidelines), 06 (document), 07 (greeting) are generated separately\n\n"
        "CRITICAL - LATIN CURRICULUM REQUIREMENTS:\n"
        "- This is a CLASSICAL LATIN curriculum (declensions, conjugations, cases)\n"
        "- class_name must describe LATIN content only (grammar, vocabulary, pronunciation)\n"
        "- summary must be about LATIN learning - NOT math, science, or other subjects\n"
        "- Topic should reference Latin grammar concepts, vocabulary themes, or language skills\n"
        "- DO NOT use topics like 'ecosystems', 'fractions', 'biology', 'math', etc.\n\n"
        f"WEEK NUMBER VALIDATION:\n"
        f"- You are generating content for WEEK {week_number} DAY {day}\n"
        f"- class_name MUST start with exactly: 'Latin A – Week {week_number:02d} Day {day} :'\n"
        f"- DO NOT use any other week number - this is Week {week_number}\n\n"
        "CLASS NAME STYLE (GOLD STANDARD PATTERN):\n"
        "- Format: 'Latin A – Week NN Day N : Engaging Subtitle – Pedagogical Intent'\n"
        "- Use en-dash (–) not hyphen (-)\n"
        "- Engaging subtitle should be narrative and exciting (not 'Introduction to...')\n"
        "- Examples from gold standard:\n"
        "  * 'Latin A – Week 11 Day 1 : Discovery – Meet the –āre Family'\n"
        "  * 'Latin A – Week 05 Day 2 : Practice – Building with –us Nouns'\n"
        "  * 'Latin A – Week 03 Day 3 : Review – Mastering First Declension'\n\n"
        "SUMMARY STYLE (GOLD STANDARD PATTERN):\n"
        "- Write in narrative present tense (\"Sparky begins...\", \"Students now meet...\")\n"
        "- Italicize ALL Latin words using *asterisks* (e.g., *puella*, *sum, esse*)\n"
        "- Connect to prior knowledge and preview future lessons\n"
        "- Include virtue and faith phrase\n"
        "- 3-5 sentences, flowing narrative (not bullet points)\n"
        "- Example: 'Sparky begins Week 2 by recalling *salve* from last week. Students now meet the **First Declension (–a)** nouns and chant endings showing case patterns. Familiar words such as *puella*, *rosa*, and *aqua* appear, building vocabulary foundations. The virtue **Patientia – Patience** reminds us to practice carefully. Tomorrow they'll strengthen accuracy and explore more noun forms.'\n\n"
        "LATIN CONTENT REASONING:\n"
        "- Read the week title and grammar_focus to identify the Latin topic\n"
        "- Generate class_name subtitle that matches Classical Latin pedagogy\n"
        "- CORRECT patterns: declensions, conjugations, cases, Latin vocabulary\n"
        "- FORBIDDEN patterns: modern languages, daily routines, non-Latin subjects\n\n"
        "INSTRUCTIONS:\n"
        f"- class_name: Format 'Latin A – Week {week_number:02d} Day {day} : [Engaging Subtitle] – {day_intent}' (≤100 chars)\n"
        "- summary: Narrative 3-5 sentences with *italicized* Latin terms, connecting prior/future (150-300 chars)\n"
        "- grade_level: Format as 'N-M' where N and M are grade numbers (e.g., '3-5', '6-8')\n\n"
        "OUTPUT FORMAT:\n"
        "Return as JSON object with these keys.\n"
        "{\n"
        f"  \"class_name\": \"Latin A – Week {week_number:02d} Day {day} : [Engaging Subtitle] – {day_intent}\",\n"
        "  \"summary\": \"Narrative paragraph with *italicized* Latin terms connecting prior knowledge and future lessons.\",\n"
        "  \"grade_level\": \"3-5\"\n"
        "}\n\n"
        "SELF-CHECK:\n"
        f"✓ Does class_name start with EXACTLY 'Latin A – Week {week_number:02d} Day {day} :'?\n"
        "✓ Does subtitle use en-dash (–) before day intent (Discovery/Practice/Review/Quiz)?\n"
        "✓ Is subtitle engaging and narrative (not 'Introduction to...')?\n"
        "✓ Does summary use *asterisks* for ALL Latin words?\n"
        "✓ Is summary narrative present tense (3-5 sentences)?\n"
        "✓ Does summary connect prior knowledge and preview tomorrow?\n"
        "✓ Is grade_level in 'N-M' format (e.g., '3-5')?\n"
    )

    # Use helper to extract data
    week_data = _extract_from_week_spec(week_spec)

    usr = (
        f"Week metadata and objectives for Day {day}:\n\n"
        f"CRITICAL: This week is about '{week_data['grammar_focus']}'. ALL 4 days must focus on this same grammar topic.\n"
        f"Do NOT introduce new topics (verbs, other declensions, etc.). Stay on '{week_data['grammar_focus']}'.\n\n"
        + orjson.dumps(
            {
                "metadata": week_data["metadata"],
                "objectives": week_data["objectives"],
                "grammar_focus": week_data["grammar_focus"],
                "week_number": week_data["week_number"],
                "day": day
            },
            option=orjson.OPT_INDENT_2
        ).decode()
    )

    return sys, usr, None


# ============================================================================
# DOCUMENT PROMPT (Field 06) - Complete lesson plan JSON
# Depends on: role_context (04), guidelines (05)
# ============================================================================

def task_day_document(week_spec: dict, day: int, research_plan: Optional[Dict[str, Any]] = None) -> Tuple[str, str, Optional[Dict]]:
    """
    Generate prompts for day document_for_sparky (field 06 - 6 teacher support documents).

    UPDATED FOR v1.1 ARCHITECTURE + PHASE 0 INTEGRATION:
    - Field 06 is now a DIRECTORY with 6 .txt files (not a single JSON)
    - Returns 6 plain-text documents for teacher support
    - Each document serves a specific instructional purpose
    - NOW receives PHASE 0 research findings with verified Latin vocabulary

    Args:
        week_spec: The week specification data from internal_documents/
        day: Day number (1-4)
        research_plan: Optional PHASE 0 research findings with verified vocabulary

    Returns:
        (system_prompt, user_prompt, json_schema_hint)
    """
    sys = """You are Steel, the curriculum architect for TEQUILA CLASSICAL LATIN A.

Generate 6 teacher support documents for field 06_document_for_sparky/.
Each document is PLAIN TEXT (not JSON) and serves a specific instructional purpose.

CRITICAL - CLASSICAL LATIN CURRICULUM ONLY:
1. This is CLASSICAL LATIN instruction (declensions, conjugations, cases).
2. ALL vocabulary MUST be Classical Latin words ONLY.
   ✅ CORRECT: salve, puella, amo, pax, Deus, aqua, terra, sum, es, est
   ❌ FORBIDDEN: levantarse, ducharse, vestirse, cepillarse (Spanish reflexive verbs)
   ❌ FORBIDDEN: ANY Spanish, French, Italian, or modern Romance language words
   ❌ FORBIDDEN: ANY words ending in -arse, -erse, -irse (Spanish infinitives)
3. ALL grammar topics MUST be Classical Latin.
   ✅ CORRECT: declensions, conjugations, cases, Latin verb forms
   ❌ FORBIDDEN: reflexive verbs, articles (el/la/le), modern verb tenses
4. ALL chants MUST be Latin paradigms (e.g., 'a/ae/ae/am/ā', 'us/ī/ō/um/ō').
5. ALL example sentences MUST be Classical Latin (e.g., 'Puella est bona', 'Sum discipulus').

REASONING CHECK before generating vocabulary_key_document:
- Is EVERY word in this list Classical Latin? (YES: puella, amo | NO: levantarse, ducharse)
- Does the vocabulary match the week's Latin grammar topic? (YES: Latin nouns for declension week | NO: daily routines)
- Are there ANY Spanish/modern words? If YES, STOP and replace with Latin.

Focus on clarity, specificity, and pedagogical value for classroom teachers teaching CLASSICAL LATIN."""

    # Use helper to extract data (supports v1.0, v1.1, custom formats)
    week_data = _extract_from_week_spec(week_spec)

    usr = f"""Generate 6 teacher support documents for Week {week_data['week_number']} Day {day}.

## Week Context
Grammar Focus: {week_data['grammar_focus']}
Vocabulary: {[v.get('word', v) if isinstance(v, dict) else v for v in week_data['vocabulary'][:7]]}
Virtue: {week_data['virtue_focus']}
Faith Phrase: {week_data['faith_phrase']}"""

    # INJECT PHASE 0 RESEARCH if available
    if research_plan:
        vocab_plan = research_plan.get("04_vocabulary_plan", {})
        if vocab_plan:
            new_words = [w.get('word', '') for w in vocab_plan.get('new_latin_words', [])]
            recycled_words = [w.get('word', '') for w in vocab_plan.get('recycled_latin_words', [])]

            usr += f"""

## PHASE 0 RESEARCH - VERIFIED LATIN VOCABULARY

The following vocabulary was researched and verified as Classical Latin by a reasoning model.
**YOU MUST USE THESE WORDS EXACTLY** in the vocabulary_key_document:

NEW LATIN WORDS (verified Classical Latin):
{', '.join(new_words)}

RECYCLED WORDS (spiral review):
{', '.join(recycled_words)}

CRITICAL: Do NOT generate different vocabulary. Use the researched words above.
These words were specifically chosen to match the grammar topic and verified as Classical Latin."""

    usr += """

## CRITICAL REQUIREMENTS - READ BEFORE GENERATING
This is a CLASSICAL LATIN curriculum. You MUST:
1. Use ONLY Classical Latin vocabulary (puella, amo, salve, pax, Deus, aqua, terra, sum, es, est).
2. NEVER use Spanish words (levantarse, ducharse, vestirse, cepillarse).
3. NEVER use words ending in -arse, -erse, -irse (these are Spanish infinitives, NOT Latin).
4. NEVER use reflexive verbs, articles (el/la), or modern Romance language words.
5. Use ONLY Latin grammar topics (declensions, conjugations, cases, Latin verb forms).
6. ALL vocabulary in vocabulary_key_document MUST be Classical Latin words.
7. ALL chants in chant_chart_document MUST be Latin paradigms.
8. Read the Grammar Focus to determine appropriate LATIN vocabulary for this week.

## Task
Return a JSON object with these 6 keys (each value is plain text, NOT nested JSON):

1. **spiral_review_document**: List specific LATIN content from prior weeks to review today (Latin words, Latin grammar)
2. **weekly_topics_document**: Week overview (LATIN grammar, LATIN skill goals, virtue, mastery indicator)
3. **virtue_and_faith_document**: How virtue connects to lesson; faith phrase meaning; scripture reference
4. **vocabulary_key_document**: Today's CLASSICAL LATIN vocabulary with pronunciation, English meaning, AND English derivatives
   - REQUIRED FORMAT (GOLD STANDARD): "amō – I love (amiable, amorous)"
   - REQUIRED: Every word MUST be Classical Latin (e.g., salve, puella, amo, pax)
   - REQUIRED: Include 2-4 English derivatives in parentheses (e.g., portable, transport)
   - FORBIDDEN: Spanish (levantarse, ducharse), reflexive verbs, modern languages
   - Use week's grammar_focus to determine appropriate Latin vocabulary
   - Example format:
     ```
     VOCABULARY KEY – Week NN Core [Topic]

     amō – I love (amiable, amorous)
     portō – I carry (portable, transport)
     laudō – I praise (laudatory, applaud)
     vocō – I call (vocal, vocation, advocate)
     ```
5. **chant_chart_document**: Latin paradigm memory chant with rhythm/motions (e.g., 'a/ae/ae/am/ā', 'sum/es/est')
6. **teacher_voice_tips_document**: Pedagogical coaching for delivering this LATIN lesson

## Output Format
Return ONLY valid JSON with this structure:
{{
  "spiral_review_document": "...",
  "weekly_topics_document": "...",
  "virtue_and_faith_document": "...",
  "vocabulary_key_document": "...",
  "chant_chart_document": "...",
  "teacher_voice_tips_document": "..."
}}

Each value should be a plain text string (use \\n for line breaks).

FINAL CHECK before returning:
✓ Does vocabulary_key_document contain ONLY Classical Latin words?
✓ Are there ZERO Spanish words (levantarse, ducharse, etc.)?
✓ Does chant_chart_document use Latin paradigms?
✓ Do all documents reference LATIN grammar and vocabulary?
"""

    # Simple schema to ensure 6 required keys are present
    schema = {
        "type": "object",
        "properties": {
            "spiral_review_document": {"type": "string"},
            "weekly_topics_document": {"type": "string"},
            "virtue_and_faith_document": {"type": "string"},
            "vocabulary_key_document": {"type": "string"},
            "chant_chart_document": {"type": "string"},
            "teacher_voice_tips_document": {"type": "string"}
        },
        "required": [
            "spiral_review_document",
            "weekly_topics_document",
            "virtue_and_faith_document",
            "vocabulary_key_document",
            "chant_chart_document",
            "teacher_voice_tips_document"
        ],
        "additionalProperties": False
    }

    return sys, usr, schema


# ============================================================================
# GREETING PROMPT (Field 07) - Student-facing welcome message
# Depends on: role_context (04), document (06)
# ============================================================================

def task_day_greeting(
    week_spec: dict,
    day: int,
    role_context: Optional[Dict[str, Any]] = None,
    document: Optional[Dict[str, Any]] = None
) -> Tuple[str, str, Optional[Dict]]:
    """
    Generate prompts for day greeting (field 07_sparkys_greeting.txt).

    PROMPT ENGINEERING PRINCIPLES:
    - Consumes role_context (field 04) for persona and tone
    - Optionally consumes document (field 06) for lesson topic reference
    - Positive framing: "Make greeting warm and specific"
    - Length constraint: 1-2 sentences, ≤200 chars

    Args:
        week_spec: Week specification data
        day: Day number (1-4)
        role_context: Optional role_context dict from field 04
        document: Optional document dict from field 06

    Returns:
        (system_prompt, user_prompt, None) - No JSON schema (output is plain text)
    """
    # Load prompt from JSON library
    prompt_spec = _load_prompt_json("day/greeting.json")

    # Extract system and user prompts from JSON
    system_content = prompt_spec["messages"][0]["content_template"]
    user_template = "\n".join(prompt_spec["messages"][1]["content_template"])

    # Handle missing role_context (fallback)
    if not role_context:
        role_context = {
            "sparky_role": "encouraging Latin guide",
            "focus_mode": _get_day_focus(day),
            "encouragement_triggers": ["first_attempt"]
        }

    # Extract metadata for interpolation (using prefixed key from compiled week spec)
    metadata = week_spec.get("01_metadata.json", {})
    week_number = metadata.get("week", metadata.get("week_number", 1))

    # Build user prompt with interpolations
    user_content = user_template.replace("{{week_number}}", str(week_number))
    user_content = user_content.replace("{{day_number}}", str(day))
    user_content = user_content.replace("{{class_name}}", f"Week {week_number} Day {day}")
    user_content = user_content.replace("{{grade_level}}", "Grade 3 (Grammar Stage, U.S.)")

    # Replace week_spec attributes
    user_content = user_content.replace("{{week_spec.virtue_focus}}", metadata.get("virtue_focus", ""))
    user_content = user_content.replace("{{week_spec.faith_phrase}}", metadata.get("faith_phrase", ""))

    # Serialize role_context and document for context
    role_context_json = json.dumps(role_context, indent=2)
    user_content = user_content.replace("{{role_context}}", role_context_json)

    if document:
        lesson_steps = document.get("lesson_flow", document.get("lesson_steps", ""))
        if isinstance(lesson_steps, dict):
            lesson_steps = json.dumps(lesson_steps)
        elif isinstance(lesson_steps, list):
            lesson_steps = "\n".join(f"- {step}" for step in lesson_steps)
        user_content = user_content.replace("{{day_document.lesson_steps}}", str(lesson_steps))
    else:
        user_content = user_content.replace("{{day_document.lesson_steps}}", "")

    # Extract JSON schema from output_contract (greeting returns JSON with greeting_text key)
    schema = prompt_spec["output_contract"]["schema"]

    return (system_content, user_content, schema)


# ============================================================================
# SCHEMA SELFCHECK PROMPT - Lightweight JSON self-validation
# ============================================================================

def task_schema_selfcheck(
    week_number: int,
    day_id: str,
    field_name: str,
    field_content: str,
    expected_schema: Dict[str, Any],
    project_root: str = "curriculum/LatinA"
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Generate schema self-validation report for a single field.

    This prompt performs lightweight, deterministic JSON/YAML validation:
    - Parses syntax
    - Checks required keys
    - Returns structured error/warning report

    Args:
        week_number: Week number (1-35)
        day_id: Day identifier (Day1, Day2, Day3, Day4)
        field_name: Field filename to validate
        field_content: Raw file content
        expected_schema: JSON Schema Draft-07 or YAML frontmatter spec
        project_root: Root path for curriculum

    Returns:
        (system_prompt, user_prompt, config_dict)

    Output:
        JSON with subject, summary, errors, warnings, status
    """
    prompt_spec = _load_prompt_json("validation/schema_selfcheck.json")

    user_content = "\n".join(prompt_spec["messages"][1]["content_template"])
    user_content = user_content.replace("{{project_root}}", project_root)
    user_content = user_content.replace("{{week_number}}", str(week_number))
    user_content = user_content.replace("{{day_id}}", day_id)
    user_content = user_content.replace("{{field_name}}", field_name)
    user_content = user_content.replace("{{field_content}}", field_content)

    schema_json = json.dumps(expected_schema, indent=2)
    user_content = user_content.replace("{{expected_schema}}", schema_json)

    system_content = prompt_spec["messages"][0]["content_template"]

    config = {
        "temperature": prompt_spec["model_preferences"]["temperature"],
        "max_tokens": prompt_spec["model_preferences"]["max_tokens"],
        "model": prompt_spec["model_preferences"]["model"]
    }

    return (system_content, user_content, config)


# ============================================================================
# PEDAGOGICAL SELFCHECK PROMPT - Pedagogy-focused QA for week bundle
# ============================================================================

def task_pedagogical_selfcheck(
    week_number: int,
    week_spec: Dict[str, Any],
    day_bundles: Dict[str, Dict[str, Any]],
    project_root: str = "curriculum/LatinA"
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Generate pedagogical QA report for week bundle.

    This prompt checks:
    - Spiral coverage (25-40%)
    - CFU usage (≥2 per day)
    - Pacing (20-25 min)
    - Differentiation strategies
    - Misconception handling
    - Age-appropriateness

    Args:
        week_number: Week number (1-35)
        week_spec: Week specification data
        day_bundles: Dict of Day1-Day4 with role_context, guidelines, document
        project_root: Root path for curriculum

    Returns:
        (system_prompt, user_prompt, config_dict)

    Output:
        Markdown report with rule results, day-by-day checklist
    """
    prompt_spec = _load_prompt_json("validation/pedagogical_selfcheck.json")

    user_content = "\n".join(prompt_spec["messages"][1]["content_template"])
    user_content = user_content.replace("{{week_number}}", str(week_number))
    user_content = user_content.replace("{{project_root}}", project_root)

    week_spec_json = json.dumps(week_spec, indent=2)
    user_content = user_content.replace("{{week_spec}}", week_spec_json)

    pedagogical_rules = prompt_spec["inputs"]["pedagogical_rules"]
    rules_json = json.dumps(pedagogical_rules, indent=2)
    user_content = user_content.replace("{{pedagogical_rules}}", rules_json)

    system_content = prompt_spec["messages"][0]["content_template"]

    config = {
        "temperature": prompt_spec["model_preferences"]["temperature"],
        "max_tokens": prompt_spec["model_preferences"]["max_tokens"],
        "model": prompt_spec["model_preferences"]["model"]
    }

    return (system_content, user_content, config)


# ============================================================================
# SPIRAL ENFORCEMENT PROMPT - Ensure 25-40% spiral coverage
# ============================================================================

def task_spiral_enforcement(
    week_number: int,
    day_id: str,
    day_document: Dict[str, Any],
    prior_knowledge_digest: Dict[str, Any],
    project_root: str = "curriculum/LatinA"
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Generate spiral enforcement report with patches.

    This prompt analyzes spiral coverage in 06_document_for_sparky.json:
    - Measures spiral % (spiral_items / total_items)
    - If out of bounds (25-40%), proposes minimal patches
    - Returns corrected document or RFC 6902 patch

    Args:
        week_number: Week number (1-35)
        day_id: Day identifier (Day1, Day2, Day3, Day4)
        day_document: DayDocument from prompt_for_day_document
        prior_knowledge_digest: Available spiral content
        project_root: Root path for curriculum

    Returns:
        (system_prompt, user_prompt, config_dict)

    Output:
        JSON with spiral_metrics, changes, patch_json, corrected_document
    """
    prompt_spec = _load_prompt_json("enforcement/spiral_enforcement.json")

    user_content = "\n".join(prompt_spec["messages"][1]["content_template"])
    user_content = user_content.replace("{{project_root}}", project_root)
    user_content = user_content.replace("{{week_number}}", str(week_number))
    user_content = user_content.replace("{{day_id}}", day_id)

    day_doc_json = json.dumps(day_document, indent=2)
    user_content = user_content.replace("{{day_document}}", day_doc_json)

    digest_json = json.dumps(prior_knowledge_digest, indent=2)
    user_content = user_content.replace("{{prior_knowledge_digest}}", digest_json)

    spiral_policy = prompt_spec["inputs"]["spiral_policy"]
    policy_json = json.dumps(spiral_policy, indent=2)
    user_content = user_content.replace("{{spiral_policy}}", policy_json)

    system_content = prompt_spec["messages"][0]["content_template"]

    config = {
        "temperature": prompt_spec["model_preferences"]["temperature"],
        "max_tokens": prompt_spec["model_preferences"]["max_tokens"],
        "model": prompt_spec["model_preferences"]["model"]
    }

    return (system_content, user_content, config)


# ============================================================================
# VIRTUE ALIGNMENT PROMPT - Audit virtue/faith integration
# ============================================================================

def task_virtue_alignment(
    week_number: int,
    day_id: str,
    week_spec: Dict[str, Any],
    day_bundle: Dict[str, Any],
    project_root: str = "curriculum/LatinA"
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Generate virtue/faith alignment audit for a single day.

    This prompt audits all 7 fields for:
    - Virtue mentions (≥2, meaningful integration)
    - Faith phrase usage (≥1, natural context)
    - Proposes line-anchored patches for weak/missing integrations

    Args:
        week_number: Week number (1-35)
        day_id: Day identifier (Day1, Day2, Day3, Day4)
        week_spec: Week specification (for virtue_focus, faith_phrase)
        day_bundle: Dict with all 7 field contents
        project_root: Root path for curriculum

    Returns:
        (system_prompt, user_prompt, config_dict)

    Output:
        Markdown report + JSON metadata with alignment summary and patches
    """
    prompt_spec = _load_prompt_json("validation/virtue_alignment.json")

    user_content = "\n".join(prompt_spec["messages"][1]["content_template"])
    user_content = user_content.replace("{{project_root}}", project_root)
    user_content = user_content.replace("{{week_number}}", str(week_number))
    user_content = user_content.replace("{{day_id}}", day_id)

    # Extract virtue and faith from week_spec
    virtue = week_spec.get("virtue_focus", week_spec.get("virtue", "N/A"))
    faith_phrase = week_spec.get("faith_phrase", "N/A")
    user_content = user_content.replace("{{week_spec.virtue}}", virtue)
    user_content = user_content.replace("{{week_spec.faith_phrase}}", faith_phrase)

    day_bundle_json = json.dumps(day_bundle, indent=2)
    user_content = user_content.replace("{{day_bundle}}", day_bundle_json)

    alignment_rules = prompt_spec["inputs"]["alignment_rules"]
    rules_json = json.dumps(alignment_rules, indent=2)
    user_content = user_content.replace("{{alignment_rules}}", rules_json)

    system_content = prompt_spec["messages"][0]["content_template"]

    config = {
        "temperature": prompt_spec["model_preferences"]["temperature"],
        "max_tokens": prompt_spec["model_preferences"]["max_tokens"],
        "model": prompt_spec["model_preferences"]["model"]
    }

    return (system_content, user_content, config)


# ============================================================================
# CHAIN CONTEXT BUILDER PROMPT - Assemble compact context bundles
# ============================================================================

def task_chain_context_builder(
    week_number: int,
    day_number: int,
    token_budget: int = 6000,
    include_assets: bool = False,
    project_root: str = "curriculum/LatinA"
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Generate compact context bundle for generation runs.

    This prompt assembles a lossless, token-budgeted context object that includes:
    - Project info (root, week, day)
    - Week spec (condensed)
    - Prior knowledge digest (week-1)
    - Manifest slice for the week
    - Virtue/faith for the week
    - Any existing day-level files

    Intelligently prunes content to fit token budget while preserving semantic nuclei.

    Args:
        week_number: Week number (1-35)
        day_number: Day number (1-4)
        token_budget: Maximum tokens for context bundle (default: 6000)
        include_assets: Whether to include asset files (default: False)
        project_root: Root path for curriculum

    Returns:
        (system_prompt, user_prompt, config_dict)

    Output:
        JSON with project_info, week_spec, prior_knowledge, manifest, day_files, provenance, size
    """
    prompt_spec = _load_prompt_json("meta/chain_context_builder.json")

    user_content = "\n".join(prompt_spec["messages"][1]["content_template"])
    user_content = user_content.replace("{{project_root}}", project_root)
    user_content = user_content.replace("{{week_number}}", str(week_number))
    user_content = user_content.replace("{{day_number}}", str(day_number))
    user_content = user_content.replace("{{token_budget}}", str(token_budget))
    user_content = user_content.replace("{{include_assets}}", str(include_assets).lower())

    system_content = prompt_spec["messages"][0]["content_template"]

    config = {
        "temperature": prompt_spec["model_preferences"]["temperature"],
        "max_tokens": prompt_spec["model_preferences"]["max_tokens"],
        "model": prompt_spec["model_preferences"]["model"]
    }

    return (system_content, user_content, config)


# ============================================================================
# LLM REPAIR CYCLE PROMPT - Automated validate→patch→revalidate loop
# ============================================================================

def task_llm_repair_cycle(
    validation_report: Dict[str, Any],
    max_iterations: int = 3,
    risk_mode: str = "conservative"
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Generate automated repair cycle plan from validation findings.

    This prompt produces a queue of atomic patches (rename/create/json-patch)
    that address validation failures mechanically, without creative rewrites.
    Continues until gate is ok/warn or max_iterations exhausted.

    Args:
        validation_report: Validation findings from prompt_for_schema_validation
        max_iterations: Maximum repair iterations (default: 3)
        risk_mode: Risk tolerance - 'conservative', 'moderate', or 'aggressive'

    Returns:
        (system_prompt, user_prompt, config_dict)

    Output:
        JSON with plan, ordered_patches, risk_notes, expected_outcome
    """
    prompt_spec = _load_prompt_json("meta/llm_repair_cycle.json")

    user_content = "\n".join(prompt_spec["messages"][1]["content_template"])

    # Validation report is embedded in the prompt
    validation_json = json.dumps(validation_report, indent=2)
    user_content = f"## Validation Report\n```json\n{validation_json}\n```\n\n" + user_content

    system_content = prompt_spec["messages"][0]["content_template"]

    config = {
        "temperature": prompt_spec["model_preferences"]["temperature"],
        "max_tokens": prompt_spec["model_preferences"]["max_tokens"],
        "model": prompt_spec["model_preferences"]["model"]
    }

    return (system_content, user_content, config)


# ============================================================================
# COST EXPLANATION PROMPT - Analyze and report LLM generation costs
# ============================================================================

def task_cost_explanation(
    generation_logs: list,
    time_window: str = "all",
    grouping: str = "by_week",
    project_root: str = "curriculum/LatinA"
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Generate cost analysis report from generation logs.

    This prompt analyzes LLM generation costs and produces a human-readable
    breakdown by provider, model, operation type, and week/day. Includes
    optimization suggestions to help educators manage token budgets.

    Args:
        generation_logs: Array of generation run records with tokens, model, cost
        time_window: Time filter - 'last_week', 'last_month', or 'all' (default: 'all')
        grouping: Grouping dimension - 'by_week', 'by_day', 'by_model', or 'by_operation'
        project_root: Root path for curriculum

    Returns:
        (system_prompt, user_prompt, config_dict)

    Output:
        Markdown report with executive summary, cost breakdown, top operations, optimizations, JSON metadata
    """
    prompt_spec = _load_prompt_json("meta/cost_explanation.json")

    user_content = "\n".join(prompt_spec["messages"][1]["content_template"])

    # Serialize generation logs
    logs_json = json.dumps(generation_logs, indent=2)
    user_content = user_content.replace("{{generation_logs}}", logs_json)
    user_content = user_content.replace("{{time_window}}", time_window)
    user_content = user_content.replace("{{grouping}}", grouping)

    system_content = prompt_spec["messages"][0]["content_template"]

    config = {
        "temperature": prompt_spec["model_preferences"]["temperature"],
        "max_tokens": prompt_spec["model_preferences"]["max_tokens"],
        "model": prompt_spec["model_preferences"]["model"]
    }

    return (system_content, user_content, config)


# ============================================================================
# QUIZ PACKET PROMPT - Generate weekly quiz for Day 4
# ============================================================================

def task_quiz_packet(
    week_number: int,
    week_spec: Dict[str, Any],
    day4_document: Dict[str, Any],
    guidelines: Optional[str] = None,
    project_root: str = "curriculum/LatinA"
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Generate weekly quiz packet for Day 4 assessment.

    This prompt creates a balanced quiz covering:
    - Vocabulary (5 pts)
    - Grammar & Chant (5 pts)
    - Translation (5 pts)
    - Virtue Reflection (5 pts)

    Outputs both Markdown quiz and minimal JSON answer key.

    Args:
        week_number: Week number (1-35)
        week_spec: Week specification data
        day4_document: Day 4 document from prompt_for_day_document
        guidelines: Optional Day 4 guidelines markdown
        project_root: Root path for curriculum

    Returns:
        (system_prompt, user_prompt, config_dict)

    Output:
        JSON with quiz_markdown and answer_key_min array
    """
    prompt_spec = _load_prompt_json("assessment/quiz_packet.json")

    user_content = "\n".join(prompt_spec["messages"][1]["content_template"])
    user_content = user_content.replace("{{week_number}}", str(week_number))

    # Extract virtue and faith from week_spec
    virtue_focus = week_spec.get("virtue_focus", week_spec.get("virtue", "N/A"))
    faith_phrase = week_spec.get("faith_phrase", "N/A")
    user_content = user_content.replace("{{week_spec.virtue_focus}}", virtue_focus)
    user_content = user_content.replace("{{week_spec.faith_phrase}}", faith_phrase)

    # Replace total points
    total_points = prompt_spec["inputs"]["format_requirements"]["total_points"]
    user_content = user_content.replace("{{format_requirements.total_points}}", str(total_points))

    # Serialize week spec (condensed)
    week_spec_json = json.dumps(week_spec, indent=2)
    if len(week_spec_json) > 1500:
        week_spec_excerpt = week_spec_json[:1500] + "\n... (truncated)"
    else:
        week_spec_excerpt = week_spec_json
    user_content = user_content.replace("{{week_spec}}", week_spec_excerpt)

    # Serialize day4 document
    day4_json = json.dumps(day4_document, indent=2)
    if len(day4_json) > 1500:
        day4_excerpt = day4_json[:1500] + "\n... (truncated)"
    else:
        day4_excerpt = day4_json
    user_content = user_content.replace("{{day4_document}}", day4_excerpt)

    # Include guidelines if provided
    if guidelines:
        if len(guidelines) > 1000:
            guidelines_excerpt = guidelines[:1000] + "\n... (truncated)"
        else:
            guidelines_excerpt = guidelines
        user_content = user_content.replace("{{guidelines}}", guidelines_excerpt)
    else:
        user_content = user_content.replace("{{guidelines}}", "[Load from Day 4 guidelines]")

    system_content = prompt_spec["messages"][0]["content_template"]

    config = {
        "temperature": prompt_spec["model_preferences"]["temperature"],
        "max_tokens": prompt_spec["model_preferences"]["max_tokens"],
        "model": prompt_spec["model_preferences"]["model"]
    }

    return (system_content, user_content, config)


# ============================================================================
# TEACHER KEY PROMPT - Generate detailed answer key for quiz
# ============================================================================

def task_teacher_key(
    week_number: int,
    quiz_markdown: str,
    answer_key_min: list,
    week_spec: Dict[str, Any]
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Generate detailed teacher answer key for weekly quiz.

    This prompt expands the minimal answer key with:
    - Grammatical rationales (1-2 sentences per question)
    - Chant references with pronunciation tips
    - Literal and idiomatic translations
    - Sample virtue reflection responses

    Args:
        week_number: Week number (1-35)
        quiz_markdown: Quiz markdown from prompt_for_quiz_packet
        answer_key_min: Minimal answer key JSON from prompt_for_quiz_packet
        week_spec: Week specification data

    Returns:
        (system_prompt, user_prompt, config_dict)

    Output:
        Markdown with title, overview, question-by-question answers, chant references, virtue samples
    """
    prompt_spec = _load_prompt_json("assessment/teacher_key.json")

    user_content = "\n".join(prompt_spec["messages"][1]["content_template"])
    user_content = user_content.replace("{{week_number}}", str(week_number))

    # Extract virtue and faith from week_spec
    virtue_focus = week_spec.get("virtue_focus", week_spec.get("virtue", "N/A"))
    faith_phrase = week_spec.get("faith_phrase", "N/A")
    user_content = user_content.replace("{{week_spec.virtue_focus}}", virtue_focus)
    user_content = user_content.replace("{{week_spec.faith_phrase}}", faith_phrase)

    # Include quiz markdown
    user_content = user_content.replace("{{quiz_markdown}}", quiz_markdown)

    # Serialize answer key
    answer_key_json = json.dumps(answer_key_min, indent=2)
    user_content = user_content.replace("{{answer_key_min}}", answer_key_json)

    system_content = prompt_spec["messages"][0]["content_template"]

    config = {
        "temperature": prompt_spec["model_preferences"]["temperature"],
        "max_tokens": prompt_spec["model_preferences"]["max_tokens"],
        "model": prompt_spec["model_preferences"]["model"]
    }

    return (system_content, user_content, config)


# ============================================================================
# EXPORT ZIP MANIFEST PROMPT - Generate file manifest for week export
# ============================================================================

def task_export_zip_manifest(
    week_number: int,
    include_assets: bool = True,
    project_root: str = "curriculum/LatinA"
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Generate export manifest for week ZIP bundle.

    This prompt produces a complete JSON manifest listing all files:
    - All 7 fields × 4 days (28 files)
    - Week_Spec files (12 files)
    - Assets (quiz, teacher key, chant chart, etc.)
    - Compiled outputs
    - Provenance and checksums (SHA-256)

    Args:
        week_number: Week number (1-35)
        include_assets: Whether to include asset files (default: True)
        project_root: Root path for curriculum

    Returns:
        (system_prompt, user_prompt, config_dict)

    Output:
        JSON with week_info, files array, provenance, counts
    """
    prompt_spec = _load_prompt_json("export/export_zip_manifest.json")

    user_content = "\n".join(prompt_spec["messages"][1]["content_template"])
    user_content = user_content.replace("{{project_root}}", project_root)
    user_content = user_content.replace("{{week_number}}", str(week_number))
    user_content = user_content.replace("{{include_assets}}", str(include_assets).lower())

    # Serialize file structure expectation
    file_structure = prompt_spec["inputs"]["file_structure_expectation"]
    file_structure_json = json.dumps(file_structure, indent=2)
    user_content = user_content.replace("{{file_structure_expectation}}", file_structure_json)

    # Replace metadata rules
    metadata_rules = prompt_spec["inputs"]["metadata_rules"]
    user_content = user_content.replace(
        "{{metadata_rules.checksum_algorithm}}",
        metadata_rules["checksum_algorithm"]
    )

    system_content = prompt_spec["messages"][0]["content_template"]

    config = {
        "temperature": prompt_spec["model_preferences"]["temperature"],
        "max_tokens": prompt_spec["model_preferences"]["max_tokens"],
        "model": prompt_spec["model_preferences"]["model"]
    }

    return (system_content, user_content, config)


# ============================================================================
# ERROR EXPLANATION PROMPT - Convert errors into actionable fixes
# ============================================================================

def task_error_explanation(
    error_context: Dict[str, Any],
    raw_error_text: str,
    recent_findings: Optional[list] = None
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Generate actionable error explanation with minimal-diff fixes.

    This prompt translates tracebacks and validation failures into:
    - Terse diagnosis (one sentence)
    - Likely causes (array of strings)
    - Minimal fix (unified-diff or JSON Patch)
    - Verification steps (concrete commands)
    - Preventive guardrails (schema hints, tests, CI)

    Args:
        error_context: Dict with component, week_number, day_number, file_path
        raw_error_text: Raw traceback or error message
        recent_findings: Optional list of validation findings

    Returns:
        (system_prompt, user_prompt, config_dict)

    Output:
        JSON with diagnosis, causes, minimal_fix, verify, guardrails
    """
    prompt_spec = _load_prompt_json("support/error_explanation.json")

    user_content = "\n".join(prompt_spec["messages"][1]["content_template"])

    # Serialize error context
    error_context_json = json.dumps(error_context, indent=2)
    user_content = user_content.replace("{{error_context}}", error_context_json)

    # Include raw error text
    user_content = user_content.replace("{{raw_error_text}}", raw_error_text)

    # Serialize recent findings
    if recent_findings:
        findings_json = json.dumps(recent_findings, indent=2)
        user_content = user_content.replace("{{recent_findings}}", findings_json)
    else:
        user_content = user_content.replace("{{recent_findings}}", "[]")

    system_content = prompt_spec["messages"][0]["content_template"]

    config = {
        "temperature": prompt_spec["model_preferences"]["temperature"],
        "max_tokens": prompt_spec["model_preferences"]["max_tokens"],
        "model": prompt_spec["model_preferences"]["model"]
    }

    return (system_content, user_content, config)


# ============================================================================
# API DOCSTRING PROMPT - Generate Python docstrings
# ============================================================================

def task_api_docstring(
    doc_style: str,
    module_path: str,
    symbol_name: str,
    signature: str,
    summary: str,
    params: list,
    returns: Dict[str, str],
    raises: Optional[list] = None,
    examples: Optional[list] = None,
    notes: Optional[list] = None
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Generate Python docstring in Google or NumPy style.

    This prompt creates clean, example-rich docstrings for TEQUILA functions:
    - Short summary line
    - Detailed Args/Parameters section
    - Returns section
    - Raises section (if applicable)
    - Examples section (runnable code)
    - Notes section (if applicable)

    Args:
        doc_style: 'google' or 'numpy'
        module_path: Path to module (e.g., 'src/cli/export.py')
        symbol_name: Function/class name
        signature: Full function signature
        summary: One-line summary
        params: List of dicts with name, type, desc
        returns: Dict with type and desc
        raises: Optional list of dicts with type and desc
        examples: Optional list of example code strings
        notes: Optional list of note strings

    Returns:
        (system_prompt, user_prompt, config_dict)

    Output:
        JSON with single key 'docstring' containing formatted docstring
    """
    prompt_spec = _load_prompt_json("support/api_docstring.json")

    user_content = "\n".join(prompt_spec["messages"][1]["content_template"])

    # Replace scalar values
    user_content = user_content.replace("{{doc_style}}", doc_style)
    user_content = user_content.replace("{{module_path}}", module_path)
    user_content = user_content.replace("{{symbol_name}}", symbol_name)
    user_content = user_content.replace("{{signature}}", signature)
    user_content = user_content.replace("{{summary}}", summary)

    # Serialize lists/dicts
    params_json = json.dumps(params, indent=2)
    user_content = user_content.replace("{{params}}", params_json)

    returns_json = json.dumps(returns, indent=2)
    user_content = user_content.replace("{{returns}}", returns_json)

    if raises:
        raises_json = json.dumps(raises, indent=2)
        user_content = user_content.replace("{{raises}}", raises_json)
    else:
        user_content = user_content.replace("{{raises}}", "[]")

    if examples:
        examples_json = json.dumps(examples, indent=2)
        user_content = user_content.replace("{{examples}}", examples_json)
    else:
        user_content = user_content.replace("{{examples}}", "[]")

    if notes:
        notes_json = json.dumps(notes, indent=2)
        user_content = user_content.replace("{{notes}}", notes_json)
    else:
        user_content = user_content.replace("{{notes}}", "[]")

    system_content = prompt_spec["messages"][0]["content_template"]

    config = {
        "temperature": prompt_spec["model_preferences"]["temperature"],
        "max_tokens": prompt_spec["model_preferences"]["max_tokens"],
        "model": prompt_spec["model_preferences"]["model"]
    }

    return (system_content, user_content, config)
