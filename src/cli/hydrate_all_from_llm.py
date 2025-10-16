#!/usr/bin/env python3
"""CLI tool to hydrate all 36 weeks using LLM generation."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import get_llm_client
from src.services.generator_week import (
    scaffold_week,
    generate_week_planning
)
from src.services.generator_day import hydrate_day_from_llm


def main():
    """Generate all content for all 36 weeks using LLM (Two-Phase Generation)."""
    print("Hydrating all 36 weeks using LLM (Two-Phase Generation)...")
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
                # Scaffold week
                print("  [1/6] Scaffolding...")
                scaffold_week(week)

                # PHASE 1: Generate week planning
                print("  [2/6] PHASE 1: Generating week planning (internal_documents/)...")
                generate_week_planning(week, client)

                # PHASE 2: Generate days from planning
                for day in range(1, 5):
                    print(f"  [{2+day}/6] PHASE 2: Generating Day {day}...")
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
