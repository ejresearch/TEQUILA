"""CLI script to validate and export a week."""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.validator import validate_week
from src.services.exporter import export_week_to_zip


def main():
    """Validate a week and export it to a zip file if valid."""
    if len(sys.argv) < 2:
        print("Usage: python -m src.cli.validate_export_week <week_number>")
        print("Example: python -m src.cli.validate_export_week 11")
        sys.exit(1)

    try:
        week_number = int(sys.argv[1])
        if week_number < 1 or week_number > 36:
            print("Error: Week number must be between 1 and 36")
            sys.exit(1)
    except ValueError:
        print("Error: Week number must be an integer")
        sys.exit(1)

    print(f"Validating Week {week_number}...")
    print("=" * 60)

    # Run validation
    result = validate_week(week_number)

    # Display errors
    if result.errors:
        print(f"\n✗ ERRORS ({len(result.errors)}):")
        for error in result.errors:
            print(f"  {error}")

    # Display warnings
    if result.warnings:
        print(f"\n⚠ WARNINGS ({len(result.warnings)}):")
        for warning in result.warnings:
            print(f"  {warning}")

    # Display info messages
    if result.info:
        print(f"\nℹ INFO ({len(result.info)}):")
        for info in result.info:
            print(f"  {info}")

    print("\n" + "=" * 60)
    print(f"Validation Summary: {result.summary()}")

    # Export if validation passed
    if result.is_valid():
        print(f"\n✓ Validation PASSED\n")
        print(f"Exporting Week {week_number} to zip...")

        try:
            zip_path = export_week_to_zip(week_number)
            print(f"\n✓ Export successful!")
            print(f"Location: {zip_path}")
            print(f"Size: {zip_path.stat().st_size / 1024:.2f} KB")
            sys.exit(0)
        except Exception as e:
            print(f"\n✗ Export failed: {e}")
            sys.exit(1)
    else:
        print(f"\n✗ Validation FAILED - Week {week_number} was not exported")
        print(f"Fix the {len(result.errors)} error(s) above and try again.")
        sys.exit(1)


if __name__ == "__main__":
    main()
