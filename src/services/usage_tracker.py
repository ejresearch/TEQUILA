"""Usage tracking for LLM API calls and cost estimation."""
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
import orjson
from threading import Lock


# Rough cost estimates per 1M tokens (as of 2025) - OpenAI only
COST_PER_1M_TOKENS = {
    "gpt-4o": {"input": 2.50, "output": 10.00},
    "gpt-4o-mini": {"input": 0.15, "output": 0.60},
    "gpt-4-turbo": {"input": 10.00, "output": 30.00},
    "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
}


class UsageTracker:
    """Thread-safe usage tracker for LLM API calls."""

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize usage tracker.

        Args:
            storage_path: Path to JSON file for persisting usage data.
                         Defaults to curriculum/usage/summary.json
        """
        if storage_path is None:
            storage_path = Path(__file__).parent.parent.parent / "curriculum" / "usage" / "summary.json"

        self.storage_path = storage_path
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = Lock()
        self._load()

    def _load(self):
        """Load existing usage data from disk."""
        if self.storage_path.exists():
            try:
                self.data = orjson.loads(self.storage_path.read_bytes())
            except Exception:
                self.data = self._init_data()
        else:
            self.data = self._init_data()

    def _init_data(self) -> Dict[str, Any]:
        """Initialize empty usage data structure."""
        return {
            "total_requests": 0,
            "total_tokens_prompt": 0,
            "total_tokens_completion": 0,
            "estimated_cost_usd": 0.0,
            "by_provider": {},
            "by_model": {},
            "sessions": [],
            "last_updated": datetime.utcnow().isoformat() + "Z"
        }

    def _save(self):
        """Persist usage data to disk."""
        self.data["last_updated"] = datetime.utcnow().isoformat() + "Z"
        self.storage_path.write_bytes(
            orjson.dumps(self.data, option=orjson.OPT_INDENT_2)
        )

    def track(
        self,
        provider: str,
        model: str,
        tokens_prompt: int,
        tokens_completion: int,
        operation: str = "generation"
    ):
        """
        Record a single LLM API call.

        Args:
            provider: Provider name (should be "openai")
            model: Model name (e.g., "gpt-4o", "gpt-4o-mini")
            tokens_prompt: Input tokens used
            tokens_completion: Output tokens generated
            operation: Type of operation (e.g., "generation", "week_spec", "day_document")
        """
        with self.lock:
            # Calculate cost
            cost = self._estimate_cost(model, tokens_prompt, tokens_completion)

            # Update totals
            self.data["total_requests"] += 1
            self.data["total_tokens_prompt"] += tokens_prompt
            self.data["total_tokens_completion"] += tokens_completion
            self.data["estimated_cost_usd"] += cost

            # Update by provider
            if provider not in self.data["by_provider"]:
                self.data["by_provider"][provider] = {
                    "requests": 0,
                    "tokens_prompt": 0,
                    "tokens_completion": 0,
                    "cost_usd": 0.0
                }
            self.data["by_provider"][provider]["requests"] += 1
            self.data["by_provider"][provider]["tokens_prompt"] += tokens_prompt
            self.data["by_provider"][provider]["tokens_completion"] += tokens_completion
            self.data["by_provider"][provider]["cost_usd"] += cost

            # Update by model
            if model not in self.data["by_model"]:
                self.data["by_model"][model] = {
                    "requests": 0,
                    "tokens_prompt": 0,
                    "tokens_completion": 0,
                    "cost_usd": 0.0
                }
            self.data["by_model"][model]["requests"] += 1
            self.data["by_model"][model]["tokens_prompt"] += tokens_prompt
            self.data["by_model"][model]["tokens_completion"] += tokens_completion
            self.data["by_model"][model]["cost_usd"] += cost

            # Add session record
            self.data["sessions"].append({
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "provider": provider,
                "model": model,
                "operation": operation,
                "tokens_prompt": tokens_prompt,
                "tokens_completion": tokens_completion,
                "cost_usd": round(cost, 4)
            })

            # Keep only last 1000 sessions
            if len(self.data["sessions"]) > 1000:
                self.data["sessions"] = self.data["sessions"][-1000:]

            self._save()

    def _estimate_cost(self, model: str, tokens_prompt: int, tokens_completion: int) -> float:
        """
        Estimate cost in USD for a request.

        Args:
            model: Model name
            tokens_prompt: Input tokens
            tokens_completion: Output tokens

        Returns:
            Estimated cost in USD
        """
        if model not in COST_PER_1M_TOKENS:
            # Unknown model, use conservative estimate
            input_cost = 5.00
            output_cost = 15.00
        else:
            pricing = COST_PER_1M_TOKENS[model]
            input_cost = pricing["input"]
            output_cost = pricing["output"]

        cost_input = (tokens_prompt / 1_000_000) * input_cost
        cost_output = (tokens_completion / 1_000_000) * output_cost

        return cost_input + cost_output

    def get_summary(self) -> Dict[str, Any]:
        """Get current usage summary."""
        with self.lock:
            return self.data.copy()

    def reset(self):
        """Reset all usage data."""
        with self.lock:
            self.data = self._init_data()
            self._save()


# Global tracker instance
_tracker: Optional[UsageTracker] = None


def get_tracker() -> UsageTracker:
    """Get global usage tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = UsageTracker()
    return _tracker
