"""Week structure generation with internal_documents planning architecture.

New Architecture:
1. Generate internal_documents/ first (week planning)
   - week_spec.json: Complete curriculum outline
   - week_summary.md: Human-readable overview
   - role_context.json: Sparky's week-level profile
   - generation_log.json: Provenance metadata

2. Generate Day folders using internal_documents as source
   - Days pull week-level data from internal_documents/
   - 06_document_for_sparky/ populated from week_spec.json
   - 04_role_context.json customized from week role_context
"""
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
import subprocess
import orjson
import logging

from .storage import (
    week_dir,
    internal_documents_dir,
    internal_doc_path,
    INTERNAL_DOCUMENTS,
    write_file,
    write_json,
    read_json
)
from .generator_day import scaffold_day
from .llm_client import LLMClient
from .prompts.kit_tasks import task_week_spec, task_role_context
from .usage_tracker import get_tracker
from .prompts.phase0_research import execute_phase0_research

logger = logging.getLogger(__name__)


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


def _strip_markdown_fences(text: str) -> str:
    """Strip markdown code fences from JSON response."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return text.strip()


def scaffold_week(week_number: int) -> Path:
    """
    Create week structure: internal_documents/ + 4 day folders.

    Args:
        week_number: The week number (1-36)

    Returns:
        Path to the created week directory.
    """
    week_path = week_dir(week_number)
    week_path.mkdir(parents=True, exist_ok=True)

    # Create internal_documents/ with placeholder files
    internal_dir = internal_documents_dir(week_number)
    internal_dir.mkdir(parents=True, exist_ok=True)

    for doc in INTERNAL_DOCUMENTS:
        doc_path = internal_doc_path(week_number, doc)
        if doc.endswith(".json"):
            write_json(doc_path, {})
        else:
            write_file(doc_path, "")

    # Create 4 day folders with 7-field structure
    for day_num in range(1, 5):
        scaffold_day(week_number, day_num)

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


def _load_curriculum_outline() -> Dict[str, Any]:
    """Load the curriculum outline JSON."""
    outline_path = Path(__file__).parent.parent.parent / "curriculum" / "curriculum_outline.json"
    if outline_path.exists():
        return orjson.loads(outline_path.read_bytes())
    return {}


def generate_week_spec_from_outline(week: int, client: LLMClient, research_plan: Dict[str, Any] = None) -> Path:
    """
    Generate week_spec.json using LLM from curriculum outline.

    NEW: Now receives PHASE 0 research findings to inform generation.

    Saves to: Week{N}/internal_documents/week_spec.json

    Args:
        week: Week number (1-35)
        client: LLM client instance
        research_plan: Optional PHASE 0 research findings

    Returns:
        Path to generated week_spec.json
    """
    import time

    # Ensure internal_documents directory exists
    internal_dir = internal_documents_dir(week)
    internal_dir.mkdir(parents=True, exist_ok=True)

    # Load curriculum outline snippet for this week
    outline = _load_curriculum_outline()
    week_key = f"week_{week:02d}"
    outline_snip = outline.get(week_key, {
        "week": week,
        "title": f"Latin A - Week {week}",
        "virtue_focus": "Wisdom"
    })

    # Get prompts (pass research plan if available)
    sys, usr, config = task_week_spec(week, outline_snip, research_plan)

    # Retry loop (up to 5 attempts)
    MAX_RETRIES = 5
    spec_data = None

    for attempt in range(1, MAX_RETRIES + 1):
        response = client.generate(prompt=usr, system=sys, json_schema=None)

        # Track usage
        if response.provider and response.tokens_prompt:
            get_tracker().track(
                provider=response.provider,
                model=response.model or "unknown",
                tokens_prompt=response.tokens_prompt or 0,
                tokens_completion=response.tokens_completion or 0,
                operation=f"week_{week}_spec_attempt{attempt}"
            )

        # Parse response
        try:
            if response.json:
                spec_data = response.json
            else:
                cleaned_text = _strip_markdown_fences(response.text)
                spec_data = orjson.loads(cleaned_text)

            # Check for placeholder content
            response_text = response.text if response.text else str(spec_data)
            if "{ ... }" in response_text or "{...}" in response_text:
                raise ValueError("Response contains placeholder ellipses")

            if attempt > 1:
                logger.info(f"Week {week} spec generated successfully on attempt {attempt}")
            break

        except Exception as e:
            logger.warning(f"Week {week} spec attempt {attempt}/{MAX_RETRIES} failed: {str(e)[:200]}")

            # Save invalid response
            invalid_path = internal_doc_path(week, f"week_spec_INVALID_attempt{attempt}.json")
            write_file(invalid_path, response.text)

            if attempt < MAX_RETRIES:
                time.sleep(2)
                continue
            else:
                logger.error(f"Week {week} spec failed after {MAX_RETRIES} attempts")
                raise ValueError(f"LLM returned invalid JSON after {MAX_RETRIES} attempts: {e}")

    # Write to internal_documents/week_spec.json
    spec_path = internal_doc_path(week, "week_spec.json")
    write_json(spec_path, spec_data)
    logger.info(f"Week {week} spec saved to {spec_path}")

    return spec_path


def generate_week_summary(week: int, client: LLMClient, research_plan: Dict[str, Any] = None) -> Path:
    """
    Generate week_summary.md using LLM with PHASE 0 research.

    NEW: Uses task_week_summary() prompt with research findings to explain
    pedagogical decisions and provide comprehensive teacher overview.

    Saves to: Week{N}/internal_documents/week_summary.md

    Args:
        week: Week number (1-36)
        client: LLM client instance
        research_plan: Optional PHASE 0 research findings

    Returns:
        Path to generated week_summary.md
    """
    from .prompts.kit_tasks import task_week_summary

    # Load week_spec
    week_spec_path = internal_doc_path(week, "week_spec.json")
    if not week_spec_path.exists():
        raise FileNotFoundError(f"Week spec not found. Run generate_week_spec_from_outline({week}) first.")

    week_spec = read_json(week_spec_path)

    # Get prompts from task_week_summary
    sys, usr, config = task_week_summary(
        week_number=week,
        week_spec=week_spec,
        prior_knowledge_digest=None  # TODO: extract from week_spec if available
    )

    # If research available, inject pedagogical explanations
    if research_plan:
        pedagogy = research_plan.get("03_pedagogical_research", {})
        duration = research_plan.get("05_session_duration", {})

        research_context = f"""

## PHASE 0 PEDAGOGICAL CONTEXT

Include these insights in your summary to help teachers understand WHY content was chosen:

- **Pedagogical Approach**: {pedagogy.get('logos_latin_approach', '')[:300]}
- **Session Duration**: {duration.get('recommended_duration_minutes', 15)} minutes ({duration.get('rationale', '')})
- **Common Misconceptions**: {', '.join(pedagogy.get('common_misconceptions', [])[:3])}

Explain the pedagogical reasoning behind vocabulary selection, grammar sequencing, and instructional approach.
"""
        usr += research_context

    # Generate summary
    response = client.generate(prompt=usr, system=sys)

    # Extract markdown content from response
    if response.json and 'content' in response.json:
        summary_content = response.json['content']
    else:
        summary_content = response.text

    summary_path = internal_doc_path(week, "week_summary.md")
    write_file(summary_path, summary_content)
    logger.info(f"Week {week} summary saved to {summary_path}")

    return summary_path


def generate_week_role_context(week: int, client: LLMClient, research_plan: Dict[str, Any] = None) -> Path:
    """
    Generate role_context.json using LLM with PHASE 0 research.

    NEW: Uses research findings to adapt Sparky's behavior based on
    week difficulty, virtue focus, and student differentiation needs.

    Saves to: Week{N}/internal_documents/role_context.json

    Args:
        week: Week number (1-36)
        client: LLM client instance
        research_plan: Optional PHASE 0 research findings

    Returns:
        Path to generated role_context.json
    """
    # Load week_spec
    week_spec_path = internal_doc_path(week, "week_spec.json")
    if not week_spec_path.exists():
        raise FileNotFoundError(f"Week spec not found. Run generate_week_spec_from_outline({week}) first.")

    week_spec = read_json(week_spec_path)

    # Get prompt (with research)
    sys, usr, _ = task_role_context(week_spec, research_plan)

    # Generate
    response = client.generate(prompt=usr, system=sys)

    # Parse
    try:
        if response.json:
            role_data = response.json
        else:
            cleaned_text = _strip_markdown_fences(response.text)
            role_data = orjson.loads(cleaned_text)
    except Exception as e:
        logger.error(f"Failed to parse role context: {e}")
        # Fallback
        role_data = {
            "identity": "Sparky the Latin tutor",
            "tone": "Warm, encouraging",
            "wait_time": "2-3 seconds",
            "praise_words": ["Optime!", "Bene!", "Excellent!"]
        }

    # Write
    role_path = internal_doc_path(week, "role_context.json")
    write_json(role_path, role_data)
    logger.info(f"Week {week} role context saved to {role_path}")

    return role_path


def save_generation_log(week: int, model_info: Dict[str, Any] = None, research_plan: Dict[str, Any] = None) -> Path:
    """
    Save generation log with provenance metadata.

    NEW: Includes PHASE 0 metadata for full cost/provenance tracking.

    Args:
        week: Week number
        model_info: Optional dict with model/token info
        research_plan: Optional PHASE 0 research findings with metadata

    Returns:
        Path to generation_log.json
    """
    log_data = {
        "week": week,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "git_commit": _get_git_commit(),
        "architecture": "PHASE 0 + PHASE 1 + PHASE 2 (v1.1)",
        "model_info": model_info or {}
    }

    # Add PHASE 0 metadata if available
    if research_plan:
        phase0_metadata = {
            "phase0_executed": True,
            "research_calls": {
                "backward_analysis": research_plan.get("01_backward_analysis", {}).get("_metadata", {}),
                "forward_analysis": research_plan.get("02_forward_analysis", {}).get("_metadata", {}),
                "pedagogical_research": research_plan.get("03_pedagogical_research", {}).get("_metadata", {}),
                "vocabulary_determination": research_plan.get("04_vocabulary_plan", {}).get("_metadata", {}),
                "virtue_faith_integration": research_plan.get("06_virtue_faith_strategy", {}).get("_metadata", {}),
                "assessment_design": research_plan.get("07_assessment_plan", {}).get("_metadata", {}),
                "differentiation": research_plan.get("08_differentiation_plan", {}).get("_metadata", {}),
                "master_analysis": research_plan.get("10_master_analysis", {}).get("_metadata", {}),
                "alignment": research_plan.get("11_alignment_guide", {}).get("_metadata", {})
            },
            "models_used": {
                "reasoning": "o1-mini (or gpt-4o fallback)",
                "generation": "gpt-4o",
                "rule_based": ["session_duration", "materials_planning"]
            },
            "vocabulary_verified": {
                "latin_only": research_plan.get("04_vocabulary_plan", {}).get("alignment_check", {}).get("NO_SPANISH_WORDS", False),
                "alignment_check": research_plan.get("04_vocabulary_plan", {}).get("alignment_check", {})
            }
        }
        log_data["phase0_research"] = phase0_metadata
    else:
        log_data["phase0_research"] = {"phase0_executed": False}

    log_path = internal_doc_path(week, "generation_log.json")
    write_json(log_path, log_data)

    return log_path


def generate_week_planning(week: int, client: LLMClient) -> Dict[str, Path]:
    """
    Generate all internal planning documents for a week.

    NEW ARCHITECTURE:
    - PHASE 0: Research & Planning (12 API calls) - execute_phase0_research()
    - PHASE 1: Week Spec Generation (uses Phase 0 findings)

    Creates internal_documents/ with:
    - phase0_research.json (12 research outputs)
    - week_spec.json (curriculum outline - informed by research)
    - week_summary.md (teacher overview)
    - role_context.json (Sparky profile)
    - generation_log.json (provenance)

    Args:
        week: Week number (1-35)
        client: LLM client instance

    Returns:
        Dict with paths to created documents
    """
    logger.info(f"=== PHASE 0: Research & Planning for Week {week} ===")

    # PHASE 0: Execute 12-step research cascade
    # Pass the raw OpenAI client (client.client for OpenAIClient wrapper)
    openai_client = getattr(client, 'client', client)
    research_plan = execute_phase0_research(week, openai_client)

    # Save PHASE 0 research to internal_documents/
    research_path = internal_doc_path(week, "phase0_research.json")
    write_json(research_path, research_plan)
    logger.info(f"Phase 0 research saved to {research_path}")

    logger.info(f"=== PHASE 1: Generating week {week} planning documents ===")

    # 1. Generate week_spec.json (now with research context)
    logger.info(f"Generating week_spec.json...")
    week_spec_path = generate_week_spec_from_outline(week, client, research_plan)

    # 2. Generate week_summary.md (with research context)
    logger.info(f"Generating week_summary.md...")
    summary_path = generate_week_summary(week, client, research_plan)

    # 3. Generate role_context.json (with research context)
    logger.info(f"Generating role_context.json...")
    role_path = generate_week_role_context(week, client, research_plan)

    # 4. Save generation log (with PHASE 0 metadata)
    logger.info(f"Saving generation_log.json...")
    log_path = save_generation_log(week, model_info=None, research_plan=research_plan)

    logger.info(f"=== Phase 1 complete: Week {week} planning done ===")

    return {
        "phase0_research": research_path,
        "week_spec": week_spec_path,
        "week_summary": summary_path,
        "role_context": role_path,
        "generation_log": log_path
    }
