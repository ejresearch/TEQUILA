#!/usr/bin/env python3
"""
Create internal_documents/ for existing weeks by reverse-engineering from day content.

Extracts week-level planning data from days and creates:
- week_spec.json
- week_summary.md
- role_context.json
- generation_log.json
"""
import json
from pathlib import Path
from datetime import datetime
import subprocess

CURRICULUM_BASE = Path("/Users/elle_jansick/steel/curriculum/LatinA")
WEEKS_TO_PROCESS = [1, 11, 12, 13, 14, 15]


def get_git_commit() -> str:
    """Get current git commit SHA."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        return result.stdout.strip()[:8]
    except:
        return "unknown"


def extract_week_spec_from_days(week_num: int) -> dict:
    """Extract week_spec.json by consolidating data from all 4 days."""
    week_dir = CURRICULUM_BASE / f"Week{week_num:02d}"

    # Read Day 1 weekly topics document
    weekly_topics_path = week_dir / f"Day1_{week_num}.1" / "06_document_for_sparky" / "weekly_topics_document.txt"
    weekly_topics = weekly_topics_path.read_text(encoding="utf-8") if weekly_topics_path.exists() else ""

    # Read Day 1 virtue and faith document
    virtue_faith_path = week_dir / f"Day1_{week_num}.1" / "06_document_for_sparky" / "virtue_and_faith_document.txt"
    virtue_faith = virtue_faith_path.read_text(encoding="utf-8") if virtue_faith_path.exists() else ""

    # Read Day 1 spiral review
    spiral_path = week_dir / f"Day1_{week_num}.1" / "06_document_for_sparky" / "spiral_review_document.txt"
    spiral_review = spiral_path.read_text(encoding="utf-8") if spiral_path.exists() else ""

    # Parse weekly topics to extract structured data
    lines = weekly_topics.split('\n')

    # Extract title from first line (e.g., "WEEK 12 – Second Conjugation –ēre Verbs")
    title_line = lines[0] if lines else f"Week {week_num}"
    week_title = title_line.replace(f"WEEK {week_num} – ", "").replace(f"Week {week_num} – ", "").strip()

    # Extract grammar focus
    grammar_focus = ""
    faith_phrase = ""
    virtue = ""
    core_verbs = []
    mastery_indicators = []

    for line in lines:
        if line.startswith("Grammar Focus"):
            grammar_focus = line.split("–", 1)[1].strip() if "–" in line else ""
        elif line.startswith("Faith Phrase"):
            faith_phrase = line.split("–", 1)[1].strip() if "–" in line else ""
        elif line.startswith("Virtue"):
            virtue = line.split("–", 1)[1].strip() if "–" in line else ""
        elif line.startswith("Core Verbs"):
            verbs_text = line.split("–", 1)[1].strip() if "–" in line else ""
            # Parse verbs like "amō (love), portō (carry)"
            core_verbs = [v.strip() for v in verbs_text.split(",") if v.strip()]
        elif line.startswith("Mastery Indicator"):
            mastery_indicators = [line.split("–", 1)[1].strip() if "–" in line else ""]

    # Build week_spec structure
    week_spec = {
        "metadata": {
            "week": week_num,
            "title": week_title,
            "created": datetime.now().isoformat(),
            "source": "reverse_engineered_from_days"
        },
        "objectives": {
            "grammar_focus": grammar_focus,
            "skill_goals": mastery_indicators,
            "daily_arc": "Day 1: Discovery; Day 2: Reinforcement; Day 3: Integration; Day 4: Assessment"
        },
        "vocabulary": {
            "core_items": core_verbs,
            "context": "Extracted from weekly topics document"
        },
        "grammar_focus": grammar_focus,
        "faith_integration": {
            "faith_phrase": faith_phrase,
            "virtue": virtue,
            "scripture": extract_scripture_from_virtue_doc(virtue_faith)
        },
        "spiral_links": {
            "prior_weeks_referenced": extract_prior_weeks_from_spiral(spiral_review),
            "bridge_goal": "Build on previous knowledge"
        },
        "assessment": {
            "day4_focus": "Mastery check and reflection",
            "mastery_indicators": mastery_indicators
        }
    }

    return week_spec


def extract_scripture_from_virtue_doc(virtue_text: str) -> str:
    """Extract scripture reference from virtue document."""
    for line in virtue_text.split('\n'):
        if line.startswith("Scripture"):
            return line.split("–", 1)[1].strip() if "–" in line else ""
    return ""


def extract_prior_weeks_from_spiral(spiral_text: str) -> list:
    """Extract prior week references from spiral review."""
    # Look for patterns like "Weeks 1–10" or "Week 11"
    import re
    weeks = []
    matches = re.findall(r'Week[s]?\s+(\d+)(?:[-–](\d+))?', spiral_text)
    for match in matches:
        if match[1]:  # Range like "1–10"
            start, end = int(match[0]), int(match[1])
            weeks.extend(range(start, end + 1))
        else:  # Single week
            weeks.append(int(match[0]))
    return sorted(set(weeks))


def create_week_summary(week_num: int, week_spec: dict) -> str:
    """Create week_summary.md from week_spec."""
    title = week_spec["metadata"]["title"]
    grammar = week_spec["grammar_focus"]
    faith = week_spec["faith_integration"]["faith_phrase"]
    virtue = week_spec["faith_integration"]["virtue"]

    summary = f"""# Week {week_num}: {title}

## Overview
{grammar}

## Faith Integration
- **Virtue**: {virtue}
- **Faith Phrase**: {faith}
- **Scripture**: {week_spec["faith_integration"]["scripture"]}

## Daily Progression
{week_spec["objectives"]["daily_arc"]}

## Mastery Goals
"""
    for indicator in week_spec["assessment"]["mastery_indicators"]:
        summary += f"- {indicator}\n"

    summary += f"""
## Spiral Review
Prior weeks referenced: {', '.join(map(str, week_spec["spiral_links"]["prior_weeks_referenced"]))}

---
*Generated by reverse-engineering from day content*
"""

    return summary


def extract_role_context_from_day1(week_num: int) -> dict:
    """Extract role_context.json from Day 1 role_context."""
    week_dir = CURRICULUM_BASE / f"Week{week_num:02d}"
    day1_role_path = week_dir / f"Day1_{week_num}.1" / "04_role_context.json"

    if not day1_role_path.exists():
        return {}

    day1_role = json.loads(day1_role_path.read_text(encoding="utf-8"))

    # Week-level role context (remove day-specific fields)
    role_context = {
        "identity": {
            "name": day1_role.get("identity_name", "Sparky"),
            "role": day1_role.get("identity_role", "Faithful Latin Tutor"),
            "tone": day1_role.get("identity_tone", "Warm, rhythmic, patient")
        },
        "student_profile": {
            "course": day1_role.get("student_course", "Latin A"),
            "grade_level": day1_role.get("student_grade_level", "3–5"),
            "current_week": week_num
        },
        "pedagogical_approach": {
            "goal": day1_role.get("pedagogical_goal", ""),
            "duration": day1_role.get("pedagogical_duration", "Four daily sessions (10–15 minutes)"),
            "virtue_focus": day1_role.get("virtue_focus", ""),
            "faith_phrase": day1_role.get("faith_phrase", "")
        },
        "spiral_strategy": {
            "previous_weeks_recalled": day1_role.get("previous_weeks_recalled", "")
        }
    }

    return role_context


def create_generation_log(week_num: int) -> dict:
    """Create generation_log.json with provenance metadata."""
    return {
        "week": week_num,
        "generation_timestamp": datetime.now().isoformat(),
        "method": "reverse_engineered",
        "source": "Manually created perfect curriculum from Desktop",
        "git_commit": get_git_commit(),
        "notes": "Internal documents created by reverse-engineering from existing day content"
    }


def process_week(week_num: int):
    """Create internal_documents/ for a single week."""
    print(f"\n{'='*60}")
    print(f"Processing Week {week_num}")
    print(f"{'='*60}")

    week_dir = CURRICULUM_BASE / f"Week{week_num:02d}"
    internal_dir = week_dir / "internal_documents"
    internal_dir.mkdir(parents=True, exist_ok=True)

    # 1. Create week_spec.json
    print("  Creating week_spec.json...")
    week_spec = extract_week_spec_from_days(week_num)
    week_spec_path = internal_dir / "week_spec.json"
    with open(week_spec_path, 'w', encoding='utf-8') as f:
        json.dump(week_spec, f, indent=2, ensure_ascii=False)
    print(f"    ✓ {week_spec_path}")

    # 2. Create week_summary.md
    print("  Creating week_summary.md...")
    week_summary = create_week_summary(week_num, week_spec)
    summary_path = internal_dir / "week_summary.md"
    summary_path.write_text(week_summary, encoding='utf-8')
    print(f"    ✓ {summary_path}")

    # 3. Create role_context.json
    print("  Creating role_context.json...")
    role_context = extract_role_context_from_day1(week_num)
    role_path = internal_dir / "role_context.json"
    with open(role_path, 'w', encoding='utf-8') as f:
        json.dump(role_context, f, indent=2, ensure_ascii=False)
    print(f"    ✓ {role_path}")

    # 4. Create generation_log.json
    print("  Creating generation_log.json...")
    gen_log = create_generation_log(week_num)
    log_path = internal_dir / "generation_log.json"
    with open(log_path, 'w', encoding='utf-8') as f:
        json.dump(gen_log, f, indent=2, ensure_ascii=False)
    print(f"    ✓ {log_path}")

    print(f"\n✓ Week {week_num} internal_documents/ created!")


def main():
    """Create internal_documents/ for all sample weeks."""
    print("="*60)
    print("CREATING INTERNAL_DOCUMENTS FOR SAMPLE WEEKS")
    print("="*60)
    print(f"Weeks: {WEEKS_TO_PROCESS}")
    print("="*60)

    for week_num in WEEKS_TO_PROCESS:
        try:
            process_week(week_num)
        except Exception as e:
            print(f"\n✗ Error processing Week {week_num}: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "="*60)
    print("INTERNAL DOCUMENTS CREATION COMPLETE")
    print("="*60)
    print(f"\nCreated internal_documents/ for {len(WEEKS_TO_PROCESS)} weeks")
    print("\nNext steps:")
    print("  1. Review: ls curriculum/LatinA/Week11/internal_documents/")
    print("  2. Validate: python -m src.cli.validate_week 11")
    print("  3. Test generation with Week 16 using these as reference")


if __name__ == "__main__":
    main()
