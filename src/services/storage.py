"""Storage service for curriculum file operations."""
import json
from pathlib import Path
from typing import Dict, Any, Optional


# Field names for Day activities (Flint fields)
DAY_FIELDS = [
    "01_class_name.txt",
    "02_summary.md",
    "03_grade_level.txt",
    "04_guidelines_for_sparky.md",
    "05_document_for_sparky.json",
    "06_sparkys_greeting.txt"
]

# Week spec parts
WEEK_SPEC_PARTS = [
    "01_metadata.json",
    "02_objectives.json",
    "03_vocabulary.json",
    "04_grammar_focus.md",
    "05_chant.json",
    "06_sessions_week_view.json",
    "07_assessment.json",
    "08_assets_index.json",
    "09_spiral_links.json",
    "10_interleaving_plan.md",
    "11_misconception_watchlist.json",
    "12_preview_next_week.md"
]

# Role context parts
ROLE_CONTEXT_PARTS = [
    "identity.json",
    "student_profile.json",
    "daily_cycle.json",
    "reinforcement_method.json",
    "feedback_style.json",
    "success_criteria.json",
    "knowledge_recycling.json"
]


def get_curriculum_base() -> Path:
    """Get the base curriculum directory."""
    return Path(__file__).parent.parent.parent / "curriculum" / "LatinA"


def week_dir(week_number: int) -> Path:
    """Get the directory path for a specific week."""
    return get_curriculum_base() / f"Week{week_number:02d}"


def day_dir(week_number: int, day_number: int) -> Path:
    """Get the directory path for a specific day's activities."""
    return week_dir(week_number) / "activities" / f"Day{day_number}"


def week_spec_dir(week_number: int) -> Path:
    """Get the directory path for week specification parts."""
    return week_dir(week_number) / "Week_Spec"


def role_context_dir(week_number: int) -> Path:
    """Get the directory path for role context parts."""
    return week_dir(week_number) / "Role_Context"


def day_field_path(week_number: int, day_number: int, field_name: str) -> Path:
    """Get the file path for a specific day field."""
    return day_dir(week_number, day_number) / field_name


def week_spec_part_path(week_number: int, part_name: str) -> Path:
    """Get the file path for a specific week spec part."""
    return week_spec_dir(week_number) / part_name


def role_context_part_path(week_number: int, part_name: str) -> Path:
    """Get the file path for a specific role context part."""
    return role_context_dir(week_number) / part_name


def read_file(path: Path) -> str:
    """Read text content from a file."""
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    return path.read_text(encoding="utf-8")


def write_file(path: Path, content: str) -> None:
    """Write text content to a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def read_json(path: Path) -> Dict[str, Any]:
    """Read and parse JSON from a file."""
    content = read_file(path)
    return json.loads(content)


def write_json(path: Path, data: Dict[str, Any]) -> None:
    """Write JSON data to a file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")


def compile_day_flint_bundle(week_number: int, day_number: int) -> Dict[str, Any]:
    """
    Compile all six Flint field files into a single JSON bundle.

    Returns a dictionary with field names as keys and their content as values.
    """
    bundle = {}

    for field in DAY_FIELDS:
        field_path = day_field_path(week_number, day_number, field)
        if not field_path.exists():
            bundle[field] = None
            continue

        # Read based on file extension
        if field.endswith(".json"):
            bundle[field] = read_json(field_path)
        else:
            bundle[field] = read_file(field_path)

    return bundle


def compile_week_spec(week_number: int) -> Dict[str, Any]:
    """
    Compile all week spec parts into a single JSON structure.

    Returns a dictionary with part names as keys and their content as values.
    """
    spec = {}

    for part in WEEK_SPEC_PARTS:
        part_path = week_spec_part_path(week_number, part)
        if not part_path.exists():
            spec[part] = None
            continue

        # Read based on file extension
        if part.endswith(".json"):
            spec[part] = read_json(part_path)
        else:
            spec[part] = read_file(part_path)

    return spec


def compile_role_context(week_number: int) -> Dict[str, Any]:
    """
    Compile all role context parts into a single JSON structure.

    Returns a dictionary with part names as keys and their content as values.
    """
    context = {}

    for part in ROLE_CONTEXT_PARTS:
        part_path = role_context_part_path(week_number, part)
        if not part_path.exists():
            context[part] = None
            continue

        # All role context parts are JSON
        context[part] = read_json(part_path)

    return context


def save_compiled_week_spec(week_number: int) -> Path:
    """
    Compile and save the complete week spec to 99_compiled_week_spec.json.

    Returns the path to the saved file.
    """
    spec = compile_week_spec(week_number)
    compiled_path = week_spec_part_path(week_number, "99_compiled_week_spec.json")
    write_json(compiled_path, spec)
    return compiled_path


def save_compiled_role_context(week_number: int) -> Path:
    """
    Compile and save the complete role context to 99_compiled_role_context.json.

    Returns the path to the saved file.
    """
    context = compile_role_context(week_number)
    compiled_path = role_context_part_path(week_number, "99_compiled_role_context.json")
    write_json(compiled_path, context)
    return compiled_path
