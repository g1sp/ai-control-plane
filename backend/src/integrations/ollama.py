"""Ollama integration for local model queries."""

import httpx
from ..config import settings
from ..services.cost_calculator import CostCalculator


class OllamaClient:
    """Client for querying local Ollama model."""

    def __init__(self, host: str = None, model: str = None, timeout: int = 30):
        self.host = host or settings.ollama_host
        self.model = model or settings.ollama_model
        self.timeout = timeout

    def query(self, prompt: str, model: str = None) -> tuple[str, int]:
        """
        Query Ollama model.

        Returns: (response_text, output_tokens)
        """
        model = model or self.model

        try:
            response = httpx.post(
                f"{self.host}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()

            result = response.json()
            response_text = result.get("response", "")
            # Ollama doesn't return token counts, so estimate
            output_tokens = CostCalculator.count_tokens(response_text)

            return response_text, output_tokens

        except httpx.HTTPError as e:
            raise Exception(f"Ollama query failed: {str(e)}")

    def is_available(self) -> bool:
        """Check if Ollama is available."""
        try:
            response = httpx.get(f"{self.host}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception:
            return False

    def list_models(self) -> list[str]:
        """List available models in Ollama."""
        try:
            response = httpx.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [m.get("name", "") for m in data.get("models", [])]
            return []
        except Exception:
            return []
