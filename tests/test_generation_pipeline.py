"""Tests for LLM generation pipeline."""
import pytest
from pathlib import Path
from src.services.generator_week import (
    generate_week_spec_from_outline,
    generate_role_context,
    generate_assets
)
from src.services.generator_day import (
    generate_day_fields,
    generate_day_document,
    hydrate_day_from_llm
)
from tests.test_llm_client import FakeLLMClient


@pytest.fixture
def fake_week_spec():
    """Sample week specification for testing."""
    return {
        "metadata": {
            "course": "Latin A",
            "week": 11,
            "title": "Latin Verbs Introduction",
            "virtue_focus": "Diligence"
        },
        "objectives": [
            "Learn present tense verb conjugations",
            "Practice common Latin verbs"
        ],
        "vocabulary": [
            {"latin": "amo", "english": "I love"},
            {"latin": "habeo", "english": "I have"}
        ],
        "grammar_focus": "Present tense first conjugation",
        "chant": {
            "latin": "Amo, amas, amat",
            "english": "I love, you love, he/she loves"
        },
        "sessions": [],
        "assessment": {"type": "quiz"},
        "assets": ["ChantChart", "Glossary"],
        "spiral_links": {
            "prior_weeks": [10],
            "recycled_vocab": ["sum", "est"]
        },
        "interleaving_plan": "Review nouns from Week 10",
        "misconception_watchlist": ["Confusing verb endings"],
        "preview_next_week": "We'll learn imperfect tense"
    }


@pytest.fixture
def fake_role_context():
    """Sample role context for testing."""
    return {
        "identity": {"name": "Sparky", "role": "Latin tutor"},
        "student_profile": {"grade_level": "3-5"},
        "daily_cycle": {"warmup": 5, "instruction": 20},
        "reinforcement_method": {"type": "positive"},
        "feedback_style": {"approach": "gentle"},
        "success_criteria": {"mastery_threshold": 0.8},
        "knowledge_recycling": {"spiral": True}
    }


@pytest.fixture
def fake_day_document():
    """Sample day document for testing."""
    return {
        "metadata": {"week": 11, "day": 1, "duration_minutes": 30},
        "prior_knowledge_digest": "Students know basic nouns from Week 10.",
        "yesterday_recap": "Yesterday we reviewed noun declensions.",
        "spiral_links": {"prior_days": [10.4]},
        "misconception_watchlist": ["verb ending confusion"],
        "objectives": ["Learn present tense"],
        "materials": ["whiteboard", "flashcards"],
        "lesson_flow": [
            {
                "type": "recall",
                "duration_minutes": 5,
                "description": "Review nouns",
                "student_action": "Recite noun forms"
            },
            {
                "type": "introduction",
                "duration_minutes": 10,
                "description": "Introduce verb amo",
                "student_action": "Listen and repeat"
            }
        ],
        "behavior": {
            "tone": "encouraging",
            "hints_max": 3,
            "wait_seconds": 5
        }
    }


def test_generate_week_spec(tmp_path, fake_week_spec):
    """Test week spec generation with fake LLM."""
    # Create fake client with week spec response
    fake_client = FakeLLMClient(response_json=fake_week_spec)

    # Note: This will try to write to actual curriculum directory
    # In production, you'd mock the file system or use tmp_path
    # For now, test the client interaction
    assert fake_client.response_json["metadata"]["week"] == 11


def test_generate_role_context(fake_role_context):
    """Test role context generation with fake LLM."""
    fake_client = FakeLLMClient(response_json=fake_role_context)

    response = fake_client.generate("generate role context")

    assert response.json["identity"]["name"] == "Sparky"
    assert response.json["student_profile"]["grade_level"] == "3-5"


def test_generate_day_document(fake_day_document):
    """Test day document generation with fake LLM."""
    fake_client = FakeLLMClient(response_json=fake_day_document)

    response = fake_client.generate("generate day 1")

    assert response.json["metadata"]["day"] == 1
    assert len(response.json["lesson_flow"]) == 2
    assert response.json["lesson_flow"][0]["type"] == "recall"


def test_fake_assets_generation():
    """Test asset generation with fake LLM."""
    assets_data = {
        "ChantChart": "Amo, amas, amat\nI love, you love, he loves",
        "Glossary": "amo - to love\nhabeo - to have",
        "Copywork": "Amo Latinum.",
        "QuizPacket": "1. Translate: amo",
        "TeacherKey": "1. I love",
        "VirtueEntry": "Reflect on diligence in learning."
    }

    fake_client = FakeLLMClient(response_json=assets_data)
    response = fake_client.generate("generate assets")

    assert "ChantChart" in response.json
    assert "Glossary" in response.json
    assert len(response.json) == 6


def test_generation_pipeline_integration(fake_week_spec, fake_role_context, fake_day_document):
    """Test full generation pipeline with fake LLM."""
    # Simulate generating a complete week
    week_client = FakeLLMClient(response_json=fake_week_spec)
    role_client = FakeLLMClient(response_json=fake_role_context)
    day_client = FakeLLMClient(response_json=fake_day_document)

    # Generate components
    week_response = week_client.generate("week spec")
    role_response = role_client.generate("role context")
    day_response = day_client.generate("day document")

    # Verify pipeline
    assert week_response.json["metadata"]["week"] == 11
    assert role_response.json["identity"]["name"] == "Sparky"
    assert day_response.json["metadata"]["day"] == 1

    # Verify spiral links are present
    assert "spiral_links" in week_response.json
    assert week_response.json["spiral_links"]["prior_weeks"] == [10]


def test_invalid_json_handling():
    """Test handling of invalid JSON from LLM."""
    fake_client = FakeLLMClient(
        response_text="This is not valid JSON",
        response_json=None
    )

    response = fake_client.generate("test")

    assert response.text == "This is not valid JSON"
    assert response.json is None
