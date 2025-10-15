#!/usr/bin/env python3
"""Test script to generate Day 1 only."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pathlib import Path
from src.services.llm_client import get_client
from src.services.generator_day import generate_day_fields, generate_day_document
from src.services.generator_week import scaffold_week, generate_week_spec_from_outline, generate_role_context, generate_assets
import orjson

def main():
    print("=" * 80)
    print("Testing Day 1 Generation")
    print("=" * 80)

    week = 1
    day = 1

    # Initialize client
    print("\n[1/6] Initializing OpenAI client...")
    client = get_client()
    print("✓ Client initialized")

    # Scaffold week
    print(f"\n[2/6] Scaffolding Week {week}...")
    scaffold_week(week)
    print(f"✓ Week {week} scaffolded")

    # Generate week spec
    print(f"\n[3/6] Generating week specification...")
    try:
        generate_week_spec_from_outline(week, client)
        print("✓ Week spec generated")
    except Exception as e:
        print(f"⚠ Week spec generation had warnings: {str(e)[:100]}")

    # Generate role context
    print(f"\n[4/6] Generating role context...")
    generate_role_context(week, client)
    print("✓ Role context generated")

    # Generate assets
    print(f"\n[5/6] Generating assets...")
    generate_assets(week, client)
    print("✓ Assets generated")

    # Generate Day 1 fields
    print(f"\n[6/6] Generating Day {day} fields...")
    field_paths = generate_day_fields(week, day, client)
    print(f"✓ Generated {len(field_paths)} field files")

    # Generate Day 1 document
    print(f"\nGenerating Day {day} document...")
    doc_path = generate_day_document(week, day, client)
    print(f"✓ Document generated at {doc_path}")

    # Verify files
    print("\n" + "=" * 80)
    print("VERIFICATION")
    print("=" * 80)

    day_dir = Path(f"curriculum/LatinA/Week0{week}/activities/Day{day}")

    files_to_check = [
        "01_class_name.txt",
        "02_summary.md",
        "03_grade_level.txt",
        "04_role_context.json",
        "05_guidelines_for_sparky.md",
        "06_document_for_sparky.json",
        "07_sparkys_greeting.txt"
    ]

    for filename in files_to_check:
        filepath = day_dir / filename
        if filepath.exists():
            size = filepath.stat().st_size
            if size > 10:
                print(f"✓ {filename}: {size} bytes")

                # Show preview for key files
                if filename in ["04_role_context.json", "05_guidelines_for_sparky.md", "07_sparkys_greeting.txt"]:
                    content = filepath.read_text(encoding='utf-8')
                    preview = content[:200].replace('\n', ' ')
                    print(f"  Preview: {preview}...")
            else:
                print(f"✗ {filename}: EMPTY ({size} bytes)")
        else:
            print(f"✗ {filename}: NOT FOUND")

    print("\n" + "=" * 80)
    print("Day 1 generation test complete!")
    print("=" * 80)

if __name__ == "__main__":
    main()
