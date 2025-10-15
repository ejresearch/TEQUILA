"""LLM client abstraction for OpenAI GPT-4o."""
from dataclasses import dataclass
from typing import Optional, Dict, Any
import orjson
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


@dataclass
class LLMResponse:
    """Response from an LLM generation request."""
    text: str
    json: Optional[Dict[str, Any]] = None
    raw: Any = None
    tokens_prompt: Optional[int] = None
    tokens_completion: Optional[int] = None
    model: Optional[str] = None
    provider: Optional[str] = None


class LLMClient:
    """OpenAI GPT-4o client for TEQUILA/Steel curriculum generation."""

    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        json_schema: Optional[Dict] = None
    ) -> LLMResponse:
        """
        Generate a response from the LLM.

        Args:
            prompt: User prompt text
            system: Optional system prompt
            json_schema: Optional JSON schema for structured output

        Returns:
            LLMResponse with text and optionally parsed JSON
        """
        raise NotImplementedError

    def _check_budget(self):
        """Check if generation would exceed budget cap."""
        from ..config import settings
        from .usage_tracker import get_tracker

        if settings.BUDGET_USD is None:
            return  # No budget set

        tracker = get_tracker()
        summary = tracker.get_summary()
        spent = summary.get("estimated_cost_usd", 0.0)

        if spent >= settings.BUDGET_USD:
            raise BudgetExceededError(
                f"Budget exceeded: ${spent:.2f} spent, limit is ${settings.BUDGET_USD:.2f}. "
                "Increase BUDGET_USD in .env or reset usage with /api/v1/usage/reset"
            )

        # Warn at threshold
        warn_threshold = settings.BUDGET_USD * settings.COST_WARN_PCT
        if spent >= warn_threshold and spent < settings.BUDGET_USD:
            import warnings
            warnings.warn(
                f"Budget warning: ${spent:.2f} spent of ${settings.BUDGET_USD:.2f} limit "
                f"({spent/settings.BUDGET_USD*100:.1f}%)"
            )

    def _dry_run_response(self, prompt: str, system: Optional[str]) -> LLMResponse:
        """Return placeholder response for dry-run mode."""
        placeholder_json = {
            "metadata": {"week": 1, "title": "DRY RUN PLACEHOLDER", "virtue_focus": "Testing"},
            "objectives": [{"id": "dry_run_1", "description": "Placeholder objective", "category": "vocabulary"}],
            "vocabulary": [{"latin": "test", "english": "test", "part_of_speech": "noun"}],
            "grammar_focus": "This is a dry-run placeholder response",
            "chant": {"latin_text": "placeholder", "english_translation": "placeholder"},
            "sessions": [
                {"day": i, "focus": "dry-run", "activities": ["placeholder"]}
                for i in range(1, 5)
            ],
            "assessment": {"format": "dry-run", "timing": "Day 4", "prior_content_percentage": 25, "items": ["placeholder"]},
            "assets": ["placeholder"],
            "spiral_links": {"prior_weeks_dependencies": [], "recycled_vocab": [], "recycled_grammar": []},
            "interleaving_plan": "Dry-run placeholder for testing without API calls",
            "misconception_watchlist": [],
            "preview_next_week": "Next week placeholder"
        }

        return LLMResponse(
            text=orjson.dumps(placeholder_json).decode(),
            json=placeholder_json,
            raw=None,
            tokens_prompt=0,
            tokens_completion=0,
            model="dry-run",
            provider="dry-run"
        )


class _TransientError(Exception):
    """Wrapper for transient errors that should be retried."""
    pass


class BudgetExceededError(Exception):
    """Raised when generation would exceed budget cap."""
    pass


class OpenAIClient(LLMClient):
    """OpenAI API client with retry logic for GPT-4o."""

    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4o",
        temp: float = 0.2,
        max_tokens: int = 2000,
        timeout: int = 60
    ):
        """Initialize OpenAI client.

        Args:
            api_key: OpenAI API key
            model: Model name (default: gpt-4o)
            temp: Temperature (default: 0.2)
            max_tokens: Maximum tokens (default: 2000)
            timeout: Request timeout in seconds (default: 60)
        """
        if not api_key:
            raise ValueError("OPENAI_API_KEY missing")

        try:
            import openai
        except ImportError:
            raise ImportError("openai package required. Install with: pip install openai")

        self.client = openai.OpenAI(api_key=api_key, timeout=timeout)
        self.model = model
        self.temp = temp
        self.max_tokens = max_tokens
        self.timeout = timeout

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(min=1, max=6),
        retry=retry_if_exception_type(_TransientError)
    )
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        json_schema: Optional[Dict] = None
    ) -> LLMResponse:
        """Generate response using OpenAI GPT-4o API.

        Args:
            prompt: User prompt text
            system: Optional system prompt
            json_schema: Optional JSON schema for structured output

        Returns:
            LLMResponse with text, JSON, and usage metadata
        """
        # Check dry-run mode
        from ..config import settings
        if settings.DRY_RUN:
            return self._dry_run_response(prompt, system)

        # Check budget
        self._check_budget()

        msgs = []
        if system:
            msgs.append({"role": "system", "content": system})
        msgs.append({"role": "user", "content": prompt})

        kwargs = {
            "model": self.model,
            "temperature": self.temp,
            "max_tokens": self.max_tokens
        }

        # Add JSON schema if provided (strict structured output)
        if json_schema:
            # Validate schema has required structure for OpenAI API
            if not isinstance(json_schema, dict):
                raise ValueError(f"json_schema must be a dict, got {type(json_schema)}")

            # Check if it's a complete OpenAI structured output schema
            if "name" in json_schema and "schema" in json_schema:
                # Already in OpenAI format
                kwargs["response_format"] = {
                    "type": "json_schema",
                    "json_schema": json_schema
                }
            elif "type" in json_schema and "properties" in json_schema:
                # Convert simple JSON schema to OpenAI format
                kwargs["response_format"] = {
                    "type": "json_schema",
                    "json_schema": {
                        "name": "response",
                        "strict": True,
                        "schema": json_schema
                    }
                }
            else:
                # Incomplete schema - log warning and skip structured output
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(
                    f"Incomplete JSON schema provided (missing 'properties' or 'name'). "
                    f"Skipping structured output. Schema keys: {list(json_schema.keys())}"
                )
                # Don't use structured output for incomplete schemas

        try:
            resp = self.client.chat.completions.create(messages=msgs, **kwargs)
        except Exception as e:
            # Log the actual error before wrapping
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"OpenAI API error: {type(e).__name__}: {e}")
            # Wrap in transient error for retry
            raise _TransientError(str(e))

        out = resp.choices[0].message.content or ""

        # Extract token usage
        usage = resp.usage if hasattr(resp, 'usage') else None
        tokens_prompt = usage.prompt_tokens if usage else None
        tokens_completion = usage.completion_tokens if usage else None

        # Attempt to parse JSON
        js = None
        if out and out.strip().startswith("{"):
            try:
                js = orjson.loads(out)
            except Exception:
                pass

        return LLMResponse(
            text=out,
            json=js,
            raw=resp,
            tokens_prompt=tokens_prompt,
            tokens_completion=tokens_completion,
            model=self.model,
            provider="openai"
        )


def get_client(
    provider: str = "openai",
    model: Optional[str] = None,
    **kwargs
) -> LLMClient:
    """
    Factory function to get LLM client.

    Args:
        provider: Provider name (only "openai" supported)
        model: Model name (default: gpt-4o)
        **kwargs: Additional arguments passed to client constructor

    Returns:
        Configured LLMClient instance

    Raises:
        ValueError: If provider is not "openai"
    """
    from ..config import settings

    if provider != "openai":
        raise ValueError(f"Only 'openai' provider is supported. Got: {provider}")

    return OpenAIClient(
        api_key=settings.OPENAI_API_KEY,
        model=model or "gpt-4o",
        temp=kwargs.get("temp", 0.2),
        max_tokens=kwargs.get("max_tokens", 2000),
        timeout=kwargs.get("timeout", 60)
    )
