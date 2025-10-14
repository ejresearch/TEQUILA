"""Tests for LLM client abstraction."""
import pytest
from src.services.llm_client import LLMClient, LLMResponse


class FakeLLMClient(LLMClient):
    """Fake LLM client for testing."""

    def __init__(self, response_text: str = None, response_json: dict = None):
        """Initialize with canned responses."""
        self.response_text = response_text or '{"test": "response"}'
        self.response_json = response_json or {"test": "response"}
        self.call_count = 0
        self.last_prompt = None
        self.last_system = None

    def generate(self, prompt, system=None, json_schema=None):
        """Return canned response and track calls."""
        self.call_count += 1
        self.last_prompt = prompt
        self.last_system = system
        return LLMResponse(
            text=self.response_text,
            json=self.response_json,
            raw=None
        )


def test_fake_llm_basic():
    """Test basic fake LLM operation."""
    fake = FakeLLMClient()
    response = fake.generate("test prompt", system="test system")

    assert response.text == '{"test": "response"}'
    assert response.json == {"test": "response"}
    assert fake.call_count == 1
    assert fake.last_prompt == "test prompt"
    assert fake.last_system == "test system"


def test_fake_llm_custom_response():
    """Test fake LLM with custom response."""
    custom_json = {"metadata": {"week": 11, "title": "Latin Verbs"}}
    fake = FakeLLMClient(response_json=custom_json)

    response = fake.generate("generate week 11")

    assert response.json["metadata"]["week"] == 11
    assert response.json["metadata"]["title"] == "Latin Verbs"


def test_fake_llm_multiple_calls():
    """Test fake LLM tracks multiple calls."""
    fake = FakeLLMClient()

    fake.generate("first")
    fake.generate("second")
    fake.generate("third")

    assert fake.call_count == 3
    assert fake.last_prompt == "third"


def test_llm_response_structure():
    """Test LLMResponse dataclass structure."""
    response = LLMResponse(
        text='{"key": "value"}',
        json={"key": "value"},
        raw={"raw_data": True}
    )

    assert response.text == '{"key": "value"}'
    assert response.json == {"key": "value"}
    assert response.raw == {"raw_data": True}


def test_llm_response_json_optional():
    """Test LLMResponse with no JSON parsing."""
    response = LLMResponse(text="plain text response")

    assert response.text == "plain text response"
    assert response.json is None
    assert response.raw is None
