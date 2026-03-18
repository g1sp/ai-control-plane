"""Model routing logic."""

from ..config import settings


class ModelRouter:
    """Decide which model to use for each request."""

    def __init__(self, ollama_client=None):
        """
        Initialize router with optional Ollama client.
        If not provided, Ollama availability will be checked on-demand.
        """
        self.ollama_client = ollama_client

    def decide(self, prompt: str, preferred_model: str = "auto", gateway_mode: str = None):
        """
        Decide which model to use and return (model_name, endpoint).

        Logic:
        - If gateway_mode is "local" AND Ollama available AND prompt is short:
          Use Ollama (free)
        - Otherwise:
          Use Claude (powerful)
        """
        mode = gateway_mode or settings.gateway_mode

        # If preferred model explicitly requested
        if preferred_model != "auto" and preferred_model in settings.models_whitelist:
            return (preferred_model, self._get_endpoint(preferred_model))

        # Auto mode: decide based on prompt and availability
        if mode == "local":
            if self.is_ollama_available() and len(prompt) < 500:
                return ("ollama", "local")

        # Default to Claude Sonnet
        return ("claude-sonnet-4-6", "remote")

    def is_ollama_available(self) -> bool:
        """Check if Ollama is available."""
        if self.ollama_client:
            return self.ollama_client.is_available()
        # If no client provided, assume not available (fail safe)
        return False

    @staticmethod
    def _get_endpoint(model: str) -> str:
        """Get endpoint for model."""
        if model == "ollama":
            return "local"
        return "remote"
