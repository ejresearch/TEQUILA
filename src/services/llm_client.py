"""LLM client abstraction supporting OpenAI and Anthropic."""
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


class LLMClient:
    """Abstract base class for LLM clients."""

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


class _TransientError(Exception):
    """Wrapper for transient errors that should be retried."""
    pass


class OpenAIClient(LLMClient):
    """OpenAI API client with retry logic."""

    def __init__(
        self,
        api_key: str,
        model: str,
        temp: float,
        max_tokens: int,
        timeout: int
    ):
        """Initialize OpenAI client."""
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
        """Generate response using OpenAI API."""
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
            kwargs["response_format"] = {
                "type": "json_schema",
                "json_schema": json_schema
            }

        try:
            resp = self.client.chat.completions.create(messages=msgs, **kwargs)
        except Exception as e:
            # Wrap in transient error for retry
            raise _TransientError(str(e))

        out = resp.choices[0].message.content or ""

        # Attempt to parse JSON
        js = None
        if out and out.strip().startswith("{"):
            try:
                js = orjson.loads(out)
            except Exception:
                pass

        return LLMResponse(text=out, json=js, raw=resp)


class AnthropicClient(LLMClient):
    """Anthropic API client with retry logic."""

    def __init__(
        self,
        api_key: str,
        model: str,
        temp: float,
        max_tokens: int,
        timeout: int
    ):
        """Initialize Anthropic client."""
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY missing")

        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic package required. Install with: pip install anthropic")

        self.client = anthropic.Anthropic(api_key=api_key, timeout=timeout)
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
        """Generate response using Anthropic API."""
        try:
            resp = self.client.messages.create(
                model=self.model,
                temperature=self.temp,
                max_tokens=self.max_tokens,
                system=system or "",
                messages=[{"role": "user", "content": prompt}]
            )
        except Exception as e:
            # Wrap in transient error for retry
            raise _TransientError(str(e))

        # Extract text from content blocks
        out = "".join([
            block.text for block in resp.content
            if getattr(block, "type", "") == "text"
        ])

        # Attempt to parse JSON
        js = None
        if out and out.strip().startswith("{"):
            try:
                js = orjson.loads(out)
            except Exception:
                pass

        return LLMResponse(text=out, json=js, raw=resp)
