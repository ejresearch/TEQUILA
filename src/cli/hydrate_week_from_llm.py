#!/usr/bin/env python3
"""CLI tool to hydrate a complete week using LLM generation."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import get_llm_client
from src.services.generator_week import (
    generate_week_spec_from_outline,
    generate_role_context,
    generate_assets
)
from src.services.generator_day import hydrate_day_from_llm
from src.services.validator import validate_week


def main():
    """Generate all content for a complete week using LLM."""
    if len(sys.argv) != 2:
        print("Usage: python -m src.cli.hydrate_week_from_llm WEEK")
        print("Example: python -m src.cli.hydrate_week_from_llm 11")
        sys.exit(1)

    try:
        week = int(sys.argv[1])

        if not (1 <= week <= 36):
            print(f"Error: Week must be 1-36, got {week}")
            sys.exit(1)

    except ValueError:
        print("Error: WEEK must be an integer")
        sys.exit(1)

    print(f"Hydrating Week {week} using LLM...")
    print("=" * 60)

    try:
        client = get_llm_client()

        # Generate week-level content
        print("\n[1/6] Generating week specification...")
        spec_path = generate_week_spec_from_outline(week, client)
        print(f"  ✓ {spec_path}")

        print("\n[2/6] Generating role context...")
        role_path = generate_role_context(week, client)
        print(f"  ✓ {role_path}")

        print("\n[3/6] Generating assets...")
        asset_paths = generate_assets(week, client)
        for path in asset_paths:
            print(f"  ✓ {path}")

        # Generate day-level content
        for day in range(1, 5):
            print(f"\n[{3+day}/6] Generating Day {day}...")
            day_result = hydrate_day_from_llm(week, day, client)
            print(f"  ✓ Fields: {len(day_result['field_paths'])} files")
            print(f"  ✓ Document: {day_result['document_path']}")

        # Validate
        print("\n" + "=" * 60)
        print("Running validation...")
        result = validate_week(week)
        print(result.summary())

        if result.is_valid():
            print("\n✓ Week hydration complete and valid!")
        else:
            print("\n⚠ Week hydration complete but has validation errors.")
            print("Review the errors above.")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
