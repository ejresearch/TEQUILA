"""Day activity generation service with retry logic (v1.0 Pilot)."""
from pathlib import Path
from typing import Dict, Any, List, Optional
import orjson
import time
import logging
from datetime import datetime
from .storage import (
    day_dir,
    day_field_path,
    week_spec_part_path,
    DAY_FIELDS,
    write_file,
    write_json
)
from .llm_client import LLMClient
from .prompts.kit_tasks import task_day_fields, task_day_document, task_day_role_context
from ..config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = settings.max_retries  # Default: 10 retries


def get_field_template_path(field_name: str) -> Path:
    """Get the path to a field template file."""
    return Path(__file__).parent.parent / "templates" / "week_kit" / "activities" / "fields" / field_name


def scaffold_day(week_number: int, day_number: int) -> Path:
    """
    Create the complete directory structure and files for a specific day.

    Creates the seven Flint field files:
    - 01_class_name.txt
    - 02_summary.md
    - 03_grade_level.txt
    - 04_role_context.json (NEW in 7-field architecture)
    - 05_guidelines_for_sparky.md (reindexed from 04)
    - 06_document_for_sparky.json (reindexed from 05)
    - 07_sparkys_greeting.txt (reindexed from 06)

    Args:
        week_number: The week number (1-36)
        day_number: The day number (1-4)

    Returns:
        Path to the created day directory.
    """
    day_path = day_dir(week_number, day_number)
    day_path.mkdir(parents=True, exist_ok=True)

    # Create each field file from templates
    for field in DAY_FIELDS:
        template_path = get_field_template_path(field)
        target_path = day_field_path(week_number, day_number, field)

        if template_path.exists():
            content = template_path.read_text(encoding="utf-8")
            # Replace template variables
            content = content.replace("{week_number}", str(week_number))
            content = content.replace("{day_number}", str(day_number))
            content = content.replace("{focus_area}", get_day_focus(day_number))

            target_path.write_text(content, encoding="utf-8")
        else:
            # Create placeholder based on file type
            if field.endswith(".json"):
                write_json(target_path, {})
            else:
                write_file(target_path, "")

    return day_path


def get_day_focus(day_number: int) -> str:
    """Get the pedagogical focus for a specific day."""
    focuses = {
        1: "Introduction and exploration",
        2: "Practice and reinforcement",
        3: "Application and extension",
        4: "Review and spiral (25% prior content)"
    }
    return focuses.get(day_number, "General instruction")


def scaffold_week_days(week_number: int) -> list[Path]:
    """
    Scaffold all four days for a specific week.

    Args:
        week_number: The week number (1-36)

    Returns:
        List of paths to created day directories.
    """
    day_paths = []
    for day_num in range(1, 5):
        day_path = scaffold_day(week_number, day_num)
        day_paths.append(day_path)

    return day_paths


# ============================================================================
# RETRY AND LOGGING UTILITIES
# ============================================================================

def _log_retry_attempt(week: int, day: int, attempt: int, error: str, log_dir: Optional[Path] = None):
    """Log a retry attempt to the logs directory."""
    if log_dir is None:
        log_dir = settings.logs_path

    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"Week{week:02d}_Day{day}_retries.log"

    timestamp = datetime.now().isoformat()
    log_entry = f"[{timestamp}] Attempt {attempt}/{MAX_RETRIES}: {error}\n"

    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry)

    logger.warning(f"Week {week} Day {day} - Attempt {attempt}/{MAX_RETRIES}: {error}")


def _save_invalid_response(week: int, day: int, field: str, attempt: int, content: str):
    """Save invalid LLM response for debugging."""
    invalid_dir = settings.logs_path / "invalid_responses"
    invalid_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"Week{week:02d}_Day{day}_{field}_v{attempt}_{timestamp}_INVALID.json"
    invalid_path = invalid_dir / filename

    write_file(invalid_path, content)
    logger.error(f"Saved invalid response to {invalid_path}")
    return invalid_path


def _prompt_user_to_continue(week: int, day: int, field: str) -> bool:
    """
    Prompt user for confirmation after MAX_RETRIES failures.

    Returns True to continue, False to abort.
    """
    print(f"\n{'='*80}")
    print(f"⚠️  GENERATION FAILED: Week {week} Day {day} - {field}")
    print(f"{'='*80}")
    print(f"After {MAX_RETRIES} attempts, the LLM failed to generate valid content.")
    print(f"Logs saved to: {settings.logs_path / f'Week{week:02d}_Day{day}_retries.log'}")
    print()

    response = input("Continue with next generation? (y/n): ").strip().lower()
    return response == 'y'


# ============================================================================
# LLM-BASED GENERATION FUNCTIONS WITH RETRY LOGIC
# ============================================================================

def generate_day_fields(week: int, day: int, client: LLMClient) -> List[Path]:
    """
    Generate the seven Flint field files for a day using LLM.

    Args:
        week: Week number (1-36)
        day: Day number (1-4)
        client: LLM client instance

    Returns:
        List of paths to generated field files
    """
    # Ensure day directory exists
    scaffold_day(week, day)

    # Load week spec to inform day fields
    spec_path = week_spec_part_path(week, "99_compiled_week_spec.json")
    if spec_path.exists():
        week_spec = orjson.loads(spec_path.read_bytes())
    else:
        week_spec = {"metadata": {"week": week, "title": f"Week {week}"}}

    # Get prompts
    sys, usr, _ = task_day_fields(week_spec, day)

    # Generate via LLM
    response = client.generate(prompt=usr, system=sys)

    # Parse response
    if response.json:
        fields_data = response.json
    else:
        try:
            fields_data = orjson.loads(response.text)
        except Exception:
            # Fallback to minimal data
            fields_data = {
                "class_name": f"Week {week} Day {day}",
                "summary": "Latin lesson",
                "grade_level": "3-5",
                "guidelines_for_sparky": "Teach Latin vocabulary",
                "sparkys_greeting": "Welcome to Latin!"
            }

    # Generate role_context separately
    sys_rc, usr_rc, _ = task_day_role_context(week_spec, day)
    response_rc = client.generate(prompt=usr_rc, system=sys_rc)

    if response_rc.json:
        role_context_data = response_rc.json
    else:
        try:
            role_context_data = orjson.loads(response_rc.text)
        except Exception:
            # Fallback minimal role_context
            role_context_data = {
                "sparky_role": "encouraging guide",
                "focus_mode": f"day_{day}_focus",
                "hints_enabled": True,
                "spiral_emphasis": [],
                "encouragement_triggers": ["first_attempt"]
            }

    # Write field files (excluding document_for_sparky which is generated separately)
    field_mapping = {
        "01_class_name.txt": fields_data.get("class_name", ""),
        "02_summary.md": fields_data.get("summary", ""),
        "03_grade_level.txt": fields_data.get("grade_level", ""),
        "05_guidelines_for_sparky.md": fields_data.get("guidelines_for_sparky", ""),
        "07_sparkys_greeting.txt": fields_data.get("sparkys_greeting", "")
    }

    created_paths = []
    for field_name, content in field_mapping.items():
        field_path = day_field_path(week, day, field_name)
        write_file(field_path, str(content))
        created_paths.append(field_path)

    # Write role_context JSON
    rc_path = day_field_path(week, day, "04_role_context.json")
    write_json(rc_path, role_context_data)
    created_paths.append(rc_path)

    return created_paths


def generate_day_document(week: int, day: int, client: LLMClient) -> Path:
    """
    Generate the document_for_sparky JSON for a day using LLM with retry logic.

    Retries up to MAX_RETRIES (10) times on validation failure.
    If all retries fail, prompts user for confirmation to continue.

    Args:
        week: Week number (1-35)
        day: Day number (1-4)
        client: LLM client instance

    Returns:
        Path to generated document_for_sparky.json

    Raises:
        ValueError: If generation fails after MAX_RETRIES and user aborts
    """
    # Ensure day directory exists
    scaffold_day(week, day)

    # Load week spec to inform day document
    spec_path = week_spec_part_path(week, "99_compiled_week_spec.json")
    if spec_path.exists():
        week_spec = orjson.loads(spec_path.read_bytes())
    else:
        week_spec = {"metadata": {"week": week, "title": f"Week {week}"}}

    # Get prompts
    sys, usr, schema = task_day_document(week_spec, day)

    # Retry loop
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Generate via LLM
            response = client.generate(prompt=usr, system=sys, json_schema=schema)

            # Parse response
            if response.json:
                doc_data = response.json
            else:
                doc_data = orjson.loads(response.text)

            # Basic validation - check required fields
            required_fields = ["metadata", "prior_knowledge_digest", "objectives", "lesson_flow"]
            missing_fields = [f for f in required_fields if f not in doc_data]

            if missing_fields:
                error_msg = f"Missing required fields: {missing_fields}"
                _log_retry_attempt(week, day, attempt, error_msg)
                _save_invalid_response(week, day, "document", attempt, response.text)

                if attempt < MAX_RETRIES:
                    time.sleep(2)  # Brief pause before retry
                    continue
                else:
                    if not _prompt_user_to_continue(week, day, "document_for_sparky"):
                        raise ValueError(f"Generation aborted by user after {MAX_RETRIES} attempts")
                    break

            # Write document_for_sparky.json (field 06 in 7-field architecture)
            doc_path = day_field_path(week, day, "06_document_for_sparky.json")
            write_json(doc_path, doc_data)

            if attempt > 1:
                logger.info(f"Week {week} Day {day} document generated successfully on attempt {attempt}")

            return doc_path

        except orjson.JSONDecodeError as e:
            error_msg = f"Invalid JSON response: {e}"
            _log_retry_attempt(week, day, attempt, error_msg)
            _save_invalid_response(week, day, "document", attempt, response.text)

            if attempt < MAX_RETRIES:
                time.sleep(2)
                continue
            else:
                if not _prompt_user_to_continue(week, day, "document_for_sparky"):
                    raise ValueError(f"Generation aborted by user after {MAX_RETRIES} attempts")
                # User chose to continue - save what we have
                doc_path = day_field_path(week, day, "06_document_for_sparky.json")
                write_file(doc_path, "{}")
                return doc_path

        except Exception as e:
            error_msg = f"Unexpected error: {e}"
            _log_retry_attempt(week, day, attempt, error_msg)

            if attempt < MAX_RETRIES:
                time.sleep(2)
                continue
            else:
                if not _prompt_user_to_continue(week, day, "document_for_sparky"):
                    raise ValueError(f"Generation aborted by user after {MAX_RETRIES} attempts")
                # User chose to continue - save placeholder
                doc_path = day_field_path(week, day, "06_document_for_sparky.json")
                write_file(doc_path, "{}")
                return doc_path

    # Fallback if loop completes without return
    doc_path = day_field_path(week, day, "06_document_for_sparky.json")
    return doc_path


def hydrate_day_from_llm(week: int, day: int, client: LLMClient) -> Dict[str, Any]:
    """
    Generate all day content (fields + document) using LLM.

    Args:
        week: Week number (1-36)
        day: Day number (1-4)
        client: LLM client instance

    Returns:
        Dictionary with paths and status
    """
    field_paths = generate_day_fields(week, day, client)
    doc_path = generate_day_document(week, day, client)

    return {
        "week": week,
        "day": day,
        "field_paths": [str(p) for p in field_paths],
        "document_path": str(doc_path),
        "status": "success"
    }
