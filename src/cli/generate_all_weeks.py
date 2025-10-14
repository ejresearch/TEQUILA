"""
Generate all weeks for Latin A v1.0 Pilot (35 weeks total).

This is the main CLI entrypoint for generating the complete curriculum.
Includes retry logic, validation, cost tracking, and export functionality.

Usage:
    python -m src.cli.generate_all_weeks --from 1 --to 35
    python -m src.cli.generate_all_weeks --from 1 --to 2  # Test with 2 weeks
    python -m src.cli.generate_all_weeks --week 11        # Single week
"""
import argparse
import sys
from pathlib import Path
from typing import Optional

from ..config import get_llm_client, settings
from ..services.generator_week import scaffold_week
from ..services.generator_day import hydrate_day_from_llm
from ..services.validator import validate_week
from ..services.exporter import export_week_to_zip
from ..services.usage_tracker import get_tracker


def print_banner():
    """Print TEQUILA banner."""
    print("=" * 80)
    print("TEQUILA: AI Latin A Curriculum Generator (v1.0 Pilot)")
    print("=" * 80)
    print(f"Target: 35 weeks × 4 days = 140 lessons")
    print(f"Model: OpenAI GPT-4o")
    print(f"Max retries per day: {settings.max_retries}")
    print(f"Spiral content requirement: ≥{settings.prior_content_min_percentage}% prior weeks")
    print("=" * 80)
    print()


def generate_week(week_number: int, client, export: bool = True) -> bool:
    """
    Generate a complete week with all days, validate, and optionally export.

    Args:
        week_number: Week number (1-35)
        client: LLM client instance
        export: Whether to export to ZIP after generation

    Returns:
        True if successful, False if aborted
    """
    print(f"\n{'─' * 80}")
    print(f"WEEK {week_number:02d}")
    print(f"{'─' * 80}")

    # Scaffold week structure
    print(f"  Scaffolding Week {week_number}...")
    week_path = scaffold_week(week_number)
    print(f"  ✓ Created structure at {week_path}")

    # Generate all 4 days
    for day in range(1, 5):
        print(f"\n  Day {day}:")
        try:
            result = hydrate_day_from_llm(week_number, day, client)
            if result.get("status") == "success":
                print(f"    ✓ Generated all fields successfully")
            else:
                print(f"    ⚠ Generation completed with warnings")
        except ValueError as e:
            if "aborted by user" in str(e):
                print(f"    ✗ Generation aborted by user")
                return False
            raise
        except Exception as e:
            print(f"    ✗ Generation failed: {e}")
            raise

    # Validate week
    print(f"\n  Validating Week {week_number}...")
    validation = validate_week(week_number)
    print(f"  {validation.summary()}")

    if not validation.is_valid():
        print(f"  ⚠ Validation errors found (see logs)")
        for error in validation.errors[:5]:  # Show first 5 errors
            print(f"    - {error}")

    # Export to ZIP
    if export:
        print(f"\n  Exporting Week {week_number}...")
        try:
            zip_path = export_week_to_zip(week_number)
            zip_size_kb = zip_path.stat().st_size / 1024
            print(f"  ✓ Exported to {zip_path.name} ({zip_size_kb:.1f} KB)")
        except Exception as e:
            print(f"  ✗ Export failed: {e}")

    # Show cost estimate
    tracker = get_tracker()
    summary = tracker.get_summary()
    print(f"\n  Cost estimate: ${summary.get('estimated_cost_usd', 0):.4f}")

    return True


def main():
    """Main entrypoint for generate_all_weeks CLI."""
    parser = argparse.ArgumentParser(
        description="Generate Latin A curriculum weeks using OpenAI GPT-4o"
    )
    parser.add_argument(
        "--from",
        dest="start_week",
        type=int,
        default=1,
        help="Starting week number (default: 1)"
    )
    parser.add_argument(
        "--to",
        dest="end_week",
        type=int,
        default=35,
        help="Ending week number (default: 35)"
    )
    parser.add_argument(
        "--week",
        type=int,
        help="Generate a single week (overrides --from/--to)"
    )
    parser.add_argument(
        "--no-export",
        action="store_true",
        help="Skip ZIP export after generation"
    )

    args = parser.parse_args()

    # Determine week range
    if args.week:
        start_week = args.week
        end_week = args.week
    else:
        start_week = args.start_week
        end_week = args.end_week

    # Validate range
    if start_week < 1 or end_week > 35:
        print("Error: Week numbers must be between 1 and 35 (v1.0 Pilot scope)")
        sys.exit(1)

    if start_week > end_week:
        print("Error: Start week must be <= end week")
        sys.exit(1)

    # Print banner
    print_banner()

    # Initialize LLM client
    print("Initializing OpenAI GPT-4o client...")
    try:
        client = get_llm_client()
        print(f"✓ Connected to OpenAI (model: {settings.MODEL_NAME})")
    except ValueError as e:
        print(f"✗ Failed to initialize LLM client: {e}")
        print("\nMake sure OPENAI_API_KEY is set in .env file")
        sys.exit(1)

    # Create logs directory
    settings.logs_path.mkdir(parents=True, exist_ok=True)
    print(f"✓ Logs will be saved to: {settings.logs_path}")

    # Generate weeks
    print(f"\nGenerating weeks {start_week} to {end_week}...")
    successful_weeks = []
    failed_weeks = []

    for week_num in range(start_week, end_week + 1):
        try:
            success = generate_week(week_num, client, export=not args.no_export)
            if success:
                successful_weeks.append(week_num)
            else:
                print(f"\n✗ Week {week_num} generation aborted by user")
                failed_weeks.append(week_num)
                break  # Stop on user abort
        except KeyboardInterrupt:
            print(f"\n\n⚠ Generation interrupted by user (Ctrl+C)")
            break
        except Exception as e:
            print(f"\n✗ Week {week_num} failed with error: {e}")
            failed_weeks.append(week_num)

            # Ask user whether to continue
            response = input("\nContinue with next week? (y/n): ").strip().lower()
            if response != 'y':
                break

    # Final summary
    print(f"\n{'=' * 80}")
    print("GENERATION COMPLETE")
    print(f"{'=' * 80}")
    print(f"Successful: {len(successful_weeks)} weeks")
    if failed_weeks:
        print(f"Failed/Aborted: {len(failed_weeks)} weeks - {failed_weeks}")

    # Final cost summary
    tracker = get_tracker()
    summary = tracker.get_summary()
    print(f"\nTotal cost estimate: ${summary.get('estimated_cost_usd', 0):.4f}")
    print(f"Total tokens: {summary.get('total_tokens', 0):,}")

    print(f"\nLogs saved to: {settings.logs_path}")
    if not args.no_export:
        print(f"Exports saved to: {settings.exports_path}")

    print("\nNext steps:")
    print("  1. Review logs/ for any retry or validation issues")
    print("  2. Validate exports with: python -m src.cli.validate_export_week <week>")
    print("  3. Review generated content for quality")
    print("=" * 80)


if __name__ == "__main__":
    main()
