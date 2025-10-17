#!/usr/bin/env python3
"""
Import sample weeks from Desktop into curriculum structure.

Converts from flat Desktop format to proper curriculum structure:
- Renames day folders from W.D to Day{D}_{W}.{D}
- Moves 06_document_for_sparky_*.txt files into 06_document_for_sparky/ directory
- Keeps field 05 as JSON (no conversion needed)
"""
import shutil
from pathlib import Path

# Source directories on Desktop
SAMPLE_WEEKS = [
    ("/Users/elle_jansick/Desktop/Week 1", 1),
    ("/Users/elle_jansick/Desktop/Week 11", 11),
    ("/Users/elle_jansick/Desktop/Week 12", 12),
    ("/Users/elle_jansick/Desktop/Week 13", 13),
    ("/Users/elle_jansick/Desktop/Week 14", 14),
    ("/Users/elle_jansick/Desktop/Week 15", 15),
]

# Target base directory
CURRICULUM_BASE = Path("/Users/elle_jansick/steel/curriculum/LatinA")

# Document file mapping
DOCUMENT_FILES = [
    "spiral_review_document.txt",
    "weekly_topics_document.txt",
    "virtue_and_faith_document.txt",
    "vocabulary_key_document.txt",
    "chant_chart_document.txt",
    "teacher_voice_tips_document.txt"
]


def import_week(source_dir: str, week_number: int):
    """Import a single week from Desktop to curriculum."""
    source_path = Path(source_dir)
    target_week_dir = CURRICULUM_BASE / f"Week{week_number:02d}"

    print(f"\n{'='*60}")
    print(f"Importing Week {week_number}")
    print(f"{'='*60}")
    print(f"Source: {source_path}")
    print(f"Target: {target_week_dir}")

    # Create week directory
    target_week_dir.mkdir(parents=True, exist_ok=True)

    # Import each day
    for day in range(1, 5):
        source_day_dir = source_path / f"{week_number}.{day}"
        if not source_day_dir.exists():
            print(f"  ⚠ Day {day}: Source not found at {source_day_dir}")
            continue

        # Create target day directory with new naming convention
        target_day_dir = target_week_dir / f"Day{day}_{week_number}.{day}"
        target_day_dir.mkdir(parents=True, exist_ok=True)

        print(f"\n  Day {day}: {source_day_dir.name} → {target_day_dir.name}")

        # Copy standard fields (01-05, 07)
        standard_fields = [
            "01_class_name.txt",
            "02_summary.md",
            "03_grade_level.txt",
            "04_role_context.json",
            "05_guidelines_for_sparky.json",
            "07_sparkys_greeting.txt"
        ]

        for field in standard_fields:
            source_file = source_day_dir / field
            if source_file.exists():
                target_file = target_day_dir / field
                shutil.copy2(source_file, target_file)
                print(f"    ✓ {field}")
            else:
                print(f"    ⚠ {field} not found")

        # Handle field 06: Create directory and move document files
        doc_dir = target_day_dir / "06_document_for_sparky"
        doc_dir.mkdir(parents=True, exist_ok=True)

        for doc_file in DOCUMENT_FILES:
            # Source files are named: 06_document_for_sparky_<name>.txt
            source_file = source_day_dir / f"06_document_for_sparky_{doc_file}"
            if source_file.exists():
                target_file = doc_dir / doc_file
                shutil.copy2(source_file, target_file)
                print(f"    ✓ 06_document_for_sparky/{doc_file}")
            else:
                print(f"    ⚠ 06_document_for_sparky_{doc_file} not found")

    print(f"\n✓ Week {week_number} import complete!")


def main():
    """Import all sample weeks."""
    print("="*60)
    print("IMPORTING SAMPLE WEEKS")
    print("="*60)
    print(f"Target: {CURRICULUM_BASE}")
    print(f"Weeks to import: 11, 12, 13, 14, 15")
    print("="*60)

    for source_dir, week_num in SAMPLE_WEEKS:
        if not Path(source_dir).exists():
            print(f"\n⚠ Skipping Week {week_num}: {source_dir} not found")
            continue

        try:
            import_week(source_dir, week_num)
        except Exception as e:
            print(f"\n✗ Error importing Week {week_num}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*60)
    print("IMPORT COMPLETE")
    print("="*60)
    print("\nNext steps:")
    print("  1. Verify imported weeks: ls curriculum/LatinA/Week{11,13,15}")
    print("  2. Validate structure: python -m src.cli.validate_week 11")
    print("  3. Export to ZIP: python -m src.services.exporter 11")


if __name__ == "__main__":
    main()
