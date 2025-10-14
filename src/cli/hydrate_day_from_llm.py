#!/usr/bin/env python3
"""CLI tool to hydrate a single day using LLM generation."""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.config import get_llm_client
from src.services.generator_day import hydrate_day_from_llm


def main():
    """Generate all content for a single day using LLM."""
    if len(sys.argv) != 3:
        print("Usage: python -m src.cli.hydrate_day_from_llm WEEK DAY")
        print("Example: python -m src.cli.hydrate_day_from_llm 11 1")
        sys.exit(1)

    try:
        week = int(sys.argv[1])
        day = int(sys.argv[2])

        if not (1 <= week <= 36):
            print(f"Error: Week must be 1-36, got {week}")
            sys.exit(1)

        if not (1 <= day <= 4):
            print(f"Error: Day must be 1-4, got {day}")
            sys.exit(1)

    except ValueError:
        print("Error: WEEK and DAY must be integers")
        sys.exit(1)

    print(f"Hydrating Week {week} Day {day} using LLM...")
    print("-" * 60)

    try:
        client = get_llm_client()
        result = hydrate_day_from_llm(week, day, client)

        print(f"\n✓ Success!")
        print(f"\nGenerated files:")
        for path in result["field_paths"]:
            print(f"  - {path}")
        print(f"  - {result['document_path']}")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
