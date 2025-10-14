"""CLI script to hydrate a specific day from templates."""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.generator_day import scaffold_day


def main():
    """Hydrate a specific day with Flint field files from templates."""
    if len(sys.argv) < 3:
        print("Usage: python -m src.cli.hydrate_day_from_kit <week_number> <day_number>")
        print("Example: python -m src.cli.hydrate_day_from_kit 11 1")
        sys.exit(1)

    try:
        week_number = int(sys.argv[1])
        day_number = int(sys.argv[2])

        if week_number < 1 or week_number > 36:
            print("Error: Week number must be between 1 and 36")
            sys.exit(1)

        if day_number < 1 or day_number > 4:
            print("Error: Day number must be between 1 and 4")
            sys.exit(1)
    except ValueError:
        print("Error: Week and day numbers must be integers")
        sys.exit(1)

    print(f"Hydrating Week {week_number}, Day {day_number}...")

    # Scaffold the specific day
    day_path = scaffold_day(week_number, day_number)

    print(f"✓ Created day structure at: {day_path}")
    print(f"\nFlint fields created:")
    print(f"  ├── 01_class_name.txt")
    print(f"  ├── 02_summary.md")
    print(f"  ├── 03_grade_level.txt")
    print(f"  ├── 04_guidelines_for_sparky.md")
    print(f"  ├── 05_document_for_sparky.json")
    print(f"  └── 06_sparkys_greeting.txt")
    print(f"\n✓ Day {day_number} hydrated successfully!")


if __name__ == "__main__":
    main()
