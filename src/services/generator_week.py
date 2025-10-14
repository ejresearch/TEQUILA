"""Week structure generation service."""
from pathlib import Path
from typing import List
from .storage import (
    week_dir,
    week_spec_dir,
    role_context_dir,
    WEEK_SPEC_PARTS,
    ROLE_CONTEXT_PARTS,
    write_file,
    write_json
)


def get_template_path(template_type: str) -> Path:
    """Get the base path for template files."""
    return Path(__file__).parent.parent / "templates" / "week_kit" / template_type


def scaffold_week(week_number: int) -> Path:
    """
    Create the complete directory structure for a week.

    Creates:
    - Week_Spec/ directory with all 12 part files
    - Role_Context/ directory with all 7 part files
    - activities/ directory (empty, days added separately)

    Returns the path to the week directory.
    """
    week_path = week_dir(week_number)

    # Create Week_Spec directory and files
    spec_dir = week_spec_dir(week_number)
    spec_dir.mkdir(parents=True, exist_ok=True)

    template_spec_dir = get_template_path("spec_parts")
    for part in WEEK_SPEC_PARTS:
        template_path = template_spec_dir / part
        target_path = spec_dir / part

        if template_path.exists():
            content = template_path.read_text(encoding="utf-8")
            # Replace template variables
            content = content.replace("{week_number}", str(week_number))
            content = content.replace("{next_week_number}", str(week_number + 1))
            target_path.write_text(content, encoding="utf-8")
        else:
            # Create empty placeholder
            if part.endswith(".json"):
                write_json(target_path, {})
            else:
                write_file(target_path, "")

    # Create Role_Context directory and files
    context_dir = role_context_dir(week_number)
    context_dir.mkdir(parents=True, exist_ok=True)

    template_context_dir = get_template_path("role_context_parts")
    for part in ROLE_CONTEXT_PARTS:
        template_path = template_context_dir / part
        target_path = context_dir / part

        if template_path.exists():
            content = template_path.read_text(encoding="utf-8")
            target_path.write_text(content, encoding="utf-8")
        else:
            # Create empty JSON placeholder
            write_json(target_path, {})

    # Create activities directory (days will be added separately)
    activities_dir = week_path / "activities"
    activities_dir.mkdir(parents=True, exist_ok=True)

    # Create assets directory with placeholder files
    assets_dir = week_path / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    # Create placeholder asset files
    asset_files = [
        "ChantChart.txt",
        "Glossary.txt",
        "Copywork.txt",
        "QuizPacket.txt",
        "TeacherKey.txt",
        "VirtueEntry.txt"
    ]

    for asset_file in asset_files:
        asset_path = assets_dir / asset_file
        write_file(asset_path, f"# {asset_file.replace('.txt', '')} - Week {week_number}\n\n")

    return week_path


def scaffold_all_weeks(num_weeks: int = 36) -> List[Path]:
    """
    Scaffold all weeks in the curriculum.

    Args:
        num_weeks: Number of weeks to scaffold (default: 36)

    Returns:
        List of paths to created week directories.
    """
    week_paths = []
    for week_num in range(1, num_weeks + 1):
        week_path = scaffold_week(week_num)
        week_paths.append(week_path)

    return week_paths
