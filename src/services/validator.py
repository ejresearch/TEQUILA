"""Validation service for curriculum content."""
import json
from pathlib import Path
from typing import Dict, List, Any, Tuple
from .storage import (
    week_dir,
    day_dir,
    week_spec_dir,
    role_context_dir,
    compile_day_flint_bundle,
    compile_week_spec,
    compile_role_context,
    DAY_FIELDS,
    WEEK_SPEC_PARTS,
    ROLE_CONTEXT_PARTS
)


class ValidationError:
    """Represents a validation error."""

    def __init__(self, severity: str, location: str, message: str):
        self.severity = severity  # 'error', 'warning', 'info'
        self.location = location
        self.message = message

    def __repr__(self):
        return f"[{self.severity.upper()}] {self.location}: {self.message}"


class ValidationResult:
    """Represents the result of a validation check."""

    def __init__(self):
        self.errors: List[ValidationError] = []
        self.warnings: List[ValidationError] = []
        self.info: List[ValidationError] = []

    def add_error(self, location: str, message: str):
        """Add an error to the validation result."""
        self.errors.append(ValidationError("error", location, message))

    def add_warning(self, location: str, message: str):
        """Add a warning to the validation result."""
        self.warnings.append(ValidationError("warning", location, message))

    def add_info(self, location: str, message: str):
        """Add an info message to the validation result."""
        self.info.append(ValidationError("info", location, message))

    def is_valid(self) -> bool:
        """Check if validation passed (no errors)."""
        return len(self.errors) == 0

    def summary(self) -> str:
        """Get a summary of validation results."""
        return (
            f"Errors: {len(self.errors)}, "
            f"Warnings: {len(self.warnings)}, "
            f"Info: {len(self.info)}"
        )


def validate_day_fields(week_number: int, day_number: int) -> ValidationResult:
    """
    Validate that all required Flint field files exist for a day.

    Checks:
    - All six field files exist
    - JSON files are valid JSON
    - Files are not empty (except where appropriate)
    """
    result = ValidationResult()
    day_path = day_dir(week_number, day_number)

    if not day_path.exists():
        result.add_error(
            f"Week{week_number:02d}/Day{day_number}",
            "Day directory does not exist"
        )
        return result

    for field in DAY_FIELDS:
        field_path = day_path / field
        location = f"Week{week_number:02d}/Day{day_number}/{field}"

        if not field_path.exists():
            result.add_error(location, "Field file missing")
            continue

        # Validate JSON files
        if field.endswith(".json"):
            try:
                with field_path.open("r", encoding="utf-8") as f:
                    json.load(f)
            except json.JSONDecodeError as e:
                result.add_error(location, f"Invalid JSON: {e}")

        # Check for empty files (warning, not error)
        if field_path.stat().st_size == 0:
            result.add_warning(location, "Field file is empty")

    return result


def validate_day_4_spiral_content(week_number: int) -> ValidationResult:
    """
    Validate that Day 4 includes adequate spiral/review content.

    Checks:
    - Day 4 guidelines mention prior content or review
    - Week spec includes spiral links (for weeks >= 2)
    """
    result = ValidationResult()

    if week_number < 2:
        result.add_info(
            f"Week{week_number:02d}/Day4",
            "Week 1 does not require spiral content validation"
        )
        return result

    day4_path = day_dir(week_number, 4)
    guidelines_path = day4_path / "04_guidelines_for_sparky.md"

    if guidelines_path.exists():
        content = guidelines_path.read_text(encoding="utf-8").lower()
        spiral_keywords = ["spiral", "review", "prior", "previous", "25%"]

        if not any(keyword in content for keyword in spiral_keywords):
            result.add_warning(
                f"Week{week_number:02d}/Day4",
                "Day 4 guidelines should mention spiral/review content (25% prior material)"
            )
    else:
        result.add_error(
            f"Week{week_number:02d}/Day4",
            "Day 4 guidelines file missing"
        )

    return result


def validate_week_spec(week_number: int) -> ValidationResult:
    """
    Validate the Week_Spec directory and all parts.

    Checks:
    - All required spec parts exist
    - JSON files are valid
    - Metadata includes required fields
    """
    result = ValidationResult()
    spec_dir = week_spec_dir(week_number)

    if not spec_dir.exists():
        result.add_error(
            f"Week{week_number:02d}/Week_Spec",
            "Week_Spec directory does not exist"
        )
        return result

    for part in WEEK_SPEC_PARTS:
        part_path = spec_dir / part
        location = f"Week{week_number:02d}/Week_Spec/{part}"

        if not part_path.exists():
            result.add_error(location, "Spec part file missing")
            continue

        # Validate JSON files
        if part.endswith(".json"):
            try:
                with part_path.open("r", encoding="utf-8") as f:
                    data = json.load(f)

                # Validate metadata structure
                if part == "01_metadata.json":
                    required_fields = ["week_number", "title", "theme"]
                    for field in required_fields:
                        if field not in data or not data[field]:
                            result.add_warning(
                                location,
                                f"Metadata missing required field: {field}"
                            )
            except json.JSONDecodeError as e:
                result.add_error(location, f"Invalid JSON: {e}")

    # Check for spiral links in weeks >= 2
    if week_number >= 2:
        spiral_links_path = spec_dir / "09_spiral_links.json"
        if spiral_links_path.exists():
            try:
                with spiral_links_path.open("r", encoding="utf-8") as f:
                    spiral_data = json.load(f)
                    if not spiral_data or not any(spiral_data.values()):
                        result.add_warning(
                            f"Week{week_number:02d}/Week_Spec/09_spiral_links.json",
                            "Week >= 2 should include spiral links to previous content"
                        )
            except json.JSONDecodeError:
                pass

    return result


def validate_role_context(week_number: int) -> ValidationResult:
    """
    Validate the Role_Context directory and all parts.

    Checks:
    - All required context parts exist
    - All files are valid JSON
    """
    result = ValidationResult()
    context_dir = role_context_dir(week_number)

    if not context_dir.exists():
        result.add_error(
            f"Week{week_number:02d}/Role_Context",
            "Role_Context directory does not exist"
        )
        return result

    for part in ROLE_CONTEXT_PARTS:
        part_path = context_dir / part
        location = f"Week{week_number:02d}/Role_Context/{part}"

        if not part_path.exists():
            result.add_error(location, "Context part file missing")
            continue

        # All role context parts should be valid JSON
        try:
            with part_path.open("r", encoding="utf-8") as f:
                json.load(f)
        except json.JSONDecodeError as e:
            result.add_error(location, f"Invalid JSON: {e}")

    return result


def validate_week(week_number: int) -> ValidationResult:
    """
    Perform complete validation of a week.

    Validates:
    - All four days and their fields
    - Week specification
    - Role context
    - Day 4 spiral content (for weeks >= 2)

    Returns a consolidated ValidationResult.
    """
    result = ValidationResult()

    # Validate week directory exists
    week_path = week_dir(week_number)
    if not week_path.exists():
        result.add_error(
            f"Week{week_number:02d}",
            "Week directory does not exist"
        )
        return result

    # Validate all days
    for day_num in range(1, 5):
        day_result = validate_day_fields(week_number, day_num)
        result.errors.extend(day_result.errors)
        result.warnings.extend(day_result.warnings)
        result.info.extend(day_result.info)

    # Validate Day 4 spiral content
    spiral_result = validate_day_4_spiral_content(week_number)
    result.errors.extend(spiral_result.errors)
    result.warnings.extend(spiral_result.warnings)
    result.info.extend(spiral_result.info)

    # Validate Week_Spec
    spec_result = validate_week_spec(week_number)
    result.errors.extend(spec_result.errors)
    result.warnings.extend(spec_result.warnings)
    result.info.extend(spec_result.info)

    # Validate Role_Context
    context_result = validate_role_context(week_number)
    result.errors.extend(context_result.errors)
    result.warnings.extend(context_result.warnings)
    result.info.extend(context_result.info)

    return result
