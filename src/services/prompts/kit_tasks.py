"""Prompt assembly functions for LLM generation tasks."""
from pathlib import Path
from typing import Dict, Optional, Tuple
import orjson


def _load_system_prompt(filename: str) -> str:
    """Load a system prompt from the prompts directory."""
    path = Path(__file__).parent / filename
    return path.read_text(encoding="utf-8")


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
    Generate prompts for Sparky role context.

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


def task_day_role_context(week_spec: dict, day: int) -> Tuple[str, str, Optional[Dict]]:
    """
    Generate prompts for day-specific role_context (the 4th Flint field).

    This field defines Sparky's behavioral parameters for the specific day,
    including teaching persona, hint availability, spiral emphasis, etc.

    Args:
        week_spec: The week specification data
        day: Day number (1-4)

    Returns:
        (system_prompt, user_prompt, json_schema_hint)
    """
    sys = _load_system_prompt("day_role_context_system.txt")

    usr = (
        f"Generate day-specific role_context JSON for Week {week_spec.get('metadata', {}).get('week_number', '?')} Day {day}.\n\n"
        "Week metadata and spiral links:\n"
        + orjson.dumps(
            {
                "metadata": week_spec.get("metadata", {}),
                "spiral_links": week_spec.get("spiral_links", {}),
                "day": day,
                "day_focus": _get_day_focus(day)
            },
            option=orjson.OPT_INDENT_2
        ).decode()
    )

    schema = {
        "type": "object",
        "properties": {
            "sparky_role": {"type": "string"},
            "focus_mode": {"type": "string"},
            "hints_enabled": {"type": "boolean"},
            "spiral_emphasis": {"type": "array", "items": {"type": "string"}},
            "encouragement_triggers": {"type": "array", "items": {"type": "string"}}
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


def task_day_fields(week_spec: dict, day: int) -> Tuple[str, str, Optional[Dict]]:
    """
    Generate prompts for day Flint fields (class_name, summary, grade_level, guidelines, greeting).

    Note: role_context (field 04) is generated separately via task_day_role_context.

    Args:
        week_spec: The week specification data
        day: Day number (1-4)

    Returns:
        (system_prompt, user_prompt, json_schema_hint)
    """
    sys = (
        "Produce the text Flint fields for a single day (excluding role_context):\n"
        "1. class_name - short lesson title\n"
        "2. summary - 2-3 sentence overview\n"
        "3. grade_level - target grade range\n"
        "4. guidelines_for_sparky - teaching notes (markdown, now field 05)\n"
        "5. sparkys_greeting - 1-2 sentence student greeting (now field 07)\n\n"
        "Return as JSON object with these keys.\n"
        "Keep greeting warm and encouraging (≤2 sentences)."
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


def task_day_document(week_spec: dict, day: int) -> Tuple[str, str, Optional[Dict]]:
    """
    Generate prompts for day document_for_sparky (the structured lesson plan).

    Args:
        week_spec: The week specification data
        day: Day number (1-4)

    Returns:
        (system_prompt, user_prompt, json_schema_hint)
    """
    sys = _load_system_prompt("day_system.txt")

    usr = (
        f"Generate Day {day} document_for_sparky JSON.\n\n"
        "Week metadata and content:\n"
        + orjson.dumps(
            {
                "metadata": week_spec.get("metadata", {}),
                "objectives": week_spec.get("objectives", []),
                "vocabulary": week_spec.get("vocabulary", []),
                "spiral_links": week_spec.get("spiral_links", {}),
                "day": day
            },
            option=orjson.OPT_INDENT_2
        ).decode()
    )

    # Schema hint
    schema = {
        "type": "object",
        "required": [
            "metadata", "prior_knowledge_digest", "yesterday_recap",
            "spiral_links", "misconception_watchlist", "objectives",
            "materials", "lesson_flow", "behavior"
        ]
    }

    return sys, usr, schema
