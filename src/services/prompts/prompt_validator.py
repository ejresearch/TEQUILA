"""
Prompt output validation utilities.

These functions validate that LLM-generated content matches expected formats
and constraints defined in prompt templates. Use for testing and repair logic.
"""
import json
import re
from typing import Dict, Any, List, Tuple, Optional


def validate_role_context(data: Dict[str, Any], day: int) -> Tuple[bool, List[str]]:
    """
    Validate role_context JSON against schema and day-specific requirements.

    Args:
        data: Parsed role_context JSON
        day: Day number (1-4)

    Returns:
        (is_valid, error_messages)
    """
    errors = []

    # Required fields
    required = ["sparky_role", "focus_mode", "hints_enabled"]
    for field in required:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    # Length constraints
    if "sparky_role" in data:
        if len(data["sparky_role"]) > 50:
            errors.append(f"sparky_role too long: {len(data['sparky_role'])} chars (max 50)")

    if "focus_mode" in data:
        if len(data["focus_mode"]) > 30:
            errors.append(f"focus_mode too long: {len(data['focus_mode'])} chars (max 30)")

    # hints_enabled type check
    if "hints_enabled" in data and not isinstance(data["hints_enabled"], bool):
        errors.append(f"hints_enabled must be boolean, got {type(data['hints_enabled'])}")

    # Day-specific spiral_emphasis requirements
    spiral_emphasis = data.get("spiral_emphasis", [])
    if day == 1:
        # Day 1 should have empty spiral_emphasis
        if len(spiral_emphasis) > 0:
            errors.append(f"Day 1 should have empty spiral_emphasis (got {len(spiral_emphasis)} items)")
    elif day == 4:
        # Day 4 must have ≥2 items
        if len(spiral_emphasis) < 2:
            errors.append(f"Day 4 requires ≥2 spiral_emphasis items (got {len(spiral_emphasis)})")
    else:
        # Day 2-3 should have ≥1 item
        if len(spiral_emphasis) < 1:
            errors.append(f"Day {day} should have ≥1 spiral_emphasis item (got {len(spiral_emphasis)})")

    # encouragement_triggers minimum
    triggers = data.get("encouragement_triggers", [])
    if len(triggers) < 3:
        errors.append(f"encouragement_triggers should have ≥3 items (got {len(triggers)})")

    return (len(errors) == 0, errors)


def validate_guidelines_markdown(text: str, day: int) -> Tuple[bool, List[str]]:
    """
    Validate guidelines markdown against structure requirements.

    Args:
        text: Guidelines markdown text
        day: Day number (1-4)

    Returns:
        (is_valid, error_messages)
    """
    errors = []

    # Check YAML frontmatter
    if not text.startswith("---"):
        errors.append("Guidelines must start with YAML frontmatter (---)")
    else:
        # Extract YAML block
        yaml_match = re.search(r'^---\n(.*?)\n---', text, re.DOTALL | re.MULTILINE)
        if not yaml_match:
            errors.append("YAML frontmatter not properly closed (missing second ---)")
        else:
            yaml_content = yaml_match.group(1)
            required_keys = ["prior_knowledge", "vocabulary", "grammar_focus", "virtue"]
            for key in required_keys:
                if key not in yaml_content:
                    errors.append(f"YAML frontmatter missing key: {key}")

    # Check required sections
    required_sections = [
        "# Week",
        "## Sparky's Role",
        "## Lesson Objectives",
        "## Teaching Flow",
        "## Behavioral Hints",
        "## Common Misconceptions",
        "## Day-Specific Notes"
    ]
    for section in required_sections:
        if section not in text:
            errors.append(f"Missing required section: {section}")

    # Day 4 specific check
    if day == 4:
        if "25%" not in text and "spiral" not in text.lower():
            errors.append("Day 4 guidelines must mention 25% spiral content requirement")

    return (len(errors) == 0, errors)


def validate_document_json(data: Dict[str, Any], day: int) -> Tuple[bool, List[str]]:
    """
    Validate document_for_sparky JSON against schema requirements.

    Args:
        data: Parsed document JSON
        day: Day number (1-4)

    Returns:
        (is_valid, error_messages)
    """
    errors = []

    # Required top-level fields
    required = [
        "metadata", "prior_knowledge_digest", "yesterday_recap",
        "spiral_links", "misconception_watchlist", "objectives",
        "materials", "lesson_flow", "behavior"
    ]
    for field in required:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    # prior_knowledge_digest word count
    if "prior_knowledge_digest" in data:
        word_count = len(data["prior_knowledge_digest"].split())
        if word_count < 120 or word_count > 200:
            errors.append(f"prior_knowledge_digest should be 120-200 words (got {word_count})")

    # lesson_flow validation
    if "lesson_flow" in data:
        lesson_flow = data["lesson_flow"]
        if len(lesson_flow) < 5:
            errors.append(f"lesson_flow must have ≥5 steps (got {len(lesson_flow)})")

        # First 1-2 steps must be recall/review
        if len(lesson_flow) >= 2:
            first_two_types = [step.get("type") for step in lesson_flow[:2]]
            if not any(t in ["recall", "review"] for t in first_two_types):
                errors.append(f"First 1-2 lesson_flow steps must be 'recall' or 'review' (got {first_two_types})")

        # Day 4 spiral requirement
        if day == 4:
            total_time = sum(step.get("duration_minutes", 0) for step in lesson_flow)
            spiral_time = sum(
                step.get("duration_minutes", 0)
                for step in lesson_flow
                if step.get("type") in ["recall", "review", "assessment"]
            )
            if total_time > 0:
                spiral_pct = (spiral_time / total_time) * 100
                if spiral_pct < 25:
                    errors.append(f"Day 4 requires ≥25% spiral content (got {spiral_pct:.1f}%)")

    return (len(errors) == 0, errors)


def validate_greeting_text(text: str) -> Tuple[bool, List[str]]:
    """
    Validate greeting text against length and format requirements.

    Args:
        text: Greeting plain text

    Returns:
        (is_valid, error_messages)
    """
    errors = []

    if len(text) > 200:
        errors.append(f"Greeting too long: {len(text)} chars (max 200)")

    if len(text.split('.')) > 3:
        errors.append("Greeting should be 1-2 sentences (found >2)")

    return (len(errors) == 0, errors)
