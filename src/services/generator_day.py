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
    week_dir,
    week_spec_part_path,
    DAY_FIELDS,
    write_file,
    write_json
)
from .llm_client import LLMClient
from .prompts.kit_tasks import (
    task_day_fields,
    task_day_document,
    task_day_role_context,
    task_day_guidelines,
    task_day_greeting,
    task_quiz_packet,
    task_teacher_key
)
from ..config import settings

# Configure logging
logger = logging.getLogger(__name__)

# Retry configuration
MAX_RETRIES = settings.max_retries  # Default: 10 retries


def _strip_markdown_fences(text: str) -> str:
    """
    Strip markdown code fences from JSON response.

    OpenAI sometimes returns JSON wrapped in ```json ... ``` fences.
    """
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]  # Remove ```json
    elif text.startswith("```"):
        text = text[3:]  # Remove ```

    if text.endswith("```"):
        text = text[:-3]  # Remove trailing ```

    return text.strip()


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
            cleaned_text = _strip_markdown_fences(response.text)
            fields_data = orjson.loads(cleaned_text)
        except Exception:
            # Fallback to minimal data
            fields_data = {
                "class_name": f"Week {week} Day {day}",
                "summary": "Latin lesson",
                "grade_level": "3-5",
                "guidelines_for_sparky": "Teach Latin vocabulary",
                "sparkys_greeting": "Welcome to Latin!"
            }

    # Generate role_context separately (field 04)
    sys_rc, usr_rc, schema_rc = task_day_role_context(week_spec, day)
    response_rc = client.generate(prompt=usr_rc, system=sys_rc, json_schema=schema_rc)

    if response_rc.json:
        role_context_data = response_rc.json
    else:
        try:
            cleaned_text = _strip_markdown_fences(response_rc.text)
            role_context_data = orjson.loads(cleaned_text)
        except Exception:
            # Fallback minimal role_context
            role_context_data = {
                "sparky_role": "encouraging guide",
                "focus_mode": f"day_{day}_focus",
                "hints_enabled": True,
                "spiral_emphasis": [],
                "encouragement_triggers": ["first_attempt"]
            }

    # Generate guidelines (field 05) - needs role_context
    sys_guide, usr_guide, _ = task_day_guidelines(week_spec, day, role_context_data)
    response_guide = client.generate(prompt=usr_guide, system=sys_guide)
    guidelines_content = response_guide.text

    # Generate greeting (field 07) - needs role_context and will need document later
    # For now generate without document (will be regenerated if needed)
    sys_greet, usr_greet, _ = task_day_greeting(week_spec, day, role_context_data, None)
    response_greet = client.generate(prompt=usr_greet, system=sys_greet)
    greeting_content = response_greet.text

    # Write field files (fields 01-03, 05, 07)
    field_mapping = {
        "01_class_name.txt": fields_data.get("class_name", ""),
        "02_summary.md": fields_data.get("summary", ""),
        "03_grade_level.txt": fields_data.get("grade_level", ""),
        "05_guidelines_for_sparky.md": guidelines_content,
        "07_sparkys_greeting.txt": greeting_content
    }

    created_paths = []
    for field_name, content in field_mapping.items():
        field_path = day_field_path(week, day, field_name)
        write_file(field_path, str(content))
        created_paths.append(field_path)

    # Write role_context JSON (field 04)
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
                cleaned_text = _strip_markdown_fences(response.text)
                doc_data = orjson.loads(cleaned_text)

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


def generate_day4_assessment(week: int, client: LLMClient) -> Dict[str, Path]:
    """
    Generate Day 4 assessment materials (quiz packet + teacher key).

    This function enforces pedagogical requirements:
    - Quiz must include ≥25% content from prior weeks (spiral enforcement)
    - Balanced coverage: vocabulary, grammar, chant, virtue reflection
    - Teacher key must provide detailed explanations

    Args:
        week: Week number (1-35)
        client: LLM client instance

    Returns:
        Dictionary with paths to generated assessment files

    Raises:
        ValueError: If week spec or Day 4 document not found
    """
    logger.info(f"Generating Day 4 assessment for Week {week}")

    # Load week spec
    spec_path = week_spec_part_path(week, "99_compiled_week_spec.json")
    if not spec_path.exists():
        raise ValueError(f"Week spec not found for Week {week}. Generate week spec first.")

    week_spec = orjson.loads(spec_path.read_bytes())

    # Load Day 4 document
    day4_doc_path = day_field_path(week, 4, "06_document_for_sparky.json")
    if not day4_doc_path.exists():
        raise ValueError(f"Day 4 document not found for Week {week}. Generate Day 4 first.")

    day4_document = orjson.loads(day4_doc_path.read_bytes())

    # Load Day 4 guidelines (optional)
    guidelines_path = day_field_path(week, 4, "05_guidelines_for_sparky.md")
    guidelines = guidelines_path.read_text(encoding="utf-8") if guidelines_path.exists() else None

    # Generate quiz packet
    logger.info("Generating quiz packet...")
    sys_quiz, usr_quiz, config_quiz = task_quiz_packet(
        week_number=week,
        week_spec=week_spec,
        day4_document=day4_document,
        guidelines=guidelines
    )

    response_quiz = client.generate(prompt=usr_quiz, system=sys_quiz)

    # Parse quiz response (expects Markdown quiz + JSON answer key at end)
    if response_quiz.json:
        quiz_data = response_quiz.json
    else:
        # Response is likely Markdown + JSON block
        # Split by JSON code fence or find JSON block at end
        text = response_quiz.text

        # Try to find JSON block (either in code fence or raw at end)
        import re
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', text, re.DOTALL)
        if not json_match:
            # Try without code fence
            json_match = re.search(r'(\{[^{]*"answer_key_min"[^}]*\})', text, re.DOTALL)

        if json_match:
            json_part = json_match.group(1)
            markdown_part = text[:json_match.start()].strip()

            try:
                answer_key_data = orjson.loads(json_part)
                quiz_data = {
                    "quiz_markdown": markdown_part,
                    "answer_key_min": answer_key_data.get("answer_key_min", [])
                }
                logger.info(f"Successfully parsed quiz: {len(markdown_part)} chars markdown, {len(quiz_data['answer_key_min'])} answer keys")
            except Exception as e:
                logger.error(f"Failed to parse JSON portion of quiz: {e}")
                raise ValueError(f"Quiz packet generation failed: invalid JSON in response")
        else:
            # No JSON found, try parsing entire response as JSON
            try:
                cleaned_text = _strip_markdown_fences(text)
                quiz_data = orjson.loads(cleaned_text)
            except Exception as e:
                logger.error(f"Failed to parse quiz packet response: {e}")
                logger.error(f"Raw response text: {text[:500]}")
                # Save the invalid response for inspection
                invalid_dir = settings.logs_path / "invalid_responses"
                invalid_dir.mkdir(parents=True, exist_ok=True)
                invalid_path = invalid_dir / f"Week{week:02d}_quiz_packet_INVALID.txt"
                write_file(invalid_path, text)
                logger.error(f"Saved invalid quiz response to {invalid_path}")
                raise ValueError(f"Quiz packet generation failed: invalid JSON response")

    quiz_markdown = quiz_data.get("quiz_markdown", "")
    answer_key_min = quiz_data.get("answer_key_min", [])

    if not quiz_markdown:
        raise ValueError("Quiz packet generation failed: empty quiz_markdown")

    # Write quiz packet to assets
    assets_dir = week_dir(week) / "assets"
    quiz_path = assets_dir / "QuizPacket.txt"
    write_file(quiz_path, quiz_markdown)
    logger.info(f"Quiz packet written to {quiz_path}")

    # Generate teacher key
    logger.info("Generating teacher answer key...")
    sys_key, usr_key, config_key = task_teacher_key(
        week_number=week,
        quiz_markdown=quiz_markdown,
        answer_key_min=answer_key_min,
        week_spec=week_spec
    )

    response_key = client.generate(prompt=usr_key, system=sys_key)
    teacher_key_markdown = response_key.text

    if not teacher_key_markdown or len(teacher_key_markdown) < 100:
        logger.warning("Teacher key generation produced minimal output")

    # Write teacher key to assets
    key_path = assets_dir / "TeacherKey.txt"
    write_file(key_path, teacher_key_markdown)
    logger.info(f"Teacher key written to {key_path}")

    return {
        "quiz_packet": quiz_path,
        "teacher_key": key_path,
        "status": "success"
    }


def hydrate_day_from_llm(week: int, day: int, client: LLMClient) -> Dict[str, Any]:
    """
    Generate all day content (fields + document) using LLM.

    For Day 4, also generates assessment materials (quiz + teacher key).

    Args:
        week: Week number (1-36)
        day: Day number (1-4)
        client: LLM client instance

    Returns:
        Dictionary with paths and status
    """
    field_paths = generate_day_fields(week, day, client)
    doc_path = generate_day_document(week, day, client)

    result = {
        "week": week,
        "day": day,
        "field_paths": [str(p) for p in field_paths],
        "document_path": str(doc_path),
        "status": "success"
    }

    # Day 4: Generate assessment materials
    if day == 4:
        try:
            assessment_paths = generate_day4_assessment(week, client)
            result["assessment_paths"] = {
                "quiz_packet": str(assessment_paths["quiz_packet"]),
                "teacher_key": str(assessment_paths["teacher_key"])
            }
            logger.info(f"Day 4 assessment generation completed for Week {week}")
        except Exception as e:
            logger.error(f"Day 4 assessment generation failed: {e}")
            # Don't fail entire day generation, but log the error
            result["assessment_error"] = str(e)

    return result
