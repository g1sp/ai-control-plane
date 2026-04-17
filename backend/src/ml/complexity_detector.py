"""Query complexity detection for adaptive tool selection."""

from typing import Dict, List, Optional
from enum import Enum
import re


class ComplexityLevel(str, Enum):
    """Query complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    VERY_COMPLEX = "very_complex"


class QueryComplexityDetector:
    """Detect query complexity for intelligent tool selection."""

    def __init__(self):
        """Initialize detector with keyword patterns."""
        # Simple queries: direct questions
        self.simple_keywords = {
            "what is", "who is", "where is", "when is",
            "how much", "how many", "list", "tell me about"
        }

        # Moderate queries: multi-step or analysis
        self.moderate_keywords = {
            "compare", "analyze", "explain", "summarize",
            "pros and cons", "advantages", "disadvantages"
        }

        # Complex queries: reasoning or multiple steps
        self.complex_keywords = {
            "why", "how would", "design", "create", "implement",
            "solve", "optimize", "improve", "refactor"
        }

        # Very complex: research or synthesis
        self.very_complex_keywords = {
            "research", "investigate", "comprehensive", "deep dive",
            "cross-domain", "integrate", "synthesize", "correlation"
        }

        # Multi-language indicators
        self.multi_lang_keywords = {"translate", "convert", "parse"}

        # Tool indicators
        self.search_keywords = {"search", "find", "lookup", "query"}
        self.math_keywords = {"calculate", "compute", "solve", "equation"}
        self.code_keywords = {"code", "script", "program", "function"}
        self.analysis_keywords = {"trend", "pattern", "predict", "forecast"}

    def detect_complexity(self, query: str) -> ComplexityLevel:
        """Detect query complexity level."""
        score = self._calculate_complexity_score(query)

        if score < 2:
            return ComplexityLevel.SIMPLE
        elif score < 4:
            return ComplexityLevel.MODERATE
        elif score < 6:
            return ComplexityLevel.COMPLEX
        else:
            return ComplexityLevel.VERY_COMPLEX

    def _calculate_complexity_score(self, query: str) -> int:
        """Calculate complexity score (0-10)."""
        score = 0
        query_lower = query.lower()

        # Base score from keywords
        if any(kw in query_lower for kw in self.very_complex_keywords):
            score += 5
        elif any(kw in query_lower for kw in self.complex_keywords):
            score += 4
        elif any(kw in query_lower for kw in self.moderate_keywords):
            score += 2
        elif any(kw in query_lower for kw in self.simple_keywords):
            score += 0.5

        # Bonus: length indicates complexity
        word_count = len(query.split())
        if word_count > 50:
            score += 2
        elif word_count > 30:
            score += 1

        # Bonus: question complexity
        sentence_count = len(re.split(r'[.!?]+', query))
        if sentence_count > 3:
            score += 1

        # Bonus: special characters (code, equations)
        special_chars = sum(1 for c in query if c in '{}[]()$^*')
        if special_chars > 5:
            score += 1

        # Bonus: specific tool indicators
        tool_indicators = 0
        if any(kw in query_lower for kw in self.search_keywords):
            tool_indicators += 1
        if any(kw in query_lower for kw in self.math_keywords):
            tool_indicators += 1
        if any(kw in query_lower for kw in self.code_keywords):
            tool_indicators += 1
        if any(kw in query_lower for kw in self.analysis_keywords):
            tool_indicators += 1

        if tool_indicators >= 2:
            score += 1

        return min(score, 10)

    def suggest_tools(
        self,
        query: str,
        available_tools: List[str]
    ) -> Dict[str, float]:
        """Suggest which tools to use based on complexity."""
        complexity = self.detect_complexity(query)
        query_lower = query.lower()

        effectiveness: Dict[str, float] = {}

        # Default effectiveness for all tools
        for tool in available_tools:
            effectiveness[tool] = 0.5

        # Adjust based on query content
        if any(kw in query_lower for kw in self.search_keywords):
            effectiveness["search"] = 1.0
            effectiveness["knowledge_base"] = 0.9

        if any(kw in query_lower for kw in self.math_keywords):
            effectiveness["calculator"] = 1.0
            effectiveness["math_solver"] = 0.95

        if any(kw in query_lower for kw in self.code_keywords):
            effectiveness["code_generator"] = 1.0
            effectiveness["code_validator"] = 0.8
            effectiveness["debugger"] = 0.7

        if any(kw in query_lower for kw in self.analysis_keywords):
            effectiveness["analytics"] = 1.0
            effectiveness["statistics"] = 0.9

        # Adjust based on complexity
        if complexity == ComplexityLevel.SIMPLE:
            effectiveness["search"] = effectiveness.get("search", 0.5)
        elif complexity == ComplexityLevel.MODERATE:
            effectiveness["calculator"] = effectiveness.get("calculator", 0.5)
            effectiveness["code_generator"] = effectiveness.get("code_generator", 0.5)
        elif complexity == ComplexityLevel.COMPLEX:
            effectiveness["code_validator"] = effectiveness.get("code_validator", 0.5)
            effectiveness["debugger"] = effectiveness.get("debugger", 0.5)
        elif complexity == ComplexityLevel.VERY_COMPLEX:
            effectiveness["analytics"] = effectiveness.get("analytics", 0.5)
            effectiveness["code_validator"] = effectiveness.get("code_validator", 0.6)

        return effectiveness

    def estimate_tokens(self, query: str) -> int:
        """Estimate token count for query."""
        word_count = len(query.split())
        # Rough estimate: 1 word ≈ 1.3 tokens
        estimated_tokens = int(word_count * 1.3)
        return max(estimated_tokens, 1)

    def estimate_duration_seconds(self, complexity: ComplexityLevel) -> float:
        """Estimate execution duration based on complexity."""
        estimates = {
            ComplexityLevel.SIMPLE: 0.5,
            ComplexityLevel.MODERATE: 1.5,
            ComplexityLevel.COMPLEX: 3.0,
            ComplexityLevel.VERY_COMPLEX: 5.0,
        }
        return estimates.get(complexity, 1.0)


class ToolEffectivenessTracker:
    """Track tool effectiveness metrics over time."""

    def __init__(self):
        """Initialize tracker."""
        self.tool_stats: Dict[str, Dict[str, float]] = {}

    def record_tool_use(
        self,
        tool_name: str,
        success: bool,
        tokens_used: int,
        duration_seconds: float,
        complexity: ComplexityLevel,
    ) -> None:
        """Record tool usage metrics."""
        if tool_name not in self.tool_stats:
            self.tool_stats[tool_name] = {
                "uses": 0,
                "successes": 0,
                "failures": 0,
                "total_tokens": 0,
                "total_duration": 0.0,
                "effectiveness": 0.5,
            }

        stats = self.tool_stats[tool_name]
        stats["uses"] += 1
        if success:
            stats["successes"] += 1
        else:
            stats["failures"] += 1

        stats["total_tokens"] += tokens_used
        stats["total_duration"] += duration_seconds

        # Recalculate effectiveness
        success_rate = stats["successes"] / max(stats["uses"], 1)
        avg_tokens = stats["total_tokens"] / max(stats["uses"], 1)
        avg_duration = stats["total_duration"] / max(stats["uses"], 1)

        # Effectiveness = success_rate - (token_penalty + duration_penalty)
        token_penalty = min(avg_tokens / 1000, 0.2)  # Up to 0.2 penalty
        duration_penalty = min(avg_duration / 10, 0.2)  # Up to 0.2 penalty

        stats["effectiveness"] = max(
            0.1,
            success_rate - token_penalty - duration_penalty
        )

    def get_tool_effectiveness(self, tool_name: str) -> float:
        """Get effectiveness score for tool (0.0-1.0)."""
        if tool_name not in self.tool_stats:
            return 0.5
        return self.tool_stats[tool_name]["effectiveness"]

    def get_tool_stats(self, tool_name: str) -> Optional[Dict[str, float]]:
        """Get full stats for tool."""
        return self.tool_stats.get(tool_name)

    def rank_tools(self, tools: List[str]) -> List[tuple[str, float]]:
        """Rank tools by effectiveness."""
        rankings = [
            (tool, self.get_tool_effectiveness(tool))
            for tool in tools
        ]
        rankings.sort(key=lambda x: x[1], reverse=True)
        return rankings

    def reset_tool(self, tool_name: str) -> None:
        """Reset stats for tool."""
        if tool_name in self.tool_stats:
            del self.tool_stats[tool_name]
