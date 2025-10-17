#!/usr/bin/env python3
"""
TEQUILA Week Generator CLI

Usage:
    gen 3              # Generate Week 3
    gen 3,5,7          # Generate Weeks 3, 5, and 7
    gen 3-10           # Generate Weeks 3 through 10
    gen 1-5,11-15      # Generate Weeks 1-5 and 11-15
"""

import sys
import subprocess
from pathlib import Path


def parse_week_spec(spec: str) -> list[int]:
    """
    Parse week specification into list of week numbers.

    Examples:
        "3" -> [3]
        "3,5,7" -> [3, 5, 7]
        "3-10" -> [3, 4, 5, 6, 7, 8, 9, 10]
        "1-3,5,7-9" -> [1, 2, 3, 5, 7, 8, 9]
    """
    weeks = set()

    # Split by comma
    parts = spec.split(',')

    for part in parts:
        part = part.strip()

        # Check if it's a range
        if '-' in part:
            start, end = part.split('-', 1)
            start = int(start.strip())
            end = int(end.strip())

            if start > end:
                raise ValueError(f"Invalid range: {start}-{end} (start > end)")
            if start < 1 or end > 35:
                raise ValueError(f"Week numbers must be between 1 and 35")

            weeks.update(range(start, end + 1))
        else:
            # Single week
            week = int(part)
            if week < 1 or week > 35:
                raise ValueError(f"Week number must be between 1 and 35, got {week}")
            weeks.add(week)

    return sorted(list(weeks))


def generate_weeks(weeks: list[int]):
    """Generate specified weeks using the main CLI."""
    # Get the project root (steel directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent

    print(f"Generating {len(weeks)} week(s): {', '.join(map(str, weeks))}")
    print("=" * 80)

    for week in weeks:
        print(f"\n📚 Generating Week {week}...")

        # Run the main generator
        cmd = [
            sys.executable,
            "-m",
            "src.cli.generate_all_weeks",
            "--week",
            str(week)
        ]

        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=False
        )

        if result.returncode != 0:
            print(f"❌ Failed to generate Week {week}")
            return result.returncode

        print(f"✅ Week {week} complete")

    print("\n" + "=" * 80)
    print(f"✨ Successfully generated {len(weeks)} week(s)!")
    return 0


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        print("\nError: No week specification provided")
        print("\nExamples:")
        print("  gen 3              # Generate Week 3")
        print("  gen 3,5,7          # Generate Weeks 3, 5, and 7")
        print("  gen 3-10           # Generate Weeks 3 through 10")
        print("  gen 1-5,11-15      # Generate Weeks 1-5 and 11-15")
        return 1

    spec = sys.argv[1]

    try:
        weeks = parse_week_spec(spec)
        return generate_weeks(weeks)
    except ValueError as e:
        print(f"Error: {e}")
        print("\nValid formats:")
        print("  - Single week: 3")
        print("  - Multiple weeks: 3,5,7")
        print("  - Range: 3-10")
        print("  - Mixed: 1-3,5,7-9")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
