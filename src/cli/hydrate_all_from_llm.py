#!/usr/bin/env python3
"""CLI tool to hydrate all 36 weeks using LLM generation."""
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


def main():
    """Generate all content for all 36 weeks using LLM."""
    print("Hydrating all 36 weeks using LLM...")
    print("=" * 60)
    print("WARNING: This will take a significant amount of time and API credits.")
    print("=" * 60)

    response = input("\nContinue? (y/N): ")
    if response.lower() != 'y':
        print("Cancelled.")
        sys.exit(0)

    try:
        client = get_llm_client()
        success_count = 0
        error_weeks = []

        for week in range(1, 37):
            print(f"\n{'=' * 60}")
            print(f"Week {week}/36")
            print('=' * 60)

            try:
                # Generate week content
                print("  [1/6] Week spec...")
                generate_week_spec_from_outline(week, client)

                print("  [2/6] Role context...")
                generate_role_context(week, client)

                print("  [3/6] Assets...")
                generate_assets(week, client)

                # Generate days
                for day in range(1, 5):
                    print(f"  [{3+day}/6] Day {day}...")
                    hydrate_day_from_llm(week, day, client)

                print(f"  ✓ Week {week} complete")
                success_count += 1

            except Exception as e:
                print(f"  ✗ Week {week} failed: {e}")
                error_weeks.append(week)

        # Summary
        print("\n" + "=" * 60)
        print("SUMMARY")
        print("=" * 60)
        print(f"Successful: {success_count}/36")
        if error_weeks:
            print(f"Failed weeks: {', '.join(map(str, error_weeks))}")
        else:
            print("All weeks generated successfully!")

    except Exception as e:
        print(f"\n✗ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
