"""CLI script to build complete week structure."""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.generator_week import scaffold_week
from src.services.generator_day import scaffold_week_days


def main():
    """Build a complete week kit with all structure and placeholder files."""
    if len(sys.argv) < 2:
        print("Usage: python -m src.cli.build_week_kit <week_number>")
        print("Example: python -m src.cli.build_week_kit 11")
        sys.exit(1)

    try:
        week_number = int(sys.argv[1])
        if week_number < 1 or week_number > 36:
            print("Error: Week number must be between 1 and 36")
            sys.exit(1)
    except ValueError:
        print("Error: Week number must be an integer")
        sys.exit(1)

    print(f"Building week {week_number} kit...")

    # Scaffold week structure (Week_Spec, Role_Context, assets)
    week_path = scaffold_week(week_number)
    print(f"✓ Created week structure at: {week_path}")

    # Scaffold all four days
    day_paths = scaffold_week_days(week_number)
    print(f"✓ Created {len(day_paths)} day activity folders")

    print(f"\n✓ Week {week_number} kit successfully created!")
    print(f"\nStructure:")
    print(f"  {week_path}/")
    print(f"    ├── Week_Spec/")
    print(f"    ├── Role_Context/")
    print(f"    ├── activities/")
    print(f"    │   ├── Day1/ (6 Flint fields)")
    print(f"    │   ├── Day2/ (6 Flint fields)")
    print(f"    │   ├── Day3/ (6 Flint fields)")
    print(f"    │   └── Day4/ (6 Flint fields)")
    print(f"    └── assets/")


if __name__ == "__main__":
    main()
