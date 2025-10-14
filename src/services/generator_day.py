"""Day activity generation service."""
from pathlib import Path
from typing import Dict, Any, List
import orjson
from .storage import (
    day_dir,
    day_field_path,
    week_spec_part_path,
    DAY_FIELDS,
    write_file,
    write_json
)
from .llm_client import LLMClient
from .prompts.kit_tasks import task_day_fields, task_day_document


def get_field_template_path(field_name: str) -> Path:
    """Get the path to a field template file."""
    return Path(__file__).parent.parent / "templates" / "week_kit" / "activities" / "fields" / field_name


def scaffold_day(week_number: int, day_number: int) -> Path:
    """
    Create the complete directory structure and files for a specific day.

    Creates the six Flint field files:
    - 01_class_name.txt
    - 02_summary.md
    - 03_grade_level.txt
    - 04_guidelines_for_sparky.md
    - 05_document_for_sparky.json
    - 06_sparkys_greeting.txt

    Args:
        week_number: The week number (1-36)
        day_number: The day number (1-4)

    Returns:
        Path to the created day directory.
    """
    day_path = day_dir(week_number, day_number)
    day_path.mkdir(parents=True, exist_ok=True)

    # Create each field file from templates
    for field in DAY_FIELDS:
        template_path = get_field_template_path(field)
        target_path = day_field_path(week_number, day_number, field)

        if template_path.exists():
            content = template_path.read_text(encoding="utf-8")
            # Replace template variables
            content = content.replace("{week_number}", str(week_number))
            content = content.replace("{day_number}", str(day_number))
            content = content.replace("{focus_area}", get_day_focus(day_number))

            target_path.write_text(content, encoding="utf-8")
        else:
            # Create placeholder based on file type
            if field.endswith(".json"):
                write_json(target_path, {})
            else:
                write_file(target_path, "")

    return day_path


def get_day_focus(day_number: int) -> str:
    """Get the pedagogical focus for a specific day."""
    focuses = {
        1: "Introduction and exploration",
        2: "Practice and reinforcement",
        3: "Application and extension",
        4: "Review and spiral (25% prior content)"
    }
    return focuses.get(day_number, "General instruction")


def scaffold_week_days(week_number: int) -> list[Path]:
    """
    Scaffold all four days for a specific week.

    Args:
        week_number: The week number (1-36)

    Returns:
        List of paths to created day directories.
    """
    day_paths = []
    for day_num in range(1, 5):
        day_path = scaffold_day(week_number, day_num)
        day_paths.append(day_path)

    return day_paths


# ============================================================================
# LLM-BASED GENERATION FUNCTIONS
# ============================================================================

def generate_day_fields(week: int, day: int, client: LLMClient) -> List[Path]:
    """
    Generate the six Flint field files for a day using LLM.

    Args:
        week: Week number (1-36)
        day: Day number (1-4)
        client: LLM client instance

    Returns:
        List of paths to generated field files
    """
    # Ensure day directory exists
    scaffold_day(week, day)

    # Load week spec to inform day fields
    spec_path = week_spec_part_path(week, "99_compiled_week_spec.json")
    if spec_path.exists():
        week_spec = orjson.loads(spec_path.read_bytes())
    else:
        week_spec = {"metadata": {"week": week, "title": f"Week {week}"}}

    # Get prompts
    sys, usr, _ = task_day_fields(week_spec, day)

    # Generate via LLM
    response = client.generate(prompt=usr, system=sys)

    # Parse response
    if response.json:
        fields_data = response.json
    else:
        try:
            fields_data = orjson.loads(response.text)
        except Exception:
            # Fallback to minimal data
            fields_data = {
                "class_name": f"Week {week} Day {day}",
                "summary": "Latin lesson",
                "grade_level": "3-5",
                "guidelines_for_sparky": "Teach Latin vocabulary",
                "sparkys_greeting": "Welcome to Latin!"
            }

    # Write field files (excluding document_for_sparky which is separate)
    field_mapping = {
        "01_class_name.txt": fields_data.get("class_name", ""),
        "02_summary.md": fields_data.get("summary", ""),
        "03_grade_level.txt": fields_data.get("grade_level", ""),
        "04_guidelines_for_sparky.md": fields_data.get("guidelines_for_sparky", ""),
        "06_sparkys_greeting.txt": fields_data.get("sparkys_greeting", "")
    }

    created_paths = []
    for field_name, content in field_mapping.items():
        field_path = day_field_path(week, day, field_name)
        write_file(field_path, str(content))
        created_paths.append(field_path)

    return created_paths


def generate_day_document(week: int, day: int, client: LLMClient) -> Path:
    """
    Generate the document_for_sparky JSON for a day using LLM.

    Args:
        week: Week number (1-36)
        day: Day number (1-4)
        client: LLM client instance

    Returns:
        Path to generated document_for_sparky.json
    """
    # Ensure day directory exists
    scaffold_day(week, day)

    # Load week spec to inform day document
    spec_path = week_spec_part_path(week, "99_compiled_week_spec.json")
    if spec_path.exists():
        week_spec = orjson.loads(spec_path.read_bytes())
    else:
        week_spec = {"metadata": {"week": week, "title": f"Week {week}"}}

    # Get prompts
    sys, usr, schema = task_day_document(week_spec, day)

    # Generate via LLM
    response = client.generate(prompt=usr, system=sys, json_schema=schema)

    # Parse response
    if response.json:
        doc_data = response.json
    else:
        try:
            doc_data = orjson.loads(response.text)
        except Exception as e:
            # Save invalid response for inspection
            invalid_path = day_field_path(week, day, "05_document_for_sparky_INVALID.json")
            write_file(invalid_path, response.text)
            raise ValueError(f"LLM returned invalid JSON: {e}")

    # Write document_for_sparky.json
    doc_path = day_field_path(week, day, "05_document_for_sparky.json")
    write_json(doc_path, doc_data)

    return doc_path


def hydrate_day_from_llm(week: int, day: int, client: LLMClient) -> Dict[str, Any]:
    """
    Generate all day content (fields + document) using LLM.

    Args:
        week: Week number (1-36)
        day: Day number (1-4)
        client: LLM client instance

    Returns:
        Dictionary with paths and status
    """
    field_paths = generate_day_fields(week, day, client)
    doc_path = generate_day_document(week, day, client)

    return {
        "week": week,
        "day": day,
        "field_paths": [str(p) for p in field_paths],
        "document_path": str(doc_path),
        "status": "success"
    }
