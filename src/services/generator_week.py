"""Week structure generation service."""
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import subprocess
import orjson
from .storage import (
    week_dir,
    week_spec_dir,
    role_context_dir,
    week_spec_part_path,
    role_context_part_path,
    WEEK_SPEC_PARTS,
    ROLE_CONTEXT_PARTS,
    write_file,
    write_json
)
from .llm_client import LLMClient
from .prompts.kit_tasks import task_week_spec, task_role_context, task_assets
from .usage_tracker import get_tracker


def get_template_path(template_type: str) -> Path:
    """Get the base path for template files."""
    return Path(__file__).parent.parent / "templates" / "week_kit" / template_type


def _get_git_commit() -> str:
    """Get current git commit hash."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=2
        )
        return result.stdout.strip()[:8] if result.returncode == 0 else "unknown"
    except Exception:
        return "unknown"


def _create_provenance(response) -> Dict[str, Any]:
    """Create generation provenance metadata from LLM response."""
    return {
        "provider": response.provider,
        "model": response.model,
        "created_at": datetime.utcnow().isoformat() + "Z",
        "git_commit": _get_git_commit(),
        "tokens_prompt": response.tokens_prompt,
        "tokens_completion": response.tokens_completion
    }


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


def _transform_week_spec_response(llm_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform LLM's week_spec_kit format to flat WeekSpec schema format.

    LLM returns: {week_info: {...}, generated_files: [{file_name, content}, ...]}
    WeekSpec expects: {metadata: {...}, objectives: [...], vocabulary: [...], ...}
    """
    # If already in flat format, return as-is
    if "metadata" in llm_response and "objectives" in llm_response:
        return llm_response

    # Extract week_info and generated_files
    week_info = llm_response.get("week_info", {})
    generated_files = llm_response.get("generated_files", [])

    # Build flat structure by extracting content from generated_files
    flat_spec = {}

    for file_obj in generated_files:
        file_name = file_obj.get("file_name", "")
        content = file_obj.get("content")

        if file_name == "01_metadata.json":
            flat_spec["metadata"] = content
        elif file_name == "02_objectives.json":
            flat_spec["objectives"] = content.get("objectives", []) if isinstance(content, dict) else content
        elif file_name == "03_vocabulary.json":
            flat_spec["vocabulary"] = content.get("vocabulary", []) if isinstance(content, dict) else content
        elif file_name == "04_grammar_focus.md":
            flat_spec["grammar_focus"] = content
        elif file_name == "05_chant.json" or file_name == "08_chant_chart.txt":
            # Chant can be in either file
            if "chant" not in flat_spec:
                flat_spec["chant"] = {"text": content} if isinstance(content, str) else content
        elif file_name == "06_sessions_week_view.json":
            flat_spec["sessions"] = content
        elif file_name == "07_assessment.json" or file_name == "09_assessment_overview.json":
            flat_spec["assessment"] = content
        elif file_name == "08_assets_index.json":
            flat_spec["assets"] = content
        elif file_name == "09_spiral_links.json" or file_name == "07_prior_knowledge_digest.json":
            flat_spec["spiral_links"] = content
        elif file_name == "10_interleaving_plan.md" or file_name == "10_teacher_notes.md":
            flat_spec["interleaving_plan"] = content
        elif file_name == "11_misconception_watchlist.json":
            flat_spec["misconception_watchlist"] = content
        elif file_name == "12_preview_next_week.md":
            flat_spec["preview_next_week"] = content

    # Add missing required fields with defaults
    if "sessions" not in flat_spec:
        flat_spec["sessions"] = []
    if "assets" not in flat_spec:
        flat_spec["assets"] = []
    if "spiral_links" not in flat_spec:
        flat_spec["spiral_links"] = {}
    if "interleaving_plan" not in flat_spec:
        flat_spec["interleaving_plan"] = ""
    if "misconception_watchlist" not in flat_spec:
        flat_spec["misconception_watchlist"] = []
    if "preview_next_week" not in flat_spec:
        flat_spec["preview_next_week"] = ""

    return flat_spec


def scaffold_week(week_number: int) -> Path:
    """
    Create the complete directory structure for a week.

    Creates:
    - Week_Spec/ directory with all 12 part files
    - Role_Context/ directory with all 7 part files
    - activities/ directory (empty, days added separately)

    Returns the path to the week directory.
    """
    week_path = week_dir(week_number)

    # Create Week_Spec directory and files
    spec_dir = week_spec_dir(week_number)
    spec_dir.mkdir(parents=True, exist_ok=True)

    template_spec_dir = get_template_path("spec_parts")
    for part in WEEK_SPEC_PARTS:
        template_path = template_spec_dir / part
        target_path = spec_dir / part

        if template_path.exists():
            content = template_path.read_text(encoding="utf-8")
            # Replace template variables
            content = content.replace("{week_number}", str(week_number))
            content = content.replace("{next_week_number}", str(week_number + 1))
            target_path.write_text(content, encoding="utf-8")
        else:
            # Create empty placeholder
            if part.endswith(".json"):
                write_json(target_path, {})
            else:
                write_file(target_path, "")

    # Create Role_Context directory and files
    context_dir = role_context_dir(week_number)
    context_dir.mkdir(parents=True, exist_ok=True)

    template_context_dir = get_template_path("role_context_parts")
    for part in ROLE_CONTEXT_PARTS:
        template_path = template_context_dir / part
        target_path = context_dir / part

        if template_path.exists():
            content = template_path.read_text(encoding="utf-8")
            target_path.write_text(content, encoding="utf-8")
        else:
            # Create empty JSON placeholder
            write_json(target_path, {})

    # Create activities directory (days will be added separately)
    activities_dir = week_path / "activities"
    activities_dir.mkdir(parents=True, exist_ok=True)

    # Create assets directory with placeholder files
    assets_dir = week_path / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    # Create placeholder asset files
    asset_files = [
        "ChantChart.txt",
        "Glossary.txt",
        "Copywork.txt",
        "QuizPacket.txt",
        "TeacherKey.txt",
        "VirtueEntry.txt"
    ]

    for asset_file in asset_files:
        asset_path = assets_dir / asset_file
        write_file(asset_path, f"# {asset_file.replace('.txt', '')} - Week {week_number}\n\n")

    return week_path


def scaffold_all_weeks(num_weeks: int = 36) -> List[Path]:
    """
    Scaffold all weeks in the curriculum.

    Args:
        num_weeks: Number of weeks to scaffold (default: 36)

    Returns:
        List of paths to created week directories.
    """
    week_paths = []
    for week_num in range(1, num_weeks + 1):
        week_path = scaffold_week(week_num)
        week_paths.append(week_path)

    return week_paths


# ============================================================================
# LLM-BASED GENERATION FUNCTIONS
# ============================================================================

def _load_curriculum_outline() -> Dict[str, Any]:
    """Load the curriculum outline JSON."""
    outline_path = Path(__file__).parent.parent.parent / "curriculum" / "curriculum_outline.json"
    if outline_path.exists():
        return orjson.loads(outline_path.read_bytes())
    return {}


def generate_week_spec_from_outline(week: int, client: LLMClient) -> Path:
    """
    Generate week specification using LLM from curriculum outline.

    Args:
        week: Week number (1-36)
        client: LLM client instance

    Returns:
        Path to the compiled week spec file
    """
    # Ensure week directory exists
    scaffold_week(week)

    # Load curriculum outline snippet for this week
    outline = _load_curriculum_outline()
    week_key = f"week_{week:02d}"
    outline_snip = outline.get(week_key, {
        "week": week,
        "title": f"Latin A - Week {week}",
        "virtue_focus": "Wisdom"
    })

    # Get prompts
    sys, usr, config = task_week_spec(week, outline_snip)

    # Generate via LLM (no schema, config has temp/max_tokens settings)
    response = client.generate(prompt=usr, system=sys, json_schema=None)

    # Track usage
    if response.provider and response.tokens_prompt:
        get_tracker().track(
            provider=response.provider,
            model=response.model or "unknown",
            tokens_prompt=response.tokens_prompt or 0,
            tokens_completion=response.tokens_completion or 0,
            operation=f"week_{week}_spec"
        )

    # Parse response - STRICT: must be valid JSON
    if response.json:
        spec_data = response.json
    else:
        try:
            # Strip markdown code fences if present
            cleaned_text = _strip_markdown_fences(response.text)
            spec_data = orjson.loads(cleaned_text)
        except Exception as e:
            # Save invalid response for inspection
            invalid_path = week_spec_dir(week) / "99_compiled_week_spec_INVALID.json"
            write_file(invalid_path, response.text)
            raise ValueError(f"LLM returned invalid JSON - cannot proceed. Error: {e}")

    # Transform LLM format to flat WeekSpec format
    spec_data = _transform_week_spec_response(spec_data)

    # Add generation provenance
    spec_data["__generation"] = _create_provenance(response)

    # Validate against Pydantic schema (lenient mode - log warnings but don't fail)
    from ..models import WeekSpec
    import logging
    logger = logging.getLogger(__name__)

    try:
        validated_spec = WeekSpec(**spec_data)
        spec_data = validated_spec.model_dump(by_alias=True)
        logger.info(f"Week {week} spec passed Pydantic validation")
    except Exception as e:
        # Save for inspection but continue (lenient mode)
        invalid_path = week_spec_dir(week) / "99_compiled_week_spec_VALIDATION_WARNINGS.json"
        write_json(invalid_path, spec_data)
        logger.warning(f"Week {week} spec has validation warnings (continuing anyway): {str(e)[:200]}")
        # Continue with the generated data even if validation fails

    # Write to individual part files
    _write_week_spec_parts(week, spec_data)

    # Write compiled spec
    compiled_path = week_spec_part_path(week, "99_compiled_week_spec.json")
    write_json(compiled_path, spec_data)

    return compiled_path


def _write_week_spec_parts(week: int, spec_data: Dict[str, Any]) -> None:
    """Write week spec data to individual part files."""
    mapping = {
        "01_metadata.json": spec_data.get("metadata", {}),
        "02_objectives.json": spec_data.get("objectives", []),
        "03_vocabulary.json": spec_data.get("vocabulary", []),
        "04_grammar_focus.md": spec_data.get("grammar_focus", ""),
        "05_chant.json": spec_data.get("chant", {}),
        "06_sessions_week_view.json": spec_data.get("sessions", []),
        "07_assessment.json": spec_data.get("assessment", {}),
        "08_assets_index.json": spec_data.get("assets", []),
        "09_spiral_links.json": spec_data.get("spiral_links", {}),
        "10_interleaving_plan.md": spec_data.get("interleaving_plan", ""),
        "11_misconception_watchlist.json": spec_data.get("misconception_watchlist", []),
        "12_preview_next_week.md": spec_data.get("preview_next_week", "")
    }

    for part_name, content in mapping.items():
        part_path = week_spec_part_path(week, part_name)
        if part_name.endswith(".json"):
            write_json(part_path, content)
        else:
            write_file(part_path, str(content))


def generate_role_context(week: int, client: LLMClient) -> Path:
    """
    Generate Sparky role context using LLM.

    Args:
        week: Week number (1-36)
        client: LLM client instance

    Returns:
        Path to the compiled role context file
    """
    # Ensure week directory exists
    scaffold_week(week)

    # Load week spec to inform role context
    spec_path = week_spec_part_path(week, "99_compiled_week_spec.json")
    if spec_path.exists():
        week_spec = orjson.loads(spec_path.read_bytes())
    else:
        week_spec = {"metadata": {"week": week}}

    # Get prompts
    sys, usr, _ = task_role_context(week_spec)

    # Generate via LLM
    response = client.generate(prompt=usr, system=sys)

    # Parse response
    if response.json:
        role_data = response.json
    else:
        try:
            cleaned_text = _strip_markdown_fences(response.text)
            role_data = orjson.loads(cleaned_text)
        except Exception as e:
            invalid_path = role_context_dir(week) / "99_compiled_role_context_INVALID.json"
            write_file(invalid_path, response.text)
            raise ValueError(f"LLM returned invalid JSON: {e}")

    # Write to individual part files
    _write_role_context_parts(week, role_data)

    # Write compiled role context
    compiled_path = role_context_part_path(week, "99_compiled_role_context.json")
    write_json(compiled_path, role_data)

    return compiled_path


def _write_role_context_parts(week: int, role_data: Dict[str, Any]) -> None:
    """Write role context data to individual part files."""
    parts = [
        "identity.json",
        "student_profile.json",
        "daily_cycle.json",
        "reinforcement_method.json",
        "feedback_style.json",
        "success_criteria.json",
        "knowledge_recycling.json"
    ]

    for part in parts:
        part_key = part.replace(".json", "")
        content = role_data.get(part_key, {})
        part_path = role_context_part_path(week, part)
        write_json(part_path, content)


def generate_assets(week: int, client: LLMClient) -> List[Path]:
    """
    Generate week assets (text files) using LLM.

    Args:
        week: Week number (1-36)
        client: LLM client instance

    Returns:
        List of paths to generated asset files
    """
    # Ensure week directory exists
    week_path = scaffold_week(week)
    assets_dir = week_path / "assets"

    # Load week spec to inform assets
    spec_path = week_spec_part_path(week, "99_compiled_week_spec.json")
    if spec_path.exists():
        week_spec = orjson.loads(spec_path.read_bytes())
    else:
        week_spec = {"metadata": {"week": week, "title": f"Week {week}"}}

    # Get prompts
    sys, usr, _ = task_assets(week_spec)

    # Generate via LLM
    response = client.generate(prompt=usr, system=sys)

    # Parse response
    if response.json:
        assets_data = response.json
    else:
        try:
            cleaned_text = _strip_markdown_fences(response.text)
            assets_data = orjson.loads(cleaned_text)
        except Exception:
            # Fallback to simple text split
            assets_data = {"ChantChart": response.text[:500]}

    # Write asset files
    asset_mapping = {
        "ChantChart.txt": assets_data.get("ChantChart", ""),
        "Glossary.txt": assets_data.get("Glossary", ""),
        "Copywork.txt": assets_data.get("Copywork", ""),
        "QuizPacket.txt": assets_data.get("QuizPacket", ""),
        "TeacherKey.txt": assets_data.get("TeacherKey", ""),
        "VirtueEntry.txt": assets_data.get("VirtueEntry", "")
    }

    created_paths = []
    for filename, content in asset_mapping.items():
        asset_path = assets_dir / filename
        write_file(asset_path, str(content))
        created_paths.append(asset_path)

    return created_paths
