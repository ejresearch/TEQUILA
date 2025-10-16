"""
Curriculum Outline Service - Master 35-week scope & sequence.

This module provides the single source of truth for all 35 weeks of Latin A.
Every week generation must reference this outline to ensure:
- Sequential dependency validation
- Grammar focus alignment
- Vocabulary progression
- Session duration correctness
"""
import json
from pathlib import Path
from typing import Dict, List, Optional


def load_curriculum_outline() -> Dict:
    """Load the master curriculum outline (70 bullets, 35 weeks)."""
    outline_path = Path(__file__).parent.parent.parent / "curriculum_outline.json"
    with open(outline_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_week_outline(week_num: int) -> Dict:
    """Get outline data for a specific week."""
    outline = load_curriculum_outline()
    if week_num < 1 or week_num > outline["total_weeks"]:
        raise ValueError(f"Week {week_num} out of range (1-{outline['total_weeks']})")

    return outline["weeks"][week_num - 1]


def get_session_duration(week_num: int) -> str:
    """Get session duration for a specific week."""
    week_outline = get_week_outline(week_num)
    return week_outline["session_duration"]


def get_prerequisites(week_num: int) -> List[int]:
    """Get list of prerequisite weeks for a given week."""
    week_outline = get_week_outline(week_num)
    return week_outline["prerequisites"]


def get_introduced_concepts(week_num: int) -> List[str]:
    """Get list of concepts introduced in a given week."""
    week_outline = get_week_outline(week_num)
    return week_outline.get("introduces", [])


def get_cumulative_concepts(week_num: int) -> List[str]:
    """
    Get all concepts introduced from Week 1 through week_num.
    Used for spiral review content generation.
    """
    outline = load_curriculum_outline()
    cumulative = []

    for week in range(1, week_num + 1):
        week_data = outline["weeks"][week - 1]
        cumulative.extend(week_data.get("introduces", []))

    return cumulative


def get_prior_weeks_summary(week_num: int) -> str:
    """
    Generate a human-readable summary of prior weeks for context.
    Used in LLM prompts for spiral review generation.
    """
    outline = load_curriculum_outline()

    if week_num == 1:
        return "No prior weeks (this is Week 1)"

    summary_lines = []
    for week in range(1, week_num):
        week_data = outline["weeks"][week - 1]
        summary_lines.append(
            f"Week {week}: {week_data['title']} "
            f"(introduced: {', '.join(week_data.get('introduces', [])[:3])}...)"
        )

    return "\n".join(summary_lines)


def validate_week_prerequisites(week_num: int, curriculum_path: Path) -> bool:
    """
    Validate that all prerequisite weeks exist before generating week_num.

    Args:
        week_num: Week to validate
        curriculum_path: Path to curriculum directory

    Returns:
        True if all prerequisites exist

    Raises:
        ValueError: If any prerequisite is missing
    """
    prerequisites = get_prerequisites(week_num)

    if not prerequisites:
        return True  # Week 1 has no prerequisites

    missing = []
    for prereq_week in prerequisites:
        prereq_path = curriculum_path / f"Week{prereq_week:02d}" / "internal_documents" / "week_spec.json"
        if not prereq_path.exists():
            missing.append(prereq_week)

    if missing:
        raise ValueError(
            f"Cannot generate Week {week_num}: prerequisite weeks {missing} are missing.\n"
            f"Required prerequisites: {prerequisites}\n"
            f"Generate weeks sequentially from Week {min(missing)} first."
        )

    return True


def get_upcoming_weeks_preview(week_num: int, look_ahead: int = 5) -> str:
    """
    Get preview of upcoming weeks to avoid teaching content too early.

    Args:
        week_num: Current week
        look_ahead: How many weeks ahead to preview

    Returns:
        Human-readable summary of upcoming topics
    """
    outline = load_curriculum_outline()
    total_weeks = outline["total_weeks"]

    if week_num >= total_weeks:
        return "No upcoming weeks (final week)"

    preview_lines = []
    for week in range(week_num + 1, min(week_num + look_ahead + 1, total_weeks + 1)):
        week_data = outline["weeks"][week - 1]
        preview_lines.append(
            f"Week {week}: {week_data['title']} "
            f"(DO NOT teach: {', '.join(week_data.get('introduces', [])[:2])})"
        )

    return "\n".join(preview_lines)


def format_week_constraints_for_prompt(week_num: int) -> str:
    """
    Format week outline constraints for LLM prompt injection.

    Returns formatted string ready to inject into week_spec generation prompt.
    """
    week_outline = get_week_outline(week_num)

    constraints = f"""
MASTER CURRICULUM OUTLINE CONSTRAINTS FOR WEEK {week_num}:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

TITLE: {week_outline['title']}
CONTENT FOCUS: {week_outline['content_focus']}

SESSION STRUCTURE:
• Duration: {week_outline['session_duration']} per day
• Days: 4 (Discovery, Reinforcement, Integration, Assessment)

GRAMMAR FOCUS:
{week_outline['grammar_focus']}

VOCABULARY DOMAIN:
{week_outline['vocabulary_domain']}

CHANT:
{week_outline['chant']}

CONCEPTS TO INTRODUCE THIS WEEK:
{chr(10).join('• ' + concept for concept in week_outline.get('introduces', []))}

PREREQUISITES (must build on these):
{get_prior_weeks_summary(week_num)}

UPCOMING TOPICS (do NOT teach yet):
{get_upcoming_weeks_preview(week_num, look_ahead=3)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Your generated week_spec.json MUST:
1. Align with the TITLE and CONTENT FOCUS above
2. Use the specified SESSION DURATION
3. Teach ONLY the concepts listed in "INTRODUCES"
4. Build on all PREREQUISITES
5. Avoid spoiling UPCOMING TOPICS
6. Match the quality of reference weeks (1, 11-15)
"""

    return constraints
