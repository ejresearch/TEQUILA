"""Prompt assembly functions for LLM generation tasks.

PROMPT ENGINEERING ARCHITECTURE (7-field day structure):
- All prompts include self-check rubrics and positive instructions
- Prompts reference role_context (field 04) for behavioral alignment
- Example skeletons embedded for LLM anchoring
- Repair logic and fallbacks for missing dependencies
- Provider-agnostic (works with OpenAI and Anthropic)
"""
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
import json
import orjson


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


def task_week_spec(outline_snip: dict) -> Tuple[str, str, Optional[Dict]]:
    """
    Generate prompts for weekly spec generation.

    Args:
        outline_snip: Snippet from curriculum outline for this week

    Returns:
        (system_prompt, user_prompt, json_schema_hint)
    """
    sys = _load_system_prompt("week_system.txt")
    usr = (
        "Using this curriculum outline seed, generate a complete Weekly Lesson Spec as JSON:\n\n"
        + orjson.dumps(outline_snip, option=orjson.OPT_INDENT_2).decode()
    )

    # Schema hint for structured output
    schema = {
        "type": "object",
        "properties": {
            "metadata": {"type": "object"},
            "objectives": {"type": "array"},
            "vocabulary": {"type": "array"},
            "grammar_focus": {"type": "string"},
            "chant": {"type": "object"},
            "sessions": {"type": "array"},
            "assessment": {"type": "object"},
            "assets": {"type": "array"},
            "spiral_links": {"type": "object"},
            "interleaving_plan": {"type": "string"},
            "misconception_watchlist": {"type": "array"},
            "preview_next_week": {"type": "string"}
        },
        "required": [
            "metadata", "objectives", "vocabulary", "grammar_focus",
            "chant", "assessment", "assets", "spiral_links",
            "interleaving_plan", "misconception_watchlist", "preview_next_week"
        ]
    }

    return sys, usr, schema


def task_role_context(week_spec: dict) -> Tuple[str, str, Optional[Dict]]:
    """
    Generate prompts for Sparky role context (week-level).

    Args:
        week_spec: The week specification data

    Returns:
        (system_prompt, user_prompt, json_schema_hint)
    """
    sys = (
        "Generate Sparky Role Context JSON with these fields:\n"
        "- identity (Sparky's character and teaching philosophy)\n"
        "- student_profile (target audience characteristics)\n"
        "- daily_cycle (typical lesson structure)\n"
        "- reinforcement_method (how Sparky encourages)\n"
        "- feedback_style (how Sparky corrects errors)\n"
        "- success_criteria (what mastery looks like)\n"
        "- knowledge_recycling (spiral learning approach)\n\n"
        "Return only valid JSON."
    )

    usr = (
        "Base this Sparky role context on the week metadata and spiral links:\n\n"
        + orjson.dumps(
            {
                "metadata": week_spec.get("metadata", {}),
                "spiral_links": week_spec.get("spiral_links", {})
            },
            option=orjson.OPT_INDENT_2
        ).decode()
    )

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
                "title": week_spec.get("metadata", {}).get("title", ""),
                "vocabulary": week_spec.get("vocabulary", [])[:5],  # Sample
                "chant": week_spec.get("chant", {}),
                "virtue_focus": week_spec.get("metadata", {}).get("virtue_focus", "")
            },
            option=orjson.OPT_INDENT_2
        ).decode()
    )

    return sys, usr, None


# ============================================================================
# ROLE_CONTEXT PROMPT (Field 04) - Foundation for all day content
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
    sys = _load_system_prompt("day_role_context_system.txt")

    # Extract spiral links for context
    spiral_links = week_spec.get("spiral_links", {})
    metadata = week_spec.get("metadata", {})
    week_number = metadata.get("week_number", "?")

    # Build spiral emphasis suggestions based on week_spec
    spiral_suggestions = []
    if spiral_links:
        if "prior_vocabulary" in spiral_links:
            prior_vocab = spiral_links.get("prior_vocabulary", [])
            if prior_vocab:
                spiral_suggestions.append(f"Prior vocabulary from weeks: {prior_vocab}")
        if "prior_grammar" in spiral_links:
            prior_grammar = spiral_links.get("prior_grammar", [])
            if prior_grammar:
                spiral_suggestions.append(f"Prior grammar concepts: {prior_grammar}")

    # Day-specific behavioral hints
    day_behaviors = {
        1: "patient, exploratory, high encouragement for first attempts",
        2: "reinforcing, practice-focused, celebrate progress",
        3: "application-oriented, challenge students to synthesize",
        4: "review-focused, spiral-heavy, assess prior knowledge"
    }

    # Build example skeleton
    example_skeleton = {
        "sparky_role": "e.g., 'patient guide', 'socratic questioner', 'encouraging coach'",
        "focus_mode": _get_day_focus(day),
        "hints_enabled": True,
        "spiral_emphasis": spiral_suggestions if day >= 2 else [],
        "encouragement_triggers": ["first_attempt", "corrected_error", "progress_shown"],
        "max_hints": 3,
        "wait_time_seconds": 5,
        "virtue_callout": f"How to integrate week's virtue: {metadata.get('virtue_focus', 'N/A')}"
    }

    usr = (
        f"Generate day-specific role_context JSON for Week {week_number} Day {day}.\n\n"
        f"BEHAVIORAL GUIDANCE FOR DAY {day}: {day_behaviors.get(day, 'general instruction')}\n\n"
        "TASK: Produce a role_context JSON object that defines Sparky's teaching behavior for this specific day.\n\n"
        "INPUTS (week metadata and spiral links):\n"
        + orjson.dumps(
            {
                "metadata": metadata,
                "spiral_links": spiral_links,
                "day": day,
                "day_focus": _get_day_focus(day),
                "spiral_suggestions": spiral_suggestions
            },
            option=orjson.OPT_INDENT_2
        ).decode()
        + "\n\n"
        "EXPECTED OUTPUT STRUCTURE (use this as your template):\n"
        + json.dumps(example_skeleton, indent=2)
        + "\n\n"
        "INSTRUCTIONS:\n"
        "1. Set sparky_role to match the day's behavioral guidance above (≤50 chars).\n"
        "2. Set focus_mode to the exact day_focus value provided in inputs.\n"
        "3. Set hints_enabled to true (always enable hints for Latin A students).\n"
        "4. Populate spiral_emphasis array:\n"
        f"   - For Day {day}: "
        + ("Include ≥2 specific prior content references from spiral_suggestions above." if day >= 2 else "Leave empty (no prior content yet).")
        + "\n"
        "5. Set encouragement_triggers to at least 3 events (use examples or add custom ones).\n"
        "6. Set max_hints to 3 (standard for this grade level).\n"
        "7. Set wait_time_seconds to 5 (allow thinking time).\n"
        "8. Include virtue_callout if week metadata specifies a virtue_focus.\n\n"
        "OUTPUT FORMAT:\n"
        "- Return ONLY valid JSON (no markdown, no code fences, no explanatory text).\n"
        "- Match the structure of the example skeleton exactly.\n"
        "- All string values must be concise (sparky_role ≤50 chars, focus_mode ≤30 chars).\n\n"
        "SELF-CHECK BEFORE RETURNING:\n"
        "✓ Is the JSON valid and parseable?\n"
        f"✓ Does focus_mode match the required value: '{_get_day_focus(day)}'?\n"
        f"✓ For Day {day}, does spiral_emphasis have {'≥2 items' if day >= 2 else '0 items (empty array)'}?\n"
        "✓ Are all required fields present: sparky_role, focus_mode, hints_enabled?\n"
        "✓ Are string lengths within limits (sparky_role ≤50, focus_mode ≤30)?\n"
    )

    schema = {  # Strict JSON schema for structured output mode
        "type": "object",
        "properties": {
            "sparky_role": {"type": "string"},
            "focus_mode": {"type": "string"},
            "hints_enabled": {"type": "boolean"},
            "spiral_emphasis": {"type": "array", "items": {"type": "string"}},
            "encouragement_triggers": {"type": "array", "items": {"type": "string"}},
            "max_hints": {"type": "integer"},
            "wait_time_seconds": {"type": "integer"},
            "virtue_callout": {"type": "string"}
        },
        "required": ["sparky_role", "focus_mode", "hints_enabled"]
    }

    return sys, usr, schema


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
    sys = _load_system_prompt("guidelines_system.txt")

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

    metadata = week_spec.get("metadata", {})
    objectives = week_spec.get("objectives", [])
    spiral_links = week_spec.get("spiral_links", {})
    vocabulary = week_spec.get("vocabulary", [])[:5]  # Sample first 5
    misconception_watchlist = week_spec.get("misconception_watchlist", [])

    # Build YAML references template
    vocab_items = []
    for v in vocabulary:
        if isinstance(v, dict):
            vocab_items.append(v.get("latin", ""))
        elif isinstance(v, str):
            vocab_items.append(v)

    yaml_references = {
        "prior_knowledge": spiral_links.get("prior_vocabulary", []),
        "vocabulary": vocab_items,
        "grammar_focus": metadata.get("grammar_focus", ""),
        "virtue": metadata.get("virtue_focus", "")
    }

    # Markdown template
    markdown_template = f"""---
references:
  prior_knowledge: {yaml_references['prior_knowledge']}
  vocabulary: {yaml_references['vocabulary']}
  grammar_focus: "{yaml_references['grammar_focus']}"
  virtue: "{yaml_references['virtue']}"
---

# Week {metadata.get('week_number', '?')} Day {day}: Teaching Guidelines

## Sparky's Role for This Day
**Persona:** {role_context.get('sparky_role', 'encouraging guide')}
**Focus Mode:** {role_context.get('focus_mode', 'general')}
**Hints Enabled:** {role_context.get('hints_enabled', True)}

## Lesson Objectives
- [List primary objectives from week_spec]
- [Include spiral review objectives for Day 4]

## Teaching Flow Overview
1. **Greeting & Activation** (2-3 min)
2. **Prior Knowledge Recall** (3-5 min) - Spiral emphasis: {role_context.get('spiral_emphasis', [])}
3. **New Content Introduction** (10-15 min)
4. **Guided Practice** (10-12 min)
5. **Assessment / Closure** (3-5 min)

## Behavioral Hints
- Encouragement triggers: {role_context.get('encouragement_triggers', [])}
- Max hints before revealing answer: {role_context.get('max_hints', 3)}
- Wait time: {role_context.get('wait_time_seconds', 5)} seconds

## Common Misconceptions
- [List from week_spec misconception_watchlist]

## Day-Specific Notes
{"- Day 4: Ensure ≥25% content is spiral review from prior weeks" if day == 4 else ""}
{"- Day 1: Focus on exploration and novelty, high encouragement" if day == 1 else ""}
"""

    usr = (
        f"Generate teaching guidelines (markdown) for Week {metadata.get('week_number', '?')} Day {day}.\n\n"
        "TASK: Produce field 05_guidelines_for_sparky.md — a markdown document with YAML references header.\n\n"
        "INPUTS:\n"
        "Week Spec:\n"
        + orjson.dumps(
            {
                "metadata": metadata,
                "objectives": objectives,
                "spiral_links": spiral_links,
                "vocabulary_sample": vocabulary,
                "misconception_watchlist": misconception_watchlist
            },
            option=orjson.OPT_INDENT_2
        ).decode()
        + "\n\nRole Context (from field 04):\n"
        + json.dumps(role_context, indent=2)
        + "\n\n"
        "EXPECTED OUTPUT STRUCTURE (use as template):\n"
        + markdown_template
        + "\n\n"
        "INSTRUCTIONS:\n"
        "1. Start with YAML frontmatter (--- references: --- block) pointing to prior_knowledge, vocabulary, grammar_focus, virtue.\n"
        "2. Include section: '## Sparky's Role for This Day' with persona, focus_mode, hints_enabled from role_context.\n"
        "3. List lesson objectives from week_spec objectives array (minimum 2, maximum 5).\n"
        "4. Provide teaching flow overview with 5 phases (greeting, recall, introduction, practice, closure).\n"
        "5. Include behavioral hints section with encouragement_triggers, max_hints, wait_time from role_context.\n"
        "6. List common misconceptions from week_spec misconception_watchlist (if present).\n"
        f"7. Add day-specific notes: {'Day 4 must emphasize ≥25% spiral review' if day == 4 else 'Day 1 focuses on exploration'}.\n\n"
        "OUTPUT FORMAT:\n"
        "- Return ONLY markdown text (no JSON, no code fences around the markdown itself).\n"
        "- Begin with YAML frontmatter (---\\nreferences:\\n  ...).\n"
        "- Use proper markdown heading hierarchy (# ## ###).\n\n"
        "SELF-CHECK BEFORE RETURNING:\n"
        "✓ Does output start with YAML frontmatter (--- references: ---)?.\n"
        "✓ Are all 4 YAML reference keys present: prior_knowledge, vocabulary, grammar_focus, virtue?\n"
        "✓ Does '## Sparky's Role' section include persona, focus_mode, hints_enabled?\n"
        "✓ Are spiral_emphasis items from role_context mentioned in 'Prior Knowledge Recall' step?\n"
        f"✓ For Day {day}: {'Is ≥25% spiral content emphasized?' if day == 4 else 'Is exploration/novelty emphasized?' if day == 1 else 'Is practice/application emphasized?'}\n"
    )

    return sys, usr, None  # No JSON schema (markdown output)


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
    sys = (
        "Generate the THREE metadata fields for a single day lesson:\n"
        "1. class_name - short lesson title\n"
        "2. summary - 2-3 sentence overview\n"
        "3. grade_level - target grade range\n"
        "\n"
        "FIELD NUMBERING (7-field architecture):\n"
        "- These are fields 01, 02, 03\n"
        "- Field 04 (role_context) is generated separately\n"
        "- Field 05 (guidelines), 06 (document), 07 (greeting) are generated separately\n\n"
        "INSTRUCTIONS:\n"
        "- class_name: Format as 'Week X Day Y: Topic' (≤100 chars)\n"
        "- summary: 2-3 sentences describing lesson focus (50-500 chars)\n"
        "- grade_level: Format as 'N-M' where N and M are grade numbers (e.g., '3-5', '6-8')\n\n"
        "OUTPUT FORMAT:\n"
        "Return as JSON object with these keys.\n"
        "{\n"
        "  \"class_name\": \"Week X Day Y: Topic\",\n"
        "  \"summary\": \"Lesson overview in 2-3 sentences.\",\n"
        "  \"grade_level\": \"3-5\"\n"
        "}\n\n"
        "SELF-CHECK:\n"
        "✓ Is class_name formatted as 'Week X Day Y: Topic'?\n"
        "✓ Is summary 2-3 sentences (50-500 chars)?\n"
        "✓ Is grade_level in 'N-M' format (e.g., '3-5')?\n"
    )

    usr = (
        f"Week metadata and objectives for Day {day}:\n\n"
        + orjson.dumps(
            {
                "metadata": week_spec.get("metadata", {}),
                "objectives": week_spec.get("objectives", []),
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

def task_day_document(week_spec: dict, day: int) -> Tuple[str, str, Optional[Dict]]:
    """
    Generate prompts for day document_for_sparky (field 06 - structured lesson plan JSON).

    UPDATED FOR 7-FIELD ARCHITECTURE:
    - Field 06 (was field 05 in legacy 6-field layout)
    - Consumes role_context from field 04
    - Validates against guidelines YAML references

    Args:
        week_spec: The week specification data
        day: Day number (1-4)

    Returns:
        (system_prompt, user_prompt, json_schema_hint)
    """
    sys = _load_system_prompt("day_system.txt")

    metadata = week_spec.get("metadata", {})
    objectives = week_spec.get("objectives", [])
    vocabulary = week_spec.get("vocabulary", [])
    spiral_links = week_spec.get("spiral_links", {})
    misconception_watchlist = week_spec.get("misconception_watchlist", [])

    usr = (
        f"Generate Day {day} document_for_sparky JSON.\n\n"
        "TASK: Produce field 06_document_for_sparky.json — a complete lesson plan in JSON format.\n\n"
        "INPUTS (week specification):\n"
        + orjson.dumps(
            {
                "metadata": metadata,
                "objectives": objectives,
                "vocabulary": vocabulary,
                "spiral_links": spiral_links,
                "misconception_watchlist": misconception_watchlist,
                "day": day
            },
            option=orjson.OPT_INDENT_2
        ).decode()
    )

    # Strict JSON schema for structured output
    schema = {
        "type": "object",
        "required": [
            "metadata", "prior_knowledge_digest", "yesterday_recap",
            "spiral_links", "misconception_watchlist", "objectives",
            "materials", "lesson_flow", "behavior"
        ]
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
    sys = _load_system_prompt("greeting_system.txt")

    # Handle missing role_context (fallback)
    if not role_context:
        role_context = {
            "sparky_role": "encouraging Latin guide",
            "focus_mode": _get_day_focus(day),
            "encouragement_triggers": ["first_attempt"]
        }

    metadata = week_spec.get("metadata", {})

    # Extract topic from document if available
    topic = "Latin"
    if document and "metadata" in document:
        topic = document["metadata"].get("title", "Latin")

    # Persona-specific greeting templates
    persona_hints = {
        "patient guide": "Use gentle, inviting language",
        "socratic questioner": "Pose a curious question",
        "cheerleader": "Use energetic, enthusiastic tone",
        "encouraging coach": "Motivational and supportive"
    }

    sparky_role = role_context.get("sparky_role", "encouraging Latin guide")
    persona_hint = persona_hints.get(sparky_role, "Use warm, friendly language")

    example_greetings = [
        f"Welcome, young scholars! Today we'll explore {topic} together.",
        f"Salvē, students! Are you ready to discover the beauty of {topic}?",
        f"Greetings, Latin learners! Let's dive into {topic} with curiosity and joy."
    ]

    usr = (
        f"Generate Sparky's greeting for Week {metadata.get('week_number', '?')} Day {day}.\n\n"
        "TASK: Produce field 07_sparkys_greeting.txt — a 1-2 sentence welcome message for students.\n\n"
        "INPUTS:\n"
        f"Sparky's Role: {sparky_role}\n"
        f"Focus Mode: {role_context.get('focus_mode', 'general')}\n"
        f"Lesson Topic: {topic}\n"
        f"Week Theme: {metadata.get('theme', 'Latin fundamentals')}\n"
        f"Virtue Focus: {metadata.get('virtue_focus', 'N/A')}\n\n"
        "PERSONA GUIDANCE:\n"
        f"{persona_hint}\n\n"
        "EXAMPLE GREETINGS (for inspiration):\n"
        + "\n".join(f"- {ex}" for ex in example_greetings)
        + "\n\n"
        "INSTRUCTIONS:\n"
        "1. Write a greeting that reflects Sparky's persona (sparky_role above).\n"
        "2. Reference the lesson topic or week theme specifically (avoid generic greetings).\n"
        "3. Keep it concise: 1-2 sentences, maximum 200 characters.\n"
        "4. Use warm, encouraging, age-appropriate language (grades 3-8).\n"
        "5. Optional: incorporate virtue focus if present.\n"
        f"6. Day-specific tone: {'Welcoming and exploratory' if day == 1 else 'Reinforcing and encouraging' if day == 2 else 'Challenging and enthusiastic' if day == 3 else 'Review-focused and celebratory' if day == 4 else 'Warm and inviting'}.\n\n"
        "OUTPUT FORMAT:\n"
        "- Return ONLY the greeting text (no JSON, no markdown, no labels).\n"
        "- Plain text, 1-2 sentences, maximum 200 characters.\n\n"
        "SELF-CHECK:\n"
        "✓ Is greeting 1-2 sentences (≤200 chars)?\n"
        f"✓ Does greeting reflect persona '{sparky_role}'?\n"
        "✓ Does greeting reference the specific lesson topic?\n"
        "✓ Is tone warm, encouraging, and age-appropriate?\n"
    )

    return sys, usr, None  # No JSON schema (plain text output)
