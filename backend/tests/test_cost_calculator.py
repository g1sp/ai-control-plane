"""Tests for cost calculator."""

import pytest
from src.services.cost_calculator import CostCalculator


class TestCostCalculator:
    """Test cost calculation."""

    def test_count_tokens_heuristic(self):
        """Token counting should use heuristic (1 token ≈ 4 chars)."""
        text = "Hello World"  # 11 chars
        tokens = CostCalculator.count_tokens(text)
        assert tokens == max(1, 11 // 4)  # Should be 2

    def test_count_tokens_minimum(self):
        """Empty text should count as at least 1 token."""
        tokens = CostCalculator.count_tokens("")
        assert tokens >= 1

    def test_calculate_cost_ollama_free(self):
        """Ollama should cost $0."""
        cost = CostCalculator.calculate_cost("ollama", 100, 100)
        assert cost == 0.0

    def test_calculate_cost_claude_sonnet(self):
        """Claude Sonnet cost should be calculated correctly."""
        # 1000 input tokens, 1000 output tokens
        cost = CostCalculator.calculate_cost("claude-sonnet-4-6", 1000, 1000)
        # Input: 1000 * 0.003 / 1000 = 0.003
        # Output: 1000 * 0.015 / 1000 = 0.015
        # Total: 0.018
        expected = 0.018
        assert abs(cost - expected) < 0.0001

    def test_calculate_cost_claude_haiku(self):
        """Claude Haiku cost should be lower than Sonnet."""
        cost_haiku = CostCalculator.calculate_cost("claude-haiku-4-5", 1000, 1000)
        cost_sonnet = CostCalculator.calculate_cost("claude-sonnet-4-6", 1000, 1000)
        assert cost_haiku < cost_sonnet

    def test_estimate_cost_for_prompt(self):
        """Estimate cost should return a reasonable value."""
        prompt = "What is the capital of France?"
        cost = CostCalculator.estimate_cost_for_prompt("claude-sonnet-4-6", prompt)
        assert cost > 0

    def test_estimate_cost_ollama_free(self):
        """Ollama cost estimate should be free."""
        prompt = "What is the capital of France?"
        cost = CostCalculator.estimate_cost_for_prompt("ollama", prompt)
        assert cost == 0.0
