#!/usr/bin/env python3
"""
Migration script: Convert 6-field day layouts to 7-field architecture.

This script:
1. Detects all days with legacy 6-field layout
2. Creates default role_context (04_role_context.json) from week-level Role_Context
3. Renames/moves existing fields to new indices:
   - 04_guidelines_for_sparky.md → 05_guidelines_for_sparky.md
   - 05_document_for_sparky.json → 06_document_for_sparky.json
   - 06_sparkys_greeting.txt → 07_sparkys_greeting.txt
4. Validates migrated structure
5. Creates migration provenance file

Usage:
    python -m src.cli.migrate_to_7field --week 1            # Migrate Week 1
    python -m src.cli.migrate_to_7field --all              # Migrate all weeks
    python -m src.cli.migrate_to_7field --dry-run --all    # Preview changes
"""
import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.services.storage import (
    week_dir,
    day_dir,
    day_field_path,
    role_context_part_path,
    detect_day_layout,
    write_json,
    read_json,
    FIELD_MIGRATION_MAP
)
from src.services.validator import validate_day_fields


def derive_default_role_context(week_number: int, day_number: int) -> Dict[str, Any]:
    """
    Derive a default role_context from week-level Role_Context.

    Args:
        week_number: Week number
        day_number: Day number (1-4)

    Returns:
        role_context dict with defaults
    """
    # Try to read week-level identity
    identity_path = role_context_part_path(week_number, "identity.json")
    sparky_role = "encouraging Latin guide"

    if identity_path.exists():
        try:
            identity = read_json(identity_path)
            sparky_role = identity.get("character_name", "Sparky the Latin Guide")
        except Exception:
            pass

    # Day-specific focus modes
    focus_modes = {
        1: "introduction_and_exploration",
        2: "practice_and_reinforcement",
        3: "application_and_extension",
        4: "review_and_spiral"
    }

    return {
        "sparky_role": sparky_role,
        "focus_mode": focus_modes.get(day_number, "general"),
        "hints_enabled": True,
        "spiral_emphasis": [] if day_number < 2 else [f"Week {max(1, week_number - 1)} content"],
        "encouragement_triggers": ["first_attempt", "corrected_error", "progress_shown"],
        "__migration": {
            "migrated_at": datetime.utcnow().isoformat() + "Z",
            "migration_script": "migrate_to_7field.py",
            "source": "week_role_context_default"
        }
    }


def migrate_day(week_number: int, day_number: int, dry_run: bool = False) -> Dict[str, Any]:
    """
    Migrate a single day from 6-field to 7-field layout.

    Args:
        week_number: Week number
        day_number: Day number (1-4)
        dry_run: If True, only preview changes without modifying files

    Returns:
        Migration result dict with status and actions taken
    """
    result = {
        "week": week_number,
        "day": day_number,
        "status": "skipped",
        "actions": [],
        "errors": []
    }

    layout = detect_day_layout(week_number, day_number)

    if layout == "7field":
        result["status"] = "already_7field"
        result["actions"].append("No migration needed (already 7-field)")
        return result

    day_path = day_dir(week_number, day_number)
    if not day_path.exists():
        result["status"] = "error"
        result["errors"].append("Day directory does not exist")
        return result

    # Step 1: Create role_context
    role_context_path = day_field_path(week_number, day_number, "04_role_context.json")
    role_context_data = derive_default_role_context(week_number, day_number)

    if not dry_run:
        write_json(role_context_path, role_context_data)
    result["actions"].append(f"Created {role_context_path.name}")

    # Step 2: Rename/move fields 04, 05, 06 → 05, 06, 07
    for old_name, new_name in FIELD_MIGRATION_MAP.items():
        old_path = day_field_path(week_number, day_number, old_name)
        new_path = day_field_path(week_number, day_number, new_name)

        if old_path.exists():
            if not dry_run:
                old_path.rename(new_path)
            result["actions"].append(f"Renamed {old_name} → {new_name}")
        else:
            result["errors"].append(f"Expected field {old_name} not found")

    # Step 3: Validate migrated structure
    if not dry_run:
        validation = validate_day_fields(week_number, day_number)
        if validation.is_valid():
            result["status"] = "migrated_success"
        else:
            result["status"] = "migrated_with_warnings"
            result["errors"].extend([str(e) for e in validation.errors])
    else:
        result["status"] = "dry_run_success"

    return result


def migrate_week(week_number: int, dry_run: bool = False) -> List[Dict[str, Any]]:
    """Migrate all days in a week."""
    results = []
    for day in range(1, 5):
        result = migrate_day(week_number, day, dry_run)
        results.append(result)
    return results


def main():
    parser = argparse.ArgumentParser(description="Migrate TEQUILA days from 6-field to 7-field layout")
    parser.add_argument("--week", type=int, help="Week number to migrate (1-36)")
    parser.add_argument("--all", action="store_true", help="Migrate all weeks")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without modifying files")

    args = parser.parse_args()

    if args.all:
        weeks = range(1, 37)
    elif args.week:
        weeks = [args.week]
    else:
        parser.error("Must specify --week or --all")

    for week in weeks:
        print(f"\n{'[DRY RUN] ' if args.dry_run else ''}Migrating Week {week}...")
        results = migrate_week(week, args.dry_run)
        for res in results:
            print(f"  Day {res['day']}: {res['status']}")
            for action in res["actions"]:
                print(f"    ✓ {action}")
            for error in res["errors"]:
                print(f"    ✗ {error}")


if __name__ == "__main__":
    main()
