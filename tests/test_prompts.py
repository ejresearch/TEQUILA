"""Test suite for prompt output validation."""
import pytest
import json
from src.services.prompts.prompt_validator import (
    validate_role_context,
    validate_guidelines_markdown,
    validate_document_json,
    validate_greeting_text,
    validate_project_manifest
)


class TestRoleContextValidation:
    """Test role_context JSON validation."""

    def test_valid_role_context_day1(self):
        """Valid role_context for Day 1 should pass."""
        data = {
            "sparky_role": "patient guide",
            "focus_mode": "introduction_and_exploration",
            "hints_enabled": True,
            "spiral_emphasis": [],
            "encouragement_triggers": ["first_attempt", "corrected_error", "progress_shown"]
        }
        is_valid, errors = validate_role_context(data, day=1)
        assert is_valid
        assert len(errors) == 0

    def test_valid_role_context_day4(self):
        """Valid role_context for Day 4 should pass."""
        data = {
            "sparky_role": "review conductor",
            "focus_mode": "review_and_spiral",
            "hints_enabled": True,
            "spiral_emphasis": ["Week 10 vocabulary", "Week 11 grammar"],
            "encouragement_triggers": ["first_attempt", "corrected_error", "progress_shown"]
        }
        is_valid, errors = validate_role_context(data, day=4)
        assert is_valid
        assert len(errors) == 0

    def test_missing_required_field(self):
        """Missing required field should fail."""
        data = {
            "sparky_role": "patient guide",
            "hints_enabled": True
            # Missing focus_mode
        }
        is_valid, errors = validate_role_context(data, day=1)
        assert not is_valid
        assert any("focus_mode" in err for err in errors)

    def test_day4_insufficient_spiral_emphasis(self):
        """Day 4 with <2 spiral_emphasis items should fail."""
        data = {
            "sparky_role": "review conductor",
            "focus_mode": "review_and_spiral",
            "hints_enabled": True,
            "spiral_emphasis": ["Week 10 vocabulary"],  # Only 1 item
            "encouragement_triggers": ["first_attempt", "corrected_error", "progress_shown"]
        }
        is_valid, errors = validate_role_context(data, day=4)
        assert not is_valid
        assert any("≥2 spiral_emphasis" in err for err in errors)


class TestGuidelinesValidation:
    """Test guidelines markdown validation."""

    def test_valid_guidelines(self):
        """Valid guidelines markdown should pass."""
        text = """---
references:
  prior_knowledge: ["Week 1 vocab"]
  vocabulary: ["amo", "amas", "amat"]
  grammar_focus: "present tense"
  virtue: "patience"
---

# Week 2 Day 1: Teaching Guidelines

## Sparky's Role for This Day
**Persona:** patient guide

## Lesson Objectives
- Learn present tense conjugations

## Teaching Flow Overview
1. Greeting

## Behavioral Hints
- Encouragement triggers

## Common Misconceptions
- None yet

## Day-Specific Notes
- Focus on exploration
"""
        is_valid, errors = validate_guidelines_markdown(text, day=1)
        assert is_valid
        assert len(errors) == 0

    def test_missing_yaml_frontmatter(self):
        """Guidelines without YAML frontmatter should fail."""
        text = "# Week 2 Day 1: Teaching Guidelines\n\nNo YAML here."
        is_valid, errors = validate_guidelines_markdown(text, day=1)
        assert not is_valid
        assert any("YAML frontmatter" in err for err in errors)


class TestDocumentValidation:
    """Test document_for_sparky JSON validation."""

    def test_valid_document(self):
        """Valid document JSON should pass."""
        data = {
            "metadata": {"week": 1, "day": 1, "title": "Test", "duration_minutes": 45},
            "prior_knowledge_digest": " ".join(["word"] * 150),  # 150 words
            "yesterday_recap": "N/A",
            "spiral_links": {"recycled_vocab": [], "recycled_grammar": [], "prior_day_concepts": [], "prior_weeks": []},
            "misconception_watchlist": [],
            "objectives": {"primary": ["obj1", "obj2"], "spiral_review": []},
            "materials": ["item1", "item2", "item3"],
            "lesson_flow": [
                {"type": "recall", "duration_minutes": 5, "description": "Review", "student_action": "Recite"},
                {"type": "introduction", "duration_minutes": 10, "description": "Introduce", "student_action": "Listen"},
                {"type": "guided_practice", "duration_minutes": 15, "description": "Practice", "student_action": "Write"},
                {"type": "independent_practice", "duration_minutes": 10, "description": "Work", "student_action": "Complete"},
                {"type": "closure", "duration_minutes": 5, "description": "Close", "student_action": "Reflect"}
            ],
            "behavior": {"tone": "encouraging", "loop_behavior": "repeat", "hints_max": 3, "wait_seconds": 5, "encouragement_frequency": "often"}
        }
        is_valid, errors = validate_document_json(data, day=1)
        assert is_valid
        assert len(errors) == 0

    def test_lesson_flow_missing_recall(self):
        """lesson_flow without initial recall step should fail."""
        data = {
            "metadata": {},
            "prior_knowledge_digest": " ".join(["word"] * 150),
            "yesterday_recap": "test",
            "spiral_links": {},
            "misconception_watchlist": [],
            "objectives": {},
            "materials": ["item1"],
            "lesson_flow": [
                {"type": "introduction", "duration_minutes": 10, "description": "Intro", "student_action": "Listen"}
            ],
            "behavior": {}
        }
        is_valid, errors = validate_document_json(data, day=1)
        assert not is_valid
        assert any("recall" in err or "review" in err for err in errors)


class TestGreetingValidation:
    """Test greeting text validation."""

    def test_valid_greeting(self):
        """Valid greeting text should pass."""
        text = "Welcome, young scholars! Today we'll explore Latin together."
        is_valid, errors = validate_greeting_text(text)
        assert is_valid
        assert len(errors) == 0

    def test_greeting_too_long(self):
        """Greeting exceeding 200 chars should fail."""
        text = "A" * 201
        is_valid, errors = validate_greeting_text(text)
        assert not is_valid
        assert any("too long" in err for err in errors)


class TestProjectManifestValidation:
    """Test project manifest JSON validation."""

    def test_valid_manifest(self):
        """Valid project manifest should pass."""
        data = {
            "project_info": {
                "title": "Latin A",
                "grade_focus": "3",
                "total_weeks": 35,
                "days_per_week": 4
            },
            "pedagogical_constants": [
                "Spiral review 25-40%",
                "Virtue integration",
                "Chant-based memorization"
            ],
            "week_manifest": [
                {
                    "week_number": i,
                    "title": f"Week {i} Title",
                    "grammar_focus": f"Grammar concept {i}",
                    "chant": f"Chant {i}",
                    "vocabulary_scope": ["word1", "word2", "word3"],
                    "virtue_focus": "Patience",
                    "faith_phrase": "Deus caritas est",
                    "day_structure": {
                        "day_1": "Learn",
                        "day_2": "Practice",
                        "day_3": "Review",
                        "day_4": "Quiz"
                    }
                }
                for i in range(1, 36)
            ]
        }
        is_valid, errors = validate_project_manifest(data)
        assert is_valid
        assert len(errors) == 0

    def test_missing_top_level_field(self):
        """Missing top-level field should fail."""
        data = {
            "project_info": {},
            "pedagogical_constants": []
            # Missing week_manifest
        }
        is_valid, errors = validate_project_manifest(data)
        assert not is_valid
        assert any("week_manifest" in err for err in errors)

    def test_incorrect_week_count(self):
        """Manifest with != 35 weeks should fail."""
        data = {
            "project_info": {
                "title": "Latin A",
                "grade_focus": "3",
                "total_weeks": 35,
                "days_per_week": 4
            },
            "pedagogical_constants": ["Spiral review"],
            "week_manifest": [
                {
                    "week_number": 1,
                    "title": "Week 1",
                    "grammar_focus": "Grammar",
                    "chant": "Chant",
                    "vocabulary_scope": ["word1"],
                    "virtue_focus": "Patience",
                    "faith_phrase": "Phrase",
                    "day_structure": {"day_1": "x", "day_2": "x", "day_3": "x", "day_4": "x"}
                }
                # Only 1 week instead of 35
            ]
        }
        is_valid, errors = validate_project_manifest(data)
        assert not is_valid
        assert any("35 weeks" in err for err in errors)

    def test_missing_week_field(self):
        """Week missing required field should fail."""
        data = {
            "project_info": {"title": "Latin A", "grade_focus": "3", "total_weeks": 35, "days_per_week": 4},
            "pedagogical_constants": ["Spiral"],
            "week_manifest": [
                {
                    "week_number": i,
                    "title": f"Week {i}",
                    # Missing grammar_focus, chant, etc.
                }
                for i in range(1, 36)
            ]
        }
        is_valid, errors = validate_project_manifest(data)
        assert not is_valid
        assert any("grammar_focus" in err for err in errors)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
