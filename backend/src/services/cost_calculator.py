"""Cost calculation and token counting."""


class CostCalculator:
    """Calculate costs based on token usage and model pricing."""

    # Pricing per 1K tokens (input, output)
    PRICING = {
        "ollama": {"input_per_1k": 0.0, "output_per_1k": 0.0},
        "claude-opus-4-6": {"input_per_1k": 0.015, "output_per_1k": 0.075},
        "claude-sonnet-4-6": {"input_per_1k": 0.003, "output_per_1k": 0.015},
        "claude-haiku-4-5": {"input_per_1k": 0.00080, "output_per_1k": 0.004},
    }

    @staticmethod
    def count_tokens(text: str, model: str = "ollama") -> int:
        """
        Estimate token count for text.

        Heuristic: 1 token ≈ 4 characters.
        For production, use actual tokenizer from API.
        """
        return max(1, len(text) // 4)

    @staticmethod
    def calculate_cost(model: str, tokens_in: int, tokens_out: int) -> float:
        """Calculate cost for a request."""
        if model not in CostCalculator.PRICING:
            model = "claude-sonnet-4-6"  # Default to sonnet if unknown

        pricing = CostCalculator.PRICING[model]
        cost = (tokens_in * pricing["input_per_1k"] / 1000) + (
            tokens_out * pricing["output_per_1k"] / 1000
        )
        return round(cost, 6)

    @staticmethod
    def estimate_cost_for_prompt(model: str, prompt: str) -> float:
        """Estimate cost before execution."""
        tokens = CostCalculator.count_tokens(prompt, model)
        # Assume output will be similar length to input (rough estimate)
        return CostCalculator.calculate_cost(model, tokens, tokens)
