#!/usr/bin/env python3
"""
TEQUILA Week Viewer CLI

View generated curriculum content without regenerating.

Usage:
    view 1                    # View all Week 1 content
    view 3,5,7                # View Weeks 3, 5, and 7
    view 3-10                 # View Weeks 3 through 10
    view 7.2                  # View Week 7 Day 2 only
    view 7 internal           # View Week 7 internal documents only
    view 8 assets             # View Week 8 assets only
    view 19 class             # View Week 19 class material (all days)
    view 22.2 class           # View Week 22 Day 2 class material only
"""

import sys
import json
from pathlib import Path
from typing import Optional, List


def parse_week_day_spec(spec: str) -> tuple[int, Optional[int]]:
    """
    Parse week.day specification.

    Examples:
        "3" -> (3, None)
        "7.2" -> (7, 2)
        "11.4" -> (11, 4)
    """
    if '.' in spec:
        week_str, day_str = spec.split('.', 1)
        week = int(week_str)
        day = int(day_str)

        if week < 1 or week > 35:
            raise ValueError(f"Week number must be between 1 and 35, got {week}")
        if day < 1 or day > 4:
            raise ValueError(f"Day number must be between 1 and 4, got {day}")

        return week, day
    else:
        week = int(spec)
        if week < 1 or week > 35:
            raise ValueError(f"Week number must be between 1 and 35, got {week}")
        return week, None


def get_curriculum_path() -> Path:
    """Get the curriculum/LatinA path."""
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    return project_root / "curriculum" / "LatinA"


def get_day_folder_name(week: int, day: int) -> str:
    """Get the day folder name (e.g., Day1_3.1)."""
    return f"Day{day}_{week}.{day}"


def print_file_content(file_path: Path, label: str = None):
    """Print file content with a header."""
    if not file_path.exists():
        print(f"  ⚠️  Not found: {file_path.name}")
        return

    header = label or file_path.name
    print(f"\n{'='*80}")
    print(f"📄 {header}")
    print(f"{'='*80}")

    # Handle JSON files
    if file_path.suffix == '.json':
        try:
            with open(file_path) as f:
                data = json.load(f)
            print(json.dumps(data, indent=2))
        except json.JSONDecodeError:
            print(f"⚠️  Invalid JSON in {file_path.name}")
    else:
        # Regular text files
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            print(content)
        except UnicodeDecodeError:
            print(f"⚠️  Binary file: {file_path.name}")


def view_internal_docs(week_path: Path, week: int):
    """View internal documents for a week."""
    internal_path = week_path / "internal_documents"

    if not internal_path.exists():
        print(f"❌ No internal documents found for Week {week}")
        return

    print(f"\n📚 Week {week} - Internal Documents")
    print("="*80)

    # Key files to show
    files = [
        "week_spec.json",
        "week_summary.md",
        "role_context.json",
        "phase0_research.json",
        "generation_log.json"
    ]

    for filename in files:
        file_path = internal_path / filename
        if file_path.exists():
            print_file_content(file_path, f"internal_documents/{filename}")


def view_assets(week_path: Path, week: int):
    """View assets for a week."""
    assets_path = week_path / "assets"

    if not assets_path.exists():
        print(f"❌ No assets found for Week {week}")
        return

    print(f"\n📦 Week {week} - Assets")
    print("="*80)

    for file_path in sorted(assets_path.glob("*")):
        if file_path.is_file():
            print_file_content(file_path, f"assets/{file_path.name}")


def view_day_class_material(day_path: Path, week: int, day: int):
    """View class material for a specific day."""
    if not day_path.exists():
        print(f"❌ Day {day} not found for Week {week}")
        return

    print(f"\n📖 Week {week} Day {day} - Class Material")
    print("="*80)

    # Core class files
    files = [
        "01_class_name.txt",
        "02_summary.md",
        "03_grade_level.txt",
        "07_sparkys_greeting.txt"
    ]

    for filename in files:
        file_path = day_path / filename
        if file_path.exists():
            print_file_content(file_path)

    # Documents for Sparky
    doc_path = day_path / "06_document_for_sparky"
    if doc_path.exists():
        print(f"\n{'='*80}")
        print(f"📝 Week {week} Day {day} - Teacher Support Documents")
        print(f"{'='*80}")

        for file_path in sorted(doc_path.glob("*.txt")):
            print_file_content(file_path, f"06_document_for_sparky/{file_path.name}")


def view_week_class_material(week_path: Path, week: int):
    """View class material for all days in a week."""
    for day in range(1, 5):
        day_folder = get_day_folder_name(week, day)
        day_path = week_path / day_folder

        if day_path.exists():
            view_day_class_material(day_path, week, day)


def view_full_week(week_path: Path, week: int):
    """View all content for a week."""
    print(f"\n🎓 WEEK {week} - COMPLETE VIEW")
    print("="*80)

    # Internal docs
    view_internal_docs(week_path, week)

    # All days
    for day in range(1, 5):
        day_folder = get_day_folder_name(week, day)
        day_path = week_path / day_folder

        if day_path.exists():
            print(f"\n\n{'#'*80}")
            print(f"# DAY {day}")
            print(f"{'#'*80}")
            view_day_class_material(day_path, week, day)

    # Assets
    view_assets(week_path, week)


def view_week(week: int, scope: Optional[str] = None, day: Optional[int] = None):
    """View week content with optional scope filter."""
    curriculum_path = get_curriculum_path()
    week_path = curriculum_path / f"Week{week:02d}"

    if not week_path.exists():
        print(f"❌ Week {week} not found at {week_path}")
        print(f"   Generate it first with: make gen WEEKS={week}")
        return 1

    # Determine what to show
    if day is not None:
        # Specific day
        if scope == "class":
            day_folder = get_day_folder_name(week, day)
            day_path = week_path / day_folder
            view_day_class_material(day_path, week, day)
        else:
            print(f"❌ Unknown scope '{scope}' for day view")
            print(f"   Use: view {week}.{day} class")
            return 1
    elif scope == "internal":
        view_internal_docs(week_path, week)
    elif scope == "assets":
        view_assets(week_path, week)
    elif scope == "class":
        view_week_class_material(week_path, week)
    elif scope is None:
        view_full_week(week_path, week)
    else:
        print(f"❌ Unknown scope: {scope}")
        print(f"   Valid scopes: internal, assets, class")
        return 1

    return 0


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 1

    spec = sys.argv[1]
    scope = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        # Parse week[.day] specification
        week, day = parse_week_day_spec(spec)

        # View the content
        return view_week(week, scope, day)

    except ValueError as e:
        print(f"❌ Error: {e}")
        print("\nValid formats:")
        print("  - Full week: view 3")
        print("  - Specific day: view 7.2")
        print("  - Internal docs: view 7 internal")
        print("  - Assets: view 8 assets")
        print("  - Class material (all days): view 19 class")
        print("  - Class material (one day): view 22.2 class")
        return 1
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
